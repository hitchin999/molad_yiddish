from datetime import date, timedelta
from pyluach import dates, parshios, hebrewcal

def get_special_shabbos_name(today: date = None) -> str:
    """
    Determine the upcoming Shabbat's special events (if any) in Hebrew (Yiddish style).
    Returns a combined string of events (e.g. "שבת פרה – מברכים חודש ניסן") or an empty string.
    """
    # Use today's date if none provided
    if today is None:
        today_date = date.today()
    elif isinstance(today, date):
        today_date = today
    else:
        # Support pyluach date types as input
        if isinstance(today, dates.GregorianDate):
            today_date = today.to_pydate()
        elif isinstance(today, dates.HebrewDate):
            today_date = today.to_greg().to_pydate()
        else:
            raise ValueError("Unsupported date type for 'today'")

    # Find the upcoming Shabbat (Saturday) on or after today
    greg_today = dates.GregorianDate.from_pydate(today_date)
    next_shabbat = greg_today.shabbos()  # GregorianDate of upcoming Shabbat
    shabbat_date = next_shabbat.to_pydate()  # Python date of that Shabbat
    shabbat_heb = next_shabbat.to_heb()      # HebrewDate of that Shabbat

    events = []  # list to collect special event labels

    Y = shabbat_heb.year  # Hebrew year of the Shabbat date

    # **Shabbat Shekalim** – Shabbat on or before Rosh Chodesh Adar (Adar II if leap year)
    adar_month = 13 if hebrewcal.Year(Y).leap else 12  # Adar II in leap years, otherwise Adar
    rc_adar = dates.HebrewDate(Y, adar_month, 1).to_pydate()  # Gregorian date of Rosh Chodesh Adar/Adar II
    delta_days = (rc_adar - shabbat_date).days
    if 0 <= delta_days <= 6:
        events.append("שבת שקלים")

    # **Shabbat Zachor** – Shabbat before Purim (14 Adar or 14 Adar II)
    purim = dates.HebrewDate(Y, adar_month, 14).to_pydate()  # Gregorian date of Purim
    delta_days = (purim - shabbat_date).days
    if 1 <= delta_days <= 6:
        events.append("שבת זכור")

    # **Shabbat HaChodesh** – Shabbat on or before Rosh Chodesh Nisan
    rc_nisan = dates.HebrewDate(Y, 1, 1).to_pydate()  # 1 Nisan in Gregorian date
    delta_days = (rc_nisan - shabbat_date).days
    if 0 <= delta_days <= 6:
        events.append("שבת החודש")

    # **Shabbat Parah** – Shabbat preceding Shabbat HaChodesh
    # Check if the following week’s Shabbat will be HaChodesh
    next_week_date = shabbat_date + timedelta(days=7)
    next_shabbat2 = dates.GregorianDate.from_pydate(next_week_date)
    next_shabbat2_heb = next_shabbat2.to_heb()
    # Calculate if 1 Nisan falls in the week after next_shabbat (i.e. on next Shabbat)
    rc_nisan2 = dates.HebrewDate(next_shabbat2_heb.year, 1, 1).to_pydate()
    delta_next = (rc_nisan2 - next_week_date).days
    if 0 <= delta_next <= 6 and "שבת החודש" not in events:
        events.append("שבת פרה")

    # **Shabbat HaGadol** – Shabbat before Pesach (15 Nisan)
    pesach = dates.HebrewDate(Y, 1, 15).to_pydate()  # Gregorian date of 15 Nisan (Pesach day 1)
    delta_days = (pesach - shabbat_date).days
    if 0 < delta_days <= 8:
        events.append("שבת הגדול")

    # **Shabbat Shuva** – Shabbat between Rosh Hashanah and Yom Kippur (Tishrei 3–9)
    if shabbat_heb.month == 7 and 3 <= shabbat_heb.day <= 9:
        events.append("שבת שובה")

    # **Shabbat Chazon** – Shabbat before Tisha B'Av (9 Av)
    tisha_bav = dates.HebrewDate(Y, 5, 9).to_pydate()  # 9 Av in Gregorian date
    delta_days = (tisha_bav - shabbat_date).days
    if 0 <= delta_days <= 6:
        events.append("שבת חזון")

    # **Shabbat Nachamu** – Shabbat after Tisha B'Av (comfort)
    if shabbat_heb.month == 5 and 10 <= shabbat_heb.day <= 16:
        events.append("שבת נחמו")

    # **Shabbat Chazak** – Shabbat where a Torah book is completed (Bereshit, Shemot, Vayikra, Bamidbar)
    parsha_indices = parshios.getparsha(next_shabbat)
    if parsha_indices:
        chazak_ports = {11, 22, 32, 42}  # indices of Vayechi, Pekudei, Bechukotai, Masei
        if any(idx in chazak_ports for idx in parsha_indices):
            events.append("שבת חזק")

    # **Purim Meshulash** – Occurs when 15 Adar (Shushan Purim) falls on Shabbat
    # (Purim observed over three days in Jerusalem)
    if ((not hebrewcal.Year(Y).leap and shabbat_heb.month == 12 and shabbat_heb.day == 15) or
        (hebrewcal.Year(Y).leap and shabbat_heb.month == 13 and shabbat_heb.day == 15)):
        events.append("פורים משולש")

    # **Shabbat Mevorchim** – Shabbat announcing the upcoming Rosh Chodesh
    if shabbat_heb.month != 6:  # Skip if upcoming month is Tishrei (no Birkat HaChodesh for Tishrei)
        # Determine next Hebrew month and year
        year_obj = hebrewcal.Year(shabbat_heb.year)
        last_month = year_obj.monthscount()  # 12 or 13
        if shabbat_heb.month == last_month:
            next_month_num = 1
            next_month_year = shabbat_heb.year
        else:
            next_month_num = shabbat_heb.month + 1
            next_month_year = shabbat_heb.year
        next_rc_date = dates.HebrewDate(next_month_year, next_month_num, 1).to_pydate()
        delta_days = (next_rc_date - shabbat_date).days
        if 1 <= delta_days <= 6 and next_month_num != 7:  # next_month_num != 7 ensures not Tishrei
            # Hebrew name of the upcoming month
            if next_month_num == 12:
                month_name = "אדר א׳" if hebrewcal.Year(next_month_year).leap else "אדר"
            elif next_month_num == 13:
                month_name = "אדר ב׳"
            else:
                month_names = {
                    1: "ניסן",  2: "אייר",   3: "סיון",
                    4: "תמוז",  5: "אב",    6: "אלול",
                    7: "תשרי",  8: "חשוון", 9: "כסלו",
                    10: "טבת", 11: "שבט"
                }
                month_name = month_names.get(next_month_num, "")
            if month_name:
                events.append(f"מברכים חודש {month_name}")

    # Combine events into one string separated by " – " or return empty string if none
    return " – ".join(events) if events else ""
  
