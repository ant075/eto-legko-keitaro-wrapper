"""add indexes for sorting"""

from alembic import op


revision = "0002_add_sorting_indexes"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_campaigns_updated_at", "campaigns", ["updated_at"])
    op.create_index("ix_countries_name_ru", "countries", ["name_ru"])


def downgrade() -> None:
    op.drop_index("ix_countries_name_ru", table_name="countries")
    op.drop_index("ix_campaigns_updated_at", table_name="campaigns")
