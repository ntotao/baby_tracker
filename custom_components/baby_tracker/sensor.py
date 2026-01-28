import logging
import requests
from datetime import timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

CONF_TELEGRAM_ID = "telegram_id"
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Baby Tracker sensor from a config entry."""
    host = config_entry.data.get(CONF_HOST)
    telegram_id = config_entry.data.get(CONF_TELEGRAM_ID)
    name = config_entry.data.get(CONF_NAME)

    data = BabyTrackerData(host, telegram_id)
    # Perform initial update
    await hass.async_add_executor_job(data.update)

    sensors = []
    sensors.append(BabyTrackerSensor(data, name, "last_feed_time", "Ultime Poppata", "timestamp"))
    sensors.append(BabyTrackerSensor(data, name, "last_feed_side", "Lato Poppata", None))
    sensors.append(BabyTrackerSensor(data, name, "last_cacca_time", "Ultima Cacca", "timestamp"))
    sensors.append(BabyTrackerSensor(data, name, "last_pipi_time", "Ultima Pipi", "timestamp"))
    
    sensors.append(BabyTrackerSensor(data, name, "count_feed", "Poppate Oggi", None))
    sensors.append(BabyTrackerSensor(data, name, "count_cacca", "Cacche Oggi", None))
    sensors.append(BabyTrackerSensor(data, name, "count_pipi", "Pipi Oggi", None))

    async_add_entities(sensors, True)

class BabyTrackerSensor(SensorEntity):
    """Representation of a Baby Tracker Sensor."""

    def __init__(self, data,name, sensor_type, label, device_class):
        self._data = data
        self._name_prefix = name
        self._type = sensor_type
        self._label = label
        self._state = None
        self._device_class = device_class

    @property
    def name(self):
        return f"{self._name_prefix} {self._label}"

    @property
    def unique_id(self):
        return f"{self._name_prefix}_{self._type}"

    @property
    def state(self):
        return self._state

    @property
    def icon(self):
        if "feed" in self._type: return "mdi:baby-bottle"
        if "cacca" in self._type: return "mdi:emoticon-poop"
        if "pipi" in self._type: return "mdi:water"
        return "mdi:baby"

    @property
    def device_class(self):
        return self._device_class

    def update(self):
        """Get the latest data."""
        self._data.update()
        data = self._data.data
        
        if data:
            if self._type == "last_feed_time":
                self._state = data.get("last_feed")
            elif self._type == "last_feed_side":
                self._state = data.get("last_feed_side")
            elif self._type == "last_cacca_time":
                self._state = data.get("last_cacca")
            elif self._type == "last_pipi_time":
                self._state = data.get("last_pipi")
            elif self._type == "count_feed":
                self._state = data.get("count_feed")
            elif self._type == "count_cacca":
                self._state = data.get("count_cacca")
            elif self._type == "count_pipi":
                self._state = data.get("count_pipi")

class BabyTrackerData:
    """Class for handling the data retrieval."""

    def __init__(self, host, telegram_id):
        self._host = host
        self._tid = telegram_id
        self.data = None

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Get the latest data from the Bot API."""
        url = f"{self._host}/api/ha/status"
        params = {"telegram_id": self._tid}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                self.data = response.json()
            else:
                _LOGGER.error("Error fetching data: %s", response.status_code)
                self.data = None
        except Exception as e:
            _LOGGER.error("Exception fetching data: %s", e)
            self.data = None
