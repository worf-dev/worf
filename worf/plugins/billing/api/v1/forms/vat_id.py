# update this if the EU gets new countries

import re

# to do: implement a specific regex for each country
# https://de.wikipedia.org/wiki/Umsatzsteuer-Identifikationsnummer

country_codes = {
    "AT",
    "BE",
    "BG",
    "CY",
    "CZ",
    "DE",
    "DK",
    "EE",
    "GR",
    "ES",
    "FI",
    "FR",
    "GB",
    "HR",
    "HU",
    "IE",
    "IT",
    "LT",
    "LU",
    "LV",
    "MT",
    "NL",
    "PL",
    "PT",
    "RO",
    "SE",
    "SI",
    "SK",
    "SM",
}


class VatId:
    def __call__(self, name, value, form):
        value = value.upper()
        if not value[:2] in country_codes:
            return ["not a valid country code"], None, True
        if not re.match("^[A-Z]{2}[A-Z]{0,3}[0-9]{6,12}[A-Z0-9]{0,3}$", value):
            return ["not a valid format"], None, True
        return [], value, False
