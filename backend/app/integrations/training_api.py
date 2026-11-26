from collections.abc import Mapping
from types import TracebackType
from typing import Any, Self

import httpx

from app.core.config import get_settings


class TrainingApiError(RuntimeError):
    """Ошибка запроса к API учебного стенда."""

    def __init__(self, status_code: int, message: str, response_body: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class TrainingApiClient:
    """Минимальный адаптер фактически поддержанного API учебного стенда."""

    def __init__(self, client: httpx.AsyncClient | None = None):
        settings = get_settings()
        self._client = client or httpx.AsyncClient(
            base_url=settings.api_base_url.rstrip("/"),
            headers={"Api-Key": settings.api_key},
            timeout=20.0,
        )
        self._owns_client = client is None

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
    ) -> Any:
        try:
            response = await self._client.request(method, path, params=params, json=json)
        except httpx.HTTPError as exc:
            raise TrainingApiError(0, f"API учебного стенда недоступен: {exc}") from exc

        if response.is_error:
            try:
                body = response.json()
            except ValueError:
                body = response.text
            raise TrainingApiError(
                response.status_code,
                f"API учебного стенда вернул HTTP {response.status_code}",
                body,
            )

        if not response.content:
            return None
        return response.json()

    async def create_campaign(self, payload: Mapping[str, Any]) -> Any:
        return await self._request("POST", "/campaigns", json=dict(payload))

    async def delete_campaign(self, campaign_id: int) -> Any:
        return await self._request("DELETE", f"/campaigns/{campaign_id}")

    async def create_stream(self, payload: Mapping[str, Any]) -> Any:
        return await self._request("POST", "/streams", json=dict(payload))

    async def get_stream(self, stream_id: int) -> Any:
        return await self._request("GET", f"/streams/{stream_id}")

    async def update_stream(self, stream_id: int, payload: Mapping[str, Any]) -> Any:
        return await self._request("PUT", f"/streams/{stream_id}", json=dict(payload))

    async def list_offers(self) -> Any:
        return await self._request("GET", "/offers")

    async def get_offer(self, offer_id: int) -> Any:
        return await self._request("GET", f"/offers/{offer_id}")

    async def list_groups(self) -> Any:
        return await self._request("GET", "/groups", params={"type": "campaigns"})

    async def list_domains(self) -> Any:
        return await self._request("GET", "/domains")

    async def list_traffic_sources(self) -> Any:
        return await self._request("GET", "/traffic_sources")

