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


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up Molad Yiddish with three sensors."""
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
    """Molad (ייִדיש) sensor."""

    _attr_name = "Molad (ייִדיש)"
    _attr_unique_id = "molad_yiddish"
    _attr_entity_id = "sensor.molad_yiddish"

    def __init__(self, hass: HomeAssistant, helper: MoladHelper) -> None:
        """Initialize the Molad sensor."""
        self.hass = hass
        self.helper = helper
        self._attr_state = None
        self._attr_extra_state_attributes: dict[str, any] = {}
        # Update hourly to catch the molad moment
        async_track_time_interval(hass, self.async_update, timedelta(hours=1))

    async def async_update(self, now=None) -> None:
        """Fetch Molad and update state+attributes."""
        today = date.today()
        try:
            m = self.helper.get_molad(today)
        except Exception as e:
            _LOGGER.error("Failed to compute Molad: %s", e)
            self._attr_state = None
            return

        # core Molad string
        self._attr_state = m.molad.friendly

        # mirror detailed attributes
        self._attr_extra_state_attributes = {
            "day":                          m.molad.day,
            "hours":                        m.molad.hours,
            "minutes":                      m.molad.minutes,
            "am_or_pm":                     m.molad.am_or_pm,
            "chalakim":                     m.molad.chalakim,
            "friendly":                     m.molad.friendly,
            "rosh_chodesh":                 m.rosh_chodesh.text,
            "rosh_chodesh_days":            m.rosh_chodesh.days,
            "rosh_chodesh_dates":           [d.strftime("%Y-%m-%d") for d in m.rosh_chodesh.gdays],
            "is_shabbos_mevorchim":         m.is_shabbos_mevorchim,
            "is_upcoming_shabbos_mevorchim":m.is_upcoming_shabbos_mevorchim,
            "month_name":                   m.rosh_chodesh.month,
        }

    @property
    def icon(self) -> str:
        return "mdi:calendar-star"


class ShabbosMevorchimSensor(SensorEntity):
    """Sensor for “Is today Shabbos Mevorchim?”."""

    _attr_name = "Shabbos Mevorchim (ייִדיש)"
    _attr_unique_id = "shabbos_mevorchim_yiddish"
    _attr_entity_id = "sensor.shabbos_mevorchim_yiddish"

    def __init__(self, hass: HomeAssistant, helper: MoladHelper) -> None:
        """Initialize the Shabbos Mevorchim sensor."""
        self.hass = hass
        self.helper = helper
        self._attr_state = None
        async_track_time_interval(hass, self.async_update, timedelta(hours=1))

    async def async_update(self, now=None) -> None:
        """Fetch and update whether today is Shabbos Mevorchim."""
        today = date.today()
        try:
            m = self.helper.get_molad(today)
            self._attr_state = m.is_shabbos_mevorchim
        except Exception as e:
            _LOGGER.error("Failed to compute Shabbos Mevorchim: %s", e)
            self._attr_state = False

    @property
    def icon(self) -> str:
        return "mdi:star-outline"


class UpcomingShabbosMevorchimSensor(SensorEntity):
    """Sensor for “Is the upcoming Shabbos Mevorchim?”."""

    _attr_name = "Upcoming Shabbos Mevorchim (ייִדיש)"
    _attr_unique_id = "upcoming_shabbos_mevorchim_yiddish"
    _attr_entity_id = "sensor.upcoming_shabbos_mevorchim_yiddish"

    def __init__(self, hass: HomeAssistant, helper: MoladHelper) -> None:
        """Initialize the Upcoming Shabbos Mevorchim sensor."""
        self.hass = hass
        self.helper = helper
        self._attr_state = None
        async_track_time_interval(hass, self.async_update, timedelta(hours=1))

    async def async_update(self, now=None) -> None:
        """Fetch and update whether the upcoming Shabbos is Mevorchim."""
        today = date.today()
        try:
            m = self.helper.get_molad(today)
            self._attr_state = m.is_upcoming_shabbos_mevorchim
        except Exception as e:
            _LOGGER.error("Failed to compute Upcoming Shabbos Mevorchim: %s", e)
            self._attr_state = False

    @property
    def icon(self) -> str:
        return "mdi:star-outline"
