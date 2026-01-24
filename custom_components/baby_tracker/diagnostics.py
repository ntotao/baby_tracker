"""Diagnostics support for Baby Tracker."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_TELEGRAM_TOKEN

TO_REDACT = {CONF_TELEGRAM_TOKEN, "allowed_chat_ids"}

async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = async_redact_data(entry.data, TO_REDACT)
    options = async_redact_data(entry.options, TO_REDACT)

    # Get Bot status/info if available
    bot_info = {}
    if app := hass.data[DOMAIN].get(entry.entry_id):
        # Basic info about bot connection is tricky to get deep inside PTB
        # but we can check if updater is running
        bot_info = {
            "running": app.updater.running,
            "bot_id": app.bot.id if app.bot else "Unknown"
        }

    return {
        "entry": {
            "data": data,
            "options": options,
        },
        "bot_info": bot_info,
    }
