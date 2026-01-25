"""Data Update Coordinator for Baby Tracker."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .event_store import EventStore

_LOGGER = logging.getLogger(__name__)

class BabyTrackerCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, store: EventStore) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=10), # Only for periodic cleanups if needed
        )
        self.store = store

    async def _async_update_data(self):
        """Fetch data from API endpoint.
        
        In this local integration, 'fetching' means ensuring our store is loaded.
        Real updates happen via push (add_event), not polling.
        """
        # Ensure data is loaded
        if not self.store.last_load:
            await self.store.async_load()
        return self.store.events

    async def async_add_event(self, event):
        """Add an event and notify listeners."""
        await self.store.add_event(event)
        # Notify HA that data has changed
        self.async_set_updated_data(self.store.events)
