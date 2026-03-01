"""Add pre_alert_sent_at to incidents_detection

Revision ID: c3d4e5f6a7b8
Revises: a9ff15ba0f87
Create Date: 2026-03-01 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'a9ff15ba0f87'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('tickets_detection', schema=None) as batch_op:
        batch_op.add_column(sa.Column('pre_alert_sent_at', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('tickets_detection', schema=None) as batch_op:
        batch_op.drop_column('pre_alert_sent_at')
