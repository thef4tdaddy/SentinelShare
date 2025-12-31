"""Add CategoryRule model

Revision ID: b43d7a747ece
Revises: dcf10852d24e
Create Date: 2025-12-30 11:45:15.467053

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b43d7a747ece'
down_revision: Union[str, None] = 'dcf10852d24e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'categoryrule',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('match_type', sa.String(), nullable=False),
        sa.Column('pattern', sa.String(), nullable=False),
        sa.Column('assigned_category', sa.String(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('categoryrule')
