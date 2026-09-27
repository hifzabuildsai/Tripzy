FROM python:3.12-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build

COPY pyproject.toml README.md ./
COPY app ./app

RUN python -m venv /opt/venv \
    && /opt/venv/bin/python -m pip install --upgrade pip \
    && /opt/venv/bin/python -m pip install .


FROM python:3.12-slim AS runtime

ENV PATH="/opt/venv/bin:${PATH}" \
    PORT=8000 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --gid 10001 tripzy \
    && useradd --uid 10001 --gid tripzy --create-home --shell /usr/sbin/nologin tripzy

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

USER tripzy

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8000') + '/health', timeout=3)" || exit 1

CMD ["python", "-m", "app.server"]
