"""Add processed fields to hook_nuevo_ticket and remove legacy GR fields

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    # Add processed tracking columns to hook_nuevo_ticket
    op.add_column('hook_nuevo_ticket', sa.Column('processed', sa.Boolean(), nullable=False, server_default=sa.text('0')))
    op.add_column('hook_nuevo_ticket', sa.Column('processed_at', sa.DateTime(), nullable=True))
    op.create_index('ix_hook_nuevo_ticket_processed', 'hook_nuevo_ticket', ['processed'])

    # Remove legacy Gestion Real fields from tickets_detection
    op.drop_column('tickets_detection', 'is_from_gestion_real')
    op.drop_column('tickets_detection', 'ultimo_contacto_gr')


def downgrade():
    # Restore legacy GR fields
    op.add_column('tickets_detection', sa.Column('ultimo_contacto_gr', sa.DateTime(), nullable=True))
    op.add_column('tickets_detection', sa.Column('is_from_gestion_real', sa.Boolean(), nullable=True, server_default=sa.text('0')))

    # Remove processed columns from hook_nuevo_ticket
    op.drop_index('ix_hook_nuevo_ticket_processed', 'hook_nuevo_ticket')
    op.drop_column('hook_nuevo_ticket', 'processed_at')
    op.drop_column('hook_nuevo_ticket', 'processed')
