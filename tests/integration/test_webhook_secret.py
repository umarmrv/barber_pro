from fastapi.testclient import TestClient

from barber_bot.api.app import create_app
from barber_bot.config import get_settings


def _set_env(monkeypatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "123456:TEST_TOKEN")
    monkeypatch.setenv("WEBHOOK_SECRET", "expected-secret")
    monkeypatch.setenv("POSTGRES_DSN", "postgresql+asyncpg://barber:barber@localhost:5432/barber")
    monkeypatch.setenv("REDIS_DSN", "redis://localhost:6379/0")
    monkeypatch.setenv("SKIP_BOT_API_CALLS", "true")


def test_webhook_rejects_invalid_secret(monkeypatch) -> None:
    _set_env(monkeypatch)
    get_settings.cache_clear()

    app = create_app()
    with TestClient(app) as client:
        response = client.post(
            "/telegram/webhook",
            headers={"X-Telegram-Bot-Api-Secret-Token": "wrong-secret"},
            json={"update_id": 1},
        )

    assert response.status_code == 403
