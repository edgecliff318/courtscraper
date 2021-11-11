FROM python:3.8.5-slim

RUN apt-get -y update \
    && apt-get -y install curl gfortran \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
COPY packages_install.sh /app/packages_install.sh

WORKDIR /app

RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

COPY ./packages ./packages

RUN /app/packages_install.sh

COPY ./ ./

RUN rm -rf ./packages

EXPOSE 8050

ENTRYPOINT ["gunicorn", "--config", "gunicorn_config.py", "server:server"]