"""
Constantes centralizadas de la aplicación
Todas las configuraciones y constantes deben estar aquí
"""

import os

# ============================================================================
# CONFIGURACIÓN DE EVOLUTION API / WHATSAPP
# ============================================================================

# IMPORTANTE: Verificar que esta URL sea accesible desde el servidor
# Si hay error de DNS, verificar:
# 1. La URL es correcta
# 2. El servidor tiene acceso a internet
# 3. El dominio está correctamente configurado
EVOLUTION_API_BASE_URL = os.getenv('EVOLUTION_API_BASE_URL')
EVOLUTION_API_KEY = os.getenv('EVOLUTION_API_KEY')
EVOLUTION_INSTANCE_NAME = os.getenv('EVOLUTION_INSTANCE_NAME')

# ============================================================================
# CONFIGURACIÓN DE OPERADORES
# ============================================================================

# NOTA: Los siguientes valores ahora se leen desde la base de datos:
# - WHATSAPP_ENABLED → ConfigHelper.is_whatsapp_enabled()
# - SYSTEM_PAUSED → SystemControl.is_paused()
# - PERSONA_GUARDIA_FINDE → ConfigHelper.get_int('PERSONA_GUARDIA_FINDE')
# - FINDE_HORA_INICIO/FIN → ConfigHelper.get_int()
# - PERSON_WHATSAPP_NUMBERS → OperatorConfig.whatsapp_number
# - PERSON_NAMES → OperatorConfig.name
# Usar el panel de administración para modificar estos valores.

# IDs de personas asignables
ASSIGNABLE_PERSONS = [10, 27, 37, 38]

# Asignación por turnos según etiquetas en notas
# [TT] = Turno Tarde
TURNO_TARDE_IDS = [27, 38]  # Luis Sarco, Yaini Al

# [TD] = Turno Día
TURNO_DIA_IDS = [10, 37]  # Gabriel Romero, Cesareo Suarez

# ============================================================================
# HORARIOS DE TRABAJO
# ============================================================================

# NOTA: Los horarios de operadores ahora se leen desde la BD:
# - OPERATOR_SCHEDULES → ScheduleHelper.get_operator_schedules()
# - Tabla: operator_schedule
# - Tipos: 'work' (horario laboral), 'assignment' (asignación), 'alert' (notificaciones)
# Usar el panel de administración para modificar horarios.

# ============================================================================
# CONFIGURACIÓN DE ALERTAS Y NOTIFICACIONES
# ============================================================================

# NOTA: Los siguientes valores ahora se leen desde la BD usando ConfigHelper:
# - TICKET_ALERT_THRESHOLD_MINUTES → ConfigHelper.get_ticket_alert_threshold()
# - TICKET_UPDATE_THRESHOLD_MINUTES → ConfigHelper.get_ticket_update_threshold()
# - TICKET_RENOTIFICATION_INTERVAL_MINUTES → ConfigHelper.get_renotification_interval()
# - END_OF_SHIFT_NOTIFICATION_MINUTES → ConfigHelper.get_end_of_shift_notification()
# - OUTHOUSE_NO_ALERT_MINUTES → ConfigHelper.get_outhouse_no_alert_minutes()
# Usar el panel de administración para modificar estos valores.

# ============================================================================
# CONFIGURACIÓN DE ESTADOS DE TICKETS
# ============================================================================

# Estado "OutHouse" - tickets en este estado no alertan (tiempo configurable en BD)
OUTHOUSE_STATUS_ID = "6"

# ============================================================================
# CONFIGURACIÓN DE SPLYNX
# ============================================================================

# ID del grupo de Soporte Técnico en Splynx
SPLYNX_SUPPORT_GROUP_ID = "4"

# ============================================================================
# CONFIGURACIÓN DE ZONA HORARIA
# ============================================================================

TIMEZONE = "America/Argentina/Buenos_Aires"

# ============================================================================
# CONFIGURACIÓN DE BASE DE DATOS
# ============================================================================

DB_HOST = os.getenv('DB_HOST', '190.7.234.37')
DB_PORT = os.getenv('DB_PORT', '3025')
DB_NAME = os.getenv('DB_NAME', 'ipnext')
DB_USER = os.getenv('DB_USER', 'mysql')
DB_PASSWORD = os.getenv('DB_PASSWORD', '1234')

DEVICE_ANALYSIS_API_URL = os.getenv('DEVICE_ANALYSIS_API_URL', 'http://190.7.234.37:7444')
