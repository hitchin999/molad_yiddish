# no_music_sensor.py
"""
Binary sensor for "נישט הערן מוזיק":
- Prohibits music during the Omer (1–49) except on Lag BaOmer (33).
- Prohibits music during the Three Weeks period (17 Tammuz–9 Av).
"""
from __future__ import annotations
import datetime
from datetime import timedelta, date
from zoneinfo import ZoneInfo

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from pyluach.hebrewcal import HebrewDate

class NoMusicSensor(BinarySensorEntity):
    _attr_name = "No Music"
    _attr_unique_id = "molad_yiddish_no_music"
    _attr_entity_id = "binary_sensor.molad_yiddish_no_music"
    _attr_icon = "mdi:music-off"

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__()
        self.hass = hass
        self._attr_is_on = False
        # Update hourly
        async_track_time_interval(hass, self.async_update, timedelta(hours=1))

    def _compute_omer_count(self, today_hd: HebrewDate) -> int | None:
        # Omer starts 16 Nissan (month 1)
        try:
            year = today_hd.year
            start = HebrewDate(year, 1, 16)
            diff = int(today_hd.to_jd() - start.to_jd()) + 1
            if 1 <= diff <= 49:
                return diff
        except Exception:
            pass
        return None

    async def async_update(self, now: datetime.datetime | None = None) -> None:
        tz = ZoneInfo(self.hass.config.time_zone)
        now = now or datetime.datetime.now(tz)
        today = now.date()
        today_hd = HebrewDate.from_pydate(today)

        # Compute Omer count
        omer = self._compute_omer_count(today_hd)
        in_omer = (omer is not None and omer != 33)

        # Three Weeks period (month 4 Tammuz, 17–30) and (month 5 Av, 1–9)
        in_three_weeks = (
            (today_hd.month == 4 and today_hd.day >= 17) or
            (today_hd.month == 5 and today_hd.day <= 9)
        )

        self._attr_is_on = in_omer or in_three_weeks
