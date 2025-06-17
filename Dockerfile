FROM python:3.11-slim AS dev

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  # Poetry's configuration:
  POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_CACHE_DIR='/var/cache/pypoetry' \
  POETRY_HOME='/usr/local' \
  POETRY_VERSION=2.1.3

# System deps:
RUN apt update && apt install curl -y && curl -sSL https://install.python-poetry.org | python3 -

# Copy only requirements to cache them in docker layer
WORKDIR /code
COPY poetry.lock pyproject.toml /code/

RUN poetry install --no-root --no-interaction --only=main

COPY src README.md /code/

RUN poetry install --no-interaction --only-root


ENTRYPOINT ["poetry", "-q", "run", "grader"]


FROM dev AS builder

RUN poetry build --format wheel

FROM python:3.11-slim AS prod

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100

COPY --from=builder /code/dist/*.whl /tmp/

RUN pip install --no-cache-dir /tmp/*.whl && \
  rm -rf /tmp/*

ENTRYPOINT ["grader"]