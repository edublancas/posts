# chrome is not available for ARM
FROM --platform=linux/amd64 python:3.12-slim

WORKDIR /srv

RUN apt-get update && apt-get install -y wget curl unzip
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt-get install -y ./google-chrome-stable_current_amd64.deb
RUN google-chrome --version

# https://googlechromelabs.github.io/chrome-for-testing/#stable
RUN curl -o chromedriver_linux64.zip https://storage.googleapis.com/chrome-for-testing-public/128.0.6613.86/linux64/chromedriver-linux64.zip
RUN unzip chromedriver_linux64.zip
RUN chmod +x chromedriver-linux64
RUN mv -f chromedriver-linux64 /usr/local/bin/chromedriver

COPY requirements.txt /srv/
RUN pip install -r requirements.txt --no-cache-dir

COPY aiwebscraper /srv/aiwebscraper
RUN pip install --editable /srv/aiwebscraper

RUN touch /srv/.root

COPY . /srv

ENTRYPOINT ["streamlit", "run", "app.py", \
            "--server.port=80", \
            "--server.headless=true", \
            "--server.address=0.0.0.0", \
            "--browser.gatherUsageStats=false", \
            "--server.enableStaticServing=true", \
            "--server.fileWatcherType=none", \
            "--client.toolbarMode=viewer"]