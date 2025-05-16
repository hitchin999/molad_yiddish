/README.md
# Molad Yiddish Integration for Home Assistant

A custom Home Assistant integration that provides Molad (new moon) and Rosh Chodesh details in Yiddish, including translated day names, month names, and time of day. It also indicates whether the current or upcoming Shabbos is Shabbos Mevorchim.

## Features

- **Sensor**: `sensor.molad_yiddish` with attributes:
  - **State**: e.g., `מולד זונטאג ביינאכט, 45 מינוט און 12 חלקים נאך 4` or `מולד זונטאג ביינאכט, 45 מינוט און 1 חלק נאך 4`
  - **month_name**: Yiddish month (e.g., `טבת`)
  - **rosh_chodesh_days**: List of Yiddish day names (e.g., `["מאנטאג", "דינסטאג"]`)
  - **rosh_chodesh_dates**: Gregorian dates (e.g., `["2025-01-01", "2025-01-02"]`)
  - **is_shabbos_mevorchim**: Boolean indicating if today is Shabbos Mevorchim
  - **is_upcoming_shabbos_mevorchim**: Boolean indicating if the next Shabbos is Mevorchim
- **Yiddish Translations**: Days, months, and time of day (e.g., `פארטאגס`, `ביינאכט`).
- **Dependency**: Uses `hdate[astral]==1.1.0`, compatible with the Jewish Calendar integration.

## Requirements

- Home Assistant 2023.7 or later
- Python 3.10 or later
- `hdate[astral]==1.1.0` (automatically installed)

## Installation

### Via HACS (Recommended)

