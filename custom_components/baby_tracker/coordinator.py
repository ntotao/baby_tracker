"""Data Update Coordinator for Baby Tracker."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .event_store import EventStore

_LOGGER = logging.getLogger(__name__)

class BabyTrackerCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API and internal state."""

    def __init__(self, hass: HomeAssistant, store: EventStore) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=10),
        )
        self.store = store
        
        # Internal State (Replacing Helpers)
        self.is_feeding = False
        self.feeding_start_time = None
        self.last_feeding_side = None
        self.last_feeding_duration = 0

    async def _async_update_data(self):
        """Fetch data from store."""
        if not self.store.last_load:
            await self.store.async_load()
        return self.store.events

    async def async_add_event(self, event):
        """Add an event and notify listeners."""
        await self.store.add_event(event)
        self.async_set_updated_data(self.store.events)

    # --- State Management Actions ---

    def start_feeding(self):
        """Start the feeding timer."""
        self.is_feeding = True
        self.feeding_start_time = datetime.now()
        self.async_set_updated_data(self.store.events) # Trigger update

    def stop_feeding(self):
        """Stop the feeding timer."""
        self.is_feeding = False
        self.async_set_updated_data(self.store.events)

    def set_feeding_data(self, side, duration):
        """Update last feeding transient data."""
        self.last_feeding_side = side
        self.last_feeding_duration = duration
        # No need to trigger update here usually, as add_event follows

    def get_todays_counts(self):
        """Get counts for today from store."""
        return self.store.get_stats_last_24h() # We can reuse or specialize this
