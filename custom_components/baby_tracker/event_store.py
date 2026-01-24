"""Persistent storage for Baby Tracker events."""
import logging
from datetime import datetime, timedelta
from homeassistant.helpers.storage import Store
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

STORAGE_KEY = "baby_tracker_events"
STORAGE_VERSION = 1

class EventStore:
    """Class to handle storage of baby tracker events."""

    def __init__(self, hass: HomeAssistant, entry_id: str):
        """Initialize the storage."""
        self.hass = hass
        self.entry_id = entry_id
        # Unique store per config entry (to support multiple babies maybe? for now just unique key)
        self._store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}_{entry_id}")
        self._data = {"events": []}

    async def async_load(self):
        """Load data from storage."""
        data = await self._store.async_load()
        if data:
            self._data = data

    async def async_save(self):
        """Save data to storage."""
        await self._store.async_save(self._data)

    async def add_event(self, summary: str, start_dt: datetime, end_dt: datetime = None, description: str = ""):
        """Add a new event."""
        if end_dt is None:
            end_dt = start_dt

        event = {
            "summary": summary,
            "start": start_dt.isoformat(),
            "end": end_dt.isoformat(),
            "description": description,
            # "uid": ... (Optional, can add unique ID)
        }
        self._data["events"].append(event)
        await self.async_save()
        _LOGGER.debug("Added event: %s", event)

    def get_events(self, start_date: datetime, end_date: datetime):
        """Get events within a date range."""
        results = []
        for event in self._data["events"]:
            # Simple string comparison works for ISO format if timezone is consistent, 
            # but ideally we parse back to datetime. 
            # Stored as ISO string.
            
            try:
                ev_start = datetime.fromisoformat(event["start"])
                ev_end = datetime.fromisoformat(event["end"])
                
                # Check overlap
                if ev_start < end_date and ev_end > start_date:
                    results.append({
                        "summary": event["summary"],
                        "start": ev_start,
                        "end": ev_end,
                        "description": event.get("description", "")
                    })
            except ValueError:
                continue
                
        return results

    def get_stats_last_24h(self):
        """Calculate statistics for the last 24 hours."""
        now = datetime.now()
        start_monitor = now - timedelta(hours=24)
        
        events_24h = [
            e for e in self._data["events"] 
            if datetime.fromisoformat(e["start"]) >= start_monitor
        ]
        
        poo_count = sum(1 for e in events_24h if "Cacca" in e["summary"] or "Misto" in e["summary"])
        pee_count = sum(1 for e in events_24h if "Pipì" in e["summary"] or "Misto" in e["summary"])
        feeding_count = sum(1 for e in events_24h if "Poppata" in e["summary"])
        
        return {
            "poo": poo_count,
            "pee": pee_count,
            "feeding": feeding_count
        }

    def get_last_events(self):
        """Get the most recent event of each type."""
        last_feeding = None
        last_poo = None
        last_pee = None
        
        # Iterate backwards
        for event in reversed(self._data["events"]):
            if not last_feeding and "Poppata" in event["summary"]:
                last_feeding = event
            if not last_poo and ("Cacca" in event["summary"] or "Misto" in event["summary"]):
                last_poo = event
            if not last_pee and ("Pipì" in event["summary"] or "Misto" in event["summary"]):
                last_pee = event
                
            if last_feeding and last_poo and last_pee:
                break
                
        return {
            "feeding": last_feeding,
            "poo": last_poo,
            "pee": last_pee
        }
