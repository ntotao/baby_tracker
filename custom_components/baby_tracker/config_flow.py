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

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            # Update config entry (merging options into data for simplicity in init)
            # In a clean implementation, options are separate, but here we can merge or just use options.
            # To avoid complexity in __init__, we update the main entry data if we can,
            # or we stick to standard HA pattern: Data is Setup, Options are Runtime/Changeable.
            
            # Let's save to options, and in __init__ we look at both.
            return self.async_create_entry(title="", data=user_input)

        # Default values from current config
        current_ids = self.config_entry.options.get(CONF_ALLOWED_CHAT_IDS, self.config_entry.data.get(CONF_ALLOWED_CHAT_IDS, ""))
        current_name = self.config_entry.options.get(CONF_BABY_NAME, self.config_entry.data.get(CONF_BABY_NAME, "Baby"))

        options_schema = vol.Schema({
            vol.Required(CONF_ALLOWED_CHAT_IDS, default=current_ids): str,
            vol.Optional(CONF_BABY_NAME, default=current_name): str,
        })

        return self.async_show_form(step_id="init", data_schema=options_schema)
