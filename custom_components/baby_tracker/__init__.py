"""The Baby Tracker integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_TELEGRAM_TOKEN, CONF_ALLOWED_CHAT_IDS
from .bot import setup_bot

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Baby Tracker component."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Baby Tracker from a config entry."""
    token = entry.data.get(CONF_TELEGRAM_TOKEN)
    
    # Parse allowed IDs (comma separated string -> list of ints)
    allowed_ids_str = entry.data.get(CONF_ALLOWED_CHAT_IDS, "")
    allowed_ids = []
    if allowed_ids_str:
        try:
            allowed_ids = [int(x.strip()) for x in allowed_ids_str.split(",") if x.strip()]
        except ValueError:
            _LOGGER.error("Invalid format for Allowed Chat IDs. Must be integers.")
    
    if not token:
        _LOGGER.error("Telegram Token not found in config entry")
        return False

    _LOGGER.info("Starting Baby Tracker Bot with Allowed IDs: %s", allowed_ids)
    
    # Start Bot
    try:
        application = await setup_bot(hass, token, allowed_ids)
        
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
