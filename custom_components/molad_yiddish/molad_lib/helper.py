"""
Vendored MoladHelper from molad==0.0.11, patched for hdate 1.1.0:
  - No Zmanim at all
  - Uses HebrewDate.from_jdn() / to_jdn()
  - Enforces month‐length guard so no phantom “Iyyar 30”
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

    def sumup(self, multipliers) -> Molad:
        shifts = [
            [2, 5,   204],
            [2, 16,  595],
            [4, 8,   876],
            [5, 21,  589],
            [1, 12,  793],
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
        # Parts → hours → days
        xx, out1 = out0[2], [0,0,0]
        out1[2] = yy = xx % 1080
        zz      = xx // 1080
        if yy < 0:
            yy, zz = yy + 1080, zz - 1

        xx = out0[1] + zz
        out1[1] = yy = xx % 24
        zz       = xx // 24
        if yy < 0:
            yy, zz = yy + 24, zz - 1

        xx = out0[0] + zz
        out1[0] = yy = (xx + 6) % 7 + 1
        if yy < 0:
            yy += 7

        return out1

    def convert_to_english(self, out1) -> Molad:
        days = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Shabbos"]
        d, h = out1[0], out1[1] - 6
        if h < 0:
            d, h = d - 1, h + 24
        chalakim = out1[2]
        daynm    = days[d-1]

        pm = "am"
        if h >= 12:
            pm, h = "pm", h - 12

        minutes = chalakim // 18
        chalakim %= 18
        h        = 12 if h == 0 else h
        filler   = "0" if minutes < 10 else ""
        friendly = f"{daynm}, {h}:{filler}{minutes} {pm} and {chalakim} chalakim"
        return Molad(daynm, h, minutes, pm, chalakim, friendly)

    def get_actual_molad(self, date):
        d       = self.get_next_numeric_month_year(date)
        year, month = d["year"], d["month"]
        guach   = {3,6,8,11,14,17,19}
        cycles  = year // 19
        yrs     = year % 19
        isleap  = yrs in guach

        if isleap:
            if   month == 13:      month = 6
            elif month == 14:      month = 7
            elif month > 6:        month += 1

        regular = sum(1 for i in range(yrs-1) if (i+1) not in guach)
        leap    = sum(1 for i in range(yrs-1) if (i+1) in guach)

        return self.sumup([1, cycles, regular, leap, month-1])

    def get_numeric_month_year(self, date):
        j = hdate.converters.gdate_to_jdn(date)
        h = HebrewDate.from_jdn(j)
        return {"year": h.year, "month": h.month}

    def get_next_numeric_month_year(self, date):
        d     = self.get_numeric_month_year(date)
        y, m  = d["year"], d["month"]
        if   m == 12:
            m, y = 1, y + 1
        elif m == 14:
            m = 7
        else:
            m += 1
        return {"year": y, "month": m}

    def get_gdate(self, numeric_date, day):
        hd  = hdate.HebrewDate(numeric_date["year"], numeric_date["month"], day)
        jdn = hd.to_jdn()
        return hdate.converters.jdn_to_gdate(jdn)

    def get_day_of_week(self, g):
        wd = g.strftime("%A")
        return "Shabbos" if wd == "Saturday" else wd

    def get_rosh_chodesh_days(self, date) -> RoshChodesh:
        this_m = self.get_numeric_month_year(date)
        next_m = self.get_next_numeric_month_year(date)
        mon    = Months(next_m["month"]).name.title()

        # ↳ guard against 29-day months
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
        rc       = gdays[0]
        days_back= (rc.weekday() - 5) % 7
        sat      = rc - datetime.timedelta(days=days_back)
        return HebrewDate.from_gdate(sat).day

    def is_shabbos_mevorchim(self, date) -> bool:
        if not is_shabbat(date):
            return False
        hd    = HebrewDate.from_gdate(date).day
        smd   = self.get_shabbos_mevorchim_hebrew_day_of_month(date)
        month = self.get_numeric_month_year(date)["month"]
        return (hd == smd) and (month != Months.ELUL.value)

    def is_upcoming_shabbos_mevorchim(self, date) -> bool:
        wd = (date.weekday() + 1) % 7 or 7
        sat = date + datetime.timedelta(days=(5 - date.weekday()) % 7 or 7)
        return self.is_shabbos_mevorchim(sat)

    def get_molad(self, date) -> MoladDetails:
        m    = self.get_actual_molad(date)
        ism  = self.is_shabbos_mevorchim(date)
        isup = self.is_upcoming_shabbos_mevorchim(date)
        rc   = self.get_rosh_chodesh_days(date)
        return MoladDetails(m, ism, isup, rc)
