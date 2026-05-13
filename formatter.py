from collections import defaultdict
from utils import points_cash_value


def availability_rank(flight: dict) -> int:
    has_economy = flight.get("economy_points") is not None
    has_business = flight.get("business_points") is not None

    if has_economy and has_business:
        return 0

    if has_economy:
        return 1

    if has_business:
        return 2

    return 3


def format_price(points: int | None, tax_usd: float | None) -> str:
    if points is None:
        return ""

    value = points_cash_value(points)

    tax = (
        f" + ${tax_usd:.2f} taxes"
        if tax_usd is not None
        else ""
    )

    return f"{points:,} points{tax} | est. value ${value:.2f}"


def format_results(flights: list[dict]) -> str:
    if not flights:
        return "No verified flights found."

    flights = sorted(
        flights,
        key=lambda f: (
            f.get("origin", ""),
            f.get("airline", ""),
            availability_rank(f),
            f.get("departure_sort", "99:99"),
        ),
    )

    grouped = defaultdict(list)

    for flight in flights:
        grouped[
            (
                flight.get("origin", ""),
                flight.get("airline", "Unknown Airline")
            )
        ].append(flight)

    lines = []

    for (origin, airline), group in grouped.items():
        lines.append(origin)

        for flight in group:
            plus_one = (
                " (+1)"
                if flight.get("arrives_next_day")
                else ""
            )

            lines.append(
                f'{flight["origin"]} '
                f'{flight["departure"]} - '
                f'{flight["destination"]} '
                f'{flight["arrival"]}{plus_one}'
            )

            economy = format_price(
                flight.get("economy_points"),
                flight.get("economy_tax_usd"),
            )

            business = format_price(
                flight.get("business_points"),
                flight.get("business_tax_usd"),
            )

            if economy:
                lines.append(
                    f"{airline} Economy Class {economy}"
                )

            if business:
                lines.append(
                    f"{airline} Business Class {business}"
                )

        lines.append("")

    return "\n".join(lines).strip()
