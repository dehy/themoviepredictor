FROM alpine

RUN apk update && apk add python3
RUN pip3 install argparse mysql-connector-python beautifulsoup4 requests

COPY . /usr/src/themoviepredictor

WORKDIR /usr/src/themoviepredictor
CMD python3 /usr/src/themoviepredictor/app.py movies import --api all --for 7