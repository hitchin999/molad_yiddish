# /config/custom_components/molad_yiddish/binary_sensor.py

from __future__ import annotations
import logging
import datetime
from datetime import timedelta, date
from zoneinfo import ZoneInfo

from astral import LocationInfo
from astral.sun import sun
from hdate import HDateInfo
from pyluach.hebrewcal import HebrewDate as PHebrewDate

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.event import async_track_sunset
from homeassistant.core import callback


from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# ─── Your override map ────────────────────────────────────────────────────────
SLUG_OVERRIDES: dict[str, str] = {
    "א׳ סליחות":             "alef_selichot",
    "ערב ראש השנה":          "erev_rosh_hashana",
    "ראש השנה א׳":           "rosh_hashana_1",
    "ראש השנה ב׳":           "rosh_hashana_2",
    "ראש השנה א׳ וב׳":       "rosh_hashana_1_2",
    "צום גדליה":             "tzom_gedalia",
    "שלוש עשרה מדות":        "shlosha_asar_midot",
    "ערב יום כיפור":          "erev_yom_kippur",
    "יום הכיפורים":          "yom_kippur",
    "ערב סוכות":             "erev_sukkot",
    "סוכות א׳":              "sukkot_1",
    "סוכות ב׳":              "sukkot_2",
    "סוכות א׳ וב׳":           "sukkot_1_2",
    "חול המועד סוכות":       "chol_hamoed_sukkot",
    "הושענא רבה":            "hoshanah_rabbah",
    "שמיני עצרת":            "shemini_atzeret",
    "שמחת תורה":             "simchat_torah",
    "ערב חנוכה":             "erev_chanukah",
    "חנוכה":                 "chanukah",
    "שובבים":               "shovavim",
    "שובבים ת\"ת":          "shovavim_tet",
    "צום עשרה בטבת":         "tzom_asara_betevet",
    "ט\"ו בשבט":             "tu_bishvat",
    "תענית אסתר":            "taanit_esther",
    "פורים":                "purim",
    "שושן פורים":           "shushan_purim",
    "ליל בדיקת חמץ":        "leil_bedikat_chametz",
    "ערב פסח":              "erev_pesach",
    "פסח א׳":               "pesach_1",
    "פסח ב׳":               "pesach_2",
    "פסח א׳ וב׳":           "pesach_1_2",
    "חול המועד פסח":        "chol_hamoed_pesach",
    "שביעי של פסח":         "pesach_seventh",
    "אחרון של פסח":         "pesach_last",
    "ל\"ג בעומר":            "lag_baomer",
    "ערב שבועות":           "erev_shavuot",
    "שבועות א׳":            "shavuot_1",
    "שבועות ב׳":            "shavuot_2",
    "שבועות א׳ וב׳":        "shavuot_1_2",
    "צום שבעה עשר בתמוז":   "tzom_17_tammuz",
    "תשעה באב":             "tzom_9_av",
    "תשעה באב נדחה":        "tzom_9_av_deferred",
    "ראש חודש":             "rosh_chodesh",
}

# ─── The fixed dynamic‐attribute binary sensor ────────────────────────────────


class HolidayAttributeBinarySensor(BinarySensorEntity):
    """Mirrors one attribute from sensor.molad_yiddish_holiday."""
    def __init__(self, hass: HomeAssistant, attr_name: str) -> None:
        super().__init__()
        self.hass = hass
        self.attr_name = attr_name

        # Human-friendly display name
        self._attr_name = f"Yiddish Holiday {attr_name}"

        # Lookup your override map here
        slug = SLUG_OVERRIDES.get(attr_name)
        if not slug:
           # _LOGGER.debug("🔖 Using slug %r for attr %r", slug, attr_name)
       # else:
          #  _LOGGER.warning("❌ No SLUG_OVERRIDES entry for %r; falling back", attr_name)
            slug = (
                attr_name
                .lower()
                .replace(" ", "_")
                .replace("׳", "")
                .replace('"', "")
            )
          #  _LOGGER.debug("🔖 Fallback slug %r for attr %r", slug, attr_name)

        # Force the exact IDs you want
        self._attr_unique_id = f"yiddish_holiday_{slug}"
        # **This** forces the actual entity_id
        self.entity_id = f"binary_sensor.yiddish_holiday_{slug}"
       # _LOGGER.debug("➡️ unique_id=%r entity_id=%r", self._attr_unique_id, self.entity_id)

        self._attr_icon = "mdi:checkbox-marked-circle-outline"

        # Schedule periodic updates
        async_track_time_interval(hass, self.async_update, timedelta(minutes=1))

    async def async_update(self, now: datetime.datetime | None = None) -> None:
        state = self.hass.states.get("sensor.molad_yiddish_holiday")
        is_on = bool(state and state.attributes.get(self.attr_name, False))
       # _LOGGER.debug("🔄 Updating %r → %s", self.attr_name, is_on)
        self._attr_is_on = is_on
        



