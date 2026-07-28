from __future__ import annotations

import json
import logging
import asyncio
import time
from typing import Any

import aiohttp
from aiohttp import web

from .audit import AuditLogger
from .canary import CanaryTokenDetector
from .config import MedGuardConfig, apply_config_update, config_payload
from .dashboard import DASHBOARD_HTML
from .detectors import InjectionPatternDetector
from .isolation import RAGContentIsolator

logger = logging.getLogger("medguard_proxy")


def blocked_response(reason: str) -> web.Response:
    return web.json_response(
        {
            "error": {
                "message": f"[MedGuard] Request blocked: {reason}",
                "type": "medguard_policy_violation",
                "code": "injection_detected",
            }
        },
        status=403,
    )


def error_response(message: str, status: int = 400, code: str = "bad_request") -> web.Response:
    return web.json_response(
        {"error": {"message": message, "type": "medguard_error", "code": code}},
        status=status,
    )


async def read_json_object(request: web.Request) -> tuple[dict[str, Any] | None, web.Response | None]:
    try:
        payload = await request.json()
    except (json.JSONDecodeError, ValueError):
        return None, error_response("request body must be valid JSON")
    if not isinstance(payload, dict):
        return None, error_response("request body must be a JSON object")
    return payload, None


def validate_messages(body: dict[str, Any]) -> tuple[list[dict[str, Any]] | None, web.Response | None]:
    messages = body.get("messages")
    if not isinstance(messages, list):
        return None, error_response("'messages' must be a list")
    if not all(isinstance(message, dict) for message in messages):
        return None, error_response("each message must be a JSON object")
    return messages, None


def message_summary(messages: list[dict[str, Any]]) -> dict[str, Any]:
    roles: dict[str, int] = {}
    total_chars = 0
    for msg in messages:
        role = str(msg.get("role", "unknown"))
        roles[role] = roles.get(role, 0) + 1
        content = msg.get("content", "")
        if isinstance(content, str):
            total_chars += len(content)
        elif isinstance(content, list):
            total_chars += sum(len(part.get("text", "")) for part in content if isinstance(part, dict))
    return {"count": len(messages), "roles": roles, "total_chars": total_chars}


def redact_canary(messages: list[dict[str, Any]], token: str) -> list[dict[str, Any]]:
    if not token:
        return messages
    redacted = []
    for msg in messages:
        content = msg.get("content")
        if isinstance(content, str):
            msg = {**msg, "content": content.replace(token, "<CANARY_TOKEN>")}
        redacted.append(msg)
    return redacted


def simulated_ai_output(user_message: str, rag_content: str, decision: str) -> str:
    if decision == "blocked":
        return "No AI response generated because MedGuard blocked the request."
    source = rag_content or user_message
    preview = " ".join(source.split())[:180]
    return f"Simulated clinical assistant output: reviewed supplied context. Key safe summary: {preview}"


