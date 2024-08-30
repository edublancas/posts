from aiwebscraper.extract import WebScraper


def test_wikipedia_hdi(snapshot):
    scraper = WebScraper(
        "https://en.wikipedia.org/wiki/Human_Development_Index",
        element_xpath="/html/body/div[2]/div/div[3]/main/div[3]/div[3]/div[1]/table[1]",
    )

    table_data = scraper.extract_table_data()

    assert table_data.columns == snapshot


def test_yahoo_finance_gainers():
    scraper = WebScraper(
        "https://finance.yahoo.com/markets/stocks/gainers/?start=0&count=100",
        element_xpath='//*[@id="nimbus-app"]/section/section/section/article/section[1]/div/div[1]',
    )

    table_data = scraper.extract_table_data()

    # assert table_data.columns == snapshot

    from IPython import embed

    embed()

    xpath, elements = scraper.extract_xpath_for_column(
        table_data.columns[1].values, table_data.columns[1].name
    )
