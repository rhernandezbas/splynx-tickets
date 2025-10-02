"""
Simple script to run database migrations programmatically.
"""

from app import create_app
from app.utils.config import db
import os
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Modificar la columna Fecha_Creacion para que sea VARCHAR(100)
    try:
        # Primero intentamos alterar la tabla directamente
        db.session.execute(text("ALTER TABLE tickets_detection MODIFY COLUMN Fecha_Creacion VARCHAR(100)"))
        db.session.commit()
        print("Columna Fecha_Creacion actualizada a VARCHAR(100)")
    except Exception as e:
        print(f"Error al modificar la columna: {e}")
        db.session.rollback()
        
    # Crear o actualizar todas las tablas basadas en los modelos
    db.create_all()
    print("Database tables created/updated successfully!")
