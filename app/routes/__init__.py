from flask import Blueprint

blueprint = Blueprint("routes", __name__)

from . import views
