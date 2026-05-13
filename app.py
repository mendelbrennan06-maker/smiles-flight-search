import streamlit as st
import pandas as pd

from utils import airport_list
from scraper import SmilesScraper
from formatter import format_results

st.set_page_config(
    page_title="Smiles Flight Search",
    layout="wide"
)

st.title("Smiles Flight Search")

st.write(
    "Search Smiles award flights "
    "and format results automatically."
)

with st.sidebar:
    st.header("Search")

    origin = st.text_input(
        "Origin airport or city",
        "NYC"
    ).upper().strip()

    destination = st.text_input(
        "Destination airport",
        "YYZ"
    ).upper().strip()

    date_obj = st.date_input("Departure date")

    max_points = st.number_input(
        "Max points",
        min_value=0,
        value=20_000,
        step=1_000
    )

    brl_rate = st.number_input(
        "BRL per USD rate",
        min_value=1.0,
        value=5.38,
        step=0.01
    )

    headless = st.checkbox(
        "Run browser hidden",
        value=False
    )

search_clicked = st.button(
    "Search flights",
    type="primary"
)

if search_clicked:
    origins = airport_list(origin)

    scraper = SmilesScraper(
        headless=headless
    )

    all_flights = []
    debug_outputs = {}

    for airport in origins:
        with st.status(
            f"Searching {airport} to {destination}..."
        ):

            flights, debug_text = scraper.search(
                origin=airport,
                destination=destination,
                date_obj=date_obj,
                max_points=max_points,
                brl_rate=brl_rate,
            )

            all_flights.extend(flights)
            debug_outputs[airport] = debug_text

    st.subheader("Formatted result")

    st.code(
        format_results(all_flights),
        language="text"
    )

    if all_flights:
        st.subheader("Table view")

        st.dataframe(
            pd.DataFrame(all_flights),
            use_container_width=True
        )

    with st.expander("Debug text from Smiles page"):
        for airport, text in debug_outputs.items():
            st.markdown(f"### {airport}")
            st.text(text[:15000])

else:
    st.info(
        "Enter route/date/max points "
        "then click Search flights."
    )
