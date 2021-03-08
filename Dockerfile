FROM python:3.7-slim

RUN apt-get update \
 && apt-get install -y curl \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
ENV POETRY_VERSION=1.0.5
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python - --version $POETRY_VERSION
ENV PATH="/root/.poetry/bin:${PATH}"

ENV WORKDIR=/var/app/
ENV PYTHONPATH=$WORKDIR
RUN mkdir -p $WORKDIR
WORKDIR $WORKDIR

# commented during development step
#COPY technical_test technical_test
ADD poetry.lock pyproject.toml $WORKDIR

RUN poetry config virtualenvs.create false
RUN poetry install

RUN ls $WORKDIR
