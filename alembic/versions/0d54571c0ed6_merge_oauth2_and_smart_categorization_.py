"""merge oauth2 and smart categorization migrations

Revision ID: 0d54571c0ed6
Revises: b43d7a747ece, cccecf203051
Create Date: 2025-12-31 15:16:36.845767

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0d54571c0ed6'
down_revision: Union[str, None] = ('b43d7a747ece', 'cccecf203051')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
