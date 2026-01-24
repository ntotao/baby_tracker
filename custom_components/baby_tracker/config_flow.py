"""Config flow for Baby Tracker integration."""
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_TELEGRAM_TOKEN, CONF_ALLOWED_CHAT_IDS

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_TELEGRAM_TOKEN): str,
    vol.Required(CONF_ALLOWED_CHAT_IDS, default=""): str,
})

class BabyTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Baby Tracker."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate token
            token = user_input[CONF_TELEGRAM_TOKEN]
            if not token or ":" not in token:
                 errors["base"] = "invalid_auth"
            else:
                return self.async_create_entry(title="Baby Tracker Bot", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "telegram_token_desc": "Got from @BotFather",
                "allowed_ids_desc": "Comma separated IDs (get from @userinfobot)"
            }
        )
