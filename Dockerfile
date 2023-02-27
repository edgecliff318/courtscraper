FROM python:3.8.5-slim

RUN apt-get -y update \
    && apt-get -y install curl gfortran wget gnupg2 \
    && rm -rf /var/lib/apt/lists/*

# install google chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update
RUN apt-get install -y google-chrome-stable

# install chromedriver
RUN apt-get install -yqq unzip
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/

# set display port to avoid crash
ENV DISPLAY=:99

# install selenium
RUN pip install selenium==4.1.3

COPY requirements.txt /app/requirements.txt
COPY packages_install.sh /app/packages_install.sh

WORKDIR /app

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

RUN pip install unidecode

COPY ./ ./

RUN rm -rf ./packages

EXPOSE 8050

ENV GOOGLE_APPLICATION_CREDENTIALS="./configuration/fubloo-app-1f213ca274de.json" 

ENTRYPOINT ["gunicorn", "--config", "gunicorn_config.py", "server:server"]