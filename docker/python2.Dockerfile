FROM docker.io/mobify/python:2.7.11

WORKDIR /grimace
RUN virtualenv /venv && \
    . /venv/bin/activate && \
    pip install nose nine
