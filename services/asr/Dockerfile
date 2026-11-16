# Образ сервиса asr. Тяжёлые модели монтируются томом /models, в образ не входят.
# Пример с реальными моделями: --build-arg EXTRAS="--extra sherpa --extra whisper"
FROM python:3.12-slim AS build
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /usr/local/bin/uv
WORKDIR /app
ARG EXTRAS=""
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project $EXTRAS
COPY src ./src
RUN uv sync --frozen --no-dev $EXTRAS

FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends libopus0 && rm -rf /var/lib/apt/lists/* \
    && useradd --system --uid 10001 --home /app doomich
WORKDIR /app
COPY --from=build --chown=doomich /app /app
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER doomich
EXPOSE 8000
CMD ["uvicorn", "--factory", "doomich_asr.app:create_app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
