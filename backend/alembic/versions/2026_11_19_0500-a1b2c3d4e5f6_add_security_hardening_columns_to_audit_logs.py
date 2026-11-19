"""add security hardening columns to audit_logs

Revision ID: a1b2c3d4e5f6
Revises: dfc3e44c585f
Create Date: 2026-11-19 05:00:00.000000+00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'dfc3e44c585f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('audit_logs', sa.Column('event_id', sa.String(length=50), nullable=True))
    op.create_index(op.f('ix_audit_logs_event_id'), 'audit_logs', ['event_id'], unique=True)
    op.add_column('audit_logs', sa.Column('request_id', sa.String(length=50), nullable=True))
    op.create_index(op.f('ix_audit_logs_request_id'), 'audit_logs', ['request_id'], unique=False)
    op.add_column('audit_logs', sa.Column('outcome', sa.String(length=50), server_default='SUCCESS', nullable=True))
    op.create_index(op.f('ix_audit_logs_outcome'), 'audit_logs', ['outcome'], unique=False)
    op.add_column('audit_logs', sa.Column('source_ip', sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column('audit_logs', 'source_ip')
    op.drop_index(op.f('ix_audit_logs_outcome'), table_name='audit_logs')
    op.drop_column('audit_logs', 'outcome')
    op.drop_index(op.f('ix_audit_logs_request_id'), table_name='audit_logs')
    op.drop_column('audit_logs', 'request_id')
    op.drop_index(op.f('ix_audit_logs_event_id'), table_name='audit_logs')
    op.drop_column('audit_logs', 'event_id')
