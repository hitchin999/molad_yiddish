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
    """Set up the three Molad Yiddish sensors."""
    helper = MoladHelper(hass.config)
    async_add_entities(
        [
            MoladYiddishSensor(hass, helper),
            ShabbosMevorchimSensor(hass, helper),
            UpcomingShabbosMevorchimSensor(hass, helper),
        ],
        update_before_add=True,
    )


class MoladYiddishSensor(SensorEntity):
    """Molad (ייִדיש) sensor with full Yiddish output."""

    _attr_name = "Molad Yiddish"
    _attr_unique_id = "molad_yiddish"
    _attr_entity_id = "sensor.molad_yiddish"

    def __init__(self, hass: HomeAssistant, helper: MoladHelper) -> None:
        """Initialize the Molad sensor."""
        self.hass = hass
        self.helper = helper
        self._attr_state = None
        self._attr_extra_state_attributes: dict[str, any] = {}
        # Update immediately on add, then hourly
        async_track_time_interval(hass, self.async_update, timedelta(hours=1))

    async def async_update(self, now=None) -> None:
        """Fetch Molad details and populate state + attributes."""
        today = date.today()
        try:
            m: MoladDetails = self.helper.get_molad(today)
        except Exception as e:
            _LOGGER.error("Failed to compute Molad: %s", e)
            self._attr_state = None
            return

        # Build the Yiddish‐only state string
        day_yd   = DAY_MAPPING.get(m.molad.day, m.molad.day)
        hours    = m.molad.hours
        minutes  = m.molad.minutes
        ampm     = m.molad.am_or_pm
        tod      = TIME_OF_DAY[ampm](hours)
        chalakim = m.molad.chalakim
        chal_txt = "חלק" if chalakim == 1 else "חלקים"
        hour12   = hours % 12 or 12

        state_str = (
            f"מולד {day_yd} {tod}, "
            f"{minutes} מינוט און {chalakim} {chal_txt} נאך {hour12}"
        )
        self._attr_state = state_str

        # Translate rosh chodesh details
        rc_days_en  = m.rosh_chodesh.days
        rc_days_yd  = [DAY_MAPPING.get(d, d) for d in rc_days_en]
        rc_dates    = [d.strftime("%Y-%m-%d") for d in m.rosh_chodesh.gdays]
        rc_text     = " & ".join(rc_days_yd) if len(rc_days_yd) == 2 else (rc_days_yd[0] if rc_days_yd else "")

        # Yiddish month name
        mon_yd = MONTH_MAPPING.get(m.rosh_chodesh.month, m.rosh_chodesh.month)

        # Populate **all** attributes in Yiddish
        self._attr_extra_state_attributes = {
            "day":                          day_yd,
            "hours":                        hours,
            "minutes":                      minutes,
            "am_or_pm":                     ampm,
            "time_of_day":                  tod,
            "chalakim":                     chalakim,
            "friendly":                     state_str,
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
    """Sensor for “Is today Shabbos Mevorchim?”."""

    _attr_name = "Shabbos Mevorchim Yiddish"
    _attr_unique_id = "shabbos_mevorchim_yiddish"
    _attr_entity_id = "sensor.shabbos_mevorchim_yiddish"

    def __init__(self, hass: HomeAssistant, helper: MoladHelper) -> None:
        self.hass = hass
        self.helper = helper
        self._attr_state = None
        async_track_time_interval(hass, self.async_update, timedelta(hours=1))

    async def async_update(self, now=None) -> None:
        """Fetch whether today is Shabbos Mevorchim."""
        today = date.today()
        try:
            m: MoladDetails = self.helper.get_molad(today)
            self._attr_state = m.is_shabbos_mevorchim
        except Exception as e:
            _LOGGER.error("Failed to compute Shabbos Mevorchim: %s", e)
            self._attr_state = False

    @property
    def icon(self) -> str:
        return "mdi:star-outline"


class UpcomingShabbosMevorchimSensor(SensorEntity):
    """Sensor for “Is the upcoming Shabbos Mevorchim?”."""

    _attr_name = "Upcoming Shabbos Mevorchim Yiddish"
    _attr_unique_id = "upcoming_shabbos_mevorchim_yiddish"
    _attr_entity_id = "sensor.upcoming_shabbos_mevorchim_yiddish"

    def __init__(self, hass: HomeAssistant, helper: MoladHelper) -> None:
        self.hass = hass
        self.helper = helper
        self._attr_state = None
        async_track_time_interval(hass, self.async_update, timedelta(hours=1))

    async def async_update(self, now=None) -> None:
        """Fetch whether the next Shabbos is Mevorchim."""
        today = date.today()
        try:
            m: MoladDetails = self.helper.get_molad(today)
            self._attr_state = m.is_upcoming_shabbos_mevorchim
        except Exception as e:
            _LOGGER.error("Failed to compute Upcoming Shabbos Mevorchim: %s", e)
            self._attr_state = False

    @property
    def icon(self) -> str:
        return "mdi:star-outline"
