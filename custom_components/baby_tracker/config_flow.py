"""Config flow for Baby Tracker integration."""
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_TELEGRAM_TOKEN, CONF_ALLOWED_CHAT_IDS, CONF_BABY_NAME

_LOGGER = logging.getLogger(__name__)

# Schema for initial setup
DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_TELEGRAM_TOKEN): str,
    vol.Required(CONF_ALLOWED_CHAT_IDS, default=""): str,
    vol.Optional(CONF_BABY_NAME, default="Baby"): str,
})

class BabyTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Baby Tracker."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return BabyTrackerOptionsFlowHandler(config_entry)

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
            errors=errors
        )

class BabyTrackerOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Robust default retrieval
        data = self.config_entry.data
        options = self.config_entry.options
        
        # Get current values, fallback to data, then fallback to empty/default string
        current_ids = options.get(CONF_ALLOWED_CHAT_IDS, data.get(CONF_ALLOWED_CHAT_IDS, ""))
        current_name = options.get(CONF_BABY_NAME, data.get(CONF_BABY_NAME, "Baby"))

        # Explicitly cast to string to ensure Schema compatibility (prevent 500 on None/Int)
        if current_ids is None: current_ids = ""
        current_ids = str(current_ids)
        current_name = str(current_name)

        options_schema = vol.Schema({
            vol.Required(CONF_ALLOWED_CHAT_IDS, default=current_ids): str,
            vol.Optional(CONF_BABY_NAME, default=current_name): str,
        })

        return self.async_show_form(step_id="init", data_schema=options_schema)