class MedGuardProxy:
    def __init__(self, config: MedGuardConfig):
        self.config = config
        self.detector = InjectionPatternDetector(config)
        self.isolator = RAGContentIsolator(config)
        self.canary = CanaryTokenDetector(config)
        self.audit = AuditLogger(config)
        self._session: aiohttp.ClientSession | None = None

    async def session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.upstream_timeout_seconds)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    def build_headers(self, request: web.Request) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        for key in ("authorization", "api-key", "x-api-key", "anthropic-version"):
            if key in request.headers:
                headers[key] = request.headers[key]
        return headers

    async def handle_chat_completions(self, request: web.Request) -> web.StreamResponse:
        body, error = await read_json_object(request)
        if error:
            return error
        messages, error = validate_messages(body)
        if error:
            return error
        if body.get("stream", False):
            return error_response(
                "streaming responses are planned for Iteration 2",
                status=400,
                code="streaming_not_supported",
            )

        detected, messages, layer1_meta = self.detector.scan_messages(messages)
        if detected and self.config.block_on_injection:
            self.audit.log("blocked", {"reason": "injection_pattern", "layer1_meta": layer1_meta})
            return blocked_response("prompt injection pattern detected")

        messages, isolation_applied = self.isolator.isolate(messages)
        messages, canary_token = self.canary.inject(messages)

        body["messages"] = messages
        self.audit.log(
            "request",
            {
                "layer1_meta": layer1_meta,
                "rag_isolation": isolation_applied,
                "canary_injected": bool(canary_token),
                "summary": message_summary(messages),
            },
        )

        target_url = self.config.target_base_url.rstrip("/") + "/chat/completions"
        session = await self.session()
        headers = self.build_headers(request)
        return await self.handle_non_streaming(session, target_url, headers, body, canary_token)

    async def handle_non_streaming(
        self,
        session: aiohttp.ClientSession,
        url: str,
        headers: dict[str, str],
        body: dict[str, Any],
        canary_token: str,
    ) -> web.Response:
        try:
            async with session.post(url, json=body, headers=headers) as resp:
                text = await resp.text()
                try:
                    response_body = json.loads(text)
                except json.JSONDecodeError:
                    return web.Response(text=text, status=resp.status, content_type=resp.content_type)

                for choice in response_body.get("choices", []):
                    content = choice.get("message", {}).get("content", "") or ""
                    if self.canary.triggered(content, canary_token):
                        logger.warning("Layer 3: canary token appeared in non-streaming output.")
                        self.audit.log("canary_triggered", {"snippet": content[:200]})
                        return blocked_response("canary token detected in output")

                return web.json_response(response_body, status=resp.status)
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            logger.warning("Upstream LLM request failed: %s", exc)
            self.audit.log("upstream_error", {"error": type(exc).__name__})
            return error_response("upstream LLM API is unavailable", status=502, code="upstream_unavailable")

    async def handle_passthrough(self, request: web.Request) -> web.Response:
        path = request.path
        target_url = self.config.target_base_url.rstrip("/") + path.replace("/v1", "", 1)
        headers = dict(request.headers)
        headers.pop("Host", None)
        body = await request.read()
        session = await self.session()
        try:
            async with session.request(request.method, target_url, headers=headers, data=body) as resp:
                response_body = await resp.read()
                return web.Response(body=response_body, status=resp.status, content_type=resp.content_type)
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            logger.warning("Upstream passthrough request failed: %s", exc)
            self.audit.log("upstream_error", {"error": type(exc).__name__, "passthrough": True})
            return error_response("upstream LLM API is unavailable", status=502, code="upstream_unavailable")

    async def cleanup(self, app: web.Application) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
        self.audit.close()


