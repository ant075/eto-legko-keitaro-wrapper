import asyncio
from collections.abc import Awaitable, Callable
from time import monotonic
from typing import Any


class ReferenceCache:
    """Процессный TTL-кеш ответов справочников учебного API."""

    TTL_SECONDS = {
        "domains": 60,
        "groups": 60,
        "traffic_sources": 60,
        "offers": 10,
    }

    def __init__(self) -> None:
        self._items: dict[str, tuple[float, Any]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str, loader: Callable[[], Awaitable[Any]]) -> Any:
        now = monotonic()
        cached = self._items.get(key)
        if cached is not None and cached[0] > now:
            return cached[1]

        # Повторная проверка под lock не даёт нескольким запросам одновременно
        # обновлять один и тот же истёкший справочник.
        async with self._lock:
            now = monotonic()
            cached = self._items.get(key)
            if cached is not None and cached[0] > now:
                return cached[1]
            value = await loader()
            ttl = self.TTL_SECONDS[key]
            self._items[key] = (monotonic() + ttl, value)
            return value


reference_cache = ReferenceCache()

