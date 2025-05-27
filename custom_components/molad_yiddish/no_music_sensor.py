# no_music_sensor.py
"""
Binary sensor for "נישט הערן מוזיק":
- Prohibits music during the Omer (1–49) except on Lag BaOmer (33).
- Prohibits music during the Three Weeks period (17 Tammuz–9 Av).
- Activates at candle-lighting time, and deactivates at havdalah.
"""

from __future__ import annotations
import datetime
from datetime import timedelta
from zoneinfo import ZoneInfo

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import (
    async_track_time_interval,
    async_track_sunset,
)
from pyluach.hebrewcal import HebrewDate


class NoMusicSensor(BinarySensorEntity):
    _attr_name = "Molad Yiddish No Music"
    _attr_unique_id = "molad_yiddish_no_music"
    _attr_icon = "mdi:music-off"

    def __init__(
        self,
        hass: HomeAssistant,
        candle_offset: int,
        havdalah_offset: int,
    ) -> None:
        super().__init__()
        self.hass = hass
        self._candle = candle_offset
        self._havdalah = havdalah_offset
        self._attr_is_on = False

        # Regular interval update as backup
        async_track_time_interval(hass, self.async_update, timedelta(hours=1))

        # Sunset-based ON trigger
        async_track_sunset(
            hass,
            self._turn_on_if_restricted,
            offset=-timedelta(minutes=self._havdalah),
        )

        # Sunset-based OFF trigger (next day)
        async_track_sunset(
            hass,
            self._turn_off,
            offset=timedelta(minutes=self._havdalah),
        )

    def _compute_omer_count(self, today_hd: HebrewDate) -> int | None:
        try:
            year = today_hd.year
            start = HebrewDate(year, 1, 16)  # 16 Nissan
            diff = int(today_hd.to_jd() - start.to_jd()) + 1
            if 1 <= diff <= 49:
                return diff
        except Exception:
            pass
        return None

    def _is_restricted_day(self, today: datetime.date) -> bool:
        today_hd = HebrewDate.from_pydate(today)

        # Omer
        omer = self._compute_omer_count(today_hd)
        in_omer = omer is not None and omer != 33

        # Three Weeks
        in_three_weeks = (
            (today_hd.month == 4 and today_hd.day >= 17) or
            (today_hd.month == 5 and today_hd.day <= 9)
        )

        return in_omer or in_three_weeks

    async def async_update(self, now: datetime.datetime | None = None) -> None:
        now = now or datetime.datetime.now(ZoneInfo(self.hass.config.time_zone))
        if self._is_restricted_day(now.date()):
            self._attr_is_on = True
        else:
            self._attr_is_on = False
        self.async_write_ha_state()

    @callback
    def _turn_on_if_restricted(self, now: datetime.datetime) -> None:
        if self._is_restricted_day(now.date()):
            self._attr_is_on = True
            self.async_write_ha_state()

    @callback
    def _turn_off(self, now: datetime.datetime) -> None:
        self._attr_is_on = False
        self.async_write_ha_state()
