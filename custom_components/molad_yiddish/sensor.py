# custom_components/molad_yiddish/sensor.py

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
from homeassistant.util.dt import now as dt_now

from .molad_lib.helper import MoladHelper, MoladDetails

_LOGGER = logging.getLogger(__name__)

# ———————————————————————————————————————————————
# Yiddish mappings
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
# ———————————————————————————————————————————————


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
            RoshChodeshTodaySensor(hass, helper),
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
        self._attr_extra_state_attributes = {}
        async_track_time_interval(hass, self.async_update, timedelta(hours=1))

    async def async_update(self, now=None) -> None:
        today = date.today()
        try:
            m: MoladDetails = self.helper.get_molad(today)
        except Exception as e:
            _LOGGER.error("Molad update failed: %s", e)
            self._attr_state = None
            return

        # Build Yiddish Molad state
        day_yd   = DAY_MAPPING[m.molad.day]
        h, mi    = m.molad.hours, m.molad.minutes
        ap       = m.molad.am_or_pm
        tod      = TIME_OF_DAY[ap](h)
        chal     = m.molad.chalakim
        chal_txt = "חלק" if chal == 1 else "חלקים"
        hh12     = h % 12 or 12
        state_str = f"מולד {day_yd} {tod}, {mi} מינוט און {chal} {chal_txt} נאך {hh12}"
        self._attr_state = state_str

        # Astral & timezone setup
        loc = LocationInfo(
            name="home",
            region="",
            timezone=self.hass.config.time_zone,
            latitude=self.hass.config.latitude,
            longitude=self.hass.config.longitude,
        )
        tz = ZoneInfo(self.hass.config.time_zone)

        # R”Ch UTC-midnight (for DevTools)
        rc_midnight = [
            f"{gd.isoformat()}T00:00:00Z"
            for gd in m.rosh_chodesh.gdays
        ]

        # R”Ch true nightfall+72m on the **previous** day
        rc_nightfall: list[str] = []
        for gd in m.rosh_chodesh.gdays:
            prev_day = gd - timedelta(days=1)
            s = sun(loc.observer, date=prev_day, tzinfo=tz)
            nf = s["sunset"] + timedelta(minutes=72)
            rc_nightfall.append(nf.isoformat())

        rc_yd   = [DAY_MAPPING[d] for d in m.rosh_chodesh.days]
        rc_text = rc_yd[0] if len(rc_yd) == 1 else " & ".join(rc_yd)
        mon_yd  = MONTH_MAPPING[m.rosh_chodesh.month]

        self._attr_extra_state_attributes = {
            "day":                           day_yd,
            "hours":                         h,
            "minutes":                       mi,
            "am_or_pm":                      ap,
            "time_of_day":                   tod,
            "chalakim":                      chal,
            "friendly":                      state_str,
            "rosh_chodesh_midnight":         rc_midnight,
            "rosh_chodesh_nightfall":        rc_nightfall,
            "rosh_chodesh":                  rc_text,
            "rosh_chodesh_days":             rc_yd,
            "is_shabbos_mevorchim":          m.is_shabbos_mevorchim,
            "is_upcoming_shabbos_mevorchim": m.is_upcoming_shabbos_mevorchim,
            "month_name":                    mon_yd,
        }

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

    @property
    def icon(self) -> str:
        return "mdi:star-outline"


class RoshChodeshTodaySensor(SensorEntity):
    """Sensor: “ראש חודש היום” once nightfall+72m has passed."""

    _attr_name = "Rosh Chodesh Today Yiddish"
    _attr_unique_id = "rosh_chodesh_today_yiddish"
    _attr_entity_id = "sensor.rosh_chodesh_today_yiddish"

    def __init__(self, hass: HomeAssistant, helper: MoladHelper) -> None:
        self.hass = hass
        self.helper = helper
        # set a non-None default immediately
        self._attr_state = "Not Rosh Chodesh Today"
        # re-evaluate every minute
        async_track_time_interval(hass, self.async_update, timedelta(minutes=1))
        # schedule the first run
        hass.async_create_task(self.async_update())

    def update(self) -> None:
        """Make update_before_add=True actually call our async_update."""
        self.hass.async_create_task(self.async_update())

    async def async_update(self, now_arg=None) -> None:
        today = date.today()
        try:
            details = self.helper.get_molad(today)
        except Exception as e:
            _LOGGER.error("R”Ch Today update failed: %s", e)
            return

        month = MONTH_MAPPING[details.rosh_chodesh.month]

        loc = LocationInfo(
            name="home", region="", timezone=self.hass.config.time_zone,
            latitude=self.hass.config.latitude, longitude=self.hass.config.longitude,
        )
        tz = ZoneInfo(self.hass.config.time_zone)

        # calculate previous-day nightfall+72m for each R”Ch date
        nightfalls: list[datetime] = []
        for gd in details.rosh_chodesh.gdays:
            prev_day = gd - timedelta(days=1)
            s = sun(loc.observer, date=prev_day, tzinfo=tz)
            nf = s["sunset"] + timedelta(minutes=72)
            nightfalls.append(nf)

        now_local = dt_now()
        new_state = "Not Rosh Chodesh Today"
        for idx, nf in enumerate(nightfalls):
            if now_local >= nf and now_local < nf + timedelta(days=1):
                if len(nightfalls) == 1:
                    new_state = f"ראש חודש {month}"
                else:
                    prefix = ["א", "ב"][idx]
                    new_state = f"{prefix}׳ ד׳ראש חודש {month}"
                break

        self._attr_state = new_state

    @property
    def icon(self) -> str:
        return "mdi:calendar-star"
