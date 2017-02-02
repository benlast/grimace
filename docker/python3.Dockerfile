FROM docker.io/mobify/python:3.5

WORKDIR /grimace
RUN pyvenv /venv && \
    . /venv/bin/activate && \
    pip install nose nine
