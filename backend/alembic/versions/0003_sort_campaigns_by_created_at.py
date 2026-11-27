"""replace campaign sorting index"""

from alembic import op


revision = "0003_campaign_created_idx"
down_revision = "0002_add_sorting_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_campaigns_updated_at", table_name="campaigns")
    op.create_index("ix_campaigns_created_at", "campaigns", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_campaigns_created_at", table_name="campaigns")
    op.create_index("ix_campaigns_updated_at", "campaigns", ["updated_at"])
