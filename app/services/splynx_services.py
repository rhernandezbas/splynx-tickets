"""modul to get splynx services"""

import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning

class SplynxServices:
    """class to get splynx services"""
    
    def __init__(self, verify_ssl=False):
        self.base_url = "https://splynx.ipnext.com.ar"
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

    def get_unassigned_tickets(self, group_id="4"):
        """Get all unassigned tickets from a specific group, excluding closed tickets
        
        Args:
            group_id: Group ID to filter tickets (default "4" for Soporte Tecnico)
            
        Returns:
            list: List of unassigned tickets (not closed)
        """
        url = f"{self.base_url}/api/2.0/admin/support/tickets"
        headers = {
            "Authorization": f"Splynx-EA (access_token={self.token})",
        }
        
        # Parámetros para filtrar tickets no asignados del grupo de Soporte
        params = {
            "group_id": group_id,
            "assign_to": "0"  # 0 significa no asignado
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, verify=self.verify_ssl)
            response.raise_for_status()
            all_tickets = response.json()
            
            # Filtrar tickets que:
            # 1. No estén cerrados (closed != "1")
            # 2. No tengan asignación (assign_to == 0 o "0")
            filtered_tickets = [
                ticket for ticket in all_tickets 
                if ticket.get('closed') not in ['1', 1]
                and ticket.get('assign_to') in [0, '0']
            ]
            
            print(f"✅ Encontrados {len(filtered_tickets)} tickets sin asignar (abiertos) de {len(all_tickets)} totales en grupo {group_id}")
            return filtered_tickets
        except requests.exceptions.RequestException as e:
            print(f"❌ Error obteniendo tickets no asignados: {e}")
            return []

    def update_ticket_assignment(self, ticket_id: str, assigned_to: int):
        """Update the assignment of a ticket
        
        Args:
            ticket_id: ID of the ticket to update
            assigned_to: Person ID to assign the ticket to
            
        Returns:
            dict: Response from API or None if error
        """
        url = f"{self.base_url}/api/2.0/admin/support/tickets/{ticket_id}"
        headers = {
            "Authorization": f"Splynx-EA (access_token={self.token})",
        }
        
        data = {
            "assign_to": str(assigned_to)
        }
        
        try:
            response = requests.put(url, headers=headers, data=data, verify=self.verify_ssl)
            response.raise_for_status()
            print(f"✅ Ticket {ticket_id} asignado a persona {assigned_to}")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error asignando ticket {ticket_id}: {e}")
            return None


    def create_ticket(self, customer_id:str, subject:str, note:str,fecha_creacion, priority:str="medium",
     status_id="1", group_id="4", type_id="10", assigned_to:int=0):
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
            'assign_to': str(assigned_to),
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