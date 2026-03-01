"""Add notification_sent to ticket_reassignment_history

Revision ID: 919f5a9d12b7
Revises: b2c3d4e5f6a7
Create Date: 2026-03-01 09:34:43.295609

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '919f5a9d12b7'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('ticket_reassignment_history', schema=None) as batch_op:
        batch_op.add_column(sa.Column('notification_sent', sa.Boolean(), nullable=True))


def downgrade():
    with op.batch_alter_table('ticket_reassignment_history', schema=None) as batch_op:
        batch_op.drop_column('notification_sent')
