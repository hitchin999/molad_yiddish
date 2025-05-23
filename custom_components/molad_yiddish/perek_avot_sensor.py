# custom_components/molad_yiddish/perek_avot_sensor.py
from __future__ import annotations
from datetime import date, timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

import pyluach.dates as pdates
from .molad_lib.helper import int_to_hebrew

class PerekAvotSensor(SensorEntity):
    """Which פרק of Pirkei Avot is read each week (from Pesach until Sukkot)."""

    _attr_name = "Perek Avos"
    _attr_unique_id = "molad_yiddish_perek_avot"
    _attr_icon = "mdi:book-open-page-variant"

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        # fallback when out of season
        self._attr_native_value = "נישט אין די צייט פון פרקי אבות"

    async def async_added_to_hass(self) -> None:
        # initial update
        await self._update_state()
        # update daily
        async_track_time_interval(
            self.hass,
            lambda now: self.hass.async_create_task(self._update_state()),
            timedelta(hours=24),
        )

    async def _update_state(self) -> None:
        today_py = date.today()
        today_hd = pdates.HebrewDate.from_pydate(today_py)

        # 1) Pesach – 15 ניסן of THIS Hebrew year
        pesach_hd = pdates.HebrewDate(today_hd.year, 1, 15)
        pesach_py = pesach_hd.to_pydate()

        # 2) first Shabbat *after* Pesach 15
        offset = (5 - pesach_py.weekday()) % 7 or 7
        first_shabbat = pesach_py + timedelta(days=offset)

        # 3) Sukkot – 15 תשרי of the NEXT Hebrew year
        sukkot_hd = pdates.HebrewDate(today_hd.year + 1, 7, 15)
        sukkot_py = sukkot_hd.to_pydate()

        # 4) If today is between those two dates, cycle chapters 1–6
        if first_shabbat <= today_py <= sukkot_py:
            weeks_since = ((today_py - first_shabbat).days // 7) + 1
            chap = ((weeks_since - 1) % 6) + 1
            state = f"פרק {int_to_hebrew(chap)}"
        else:
            state = "נישט אין די צייט פון פרקי אבות"

        self._attr_native_value = state
        self.async_write_ha_state()
        
