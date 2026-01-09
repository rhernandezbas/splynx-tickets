"""
Simple script to run database migrations programmatically.
"""

from app import create_app
from app.utils.config import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Modificar la columna Fecha_Creacion para que sea VARCHAR(100)
    try:
        db.session.execute(text("ALTER TABLE tickets_detection MODIFY COLUMN Fecha_Creacion VARCHAR(100)"))
        db.session.commit()
        print("Columna Fecha_Creacion actualizada a VARCHAR(100)")
    except Exception as e:
        print(f"Error al modificar la columna Fecha_Creacion: {e}")
        db.session.rollback()
    
    # Agregar columna assigned_to a tickets_detection si no existe
    try:
        db.session.execute(text("ALTER TABLE tickets_detection ADD COLUMN assigned_to INTEGER"))
        db.session.commit()
        print("Columna assigned_to agregada a tickets_detection")
    except Exception as e:
        print(f"Info: assigned_to ya existe o error: {e}")
        db.session.rollback()
    
    # Agregar columna Cliente_Nombre a tickets_detection si no existe
    try:
        db.session.execute(text("ALTER TABLE tickets_detection ADD COLUMN Cliente_Nombre VARCHAR(200)"))
        db.session.commit()
        print("Columna Cliente_Nombre agregada a tickets_detection")
    except Exception as e:
        print(f"Info: Cliente_Nombre ya existe o error: {e}")
        db.session.rollback()
    
    # Crear o actualizar todas las tablas basadas en los modelos
    # Esto creará automáticamente la tabla ticket_response_metrics si no existe
    db.create_all()
    print("Database tables created/updated successfully!")
    print("✅ Tabla ticket_response_metrics creada para métricas de tiempo de respuesta")
    
    # Agregar constraint UNIQUE a ticket_id si no existe
    try:
        # Verificar si el constraint ya existe
        result = db.session.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.table_constraints 
            WHERE table_name = 'ticket_response_metrics' 
            AND constraint_type = 'UNIQUE' 
            AND constraint_name LIKE '%ticket_id%'
        """))
        constraint_exists = result.scalar() > 0
        
        if not constraint_exists:
            db.session.execute(text("ALTER TABLE ticket_response_metrics ADD UNIQUE (ticket_id)"))
            db.session.commit()
            print("✅ Constraint UNIQUE agregado a ticket_id en ticket_response_metrics")
        else:
            print("ℹ️  Constraint UNIQUE ya existe en ticket_id")
    except Exception as e:
        print(f"Info: Error al agregar constraint UNIQUE (puede que ya exista): {e}")
        db.session.rollback()
    
    # Inicializar trackers para las personas asignables
    from app.interface.interfaces import AssignmentTrackerInterface
    assignable_persons = [10, 27, 37, 38]
    
    for person_id in assignable_persons:
        existing = AssignmentTrackerInterface.get_by_person_id(person_id)
        if not existing:
            AssignmentTrackerInterface.create(person_id)
            print(f"Tracker creado para persona ID: {person_id}")
        else:
            print(f"Tracker ya existe para persona ID: {person_id}")
    
    print("Migration completed successfully!")
