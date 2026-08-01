from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib

from .config import MedGuardConfig


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts)
    return ""


def messages_to_text(messages: list[dict[str, Any]]) -> str:
    rows: list[str] = []
    for message in messages:
        role = str(message.get("role", "unknown"))
        text = _content_to_text(message.get("content", "")).strip()
        if text:
            rows.append(f"{role}: {text}")
    return "\n".join(rows)


class RiskScorer:
    def __init__(self, config: MedGuardConfig):
        self.config = config
        self._model: Any | None = None
        self._load_error: str | None = None

    def _load_model(self) -> Any | None:
        if self._model is not None or self._load_error is not None:
            return self._model

        path = Path(self.config.risk_model_path)
        if not path.exists():
            self._load_error = "model file not found"
            return None

        try:
            self._model = joblib.load(path)
        except Exception as exc:  # pragma: no cover - defensive fallback
            self._load_error = type(exc).__name__
            return None
        return self._model

    def score_text(self, text: str) -> dict[str, Any]:
        if not self.config.risk_model_enabled:
            return {"available": False, "reason": "disabled"}

        model = self._load_model()
        if model is None:
            return {"available": False, "reason": self._load_error or "unavailable"}

        if not text.strip():
            return {"available": True, "risk_score": 0.0, "label": "low_risk", "action": "pass"}

        probability = float(model.predict_proba([text])[0][1])
        score = round(probability, 4)
        if score >= self.config.risk_block_threshold:
            action = "block"
            label = "likely_prompt_injection"
        elif score >= self.config.risk_warn_threshold:
            action = "warn"
            label = "suspicious"
        else:
            action = "pass"
            label = "low_risk"
        return {"available": True, "risk_score": score, "label": label, "action": action}

    def score_messages(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        return self.score_text(messages_to_text(messages))
