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
            token = user_input[CONF_TELEGRAM_TOKEN]
            
            # Simple validation
            if not token or ":" not in token:
                 errors["base"] = "invalid_auth"
            else:
                return self.async_create_entry(title="Baby Tracker Bot", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_TELEGRAM_TOKEN): str,
                vol.Required(CONF_ALLOWED_CHAT_IDS, default=""): str,
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

        # Config Entry Options take precedence, fallback to Config Entry Data, then Default
        ids_default = self.config_entry.options.get(
            CONF_ALLOWED_CHAT_IDS, 
            self.config_entry.data.get(CONF_ALLOWED_CHAT_IDS, "")
        )
        name_default = self.config_entry.options.get(
            CONF_BABY_NAME, 
            self.config_entry.data.get(CONF_BABY_NAME, "Baby")
        )

        # Ensure strict strings for UI
        ids_default = str(ids_default) if ids_default is not None else ""
        name_default = str(name_default) if name_default is not None else "Baby"

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_ALLOWED_CHAT_IDS, default=ids_default): str,
                vol.Optional(CONF_BABY_NAME, default=name_default): str,
            }),
        )
