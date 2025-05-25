# /config/custom_components/molad_yiddish/sfirah_sensor.py

import logging
import unicodedata
from datetime import timedelta
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later

from .molad_lib.sfirah_helper import SfirahHelper
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """
    Set up the Omer (Sefirah) sensors with optional nikud stripping and user-defined Havdalah offset.
    """
    # Pull options from entry (strip nikud, Havdalah offset)
    opts = hass.data[DOMAIN].get(entry.entry_id, {}) or {}
    strip_nikud = opts.get("strip_nikud", False)
    havdalah_offset = opts.get("havdalah_offset", 72)

    # Initialize helper with offset
    helper = SfirahHelper(hass, havdalah_offset)

    # Create sensor entities
    async_add_entities(
        [
            SefirahCounterYiddish(hass, helper, strip_nikud, havdalah_offset),
            SefirahCounterMiddosYiddish(hass, helper, strip_nikud, havdalah_offset),
        ],
        update_before_add=True,
    )


class BaseSefirahSensor(SensorEntity):
    """Base class for Sefirah (Omer) sensors."""

    def __init__(
        self,
        hass: HomeAssistant,
        helper: SfirahHelper,
        name: str,
        unique_id: str,
        strip_nikud: bool,
        havdalah_offset: int,
    ) -> None:
        super().__init__()
        self.hass = hass
        self._helper = helper
        self._strip = strip_nikud
        self._havdalah_offset = havdalah_offset
        self._state = None
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._unsub_sunset = None

    @property
    def native_value(self):
        return self._state

    async def async_update(self) -> None:
        """Fetch new state from helper and apply nikud stripping."""
        text = self._get_text()
        if self._strip:
            text = unicodedata.normalize('NFKC', text)
            text = ''.join(ch for ch in text if unicodedata.category(ch)[0] != 'M')
        self._state = text

    @callback
    def _schedule_after_sunset(self) -> None:
        """Schedule an update havdalah_offset minutes after sunset."""
        async_call_later(
            self.hass,
            self._havdalah_offset * 60,
            lambda _now: self.async_schedule_update_ha_state(),
        )

    async def async_added_to_hass(self) -> None:
        """Register for sunset event when added to Home Assistant."""
        # Trigger initial load
        self.async_schedule_update_ha_state()

        def _on_sunset(event):
            self._schedule_after_sunset()

        self._unsub_sunset = self.hass.bus.async_listen("sunset", _on_sunset)

    async def async_will_remove_from_hass(self) -> None:
        """Cleanup the listener when removed from Home Assistant."""
        if self._unsub_sunset:
            self._unsub_sunset()


class SefirahCounterYiddish(BaseSefirahSensor):
    """Sensor for the Sefirah count in Yiddish text."""

    def __init__(
        self,
        hass: HomeAssistant,
        helper: SfirahHelper,
        strip_nikud: bool,
        havdalah_offset: int,
    ) -> None:
        super().__init__(
            hass,
            helper,
            "Sefirah Counter Yiddish",
            "sefirah_counter_yiddish",
            strip_nikud,
            havdalah_offset,
        )

    def _get_text(self) -> str:
        return self._helper.get_sefirah_text()


class SefirahCounterMiddosYiddish(BaseSefirahSensor):
    """Sensor for the Sefirah middos count in Yiddish text."""

    def __init__(
        self,
        hass: HomeAssistant,
        helper: SfirahHelper,
        strip_nikud: bool,
        havdalah_offset: int,
    ) -> None:
        super().__init__(
            hass,
            helper,
            "Sefirah Counter Middos Yiddish",
            "sefirah_counter_middos_yiddish",
            strip_nikud,
            havdalah_offset,
        )

    def _get_text(self) -> str:
        return self._helper.get_middos_text()
