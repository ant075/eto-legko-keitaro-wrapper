import os
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass, field

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("API_KEY", "test-key")
os.environ.setdefault("API_BASE_URL", "https://training-api.test/admin_api/v1")
os.environ.setdefault("REDIRECT_TARGET_URL", "https://google.com")
os.environ.setdefault("DATABASE_URL", "sqlite://")

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Campaign, CampaignOffer, CampaignOfferPublication, Country


@dataclass
class FakeTrainingApi:
    campaigns: list[dict] = field(default_factory=list)
    streams: dict[int, dict] = field(default_factory=dict)
    offers: dict[int, dict] = field(default_factory=dict)
    calls: list[tuple[str, str, dict | None]] = field(default_factory=list)
    next_campaign_id: int = 100
    next_stream_id: int = 200
    fail: set[str] = field(default_factory=set)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return None

    def _check(self, operation: str) -> None:
        if operation in self.fail:
            from app.integrations.training_api import TrainingApiError

            raise TrainingApiError(500, f"fake failure: {operation}")

    async def create_campaign(self, payload):
        self._check("create_campaign")
        campaign = {"id": self.next_campaign_id, "alias": "test-alias", **payload}
        self.next_campaign_id += 1
        self.campaigns.append(campaign)
        self.calls.append(("POST", "/campaigns", payload))
        return campaign

    async def list_campaigns(self, *, offset=0, limit=100):
        self._check("list_campaigns")
        self.calls.append(("GET", "/campaigns", {"offset": offset, "limit": limit}))
        return self.campaigns[offset:offset + limit]

    async def get_campaign_streams(self, campaign_id):
        self._check("get_campaign_streams")
        self.calls.append(("GET", f"/campaigns/{campaign_id}/streams", None))
        return [stream for stream in self.streams.values() if stream.get("campaign_id") == campaign_id]

    async def delete_campaign(self, campaign_id):
        self._check("delete_campaign")
        self.calls.append(("DELETE", f"/campaigns/{campaign_id}", None))
        self.campaigns[:] = [item for item in self.campaigns if item["id"] != campaign_id]

    async def create_stream(self, payload):
        self._check("create_stream")
        stream_id = self.next_stream_id
        self.next_stream_id += 1
        self.streams[stream_id] = {"id": stream_id, **payload}
        self.calls.append(("POST", "/streams", payload))
        return {"id": stream_id}

    async def get_stream(self, stream_id):
        self._check("get_stream")
        self.calls.append(("GET", f"/streams/{stream_id}", None))
        return self.streams[stream_id]

    async def update_stream(self, stream_id, payload):
        self._check("update_stream")
        self.calls.append(("PUT", f"/streams/{stream_id}", payload))
        self.streams.setdefault(stream_id, {"id": stream_id}).update(payload)

    async def get_offer(self, offer_id):
        self._check("get_offer")
        self.calls.append(("GET", f"/offers/{offer_id}", None))
        return self.offers[offer_id]

    async def list_offers(self):
        self._check("list_offers")
        self.calls.append(("GET", "/offers", None))
        return list(self.offers.values())


@pytest.fixture
def fake_api(monkeypatch) -> FakeTrainingApi:
    api = FakeTrainingApi(
        offers={
            11: {"id": 11, "name": "Alpha offer"},
            12: {"id": 12, "name": "Beta offer"},
            13: {"id": 13, "name": "Gamma offer"},
        }
    )

    class FakeClient:
        def __new__(cls, *args, **kwargs):
            return api

    monkeypatch.setattr("app.services.campaigns.TrainingApiClient", FakeClient)
    monkeypatch.setattr("app.services.offers.TrainingApiClient", FakeClient)
    return api


@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, connection_record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def db_session(db_engine) -> Iterator[Session]:
    factory = sessionmaker(bind=db_engine, expire_on_commit=False)
    with factory() as session:
        session.add(Country(code="GM", name_ru="Гамбия"))
        session.commit()
        yield session


@pytest.fixture
def campaign(db_session: Session) -> Campaign:
    campaign = Campaign(
        id=1,
        name="Test campaign",
        alias="test-campaign",
        group_id=2,
        traffic_source_id=3,
        domain_id=4,
        redirect_stream_id=201,
        offers_stream_id=202,
        country_code="GM",
        is_dirty=False,
    )
    campaign.offers.append(CampaignOffer(
        campaign_id=1, offer_id=11, name="Alpha offer", weight=100,
        is_pinned=False, is_deleted=False, position=1,
    ))
    campaign.publications.append(CampaignOfferPublication(
        campaign_id=1, offer_id=11, name="Alpha offer", weight=100,
        is_deleted=False, position=1,
    ))
    db_session.add(campaign)
    db_session.commit()
    return campaign


@pytest_asyncio.fixture
async def client(db_engine) -> AsyncIterator[AsyncClient]:
    factory = sessionmaker(bind=db_engine, expire_on_commit=False)

    def override_get_db():
        with factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.clear()


