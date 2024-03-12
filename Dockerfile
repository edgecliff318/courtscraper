FROM python:3.11.2-slim

RUN apt-get -y update \
    && apt-get -y install curl gfortran wget gnupg2 \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app
COPY . .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

EXPOSE 8060

ENV GOOGLE_APPLICATION_CREDENTIALS="./configuration/fubloo-app-1f213ca274de.json"

ENTRYPOINT [./scripts/start.sh]
