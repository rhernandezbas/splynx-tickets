""" """

import requests
from app_smart_olt.utils.constans import url_base, token_api


class SmartOLTService:
    """ """

    def __init__(self):
        """ """
        self.url = url_base
        self.headers = {
            "X-Token": {token_api},
            "Content-Type": "application/json",
        }


    def get_onu_uncofigured(self)->dict:
        """get onu uncofigured"""

        try:
            url = f"{self.url}/onu/unconfigured_onus"
            headers = self.headers
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            resp = response.json()
            return resp
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            raise
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")
            raise

    def authorize_onu(self, form_data:dict)->dict:
        """authorize onu """


        try:
            url = f"{self.url}/onu/authorize_onu"
            headers = self.headers
            body = {
                "olt_id": "",
                "pon_type": "",
                "board": "",
                "port": "",
                "sn": "",
                "vlan": "245",
                "onu_type": "",
                "zone": "City Centre",
                "odb": "Splitter325",
                "name": "",
                "address_or_comment": "Avenue 9",
                "onu_mode": "Routing",
                "onu_external_id": "test2"
            }

            response = requests.post(url, json=body, headers=headers)
            response.raise_for_status()
            resp = response.json()
            return resp
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            raise
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")
            raise

    def set_onu_ppoe(self, onu_external_id:str, username:str, password:str)->dict:
        """set onu pppoe"""

        try:
            url = f"{self.url}/onu/set_onu_wan_mode_pppoe/{onu_external_id}"
            headers = self.headers
            body = {
                "username": f"{username}",
                "password": f"{password}"
            }
            response = requests.post(url, json=body, headers=headers)
            response.raise_for_status()
            resp = response.json()
            return resp
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            raise
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")
            raise

    def set_onu_wifi(self,onu_external_id:str, wifi_name:str, wifi_password:str)->dict:
        """set onu wifi"""
        try:
            url = f"{self.url}/onu/set_wifi_port_access/{onu_external_id}"
            headers = self.headers
            body = {
                "vlan": "10",
                "dhcp": "No control",
                "ssid": f"{wifi_name}",
                "password": f"{wifi_password}",
                "authentication_mode":"WPA2"}
            response = requests.post(url, json=body, headers=headers)
            response.raise_for_status()
            resp = response.json()
            return resp
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            raise
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")
            raise