# ─── MeluchaProhibitionSensor (sunset-driven) ─────────────────────────────────

# adjust this list to exactly match your HDateInfo.holiday_name values:
FULL_YOM_TOV = {
    "Rosh Hashanah I", "Rosh Hashanah II",
    "Yom Kippur",
    "Sukkot I", "Sukkot II",
    "Shemini Atzeret", "Simchat Torah",
    "Pesach I", "Pesach II",
    "Shavuot I", "Shavuot II",
    "Pesach VII", "Pesach VIII",
}

class MeluchaProhibitionSensor(BinarySensorEntity):
    """True from candle-lighting until havdalah on Shabbos & full Yom Tov."""

    _attr_name = "Molad Yiddish Melucha Prohibition"
    _attr_unique_id = "molad_yiddish_melucha"
    _attr_icon = "mdi:briefcase-variant-off"

    def __init__(
        self,
        hass: HomeAssistant,
        candle_offset: int,
        havdalah_offset: int
    ) -> None:
        super().__init__()
        self.hass = hass
        self._candle = candle_offset
        self._havdalah = havdalah_offset
        self._attr_is_on = False

        # cache these (in case you use them elsewhere)
        self._loc = LocationInfo(
            latitude=hass.config.latitude,
            longitude=hass.config.longitude,
            timezone=hass.config.time_zone,
        )
        self._tz = ZoneInfo(hass.config.time_zone)

        # Candle-lighting on Fri & on Yom Tov eve → turn on
        async_track_sunset(
            self.hass,
            self._turn_on_if_needed,
            offset=-datetime.timedelta(minutes=self._candle),
        )

        # Havdalah on Sat & on Yom Tov end → turn off
        async_track_sunset(
            self.hass,
            self._turn_off_if_needed,
            offset=datetime.timedelta(minutes=self._havdalah),
        )




    @callback
    def _turn_on_if_needed(self, now: datetime.datetime) -> None:
        today = now.date()
        heb = HDateInfo(today, diaspora=False)

        # Friday (4) → Shabbos eve
        if today.weekday() == 4:
            self._attr_is_on = True
        # Or if it’s one of our FULL_YOM_TOV days
        elif heb.holiday_name in FULL_YOM_TOV:
            self._attr_is_on = True

        self.async_write_ha_state()

    @callback
    def _turn_off_if_needed(self, now: datetime.datetime) -> None:
        self._attr_is_on = False
        self.async_write_ha_state()


class ErevHolidaySensor(BinarySensorEntity):
    """True on specific Erev‐days from dawn until candle‐lighting."""

    _attr_name = "Molad Yiddish Erev"
    _attr_unique_id = "molad_yiddish_erev"
    _attr_icon = "mdi:weather-sunset-up"

    _EREV_DATES = {
        (6, 29),  # ערב ראש השנה
        (7, 9),   # ערב יום כיפור
        (7, 14),  # ערב סוכות
        (7, 21),  # הושענא רבה
        (9, 24),  # ערב חנוכה
        (1, 14),  # ערב פסח
        (3, 5),   # ערב שבועות
    }

    def __init__(self, hass: HomeAssistant, candle_offset: int) -> None:
        super().__init__()
        self.hass = hass
        self._candle = candle_offset
        self._attr_is_on = False
        async_track_time_interval(hass, self.async_update, timedelta(hours=1))

    async def async_update(self, now=None) -> None:
        tz = ZoneInfo(self.hass.config.time_zone)
        now = now or datetime.datetime.now(tz)
        today = now.date()
        hd = PHebrewDate.from_pydate(today)
        is_erev = (hd.month, hd.day) in self._EREV_DATES

        loc = LocationInfo(latitude=self.hass.config.latitude,
                           longitude=self.hass.config.longitude,
                           timezone=self.hass.config.time_zone)
        s = sun(loc.observer, date=today, tzinfo=tz)
        start = s["dawn"]
        end = s["sunset"] - timedelta(minutes=self._candle)
        self._attr_is_on = is_erev and (start <= now < end)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up all binary sensors for Molad Yiddish."""
    opts = hass.data[DOMAIN][entry.entry_id]
    candle = opts["candlelighting_offset"]
    havdalah = opts["havdalah_offset"]

    # Static ones first
    entities: list[BinarySensorEntity] = [
        MeluchaProhibitionSensor(hass, candle, havdalah),
        ErevHolidaySensor(hass, candle),
    ]

    # Then one per holiday attribute
    for name in SLUG_OVERRIDES:
        entities.append(HolidayAttributeBinarySensor(hass, name))

    async_add_entities(entities, update_before_add=True)
