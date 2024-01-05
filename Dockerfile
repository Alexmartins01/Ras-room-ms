FROM alpine:latest


RUN apk add --no-cache build-base
RUN apk add --no-cache python3-dev py3-pip

# mariadb because i couldn't get it to work on ubuntu with mysql
RUN apk add --no-cache mariadb-client mariadb-connector-c mariadb-dev

RUN mkdir /app

WORKDIR /app
ADD rooms/ rooms/
COPY requirements.txt .
RUN python3 -m venv .venv/

ENV PATH="/app/.venv/bin:$PATH"

RUN python3 -m pip install -r requirements.txt

COPY rooms-start.sh util_cmd.py .

CMD ash rooms-start.sh

EXPOSE 8000