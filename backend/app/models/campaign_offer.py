from sqlalchemy import Boolean, ForeignKeyConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class CampaignOffer(Base):
    __tablename__ = "campaign_offers"
    __table_args__ = (ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),)
    campaign_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    offer_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    weight: Mapped[int] = mapped_column(Integer, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    campaign = relationship("Campaign", back_populates="offers")

