# molad_lib/helper.py

"""
Vendored MoladHelper from molad==0.0.11.
Copy the contents of the original `molad/helper.py` here,
and remove its `requirements` declaration so Home Assistant
won't try to pip-install anything.
"""

# original imports (patch out any `import hdate.htables` if broken)
import datetime

class MoladHelper:
    def __init__(self, config):
        self.latitude = config.latitude
        self.longitude = config.longitude
        self.time_zone = config.time_zone
        # any other setup…

    def get_molad(self, date: datetime.date):
        # … original implementation …
        # returns an object with:
        #  .molad.{day, hours, minutes, am_or_pm, chalakim, friendly}
        #  .rosh_chodesh.{days, gdays, month}
        #  .is_shabbos_mevorchim
        #  .is_upcoming_shabbos_mevorchim
        pass

    def is_shabbos_mevorchim(self, date: datetime.date) -> bool:
        # … original implementation …
        pass

    def is_upcoming_shabbos_mevorchim(self, date: datetime.date) -> bool:
        # … original implementation …
        pass
