"""
Vendored MoladHelper using pyluach for accurate molad calculations.

Requires:
    pip install pyluach
"""

import datetime
import logging

import hdate
import hdate.converters
from hdate.hebrew_date import Months, HebrewDate, is_shabbat
from pyluach.hebrewcal import Month as PMonth

_LOGGER = logging.getLogger(__name__)

# Mapping from hdate.Months.name to pyluach month number (1=Nissan … 13=Adar II)
_HD2PY = {
    "NISSAN":   1,
    "IYYAR":    2,
    "SIVAN":    3,
    "TAMMUZ":   4,
    "AV":       5,
    "ELUL":     6,
    "TISHREI":  7,
    "CHESHVAN": 8,
    "KISLEV":   9,
    "TEVET":   10,
    "SHEVAT":  11,
    "ADAR":    12,
    "ADAR_I":  12,
    "ADAR_II": 13,
}

class Molad:
    def __init__(self, day, hours, minutes, am_or_pm, chalakim, friendly):
        self.day      = day
        self.hours    = hours
        self.minutes  = minutes
        self.am_or_pm = am_or_pm
        self.chalakim = chalakim
        self.friendly = friendly

class RoshChodesh:
    def __init__(self, month, text, days, gdays=None):
        self.month = month
        self.text  = text
        self.days  = days
        self.gdays = gdays

class MoladDetails:
    def __init__(self, molad: Molad,
                 is_shabbos_mevorchim: bool,
                 is_upcoming_shabbos_mevorchim: bool,
                 rosh_chodesh: RoshChodesh):
        self.molad                        = molad
        self.is_shabbos_mevorchim         = is_shabbos_mevorchim
        self.is_upcoming_shabbos_mevorchim= is_upcoming_shabbos_mevorchim
        self.rosh_chodesh                 = rosh_chodesh

class MoladHelper:

    def __init__(self, config):
        self.config = config

    def get_actual_molad(self, date: datetime.date) -> Molad:
        """
        Compute the molad of the *next* Hebrew month using pyluach’s
        molad_announcement(), mapping hdate’s month enum to pyluach’s month numbers.
        """
        # get next Hebrew month/year
        nxt = self.get_next_numeric_month_year(date)
        year, cust_month = nxt["year"], nxt["month"]

        # map hdate’s month to pyluach’s month number
        hd_name = Months(cust_month).name.replace(" ", "_").upper()
        try:
            py_month = _HD2PY[hd_name]
        except KeyError:
            _LOGGER.error("Unknown month %s", hd_name)
            raise

        pm  = PMonth(year, py_month)
        ann = pm.molad_announcement()  # {"weekday":1–7,"hour":0–23,"minutes":0–59,"parts":0–1079}

        wd    = ann["weekday"]   # 1=Sunday … 7=Shabbos
        h24   = ann["hour"]
        mins  = ann["minutes"]
        parts = ann["parts"]

        ampm = "am" if h24 < 12 else "pm"
        h12  = h24 % 12 or 12

        day_name = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Shabbos"][wd-1]
        friendly = f"{day_name}, {h12}:{mins:02d} {ampm} and {parts} chalakim"

        return Molad(day_name, h12, mins, ampm, parts, friendly)

    def get_numeric_month_year(self, date):
        j = hdate.converters.gdate_to_jdn(date)
        h = HebrewDate.from_jdn(j)
        _LOGGER.debug(f"Current Hebrew date: {h.year}-{h.month.value} ({h.month.name})")
        return {"year": h.year, "month": h.month.value}

    def get_next_numeric_month_year(self, date):
        d = self.get_numeric_month_year(date)
        y, m = d["year"], d["month"]
        # wrap custom month after Adar II back to Nissan
        if m == 12 and not HebrewDate(y, m, 1).is_leap_year():
            m, y = 1, y + 1
        elif m == 13:
            m, y = 1, y + 1
        else:
            m += 1
        _LOGGER.debug(f"Next custom month: {m}, Year: {y}")
        return {"year": y, "month": m}

    def get_gdate(self, numeric_date, day):
        hd = hdate.HebrewDate(numeric_date["year"], numeric_date["month"], day)
        jdn = hd.to_jdn()
        return hdate.converters.jdn_to_gdate(jdn)

    def get_day_of_week(self, g):
        wd = g.strftime("%A")
        return "Shabbos" if wd == "Saturday" else wd

    def get_rosh_chodesh_days(self, date) -> RoshChodesh:
        this_m = self.get_numeric_month_year(date)
        next_m = self.get_next_numeric_month_year(date)
        mon    = Months(next_m["month"]).name.title()

        cm     = Months(this_m["month"])
        length = cm.days(this_m["year"]) if callable(cm.days) else cm.length

        days, gdays = [], []
        if length >= 30:
            g1 = self.get_gdate(this_m, 30)
            days.append(self.get_day_of_week(g1))
            gdays.append(g1)

        g2 = self.get_gdate(next_m, 1)
        days.append(self.get_day_of_week(g2))
        gdays.append(g2)

        text = " & ".join(days) if len(days) == 2 else days[0]
        return RoshChodesh(mon, text, days, gdays)

    def get_shabbos_mevorchim_hebrew_day_of_month(self, date):
        gdays = self.get_rosh_chodesh_days(date).gdays
        if not gdays:
            return None
        rc = gdays[0]
        days_back = (rc.weekday() - 5) % 7
        sat = rc - datetime.timedelta(days=days_back)
        return HebrewDate.from_gdate(sat).day

    def is_shabbos_mevorchim(self, date) -> bool:
        if not is_shabbat(date):
            return False
        hd   = HebrewDate.from_gdate(date).day
        smd  = self.get_shabbos_mevorchim_hebrew_day_of_month(date)
        month= self.get_numeric_month_year(date)["month"]
        return (hd == smd) and (month != Months.ELUL.value)

    def is_upcoming_shabbos_mevorchim(self, date) -> bool:
        sat = date + datetime.timedelta(days=(5 - date.weekday()) % 7 or 7)
        return self.is_shabbos_mevorchim(sat)

    def get_molad(self, date) -> MoladDetails:
        m   = self.get_actual_molad(date)
        ism = self.is_shabbos_mevorchim(date)
        isu = self.is_upcoming_shabbos_mevorchim(date)
        rc  = self.get_rosh_chodesh_days(date)
        return MoladDetails(m, ism, isu, rc)
        
