FROM python:3.11.2-slim

RUN apt-get -y update \
    && apt-get -y install curl gfortran wget gnupg2 \
    && rm -rf /var/lib/apt/lists/*

# install google chrome
RUN wget -qO- https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get update
RUN apt-get install google-chrome-stable -y
RUN apt-get clean
# # install chromedriver
RUN apt-get install unzip jq -yqq
RUN wget -O /tmp/chromedriver-linux64.zip https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/`wget -qO- https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json | jq -r '.channels.Stable.version'`/linux64/chromedriver-linux64.zip
RUN unzip /tmp/chromedriver-linux64.zip chromedriver-linux64/chromedriver -d /usr/local/bin/
# set display port to avoid crash
ENV DISPLAY=:99

# install selenium
RUN pip install selenium>=4.1.3
RUN pip install unidecode


WORKDIR /app
COPY . .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

EXPOSE 8060

ENV GOOGLE_APPLICATION_CREDENTIALS="./configuration/fubloo-app-1f213ca274de.json"

ENTRYPOINT [./scripts/start.sh]
