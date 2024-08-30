FROM ubuntu:latest

RUN apt-get update -y
RUN apt-get install -y git curl python3

RUN curl -sSL https://install.python-poetry.org > install-poetry.py
RUN python3 install-poetry.py

ENV PATH=/root/.local/bin:$PATH

COPY . .

RUN poetry lock --no-update
RUN poetry install
