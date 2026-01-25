"""Binary Sensor platform for Baby Tracker."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BabyTrackerCoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Baby Tracker binary sensors."""
    coordinator: BabyTrackerCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([
        BabyFeedingSensor(coordinator, entry),
    ])

class BabyFeedingSensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of Feeding Status."""

    _attr_has_entity_name = True
    _attr_name = "Allattamento in Corso"
    _attr_icon = "mdi:timer-outline"

    def __init__(self, coordinator: BabyTrackerCoordinator, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_feeding_active"

    @property
    def is_on(self) -> bool:
        """Return true if feeding is active."""
        return self.coordinator.is_feeding
