FROM python:3.10-slim-buster

ADD https://www.google.com /time.now

WORKDIR /app

RUN apt-get -y update && apt-get -y install git curl gcc python3-dev ffmpeg

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "-m" , "scp"]