FROM python:3.12-alpine3.20
LABEL maintainer="tetyana.pas@gmail.com"

ENV PYTHONUNBUFFERED 1

WORKDIR app/

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .
