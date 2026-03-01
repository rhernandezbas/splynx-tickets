"""
Singleton version of SplynxServices to avoid multiple logins
"""

import os
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from app.utils.logger import get_logger
from threading import Lock

logger = get_logger(__name__)


class SplynxServicesSingleton:
    """
    Singleton class for Splynx services.
    Ensures only one instance exists and reuses the authentication token.
    Thread-safe implementation.
    """

    _instance = None
    _lock = Lock()

    def __new__(cls, verify_ssl=None):
        """Thread-safe singleton pattern"""
        if cls._instance is None:
            with cls._lock:
                # Double-checked locking
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, verify_ssl=None):
        """Initialize only once"""
        if self._initialized:
            return

        self.base_url = os.getenv('SPLYNX_BASE_URL', 'https://splynx.ipnext.com.ar')
        self.user = os.getenv('SPLYNX_USER')
        self.password = os.getenv('SPLYNX_PASSWORD')

        # SSL verification: use env var, fallback to parameter, then default to True
        if verify_ssl is None:
            self.verify_ssl = os.getenv('SPLYNX_SSL_VERIFY', 'True').lower() == 'true'
        else:
            self.verify_ssl = verify_ssl

        self.token = None
        self._token_lock = Lock()

        # Disable SSL warnings if SSL verification is disabled
        if not self.verify_ssl:
            urllib3.disable_warnings(InsecureRequestWarning)
            logger.warning("⚠️ SSL verification is disabled. This is insecure for production!")

        # Get initial token
        self.token = self.login_token()
        self._initialized = True

        logger.info("🔐 SplynxServicesSingleton initialized (singleton)")

    def login_token(self):
        """
        Login to Splynx and get authentication token.
        Thread-safe token refresh.
        """
        with self._token_lock:
            url = f"{self.base_url}/api/2.0/admin/auth/tokens"
            headers = {
                "Content-Type": "application/json",
            }
            body = {
                "auth_type": "admin",
                "login": self.user,
                "password": self.password
            }

            try:
                response = requests.post(url, headers=headers, json=body, verify=self.verify_ssl, timeout=10)
                response.raise_for_status()
                token_data = response.json()
                token = token_data["access_token"]
                logger.info("✅ Splynx token obtained successfully")
                return token
            except requests.exceptions.SSLError as e:
                logger.error(f"SSL Error: {e}")
                logger.warning("Consider setting verify_ssl=False for development")
                raise
            except requests.exceptions.RequestException as e:
                logger.error(f"Request Error during login: {e}")
                raise

    def _refresh_token_if_needed(self, response):
        """Check if token expired and refresh if needed"""
        if response.status_code == 401:
            logger.warning("⚠️ Token expired, refreshing...")
            self.token = self.login_token()
            return True
        return False

    def _make_request(self, method, url, **kwargs):
        """
        Generic request method with automatic token refresh.

        Args:
            method: HTTP method ('get', 'post', 'put', 'delete')
            url: Full URL for the request
            **kwargs: Additional arguments for requests

        Returns:
            Response object or None if error
        """
        headers = kwargs.get('headers', {})
        headers["Authorization"] = f"Splynx-EA (access_token={self.token})"
        kwargs['headers'] = headers
        kwargs['verify'] = self.verify_ssl
        kwargs.setdefault('timeout', 30)

        try:
            response = getattr(requests, method)(url, **kwargs)

            # Check if token expired and retry once
            if self._refresh_token_if_needed(response):
                headers["Authorization"] = f"Splynx-EA (access_token={self.token})"
                response = getattr(requests, method)(url, **kwargs)

            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error ({method.upper()} {url}): {e}")
            raise

    def search_customer(self, customer_id: str):
        """Search customer by ID"""
        url = f"{self.base_url}/api/2.0/admin/customers/customer/{customer_id}"
        response = self._make_request('get', url)
        return response.json() if response else None

    def get_ticket_data_status(self, ticket_id: str):
        """Get the status of a ticket by its ID"""
        url = f"{self.base_url}/api/2.0/admin/support/tickets/{ticket_id}"

        try:
            response = self._make_request('get', url)
            return response.json() if response else None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Ticket {ticket_id} not found")
            else:
                logger.error(f"Error checking ticket {ticket_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error checking ticket {ticket_id}: {e}")
            return None

    def get_unassigned_tickets(self, group_id="4"):
        """Get all unassigned tickets from a specific group, excluding closed tickets"""
        url = f"{self.base_url}/api/2.0/admin/support/tickets"
        params = {
            "group_id": group_id,
            "assign_to": "0"
        }

        try:
            response = self._make_request('get', url, params=params)
            all_tickets = response.json() if response else []

            # Filter open tickets
            filtered_tickets = [
                ticket for ticket in all_tickets
                if ticket.get('closed') not in ['1', 1]
                and ticket.get('assign_to') in [0, '0']
                and str(ticket.get('group_id')) == str(group_id)
            ]

            logger.info(f"✅ Found {len(filtered_tickets)} unassigned tickets (open) from {len(all_tickets)} total in group {group_id}")
            return filtered_tickets
        except Exception as e:
            logger.error(f"❌ Error getting unassigned tickets: {e}")
            return []

    def get_assigned_tickets(self, group_id="4"):
        """Get all assigned tickets from a specific group, excluding closed tickets"""
        url = f"{self.base_url}/api/2.0/admin/support/tickets"
        params = {"group_id": group_id}

        try:
            response = self._make_request('get', url, params=params)
            all_tickets = response.json() if response else []

            filtered_tickets = [
                ticket for ticket in all_tickets
                if ticket.get('closed') not in ['1', 1]
                and ticket.get('assign_to') not in [0, '0', None, '']
                and str(ticket.get('group_id')) == str(group_id)
            ]

            logger.info(f"✅ Found {len(filtered_tickets)} assigned tickets (open) from {len(all_tickets)} total in group {group_id}")
            return filtered_tickets
        except Exception as e:
            logger.error(f"❌ Error getting assigned tickets: {e}")
            return []

    def update_ticket_assignment(self, ticket_id: str, assigned_to: int):
        """Update the assignment of a ticket"""
        url = f"{self.base_url}/api/2.0/admin/support/tickets/{ticket_id}"
        data = {"assign_to": str(assigned_to)}

        try:
            response = self._make_request('put', url, data=data)

            if response and response.status_code in [200, 201, 202, 204]:
                logger.info(f"✅ Ticket {ticket_id} assigned to person {assigned_to}")

                if response.status_code == 202:
                    return {"success": True, "ticket_id": ticket_id, "assigned_to": assigned_to}

                try:
                    if response.text and response.text.strip():
                        return response.json()
                    else:
                        return {"success": True, "ticket_id": ticket_id, "assigned_to": assigned_to}
                except (ValueError, Exception):
                    return {"success": True, "ticket_id": ticket_id, "assigned_to": assigned_to}

            return None

        except Exception as e:
            logger.error(f"❌ Error assigning ticket {ticket_id}: {e}")
            return None

    def create_ticket(self, customer_id: str, subject: str, note: str, fecha_creacion,
                     priority: str = "medium", status_id="1", group_id="4",
                     type_id="10", assigned_to: int = 0):
        """Create a ticket in Splynx"""
        url = f"{self.base_url}/api/2.0/admin/support/tickets"

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
            'created_at': fecha_creacion,
            'updated_at': fecha_creacion,
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
            response = self._make_request('post', url, data=data)
            logger.info(f"Status Code: {response.status_code}")

            if response.status_code != 200:
                logger.warning(f"Response Text: {response.text}")

            return response.json() if response else None

        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            raise

    def reopen_ticket(self, ticket_id: str):
        """Reopen a closed ticket in Splynx by setting closed=0 and status_id=1"""
        url = f"{self.base_url}/api/2.0/admin/support/tickets/{ticket_id}"
        data = {"closed": "0", "status_id": "1"}

        try:
            response = self._make_request('put', url, data=data)

            if response and response.status_code in [200, 201, 202, 204]:
                logger.info(f"✅ Ticket {ticket_id} reabierto en Splynx")
                return {"success": True, "ticket_id": ticket_id}

            return None

        except Exception as e:
            logger.error(f"❌ Error reabriendo ticket {ticket_id}: {e}")
            return None

    @classmethod
    def reset_instance(cls):
        """Reset singleton instance (useful for testing)"""
        with cls._lock:
            cls._instance = None
            logger.info("🔄 SplynxServicesSingleton instance reset")
