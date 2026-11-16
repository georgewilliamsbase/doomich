# Образ Core API и воркеров.
# Сборка с Docling (тяжелее, для воркера документов): --build-arg EXTRAS="--extra docling --extra ocr"
FROM python:3.12-slim AS build
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /usr/local/bin/uv
WORKDIR /app
ARG EXTRAS=""
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project $EXTRAS
COPY src ./src
COPY migrations ./migrations
COPY alembic.ini README.md ./
RUN uv sync --frozen --no-dev $EXTRAS

FROM python:3.12-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends libopus0 fonts-dejavu-core tesseract-ocr tesseract-ocr-rus \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --uid 10001 --home /app doomich
WORKDIR /app
COPY --from=build --chown=doomich /app /app
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 DOOMICH_DATA_DIR=/data
USER doomich
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"
CMD ["uvicorn", "--factory", "doomich.main:create_app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--no-access-log"]
