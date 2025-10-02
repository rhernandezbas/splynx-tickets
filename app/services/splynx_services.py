"""modul to get splynx services"""

import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning

class SplynxServices:
    """class to get splynx services"""
    
    def __init__(self, verify_ssl=False):
        self.base_url = "https://ipnext.splynx.app"
        self.user = "Ronald"
        self.password = "Ronald2025!"
        
        self.verify_ssl = verify_ssl
        
        # Disable SSL warnings if SSL verification is disabled
        if not self.verify_ssl:
            urllib3.disable_warnings(InsecureRequestWarning)

        self.token = self.login_token()

    
    def login_token(self):
        """login to splynx"""
        
        url = f"{self.base_url}/api/2.0/admin/auth/tokens"
        headers = {
            "Content-Type": "application/json",
        }
        body = {
            "auth_type":"admin",
            "login": self.user,
            "password": self.password
        }
        
        try:
            # Make request with SSL verification setting
            response = requests.post(url, headers=headers, json=body, verify=self.verify_ssl)
            response.raise_for_status()  # Raise an exception for bad status codes
            token = response.json()
            token = token["access_token"]
            return token
        except requests.exceptions.SSLError as e:
            print(f"SSL Error: {e}")
            print("Consider setting verify_ssl=False for development (not recommended for production)")
            raise
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")
            raise

    def search_customer(self, customer_id:str):
        """search customer"""

        token = self.token

        url = f"{self.base_url}/api/2.0/admin/customers/customer/{customer_id}"
        headers = {
            "Authorization": f"Splynx-EA (access_token={token})",
        }
        
        try:
            # Make request with SSL verification setting
            response = requests.get(url, headers=headers, verify=self.verify_ssl)
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()
        except requests.exceptions.SSLError as e:
            print(f"SSL Error: {e}")
            print("Consider setting verify_ssl=False for development (not recommended for production)")
            raise
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")
            raise

    def get_ticket_data_status(self, ticket_id: str):
        """Get the status of a ticket by its ID
        
        Args:
            ticket_id: The ID of the ticket to check
            
        Returns:
            dict: The ticket data if found, None otherwise
        """
        url = f"{self.base_url}/api/2.0/admin/support/tickets/{ticket_id}"
        headers = {
            "Authorization": f"Splynx-EA (access_token={self.token})",
        }
        
        try:
            response = requests.get(url, headers=headers, verify=self.verify_ssl)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"Ticket {ticket_id} not found")
            else:
                print(f"Error checking ticket {ticket_id}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error checking ticket {ticket_id}: {e}")
            return None


    def create_ticket(self, customer_id:str, subject:str, note:str,fecha_creacion, priority:str="medium",
     status_id="1", group_id="4", type_id="10", ):
        """Create a ticket in Splynx with simplified parameters"""

        token = self.token
        
        url = f"{self.base_url}/api/2.0/admin/support/tickets"
        headers = {
            "Authorization": f"Splynx-EA (access_token={token})",
        }
        
        data = {
            'customer_id': str(customer_id),
            'reporter_type': "customer",
            'hidden': "false",
            'assign_to': "0",
            'status_id': str(status_id),
            'group_id': str(group_id),
            'type_id': str(type_id),    
            'subject': subject,
            'priority': priority,
            'star': "false",
            'unread_by_customer': "false",
            'unread_by_admin': "false",
            'closed': "false",
            'created_at': fecha_creacion,    # Dynamic current time
            'updated_at': fecha_creacion,    # Dynamic current time
            'source': "0",
            'shareable': "1",
            'note': note,
            'watching': "13",
            'related_account_id': "0",
            'related_account_type': "main",
            'hidden_from_related_account': "0",
            'unread_by_related_account': "1",
            'lead_id': "0"
        }
        
        
        try:
            # Make request with SSL verification setting using form data
            response = requests.post(url, headers=headers, data=data, verify=self.verify_ssl)
            print(response)
            # Print response details for debugging
            print(f"Status Code: {response.status_code}")
            if response.status_code != 200:
                print(f"Response Text: {response.text}")
            
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            raise
        except requests.exceptions.SSLError as e:
            print(f"SSL Error: {e}")
            print("Consider setting verify_ssl=False for development (not recommended for production)")
            raise
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")
            raise