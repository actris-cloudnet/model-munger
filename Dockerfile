FROM python:3.10-bullseye AS base

WORKDIR /app
COPY pyproject.toml README.md /app
COPY src /app/src
RUN pip3 install --upgrade pip && pip3 install --no-cache-dir .
