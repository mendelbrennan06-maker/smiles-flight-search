from datetime import datetime, timezone
from dateutil import parser
import re

POINT_VALUE_TIERS = [
    (0, 20_000, 0.005),
    (20_000, 40_000, 0.0045),
    (40_000, 60_000, 0.0043),
    (60_000, 999_999_999, 0.004),
]

AIRPORTS_BY_CITY = {
    "NYC": ["LGA", "JFK", "EWR"],
}

CABIN_TRANSLATIONS = {
    "econômica": "Economy",
    "economica": "Economy",
    "economy": "Economy",
    "executiva": "Business",
    "business": "Business",
    "classe executiva": "Business",
}


def airport_list(origin: str) -> list[str]:
    origin = origin.strip().upper()
    return AIRPORTS_BY_CITY.get(origin, [origin])


def points_cash_value(points: int) -> float:
    for low, high, value in POINT_VALUE_TIERS:
        if low <= points < high:
            return points * value
    return points * 0.004


def brl_to_usd(brl_amount: float, brl_per_usd_rate: float) -> float:
    adjusted_rate = brl_per_usd_rate - 0.10
    if adjusted_rate <= 0:
        raise ValueError("BRL/USD rate must be greater than 0.10")
    return brl_amount / adjusted_rate


def parse_points(text: str) -> int | None:
    if not text:
        return None

    clean = text.lower().replace(".", "").replace(",", "")
    match = re.search(r"(\d+)\s*(milhas|milha|miles|pontos|pts)?", clean)

    if not match:
        return None

    return int(match.group(1))


def parse_money_brl(text: str) -> float | None:
    if not text:
        return None

    clean = text.replace("R$", "").strip()
    match = re.search(r"(\d+[\.,]?\d*)", clean)

    if not match:
        return None

    value = match.group(1)

    if "," in value:
        value = value.replace(".", "").replace(",", ".")

    return float(value)


def normalize_cabin(text: str) -> str | None:
    if not text:
        return None

    lower = text.lower()

    for key, label in CABIN_TRANSLATIONS.items():
        if key in lower:
            return label

    return None


def to_ampm(time_text: str) -> str:
    if not time_text:
        return ""

    try:
        dt = parser.parse(time_text)
        return dt.strftime("%I:%M%p").lstrip("0").lower()
    except Exception:
        return time_text


def date_to_smiles_timestamp_ms(date_obj) -> int:
    dt = datetime(
        date_obj.year,
        date_obj.month,
        date_obj.day,
        tzinfo=timezone.utc
    )

    return int(dt.timestamp() * 1000)


def build_smiles_url(origin: str, destination: str, date_obj) -> str:
    timestamp_ms = date_to_smiles_timestamp_ms(date_obj)

    return (
        "https://www.smiles.com.br/mfe/emissao-passagem/"
        f"?adults=1&cabin=ALL&children=0&departureDate={timestamp_ms}"
        "&infants=0&isElegible=false&isFlexibleDateChecked=false&returnDate="
        "&searchType=congenere&segments=1&tripType=2"
        f"&originAirport={origin.upper()}&originCity=&originCountry="
        "&originAirportIsAny=false"
        f"&destinationAirport={destination.upper()}&destinCity=&destinCountry="
        "&destinAirportIsAny=false&novo-resultado-voos=true"
    )
