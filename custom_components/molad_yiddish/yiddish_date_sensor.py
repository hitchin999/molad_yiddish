# homeassistant/custom_components/molad_yiddish/yiddish_date_sensor.py
from __future__ import annotations
import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from astral import LocationInfo
from astral.sun import sun

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_sunset
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED

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
    """Today’s Hebrew date in Yiddish formatting,
       flips at sunset+havdalah_offset only."""

    _attr_name = "Yiddish Date"
    _attr_unique_id = "yiddish_date"
    _attr_icon = "mdi:calendar-range"

    def __init__(self, hass: HomeAssistant, havdalah_offset: int) -> None:
        super().__init__()
        self.hass = hass
        self._havdalah_offset = timedelta(minutes=havdalah_offset)

        # for calculating local sunset
        self._tz = ZoneInfo(hass.config.time_zone)
        self._loc = LocationInfo(
            latitude=hass.config.latitude,
            longitude=hass.config.longitude,
            timezone=hass.config.time_zone,
        )

        self._state: str | None = None

    async def async_added_to_hass(self) -> None:
        # 1) initial fill (at startup or reboot)
        await self._update_state()

        # 2) whenever HA starts up later
        self.hass.bus.async_listen(
            EVENT_HOMEASSISTANT_STARTED,
            lambda event: self.hass.async_create_task(self._update_state()),
)

        # 3) schedule the coroutine itself at sunset+offset
        async_track_sunset(
            self.hass,
            self._update_state,           # <-- pass the async method directly
            offset=self._havdalah_offset,
        )

    @property
    def state(self) -> str:
        return self._state or ""

    async def _update_state(self) -> None:
        """Recompute what “today” means (Hebrew date) based on now vs. sunset+offset."""
        now = datetime.now(self._tz)
        # compute today’s local sunset
        s = sun(self._loc.observer, date=now.date(), tzinfo=self._tz)
        switch_time = s["sunset"] + self._havdalah_offset

        # if we’re already past sunset+offset, treat as "tomorrow"
        py_date = (
            now.date() + timedelta(days=1)
            if now >= switch_time
            else now.date()
        )

        # now convert that python date to a Hebrew date
        heb = PHebrewDate.from_pydate(py_date)
        day_heb   = int_to_hebrew(heb.day)
        month_heb = get_hebrew_month_name(heb.month, heb.year)
        year_num  = heb.year % 1000
        year_heb  = int_to_hebrew(year_num)

        # assemble and normalize quotes
        state = f"{day_heb} {month_heb} {year_heb}"
        state = state.replace("\u05F4", '"').replace("\u05F3", "'")

        self._state = state
        self.async_write_ha_state()
