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


async def search_offers(api_client, query: str) -> list[dict[str, object]]:
    raw_offers = await reference_cache.get("offers", api_client.list_offers)
    if isinstance(raw_offers, dict):
        raw_offers = raw_offers.get("offers", [])
    needle = query.strip().casefold()
    return [
        {"id": item.get("id", item.get("offer_id")), "name": item.get("name", "")}
        for item in raw_offers
        if item.get("id", item.get("offer_id")) is not None
           and needle in str(item.get("name", "")).casefold()
    ]
