import re
import random

from playwright.sync_api import sync_playwright

from utils import (
    build_smiles_url,
    to_ampm,
    parse_points,
    parse_money_brl,
    brl_to_usd,
)


class SmilesScraper:

    def __init__(self, headless=True):
        self.headless = headless

    def search(
        self,
        origin,
        destination,
        date_obj,
        max_points,
        brl_rate,
    ):

        flights = []
        debug_text = ""

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ]
            )

            context = browser.new_context(
                viewport={
                    "width": 1440,
                    "height": 1200,
                },

                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),

                locale="en-US",

                timezone_id="America/New_York",
            )

            page = context.new_page()

            page.set_default_timeout(60000)

            url = build_smiles_url(
                origin,
                destination,
                date_obj
            )

            page.goto(
                url,
                wait_until="networkidle",
                timeout=90000
            )

            page.wait_for_timeout(
                random.randint(4000, 7000)
            )

            # Cookie buttons
            cookie_texts = [
                "Accept",
                "Aceitar",
                "I agree",
                "Concordo",
            ]

            for text in cookie_texts:
                try:
                    page.get_by_text(
                        text,
                        exact=False
                    ).click(timeout=3000)

                    page.wait_for_timeout(2000)

                except Exception:
                    pass

            # Scroll like a user
            try:
                page.mouse.wheel(0, 1200)
                page.wait_for_timeout(2000)

                page.mouse.wheel(0, -500)
                page.wait_for_timeout(2000)

            except Exception:
                pass

            # Retry waiting
            page.wait_for_timeout(
                random.randint(6000, 12000)
            )

            # Attempt to click search again
            search_texts = [
                "Search",
                "Buscar",
                "Pesquisar",
            ]

            for text in search_texts:
                try:
                    page.get_by_text(
                        text,
                        exact=False
                    ).click(timeout=3000)

                    page.wait_for_timeout(5000)

                except Exception:
                    pass

            # Final wait
            page.wait_for_timeout(
                random.randint(5000, 10000)
            )

            try:
                debug_text = page.locator(
                    "body"
                ).inner_text(timeout=20000)

            except Exception as exc:
                debug_text = str(exc)

            card_selectors = [
                "[data-testid*='flight']",
                "[class*='flight']",
                "[class*='Flight']",
                "[class*='result']",
                "[class*='Result']",
                "[class*='card']",
                "[class*='Card']",
            ]

            cards = []

            for selector in card_selectors:

                locator = page.locator(selector)

                try:
                    count = locator.count()

                    if count > 0:
                        cards = [
                            locator.nth(i)
                            for i in range(
                                min(count, 100)
                            )
                        ]

                        break

                except Exception:
                    continue

            for card in cards:

                try:
                    text = card.inner_text(
                        timeout=3000
                    )

                    parsed = self._parse_card_text(
                        text,
                        origin,
                        destination,
                        brl_rate,
                    )

                    if not parsed:
                        continue

                    if not self._under_max_points(
                        parsed,
                        max_points
                    ):
                        continue

                    flights.append(parsed)

                except Exception:
                    continue

            browser.close()

        return flights, debug_text

    def _under_max_points(
        self,
        flight,
        max_points
    ):

        prices = [
            flight.get("economy_points"),
            flight.get("business_points"),
        ]

        prices = [
            p for p in prices
            if p is not None
        ]

        return (
            bool(prices)
            and any(p <= max_points for p in prices)
        )

    def _parse_card_text(
        self,
        text,
        origin,
        destination,
        brl_rate,
    ):

        lower = text.lower()

        airline = "Unknown Airline"

        if "air canada" in lower:
            airline = "Air Canada"

        elif "american" in lower:
            airline = "American Airlines"

        elif "united" in lower:
            airline = "United"

        elif "delta" in lower:
            airline = "Delta"

        times = re.findall(
            r"\b([01]?\d|2[0-3]):([0-5]\d)\b",
            text
        )

        if len(times) < 2:
            return None

        departure_24 = (
            f"{times[0][0].zfill(2)}:"
            f"{times[0][1]}"
        )

        arrival_24 = (
            f"{times[1][0].zfill(2)}:"
            f"{times[1][1]}"
        )

        departure = to_ampm(departure_24)
        arrival = to_ampm(arrival_24)

        arrives_next_day = (
            "(+1)" in text
            or "+1" in text
        )

        all_points = re.findall(
            r"(?:\d+[\.,]?\d*)\s*"
            r"(?:milhas|milha|miles|pontos|pts)",
            text,
            flags=re.I
        )

        parsed_points = [
            parse_points(p)
            for p in all_points
        ]

        parsed_points = [
            p for p in parsed_points
            if p is not None
        ]

        money_matches = re.findall(
            r"R\$\s*\d+[\.,]?\d*",
            text,
            flags=re.I
        )

        taxes_brl = [
            parse_money_brl(m)
            for m in money_matches
        ]

        taxes_brl = [
            t for t in taxes_brl
            if t is not None
        ]

        first_tax_usd = (
            brl_to_usd(
                taxes_brl[0],
                brl_rate
            )
            if taxes_brl
            else None
        )

        economy_points = None
        business_points = None

        economy_tax_usd = None
        business_tax_usd = None

        if parsed_points:

            if (
                "business" in lower
                or "executiva" in lower
            ):

                if (
                    "econom" in lower
                    or "econôm" in lower
                ):

                    economy_points = min(
                        parsed_points
                    )

                    business_points = max(
                        parsed_points
                    )

                    economy_tax_usd = first_tax_usd
                    business_tax_usd = first_tax_usd

                else:
                    business_points = parsed_points[0]
                    business_tax_usd = first_tax_usd

            else:
                economy_points = parsed_points[0]
                economy_tax_usd = first_tax_usd

        return {
            "origin": origin,
            "destination": destination,
            "departure": departure,
            "arrival": arrival,
            "departure_sort": departure_24,
            "arrival_sort": arrival_24,
            "arrives_next_day": arrives_next_day,
            "airline": airline,
            "economy_points": economy_points,
            "business_points": business_points,
            "economy_tax_usd": economy_tax_usd,
            "business_tax_usd": business_tax_usd,
            "raw_text": text,
        }
