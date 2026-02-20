from fastapi.testclient import TestClient

from barber_bot.api.app import create_app
from barber_bot.config import get_settings


def _set_env(monkeypatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "123456:TEST_TOKEN")
    monkeypatch.setenv("WEBHOOK_SECRET", "webhook-secret")
    monkeypatch.setenv("ADMIN_API_SECRET", "admin-secret")
    monkeypatch.setenv("POSTGRES_DSN", "postgresql+asyncpg://barber:barber@localhost:5432/barber")
    monkeypatch.setenv("REDIS_DSN", "redis://localhost:6379/0")
    monkeypatch.setenv("SKIP_BOT_API_CALLS", "true")


def test_admin_endpoint_requires_admin_secret(monkeypatch) -> None:
    _set_env(monkeypatch)
    get_settings.cache_clear()

    app = create_app()
    with TestClient(app) as client:
        response = client.get("/telegram/webhook_info")

    assert response.status_code == 403


def test_admin_endpoint_uses_admin_secret_not_webhook_secret(monkeypatch) -> None:
    _set_env(monkeypatch)
    get_settings.cache_clear()

    app = create_app()
    with TestClient(app) as client:
        wrong = client.get(
            "/telegram/webhook_info",
            headers={"X-Admin-Api-Secret": "webhook-secret"},
        )
        right = client.get(
            "/telegram/webhook_info",
            headers={"X-Admin-Api-Secret": "admin-secret"},
        )

    assert wrong.status_code == 403
    assert right.status_code == 200
    assert right.json()["ok"] is True
    assert right.json()["skipped"] is True


def test_webhook_sync_and_delete_in_skip_mode(monkeypatch) -> None:
    _set_env(monkeypatch)
    get_settings.cache_clear()

    app = create_app()
    with TestClient(app) as client:
        sync_response = client.post(
            "/telegram/webhook_sync?drop_pending_updates=true",
            headers={"X-Admin-Api-Secret": "admin-secret"},
        )
        delete_response = client.post(
            "/telegram/webhook_delete",
            headers={"X-Admin-Api-Secret": "admin-secret"},
        )

    assert sync_response.status_code == 200
    assert sync_response.json()["ok"] is True
    assert sync_response.json()["skipped"] is True
    assert sync_response.json()["drop_pending_updates"] is True

    assert delete_response.status_code == 200
    assert delete_response.json()["ok"] is True
    assert delete_response.json()["skipped"] is True
