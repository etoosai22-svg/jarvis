"""auth_required=True일 때 보호 라우트가 실제로 막히는지 확인한다."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app


@pytest.fixture
def secured_client(client: TestClient):
    base = get_settings()
    secured = Settings(
        **{**base.model_dump(), "auth_required": True, "oauth_issuer_url": "https://issuer.example.com"}
    )
    app.dependency_overrides[get_settings] = lambda: secured
    yield client
    app.dependency_overrides.pop(get_settings, None)


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/v1/tasks"),
        ("get", "/api/v1/memory"),
    ],
)
def test_protected_routes_require_a_token(secured_client, method, path):
    response = getattr(secured_client, method)(path)
    assert response.status_code == 401


def test_invalid_token_is_rejected(secured_client):
    response = secured_client.get("/api/v1/tasks", headers={"Authorization": "Bearer not-a-jwt"})
    assert response.status_code == 401


def test_health_stays_public(secured_client):
    assert secured_client.get("/api/v1/health").status_code == 200
