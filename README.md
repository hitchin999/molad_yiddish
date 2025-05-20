# Molad Yiddish Integration for Home Assistant

A custom Home Assistant integration that provides Molad (new moon) and Rosh Chodesh details in Yiddish, including translated day names, month names, and time of day. It also includes logic for identifying special Shabbatot (like שבת זכור, שבת נחמו) and a sensor for ספירת העומר in Yiddish.

---

## Features

### 🌙 Molad Sensor

- **Entity**: `sensor.molad_yiddish`
- **Example State**:  
  `מולד זונטאג צופרי, 14 מינוט און 3 חלקים נאך 9`
- **Attributes**:
  - `day`: e.g. `זונטאג`
  - `hours`, `minutes`, `chalakim`: Molad time parts
  - `am_or_pm`: `am` / `pm`
  - `time_of_day`: e.g. `פארטאגס`, `ביינאכט`
  - `friendly`: Full friendly Molad string
  - `rosh_chodesh`: e.g. `"מיטוואך"`
  - `rosh_chodesh_days`: List of Yiddish day names
  - `rosh_chodesh_midnight`: Midnight datetimes for Rosh Chodesh
  - `rosh_chodesh_nightfall`: Nightfall datetimes for Rosh Chodesh
  - `month_name`: e.g. `טבת`
  - `is_shabbos_mevorchim`: `true/false`
  - `is_upcoming_shabbos_mevorchim`: `true/false`

---

### 🌟 Special Shabbos Sensor

- **Entity**: `sensor.special_shabbos_yiddish`
- **State**: Name(s) of upcoming Shabbos specials in Yiddish.
- **Examples**:
  - `שבת חזק`
  - `שבת הגדול – מברכים חודש ניסן`
  - `שבת חזון – מברכים חודש אב`
  - `No Data` if no special Shabbos this week
- **Logic includes**:
  - שבת שקלים
  - שבת זכור
  - שבת פרה
  - שבת החודש
  - שבת הגדול
  - שבת שובה
  - שבת חזון
  - שבת נחמו
  - שבת חזק
  - פורים משולש
  - מברכים חודש (not on תשרי)

---

### 🔢 Sefiras HaOmer Yiddish Sensor (new)

- **Entity**: `sensor.sefirah_counter_yiddish`
- **State**: Current Sefira count in Yiddish (e.g., `"הַיּוֹם שִׁבְעָה וּשְׁלֹשִׁים יוֹם שֶׁהֵם חֲמִשָּׁה שָׁבוּעוֹת וּשְׁנֵי יָמִים לָעֹֽמֶר"`)
- Updates daily at 72 Minutes after Sunset based on current Hebrew date

---

### 🧠 Sefiras HaOmer Middos Yiddish Sensor (new)

- **Entity**: `sensor.sefirah_counter_middos_yiddish`
- **State**: Current Sefira count in Yiddish (e.g., `"גְבוּרָה שֶׁבְּיְסוֹד"`)
- Updates daily at 72 Minutes after Sunset based on current Hebrew date

---

## Requirements

- Home Assistant 2023.7+
- Python 3.10+
- [HACS](https://hacs.xyz/) for easiest install
- Python packages (auto-installed):
  - `hdate[astral]==1.1.0`
  - `pyluach==1.2.0`

---

## Installation

### HACS (Recommended)
1. Go to **HACS > Integrations > ⋮ > Custom repositories**
2. Add: `https://github.com/hitchin999/molad_yiddish` (type: *Integration*)
3. Install `Molad Yiddish` from HACS
4. Restart Home Assistant
5. Add via **Settings > Devices & Services > Add Integration > Molad Yiddish**

### Manual
1. Copy folder to: `config/custom_components/molad_yiddish/`
2. Restart Home Assistant
3. Add integration as above

---

## Usage & Templates

Example card template:

```yaml
type: markdown
content: >
  🌙 {{ states('sensor.molad_yiddish') }}

  📆 ראש חודש: {{ state_attr('sensor.molad_yiddish', 'rosh_chodesh') }}

  🔯 {{ states('sensor.special_shabbos_yiddish') }}

  🕯️ ספירה: {{ states('sensor.sfira_yiddish') }}
