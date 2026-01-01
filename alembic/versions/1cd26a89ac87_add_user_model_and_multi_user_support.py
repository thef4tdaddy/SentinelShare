"""add_user_model_and_multi_user_support

Revision ID: 1cd26a89ac87
Revises: 0d54571c0ed6
Create Date: 2026-01-01 13:35:26.387161

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1cd26a89ac87'
down_revision: Union[str, None] = '0d54571c0ed6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user table
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('forwarding_target_email', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=True)
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)

    # Add user_id to processedemail
    with op.batch_alter_table('processedemail', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_index('ix_processedemail_user_id', ['user_id'], unique=False)
        batch_op.create_foreign_key('fk_processedemail_user_id', 'user', ['user_id'], ['id'])

    # Add user_id to stats
    with op.batch_alter_table('stats', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_index('ix_stats_user_id', ['user_id'], unique=False)
        batch_op.create_foreign_key('fk_stats_user_id', 'user', ['user_id'], ['id'])

    # Add user_id to preference
    with op.batch_alter_table('preference', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_index('ix_preference_user_id', ['user_id'], unique=False)
        batch_op.create_foreign_key('fk_preference_user_id', 'user', ['user_id'], ['id'])

    # Add user_id to manualrule
    with op.batch_alter_table('manualrule', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_index('ix_manualrule_user_id', ['user_id'], unique=False)
        batch_op.create_foreign_key('fk_manualrule_user_id', 'user', ['user_id'], ['id'])

    # Add user_id to learningcandidate
    with op.batch_alter_table('learningcandidate', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_index('ix_learningcandidate_user_id', ['user_id'], unique=False)
        batch_op.create_foreign_key('fk_learningcandidate_user_id', 'user', ['user_id'], ['id'])

    # Add user_id to categoryrule
    with op.batch_alter_table('categoryrule', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_index('ix_categoryrule_user_id', ['user_id'], unique=False)
        batch_op.create_foreign_key('fk_categoryrule_user_id', 'user', ['user_id'], ['id'])

    # Update emailaccount: add user_id, remove unique constraint on email
    with op.batch_alter_table('emailaccount', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_index('ix_emailaccount_user_id', ['user_id'], unique=False)
        batch_op.create_foreign_key('fk_emailaccount_user_id', 'user', ['user_id'], ['id'])
        # Drop unique constraint on email (allows same email for different users)
        batch_op.drop_index('ix_emailaccount_email')
        batch_op.create_index('ix_emailaccount_email', ['email'], unique=False)


def downgrade() -> None:
    # Reverse the changes using batch operations for SQLite compatibility
    
    # EmailAccount: restore unique constraint and remove user_id
    with op.batch_alter_table('emailaccount', schema=None) as batch_op:
        batch_op.drop_index('ix_emailaccount_email')
        batch_op.create_index('ix_emailaccount_email', ['email'], unique=True)
        batch_op.drop_constraint('fk_emailaccount_user_id', type_='foreignkey')
        batch_op.drop_index('ix_emailaccount_user_id')
        batch_op.drop_column('user_id')

    # CategoryRule
    with op.batch_alter_table('categoryrule', schema=None) as batch_op:
        batch_op.drop_constraint('fk_categoryrule_user_id', type_='foreignkey')
        batch_op.drop_index('ix_categoryrule_user_id')
        batch_op.drop_column('user_id')

    # LearningCandidate
    with op.batch_alter_table('learningcandidate', schema=None) as batch_op:
        batch_op.drop_constraint('fk_learningcandidate_user_id', type_='foreignkey')
        batch_op.drop_index('ix_learningcandidate_user_id')
        batch_op.drop_column('user_id')

    # ManualRule
    with op.batch_alter_table('manualrule', schema=None) as batch_op:
        batch_op.drop_constraint('fk_manualrule_user_id', type_='foreignkey')
        batch_op.drop_index('ix_manualrule_user_id')
        batch_op.drop_column('user_id')

    # Preference
    with op.batch_alter_table('preference', schema=None) as batch_op:
        batch_op.drop_constraint('fk_preference_user_id', type_='foreignkey')
        batch_op.drop_index('ix_preference_user_id')
        batch_op.drop_column('user_id')

    # Stats
    with op.batch_alter_table('stats', schema=None) as batch_op:
        batch_op.drop_constraint('fk_stats_user_id', type_='foreignkey')
        batch_op.drop_index('ix_stats_user_id')
        batch_op.drop_column('user_id')

    # ProcessedEmail
    with op.batch_alter_table('processedemail', schema=None) as batch_op:
        batch_op.drop_constraint('fk_processedemail_user_id', type_='foreignkey')
        batch_op.drop_index('ix_processedemail_user_id')
        batch_op.drop_column('user_id')

    # Drop user table
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_table('user')
