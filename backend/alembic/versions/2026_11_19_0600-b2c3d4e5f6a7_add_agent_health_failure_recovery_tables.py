"""add agent health and failure recovery tables and columns

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-11-19 06:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add health and failure metrics columns to 'agents'
    op.add_column('agents', sa.Column('health_status', sa.String(length=50), nullable=False, server_default='HEALTHY'))
    op.add_column('agents', sa.Column('last_heartbeat_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('agents', sa.Column('failed_work_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('agents', sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('agents', sa.Column('total_processing_time_ms', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('agents', sa.Column('last_error_message', sa.Text(), nullable=True))
    op.add_column('agents', sa.Column('is_paused', sa.Boolean(), nullable=False, server_default='false'))
    op.create_index(op.f('ix_agents_health_status'), 'agents', ['health_status'], unique=False)

    # 2. Add recovery tracking columns to 'requests'
    op.add_column('requests', sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('requests', sa.Column('last_recovery_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('requests', sa.Column('recovery_reason', sa.String(length=255), nullable=True))

    # 3. Create 'agent_failures' table
    op.create_table(
        'agent_failures',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('failure_id', sa.String(length=50), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=True),
        sa.Column('agent_code', sa.String(length=50), nullable=True),
        sa.Column('request_id', sa.Integer(), nullable=True),
        sa.Column('request_code', sa.String(length=50), nullable=True),
        sa.Column('failure_type', sa.String(length=100), nullable=False),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.Column('recovery_status', sa.String(length=50), nullable=False, server_default='DETECTED'),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('recovered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['request_id'], ['requests.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_agent_failures_failure_id'), 'agent_failures', ['failure_id'], unique=True)
    op.create_index(op.f('ix_agent_failures_agent_id'), 'agent_failures', ['agent_id'], unique=False)
    op.create_index(op.f('ix_agent_failures_agent_code'), 'agent_failures', ['agent_code'], unique=False)
    op.create_index(op.f('ix_agent_failures_request_id'), 'agent_failures', ['request_id'], unique=False)
    op.create_index(op.f('ix_agent_failures_failure_type'), 'agent_failures', ['failure_type'], unique=False)
    op.create_index(op.f('ix_agent_failures_recovery_status'), 'agent_failures', ['recovery_status'], unique=False)
    op.create_index(op.f('ix_agent_failures_created_at'), 'agent_failures', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('agent_failures')
    op.drop_column('requests', 'recovery_reason')
    op.drop_column('requests', 'last_recovery_at')
    op.drop_column('requests', 'retry_count')
    op.drop_index(op.f('ix_agents_health_status'), table_name='agents')
    op.drop_column('agents', 'is_paused')
    op.drop_column('agents', 'last_error_message')
    op.drop_column('agents', 'total_processing_time_ms')
    op.drop_column('agents', 'retry_count')
    op.drop_column('agents', 'failed_work_count')
    op.drop_column('agents', 'last_heartbeat_at')
    op.drop_column('agents', 'health_status')
