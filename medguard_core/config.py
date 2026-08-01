from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MedGuardConfig:
    target_base_url: str = "https://api.openai.com/v1"
    port: int = 8081
    host: str = "127.0.0.1"

    injection_guard_enabled: bool = True
    block_on_injection: bool = True

    rag_isolation_enabled: bool = True
    rag_min_length: int = 150
    rag_open_tag: str = "<UNTRUSTED_MEDICAL_DATA>"
    rag_close_tag: str = "</UNTRUSTED_MEDICAL_DATA>"

    canary_enabled: bool = True

    risk_model_enabled: bool = True
    risk_model_path: str = "./models/risk_scorer.joblib"
    risk_block_threshold: float = 0.85
    risk_warn_threshold: float = 0.60

    audit_enabled: bool = True
    audit_log_path: str = "./logs/audit.jsonl"

    upstream_timeout_seconds: float = 30.0
    # Optional server-side credential for Dashboard live-analysis mode. It is
    # deliberately excluded from config_payload so it never reaches the UI.
    upstream_api_key: str | None = None
    upstream_model: str | None = None


def config_payload(config: MedGuardConfig) -> dict:
    return {
        "target_base_url": config.target_base_url,
        "host": config.host,
        "port": config.port,
        "injection_guard_enabled": config.injection_guard_enabled,
        "rag_isolation_enabled": config.rag_isolation_enabled,
        "canary_enabled": config.canary_enabled,
        "risk_model_enabled": config.risk_model_enabled,
        "block_on_injection": config.block_on_injection,
        "mode": "block" if config.block_on_injection else "sanitize",
        "rag_min_length": config.rag_min_length,
        "risk_block_threshold": config.risk_block_threshold,
        "risk_warn_threshold": config.risk_warn_threshold,
        "upstream_model": config.upstream_model,
    }


def apply_config_update(config: MedGuardConfig, payload: dict) -> None:
    for field in (
        "injection_guard_enabled",
        "rag_isolation_enabled",
        "canary_enabled",
        "risk_model_enabled",
        "block_on_injection",
    ):
        if field in payload:
            setattr(config, field, bool(payload[field]))

    if payload.get("mode") in ("block", "sanitize"):
        config.block_on_injection = payload["mode"] == "block"

    if "rag_min_length" in payload:
        try:
            config.rag_min_length = max(0, int(payload["rag_min_length"]))
        except (TypeError, ValueError):
            pass

    for field in ("risk_block_threshold", "risk_warn_threshold"):
        if field in payload:
            try:
                value = float(payload[field])
                if 0.0 <= value <= 1.0:
                    setattr(config, field, value)
            except (TypeError, ValueError):
                pass
