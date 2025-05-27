from datetime import timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import (
    async_track_time_change,
    async_track_time_interval,
)

from .molad_lib import specials

class SpecialShabbosSensor(SensorEntity):
    """Sensor that provides the upcoming special Shabbatot (Yiddish integration)."""

    _attr_name = "Special Shabbos Yiddish"
    _attr_unique_id = "molad_yiddish_special_shabbos"
    _attr_icon = "mdi:calendar-star"
    _attr_has_entity_name = True

    def __init__(self):
        self._state = ""

    @property
    def state(self):
        return self._state

    async def async_added_to_hass(self):
        await self.async_update()

        # Update daily just after midnight
        async_track_time_change(
            self.hass,
            lambda now: self.hass.async_create_task(self.async_update()),
            hour=0,
            minute=0,
            second=5,
        )

        # Backup: every 6 hours
        async_track_time_interval(
            self.hass,
            lambda now: self.hass.async_create_task(self.async_update()),
            timedelta(hours=6),
        )

    async def async_update(self):
        try:
            self._state = specials.get_special_shabbos_name()
        except Exception:
            self._state = ""
        self.async_write_ha_state()
