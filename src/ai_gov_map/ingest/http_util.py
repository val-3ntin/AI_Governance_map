"""Small HTTP helpers shared by source adapters."""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 45
DEFAULT_HEADERS = {
    "User-Agent": "AI-Gov-Map/0.1 (+https://github.com/val-3ntin/AI_Governance_map; research ingest)",
    "Accept": "*/*",
}


class HttpError(RuntimeError):
    """Raised when an HTTP request ultimately fails."""


def get_text(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    retries: int = 3,
    backoff: float = 2.0,
    session: requests.Session | None = None,
) -> tuple[str, requests.Response]:
    """GET ``url`` with retries; return ``(text, response)``."""
    sess = session or requests.Session()
    merged = {**DEFAULT_HEADERS, **(headers or {})}
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            resp = sess.get(url, params=params, headers=merged, timeout=timeout)
            if resp.status_code == 429 and attempt < retries:
                wait = backoff * attempt * 2
                logger.warning("HTTP 429 from %s; sleeping %.1fs", url, wait)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.text, resp
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < retries:
                wait = backoff * attempt
                logger.warning(
                    "Request failed (%s) attempt %s/%s; sleeping %.1fs",
                    exc,
                    attempt,
                    retries,
                    wait,
                )
                time.sleep(wait)
                continue
            raise HttpError(f"GET failed for {url}: {exc}") from exc
    raise HttpError(f"GET failed for {url}: {last_exc}")


def get_bytes(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    retries: int = 3,
    backoff: float = 2.0,
    session: requests.Session | None = None,
) -> tuple[bytes, requests.Response]:
    text, resp = get_text(
        url,
        params=params,
        headers=headers,
        timeout=timeout,
        retries=retries,
        backoff=backoff,
        session=session,
    )
    return resp.content if resp.content else text.encode("utf-8"), resp
