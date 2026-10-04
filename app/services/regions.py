"""Country → state/province catalog for the family profile cascade.

Region codes match the Jurisdiction rows the curriculum packs seed
("MD", "VA", "DC", "ON" …), so a family's chosen region filters directly
against Curriculum.region_code.
"""

from __future__ import annotations

US_REGIONS: dict[str, str] = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii",
    "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine",
    "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska",
    "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
    "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island",
    "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas",
    "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}

CA_REGIONS: dict[str, str] = {
    "AB": "Alberta", "BC": "British Columbia", "MB": "Manitoba",
    "NB": "New Brunswick", "NL": "Newfoundland and Labrador",
    "NT": "Northwest Territories", "NS": "Nova Scotia", "NU": "Nunavut",
    "ON": "Ontario", "PE": "Prince Edward Island", "QC": "Quebec",
    "SK": "Saskatchewan", "YT": "Yukon",
}

COUNTRIES: dict[str, dict] = {
    "US": {"name": "United States", "regions": US_REGIONS},
    "CA": {"name": "Canada", "regions": CA_REGIONS},
}


def valid_country(code: str) -> bool:
    return code in COUNTRIES


def valid_region(country_code: str, region_code: str) -> bool:
    country = COUNTRIES.get(country_code)
    return country is not None and region_code in country["regions"]


def region_name(country_code: str, region_code: str) -> str | None:
    return COUNTRIES.get(country_code, {}).get("regions", {}).get(region_code)


def country_name(country_code: str) -> str | None:
    return COUNTRIES.get(country_code, {}).get("name")


# Free-text jurisdiction → (country, region), for legacy curricula whose
# jurisdiction was only ever a display string ("Montgomery County, Maryland").
_TEXT_REGION_MAP = [
    ("ontario", ("CA", "ON")),
    ("maryland", ("US", "MD")),
    ("columbia", ("US", "DC")),
    ("virginia", ("US", "VA")),
]


def infer_region(jurisdiction_text: str | None) -> tuple[str | None, str | None]:
    if not jurisdiction_text:
        return None, None
    text = jurisdiction_text.lower()
    for needle, codes in _TEXT_REGION_MAP:
        if needle in text:
            return codes
    return None, None
