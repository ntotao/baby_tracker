import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)
DOMAIN = "baby_tracker"
CONF_TELEGRAM_ID = "telegram_id"

class BabyTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Baby Tracker."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            # Validate input (optional: check connection)
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        data_schema = vol.Schema({
            vol.Required(CONF_HOST, default="http://192.168.1.X:8000"): str,
            vol.Required(CONF_TELEGRAM_ID): int,
            vol.Optional(CONF_NAME, default="Baby Tracker"): str,
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )
