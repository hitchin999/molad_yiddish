# Molad Yiddish Integration for Home Assistant

A custom Home Assistant integration that provides Molad (new moon) and Rosh Chodesh details in Yiddish, including translated day names, month names, and time of day. It also indicates whether the current or upcoming Shabbos is Shabbos Mevorchim.

## Features

- **Sensor**: `sensor.molad_yiddish` with attributes:
  - **State**: e.g., `מולד זונטאג ביינאכט, 45 מינוט און 12 חלקים נאך 4`
  - **month_name**: Yiddish month (e.g., `טבת`)
  - **rosh_chodesh_days**: List of Yiddish day names (e.g., `["מאנטאג", "דינסטאג"]`)
  - **rosh_chodesh_dates**: Gregorian dates (e.g., `["2025-01-01", "2025-01-02"]`)
  - **is_shabbos_mevorchim**: Boolean indicating if today is Shabbos Mevorchim
  - **is_upcoming_shabbos_mevorchim**: Boolean indicating if the next Shabbos is Mevorchim
- **Yiddish Translations**: Days, months, and time of day (e.g., `פארטאגס`, `ביינאכט`).
- **Dependency**: Uses `hdate[astral]==1.1.0`, compatible with the Jewish Calendar integration.

## Installation

### Via HACS (Recommended)

1. Ensure [HACS](https://hacs.xyz/) is installed in Home Assistant.
2. Go to **HACS > Integrations > Explore & Download Repositories**.
3. Search for `Molad Yiddish` or add the repository URL: `https://github.com/hitchin999/molad_yiddish`.
4. Click **Download** and follow prompts to install.
5. Restart Home Assistant (Settings > System > Restart).
6. Add the integration via **Settings > Devices & Services > Add Integration > Molad (ייִדיש)**.

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
