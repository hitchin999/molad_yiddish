# Molad Yiddish Integration for Home Assistant

A custom Home Assistant integration that provides Molad (new moon), Rosh Chodesh details, and special Shabbos announcements in Yiddish. It includes full Yiddish translations of day names, month names, and times of day.

## Features

- **Sensor**: `sensor.molad_yiddish`  
  - State: e.g., `מולד זונטאג פארטאגס, 49 מינוט און 15 חלקים נאך 4`
  - Attributes:
    - `month_name`: Yiddish month (e.g., `סיון`)
    - `rosh_chodesh`: Days of Rosh Chodesh (e.g., `מיטוואך`)
    - `rosh_chodesh_days`: List of days (e.g., `["דינסטאג", "מיטוואך"]`)
    - `rosh_chodesh_midnight`: Gregorian dates at midnight UTC
    - `rosh_chodesh_nightfall`: Nightfall times with 72-minute offset
    - `is_shabbos_mevorchim`: Boolean if *today* is Shabbos Mevorchim
    - `is_upcoming_shabbos_mevorchim`: Boolean if the *upcoming* Shabbos is Mevorchim

- **Binary Sensors**:
  - `binary_sensor.shabbos_mevorchim_yiddish`: `on` if today is Shabbos Mevorchim
  - `binary_sensor.upcoming_shabbos_mevorchim_yiddish`: `on` if upcoming Shabbos is Mevorchim

- **New Sensor**: `sensor.special_shabbos_yiddish`
  - State: Returns Yiddish string for upcoming Shabbos (from Sunday onward) if it's:
    - One of: שבת זכור, שבת שקלים, שבת פרה, שבת החודש, שבת הגדול
    - Or: שבת שובה, שבת נחמו, שבת חזון, שבת חזק
    - Also includes: מברכים חודש סיון, etc.
    - Multiple events are joined with `–`

- **Fully Offline**: No external API calls; uses `hdate` and `pyluach`.

- **Hebrew-to-Yiddish Conversion**: Days (`Sunday` → `זונטאג`), months, and time-of-day (e.g., `צופרי`, `ביינאכט`) are all localized.

## Dependencies

Automatically installed:
- `hdate[astral]==1.1.0`
- `pyluach==1.2.0`

## Requirements

- Home Assistant 2023.7+
- Python 3.10+

## Installation

### Via HACS (Recommended)
1. Make sure [HACS](https://hacs.xyz/) is installed.
2. Go to **HACS > Integrations > 3-dots menu > Custom repositories**
3. Add: `https://github.com/hitchin999/molad_yiddish`, set category to **Integration**
4. Download and restart Home Assistant.
5. Go to **Settings > Devices & Services > Add Integration > Molad Yiddish**

### Manual Installation
1. Copy the folder `custom_components/molad_yiddish/` to `/config/custom_components/`
2. Restart Home Assistant
3. Add integration via **Settings > Devices & Services > Add Integration > Molad Yiddish**

## Usage Example

```yaml
type: markdown
content: >
  {{ states('sensor.molad_yiddish') }}
  {{ states('sensor.special_shabbos_yiddish') }}
  {{ state_attr('sensor.molad_yiddish', 'month_name') }}
