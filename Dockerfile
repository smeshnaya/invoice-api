FROM python:3.12 AS poetry
LABEL maintainer="Alexey Voskresenskiy <alexey.voskresenskiy@ornament.health>"
ENV PYTHONUNBUFFERED=true
RUN pip install poetry==1.6.1


FROM poetry AS builder
WORKDIR /app
ENV POETRY_HOME=/opt/poetry \
    PATH="$POETRY_HOME/bin:$PATH"

COPY pyproject.toml .
COPY poetry.toml .
COPY poetry.lock .

RUN poetry install --no-interaction

FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /app .
COPY . .

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PYTHONPATH=/app/.venv

RUN mkdir -p /app/datadir/logs

HEALTHCHECK --interval=1m --timeout=1s CMD python bin/healthcheck.py http://127.0.0.1:5000 || exit 1

CMD python main.py