1. Ensure [HACS](https://hacs.xyz/) is installed in Home Assistant.
2. Go to **HACS > Integrations > Three dots (top-right) > Custom repositories**.
3. Add the repository URL: `https://github.com/hitchin999/molad_yiddish` and set category to **Integration**.
4. Click **Add**, then find `Molad Yiddish` in HACS > Integrations.
5. Click **Download** and follow prompts to install.
6. Restart Home Assistant (Settings > System > Restart).
7. Add the integration via **Settings > Devices & Services > Add Integration > Molad (ייִדיש)**.

### Manual Installation

1. Copy the `custom_components/molad_yiddish/` folder to your Home Assistant configuration directory: `/config/custom_components/molad_yiddish/`.
2. Restart Home Assistant.
3. Add the integration via **Settings > Devices & Services > Add Integration > Molad (ייִדיש)**.

## Usage

- Check `sensor.molad_yiddish` in **Developer Tools > States** to view attributes.
- Example template for Shabbos announcements:
  ```yaml
  שבת מברכים חודש {{ state_attr('sensor.molad_yiddish', 'month_name') }} - ראש חודש, {{ state_attr('sensor.molad_yiddish', 'rosh_chodesh_days') | join(' און ') }}
  {{ state }}
  ```

## Notes

- Uses Jerusalem coordinates (31.7683, 35.2137) by default.
- Compatible with the Jewish Calendar integration.

## Contributing

Submit issues or pull requests at [https://github.com/hitchin999/molad_yiddish](https://github.com/hitchin999/molad_yiddish).

## License

MIT License (see [LICENSE](LICENSE) file).

/config/custom_components/molad_yiddish/sensor.py
"""Sensor platform for Molad Yiddish integration."""
from __future__ import annotations
from datetime import datetime, timedelta
import logging
from typing import Any
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from hdate import HDate, Location

_LOGGER = logging.getLogger(__name__)

# Yiddish translations
DAY_MAPPING = {
    "Sunday": "זונטאג",
    "Monday": "מאנטאג",
    "Tuesday": "דינסטאג",
    "Wednesday": "מיטוואך",
    "Thursday": "דאנערשטאג",
    "Friday": "פרייטאג",
    "Saturday": "שבת"
}

MONTH_MAPPING = {
    "Tishri": "תשרי",
    "Cheshvan": "חשוון",
    "Kislev": "כסלו",
    "Tevet": "טבת",
    "Shvat": "שבט",
    "Adar": "אדר",
    "Adar I": "אדר א",
    "Adar II": "אדר ב",
    "Nissan": "ניסן",
    "Iyar": "אייר",
    "Sivan": "סיון",
    "Tammuz": "תמוז",
    "Av": "אב",
    "Elul": "אלול"
}

TIME_OF_DAY = {
    "am": lambda h: "פארטאגס" if h < 6 else "צופרי",
    "pm": lambda h: "נאכמיטאג" if h < 18 else "ביינאכט"
}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Molad Yiddish sensor."""
    async_add_entities([MoladYiddishSensor(hass)])

class MoladYiddishSensor(SensorEntity):
    """Representation of a Molad Yiddish sensor."""
    
    _attr_name = "Molad (ייִדיש)"
    _attr_unique_id = "molad_yiddish_sensor"
    
    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._attr_state = None
        self._attr_extra_state_attributes = {}
        self._location = Location(latitude=31.7683, longitude=35.2137, timezone="Asia/Jerusalem")
        # Schedule daily updates at midnight
        async_track_time_interval(hass, self.async_update, timedelta(days=1))
    
    async def async_update(self, now=None) -> None:
        """Update the sensor data."""
        try:
            # Get current Hebrew date and Molad
            today = datetime.now()
            hdate_now = HDate(gdate=today, diaspora=False, location=self._location)
            molad = hdate_now.molad
            
            # Molad details
            molad_time = molad.molad_time
            hours = molad_time.hour
            am_or_pm = "am" if hours < 12 else "pm"
            time_of_day = TIME_OF_DAY[am_or_pm](hours)
            minutes = molad_time.minute
            chalakim = molad_time.chalakim
            day_yd = DAY_MAPPING.get(molad_time.gdate.strftime("%A"), molad_time.gdate.strftime("%A"))
            mon_yd = MONTH_MAPPING.get(molad.hebrew_month_name, molad.hebrew_month_name)
            
            # Rosh Chodesh days and dates
            rosh_chodesh = hdate_now.rosh_chodesh
            rosh_chodesh_days = []
            rosh_chodesh_dates = []
            for date in rosh_chodesh:
                rosh_hdate = HDate(gdate=date, diaspora=False)
                day_name = rosh_hdate.gdate.strftime("%A")
                rosh_chodesh_days.append(DAY_MAPPING.get(day_name, day_name))
                rosh_chodesh_dates.append(date.strftime("%Y-%m-%d"))
            
            # Shabbos Mevorchim logic
            next_shabbos = hdate_now.gdate + timedelta(days=(5 - hdate_now.gdate.weekday() + 7) % 7)
            is_shabbos_mevorchim = hdate_now.gdate.weekday() == 5 and any((next_shabbos + timedelta(days=1)) <= rc for rc in rosh_chodesh)
            is_upcoming_shabbos_mevorchim = hdate_now.gdate.weekday() != 5 and any(next_shabbos <= rc <= next_shabbos + timedelta(days=6) for rc in rosh_chodesh)
            
            # Update state and attributes
            chalakim_text = "חלק" if chalakim == 1 else "חלקים"
            self._attr_state = f"מולד {day_yd} {time_of_day}, {minutes} מינוט און {chalakim} {chalakim_text} נאך {hours % 12 or 12}"
            self._attr_extra_state_attributes = {
                "month_name": mon_yd,
                "rosh_chodesh_days": rosh_chodesh_days,
                "rosh_chodesh_dates": rosh_chodesh_dates,
                "is_shabbos_mevorchim": is_shabbos_mevorchim,
                "is_upcoming_shabbos_mevorchim": is_upcoming_shabbos_mevorchim
            }
            _LOGGER.debug("Molad Yiddish updated")
        except Exception as e:
            _LOGGER.error(f"Error updating Molad Yiddish sensor: {e}")
            self._attr_state = None
    
    @property
    def icon(self) -> str:
        """Return the icon for the sensor."""
        return "mdi:calendar-star"
