# Molad Yiddish Integration for Home Assistant

A custom Home Assistant integration that provides:

* **Molad (new moon)** details in Yiddish
* **Rosh Chodesh** sensor with nightfall and midnight attributes
* **Special Shabbos** sensor for Shabbat specials (שבת זכור, שבת נחמו, etc.)
* **Sefiras HaOmer** counters in Yiddish (day‐count & middos)
* **Yiddish Day Label**: a daily label in Yiddish (weekday, Erev/Motzaei Shabbos, Yom Tov)

All date calculations are standalone (no external Jewish-calendar integration) and use your HA latitude, longitude & timezone.

---

## Features

### 🌙 Molad Sensor

* **Entity**: `sensor.molad_yiddish`
* **State Example**: `מולד זונטאג צופרי, 14 מינוט און 3 חלקים נאך 9`
* **Attributes**:

  * `day`: Yiddish weekday name (זונטאג, מאנטאג, …)
  * `hours`, `minutes`, `chalakim`: Molad time components
  * `am_or_pm`: `am` / `pm`
  * `time_of_day`: פרייטאגס, צופרי, נאכמיטאג, ביינאכט
  * `friendly`: full human-friendly Molad string
  * **Rosh Chodesh**:

    * `rosh_chodesh`: Yiddish day(s)
    * `rosh_chodesh_days`: list of day names
    * `rosh_chodesh_midnight`: ISO datetimes at midnight
    * `rosh_chodesh_nightfall`: ISO datetimes at nightfall
  * `month_name`: Hebrew month in Hebrew letters
  * `is_shabbos_mevorchim` / `is_upcoming_shabbos_mevorchim`

### 🌟 Special Shabbos Sensor

* **Entity**: `sensor.special_shabbos_yiddish`
* **State**: Yiddish name(s) of upcoming special Shabbos
* **Examples**: `שבת זכור`, `שבת נחמו`, `שבת הגדול – מברכים חודש ניסן`, `No Data`
* **Includes**: שבת שקלים, שבת זכור, שבת פרה, שבת החודש, שבת הגדול, שבת שובה, שבת חזון, שבת נחמו, שבת חזק, פורים משולש, מברכים חודש

### 🔢 Sefiras HaOmer Sensors

* **Counter** (day‐count)

  * **Entity**: `sensor.sefirah_counter_yiddish`
  * **Updates**: daily at Havdalah offset (default 72 min after sunset)
* **Middos** (qualities)

  * **Entity**: `sensor.sefirah_counter_middos_yiddish`
  * **Updates**: same schedule

Both counters optionally strip Nikud (Yom Tov accent marks) via the `strip_nikud` option.

### 🗓️ Yiddish Day Label Sensor (new)

* **Entity**: `sensor.yiddish_day_label`
* **Behavior**:

  * **Shabbos** (`שבת קודש`) during Friday < candlelighting (offset) → Saturday < havdalah (offset)
  * **Yom Tov** (`יום טוב`) on major holidays
  * **Erev Shabbos** (`ערש"ק`) Friday afternoon
  * **Motzaei Shabbos** (`מוצש"ק`) Saturday night
  * Otherwise weekday in Yiddish (זונטאג … פרייטאג)
* **Configuration**:

  * **candlelighting\_offset**: minutes before sunset (default: 15)
  * **havdalah\_offset**: minutes after sunset (default: 72)

---

## Configuration Options

After adding the integration via UI, go to **Settings → Devices & Services → Molad Yiddish → Options** to set:

| Option                     | Default | Description                                |
| -------------------------- | ------- | ------------------------------------------ |
| **candlelighting\_offset** | 15      | Minutes before sunset                      |
| **havdalah\_offset**       | 72      | Minutes after sunset (Yom Tov/Shabbos end) |
| **strip\_nikud**           | false   | Remove Hebrew vowel points from Omer text  |

---

## Requirements

* HA 2023.7+
* Python 3.10+
* **HACS** recommended
* Installed via manifest:

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

1. Copy `molad_yiddish/` to `config/custom_components/`
2. Restart Home Assistant
3. Add integration via UI as above

---

## Lovelace Examples

```yaml
# Molad + Rosh Chodesh
type: markdown
content: |
  🌙 {{ states('sensor.molad_yiddish') }}

  📆 ראש חודש: {{ state_attr('sensor.molad_yiddish','rosh_chodesh') }}
  🌓 חודש: {{ state_attr('sensor.molad_yiddish','month_name') }}

# Special Shabbos
- {{ states('sensor.special_shabbos_yiddish') }}

# Omer Counters
- ספירה: {{ states('sensor.sefirah_counter_yiddish') }}
- מידות: {{ states('sensor.sefirah_counter_middos_yiddish') }}

# Yiddish Day
- היום: {{ states('sensor.yiddish_day_label') }}
```
