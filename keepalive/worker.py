import logging
import os
import random
import time
from typing import List

import httpx


logging.basicConfig(
    level=os.getenv("KEEPALIVE_LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s keepalive %(message)s",
)
logger = logging.getLogger(__name__)


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _default_targets() -> str:
    return ",".join(
        [
            "https://soccho-gateway.onrender.com/healthz",
            "https://soccho-auth.onrender.com/api/auth/health/",
            "https://soccho-social.onrender.com/health/",
            "https://soccho-transaction.onrender.com/health/",
            "https://soccho-notification.onrender.com/health/",
        ]
    )


def _targets_from_env() -> List[str]:
    raw_targets = os.getenv("KEEPALIVE_TARGETS", _default_targets())
    targets = [item.strip() for item in raw_targets.split(",") if item.strip()]
    if not targets:
        raise ValueError("KEEPALIVE_TARGETS must include at least one URL")
    return targets


def _probe_target(client: httpx.Client, url: str) -> None:
    try:
        response = client.get(url)
    except httpx.RequestError as exc:
        logger.warning("probe failed url=%s error_type=%s message=%s", url, type(exc).__name__, str(exc))
        return

    if response.status_code >= 500:
        logger.warning("probe unhealthy url=%s status=%s", url, response.status_code)
    else:
        logger.info("probe ok url=%s status=%s", url, response.status_code)


def run() -> None:
    enabled = _env_bool("KEEPALIVE_ENABLED", True)
    interval_seconds = float(os.getenv("KEEPALIVE_INTERVAL_SECONDS", "600"))
    timeout_seconds = float(os.getenv("KEEPALIVE_TIMEOUT_SECONDS", "15"))
    jitter_seconds = max(0.0, float(os.getenv("KEEPALIVE_JITTER_SECONDS", "0")))
    targets = _targets_from_env()

    logger.info(
        "worker boot enabled=%s interval_seconds=%s timeout_seconds=%s jitter_seconds=%s targets=%s",
        enabled,
        interval_seconds,
        timeout_seconds,
        jitter_seconds,
        len(targets),
    )

    if interval_seconds <= 0:
        raise ValueError("KEEPALIVE_INTERVAL_SECONDS must be greater than zero")

    with httpx.Client(timeout=timeout_seconds, follow_redirects=False) as client:
        while True:
            cycle_start = time.monotonic()
            if enabled:
                for target in targets:
                    _probe_target(client, target)
                target_delay = interval_seconds + random.uniform(0, jitter_seconds)
                elapsed = time.monotonic() - cycle_start
                delay = max(0.0, target_delay - elapsed)
            else:
                logger.info("worker idle because KEEPALIVE_ENABLED=false")
                delay = 60.0
            time.sleep(delay)


if __name__ == "__main__":
    run()
