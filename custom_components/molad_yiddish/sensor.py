# custom_components/molad_yiddish/sensor.py

from __future__ import annotations
from datetime import date, timedelta
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

from .molad_lib.helper import MoladHelper, MoladDetails

_LOGGER = logging.getLogger(__name__)

# Yiddish translations for days/months/time-of-day
DAY_MAPPING = {
    "Sunday": "זונטаг", "Monday": "מאנטאג", "Tuesday": "דינסטאג",
    "Wednesday": "מיטוואך", "Thursday": "דאנערשטאג",
    "Friday": "פרייטאג", "Shabbos": "שבת",
}
MONTH_MAPPING = {
    "Tishri": "תשרי",   "Cheshvan": "חשוון", "Kislev": "כסלו",
    "Tevet": "טבת",     "Shvat":    "שבט",    "Adar":   "אדר",
    "Adar I": "אדר א",  "Adar II": "אדר ב",    "Nissan": "ניסן",
    "Iyar":   "אייר",   "Sivan":   "סיון",   "Tammuz":"תמוז",
    "Av":     "אב",     "Elul":    "אלול",
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
    helper = MoladHelper(hass.config)
    async_add_entities(
        [
            MoladYiddishSensor(hass, helper),
            ShabbosMevorchimSensor(hass, helper),
            UpcomingShabbosMevorchimSensor(hass, helper),
        ],
        True  # update_before_add
    )


class MoladYiddishSensor(SensorEntity):
    _attr_name = "Molad Yiddish"
    _attr_unique_id = "molad_yiddish"
    _attr_entity_id = "sensor.molad_yiddish"

    def __init__(self, hass: HomeAssistant, helper: MoladHelper) -> None:
        self.helper = helper
        async_track_time_interval(hass, self.async_update, timedelta(hours=1))

    async def async_update(self, now=None) -> None:
        today = date.today()
        try:
            m: MoladDetails = self.helper.get_molad(today)
        except Exception as e:
            _LOGGER.error("Molad update failed: %s", e)
            self._attr_state = None
            return

        # Build state string in Yiddish
        d_yd   = DAY_MAPPING[m.molad.day]
        h, mi  = m.molad.hours, m.molad.minutes
        ap     = m.molad.am_or_pm
        tod    = TIME_OF_DAY[ap](h)
        chal   = m.molad.chalakim
        chal_s = "חלק" if chal==1 else "חלקים"
        hh12   = h%12 or 12

        state = f"מולד {d_yd} {tod}, {mi} מינוט און {chal} {chal_s} נאך {hh12}"
        self._attr_state = state

        # R”Ch days & dates
        rc_days_en  = m.rosh_chodesh.days
        rc_days_yd  = [DAY_MAPPING[d] for d in rc_days_en]
        rc_dates    = [d.strftime("%Y-%m-%d") for d in m.rosh_chodesh.gdays]
        rc_text     = " & ".join(rc_days_yd) if len(rc_days_yd)==2 else (rc_days_yd[0] if rc_days_yd else "")

        # Yiddish month
        mon_yd = MONTH_MAPPING[m.rosh_chodesh.month]

        # All attributes in Yiddish
        self._attr_extra_state_attributes = {
            "day":                          d_yd,
            "hours":                        h,
            "minutes":                      mi,
            "am_or_pm":                     ap,
            "time_of_day":                  tod,
            "chalakim":                     chal,
            "friendly":                     state,
            "rosh_chodesh":                 rc_text,
            "rosh_chodesh_days":            rc_days_yd,
            "rosh_chodesh_dates":           rc_dates,
            "is_shabbos_mevorchim":         m.is_shabbos_mevorchim,
            "is_upcoming_shabbos_mevorchim":m.is_upcoming_shabbos_mevorchim,
            "month_name":                   mon_yd,
        }

    @property
    def icon(self) -> str:
        return "mdi:calendar-star"


class ShabbosMevorchimSensor(SensorEntity):
    _attr_name = "Shabbos Mevorchim Yiddish"
    _attr_unique_id = "shabbos_mevorchim_yiddish"
    _attr_entity_id = "sensor.shabbos_mevorchim_yiddish"

    def __init__(self, hass: HomeAssistant, helper: MoladHelper) -> None:
        self.helper = helper
        async_track_time_interval(hass, self.async_update, timedelta(hours=1))

    async def async_update(self, now=None) -> None:
        try:
            self._attr_state = self.helper.get_molad(date.today()).is_shabbos_mevorchim
        except Exception as e:
            _LOGGER.error("Shabbos Mevorchim failed: %s", e)
            self._attr_state = False

    @property
    def icon(self) -> str:
        return "mdi:star-outline"


class UpcomingShabbosMevorchimSensor(SensorEntity):
    _attr_name = "Upcoming Shabbos Mevorchim Yiddish"
    _attr_unique_id = "upcoming_shabbos_mevorchim_yiddish"
    _attr_entity_id = "sensor.upcoming_shabbos_mevorchim_yiddish"

    def __init__(self, hass: HomeAssistant, helper: MoladHelper) -> None:
        self.helper = helper
        async_track_time_interval(hass, self.async_update, timedelta(hours=1))

    async def async_update(self, now=None) -> None:
        try:
            self._attr_state = self.helper.get_molad(date.today()).is_upcoming_shabbos_mevorchim
        except Exception as e:
            _LOGGER.error("Upcoming Shabbos Mevorchim failed: %s", e)
            self._attr_state = False

    @property
    def icon(self) -> str:
        return "mdi:star-outline"
