FROM python:3.9.5-alpine

WORKDIR /usr/src/app

COPY ./requirements.txt .

CMD pip install -r requirements.txt

COPY . .

RUN python app.py
