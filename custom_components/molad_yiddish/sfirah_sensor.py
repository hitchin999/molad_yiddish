# /config/custom_components/molad_yiddish/sfirah_sensor.py

import logging
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later

# Pull the sun event constant from homeassistant.const
from homeassistant.const import SUN_EVENT_SUNSET

from .molad_lib.sfirah_helper import SfirahHelper

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    helper = SfirahHelper(hass)
    async_add_entities(
        [
            SefirahCounterYiddish(helper),
            SefirahCounterMiddosYiddish(helper),
        ],
        update_before_add=True,
    )


class BaseSefirahSensor(SensorEntity):
    """Base class for Sefirah (Omer) sensors."""

    def __init__(self, helper: SfirahHelper, name: str, unique_id: str) -> None:
        super().__init__()
        self._helper = helper
        self._state = None
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._unsub_sun = None

    @property
    def native_value(self):
        return self._state

    async def async_update(self) -> None:
        """Fetch new state from helper."""
        self._state = self._get_text()

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

        # Listen for the sun.set event
        self._unsub_sun = self.hass.bus.async_listen(SUN_EVENT_SUNSET, _on_sunset)

    async def async_will_remove_from_hass(self) -> None:
        """Cleanup listener when removed."""
        if self._unsub_sun:
            self._unsub_sun()


class SefirahCounterYiddish(BaseSefirahSensor):
    """Sensor for the sefira counter in Yiddish text."""

    def __init__(self, helper: SfirahHelper) -> None:
        super().__init__(helper, name="Sefirah Counter Yiddish", unique_id="sefirah_counter_yiddish")

    def _get_text(self) -> str:
        return self._helper.get_sefirah_text()


class SefirahCounterMiddosYiddish(BaseSefirahSensor):
    """Sensor for the sefira middos counter in Yiddish text."""

    def __init__(self, helper: SfirahHelper) -> None:
        super().__init__(helper, name="Sefirah Counter Middos Yiddish", unique_id="sefirah_counter_middos_yiddish")

    def _get_text(self) -> str:
        return self._helper.get_middos_text()
        
