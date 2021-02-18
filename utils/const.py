from enum import Enum
from collections import namedtuple


Freqs = namedtuple("Freqs", ("label", "sql_fmt", "pd_fmt"))

class FREQ(Enum):
    DAY = Freqs("DAY", "%Y-%m-%d", "D")
    WEEK = Freqs("WEEK", "%x-%u", "W")
    MONTH = Freqs("MONTH", "%Y-%m", "M")
    QUARTER = Freqs("MONTH", None, "Q")
    YEAR = Freqs("YEAR", "%Y", "Y")

