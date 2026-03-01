"""
Helper para leer configuración del sistema desde la base de datos
"""

from typing import Optional, Union
from app.models.models import SystemConfig
from app.utils.logger import get_logger

logger = get_logger(__name__)

class ConfigHelper:
    """Helper para obtener valores de configuración desde la BD"""
    
    _cache = {}
    
    @staticmethod
    def get_config(key: str, default: Optional[Union[str, int, bool]] = None) -> Union[str, int, bool, None]:
        """
        Obtiene un valor de configuración desde la BD
        
        Args:
            key: Clave de configuración
            default: Valor por defecto si no existe
            
        Returns:
            Valor de configuración convertido al tipo correcto
        """
        # Verificar cache primero
        if key in ConfigHelper._cache:
            return ConfigHelper._cache[key]
        
        try:
            config = SystemConfig.query.filter_by(key=key).first()
            
            if not config:
                logger.warning(f"Configuración '{key}' no encontrada, usando default: {default}")
                return default
            
            # Convertir según el tipo
            value = config.value
            value_type = config.value_type
            
            if value_type == 'int':
                result = int(value)
            elif value_type == 'bool':
                result = value.lower() in ('true', '1', 'yes', 'on')
            elif value_type == 'float':
                result = float(value)
            else:  # string o json
                result = value
            
            # Guardar en cache
            ConfigHelper._cache[key] = result
            return result
            
        except Exception as e:
            logger.error(f"Error obteniendo configuración '{key}': {e}")
            return default
    
    @staticmethod
    def clear_cache():
        """Limpia el cache de configuración"""
        ConfigHelper._cache = {}
    
    @staticmethod
    def get_int(key: str, default: int = 0) -> int:
        """Obtiene un valor entero de configuración"""
        return ConfigHelper.get_config(key, default)
    
    @staticmethod
    def get_bool(key: str, default: bool = False) -> bool:
        """Obtiene un valor booleano de configuración"""
        return ConfigHelper.get_config(key, default)
    
    @staticmethod
    def get_str(key: str, default: str = '') -> str:
        """Obtiene un valor string de configuración"""
        return ConfigHelper.get_config(key, default)
    
    # Métodos de conveniencia para valores específicos
    @staticmethod
    def get_ticket_alert_threshold() -> int:
        """Obtiene el umbral de alerta de tickets en minutos"""
        return ConfigHelper.get_int('TICKET_ALERT_THRESHOLD_MINUTES', 60)
    
    @staticmethod
    def get_ticket_update_threshold() -> int:
        """Obtiene el umbral de actualización de tickets en minutos"""
        return ConfigHelper.get_int('TICKET_UPDATE_THRESHOLD_MINUTES', 60)
    
    @staticmethod
    def get_renotification_interval() -> int:
        """Obtiene el intervalo de renotificación en minutos"""
        return ConfigHelper.get_int('TICKET_RENOTIFICATION_INTERVAL_MINUTES', 60)
    
    @staticmethod
    def get_end_of_shift_notification() -> int:
        """Obtiene los minutos antes del fin de turno para notificar"""
        return ConfigHelper.get_int('END_OF_SHIFT_NOTIFICATION_MINUTES', 60)
    
    @staticmethod
    def get_outhouse_no_alert_minutes() -> int:
        """Obtiene los minutos sin alerta para tickets OutHouse"""
        return ConfigHelper.get_int('OUTHOUSE_NO_ALERT_MINUTES', 120)
    
    @staticmethod
    def get_pre_alert_minutes() -> int:
        """Obtiene los minutos antes del vencimiento para enviar pre-alerta"""
        return ConfigHelper.get_int('TICKET_PRE_ALERT_MINUTES', 15)

    @staticmethod
    def is_whatsapp_enabled() -> bool:
        """Verifica si WhatsApp está habilitado"""
        return ConfigHelper.get_bool('WHATSAPP_ENABLED', True)
