from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate

# Configuración de Selenium-Gr
USUARIO = "RoxZ3008"
CONTRASENA = "RoxZG3008$"
LOGIN_URL = "https://gestionreal.com.ar/login/main_login.php"
CASOS_URL = "https://gestionreal.com.ar/index.php?menuitem=10"
DEPARTAMENTOS_selenium = {
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





db = SQLAlchemy()
ma = Marshmallow()
migrate = Migrate()


class Config:

    DB_USER = "mysql"
    DB_PASSWORD = "1234"
    DB_HOST = "190.7.234.37"
    DB_PORT = "3025"
    DB_NAME = "ipnext"

    # Use connect_args to specify authentication options
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