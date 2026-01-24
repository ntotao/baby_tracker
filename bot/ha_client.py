import requests
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class HomeAssistantClient:
    def __init__(self, url, token):
        self.url = url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def check_connection(self):
        """Checks if we can reach the API."""
        try:
            response = requests.get(f"{self.url}/api/", headers=self.headers, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Connection check failed: {e}")
            return False

    def get_state(self, entity_id):
        """Gets the state object of an entity."""
        try:
            response = requests.get(f"{self.url}/api/states/{entity_id}", headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get state for {entity_id}: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error getting state for {entity_id}: {e}")
            return None

    def call_service(self, domain, service, service_data=None):
        """Calls a service in Home Assistant."""
        try:
            endpoint = f"{self.url}/api/services/{domain}/{service}"
            response = requests.post(endpoint, headers=self.headers, json=service_data or {})
            
            if response.status_code in [200, 201]:
                logger.debug(f"Service call {domain}.{service} successful.")
                return True
            else:
                logger.error(f"Service call failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Function call_service failed: {e}")
            return False

    def update_date_time_now(self, entity_id):
        """Sets an input_datetime to now."""
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return self.call_service("input_datetime", "set_datetime", {
            "entity_id": entity_id,
            "datetime": now_str
        })
    
    def update_date_time_custom(self, entity_id, dt_obj: datetime):
        """Sets an input_datetime to a custom datetime."""
        dt_str = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
        return self.call_service("input_datetime", "set_datetime", {
            "entity_id": entity_id,
            "datetime": dt_str
        })

    def set_value(self, entity_id, value):
        """Sets a value for input_number or input_text."""
        domain = entity_id.split('.')[0]
        return self.call_service(domain, "set_value", {
            "entity_id": entity_id,
            "value": value
        })

    def increment_counter(self, entity_id):
        """Increments a counter."""
        return self.call_service("counter", "increment", {"entity_id": entity_id})
