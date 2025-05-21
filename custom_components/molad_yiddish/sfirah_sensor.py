# /config/custom_components/molad_yiddish/sfirah_sensor.py

import logging
import re
import unicodedata
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later

from .molad_lib.sfirah_helper import SfirahHelper

_LOGGER = logging.getLogger(__name__)


def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """
    Set up the Omer (Sefirah) sensors with optional nikud stripping.
    """
    helper = SfirahHelper(hass)
    strip_nikud = entry.options.get("strip_nikud", False)
    async_add_entities(
        [
            SefirahCounterYiddish(hass, helper, strip_nikud),
            SefirahCounterMiddosYiddish(hass, helper, strip_nikud),
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
    ) -> None:
        super().__init__()
        self.hass = hass
        self._helper = helper
        self._strip = strip_nikud
        self._state = None
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._unsub_sun = None

    @property
    def native_value(self):
        return self._state

    async def async_update(self) -> None:
        """Fetch new state from helper and apply nikud stripping."""
        text = self._get_text()
        if self._strip:
            # Normalize compatibility characters (presentation forms)
            text = unicodedata.normalize('NFKC', text)
            # Remove all combining marks (Nikud and other diacritics)
            text = ''.join(ch for ch in text if unicodedata.category(ch)[0] != 'M')
        self._state = text

    @callback
    def _schedule_after_sunset(self) -> None:
        """Schedule an update 72 minutes after sunset."""
        async_call_later(self.hass, 72 * 60, lambda _now: self.async_schedule_update_ha_state())

    async def async_added_to_hass(self) -> None:
        """Register for sunset event when added."""
        # Initial state update
        self.async_schedule_update_ha_state()

        def _on_sunset(event):
            self._schedule_after_sunset()

        # Listen for sunset event
        self._unsub_sun = self.hass.bus.async_listen("sunset", _on_sunset)

    async def async_will_remove_from_hass(self) -> None:
        """Cleanup listener when removed."""
        if self._unsub_sun:
            self._unsub_sun()


class SefirahCounterYiddish(BaseSefirahSensor):
    """Sensor for the Sefirah count in Yiddish text."""

    def __init__(self, hass: HomeAssistant, helper: SfirahHelper, strip_nikud: bool) -> None:
        super().__init__(hass, helper, "Sefirah Counter Yiddish", "sefirah_counter_yiddish", strip_nikud)

    def _get_text(self) -> str:
        return self._helper.get_sefirah_text()


class SefirahCounterMiddosYiddish(BaseSefirahSensor):
    """Sensor for the Sefirah middos count in Yiddish text."""

    def __init__(self, hass: HomeAssistant, helper: SfirahHelper, strip_nikud: bool) -> None:
        super().__init__(hass, helper, "Sefirah Counter Middos Yiddish", "sefirah_counter_middos_yiddish", strip_nikud)

    def _get_text(self) -> str:
        return self._helper.get_middos_text()
