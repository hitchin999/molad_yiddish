import unicodedata
from datetime import timedelta
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    async_call_later,
    async_track_time_change,
)

from .molad_lib.sfirah_helper import SfirahHelper
from .const import DOMAIN


def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    opts = hass.data[DOMAIN].get(entry.entry_id, {}) or {}
    strip_nikud = opts.get("strip_nikud", False)
    havdalah_offset = opts.get("havdalah_offset", 72)

    helper = SfirahHelper(hass, havdalah_offset)

    async_add_entities(
        [
            SefirahCounterYiddish(hass, helper, strip_nikud, havdalah_offset),
            SefirahCounterMiddosYiddish(hass, helper, strip_nikud, havdalah_offset),
        ],
        update_before_add=True,
    )


class BaseSefirahSensor(SensorEntity):
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
        self._attr_icon = "mdi:counter"
        self._unsub_sunset = None

    @property
    def native_value(self):
        return self._state

    @property
    def icon(self) -> str:
        return self._attr_icon

    async def async_update(self) -> None:
        text = self._get_text()
        if self._strip:
            text = unicodedata.normalize('NFKC', text)
            text = ''.join(ch for ch in text if unicodedata.category(ch)[0] != 'M')
        self._state = text
        self.async_write_ha_state()

    @callback
    def _schedule_after_sunset(self) -> None:
        async_call_later(
            self.hass,
            self._havdalah_offset * 60,
            lambda _now: self.async_schedule_update_ha_state(),
        )

    async def async_added_to_hass(self) -> None:
        self.async_schedule_update_ha_state()

        def _on_sunset(event):
            self._schedule_after_sunset()

        self._unsub_sunset = self.hass.bus.async_listen("sunset", _on_sunset)

        async_track_time_change(
            self.hass,
            lambda now: self.hass.async_create_task(self.async_update()),
            hour=0,
            minute=5,
            second=0,
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub_sunset:
            self._unsub_sunset()


class SefirahCounterYiddish(BaseSefirahSensor):
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
