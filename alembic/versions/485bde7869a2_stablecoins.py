"""stablecoins

Revision ID: 485bde7869a2
Revises: 3c43736c2980
Create Date: 2025-04-01 22:45:52.271651

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "485bde7869a2"
down_revision: Union[str, None] = "3c43736c2980"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "transactions", sa.Column("stable_coin", sa.String(length=8), nullable=False)
    )

    # Create the tokens table (add this part)
    op.create_table(
        "tokens",
        sa.Column("name", sa.String(8), primary_key=True),
        sa.Column("is_stable", sa.Boolean(), nullable=False),
    )

    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("transactions", "stable_coin")

    op.drop_table("tokens")
    # ### end Alembic commands ###
