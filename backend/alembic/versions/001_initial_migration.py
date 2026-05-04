"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'intel_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('url', sa.String(length=1000), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=True),
        sa.Column('is_processed', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_intel_items_id'), 'intel_items', ['id'], unique=False)
    op.create_index(op.f('ix_intel_items_url'), 'intel_items', ['url'], unique=True)
    op.create_index(op.f('ix_intel_items_source'), 'intel_items', ['source'], unique=False)
    op.create_index(op.f('ix_intel_items_severity'), 'intel_items', ['severity'], unique=False)
    op.create_index(op.f('ix_intel_items_is_processed'), 'intel_items', ['is_processed'], unique=False)
    op.create_index(op.f('ix_intel_items_published_at'), 'intel_items', ['published_at'], unique=False)

    op.create_table(
        'daily_briefs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('summary_md', sa.Text(), nullable=True),
        sa.Column('top_cves', sa.JSON(), nullable=True),
        sa.Column('threat_themes', sa.JSON(), nullable=True),
        sa.Column('recommendations_md', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_daily_briefs_id'), 'daily_briefs', ['id'], unique=False)
    op.create_index(op.f('ix_daily_briefs_date'), 'daily_briefs', ['date'], unique=True)

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('receive_digest', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('digest_time', sa.Time(), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subscriptions_id'), 'subscriptions', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_subscriptions_id'), table_name='subscriptions')
    op.drop_table('subscriptions')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_daily_briefs_date'), table_name='daily_briefs')
    op.drop_index(op.f('ix_daily_briefs_id'), table_name='daily_briefs')
    op.drop_table('daily_briefs')
    op.drop_index(op.f('ix_intel_items_published_at'), table_name='intel_items')
    op.drop_index(op.f('ix_intel_items_is_processed'), table_name='intel_items')
    op.drop_index(op.f('ix_intel_items_severity'), table_name='intel_items')
    op.drop_index(op.f('ix_intel_items_source'), table_name='intel_items')
    op.drop_index(op.f('ix_intel_items_url'), table_name='intel_items')
    op.drop_index(op.f('ix_intel_items_id'), table_name='intel_items')
    op.drop_table('intel_items')
