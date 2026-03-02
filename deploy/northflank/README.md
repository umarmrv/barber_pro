# Northflank Deploy

This directory contains an isolated deployment set for Northflank. It does not replace the existing `deploy/` files used for local `docker-compose`.

## Runtime

- Framework: FastAPI + uvicorn
- Public API port: `8000`
- Health endpoint: `GET /healthz`
- Readiness endpoint: `GET /readyz`
- Telegram webhook endpoint: `POST /telegram/webhook`

## Service Commands

- API:
  `python -m barber_bot.entrypoints.api_server`
- Bot:
  `python -m barber_bot.entrypoints.bot_service`
- Scheduler:
  `python -m barber_bot.scheduler.runner`

## Required Environment

Use `deploy/northflank/.env.example` as the baseline for service secrets and variables.

Important names for this codebase:

- `POSTGRES_DSN`
- `POSTGRES_DSN_SYNC`
- `REDIS_DSN`
- `WEBHOOK_URL`
- `WEBHOOK_SECRET`

## Webhook URL

Set:

`WEBHOOK_URL=https://<northflank-domain>/telegram/webhook`

Do not use `/webhook`; the app route is `/telegram/webhook`.

## Build

Build with the repository root as context and the Dockerfile path:

`deploy/northflank/Dockerfile`

The image includes `postgresql-client`, so `psql` is available for one-off migration jobs.

## Migrations

Run the helper as a one-off job:

`sh deploy/northflank/migrate.sh`

The script applies:

1. `migrations/001_init.sql`
2. `migrations/002_seed.sql`
3. `migrations/003_admin_guest_hard_delete.sql`
4. `migrations/004_tajik_locale_and_service_name.sql`

It uses `POSTGRES_DSN_SYNC` if present, otherwise falls back to `POSTGRES_DSN`.

## Recommended Service Layout

- `barber-api`: public HTTP service, port `8000`
- `barber-bot`: internal worker, no public port
- `barber-scheduler`: internal worker, no public port

Recommended override for `barber-bot`:

- `SKIP_BOT_API_CALLS=true`

This prevents duplicate `setWebhook` and command registration if `barber-api` is already handling those on startup.
