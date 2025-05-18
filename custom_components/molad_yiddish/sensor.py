# custom_components/molad_yiddish/sensor.py

from __future__ import annotations
from datetime import date, timedelta
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.event import async_track_time_interval

from .molad_lib.helper import MoladHelper

_LOGGER = logging.getLogger(__name__)

# Yiddish translations
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
    "Tevet": "טבת",   "Shvat":    "שבט",    "Adar":  "אדר",
    "Adar I": "אדר א","Adar II": "אדר ב",  "Nissan":"ניסן",
    "Iyar":   "אייר", "Sivan":   "סיון",  "Tammuz":"תמוז",
    "Av":     "אב",    "Elul":    "אלול",
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
    async_add_entities([MoladYiddishSensor(hass)])


class MoladYiddishSensor(SensorEntity):
    """Molad Yiddish sensor, but entity_id forced to sensor.molad."""

    _attr_name = "Molad (ייִדיש)"
    _attr_unique_id = "molad_yiddish_sensor"
    # *** override the slugifier and force exactly this entity_id: ***
    _attr_entity_id = "sensor.molad"

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._molad = MoladHelper(hass.config)
        self._attr_state = None
        self._attr_extra_state_attributes: dict[str, any] = {}
        async_track_time_interval(hass, self.async_update, timedelta(hours=1))

    async def async_update(self, now=None) -> None:
        today = date.today()
        try:
            m = self._molad.get_molad(today)
        except Exception as e:
            _LOGGER.error("Failed to compute molad: %s", e)
            self._attr_state = None
            return

        # raw values
        day       = m.molad.day
        hours     = m.molad.hours
        minutes   = m.molad.minutes
        ampm      = m.molad.am_or_pm
        chalakim  = m.molad.chalakim
        friendly  = m.molad.friendly

        # Yiddish translations
        day_yd    = DAY_MAPPING.get(day, day)
        tod       = TIME_OF_DAY[ampm](hours)
        chal_txt  = "חלק" if chalakim == 1 else "חלקים"
        hour12    = hours % 12 or 12
        mon_yd    = MONTH_MAPPING.get(m.rosh_chodesh.month, m.rosh_chodesh.month)

        # build the sensor state exactly as before:
        self._attr_state = friendly

        # build lists for rosh chodesh days & dates
        rc_days  = [DAY_MAPPING.get(d, d) for d in m.rosh_chodesh.days]
        rc_dates = [g.strftime("%Y-%m-%d")         for g in m.rosh_chodesh.gdays]

        # mirror *all* your old attributes
        self._attr_extra_state_attributes = {
            "icon":                       "mdi:moon-waxing-crescent",
            "friendly_name":              "Molad",
            "day":                        day,
            "hours":                      hours,
            "minutes":                    minutes,
            "am_or_pm":                   ampm,
            "chalakim":                   chalakim,
            "friendly":                   friendly,
            "rosh_chodesh":               m.rosh_chodesh.text,
            "rosh_chodesh_days":          rc_days,
            "rosh_chodesh_dates":         rc_dates,
            "is_shabbos_mevorchim":       m.is_shabbos_mevorchim,
            "is_upcoming_shabbos_mevorchim": m.is_upcoming_shabbos_mevorchim,
            "month_name":                 mon_yd,
        }

    @property
    def icon(self) -> str:
        return "mdi:moon-waxing-crescent"
