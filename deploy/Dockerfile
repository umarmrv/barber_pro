FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY migrations ./migrations

RUN pip install --no-cache-dir .[dev]

CMD ["python", "-m", "barber_bot.entrypoints.api_server"]
