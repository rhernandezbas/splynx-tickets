from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate

# Importar todas las constantes desde el archivo centralizado
from app.utils.constants import *





db = SQLAlchemy()
ma = Marshmallow()
migrate = Migrate()


class Config:
    """Configuración de Flask y SQLAlchemy"""
    
    # Usar constantes importadas
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280, 
        'pool_pre_ping': True,
        'connect_args': {
            'charset': 'utf8mb4',
            'use_unicode': True
        }
    }