"""The Baby Tracker integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_TELEGRAM_TOKEN
from .bot import setup_bot

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Baby Tracker component."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Baby Tracker from a config entry."""
    token = entry.data.get(CONF_TELEGRAM_TOKEN)
    
    if not token:
        _LOGGER.error("Telegram Token not found in config entry")
        return False

    _LOGGER.info("Starting Baby Tracker Bot...")
    
    # Start Bot
    try:
        application = await setup_bot(hass, token)
        
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = application
        
    except Exception as e:
        _LOGGER.exception("Failed to start Telegram Bot: %s", e)
        return False

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    application = hass.data[DOMAIN].pop(entry.entry_id)
    
    if application:
        _LOGGER.info("Stopping Baby Tracker Bot...")
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

    return True
