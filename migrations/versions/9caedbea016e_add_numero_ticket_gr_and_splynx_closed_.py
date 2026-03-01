"""Add numero_ticket_gr and splynx_closed_at to incidents_detection

Revision ID: 9caedbea016e
Revises: c3d4e5f6a7b8
Create Date: 2026-03-01 13:03:17.418534

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '9caedbea016e'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('tickets_detection', schema=None) as batch_op:
        batch_op.add_column(sa.Column('numero_ticket_gr', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('splynx_closed_at', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('tickets_detection', schema=None) as batch_op:
        batch_op.drop_column('splynx_closed_at')
        batch_op.drop_column('numero_ticket_gr')
