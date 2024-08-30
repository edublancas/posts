from pathlib import Path
from typing import List, Dict
import json

from openai import OpenAI
from pydantic import BaseModel
from selenium.webdriver.common.by import By
from tenacity import retry, stop_after_attempt
from bs4 import BeautifulSoup

from aiwebscraper.browser import Browser

from aiwebscraper.cache import FunctionCache

client = OpenAI()


MODEL = "gpt-4o-2024-08-06"
# MODEL = "gpt-4o-mini"


class ParsedColumn(BaseModel):
    name: str
    values: List[str]


class ParsedTable(BaseModel):
    name: str
    columns: List[ParsedColumn]


class ColumnXPath(BaseModel):
    name: str
    xpath: str


def find_root_dir(max_levels=5):
    current_dir = Path.cwd()

    for _ in range(max_levels):
        env_file = current_dir / ".root"

        if env_file.is_file():
            return current_dir

        parent_dir = current_dir.parent

        if parent_dir == current_dir:
            break

        current_dir = parent_dir

    raise FileNotFoundError("No root directory found")


path_to_cache = find_root_dir() / "cache.db"


def chat_completion_parsed_table(*, model, messages):
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=messages,
        response_format=ParsedTable,
    )
    parsed = completion.choices[0].message.parsed
    return {c.name: c.values for c in parsed.columns}


chat_completion_parsed_table_cached = FunctionCache(
    chat_completion_parsed_table,
    path_to_cache,
)


def extract_table_data(html_content: str) -> ParsedTable:
    """Extracts the table data from the HTML content."""

    SYS_PROMPT = """
You're an expert web scraper. You're given the HTML contents of a table and you
have to extract structured data from it.

Tables might collapse rows into a single row. If that's the case, extract
the collapsed row as multiple JSON values to ensure all columns contain the same number
of rows.
    """
    table = chat_completion_parsed_table_cached(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": SYS_PROMPT,
            },
            {
                "role": "user",
                "content": "The HTML content is: " + html_content,
            },
            {
                "role": "user",
                "content": "Extract the table:",
            },
        ],
    )
    return table


def get_xpath_for_column(
    html_content: str,
    extracted_values: List[str],
    column_name: str,
) -> ColumnXPath:
    """Gets the XPath for a column."""

    # Only use // at the beginning of the XPath.
    # When selecting by class, respect the whitespace in the class name.
    SYS_PROMPT = """
    You're an expert web scraper.

    The user will provide the HTML content and the extracted values in JSON format.
    Your job is to come up with an XPath that will return all elements of that column.

    The XPath should be a string that can be evaluated by Selenium's
    `driver.find_elements(By.XPATH, xpath)` method.

    Return the full matching element, not just the text.
    """
    # TODO: note that the extracted values might not match 100% since the extractor
    # might interpret images as text. we need to add that to the prompt somehow
    completion = client.beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": SYS_PROMPT,
            },
            {
                "role": "user",
                "content": "The HTML content is: " + html_content,
            },
            {
                "role": "user",
                "content": "The extracted values in JSON format are: "
                + json.dumps(extracted_values),
            },
            {
                "role": "user",
                "content": "Extract the column with name: " + column_name,
            },
        ],
        response_format=ColumnXPath,
    )

    parsed = completion.choices[0].message.parsed
    return parsed


def clean_html(html_content: str) -> str:
    # Parse the HTML
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()

    # List of attributes to keep
    attrs_to_keep = ["class", "id", "data-testid"]

    # Remove all attributes except those in attrs_to_keep
    for tag in soup.find_all():
        for attr in list(tag.attrs.keys()):
            if attr not in attrs_to_keep:
                del tag[attr]

    # Get the cleaned HTML as a string
    cleaned_html = str(soup)

    return cleaned_html


class WebScraper:
    """
    Scrapes a website and extracts data from it.
    """

    def __init__(self, url: str, element_xpath: str):
        self.url = url
        self.element_xpath = element_xpath

        self.browser = Browser(url)
        self.browser.wait_randomly(2, 3)

        if element_xpath is None:
            self.body_element = self.browser.find_element_by_xpath("//body")
        else:
            self.body_element = self.browser.find_element_by_xpath(element_xpath)

        # maybe remove all script tags?
        self.html_content = clean_html(self.body_element.get_attribute("innerHTML"))

    def extract_table_data(self) -> ParsedTable:
        return extract_table_data(self.html_content)

    def extract_xpath_for_column(
        self, values: List[str], column_name: str
    ) -> List[str]:
        # wikipedia: 4 is not working because the model is intepreting the content
        parsed = get_xpath_for_column(
            self.html_content,
            values,
            column_name,
        )
        elements = self.body_element.find_elements(By.XPATH, parsed.xpath)
        return parsed.xpath, elements


def get_from_xpaths(url, element_xpath, xpaths: Dict[str, str]) -> ParsedTable:
    browser = Browser(url)
    browser.wait_randomly(2, 3)

    if element_xpath is None:
        body_element = browser.find_element_by_xpath("//body")
    else:
        body_element = browser.find_element_by_xpath(element_xpath)

    table = {}

    for name, xpath in xpaths.items():
        elements = body_element.find_elements(By.XPATH, xpath)
        values = [element.text for element in elements]
        table[name] = values

    return table


def get_data_with_scraper(scraper: WebScraper, data: Dict[str, List[str]]) -> Dict:
    xpaths = {}

    @retry(stop=stop_after_attempt(3))
    def extract_xpath_for_column(values, name):
        xpath, results = scraper.extract_xpath_for_column(values, name)

        if not results:
            raise ValueError("XPath did not return any results")

        return xpath, results

    for name, values in data.items():
        xpath, _ = extract_xpath_for_column(values, name)
        xpaths[name] = xpath

    return {
        "url": scraper.url,
        "element_xpath": scraper.element_xpath,
        "xpaths": xpaths,
    }


def get_data(*, url, element_xpath, xpaths: Dict[str, str]) -> Dict:
    scraper = WebScraper(url, element_xpath)
    return get_data_with_scraper(scraper, xpaths)
