# Barber Shop Telegram Bot

Production-oriented Telegram booking bot for a single barber shop branch.

## Stack
- Python 3.11
- aiogram 3 + FastAPI webhook
- PostgreSQL + Redis
- Docker Compose + Nginx

## Features
- RU/UZ language support
- Booking flow: service -> barber -> date -> slot -> confirm
- Booking constraints: from +1 hour to +14 days
- Cancellations allowed until 2 hours before start
- Reminder jobs (24h, 2h)
- Admin commands in Telegram
- Webhook secret verification
- Admin API secret for operational endpoints
- Update idempotency via Redis

## Quick start
1. Copy `.env.example` to `.env` and fill values.
2. Run:
   ```bash
   docker compose -f deploy/docker-compose.yml up --build
   ```
3. `api` configures webhook automatically if `WEBHOOK_URL` is set.
4. Optional manual sync: call `POST /telegram/webhook_sync` with `X-Admin-Api-Secret`.

## Main services
- `api`: FastAPI endpoint for Telegram webhook, health checks, and webhook ops
- `bot`: startup/housekeeping service
- `scheduler`: reminder processor
- `postgres`, `redis`, `nginx`

## API Endpoints
- `GET /healthz`
- `GET /readyz`
- `POST /telegram/webhook` (requires `X-Telegram-Bot-Api-Secret-Token`)
- `GET /telegram/webhook_info` (requires `X-Admin-Api-Secret`)
- `POST /telegram/webhook_sync` (requires `X-Admin-Api-Secret`)
- `POST /telegram/webhook_delete` (requires `X-Admin-Api-Secret`)

## Local tests
```bash
python -m pytest
```

## DB migration for existing Postgres
If your database was created before guest clients/hard-delete support, apply:
```bash
psql "$POSTGRES_DSN_SYNC" -f migrations/003_admin_guest_hard_delete.sql
```
