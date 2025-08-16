import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Perfect PO API" in response.json()["message"]


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_docs_endpoint():
    """Test that the docs endpoint is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_redoc_endpoint():
    """Test that the redoc endpoint is accessible."""
    response = client.get("/redoc")
    assert response.status_code == 200


def test_auth_endpoints_exist():
    """Test that auth endpoints are registered."""
    response = client.get("/docs")
    assert response.status_code == 200
    # The docs should contain auth endpoints
    docs_content = response.text
    assert "/auth/register" in docs_content
    assert "/auth/login" in docs_content


def test_catalog_endpoints_exist():
    """Test that catalog endpoints are registered."""
    response = client.get("/docs")
    assert response.status_code == 200
    # The docs should contain catalog endpoints
    docs_content = response.text
    assert "/catalogs/upload" in docs_content
    assert "/catalogs/" in docs_content


