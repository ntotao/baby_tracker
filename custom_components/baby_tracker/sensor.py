import logging
import requests
from datetime import timedelta
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_HOST, CONF_NAME
import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

CONF_TELEGRAM_ID = "telegram_id"
DEFAULT_NAME = "Baby Tracker"
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60) # Poll every minute

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_TELEGRAM_ID): cv.positive_int,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Baby Tracker sensor platform."""
    host = config.get(CONF_HOST)
    telegram_id = config.get(CONF_TELEGRAM_ID)
    name = config.get(CONF_NAME)

    data = BabyTrackerData(host, telegram_id)
    data.update()

    if data.data is None:
        _LOGGER.error("Could not connect to Baby Tracker Bot at %s", host)
        return

    sensors = []
    sensors.append(BabyTrackerSensor(data, name, "last_feed_time", "Ultime Poppata", "timestamp"))
    sensors.append(BabyTrackerSensor(data, name, "last_feed_side", "Lato Poppata", None))
    sensors.append(BabyTrackerSensor(data, name, "last_cacca_time", "Ultima Cacca", "timestamp"))
    sensors.append(BabyTrackerSensor(data, name, "last_pipi_time", "Ultima Pipi", "timestamp"))
    
    sensors.append(BabyTrackerSensor(data, name, "count_feed", "Poppate Oggi", None))
    sensors.append(BabyTrackerSensor(data, name, "count_cacca", "Cacche Oggi", None))
    sensors.append(BabyTrackerSensor(data, name, "count_pipi", "Pipi Oggi", None))

    add_entities(sensors, True)

class BabyTrackerSensor(SensorEntity):
    """Representation of a Baby Tracker Sensor."""

    def __init__(self, data, name, sensor_type, label, device_class):
        self._data = data
        self._name = f"{name} {label}"
        self._type = sensor_type
        self._state = None
        self._device_class = device_class

    @property
    def name(self):
        return self._name

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
