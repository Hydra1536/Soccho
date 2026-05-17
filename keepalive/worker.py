import logging
import os
import random
import threading
import time
from typing import List
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx


logging.basicConfig(
    level=os.getenv("KEEPALIVE_LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s keepalive %(message)s",
)
logger = logging.getLogger(__name__)


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in {"/health", "/healthz", "/"}:
            body = b'{"status":"ok"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, _format, *_args):
        return


def _start_port_health_server_if_needed() -> None:
    port_raw = os.getenv("PORT", "").strip()
    if not port_raw:
        return

    try:
        port = int(port_raw)
    except ValueError:
        logger.warning("invalid PORT value=%s, health server disabled", port_raw)
        return

    server = ThreadingHTTPServer(("0.0.0.0", port), _HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info("health server started on port=%s", port)


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
    _start_port_health_server_if_needed()
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
