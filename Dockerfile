FROM python:3.7-buster

RUN curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python

RUN mkdir -p /src
COPY lib /src/lib
COPY src /src/app

WORKDIR /src/lib
RUN /root/.poetry/bin/poetry install

CMD /root/.poetry/bin/poetry run python3 ../app/app.py