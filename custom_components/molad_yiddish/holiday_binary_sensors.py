# holiday_binary_sensors.py
import datetime
from datetime import timedelta, date
from zoneinfo import ZoneInfo
from astral import LocationInfo
from astral.sun import sun
from hdate import HDateInfo
from pyluach.hebrewcal import HebrewDate as PHebrewDate
from pyluach.parshios import getparsha_string

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant

class MeluchaProhibitionSensor(BinarySensorEntity):
    """True for every Shabbos & full Yom Tov from candle‐lighting until havdalah."""
    _attr_name = "Molad Yiddish Melucha Prohibition"
    _attr_unique_id = "molad_yiddish_melucha"
    _attr_icon = "mdi:briefcase-variant-off"

    def __init__(self, hass: HomeAssistant, candle_offset: int, havdalah_offset: int) -> None:
        super().__init__()
        self.hass = hass
        self._candle = candle_offset
        self._havdalah = havdalah_offset
        self._attr_is_on = False
        from homeassistant.helpers.event import async_track_time_interval
        async_track_time_interval(hass, self.async_update, timedelta(hours=1))

    async def async_update(self, now=None) -> None:
        tz = ZoneInfo(self.hass.config.time_zone)
        now = now or datetime.datetime.now(tz)
        today = now.date()

        heb = HDateInfo(today, diaspora=False)
        is_yom_tov = bool(heb.is_yom_tov or heb.is_holiday)

        loc = LocationInfo(
            latitude=self.hass.config.latitude,
            longitude=self.hass.config.longitude,
            timezone=self.hass.config.time_zone,
        )
        s_today = sun(loc.observer, date=today, tzinfo=tz)
        s_yest = sun(loc.observer, date=today - timedelta(days=1), tzinfo=tz)
        start = s_today["sunset"] - timedelta(minutes=self._candle)
        end = s_today["sunset"] + timedelta(minutes=self._havdalah)

        # Shabbos: from candlelighting Friday until havdalah Saturday
        is_shabbos = s_yest["sunset"] - timedelta(minutes=self._candle) <= now < end

        self._attr_is_on = (is_yom_tov or is_shabbos) and (start <= now < end)


class ErevHolidaySensor(BinarySensorEntity):
    """True on specific Erev‐days from dawn until candle‐lighting."""
    _attr_name = "Molad Yiddish Erev"
    _attr_unique_id = "molad_yiddish_erev"
    _attr_icon = "mdi:weather-sunset-up"

    _EREV_DATES = {
        (6, 29),  # ערב ראש השנה
        (7, 9),   # ערב יום כיפור
        (7, 14),  # ערב סוכות
        (7, 21),  # הושענא רבה
        (9, 24),  # ערב חנוכה
        (1, 14),  # ערב פסח
        (3, 5),   # ערב שבועות
    }

    def __init__(self, hass: HomeAssistant, candle_offset: int) -> None:
        super().__init__()
        self.hass = hass
        self._candle = candle_offset
        self._attr_is_on = False
        from homeassistant.helpers.event import async_track_time_interval
        async_track_time_interval(hass, self.async_update, timedelta(hours=1))

    async def async_update(self, now=None) -> None:
        tz = ZoneInfo(self.hass.config.time_zone)
        now = now or datetime.datetime.now(tz)
        today = now.date()

        hd = PHebrewDate.from_pydate(today)
        is_erev = (hd.month, hd.day) in self._EREV_DATES

        loc = LocationInfo(
            latitude=self.hass.config.latitude,
            longitude=self.hass.config.longitude,
            timezone=self.hass.config.time_zone,
        )
        s = sun(loc.observer, date=today, tzinfo=tz)
        start = s["dawn"]
        end = s["sunset"] - timedelta(minutes=self._candle)

        self._attr_is_on = is_erev and (start <= now < end)
