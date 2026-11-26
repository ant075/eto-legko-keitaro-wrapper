from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.config import get_settings
from app.db.base import Base


class Campaign(Base):
    __tablename__ = "campaigns"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    alias: Mapped[str | None] = mapped_column(String(255))
    group_id: Mapped[int] = mapped_column(Integer, nullable=False)
    traffic_source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    domain_id: Mapped[int] = mapped_column(Integer, nullable=False)
    redirect_stream_id: Mapped[int] = mapped_column(Integer, nullable=False)
    offers_stream_id: Mapped[int] = mapped_column(Integer, nullable=False)
    country_code: Mapped[str] = mapped_column(ForeignKey("countries.code"), nullable=False)
    is_dirty: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), index=True)
    country = relationship("Country", lazy="joined")
    offers = relationship(
        "CampaignOffer",
        back_populates="campaign",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    publications = relationship(
        "CampaignOfferPublication",
        back_populates="campaign",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def country_name(self) -> str:
        return self.country.name_ru if self.country else self.country_code

    @property
    def redirect_target_url(self) -> str:
        return get_settings().redirect_target_url

