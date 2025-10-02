"""Config"""

from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from app_smart_olt.utils.constans import db_user, db_pass, db_endpoint, db_schema

db = SQLAlchemy()
ma = Marshmallow()


class Config:
    db_user = db_user
    db_pass = db_pass
    db_endpoint = db_endpoint
    db_schema = db_schema

    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{db_user}:{db_pass}@{db_endpoint}/{db_schema}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_recycle': 1800,  # Recicla las conexiones después de 30 min (1800 segundos)
                                 'pool_size': 20,  # Mantén un máximo de 20 conexiones abiertas simultáneamente
                                 'max_overflow': 20,  # Permite abrir hasta 20 conexiones adicionales si el pool está
                                 # lleno
                                 'pool_timeout': 30,  # Espera 30 segundos para obtener una conexión del pool
                                 'pool_pre_ping': True,  # Verifica si la conexión está viva antes de usarla
                                 }
