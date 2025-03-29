"""total_usd @ transacrions

Revision ID: 3c43736c2980
Revises: 834029a52494
Create Date: 2025-03-29 12:38:37.814100

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c43736c2980'
down_revision: Union[str, None] = '834029a52494'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('transactions', sa.Column('total_usd', sa.Float(), nullable=True))
    op.execute("UPDATE transactions SET total_usd = 1.0")
    op.alter_column('transactions', 'total_usd', existing_type=sa.Float(), nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('transactions', 'total_usd')
    # ### end Alembic commands ###
