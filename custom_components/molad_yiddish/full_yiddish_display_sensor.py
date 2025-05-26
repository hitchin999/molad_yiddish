from __future__ import annotations
import datetime
from datetime import timedelta
from zoneinfo import ZoneInfo

from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.event import async_track_time_interval


class FullYiddishDisplaySensor(SensorEntity):
    """
    Combines Yiddish day label, parsha, holiday, R"Chodesh, and special Shabbos into one filtered string.
    """
    _attr_name = "Molad Yiddish Full Display"
    _attr_unique_id = "molad_yiddish_full_display"

    # Values to hide from holiday sensor
    HIDE: set[str] = {
        "ראש השנה א׳ וב׳",
        "סוכות א׳ וב׳",
        "פסח א׳ וב׳",
        "שבועות א׳ וב׳",
        "ראש חודש",
        "תענית מתחילה עכשיו",
    }

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__()
        self.hass = hass
        self._state = ""
        # Update every minute to catch changes
        async_track_time_interval(hass, self.async_update, timedelta(minutes=1))

    @property
    def native_value(self) -> str:
        return self._state

    async def async_update(self, now: datetime.datetime | None = None) -> None:
        tz = ZoneInfo(self.hass.config.time_zone)
        now = now or datetime.datetime.now(tz)

        # Fetch entity states
        day_label = self.hass.states.get("sensor.yiddish_day_label")
        parsha = self.hass.states.get("sensor.molad_yiddish_parsha")
        holiday = self.hass.states.get("sensor.molad_yiddish_holiday")
        rosh_chodesh = self.hass.states.get("sensor.rosh_chodesh_today_yiddish")
        special_shabbos = self.hass.states.get("sensor.special_shabbos_yiddish")

        parts: list[str] = []
        # Add Yiddish Day Label
        if day_label and day_label.state:
            parts.append(day_label.state)
        # Add Parsha
        if parsha and parsha.state:
            parts.append(parsha.state)
        # Add holiday if not hidden
        if holiday and (h := holiday.state) and h not in self.HIDE:
            parts.append(h)
        # Add Rosh Chodesh
        if rosh_chodesh and rosh_chodesh.state != "Not Rosh Chodesh Today":
            parts.append(rosh_chodesh.state)
        # Add Special Shabbos if applicable
        if special_shabbos and special_shabbos.state not in ("No data", ""):
            wd = now.weekday()  # Mon=0 ... Sun=6
            hr = now.hour
            # After midday Fri or any time Sat
            if (wd == 4 and hr >= 13) or wd == 5:
                parts.append(special_shabbos.state)

        # Build state so there's *no* separator between day_label & parsha,
        # but *yes* between parsha and anything that follows.
        if len(parts) >= 2:
            # Join everything after the second element with separators...
            suffix = parts[2:]
            if suffix:
                self._state = f"{parts[0]}{parts[1]} · " + " · ".join(suffix)
            else:
                # Only day_label and parsha present
                self._state = f"{parts[0]}{parts[1]}"
        else:
            # Fallback for cases where there's only one or zero parts
            self._state = " · ".join(parts)
