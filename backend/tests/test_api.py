"""
AIF369 Backend — Test Suite
Tests the Flask API endpoints, form validation, and BigQuery integration.
Run with: pytest tests/ -v
"""
import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Ensure backend module is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def app():
    """Create a test Flask app with mocked BigQuery client."""
    with patch("main.bigquery.Client") as mock_bq:
        mock_client = MagicMock()
        mock_client.insert_rows_json.return_value = []  # No errors
        mock_bq.return_value = mock_client

        from main import app as flask_app
        flask_app.config["TESTING"] = True
        yield flask_app


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


# ── Health check ──────────────────────────────────────────

class TestHealthCheck:
    def test_root_returns_ok(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
        assert data["service"] == "aif369-backend"


# ── Contact form ──────────────────────────────────────────

class TestContactForm:
    def test_valid_submission(self, client):
        payload = {
            "name": "Juan Pérez",
            "email": "juan@example.com",
            "company": "Startup XYZ",
            "message": "Necesito un diagnóstico express de IA."
        }
        response = client.post(
            "/api/contact",
            data=json.dumps(payload),
            content_type="application/json"
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "submission_id" in data

    def test_missing_name_returns_400(self, client):
        payload = {
            "email": "test@example.com",
            "message": "Hello"
        }
        response = client.post(
            "/api/contact",
            data=json.dumps(payload),
            content_type="application/json"
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "name" in data["error"]

    def test_missing_email_returns_400(self, client):
        payload = {
            "name": "Test User",
            "message": "Hello"
        }
        response = client.post(
            "/api/contact",
            data=json.dumps(payload),
            content_type="application/json"
        )
        assert response.status_code == 400

    def test_missing_message_returns_400(self, client):
        payload = {
            "name": "Test User",
            "email": "test@example.com"
        }
        response = client.post(
            "/api/contact",
            data=json.dumps(payload),
            content_type="application/json"
        )
        assert response.status_code == 400

    def test_wrong_content_type_returns_400(self, client):
        response = client.post(
            "/api/contact",
            data="not json",
            content_type="text/plain"
        )
        assert response.status_code == 400

    def test_form_type_is_captured(self, client):
        """Verify form_type field (diagnostico, education, etc.) is captured."""
        payload = {
            "name": "María López",
            "email": "maria@pyme.cl",
            "message": "Quiero el diagnóstico express",
            "form_type": "diagnostico",
            "interest": "diagnostico-express"
        }
        response = client.post(
            "/api/contact",
            data=json.dumps(payload),
            content_type="application/json"
        )
        assert response.status_code == 200

    def test_fullName_alias_works(self, client):
        """Frontend sends fullName instead of name."""
        payload = {
            "fullName": "Carlos Ruiz",
            "email": "carlos@corp.com",
            "context": "Necesito orientación en IA"
        }
        response = client.post(
            "/api/contact",
            data=json.dumps(payload),
            content_type="application/json"
        )
        assert response.status_code == 200


# ── Education form ────────────────────────────────────────

class TestEducationForm:
    def test_valid_education_submission(self, client):
        payload = {
            "name": "Ana Torres",
            "email": "ana@empresa.com",
            "company": "Empresa ABC",
            "interest": "curso-desarrollo-ia",
            "team_size": "6-15",
            "message": "Necesitamos formación para el equipo."
        }
        response = client.post(
            "/api/education",
            data=json.dumps(payload),
            content_type="application/json"
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

    def test_missing_interest_returns_400(self, client):
        payload = {
            "name": "Test",
            "email": "test@test.com",
            "company": "Test Co",
            "message": "Test message"
        }
        response = client.post(
            "/api/education",
            data=json.dumps(payload),
            content_type="application/json"
        )
        assert response.status_code == 400

    def test_missing_company_returns_400(self, client):
        payload = {
            "name": "Test",
            "email": "test@test.com",
            "interest": "coaching-equipos",
            "message": "Test"
        }
        response = client.post(
            "/api/education",
            data=json.dumps(payload),
            content_type="application/json"
        )
        assert response.status_code == 400


# ── BigQuery error handling ───────────────────────────────

class TestBigQueryErrors:
    def test_bq_insert_error_returns_500(self, client):
        """When BigQuery insert fails, return 500."""
        with patch("main.bq_client") as mock_bq:
            mock_bq.insert_rows_json.return_value = [{"errors": ["insert failed"]}]
            payload = {
                "name": "Test",
                "email": "test@test.com",
                "message": "Test"
            }
            response = client.post(
                "/api/contact",
                data=json.dumps(payload),
                content_type="application/json"
            )
            assert response.status_code == 500
