"""Sensor platform for Molad Yiddish integration."""
from __future__ import annotations
from datetime import date, timedelta
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

from .molad_lib.helper import MoladHelper

_LOGGER = logging.getLogger(__name__)

# Yiddish translations
DAY_MAPPING = {
    "Sunday":   "זונטאג",
    "Monday":   "מאנטאג",
    "Tuesday":  "דינסטאג",
    "Wednesday":"מיטוואך",
    "Thursday": "דאנערשטאג",
    "Friday":   "פרייטאג",
    "Shabbos":  "שבת",
}

MONTH_MAPPING = {
    "Tishri":   "תשרי",
    "Cheshvan": "חשוון",
    "Kislev":   "כסלו",
    "Tevet":    "טבת",
    "Shvat":    "שבט",
    "Adar":     "אדר",
    "Adar I":   "אדר א",
    "Adar II":  "אדר ב",
    "Nissan":   "ניסן",
    "Iyar":     "אייר",
    "Sivan":    "סיון",
    "Tammuz":   "תמוז",
    "Av":       "אב",
    "Elul":     "אלול",
}

TIME_OF_DAY = {
    "am": lambda h: "פארטאגס" if h < 6 else "צופרי",
    "pm": lambda h: "נאכמיטאג" if h < 18 else "ביינאכט",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Molad Yiddish sensor."""
    async_add_entities([MoladYiddishSensor(hass)])


class MoladYiddishSensor(SensorEntity):
    """Representation of a Molad Yiddish sensor."""

    _attr_name = "Molad (ייִדיש)"
    _attr_unique_id = "molad_yiddish_sensor"

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._molad = MoladHelper(hass.config)
        self._attr_state = None
        self._attr_extra_state_attributes: dict[str, any] = {}
        # Refresh hourly so we catch the molad moment precisely
        async_track_time_interval(hass, self.async_update, timedelta(hours=1))

    async def async_update(self, now=None) -> None:
        """Fetch new state data for the sensor."""
        today = date.today()
        try:
            m = self._molad.get_molad(today)
        except Exception as e:
            _LOGGER.error("Failed to compute molad: %s", e)
            self._attr_state = None
            return

        day       = m.molad.day
        hours     = m.molad.hours
        minutes   = m.molad.minutes
        chalakim  = m.molad.chalakim
        ampm      = m.molad.am_or_pm

        day_yd    = DAY_MAPPING.get(day, day)
        mon_yd    = MONTH_MAPPING.get(m.rosh_chodesh.month, m.rosh_chodesh.month)
        tod       = TIME_OF_DAY[ampm](hours)
        chal_text = "חלק" if chalakim == 1 else "חלקים"
        hour12    = hours % 12 or 12

        self._attr_state = (
            f"מולד {day_yd} {tod}, "
            f"{minutes} מינוט און {chalakim} {chal_text} נאך {hour12}"
        )

        rc_days  = [ DAY_MAPPING.get(d, d) for d in m.rosh_chodesh.days ]
        rc_dates = [ d.strftime("%Y-%m-%d") for d in m.rosh_chodesh.gdays ]

        self._attr_extra_state_attributes = {
            "month_name":           mon_yd,
            "rosh_chodesh_days":    rc_days,
            "rosh_chodesh_dates":   rc_dates,
            "is_shabbos_mevorchim": m.is_shabbos_mevorchim,
            "is_upcoming_shabbos_mevorchim": m.is_upcoming_shabbos_mevorchim,
        }

        _LOGGER.debug("Molad Yiddish updated")

    @property
    def icon(self) -> str:
        return "mdi:calendar-star"
