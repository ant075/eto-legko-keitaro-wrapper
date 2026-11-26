import asyncio
from collections.abc import Awaitable, Callable
from time import monotonic
from typing import Any

from app.schemas.reference import ExternalReferenceItem


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


def parse_reference_items(raw: Any, key: str) -> list[dict[str, object]]:
    if isinstance(raw, dict):
        raw = raw.get(key, [])
    if not isinstance(raw, list):
        raise ValueError(f"API учебного стенда вернул некорректный список {key}")
    return [ExternalReferenceItem.model_validate(item).model_dump() for item in raw]


async def search_offers(api_client, query: str) -> list[dict[str, object]]:
    raw_offers = parse_reference_items(
        await reference_cache.get("offers", api_client.list_offers), "offers"
    )
    needle = query.strip().casefold()
    return [
        {"id": item["id"], "name": item["name"]}
        for item in raw_offers
        if needle in str(item["name"]).casefold()
    ]
