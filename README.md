# Molad Yiddish Integration for Home Assistant

A custom Home Assistant integration that provides:

* **Molad (new moon)** details in Yiddish
* **Parsha** weekly Torah portion
* **Rosh Chodesh Today** indicator (boolean)
* **Shabbos Mevorchim** and **Upcoming Shabbos Mevorchim** indicators (booleans)
* **Rosh Chodesh** sensor with nightfall and midnight attributes
* **Special Shabbos** sensor for Shabbat specials (שבת זכור, שבת נחמו, etc.)
* **Sefiras HaOmer** counters in Yiddish with the option to Remove Nekides (הַיּוֹם אַרְבָּעִים יוֹם שֶׁהֵם חֲמִשָּׁה שָׁבוּעוֹת וַחֲמִשָּׁה יָמִים לָעֹֽמֶר and הוֹד שֶׁבְּיְסוֹד)
* **Yiddish Day Label**: a daily label in Yiddish (זונטאג, מאנטאג)
* **Yiddish Date**: current Hebrew date rendered in כ״ה חשוון תשפ״ה

All date calculations are standalone (no external Jewish-calendar integration) and use your Home Assistant latitude, longitude & timezone.

---

## Features

### 🌙 Molad Sensor

* **Entity**: `sensor.molad_yiddish`
* **State Example**: `מולד זונטאג צופרי, 14 מינוט און 3 חלקים נאך 9`
* **Attributes**:

  * `day`: Yiddish weekday name (`זונטאג`, `מאנטאג`, …)
  * `hours`, `minutes`, `chalakim`: Molad time components
  * `am_or_pm`: `am` / `pm`
  * `time_of_day`: (e.g., `צופרי`, `נעכט`)
  * `friendly`: full human-friendly Molad string
  * **Rosh Chodesh**:

    * `rosh_chodesh`: Yiddish day(s) of R"Ch
    * `rosh_chodesh_days`: list of Yiddish day names
    * `rosh_chodesh_midnight`: ISO datetimes at midnight
    * `rosh_chodesh_nightfall`: ISO datetimes at nightfall
  * `month_name`: Hebrew month in Hebrew letters

### 📖 Parsha Sensor

* **Entity**: `sensor.molad_yiddish_parsha`
* **State Example**: `שמות` or corresponding Yiddish reading
* **Behavior**: Updates weekly just after midnight to reflect the current Torah portion in Yiddish

### 🗓️ Rosh Chodesh Today

* **Entity**: `binary_sensor.rosh_chodesh_today`
* **State**: `on` if today (after nightfall) is Rosh Chodesh, otherwise `off`

### 🌟 Shabbos Mevorchim Indicators

* **Entity**: `binary_sensor.shabbos_mevorchim`

  * `on` if today is Shabbos Mevorchim, otherwise `off`
* **Entity**: `binary_sensor.upcoming_shabbos_mevorchim`

  * `on` if the upcoming Shabbos is Mevorchim, otherwise `off`

### 🌟 Special Shabbos Sensor

* **Entity**: `sensor.special_shabbos_yiddish`
* **State Example**: `שבת זכור`, `שבת נחמו`, `No Data`
* **Includes**: שבת שקלים, שבת זכור, שבת פרה, שבת החודש, שבת הגדול, שבת שובה, שבת חזון, שבת נחמו, שבת חזק, פורים משולש, מברכים חודש

### 🔢 Sefiras HaOmer Sensors

* **Counter** (day‐count):

  * **Entity**: `sensor.sefirah_counter_yiddish`
  * **Updates**: daily at Havdalah offset (default 72 min after sunset)
* **Middos** (qualities):

  * **Entity**: `sensor.sefirah_counter_middos_yiddish`
  * **Updates**: same schedule

Both counters optionally strip Nikud via `strip_nikud` option.

### 🗓️ Yiddish Day Label

* **Entity**: `sensor.yiddish_day_label`
* **Behavior**:

  * `שבת קודש` during Shabbos (from candlelighting to Havdalah)
  * `ארש"ק` (Erev Shabbos) on Friday afternoon
  * `מוצש"ק` (Motzaei Shabbos) Saturday night
  * `יום טוב` on major Yom Tov
  * Otherwise weekday in Yiddish (`זונטאג` … `פרייטאג`)

### 📆 Yiddish Date

* **Entity**: `sensor.yiddish_date`
* **State Example**: `ט"ו באייר תשפ"ה`
* **Attributes**:

  * `hebrew_day`: numeric day
  * `hebrew_month`: Hebrew month name in Yiddish

---

## Configuration Options

After adding the integration via UI, go to **Settings → Devices & Services → Molad Yiddish → Options** to set:

| Option                   | Default | Description                               |
| ------------------------ | ------- | ----------------------------------------- |
| `וויפיל מינוט פארן שקיעה איז הדלקת הנרות`                     | 15      | Minutes before sunset for Erev Shabbos    |
| `וויפיל מינוט נאכן שקיעה איז מוצאי`        | 72      | Minutes after sunset for Motzaei Shabbos  |
| `נעם אראפ די נְקֻודּוֹת` | false   | Remove Hebrew vowel points from Omer text |

---

## Requirements

* HA 2023.7+
* Python 3.10+
* **HACS** recommended
* Dependencies installed via manifest:

  * `hdate[astral]==1.1.0`
  * `pyluach==2.2.0`

---

## Installation

### HACS (Recommended)

1. Go to **HACS → Integrations → ⋮ → Custom repositories**
2. Add: `https://github.com/hitchin999/molad_yiddish` (type: Integration)
3. Install **Molad Yiddish**
4. Restart Home Assistant
5. **Settings → Devices & Services → Add Integration → Molad Yiddish**

### Manual

1. Copy `custom_components/molad_yiddish/` to `config/custom_components/`
2. Restart Home Assistant
3. Add integration via UI as above

---

## Lovelace Examples

```yaml
# Molad + Rosh Chodesh + Parsha
type: markdown
content: |
  🌙 {{ states('sensor.molad_yiddish') }}
  📖 {{ states('sensor.molad_yiddish_parsha') }}
  📆 ראש חודש: {{ state_attr('sensor.molad_yiddish','rosh_chodesh') }}

# Rosh Chodesh Today Indicator
- R"Ch Today: {{ states('binary_sensor.rosh_chodesh_today') }}

# Shabbos Mevorchim
- ש״מ: {{ states('binary_sensor.shabbos_mevorchim') }}
- Upcoming ש״מ: {{ states('binary_sensor.upcoming_shabbos_mevorchim') }}

# Special Shabbos
- {{ states('sensor.special_shabbos_yiddish') }}

# Omer Counters
- ספירה: {{ states('sensor.sefirah_counter_yiddish') }}
- מידות: {{ states('sensor.sefirah_counter_middos_yiddish') }}

# Yiddish Day & Date
- היום: {{ states('sensor.yiddish_day_label') }}
- תאריך: {{ states('sensor.yiddish_date') }}
```
