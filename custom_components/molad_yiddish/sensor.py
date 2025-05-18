# custom_components/molad_yiddish/sensor.py

from __future__ import annotations
import logging
from datetime import date, timedelta
from zoneinfo import ZoneInfo

from astral import LocationInfo
from astral.sun import sun
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

from .molad_lib.helper import MoladHelper, MoladDetails

_LOGGER = logging.getLogger(__name__)

# Yiddish translations
DAY_MAPPING = {
    "Sunday":    "זונטאג",
    "Monday":    "מאנטאג",
    "Tuesday":   "דינסטאג",
    "Wednesday": "מיטוואך",
    "Thursday":  "דאנערשטאג",
    "Friday":    "פרייטאג",
    "Shabbos":   "שבת",
}

MONTH_MAPPING = {
    "Tishri":   "תשרי",   "Cheshvan": "חשוון", "Kislev":   "כסלו",
    "Tevet":    "טבת",     "Shvat":    "שבט",    "Adar":     "אדר",
    "Adar I":   "אדר א",   "Adar II":  "אדר ב",  "Nissan":   "ניסן",
    "Iyar":     "אייר",    "Sivan":    "סיון",   "Tammuz":   "תמוז",
    "Av":       "אב",      "Elul":     "אלול",
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
    """Set up Molad Yiddish sensors."""
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
    """Main Molad (ייִדיש) sensor."""

    _attr_name = "Molad Yiddish"
    _attr_unique_id = "molad_yiddish"
    _attr_entity_id = "sensor.molad_yiddish"

    def __init__(self, hass: HomeAssistant, helper: MoladHelper) -> None:
        self.hass = hass
        self.helper = helper
        self._attr_state = None
        self._attr_extra_state_attributes: dict[str, any] = {}
        async_track_time_interval(hass, self.async_update, timedelta(hours=1))

    async def async_update(self, now=None) -> None:
        today = date.today()
        try:
            m: MoladDetails = self.helper.get_molad(today)
        except Exception as e:
            _LOGGER.error("Molad update failed: %s", e)
            self._attr_state = None
            return

        # Build the Yiddish Molad state string
        day_yd   = DAY_MAPPING[m.molad.day]
        h, mi    = m.molad.hours, m.molad.minutes
        ap       = m.molad.am_or_pm
        tod      = TIME_OF_DAY[ap](h)
        chal     = m.molad.chalakim
        chal_txt = "חלק" if chal == 1 else "חלקים"
        hh12     = h % 12 or 12
        state_str = f"מולד {day_yd} {tod}, {mi} מינוט און {chal} {chal_txt} נאך {hh12}"
        self._attr_state = state_str

        # Astral location setup
        loc = LocationInfo(
            name="home",
            region="",
            timezone=self.hass.config.time_zone,
            latitude=self.hass.config.latitude,
            longitude=self.hass.config.longitude,
        )
        tz = ZoneInfo(self.hass.config.time_zone)

        # 1) raw UTC-midnight for DevTools
        rc_midnight = [
            f"{gd.isoformat()}T00:00:00Z"
            for gd in m.rosh_chodesh.gdays
        ]

        # 2) true local nightfall+72m, on the day before each R”Ch
        rc_nightfall: list[str] = []
        for gd in m.rosh_chodesh.gdays:
            prev_day = gd - timedelta(days=1)
            s = sun(loc.observer, date=prev_day, tzinfo=tz)
            nf = s["sunset"] + timedelta(minutes=72)
            rc_nightfall.append(nf.isoformat())

        rc_yd  = [DAY_MAPPING[d] for d in m.rosh_chodesh.days]
        rc_text= rc_yd[0] if len(rc_yd) == 1 else " & ".join(rc_yd)
        mon_yd = MONTH_MAPPING[m.rosh_chodesh.month]

        # Publish attributes
        self._attr_extra_state_attributes = {
            "day":                            day_yd,
            "hours":                          h,
            "minutes":                        mi,
            "am_or_pm":                       ap,
            "time_of_day":                    tod,
            "chalakim":                       chal,
            "friendly":                       state_str,
            "rosh_chodesh_midnight":          rc_midnight,
            "rosh_chodesh_nightfall":         rc_nightfall,
            "rosh_chodesh":                   rc_text,
            "rosh_chodesh_days":              rc_yd,
            "is_shabbos_mevorchim":           m.is_shabbos_mevorchim,
            "is_upcoming_shabbos_mevorchim":  m.is_upcoming_shabbos_mevorchim,
            "month_name":                     mon_yd,
        }

    def update(self) -> None:
        """Legacy sync update so update_before_add fires immediately."""
        self.hass.async_create_task(self.async_update())

    @property
    def icon(self) -> str:
        return "mdi:calendar-star"


class ShabbosMevorchimSensor(BinarySensorEntity):
    """Binary sensor: is *today* Shabbos Mevorchim?"""

    _attr_name = "Shabbos Mevorchim Yiddish"
    _attr_unique_id = "shabbos_mevorchim_yiddish"
    _attr_entity_id = "binary_sensor.shabbos_mevorchim_yiddish"

    def __init__(self, hass: HomeAssistant, helper: MoladHelper) -> None:
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
    """Binary sensor: is the *upcoming* Shabbos Mevorchim?"""

    _attr_name = "Upcoming Shabbos Mevorchim Yiddish"
    _attr_unique_id = "upcoming_shabbos_mevorchim_yiddish"
    _attr_entity_id = "binary_sensor.upcoming_shabbos_mevorchim_yiddish"

    def __init__(self, hass: HomeAssistant, helper: MoladHelper) -> None:
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
