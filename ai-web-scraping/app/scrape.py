import datetime
import json
from enum import Enum
import streamlit as st
import pandas as pd

from aiwebscraper.extract import WebScraper, get_data, get_from_xpaths
from aiwebscraper.cache import FunctionCache


class ScrapingStep(Enum):
    WAITING_FOR_INPUT = 1
    WAITING_FOR_CONFIRMATION = 2
    GETTING_XPATHS = 3
    FINISHED = 4


# Initialize the step in session state if it doesn't exist
if "step" not in st.session_state:
    st.session_state.step = ScrapingStep.WAITING_FOR_INPUT.value

if "df" not in st.session_state:
    st.session_state.df = None


def _scrape_data(*, url: str, xpath: str):
    try:
        scraper = WebScraper(url, xpath)
        parsed_table = scraper.extract_table_data()
        return parsed_table
    except Exception as e:
        return str(e)


scrape_data = FunctionCache(_scrape_data, "cache.db")
get_data_cached = FunctionCache(get_data, "cache.db")

# scrape_data = _scrape_data
# get_data_cached = get_data

st.title("AI Web Scraper")
st.write("Scrape a website using AI.")


def scrape_example(url: str, xpath: str):
    st.session_state.url = url
    st.session_state.xpath = xpath
    result = scrape_data(url=url, xpath=xpath)

    if isinstance(result, str):
        st.error(f"An error occurred: {result}")
    else:
        try:
            df = pd.DataFrame.from_records(result)
            df = df[list(result)]
        except Exception:
            st.session_state.df = result
        else:
            st.session_state.df = df

        st.session_state.result = result
        st.session_state.step = ScrapingStep.WAITING_FOR_CONFIRMATION.value
        st.rerun()


if st.session_state.step == ScrapingStep.WAITING_FOR_INPUT.value:
    url = st.text_input("Enter the URL to scrape:")
    xpath = st.text_input("Enter the XPath of the element to scrape:")

    if st.button("Scrape Data"):
        if url and xpath:
            st.info("Scraping data...")
            scrape_example(url, xpath)
        else:
            st.warning("Please enter both URL and XPath.")

    st.write("Or select an example:")

    if st.button("Yahoo Finance Top Stocks"):
        scrape_example(
            "https://finance.yahoo.com/markets/stocks/gainers/?start=0&count=100",
            '//*[@id="nimbus-app"]/section/section/section/article/section[1]/div/div[1]',
        )

    if st.button("Wikipedia Human Development Index"):
        scrape_example(
            "https://en.wikipedia.org/wiki/Human_Development_Index",
            "/html/body/div[2]/div/div[3]/main/div[3]/div[3]/div[1]/table[1]",
        )

    if st.button("NYC 10-day Weather Forecast"):
        scrape_example(
            "https://weather.com/weather/tenday/l/5270ac845006eff915905ebb80f9449d5ab8cc74d4398ef448d8585a469f07b53697c3b66978e0f3df1a22589d061ec2",
            "/html/body/div[1]/main/div[2]/main/div[1]/section/div[2]/div[2]",
        )

if st.session_state.step == ScrapingStep.WAITING_FOR_CONFIRMATION.value:

    if isinstance(st.session_state.df, dict):
        st.warning("Could not parse the result as a table. Showing JSON instead.")
        st.json(st.session_state.df, expanded=1)
    else:
        st.write(st.session_state.df)

    if st.button("Export scraper"):
        st.session_state.step = ScrapingStep.GETTING_XPATHS.value
        st.rerun()

if st.session_state.step == ScrapingStep.GETTING_XPATHS.value:
    st.info("Exporting scraper...")

    data = get_data_cached(
        url=st.session_state.url,
        element_xpath=st.session_state.xpath,
        xpaths=st.session_state.result,
    )
    st.session_state.step = ScrapingStep.FINISHED.value
    st.session_state.data = data

    # table = get_from_xpaths(data["url"], data["element_xpath"], data["xpaths"])
    # st.write(pd.DataFrame.from_records(table))

    st.rerun()

if st.session_state.step == ScrapingStep.FINISHED.value:
    st.success("Scraper exported successfully!")
    current_timestamp = datetime.datetime.now()
    unique_name = f"scraper_{current_timestamp.strftime('%Y%m%d_%H%M%S')}"

    st.download_button(
        label="Download Data as JSON",
        data=json.dumps(st.session_state.data, indent=2),
        file_name=unique_name,
        mime="application/json",
    )
