"""
Scheduler para tareas programadas
Ejecuta el flujo completo de tickets cada 10 minutos
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import requests
from datetime import datetime
import pytz


def run_all_flow_job(app):
    """Ejecuta el flujo completo de tickets llamando al endpoint HTTP"""
    
    # Obtener hora actual en Argentina
    tz_argentina = pytz.timezone('America/Argentina/Buenos_Aires')
    now = datetime.now(tz_argentina)
    
    print(f"\n{'='*60}")
    print(f"🕐 CRON JOB INICIADO - {now.strftime('%Y-%m-%d %H:%M:%S')} (Argentina)")
    print(f"{'='*60}")
    
    try:
        # Llamar al endpoint all_flow
        print("📡 Llamando al endpoint /api/tickets/all_flow...")
        response = requests.post('http://localhost:7842/api/tickets/all_flow', timeout=300)
        
        if response.status_code == 200:
            print("✅ Endpoint ejecutado exitosamente")
            print(f"📄 Respuesta: {response.json()}")
        else:
            print(f"⚠️ Endpoint respondió con código: {response.status_code}")
            print(f"📄 Respuesta: {response.text}")
        
        print(f"{'='*60}")
        print(f"✅ CRON JOB COMPLETADO - {datetime.now(tz_argentina).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al llamar al endpoint: {str(e)}")
        print(f"{'='*60}\n")
    except Exception as e:
        print(f"❌ Error en cron job: {str(e)}")
        print(f"{'='*60}\n")


def init_scheduler(app):
    """Inicializa el scheduler con la tarea programada"""
    scheduler = BackgroundScheduler(timezone='America/Argentina/Buenos_Aires')
    
    # Agregar job que se ejecuta cada 10 minutos
    scheduler.add_job(
        func=lambda: run_all_flow_job(app),
        trigger=IntervalTrigger(minutes=10),
        id='all_flow_job',
        name='Ejecutar all_flow cada 10 minutos',
        replace_existing=True
    )
    
    # Iniciar el scheduler
    scheduler.start()
    
    print("\n" + "="*60)
    print("⏰ SCHEDULER INICIADO")
    print("📋 Tarea: Ejecutar all_flow cada 10 minutos")
    print("🌎 Zona horaria: America/Argentina/Buenos_Aires")
    print("="*60 + "\n")
    
    # Ejecutar inmediatamente al iniciar
    print("🚀 Ejecutando flujo inicial al arrancar la aplicación...")
    import threading
    threading.Thread(target=lambda: run_all_flow_job(app)).start()
    
    return scheduler
