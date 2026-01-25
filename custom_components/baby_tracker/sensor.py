"""Sensor platform for Baby Tracker."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
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
    """Set up the Baby Tracker sensors."""
    coordinator: BabyTrackerCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([
        BabyTrackerCounter(coordinator, entry, "feeding", "mdi:baby-bottle", "Poppate Oggi"),
        BabyTrackerCounter(coordinator, entry, "poo", "mdi:emoticon-poop", "Cacche Oggi"),
        BabyTrackerCounter(coordinator, entry, "pee", "mdi:water", "Pipì Oggi"),
    ])

class BabyTrackerCounter(CoordinatorEntity, SensorEntity):
    """Representation of a Baby Tracker Counter."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self, 
        coordinator: BabyTrackerCoordinator, 
        entry: ConfigEntry,
        count_type: str,
        icon: str,
        name: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._count_type = count_type
        self._attr_icon = icon
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{count_type}_count"
    
    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        stats = self.coordinator.get_todays_counts()
        return stats.get(self._count_type, 0)
