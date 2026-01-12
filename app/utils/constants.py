"""
Constantes centralizadas de la aplicación
Todas las configuraciones y constantes deben estar aquí
"""

# ============================================================================
# CONFIGURACIÓN DE SELENIUM / GESTION REAL
# ============================================================================

USUARIO = "RoxZ3008"
CONTRASENA = "RoxZG3008$"
LOGIN_URL = "https://gestionreal.com.ar/login/main_login.php"
CASOS_URL = "https://gestionreal.com.ar/index.php?menuitem=10"

DEPARTAMENTOS_SELENIUM = {
    "Soporte_Tecnico": {
        "nombre_display": "Soporte Tecnico",
        "xpath_grupo": "//li[contains(text(),'Soporte Tecnico')]"
    }
}

DEPARTAMENTOS = {
    "Soporte_Tecnico": "Soporte Técnico",
    #"administracion": "administracion",
    #"Facturacion": "Facturación"
}

# ============================================================================
# CONFIGURACIÓN DE EVOLUTION API / WHATSAPP
# ============================================================================

# Feature flag para habilitar/deshabilitar todas las notificaciones de WhatsApp
# True = Envía notificaciones | False = No envía notificaciones
WHATSAPP_ENABLED = True

# Feature flag para pausar/reanudar el sistema completo
# True = Sistema pausado (no asigna tickets ni procesa) | False = Sistema activo
SYSTEM_PAUSED = False

# IMPORTANTE: Verificar que esta URL sea accesible desde el servidor
# Si hay error de DNS, verificar:
# 1. La URL es correcta
# 2. El servidor tiene acceso a internet
# 3. El dominio está correctamente configurado
EVOLUTION_API_BASE_URL = "https://ipnext-evolution-api.s2vvnr.easypanel.host"
EVOLUTION_API_KEY = "AD11C79C765A-43A2-91ED-555EA96FA07C"
EVOLUTION_INSTANCE_NAME = "test1"

# ============================================================================
# CONFIGURACIÓN DE OPERADORES
# ============================================================================

# Persona de guardia para fin de semana (sábado y domingo)
PERSONA_GUARDIA_FINDE = 10  # Gabriel Romero

# Horario de trabajo en fin de semana (sábado y domingo)
FINDE_HORA_INICIO = 9   # 9:00 AM
FINDE_HORA_FIN = 21     # 9:00 PM

# Mapeo de IDs de personas a números de WhatsApp
PERSON_WHATSAPP_NUMBERS = {
    10: "541159300124",  # Gabriel Romero
    27: "541152596634",  # Luis Sarco
    37: "542324531873",  # Cesareo Suarez
    38: "542324531872"   # Yaini Al
}

"""PERSON_WHATSAPP_NUMBERS = {
    10: "541178547218",  # Gabriel Romero
    27: "541178547218",  # Luis Sarco
    37: "541178547218",  # Cesareo Suarez
    38: "541178547218"   # Yaini Al
}
"""
# Nombres de los operadores
PERSON_NAMES = {
    10: "Gabriel Romero",
    27: "Luis Sarco",
    37: "Cesareo Suarez",
    38: "Yaini Al"
}

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

# Horarios de trabajo de operadores (en formato 24h)
# Formato: {person_id: [{"start": "HH:MM", "end": "HH:MM"}]}
# Lunes a Viernes
OPERATOR_SCHEDULES = {
    10: [  # Gabriel Romero
        {"start": "08:00", "end": "16:00"}   # Turno diurno
    ],
    27: [  # Luis Sarco
        {"start": "10:00", "end": "17:20"}   # Turno único
    ],
    37: [  # Cesareo Suarez
        {"start": "08:00", "end": "15:00"}   # Turno diurno
    ],
    38: [  # Yaini Al
        {"start": "17:00", "end": "23:00"}   # Turno tarde/noche
    ]
}

# ============================================================================
# CONFIGURACIÓN DE ALERTAS Y NOTIFICACIONES
# ============================================================================

# Tiempo límite en minutos para alertar sobre tickets asignados
TICKET_ALERT_THRESHOLD_MINUTES = 45

# Tiempo mínimo desde última actualización para enviar alerta (en minutos)
# Si el ticket fue actualizado hace menos de este tiempo, no se envía alerta
TICKET_UPDATE_THRESHOLD_MINUTES = 45

# Intervalo mínimo entre notificaciones del mismo ticket (en minutos)
# No se volverá a notificar un ticket si ya fue notificado hace menos de este tiempo
TICKET_RENOTIFICATION_INTERVAL_MINUTES = 45

# Minutos antes del fin de turno para enviar notificación de resumen
END_OF_SHIFT_NOTIFICATION_MINUTES = 60  # 1 hora antes

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

DB_USER = "mysql"
DB_PASSWORD = "1234"
DB_HOST = "190.7.234.37"
DB_PORT = "3025"
DB_NAME = "ipnext"
