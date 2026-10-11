FROM python:3.12-slim

RUN pip install --no-cache-dir dbt-core==1.12.5 dbt-postgres==1.11.0

WORKDIR /usr/app
ENV DBT_PROFILES_DIR=/usr/app
