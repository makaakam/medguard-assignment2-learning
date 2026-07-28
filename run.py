from __future__ import annotations

import argparse
import logging

from aiohttp import web

from medguard_core import MedGuardConfig, create_app

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
logger = logging.getLogger("medguard_proxy")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="MedGuard Proxy - prompt injection defense for clinical LLM agents"
    )
    parser.add_argument("--target", default="https://api.openai.com/v1", help="Target LLM API base URL")
    parser.add_argument("--port", type=int, default=8081)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--audit-log", default="./logs/audit.jsonl")
    parser.add_argument("--no-injection-guard", action="store_true", help="Disable Layer 1")
    parser.add_argument("--no-rag-isolation", action="store_true", help="Disable Layer 2")
    parser.add_argument("--no-canary", action="store_true", help="Disable Layer 3")
    parser.add_argument("--sanitize", action="store_true", help="Sanitize injections instead of blocking")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    config = MedGuardConfig(
        target_base_url=args.target,
        port=args.port,
        host=args.host,
        audit_log_path=args.audit_log,
        injection_guard_enabled=not args.no_injection_guard,
        rag_isolation_enabled=not args.no_rag_isolation,
        canary_enabled=not args.no_canary,
        block_on_injection=not args.sanitize,
    )

    logger.info("=" * 60)
    logger.info("MedGuard Proxy starting")
    logger.info("  Dashboard : http://localhost:%d/dashboard", config.port)
    logger.info("  Base URL  : http://localhost:%d/v1", config.port)
    logger.info("  Target API: %s", config.target_base_url)
    logger.info("  Layer 1   : %s", "ON" if config.injection_guard_enabled else "OFF")
    logger.info("  Layer 2   : %s", "ON" if config.rag_isolation_enabled else "OFF")
    logger.info("  Layer 3   : %s", "ON" if config.canary_enabled else "OFF")
    logger.info("=" * 60)

    web.run_app(create_app(config), host=config.host, port=config.port, print=None)


if __name__ == "__main__":
    main()
