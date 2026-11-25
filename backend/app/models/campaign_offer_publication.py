from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKeyConstraint, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class CampaignOfferPublication(Base):
    __tablename__ = "campaign_offer_publications"
    __table_args__ = (
        ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        ForeignKeyConstraint(["campaign_id", "offer_id"], ["campaign_offers.campaign_id", "campaign_offers.offer_id"], ondelete="CASCADE"),
    )
    campaign_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    offer_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    weight: Mapped[int] = mapped_column(Integer, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    campaign = relationship("Campaign", back_populates="publications")

