import sys
import json

import click
import pandas as pd

from aiwebscraper.extract import (
    WebScraper,
    ParsedTable,
    get_from_xpaths,
    get_data_with_scraper,
)


@click.group()
def cli():
    pass


@cli.command()
@click.argument("json_file", type=click.Path(exists=True))
def fromresult(json_file):
    """Process a JSON file."""
    try:
        with open(json_file, "r") as file:
            data = json.load(file)

        table = get_from_xpaths(data["url"], data["element_xpath"], data["xpaths"])
        click.echo(table)

    except json.JSONDecodeError:
        click.echo(f"Error: {json_file} is not a valid JSON file.", err=True)
        sys.exit(1)


@cli.command()
@click.argument("url", type=str)
@click.option(
    "--element-xpath",
    type=str,
    default=None,
    help="XPath of the element to scrape",
)
@click.option(
    "--output",
    "-o",
    type=str,
    default=None,
    help="Output file to save the results",
)
def scrape(url, element_xpath, output):
    """Scrape data from a given URL."""

    scraper = WebScraper(url, element_xpath)
    parsed_table: ParsedTable = scraper.extract_table_data()

    click.echo(f"Successfully scraped data from {url}")

    for name, values in parsed_table.items():
        click.echo(f"Column: {name}")
        click.echo(f"Values: {', '.join(values[:5])}...")

    if output:
        data = get_data_with_scraper(scraper, parsed_table)

        # TODO: maybe try with the mini model here?
        table = get_from_xpaths(data["url"], data["element_xpath"], data["xpaths"])

        df = pd.DataFrame.from_records(table)
        click.echo(df)

        with open(output, "w") as file:
            json.dump(data, file)

        click.echo(f"XPaths saved to {output}")
