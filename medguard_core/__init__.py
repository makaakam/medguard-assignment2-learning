"""MedGuard proxy package."""

from .config import MedGuardConfig
from .proxy import create_app

__all__ = ["MedGuardConfig", "create_app"]
