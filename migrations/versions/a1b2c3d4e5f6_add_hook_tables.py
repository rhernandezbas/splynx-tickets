"""Add hook_nuevo_ticket and hook_cierre_ticket tables

Revision ID: a1b2c3d4e5f6
Revises: f0fb571414ca
Create Date: 2026-02-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'a8c2d4e6f0b1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'hook_nuevo_ticket',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('nombre_empresa', sa.String(200), nullable=True),
        sa.Column('numero_ticket', sa.Integer(), nullable=True),
        sa.Column('fecha_creado', sa.String(50), nullable=True),
        sa.Column('departamento', sa.String(200), nullable=True),
        sa.Column('canal_entrada', sa.String(100), nullable=True),
        sa.Column('motivo_contacto', sa.String(200), nullable=True),
        sa.Column('numero_cliente', sa.String(100), nullable=True),
        sa.Column('numero_whatsapp', sa.String(50), nullable=True),
        sa.Column('nombre_usuario', sa.String(200), nullable=True),
        sa.Column('received_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'hook_cierre_ticket',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('nombre_empresa', sa.String(200), nullable=True),
        sa.Column('numero_ticket', sa.Integer(), nullable=True),
        sa.Column('fecha_creado', sa.String(50), nullable=True),
        sa.Column('fecha_cerrado', sa.String(50), nullable=True),
        sa.Column('asignado', sa.String(200), nullable=True),
        sa.Column('descripcion_cierre', sa.Text(), nullable=True),
        sa.Column('motivo', sa.String(200), nullable=True),
        sa.Column('tiempo_vida_ticket', sa.String(100), nullable=True),
        sa.Column('tiempo_trabajo_real', sa.String(100), nullable=True),
        sa.Column('tiempo_reaccion', sa.String(100), nullable=True),
        sa.Column('departamento', sa.String(200), nullable=True),
        sa.Column('canal_entrada', sa.String(100), nullable=True),
        sa.Column('motivo_contacto', sa.String(200), nullable=True),
        sa.Column('numero_cliente', sa.String(100), nullable=True),
        sa.Column('numero_whatsapp', sa.String(50), nullable=True),
        sa.Column('nombre_usuario', sa.String(200), nullable=True),
        sa.Column('received_at', sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table('hook_cierre_ticket')
    op.drop_table('hook_nuevo_ticket')
