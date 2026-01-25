"""Persistent storage for Baby Tracker events (v2.0)."""
import logging
from datetime import datetime, timedelta
from homeassistant.helpers.storage import Store
from homeassistant.core import HomeAssistant

from .models import BabyEvent

_LOGGER = logging.getLogger(__name__)

STORAGE_KEY = "baby_tracker_events"
STORAGE_VERSION = 2  # Bumping version to indicate new schema if needed

class EventStore:
    """Class to handle storage of baby tracker events."""

    def __init__(self, hass: HomeAssistant, entry_id: str):
        """Initialize the storage."""
        self.hass = hass
        self.entry_id = entry_id
        self._store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}_{entry_id}")
        self.events: list[BabyEvent] = []
        self.last_load = None

    async def async_load(self):
        """Load data from storage with validation."""
        raw_data = await self._store.async_load()
        self.events = []
        
        if raw_data and "events" in raw_data:
            for ev_dict in raw_data["events"]:
                # Try to parse into model
                event = BabyEvent.from_dict(ev_dict)
                if event:
                    self.events.append(event)
                else:
                    _LOGGER.warning("Skipping corrupted event: %s", ev_dict)
        
        self.last_load = datetime.now()

    async def async_save(self):
        """Save data to storage."""
        data = {
            "events": [ev.to_dict() for ev in self.events]
        }
        await self._store.async_save(data)

    async def add_event(self, event: BabyEvent):
        """Add a new event."""
        self.events.append(event)
        await self.async_save()
        _LOGGER.debug("Added event: %sMs", event)

    def get_events(self, start_date: datetime, end_date: datetime) -> list[BabyEvent]:
        """Get events within a date range."""
        results = []
        for event in self.events:
            if event.end and event.start < end_date and event.end > start_date:
                results.append(event)
            elif not event.end and event.start >= start_date and event.start <= end_date:
                results.append(event)
        return results

    def get_stats_last_24h(self):
        """Calculate statistics for the last 24 hours."""
        now = datetime.now()
        start_monitor = now - timedelta(hours=24)
        
        events_24h = [
            e for e in self.events
            if e.start >= start_monitor
        ]
        
        poo_count = sum(1 for e in events_24h if e.type == "poo" or (e.type == "diaper" and "Cacca" in e.summary))
        pee_count = sum(1 for e in events_24h if e.type == "pee" or (e.type == "diaper" and "Pipì" in e.summary))
        feeding_count = sum(1 for e in events_24h if e.type == "feeding" or "Poppata" in e.summary)
        
        # Fallback for old "summary-based" logic if type isn't migrated
        if poo_count == 0 and pee_count == 0 and feeding_count == 0:
             poo_count = sum(1 for e in events_24h if "Cacca" in e.summary or "Misto" in e.summary)
             pee_count = sum(1 for e in events_24h if "Pipì" in e.summary or "Misto" in e.summary)
             feeding_count = sum(1 for e in events_24h if "Poppata" in e.summary)

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
        for event in reversed(self.events):
            # Prefer 'type' but fallback to string matching for old data compatibility
            is_feeding = event.type == "feeding" or "Poppata" in event.summary
            is_poo = event.type == "poo" or "Cacca" in event.summary or "Misto" in event.summary
            is_pee = event.type == "pee" or "Pipì" in event.summary or "Misto" in event.summary

            if not last_feeding and is_feeding:
                last_feeding = event
            if not last_poo and is_poo:
                last_poo = event
            if not last_pee and is_pee:
                last_pee = event
                
            if last_feeding and last_poo and last_pee:
                break
                
        return {
            "feeding": last_feeding,
            "poo": last_poo,
            "pee": last_pee
        }
