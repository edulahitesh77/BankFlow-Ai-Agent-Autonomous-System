"""add branches and federation events tables and request federation columns

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-11-19 07:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func
import hashlib


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create 'branches' table
    branches_table = op.create_table(
        'branches',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('branch_id', sa.String(length=50), nullable=False),
        sa.Column('branch_name', sa.String(length=100), nullable=False),
        sa.Column('location', sa.String(length=150), nullable=False),
        sa.Column('branch_status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('api_endpoint', sa.String(length=255), nullable=True),
        sa.Column('database_name', sa.String(length=100), nullable=True),
        sa.Column('api_key_hash', sa.String(length=255), nullable=False),
        sa.Column('is_gateway_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_branches_branch_id'), 'branches', ['branch_id'], unique=True)
    op.create_index(op.f('ix_branches_branch_status'), 'branches', ['branch_status'], unique=False)

    # 2. Create 'federation_events' table
    op.create_table(
        'federation_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('federation_event_id', sa.String(length=100), nullable=False),
        sa.Column('source_branch_id', sa.String(length=50), nullable=False),
        sa.Column('destination_branch_id', sa.String(length=50), nullable=False),
        sa.Column('request_id', sa.String(length=50), nullable=True),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('requested_scope', sa.String(length=100), nullable=False),
        sa.Column('authorization_result', sa.String(length=50), nullable=False),
        sa.Column('correlation_id', sa.String(length=100), nullable=False),
        sa.Column('event_status', sa.String(length=50), nullable=False),
        sa.Column('request_payload', sa.JSON(), nullable=True),
        sa.Column('response_payload', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.String(length=255), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_federation_events_federation_event_id'), 'federation_events', ['federation_event_id'], unique=True)
    op.create_index(op.f('ix_federation_events_source_branch_id'), 'federation_events', ['source_branch_id'], unique=False)
    op.create_index(op.f('ix_federation_events_destination_branch_id'), 'federation_events', ['destination_branch_id'], unique=False)
    op.create_index(op.f('ix_federation_events_correlation_id'), 'federation_events', ['correlation_id'], unique=False)
    op.create_index(op.f('ix_federation_events_authorization_result'), 'federation_events', ['authorization_result'], unique=False)
    op.create_index(op.f('ix_federation_events_timestamp'), 'federation_events', ['timestamp'], unique=False)

    # 3. Add federation columns to 'requests'
    op.add_column('requests', sa.Column('branch_id', sa.String(length=50), nullable=False, server_default='BLR001'))
    op.add_column('requests', sa.Column('origin_branch_id', sa.String(length=50), nullable=True))
    op.add_column('requests', sa.Column('requires_federation', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('requests', sa.Column('federation_status', sa.String(length=50), nullable=True))
    op.create_index(op.f('ix_requests_branch_id'), 'requests', ['branch_id'], unique=False)

    # 4. Seed the three fictional bank branches
    def hash_key(key: str) -> str:
        return hashlib.sha256(key.encode('utf-8')).hexdigest()

    op.bulk_insert(
        branches_table,
        [
            {
                'branch_id': 'BLR001',
                'branch_name': 'Bengaluru',
                'location': 'Bengaluru, Karnataka',
                'branch_status': 'ACTIVE',
                'api_endpoint': 'http://localhost:8000/api/branches/BLR001',
                'database_name': 'bankflow_ai_blr',
                'api_key_hash': hash_key('blr_fed_key_2026_secret'),
                'is_gateway_enabled': True,
            },
            {
                'branch_id': 'CHE001',
                'branch_name': 'Chennai',
                'location': 'Chennai, Tamil Nadu',
                'branch_status': 'ACTIVE',
                'api_endpoint': 'http://localhost:8000/api/branches/CHE001',
                'database_name': 'bankflow_ai_che',
                'api_key_hash': hash_key('che_fed_key_2026_secret'),
                'is_gateway_enabled': True,
            },
            {
                'branch_id': 'HYD001',
                'branch_name': 'Hyderabad',
                'location': 'Hyderabad, Telangana',
                'branch_status': 'ACTIVE',
                'api_endpoint': 'http://localhost:8000/api/branches/HYD001',
                'database_name': 'bankflow_ai_hyd',
                'api_key_hash': hash_key('hyd_fed_key_2026_secret'),
                'is_gateway_enabled': True,
            },
        ]
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_requests_branch_id'), table_name='requests')
    op.drop_column('requests', 'federation_status')
    op.drop_column('requests', 'requires_federation')
    op.drop_column('requests', 'origin_branch_id')
    op.drop_column('requests', 'branch_id')

    op.drop_table('federation_events')
    op.drop_table('branches')
