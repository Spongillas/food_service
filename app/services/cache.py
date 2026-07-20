import time
from typing import Any


class TTLCache:
    """Простой in-memory кэш с TTL, чтобы не дёргать AI повторно на одинаковые запросы."""

    def __init__(self, ttl_seconds: int = 3600):
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[float, Any]] = {}

    @staticmethod
    def make_key(*parts: str) -> str:
        return "|".join(p.strip().lower() for p in parts)

    def get(self, key: str) -> Any | None:
        item = self._store.get(key)
        if item is None:
            return None
        expires_at, value = item
        if time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (time.time() + self._ttl, value)


search_cache = TTLCache(ttl_seconds=3600)
