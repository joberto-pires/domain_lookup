import json
import os
import httpx
from app.config import settings

class ProviderError(Exception):
    def __init__(self, message, http_status=None, retryable=False):
        super().__init__(message)
        self.http_status = http_status
        self.retryable = retryable

MOCK_SEQUENCE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "example_com_sequence.json")

def _load_mock_sequence():
    with open(MOCK_SEQUENCE_PATH) as f:
        return json.load(f)

def _mock_fetch(domain: str) -> list[str]:
    import redis as redis_lib
    r = redis_lib.from_url(settings.redis_url, decode_responses=True)
    key = f"mock:{domain}:index"
    idx = r.incr(key) - 1
    sequence = _load_mock_sequence()
    if idx >= len(sequence):
        return []
    entry = sequence[idx]
    if entry["type"] == "error":
        raise ProviderError(entry["message"], retryable=entry.get("retryable", False))
    return entry["hostnames"]

def fetch_hostnames(domain: str) -> list[str]:
    if settings.mock_mode:
        return _mock_fetch(domain)

    url = f"{settings.provider_base_url}?domain={domain}"
    try:
        resp = httpx.get(url, timeout=settings.http_timeout)
    except httpx.TimeoutException:
        raise ProviderError("Provider timeout", retryable=True)

    if resp.status_code >= 500:
        raise ProviderError(f"Provider HTTP {resp.status_code}", http_status=resp.status_code, retryable=True)
    if resp.status_code >= 400:
        raise ProviderError(f"Provider HTTP {resp.status_code}", http_status=resp.status_code, retryable=False)

    try:
        data = resp.json()
        return data.get("hostnames", [])
    except (json.JSONDecodeError, AttributeError):
        raise ProviderError("Malformed provider payload", retryable=False)
