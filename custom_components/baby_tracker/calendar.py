"""Calendar platform for Baby Tracker."""
import logging
from datetime import datetime, timedelta
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .event_store import EventStore

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the Baby Tracker calendar platform."""
    
    # Retrieve Store initialized in __init__.py
    store = hass.data[DOMAIN].get(entry.entry_id + "_store")
    
    if not store:
        _LOGGER.error("Event Store not found for calendar setup!")
        return
        
    async_add_entities([BabyTrackerCalendar(store, entry)], True)


class BabyTrackerCalendar(CalendarEntity):
    """Representation of a Baby Tracker Calendar."""

    def __init__(self, store: EventStore, entry: ConfigEntry):
        """Initialize the calendar."""
        self._store = store
        self._entry = entry
        self._attr_name = "Baby Tracker"
        self._attr_unique_id = f"{entry.entry_id}_calendar"

    @property
    def event(self):
        """Return the next upcoming event."""
        return None

    async def async_get_events(self, hass, start_date, end_date):
        """Get all events in a specific time frame."""
        # start_date and end_date are datetime objects
        stored_events = self._store.get_events(start_date, end_date)
        
        calendar_events = []
        for ev in stored_events:
            # BabyEvent is an object now, not a dict
            calendar_events.append(CalendarEvent(
                summary=ev.summary,
                start=ev.start,
                end=ev.end if ev.end else ev.start + timedelta(minutes=1), # Ensure duration for point events
                description=ev.description
            ))
            
        return calendar_events
