# /config/custom_components/molad_yiddish/sensor.py
from __future__ import annotations
import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from astral import LocationInfo
from astral.sun import sun
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

from hdate.converters import gdate_to_jdn
from hdate.hebrew_date import HebrewDate

import pyluach.dates as pdates
from pyluach.hebrewcal import HebrewDate as PHebrewDate

from .molad_lib.helper import MoladHelper, MoladDetails
from .molad_lib.sfirah_helper import SfirahHelper
from .sfirah_sensor import SefirahCounterYiddish, SefirahCounterMiddosYiddish
from .special_shabbos_sensor import SpecialShabbosSensor
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DAY_MAPPING = {
    "Sunday": "זונטאג",
    "Monday": "מאנטאג",
    "Tuesday": "דינסטאג",
    "Wednesday": "מיטוואך",
    "Thursday": "דאנערשטאג",
    "Friday": "פרייטאג",
    "Shabbos": "שבת",
}

MONTH_MAPPING = {
    "Tishri": "תשרי", "Cheshvan": "חשוון", "Kislev": "כסלו",
    "Tevet": "טבת", "Shvat": "שבט", "Adar": "אדר",
    "Adar I": "אדר א", "Adar II": "אדר ב", "Nissan": "ניסן",
    "Iyar": "אייר", "Sivan": "סיון", "Tammuz": "תמוז",
    "Av": "אב", "Elul": "אלול",
}

