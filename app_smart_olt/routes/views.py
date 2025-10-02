"""Views"""

from flask import jsonify
from app_smart_olt.routes import api_smart
from app_smart_olt.services.smart_olt_services import SmartOLTService

@api_smart.route("/get_onu", methods=["GET"])
def get_onu() -> jsonify:
    """get onu"""

    smart_olt = SmartOLTService()
    get_onu_data = smart_olt.get_onu_uncofigured()

    return jsonify(get_onu_data), 200
