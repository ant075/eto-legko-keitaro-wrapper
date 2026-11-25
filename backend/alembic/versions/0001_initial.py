"""initial schema"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("countries", sa.Column("code", sa.String(2), primary_key=True), sa.Column("name_ru", sa.String(255), nullable=False))
    op.create_table("campaigns",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(255), nullable=False),
        sa.Column("alias", sa.String(255)), sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("traffic_source_id", sa.Integer(), nullable=False), sa.Column("domain_id", sa.Integer(), nullable=False),
        sa.Column("redirect_stream_id", sa.Integer(), nullable=False), sa.Column("offers_stream_id", sa.Integer(), nullable=False),
        sa.Column("country_code", sa.String(2), sa.ForeignKey("countries.code"), nullable=False),
        sa.Column("is_dirty", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()))
    op.create_table("campaign_offers",
        sa.Column("campaign_id", sa.Integer(), nullable=False), sa.Column("offer_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False), sa.Column("weight", sa.Integer(), nullable=False),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("campaign_id", "offer_id"))
    op.create_table("campaign_offer_publications",
        sa.Column("campaign_id", sa.Integer(), nullable=False), sa.Column("offer_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False), sa.Column("weight", sa.Integer(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["campaign_id", "offer_id"], ["campaign_offers.campaign_id", "campaign_offers.offer_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("campaign_id", "offer_id"))


def downgrade() -> None:
    op.drop_table("campaign_offer_publications")
    op.drop_table("campaign_offers")
    op.drop_table("campaigns")
    op.drop_table("countries")

