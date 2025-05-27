#custom_components/molad_yiddish/special_shabbos_sensor.py
from homeassistant.components.sensor import SensorEntity
from .molad_lib import specials

async def async_setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Special Shabbos Yiddish sensor."""
    add_entities([SpecialShabbosSensor()], update_before_add=True)

class SpecialShabbosSensor(SensorEntity):
    """Sensor that provides the upcoming special Shabbatot (Yiddish integration)."""

    _attr_icon = "mdi:calendar-star"  # icon for a special event
    _attr_has_entity_name = True

    def __init__(self):
        self._attr_name = "Special Shabbos Yiddish"
        self._attr_unique_id = "molad_yiddish_special_shabbos"
        self._state = None

    @property
    def state(self):
        """Return the state of the sensor (Hebrew string of special Shabbatot)."""
        return self._state

    def update(self):
        """Update the sensor state by computing the upcoming Shabbat specials."""
        try:
            # Call the rule engine to get the special Shabbat name (or empty string)
            self._state = specials.get_special_shabbos_name()
        except Exception as e:
            # In case of any calculation errors, set state to empty
            self._state = ""
