"""populate_stable_coin_column_with_dai

Revision ID: 3ac5b0baed62
Revises: 485bde7869a2
Create Date: 2025-04-03 07:39:46.340297

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3ac5b0baed62"
down_revision: Union[str, None] = "485bde7869a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "UPDATE transactions SET stable_coin = 'dai' WHERE stable_coin IS NULL OR stable_coin = ''"
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