def create_app(config: MedGuardConfig) -> web.Application:
    proxy = MedGuardProxy(config)
    app = web.Application()

    def metrics() -> dict[str, int]:
        events = proxy.audit.recent()
        total = sum(1 for event in events if event.get("event") in ("request", "demo_analyze"))
        blocked = sum(1 for event in events if event.get("event") == "blocked" or event.get("decision") == "blocked")
        sanitized = sum(1 for event in events if event.get("layer1_meta", {}).get("layer1") == "sanitized")
        passed = sum(1 for event in events if event.get("decision") == "passed" or event.get("event") == "request")
        return {
            "total_requests": total,
            "blocked": blocked,
            "passed": passed,
            "sanitized": sanitized,
            "detections": sum(
                len(event.get("layer1_meta", {}).get("detections", []))
                for event in events
                if isinstance(event.get("layer1_meta"), dict)
            ),
            "rag_isolated": sum(1 for event in events if event.get("rag_isolation")),
            "canary_injected": sum(1 for event in events if event.get("canary_injected")),
            "upstream_errors": sum(1 for event in events if event.get("event") == "upstream_error"),
        }

    async def dashboard_handler(request: web.Request) -> web.Response:
        return web.Response(text=DASHBOARD_HTML, content_type="text/html")

    async def status_handler(request: web.Request) -> web.Response:
        return web.json_response({"status": "ok", "config": config_payload(config), "metrics": metrics()})

    async def config_handler(request: web.Request) -> web.Response:
        payload, error = await read_json_object(request)
        if error:
            return error
        apply_config_update(config, payload)
        proxy.audit.log("config_updated", {"config": config_payload(config)})
        return web.json_response({"config": config_payload(config)})

    async def events_handler(request: web.Request) -> web.Response:
        return web.json_response({"events": proxy.audit.recent()})

    async def run_demo_analysis(payload: dict[str, Any], request: web.Request | None = None) -> dict[str, Any]:
        started = time.perf_counter()
        messages: list[dict[str, Any]] = [{"role": "user", "content": str(payload.get("user_message", ""))}]
        rag_content = str(payload.get("rag_content", ""))
        if rag_content:
            messages.append({"role": "tool", "content": rag_content})

        original_messages = list(messages)
        detected, processed_messages, layer1_meta = proxy.detector.scan_messages(messages)
        decision = "blocked" if detected and config.block_on_injection else "passed"
        isolation_applied = False
        canary_token = ""

        if decision != "blocked":
            processed_messages, isolation_applied = proxy.isolator.isolate(processed_messages)
            processed_messages, canary_token = proxy.canary.inject(processed_messages)

        ai_output = simulated_ai_output(str(payload.get("user_message", "")), rag_content, decision)
        ai_error = None
        final_safety = "blocked" if decision == "blocked" else "allowed"

        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        return {
            "decision": decision,
            "final_safety": final_safety,
            "latency_ms": latency_ms,
            "layer1": layer1_meta,
            "rag_isolation": isolation_applied,
            "canary_injected": bool(canary_token),
            "original_messages": original_messages,
            "processed_messages": redact_canary(processed_messages, canary_token),
            "ai_output": ai_output,
            "ai_error": ai_error,
            "explanation": (
                "Request blocked before reaching the LLM API."
                if decision == "blocked"
                else "Request would be forwarded after the shown MedGuard transformations."
            ),
        }

    async def demo_analyze_handler(request: web.Request) -> web.Response:
        payload, error = await read_json_object(request)
        if error:
            return error
        result = await run_demo_analysis(payload, request)
        proxy.audit.log(
            "demo_analyze",
            {
                "decision": result["decision"],
                "final_safety": result["final_safety"],
                "latency_ms": result["latency_ms"],
                "layer1_meta": result["layer1"],
                "rag_isolation": result["rag_isolation"],
                "canary_injected": result["canary_injected"],
                "summary": message_summary(result["processed_messages"]),
            },
        )
        return web.json_response(result)

    async def chat_handler(request: web.Request) -> web.StreamResponse:
        return await proxy.handle_chat_completions(request)

    async def health_handler(request: web.Request) -> web.Response:
        return web.json_response(
            {
                "status": "ok",
                "defense_layers": {
                    "layer1_injection_guard": config.injection_guard_enabled,
                    "layer2_rag_isolation": config.rag_isolation_enabled,
                    "layer3_canary": config.canary_enabled,
                },
                "target": config.target_base_url,
            }
        )

    app.router.add_get("/", dashboard_handler)
    app.router.add_get("/dashboard", dashboard_handler)
    app.router.add_get("/api/status", status_handler)
    app.router.add_post("/api/config", config_handler)
    app.router.add_get("/api/events", events_handler)
    app.router.add_post("/api/demo/analyze", demo_analyze_handler)
    app.router.add_post("/v1/chat/completions", chat_handler)
    app.router.add_post("/chat/completions", chat_handler)
    app.router.add_get("/health", health_handler)
    app.router.add_get("/v1/models", proxy.handle_passthrough)
    app.router.add_route("*", "/v1/{path:.*}", proxy.handle_passthrough)
    app.on_cleanup.append(proxy.cleanup)
    return app
