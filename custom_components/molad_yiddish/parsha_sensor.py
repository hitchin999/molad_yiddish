from __future__ import annotations
from datetime import date, timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.event import async_track_time_interval
from pyluach import dates, parshios

class ParshaYiddishSensor(SensorEntity):
    """Offline Parsha sensor using pyluach for weekly readings."""

    _attr_name = "Molad Yiddish Parsha"             # Friendly name shown in the UI
    _attr_icon = "mdi:book-open-page-variant"
    _attr_unique_id = "molad_yiddish_parsha"        # Make it manageable in the UI

    def __init__(self, hass) -> None:
        super().__init__()                          # always call super()
        self.hass = hass
        self._state: str | None = None

    async def async_added_to_hass(self) -> None:
        # Initial update
        await self._update_state()
        # Schedule daily updates just after midnight
        async_track_time_interval(
            self.hass,
            lambda now: self.hass.async_create_task(self._update_state()),
            timedelta(days=1, seconds=5)
        )

    @property
    def state(self) -> str:
        # Return 'none' when no parsha is available
        return self._state or "none"

    async def _update_state(self) -> None:
        # Determine upcoming Shabbat (Saturday)
        today = date.today()
        # weekday(): Monday=0...Sunday=6; Saturday=5
        offset = (5 - today.weekday()) % 7
        shabbat = today + timedelta(days=offset)

        # Use pyluach to get parsha indices for that date
        greg = dates.GregorianDate(shabbat.year, shabbat.month, shabbat.day)
        parsha_indices = parshios.getparsha(greg)

        if parsha_indices:
            # Standard weekly Parsha(s)
            heb = parshios.getparsha_string(greg, hebrew=True)
            # Replace comma with hyphen for combined parshas
            combined = heb.replace(", ", "-")
            self._state = f"פרשת {combined}"
        else:
            # No Parsha (e.g., holiday week)
            self._state = "none"

        self.async_write_ha_state()
