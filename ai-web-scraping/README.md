

```sh
pip install invoke
invoke setup
conda activate aiwebscraper

streamlit run app/app.pyp
```

```
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```


```sh
docker run -it --entrypoint /bin/bash aiwebscraper
```


Testing selenium:

```
/usr/bin/google-chrome --no-sandbox --headless
```

```python
from aiwebscraper.browser import Browser

b = Browser("https://google.com")
```

```sh

ws scrape \
    'https://finance.yahoo.com/markets/stocks/gainers/?start=0&count=100' \
    --element-xpath '//*[@id="nimbus-app"]/section/section/section/article/section[1]/div/div[1]' \
    --output stocks.json

ws fromresult stocks.json

```


```sh
ws scrape \
    'https://en.wikipedia.org/wiki/Human_Development_Index' \
    --element-xpath '/html/body/div[2]/div/div[3]/main/div[3]/div[3]/div[1]/table[1]' \
    --output hdi.json

ws fromresult hdi.json
```