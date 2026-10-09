"""Canonical dimensions for the HackIAthon World Bank comparison grid."""

from itertools import product

SNAPSHOT_COUNTRIES = ("PAN", "CRI", "COL", "DOM", "MEX", "GTM")
SNAPSHOT_INDICATORS = (
    "NY.GDP.MKTP.KD.ZG",
    "FP.CPI.TOTL.ZG",
    "SL.UEM.TOTL.ZS",
    "SP.POP.TOTL",
    "IT.NET.USER.ZS",
    "NE.EXP.GNFS.ZS",
)
SNAPSHOT_INDICATOR_YEARS = tuple(range(2010, 2025))
EXPECTED_INDICATOR_KEYS = set(product(SNAPSHOT_COUNTRIES, SNAPSHOT_INDICATORS, SNAPSHOT_INDICATOR_YEARS))
INDICATOR_UNITS = {
    "NY.GDP.MKTP.KD.ZG": "% anual",
    "FP.CPI.TOTL.ZG": "% anual",
    "SL.UEM.TOTL.ZS": "% de fuerza laboral",
    "SP.POP.TOTL": "personas",
    "IT.NET.USER.ZS": "% de población",
    "NE.EXP.GNFS.ZS": "% del PIB",
}
