FROM python:3.11-slim AS dev

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100

# System deps:
RUN apt update && apt install curl -y && curl -LsSf https://astral.sh/uv/install.sh | env UV_UNMANAGED_INSTALL="/usr/bin" sh

# Copy only requirements to cache them in docker layer
WORKDIR /code
COPY uv.lock pyproject.toml /code/

RUN uv sync --no-install-project --no-dev -p $(which python)

COPY README.md /code/

COPY src /code/src/

RUN uv sync --no-dev -p $(which python)

ENTRYPOINT ["uv", "run", "grader"]

FROM dev AS builder

RUN uv build --wheel

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