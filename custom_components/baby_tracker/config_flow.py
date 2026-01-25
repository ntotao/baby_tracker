"""Config flow for Baby Tracker integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.const import CONF_NAME

from .const import DOMAIN, CONF_TELEGRAM_TOKEN, CONF_ALLOWED_CHAT_IDS, CONF_BABY_NAME

_LOGGER = logging.getLogger(__name__)

class BabyTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Baby Tracker."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            token = user_input.get(CONF_TELEGRAM_TOKEN)
            
            # Simple validation
            if not token or ":" not in token:
                 errors["base"] = "invalid_auth"
            else:
                return self.async_create_entry(title="Baby Tracker Bot", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_TELEGRAM_TOKEN): str,
                vol.Optional(CONF_ALLOWED_CHAT_IDS, default=""): str,
                vol.Optional(CONF_BABY_NAME, default="Baby"): str,
            }),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return BabyTrackerOptionsFlowHandler(config_entry)


class BabyTrackerOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Robust retrieval: Look in options first, then data, then empty string default
        # The key is to handle the case where keys are MISSING entirely
        
        # 1. Chat IDs
        ids_opt = self.config_entry.options.get(CONF_ALLOWED_CHAT_IDS)
        ids_data = self.config_entry.data.get(CONF_ALLOWED_CHAT_IDS)
        current_ids = ids_opt if ids_opt is not None else ids_data
        if current_ids is None: current_ids = ""
        current_ids = str(current_ids)

        # 2. Baby Name
        name_opt = self.config_entry.options.get(CONF_BABY_NAME)
        name_data = self.config_entry.data.get(CONF_BABY_NAME)
        current_name = name_opt if name_opt is not None else name_data
        if current_name is None: current_name = "Baby"
        current_name = str(current_name)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(CONF_ALLOWED_CHAT_IDS, default=current_ids): str,
                vol.Optional(CONF_BABY_NAME, default=current_name): str,
            }),
        )
