from flask import Blueprint

api_smart = Blueprint("smart_olt", __name__)

from . import views


