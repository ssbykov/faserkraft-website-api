"""
tests/test_security.py
Запуск: pytest -q   (нужен pytest: poetry add --group dev pytest)
Тесты не требуют базы данных: проверяют маршрутизацию и настройки.
"""
import os

os.environ.setdefault("ENVIRONMENT", "production")
os.environ.setdefault("SECRET_KEY", "x" * 48)
os.environ.setdefault("POSTGRES_PASSWORD", "test-password-123")
os.environ.setdefault("CORS_ORIGINS", '["https://faserkraft.ru"]')

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
API = "/api/v1"
SAFE = {"GET", "HEAD", "OPTIONS"}


def test_only_lead_creation_is_writable():
    writable = []
    for path, operations in app.openapi()["paths"].items():
        if path.startswith(API):
            for method in operations:
                if method.upper() not in SAFE:
                    writable.append((path, method.upper()))
    assert writable == [(f"{API}/leads", "POST")], writable

def test_lead_route_is_registered():
    response = client.post(f"{API}/leads", json={})
    assert response.status_code == 422

@pytest.mark.parametrize(
    "method,path",
    [
        ("post", f"{API}/products"),
        ("patch", f"{API}/products/1"),
        ("delete", f"{API}/pages/1"),
        ("post", f"{API}/pages"),
        ("patch", f"{API}/leads/1/status"),
        ("get", f"{API}/leads"),
        ("post", f"{API}/auth/login"),
        ("get", f"{API}/auth/me"),
    ],
)
def test_write_and_auth_routes_are_gone(method, path):
    response = getattr(client, method)(path)
    assert response.status_code in (404, 405)


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
def test_docs_disabled_in_production(path):
    assert client.get(path).status_code == 404


def test_security_headers_present():
    response = client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"


def test_cors_rejects_foreign_origin():
    response = client.options(
        f"{API}/leads",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in response.headers


def test_oversized_body_rejected():
    response = client.post(f"{API}/leads", content=b"x" * 2_000_000)
    assert response.status_code == 413
