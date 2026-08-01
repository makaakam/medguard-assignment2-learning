from __future__ import annotations

import logging
import re
from typing import Any

from .config import MedGuardConfig

logger = logging.getLogger("medguard_proxy")


_TEXT_KEYS = frozenset(
    {
        "text",
        "content",
        "input_text",
        "output_text",
        "arguments",
        "prompt",
        "query",
        "value",
    }
)
_CONTAINER_KEYS = frozenset(
    {"parts", "items", "blocks", "segments", "messages", "input"}
)
_MAX_CONTENT_DEPTH = 32


def extract_text_content(content: Any) -> str:
    """Collect text from nested chat/multimodal content safely.

    OpenAI-compatible messages may use a string, an array of text/image
    blocks, or provider-specific nested tool/function objects.  Only known
    text-bearing keys are collected, so image URLs and metadata do not become
    detector input.  A depth and cycle guard prevents malformed Python values
    from hanging or overflowing the detector; JSON request bodies cannot have
    cycles, but direct callers can.
    """

    seen: set[int] = set()

    def walk(value: Any, *, text_context: bool, depth: int) -> list[str]:
        if depth > _MAX_CONTENT_DEPTH:
            return []
        if isinstance(value, str):
            return [value] if text_context else []
        if value is None or isinstance(value, (bytes, bytearray, memoryview)):
            return []

        if isinstance(value, (list, tuple)):
            marker = id(value)
            if marker in seen:
                return []
            seen.add(marker)
            parts: list[str] = []
            for item in value:
                parts.extend(walk(item, text_context=text_context, depth=depth + 1))
            return parts

        if isinstance(value, dict):
            marker = id(value)
            if marker in seen:
                return []
            seen.add(marker)
            parts: list[str] = []
            for key, child in value.items():
                if key in _TEXT_KEYS:
                    parts.extend(walk(child, text_context=True, depth=depth + 1))
                elif key in _CONTAINER_KEYS:
                    parts.extend(walk(child, text_context=text_context, depth=depth + 1))
                elif isinstance(child, (dict, list, tuple)):
                    # Unknown wrappers can still contain a recognised text
                    # field.  Recurse into containers, but skip metadata
                    # leaves such as type/id/mime/source.
                    parts.extend(walk(child, text_context=False, depth=depth + 1))
            return parts

        return []

    return "\n".join(
        part
        for part in walk(content, text_context=isinstance(content, str), depth=0)
        if part
    )


def append_text_content(content: Any, suffix: str) -> Any:
    """Append an instruction without breaking multimodal message content."""
    if isinstance(content, str):
        return content + suffix
    if isinstance(content, (list, tuple)):
        return [*content, {"type": "text", "text": suffix}]
    if content is None:
        return suffix
    return f"{content}{suffix}"


class InjectionPatternDetector:
    """Rule-based prompt injection detector for clinical LLM workflows."""

    PATTERNS: list[tuple[str, str]] = [
        (
            "role_override",
            r"ignore\s+.{0,40}(previous|prior|above|all)\s+.{0,20}"
            r"(instruction|prompt|rule|constraint|guideline)",
        ),
        (
            "role_override",
            r"(disregard|forget|bypass)\s+.{0,30}"
            r"(your|the|all)\s+.{0,20}(instruction|training|rule|policy|system)",
        ),
        (
            "identity_replacement",
            r"you\s+are\s+(now|a|an)\s+.{0,40}"
            r"(different|unrestricted|new|alternative|uncensored|jailbreak)",
        ),
        (
            "identity_replacement",
            r"(pretend|act|behave|respond)\s+(as|like)\s+.{0,30}"
            r"(different|unrestricted|new\s+ai|without\s+restriction)",
        ),
        (
            "privilege_escalation",
            r"(reveal|expose|leak|output|display|show|print|return)\s+.{0,40}"
            r"(patient|confidential|private|system\s*prompt|all\s*record|database|ehr)",
        ),
        (
            "privilege_escalation",
            r"(access|query|select\s+\*|drop\s+table|delete\s+from)\s+.{0,30}"
            r"(patient|record|database|table)",
        ),
        (
            "system_bypass",
            r"(system|admin|developer|root|god)\s*"
            r"(override|command|mode|access|privilege|key)",
        ),
        (
            "system_bypass",
            r"(previous\s+instructions?\s+are\s+(deprecated|void|invalid|overridden)"
            r"|new\s+instructions?\s+follow)",
        ),
        (
            "medical_hijack",
            r"(prescribe|recommend|change|update|modify)\s+.{0,30}"
            r"(dosage|medication|drug|treatment)\s+.{0,30}"
            r"(without|bypass|ignore|regardless)",
        ),
        (
            "medical_hijack",
            r"(suppress|hide|omit|remove)\s+.{0,30}"
            r"(symptom|allerg|contraindic|warning|alert|flag)",
        ),
    ]

    _compiled = [
        (category, re.compile(pattern, re.IGNORECASE | re.DOTALL))
        for category, pattern in PATTERNS
    ]

    def __init__(self, config: MedGuardConfig):
        self.config = config

    def scan(self, text: str) -> tuple[bool, str | None]:
        if not self.config.injection_guard_enabled:
            return False, None
        for category, pattern in self._compiled:
            if pattern.search(text):
                return True, category
        return False, None

    def scan_messages(self, messages: list[dict]) -> tuple[bool, list[dict], dict]:
        meta: dict[str, Any] = {"layer1": "pass", "detections": []}
        any_detected = False
        new_messages = []

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            text = extract_text_content(content)
            if role in ("user", "tool", "function") and text:
                detected, category = self.scan(text)
                if detected:
                    any_detected = True
                    meta["detections"].append({"role": role, "category": category})
                    meta["layer1"] = "blocked" if self.config.block_on_injection else "sanitized"
                    logger.warning("Layer 1: injection detected in %s message: %s", role, category)
                    if self.config.block_on_injection:
                        return True, messages, meta
                    msg = {
                        **msg,
                        "content": "[CONTENT REMOVED BY MEDGUARD: injection pattern detected]",
                    }
            new_messages.append(msg)

        return any_detected, new_messages, meta
