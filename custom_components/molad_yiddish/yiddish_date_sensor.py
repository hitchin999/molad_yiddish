# homeassistant/custom_components/molad_yiddish/yiddish_date_sensor.py
from __future__ import annotations
import logging
from datetime import date, timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval, async_track_sunset

from pyluach.hebrewcal import Year, HebrewDate as PHebrewDate
from .molad_lib.helper import int_to_hebrew

_LOGGER = logging.getLogger(__name__)

def get_hebrew_month_name(month: int, year: int) -> str:
    """
    Map Pyluach month-numbers to Hebrew month names, handling leap years:
      1=Nisan,2=Iyar,3=Sivan,4=Tammuz,5=Av,6=Elul,
      7=Tishrei,8=Cheshvan,9=Kislev,10=Tevet,11=Shevat,
      12=Adar I (or Adar in non-leap), 13=Adar II
    """
    # Adar logic
    if month == 12:
        return "אדר א׳" if Year(year).leap else "אדר"
    if month == 13:
        return "אדר ב׳"

    # The rest of the months
    return {
        1:  "ניסן",
        2:  "אייר",
        3:  "סיון",
        4:  "תמוז",
        5:  "אב",
        6:  "אלול",
        7:  "תשרי",
        8:  "חשון",
        9:  "כסלו",
        10: "טבת",
        11: "שבט",
    }.get(month, "")


class YiddishDateSensor(SensorEntity):
    """Today's Hebrew date in Yiddish formatting,
       updates at 00:00 and at sunset+havdalah_offset."""

    _attr_name = "Yiddish Date"
    _attr_unique_id = "yiddish_date"
    _attr_icon = "mdi:calendar-range"

    def __init__(self, hass: HomeAssistant, havdalah_offset: int) -> None:
        super().__init__()
        self.hass = hass
        self._havdalah_offset = havdalah_offset
        self._state: str | None = None

    async def async_added_to_hass(self) -> None:
        # 1) initial fill
        await self._update_state()

        # 2) update just after local midnight
        async_track_time_interval(
            self.hass,
            lambda now: self.hass.async_create_task(self._update_state()),
            timedelta(days=1, seconds=5),
        )

        # 3) update at sunset + havdalah_offset
        async_track_sunset(
            self.hass,
            lambda now: self.hass.async_create_task(self._update_state()),
            offset=timedelta(minutes=self._havdalah_offset),
        )

    @property
    def state(self) -> str:
        return self._state or ""

    async def _update_state(self) -> None:
        today = date.today()
        heb = PHebrewDate.from_pydate(today)

        # day → Hebrew numerals
        day_heb = int_to_hebrew(heb.day)
        # month → accurate name including Adar I/II
        month_heb = get_hebrew_month_name(heb.month, heb.year)
        # year → last three digits (e.g. 5785 → 785 → תשפ״ה)
        year_num = heb.year % 1000
        year_heb = int_to_hebrew(year_num)

        self._state = f"{day_heb} {month_heb} {year_heb}"
        self.async_write_ha_state()
