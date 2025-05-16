"""Sensor platform for Molad Yiddish integration."""
from __future__ import annotations
from datetime import datetime
import logging
from typing import Any
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
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
    async_add_entities([MoladYiddishSensor()])

class MoladYiddishSensor(SensorEntity):
    """Representation of a Molad Yiddish sensor."""
    
    _attr_name = "Molad (ייִדיש)"
    _attr_unique_id = "molad_yiddish_sensor"
    
    def __init__(self) -> None:
        """Initialize the sensor."""
        self._attr_state = None
        self._attr_extra_state_attributes = {}
        self._location = Location(latitude=31.7683, longitude=35.2137, timezone="Asia/Jerusalem")
    
    async def async_update(self) -> None:
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
            is_shabbos_mevorchim = hdate_now.gdate.weekday() == 5 and hdate_now.hebrew_day >= 23
            is_upcoming_shabbos_mevorchim = hdate_now.hebrew_day >= 16 and hdate_now.gdate.weekday() != 5
            
            # Update state and attributes
            self._attr_state = f"מולד {day_yd} {time_of_day}, {minutes} מינוט און {chalakim} חלקים"
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
