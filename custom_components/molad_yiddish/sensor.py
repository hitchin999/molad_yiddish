# custom_components/molad_yiddish/sensor.py

from __future__ import annotations
from datetime import date, timedelta
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
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
    """Set up the Molad Yiddish sensor."""
    async_add_entities([MoladYiddishSensor(hass)])


class MoladYiddishSensor(SensorEntity):
    """Molad (ייִדיש) sensor with full Yiddish output."""

    _attr_name = "Molad (ייִדיש)"
    _attr_unique_id = "molad_yiddish_sensor"
    _attr_entity_id = "sensor.molad_yiddish"   # ← force this entity_id

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._helper = MoladHelper(hass.config)
        self._attr_state = None
        self._attr_extra_state_attributes: dict[str, any] = {}
        # Update hourly to catch the molad moment
        async_track_time_interval(hass, self.async_update, timedelta(hours=1))

    async def async_update(self, now=None) -> None:
        """Fetch new state data."""
        today = date.today()
        try:
            m = self._helper.get_molad(today)
        except Exception as e:
            _LOGGER.error("Failed to compute molad: %s", e)
            self._attr_state = None
            return

        # Raw fields
        day_en    = m.molad.day
        hours     = m.molad.hours
        minutes   = m.molad.minutes
        ampm      = m.molad.am_or_pm
        chalakim  = m.molad.chalakim

        # Yiddish translations
        day_yd    = DAY_MAPPING.get(day_en, day_en)
        tod       = TIME_OF_DAY[ampm](hours)
        chal_txt  = "חלק" if chalakim == 1 else "חלקים"
        hour12    = hours % 12 or 12
        mon_en    = m.rosh_chodesh.month
        mon_yd    = MONTH_MAPPING.get(mon_en, mon_en)

        # Build the Yiddish‐only state string:
        # e.g. "מולד זונטאג פארטאגס, 15 מינוט און 5 חלקים נאך 2"
        state_str = (
            f"מולד {day_yd} {tod}, "
            f"{minutes} מינוט און {chalakim} {chal_txt} נאך {hour12}"
        )
        self._attr_state = state_str

        # Rosh Chodesh days & dates (in Yiddish & ISO):
        rc_days_en  = m.rosh_chodesh.days
        rc_days_yd  = [DAY_MAPPING.get(d, d) for d in rc_days_en]
        rc_dates_iso = [d.strftime("%Y-%m-%d") for d in m.rosh_chodesh.gdays]
        rc_text     = " & ".join(rc_days_yd) if len(rc_days_yd) > 1 else (rc_days_yd[0] if rc_days_yd else "")

        # Mirror all your old attributes — values now in Yiddish
        self._attr_extra_state_attributes = {
            "icon":                         "mdi:moon-waxing-crescent",
            "friendly_name":                "Molad (ייִדיש)",
            "day":                          day_yd,
            "hours":                        hours,
            "minutes":                      minutes,
            "time_of_day":                  tod,
            "chalakim":                     chalakim,
            "friendly":                     state_str,
            "rosh_chodesh":                 rc_text,
            "rosh_chodesh_days":            rc_days_yd,
            "rosh_chodesh_dates":           rc_dates_iso,
            "is_shabbos_mevorchim":         m.is_shabbos_mevorchim,
            "is_upcoming_shabbos_mevorchim":m.is_upcoming_shabbos_mevorchim,
            "month_name":                   mon_yd,
        }

    @property
    def icon(self) -> str:
        """Return the icon for the sensor."""
        return "mdi:calendar-star"