TIME_OF_DAY = {
    "am": lambda h: "פארטאגס" if h < 6 else "צופרי",
    "pm": lambda h: "נאכמיטאג" if h < 18 else "ביינאכט",
}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up Molad Yiddish and related sensors with user-configurable offsets."""
    molad_helper = MoladHelper(hass.config)
    sfirah_helper = SfirahHelper(hass)
    strip_nikud = entry.options.get("strip_nikud", False)
    opts = hass.data[DOMAIN][entry.entry_id]
    candle_offset = opts.get("candlelighting_offset", 15)
    havdalah_offset = opts.get("havdalah_offset", 72)

    async_add_entities([
        MoladYiddishSensor(hass, molad_helper, candle_offset, havdalah_offset),
        YiddishDayLabelSensor(hass, candle_offset, havdalah_offset),
        ShabbosMevorchimSensor(hass, molad_helper),
        UpcomingShabbosMevorchimSensor(hass, molad_helper),
        SpecialShabbosSensor(),
        SefirahCounterYiddish(hass, sfirah_helper, strip_nikud, havdalah_offset),
        SefirahCounterMiddosYiddish(hass, sfirah_helper, strip_nikud, havdalah_offset),
    ], update_before_add=True)


class MoladYiddishSensor(SensorEntity):
    _attr_name = "Molad Yiddish"
    _attr_unique_id = "molad_yiddish"
    _attr_entity_id = "sensor.molad_yiddish"

    def __init__(
        self,
        hass: HomeAssistant,
        helper: MoladHelper,
        candle_offset: int,
        havdalah_offset: int,
    ) -> None:
        super().__init__()
        self.hass = hass
        self.helper = helper
        self._candle_offset = candle_offset
        self._havdalah_offset = havdalah_offset
        self._attr_native_value = None
        self._attr_extra_state_attributes: dict[str, any] = {}
        async_track_time_interval(hass, self.async_update, timedelta(hours=1))

    async def async_update(self, now=None) -> None:
        today = date.today()
        jdn = gdate_to_jdn(today)
        heb = HebrewDate.from_jdn(jdn)
        base_date = today - timedelta(days=15) if heb.day < 3 else today

        try:
            details: MoladDetails = self.helper.get_molad(base_date)
        except Exception as e:
            _LOGGER.error("Molad update failed: %s", e)
            self._attr_native_value = None
            return

        m = details.molad
        h, mi = m.hours, m.minutes
        tod = TIME_OF_DAY[m.am_or_pm](h)
        chal = m.chalakim
        chal_txt = "חלק" if chal == 1 else "חלקים"
        hh12 = h % 12 or 12

        tz = ZoneInfo(self.hass.config.time_zone)
        now_local = now.astimezone(tz) if now else datetime.now(tz)
        loc = LocationInfo(latitude=self.hass.config.latitude,
                           longitude=self.hass.config.longitude,
                           timezone=self.hass.config.time_zone)

        # Determine if it's Motzaei Shabbos
        motzei = False
        if m.day == "Shabbos":
            sd = sun(loc.observer, date=now_local.date(), tzinfo=tz)
            motzei_start = sd["sunset"] + timedelta(minutes=self._havdalah_offset)
            next_mid = (now_local.replace(hour=0, minute=0) + timedelta(days=1)).replace(tzinfo=tz)
            motzei = motzei_start <= now_local < next_mid

        if motzei:
            day_yd = 'מוצש"ק'
            state = f"מולד {day_yd}, {mi} מינוט און {chal} {chal_txt} נאך {hh12}"
        else:
            day_yd = DAY_MAPPING.get(m.day, m.day)
            state = f"מולד {day_yd} {tod}, {mi} מינוט און {chal} {chal_txt} נאך {hh12}"

        self._attr_native_value = state

        # Rosh Chodesh attributes
        rc = details.rosh_chodesh
        rc_mid = [f"{gd.isoformat()}T00:00:00Z" for gd in rc.gdays]
        rc_night = []
        for gd in rc.gdays:
            prev = gd - timedelta(days=1)
            sd = sun(loc.observer, date=prev, tzinfo=tz)
            rc_night.append((sd["sunset"] + timedelta(minutes=self._havdalah_offset)).isoformat())

        rc_days = [DAY_MAPPING.get(d, d) for d in rc.days]
        rc_text = rc_days[0] if len(rc_days) == 1 else " & ".join(rc_days)

        self._attr_extra_state_attributes = {
            "day": day_yd,
            "hours": h,
            "minutes": mi,
            "time_of_day": tod,
            "chalakim": chal,
            "friendly": state,
            "rosh_chodesh_midnight": rc_mid,
            "rosh_chodesh_nightfall": rc_night,
            "rosh_chodesh": rc_text,
            "rosh_chodesh_days": rc_days,
            "is_shabbos_mevorchim": details.is_shabbos_mevorchim,
            "is_upcoming_shabbos_mevorchim": details.is_upcoming_shabbos_mevorchim,
            "month_name": MONTH_MAPPING.get(rc.month, rc.month),
        }

    def update(self) -> None:
        self.hass.async_create_task(self.async_update())

    @property
    def icon(self) -> str:
        return "mdi:calendar-star"


class YiddishDayLabelSensor(SensorEntity):
    """Sensor for standalone Yiddish day label."""

    _attr_name = "Yiddish Day Label"
    _attr_unique_id = "yiddish_day_label"

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
        self._state = None

    @property
    def native_value(self):
        return self._state

    async def async_update(self, now=None) -> None:
        tz = ZoneInfo(self.hass.config.time_zone)
        loc = LocationInfo(latitude=self.hass.config.latitude,
                           longitude=self.hass.config.longitude,
                           timezone=self.hass.config.time_zone)
        current = datetime.now(tz)
        s = sun(loc.observer, date=current.date(), tzinfo=tz)
        candle = s["sunset"] - timedelta(minutes=self._candle)
        havdalah = s["sunset"] + timedelta(minutes=self._havdalah)

        # Hebrew date
        g = pdates.GregorianDate(current.year, current.month, current.day)
        hdate = g.to_heb()
        if current >= s["sunset"]:
            hdate = PHebrewDate(hdate.year, hdate.month, hdate.day) + 1

        # Holiday
        is_tov = bool(hdate.festival(israel=False, include_working_days=False))

        # Shabbos
        wd = current.weekday()
        is_shab = (wd == 4 and current >= candle) or (wd == 5 and current < havdalah)

        if is_shab:
            lbl = "שבת קודש"
        elif is_tov:
            lbl = "יום טוב"
        elif wd == 4 and current.hour >= 12:
            lbl = "ערש\"ק"
        elif wd == 5 and current >= havdalah:
            lbl = "מוצש\"ק"
        else:
            days = ["זונטאג","מאנטאג","דינסטאג","מיטוואך","דאנערשטאג","פרייטאג","שבת"]
            idx = {6:0,0:1,1:2,2:3,3:4,4:5,5:6}[wd]
            lbl = days[idx]

        self._state = lbl

    def update(self) -> None:
        self.hass.async_create_task(self.async_update())


class ShabbosMevorchimSensor(BinarySensorEntity):
    _attr_name = "Shabbos Mevorchim Yiddish"
    _attr_unique_id = "shabbos_mevorchim_yiddish"
    _attr_entity_id = "binary_sensor.shabbos_mevorchim_yiddish"

    def __init__(self, hass: HomeAssistant, helper: MoladHelper) -> None:
        super().__init__()
        self.hass = hass
        self.helper = helper
        self._attr_is_on = False
        async_track_time_interval(hass, self.async_update, timedelta(hours=1))

    async def async_update(self, now=None) -> None:
        try:
            self._attr_is_on = self.helper.get_molad(date.today()).is_shabbos_mevorchim
        except Exception as e:
            _LOGGER.error("Shabbos Mevorchim failed: %s", e)
            self._attr_is_on = False

    def update(self) -> None:
        self.hass.async_create_task(self.async_update())

    @property
    def icon(self) -> str:
        return "mdi:star-outline"


class UpcomingShabbosMevorchimSensor(BinarySensorEntity):
    _attr_name = "Upcoming Shabbos Mevorchim Yiddish"
    _attr_unique_id = "upcoming_shabbos_mevorchim_yiddish"
    _attr_entity_id = "binary_sensor.upcoming_shabbos_mevorchim_yiddish"

    def __init__(self, hass: HomeAssistant, helper: MoladHelper) -> None:
        super().__init__()
        self.hass = hass
        self.helper = helper
        self._attr_is_on = False
        async_track_time_interval(hass, self.async_update, timedelta(hours=1))

    async def async_update(self, now=None) -> None:
        try:
            self._attr_is_on = self.helper.get_molad(date.today()).is_upcoming_shabbos_mevorchim
        except Exception as e:
            _LOGGER.error("Upcoming Shabbos Mevorchim failed: %s", e)
            self._attr_is_on = False

    def update(self) -> None:
        self.hass.async_create_task(self.async_update())

    @property
    def icon(self) -> str:
        return "mdi:star-outline"
