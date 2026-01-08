"""
Scheduler para tareas programadas
Ejecuta el flujo completo de tickets cada 10 minutos
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import requests
from datetime import datetime
import pytz
import os
import atexit

# Variable global para evitar múltiples schedulers
_scheduler_instance = None
_scheduler_lock_file = '/tmp/splynx_scheduler.lock'


def run_all_flow_job(app):
    """Ejecuta el flujo completo de tickets llamando al endpoint HTTP"""
    
    # Obtener hora actual en Argentina
    tz_argentina = pytz.timezone('America/Argentina/Buenos_Aires')
    now = datetime.now(tz_argentina)
    
    print(f"\n{'='*60}")
    print(f"🕐 CRON JOB INICIADO - {now.strftime('%Y-%m-%d %H:%M:%S')} (Argentina)")
    print(f"🔧 PID: {os.getpid()}")
    print(f"{'='*60}")
    
    try:
        # Llamar al endpoint all_flow
        print("📡 Llamando al endpoint /api/tickets/all_flow...")
        response = requests.post('http://localhost:7842/api/tickets/all_flow', timeout=300)
        
        if response.status_code == 200:
            print("✅ Endpoint all_flow ejecutado exitosamente")
            print(f"📄 Respuesta: {response.json()}")
        else:
            print(f"⚠️ Endpoint all_flow respondió con código: {response.status_code}")
            print(f"📄 Respuesta: {response.text}")
        
        # Llamar al endpoint de asignación de tickets no asignados
        print("\n📡 Llamando al endpoint /api/tickets/assign_unassigned...")
        response_assign = requests.post('http://localhost:7842/api/tickets/assign_unassigned', timeout=300)
        
        if response_assign.status_code == 200:
            print("✅ Endpoint assign_unassigned ejecutado exitosamente")
            print(f"📄 Respuesta: {response_assign.json()}")
        else:
            print(f"⚠️ Endpoint assign_unassigned respondió con código: {response_assign.status_code}")
            print(f"📄 Respuesta: {response_assign.text}")
        
        print(f"\n{'='*60}")
        print(f"✅ CRON JOB COMPLETADO - {datetime.now(tz_argentina).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al llamar al endpoint: {str(e)}")
        print(f"{'='*60}\n")
    except Exception as e:
        print(f"❌ Error en cron job: {str(e)}")
        print(f"{'='*60}\n")


def _cleanup_lock():
    """Limpia el archivo de lock al salir"""
    try:
        if os.path.exists(_scheduler_lock_file):
            os.remove(_scheduler_lock_file)
            print("🧹 Lock file removido")
    except Exception as e:
        print(f"⚠️ Error al remover lock file: {e}")


def init_scheduler(app):
    """Inicializa el scheduler con la tarea programada"""
    global _scheduler_instance
    
    # Verificar si ya existe una instancia
    if _scheduler_instance is not None:
        print("⚠️ Scheduler ya existe en este proceso, omitiendo...")
        return _scheduler_instance
    
    # Verificar lock file para evitar múltiples schedulers entre procesos
    if os.path.exists(_scheduler_lock_file):
        try:
            with open(_scheduler_lock_file, 'r') as f:
                existing_pid = f.read().strip()
            print(f"⚠️ Scheduler ya está corriendo en PID {existing_pid}, omitiendo...")
            return None
        except Exception as e:
            print(f"⚠️ Error leyendo lock file: {e}")
            # Continuar de todas formas
    
    # Crear lock file con el PID actual
    try:
        with open(_scheduler_lock_file, 'w') as f:
            f.write(str(os.getpid()))
        # Registrar limpieza al salir
        atexit.register(_cleanup_lock)
    except Exception as e:
        print(f"⚠️ No se pudo crear lock file: {e}")
    
    scheduler = BackgroundScheduler(timezone='America/Argentina/Buenos_Aires')
    
    # Agregar job que se ejecuta cada 3 minutos
    scheduler.add_job(
        func=lambda: run_all_flow_job(app),
        trigger=IntervalTrigger(minutes=3),
        id='all_flow_job',
        name='Ejecutar all_flow cada 3 minutos',
        replace_existing=True
    )
    
    # Iniciar el scheduler
    scheduler.start()
    _scheduler_instance = scheduler
    
    print("\n" + "="*60)
    print("⏰ SCHEDULER INICIADO")
    print("📋 Tarea: Ejecutar all_flow cada 3 minutos")
    print("🌎 Zona horaria: America/Argentina/Buenos_Aires")
    print(f"🔧 PID: {os.getpid()}")
    print("="*60 + "\n")
    
    # Ejecutar inmediatamente al iniciar
    print("🚀 Ejecutando flujo inicial al arrancar la aplicación...")
    import threading
    threading.Thread(target=lambda: run_all_flow_job(app)).start()
    
    return scheduler
