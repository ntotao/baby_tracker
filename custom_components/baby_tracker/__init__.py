"""The Baby Tracker integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_TELEGRAM_TOKEN, CONF_ALLOWED_CHAT_IDS, CONF_BABY_NAME
from .bot import setup_bot
from .event_store import EventStore
from .coordinator import BabyTrackerCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Baby Tracker component."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Baby Tracker from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    token = entry.data.get(CONF_TELEGRAM_TOKEN)
    
    # Options + Data merge logic
    allowed_ids_str = entry.options.get(CONF_ALLOWED_CHAT_IDS, entry.data.get(CONF_ALLOWED_CHAT_IDS, ""))
    baby_name = entry.options.get(CONF_BABY_NAME, entry.data.get(CONF_BABY_NAME, "Baby"))
    
    allowed_ids = []
    if allowed_ids_str:
        try:
            allowed_ids = [int(x.strip()) for x in allowed_ids_str.split(",") if x.strip()]
        except ValueError:
            _LOGGER.error("Invalid format for Allowed Chat IDs. Must be integers.")
    
    if not token:
        _LOGGER.error("Telegram Token not found in config entry")
        return False

    # 1. Initialize Store
    store = EventStore(hass, entry.entry_id)
    await store.async_load()

    # 2. Initialize Coordinator
    coordinator = BabyTrackerCoordinator(hass, store)
    # Perform first refresh (lazy load check)
    await coordinator.async_config_entry_first_refresh()

    # Store references
    hass.data[DOMAIN][entry.entry_id] = coordinator
    # Keep store accessible efficiently if needed, or just access via coordinator
    hass.data[DOMAIN][entry.entry_id + "_store"] = store 

    _LOGGER.info("Starting %s Tracker Bot... (v2.0)", baby_name)
    
    # 3. Start Bot
    try:
        application = await setup_bot(hass, token, allowed_ids, entry.entry_id, baby_name)
        hass.data[DOMAIN][entry.entry_id + "_bot"] = application
        
        # Forward setup
        await hass.config_entries.async_forward_entry_setups(entry, ["calendar"])
        
        # Listen for updates to options
        entry.async_on_unload(entry.add_update_listener(update_listener))
        
    except Exception as e:
        _LOGGER.exception("Failed to start Telegram Bot: %s", e)
        return False

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    # Stop Bot
    if bot_app := hass.data[DOMAIN].pop(entry.entry_id + "_bot", None):
        _LOGGER.info("Stopping Baby Tracker Bot...")
        await bot_app.updater.stop()
        await bot_app.stop()
        await bot_app.shutdown()
    
    # Remove data
    hass.data[DOMAIN].pop(entry.entry_id, None)       # Coordinator
    hass.data[DOMAIN].pop(entry.entry_id + "_store", None) # Store

    return await hass.config_entries.async_unload_platforms(entry, ["calendar"])

async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
