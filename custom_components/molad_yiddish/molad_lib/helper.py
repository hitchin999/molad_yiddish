# custom_components/molad_yiddish/molad_lib/helper.py

"""
Vendored MoladHelper from molad==0.0.11, patched for hdate 1.1.0:
  - Removed all Zmanim usage (no .time / .havdalah / .candle_lighting)
  - Use is_shabbat() helper for Shabbos checks
  - Use HebrewDate.from_jdn() / to_jdn() instead of missing converter functions
  - Add month‐length guard so we never try day 30 on a 29-day month
"""

import datetime
import math

import hdate
import hdate.converters
from hdate.hebrew_date import Months, HebrewDate, is_shabbat


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
    def __init__(
        self,
        molad: Molad,
        is_shabbos_mevorchim: bool,
        is_upcoming_shabbos_mevorchim: bool,
        rosh_chodesh: RoshChodesh
    ):
        self.molad                        = molad
        self.is_shabbos_mevorchim         = is_shabbos_mevorchim
        self.is_upcoming_shabbos_mevorchim= is_upcoming_shabbos_mevorchim
        self.rosh_chodesh                 = rosh_chodesh

class MoladHelper:

    def __init__(self, config):
        self.config = config

    def sumup(self, multipliers) -> Molad:
        shifts = [
            [2, 5,   204],  # starting point
            [2, 16,  595],  # 19-year cycle
            [4, 8,   876],  # regular year
            [5, 21,  589],  # leap year
            [1, 12,  793],  # month
        ]
        out00 = self.multiply_matrix([multipliers], shifts)[0]
        out1  = self.carry_and_reduce(out00)
        return self.convert_to_english(out1)

    def multiply_matrix(self, m1, m2):
        res = [[0]*len(m2[0]) for _ in m1]
        for i in range(len(m1)):
            for j in range(len(m2[0])):
                for k in range(len(m2)):
                    res[i][j] += m1[i][k] * m2[k][j]
        return res

    def carry_and_reduce(self, out0):
        # 1080 chalakim per hour
        xx = out0[2]
        yy = xx % 1080
        zz = xx // 1080
        if yy < 0:
            yy += 1080; zz -= 1
        out1 = [0,0,0]; out1[2] = yy

        # 24 hours per day
        xx = out0[1] + zz
        yy = xx % 24
        zz = xx // 24
        if yy < 0:
            yy += 24; zz -= 1
        out1[1] = yy

        # 7 days per week (1=Sunday…7=Shabbos)
        xx = out0[0] + zz
        yy = (xx + 6) % 7 + 1
        if yy < 0:
            yy += 7
        out1[0] = yy
        return out1

    def convert_to_english(self, out1) -> Molad:
        days = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Shabbos"]
        daynm = days[out1[0]-1]
        hours = out1[1] - 6
        if hours < 0:
            daynm = days[out1[0]-2]  # go back one day if before 6 PM
            hours += 24
        chalakim = out1[2]

        pm = "am"
        if hours >= 12:
            pm = "pm"; hours -= 12

        minutes = chalakim // 18
        chalakim = chalakim % 18
        hours = 12 if hours == 0 else hours
        filler = "0" if minutes < 10 else ""
        friendly = f"{daynm}, {hours}:{filler}{minutes} {pm} and {chalakim} chalakim"
        return Molad(daynm, hours, minutes, pm, chalakim, friendly)

    def get_actual_molad(self, date):
        d      = self.get_next_numeric_month_year(date)
        year   = d["year"]
        month  = d["month"]
        guach  = [3,6,8,11,14,17,19]

        cycles = year // 19
        yrs    = year % 19
        isleap = yrs in guach

        if isleap:
            if month == 13:
                month = 6
            elif month == 14:
                month = 7
            elif month > 6:
                month += 1

        regular = sum(1 for i in range(yrs-1) if (i+1) not in guach)
        leap    = sum(1 for i in range(yrs-1) if (i+1) in guach)

        return self.sumup([1, cycles, regular, leap, month-1])

    def get_numeric_month_year(self, date):
        j = hdate.converters.gdate_to_jdn(date)
        h = HebrewDate.from_jdn(j)
        return {"year": h.year, "month": h.month}

    def get_next_numeric_month_year(self, date):
        d      = self.get_numeric_month_year(date)
        year   = d["year"]
        month  = d["month"]
        if month == 12:
            month, year = 1, year + 1
        elif month == 14:
            month = 7
        else:
            month += 1
        return {"year": year, "month": month}

    def get_gdate(self, numeric_date, day):
        hd  = hdate.HebrewDate(numeric_date["year"], numeric_date["month"], day)
        jdn = hd.to_jdn()
        return hdate.converters.jdn_to_gdate(jdn)

    def get_day_of_week(self, gdate):
        wd = gdate.strftime("%A")
        return "Shabbos" if wd == "Saturday" else wd

    def get_rosh_chodesh_days(self, date) -> RoshChodesh:
        this_m = self.get_numeric_month_year(date)
        next_m = self.get_next_numeric_month_year(date)
        next_name = Months(next_m["month"]).name.title()

        if next_m["month"] == 1:
            return RoshChodesh(next_name, "", [], [])

        # **month‐length guard** so we skip day 30 if this month has only 29 days:
        me     = Months(this_m["month"])
        length = me.days(this_m["year"]) if callable(me.days) else me.length

        days_list = []
        gdays     = []

        # only include the 30th if the month really has 30 days:
        if length >= 30:
            g1 = self.get_gdate(this_m, 30)
            days_list.append(self.get_day_of_week(g1))
            gdays.append(g1)

        # always include the 1st of next month:
        g2 = self.get_gdate(next_m, 1)
        days_list.append(self.get_day_of_week(g2))
        gdays.append(g2)

        text = " & ".join(days_list) if len(days_list) == 2 else days_list[0]
        return RoshChodesh(next_name, text, days_list, gdays)

    def get_shabbos_mevorchim_hebrew_day_of_month(self, date):
        # walk back from the first R”Ch date to the previous Saturday:
        rc_gdays = self.get_rosh_chodesh_days(date).gdays
        if not rc_gdays:
            return None
        first_rc = rc_gdays[0]
        # compute days back to Saturday (weekday=5)
        days_back = (first_rc.weekday() - 5) % 7
        sat_date  = first_rc - datetime.timedelta(days=days_back)
        return HebrewDate.from_gdate(sat_date).day

    def is_shabbos_mevorchim(self, date) -> bool:
        # true when today is Saturday *and* matches the Mevorchim day:
        if not is_shabbat(date):
            return False
        hd  = HebrewDate.from_gdate(date).day
        smd = self.get_shabbos_mevorchim_hebrew_day_of_month(date)
        # exclude Elul per custom logic
        month = self.get_numeric_month_year(date)["month"]
        return hd == smd and month != Months.ELUL.value

    def is_upcoming_shabbos_mevorchim(self, date) -> bool:
        # look ahead to the next Saturday:
        days_ahead = (5 - date.weekday()) % 7
        days_ahead = days_ahead or 7
        next_sat   = date + datetime.timedelta(days=days_ahead)
        return self.is_shabbos_mevorchim(next_sat)

    def get_molad(self, date) -> MoladDetails:
        molad = self.get_actual_molad(date)
        ism   = self.is_shabbos_mevorchim(date)
        isum  = self.is_upcoming_shabbos_mevorchim(date)
        rc    = self.get_rosh_chodesh_days(date)
        return MoladDetails(molad, ism, isum, rc)
      
