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
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Variable global para evitar múltiples schedulers
_scheduler_instance = None
_scheduler_lock_file = '/tmp/splynx_scheduler.lock'


def run_process_webhooks_job(app):
    """Procesa webhooks pendientes y crea tickets en Splynx llamando al endpoint HTTP"""
    with app.app_context():
        from app.utils.config_helper import ConfigHelper

        # Obtener configuración de horarios desde BD
        FINDE_HORA_INICIO = ConfigHelper.get_int('FINDE_HORA_INICIO', 9)
        FINDE_HORA_FIN = ConfigHelper.get_int('FINDE_HORA_FIN', 21)

    # Obtener hora actual en Argentina
    tz_argentina = pytz.timezone('America/Argentina/Buenos_Aires')
    now = datetime.now(tz_argentina)
    day_of_week = now.weekday()  # 0=Lunes, 6=Domingo
    current_hour = now.hour

    # HORARIO LABORAL: 8 AM - 11 PM (lunes a viernes) / 9 AM - 9 PM (fin de semana)
    if day_of_week >= 5:  # Sábado o Domingo
        if not (FINDE_HORA_INICIO <= current_hour < FINDE_HORA_FIN):
            logger.info(f"FIN DE SEMANA FUERA DE HORARIO ({current_hour}:00) - Saltando ejecución")
            return
    else:  # Lunes a Viernes
        if not (8 <= current_hour < 23):  # 8 AM - 11 PM
            logger.info(f"FUERA DE HORARIO LABORAL ({current_hour}:00) - Saltando ejecución")
            return

    logger.info("="*60)
    logger.info(f"CRON JOB process_webhooks INICIADO - {now.strftime('%Y-%m-%d %H:%M:%S')} (Argentina)")
    logger.info(f"PID: {os.getpid()}")
    logger.info("="*60)

    try:
        logger.info("Llamando al endpoint /api/tickets/process_webhooks...")
        response = requests.post('http://localhost:7842/api/tickets/process_webhooks', timeout=300)

        if response.status_code == 200:
            response_data = response.json()
            logger.info("Endpoint process_webhooks ejecutado exitosamente")
            logger.info(f"Respuesta: {response_data}")
        else:
            logger.error(f"Endpoint process_webhooks FALLO con codigo: {response.status_code}")
            logger.error(f"Respuesta: {response.text}")

        logger.info("="*60)
        logger.info(f"CRON JOB COMPLETADO - {datetime.now(tz_argentina).strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*60)

    except requests.exceptions.RequestException as e:
        logger.error(f"Error al llamar al endpoint: {str(e)}")
        logger.info("="*60)
    except Exception as e:
        logger.error(f"Error en cron job: {str(e)}")
        logger.info("="*60)


def _cleanup_lock():
    """Limpia el archivo de lock al salir"""
    try:
        if os.path.exists(_scheduler_lock_file):
            os.remove(_scheduler_lock_file)
            logger.info("🧹 Lock file removido")
    except Exception as e:
        logger.warning(f"⚠️ Error al remover lock file: {e}")


def init_scheduler(app):
    """Inicializa el scheduler con la tarea programada"""
    global _scheduler_instance
    
    # Verificar si ya existe una instancia
    if _scheduler_instance is not None:
        logger.warning("⚠️ Scheduler ya existe en este proceso, omitiendo...")
        return _scheduler_instance
    
    # Verificar lock file para evitar múltiples schedulers entre procesos
    if os.path.exists(_scheduler_lock_file):
        try:
            with open(_scheduler_lock_file, 'r') as f:
                existing_pid = f.read().strip()
            logger.warning(f"⚠️ Scheduler ya está corriendo en PID {existing_pid}, omitiendo...")
            return None
        except Exception as e:
            logger.warning(f"⚠️ Error leyendo lock file: {e}")
            # Continuar de todas formas
    
    # Crear lock file con el PID actual
    try:
        with open(_scheduler_lock_file, 'w') as f:
            f.write(str(os.getpid()))
        # Registrar limpieza al salir
        atexit.register(_cleanup_lock)
    except Exception as e:
        logger.warning(f"⚠️ No se pudo crear lock file: {e}")
    
    scheduler = BackgroundScheduler(timezone='America/Argentina/Buenos_Aires')
    
    # Agregar job que se ejecuta cada 3 minutos - procesa webhooks y crea tickets
    scheduler.add_job(
        func=lambda: run_process_webhooks_job(app),
        trigger=IntervalTrigger(minutes=3),
        id='process_webhooks_job',
        name='Procesar webhooks cada 3 minutos',
        replace_existing=True
    )
    
    # Agregar job para asignar tickets sin asignar (cada 3 minutos)
    scheduler.add_job(
        func=lambda: requests.post('http://localhost:7842/api/tickets/assign_unassigned'),
        trigger=IntervalTrigger(minutes=3),
        id='assign_unassigned_job',
        name='Asignar tickets sin asignar cada 3 minutos',
        replace_existing=True
    )

    # Agregar job para alertar tickets vencidos (cada 3 minutos)
    scheduler.add_job(
        func=lambda: requests.post('http://localhost:7842/api/tickets/alert_overdue'),
        trigger=IntervalTrigger(minutes=3),
        id='alert_overdue_job',
        name='Alertar tickets vencidos cada 3 minutos',
        replace_existing=True
    )
    
    # Agregar job para notificaciones de fin de turno (cada hora)
    scheduler.add_job(
        func=lambda: requests.post('http://localhost:7842/api/tickets/end_of_shift_notifications'),
        trigger=IntervalTrigger(hours=1),
        id='end_of_shift_notifications_job',
        name='Verificar notificaciones de fin de turno cada hora',
        replace_existing=True
    )
    
    # Agregar job para desasignación automática después de fin de turno (cada 40 minutos)
    scheduler.add_job(
        func=lambda: requests.post('http://localhost:7842/api/tickets/auto_unassign_after_shift'),
        trigger=IntervalTrigger(minutes=40),
        id='auto_unassign_after_shift_job',
        name='Desasignar tickets 1 hora después del fin de turno cada 40 minutos',
        replace_existing=True
    )
    
    # Agregar job para sincronización de estado de tickets con Splynx (cada 5 minutos)
    scheduler.add_job(
        func=lambda: requests.post('http://localhost:7842/api/tickets/sync_status'),
        trigger=IntervalTrigger(minutes=5),
        id='sync_tickets_status_job',
        name='Sincronizar estado de tickets con Splynx cada 5 minutos',
        replace_existing=True
    )
    
    # Agregar job para importar tickets existentes del grupo 4 (cada 5 minutos)
    scheduler.add_job(
        func=lambda: requests.post('http://localhost:7842/api/tickets/import_existing'),
        trigger=IntervalTrigger(minutes=5),
        id='import_existing_tickets_job',
        name='Importar tickets existentes del grupo 4 cada 5 minutos',
        replace_existing=True
    )
    
    # Iniciar el scheduler
    scheduler.start()
    _scheduler_instance = scheduler
    
    logger.info("="*60)
    logger.info("SCHEDULER INICIADO")
    logger.info("Tareas programadas:")
    logger.info("   - process_webhooks cada 3 minutos")
    logger.info("   - Asignacion tickets sin asignar cada 3 minutos (independiente)")
    logger.info("   - Alertas tickets vencidos cada 3 minutos")
    logger.info("   - Notificaciones de fin de turno cada hora")
    logger.info("   - Desasignacion automatica cada 40 minutos")
    logger.info("   - Sincronizacion estado tickets cada 5 minutos")
    logger.info("   - Importacion tickets existentes cada 5 minutos")
    logger.info("Zona horaria: America/Argentina/Buenos_Aires")
    logger.info(f"PID: {os.getpid()}")
    logger.info("="*60)

    # Ejecutar inmediatamente al iniciar
    logger.info("Ejecutando flujo inicial al arrancar la aplicacion...")
    import threading
    threading.Thread(target=lambda: run_process_webhooks_job(app)).start()
    
    return scheduler
