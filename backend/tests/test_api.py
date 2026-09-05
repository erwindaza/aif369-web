"""
AIF369 Backend — QA Test Suite
Tests ALL Flask API endpoints, form validation, BigQuery integration, and chat.
Run with: pytest tests/ -v
Run smoke against deployed: pytest tests/ -v -k smoke --deployed-url=https://...
"""
import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Ensure backend module is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Set test secrets before importing main (which reads os.getenv at import time)
os.environ.setdefault("CONTENT_API_KEY", "test-content-key-for-tests")
# Disable SMTP in tests to prevent real email sending
os.environ["SMTP_PASSWORD"] = ""
os.environ["AIF369_SKIP_STARTUP_BQ"] = "1"

# Test constant matching the env var above
TEST_CONTENT_API_KEY = os.environ["CONTENT_API_KEY"]


# ── Fixtures ──────────────────────────────────────────────

class _FakeFirestoreDoc:
    """Minimal stand-in for a Firestore DocumentReference, backed by a dict."""

    def __init__(self, store, key):
        self._store = store
        self._key = key

    def set(self, data):
        self._store[self._key] = dict(data)

    def get(self):
        data = self._store.get(self._key)
        snapshot = MagicMock()
        snapshot.exists = data is not None
        snapshot.to_dict.return_value = data
        return snapshot


class _FakeFirestoreCollection:
    def __init__(self, store):
        self._store = store

    def document(self, key):
        return _FakeFirestoreDoc(self._store, key)

    def stream(self):
        return iter(list(self._store.values()))


class _FakeFirestoreClient:
    """In-memory Firestore fake so revenue-access tests exercise real set/get round trips."""

    def __init__(self):
        self._collections = {}

    def collection(self, name):
        return _FakeFirestoreCollection(self._collections.setdefault(name, {}))


@pytest.fixture
def app():
    """Create a test Flask app with mocked BigQuery and Firestore clients."""
    with patch("main.bigquery.Client") as mock_bq, patch("main.firestore.Client") as mock_fs:
        mock_client = MagicMock()
        mock_client.insert_rows_json.return_value = []  # No errors
        mock_bq.return_value = mock_client
        mock_fs.return_value = _FakeFirestoreClient()

        # Reset the lazy clients so the mocks take effect
        import main
        main._bq_client = None
        main._firestore_client = None

        from main import app as flask_app
        flask_app.config["TESTING"] = True
        yield flask_app

        # Clean up: reset lazy clients after test
        main._bq_client = None
        main._firestore_client = None


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


def _post_json(client, url, payload, headers=None):
    """Helper: POST JSON to endpoint."""
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    return client.post(url, data=json.dumps(payload), headers=h)


# ══════════════════════════════════════════════════════════
# 1. HEALTH CHECK
# ══════════════════════════════════════════════════════════

class TestHealthCheck:
    def test_root_returns_ok(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
        assert data["service"] == "aif369-backend"

    def test_root_has_service_name(self, client):
        response = client.get("/")
        data = response.get_json()
        assert "service" in data


class TestRevenueEngine:
    @pytest.fixture(autouse=True)
    def configure_revenue_engine(self):
        import main
        main.PAYPAL_CLIENT_SECRET = "test-secret"
        main.PAYPAL_CLIENT_ID = "test-client"

    def test_products_catalog_is_public(self, client):
        response = client.get("/api/revenue/products")
        assert response.status_code == 200
        data = response.get_json()
        product_ids = {product["id"] for product in data["products"]}
        assert "engineering-with-ai-masterclass" in product_ids
        assert "private-ai-class" in product_ids

    def test_access_locked_without_completed_payment(self, client):
        response = _post_json(client, "/api/revenue/access", {
            "access_token": "no-such-token",
        })
        assert response.status_code == 200
        assert response.get_json()["access_status"] == "LOCKED"

    def test_format_paypal_amount_zero_decimal_currency(self):
        """CLP (and similar) must never carry decimals — PayPal rejects '24990.00'."""
        import main
        assert main._format_paypal_amount(24990, "CLP") == "24990"
        assert main._format_paypal_amount(39.9, "USD") == "39.90"

    @patch("main.http_requests.post")
    def test_create_order_uses_backend_price(self, mock_post, client):
        token_response = MagicMock()
        token_response.json.return_value = {"access_token": "token"}
        token_response.raise_for_status.return_value = None
        order_response = MagicMock()
        order_response.json.return_value = {"id": "ORDER-1", "status": "CREATED"}
        order_response.raise_for_status.return_value = None
        mock_post.side_effect = [token_response, order_response]

        response = _post_json(client, "/api/paypal/revenue/create-order", {
            "email": "student@example.com",
            "product_id": "engineering-with-ai-masterclass",
            "amount": 1,
        })

        assert response.status_code == 200
        order_payload = mock_post.call_args_list[1].kwargs["json"]
        amount = order_payload["purchase_units"][0]["amount"]
        assert amount == {"currency_code": "CLP", "value": "24990"}

    @patch("main.http_requests.post")
    def test_capture_denied_does_not_activate_access(self, mock_post, client):
        token_response = MagicMock()
        token_response.json.return_value = {"access_token": "token"}
        token_response.raise_for_status.return_value = None
        capture_response = MagicMock()
        capture_response.json.return_value = {"status": "DENIED", "purchase_units": []}
        capture_response.raise_for_status.return_value = None
        mock_post.side_effect = [token_response, capture_response]

        response = _post_json(client, "/api/paypal/revenue/capture-order", {
            "orderID": "ORDER-DENIED",
            "email": "student@example.com",
            "product_id": "engineering-with-ai-masterclass",
        })

        assert response.status_code == 400
        assert response.get_json()["access_status"] == "LOCKED"
        assert "access_token" not in response.get_json()

    @patch("main.http_requests.post")
    def test_capture_completed_activates_access(self, mock_post, client):
        token_response = MagicMock()
        token_response.json.return_value = {"access_token": "token"}
        token_response.raise_for_status.return_value = None
        capture_response = MagicMock()
        capture_response.json.return_value = {
            "status": "COMPLETED",
            "purchase_units": [{
                "payments": {
                    "captures": [{
                        "id": "CAPTURE-1",
                        "amount": {"currency_code": "CLP", "value": "24990"},
                    }]
                }
            }],
        }
        capture_response.raise_for_status.return_value = None
        mock_post.side_effect = [token_response, capture_response]

        response = _post_json(client, "/api/paypal/revenue/capture-order", {
            "orderID": "ORDER-OK",
            "email": "student@example.com",
            "product_id": "engineering-with-ai-masterclass",
        })

        assert response.status_code == 200
        result = response.get_json()
        assert result["access_status"] == "ACTIVE"
        access_token = result["access_token"]
        assert access_token

        access = _post_json(client, "/api/revenue/access", {
            "access_token": access_token,
        })
        assert access.get_json()["access_status"] == "ACTIVE"

    @patch("main.http_requests.post")
    def test_capture_completed_rejects_lookup_by_email_alone(self, mock_post, client):
        """Knowing the buyer's email must never be enough to see their access/payment status."""
        token_response = MagicMock()
        token_response.json.return_value = {"access_token": "token"}
        token_response.raise_for_status.return_value = None
        capture_response = MagicMock()
        capture_response.json.return_value = {
            "status": "COMPLETED",
            "purchase_units": [{
                "payments": {
                    "captures": [{
                        "id": "CAPTURE-2",
                        "amount": {"currency_code": "CLP", "value": "24990"},
                    }]
                }
            }],
        }
        capture_response.raise_for_status.return_value = None
        mock_post.side_effect = [token_response, capture_response]

        _post_json(client, "/api/paypal/revenue/capture-order", {
            "orderID": "ORDER-OK-2",
            "email": "student@example.com",
            "product_id": "engineering-with-ai-masterclass",
        })

        access = _post_json(client, "/api/revenue/access", {
            "email": "student@example.com",
            "product_id": "engineering-with-ai-masterclass",
        })
        assert access.get_json()["access_status"] == "LOCKED"

    @patch("main.http_requests.post")
    def test_capture_amount_mismatch_keeps_access_locked(self, mock_post, client):
        token_response = MagicMock()
        token_response.json.return_value = {"access_token": "token"}
        token_response.raise_for_status.return_value = None
        capture_response = MagicMock()
        capture_response.json.return_value = {
            "status": "COMPLETED",
            "purchase_units": [{
                "payments": {
                    "captures": [{
                        "id": "CAPTURE-LOW",
                        "amount": {"currency_code": "CLP", "value": "1"},
                    }]
                }
            }],
        }
        capture_response.raise_for_status.return_value = None
        mock_post.side_effect = [token_response, capture_response]

        response = _post_json(client, "/api/paypal/revenue/capture-order", {
            "orderID": "ORDER-LOW",
            "email": "student@example.com",
            "product_id": "engineering-with-ai-masterclass",
        })

        assert response.status_code == 409
        assert response.get_json()["access_status"] == "LOCKED"

    def test_student_enrollment_saved_to_bigquery(self, client):
        response = _post_json(client, "/api/student-enrollments", {
            "product_id": "engineering-with-ai-masterclass",
            "full_name": "Test Student",
            "email": "student@example.com",
        })
        assert response.status_code == 201
        assert response.get_json()["success"] is True

    def test_student_enrollment_bq_failure_returns_503(self, client):
        with patch("main.get_bq_client") as mock_get_bq:
            mock_bq = MagicMock()
            mock_get_bq.return_value = mock_bq
            mock_bq.insert_rows_json.side_effect = Exception("BQ unavailable")
            response = _post_json(client, "/api/student-enrollments", {
                "product_id": "engineering-with-ai-masterclass",
                "full_name": "Test Student",
                "email": "student@example.com",
            })
            assert response.status_code == 503

    def test_admin_revenue_requires_api_key(self, client):
        response = client.get("/api/admin/revenue")
        assert response.status_code == 401

    def test_admin_revenue_sums_completed_captures(self, client):
        with patch("main.get_bq_client") as mock_get_bq:
            mock_bq = MagicMock()
            mock_get_bq.return_value = mock_bq
            mock_bq.query.return_value.result.return_value = [
                {
                    "event_type": "paypal_capture_completed",
                    "payload": json.dumps({"amount": 39.0, "product_id": "engineering-with-ai-masterclass"}),
                    "created_at": "2026-01-01T00:00:00+00:00",
                },
                {
                    "event_type": "paypal_order_created",
                    "payload": json.dumps({"amount": 39.0, "product_id": "engineering-with-ai-masterclass"}),
                    "created_at": "2026-01-01T00:00:00+00:00",
                },
            ]
            response = client.get("/api/admin/revenue", headers={"X-API-Key": TEST_CONTENT_API_KEY})
            assert response.status_code == 200
            data = response.get_json()
            assert data["gross_revenue"] == 39.0
            assert data["payments_count"] == 1
            assert len(data["recent_events"]) == 2


# ══════════════════════════════════════════════════════════
# 2. CONTACT FORM  /api/contact
# ══════════════════════════════════════════════════════════

class TestContactForm:
    def test_valid_submission(self, client):
        payload = {
            "name": "Juan Pérez",
            "email": "juan@example.com",
            "company": "Startup XYZ",
            "message": "Necesito un diagnóstico express de IA."
        }
        response = _post_json(client, "/api/contact", payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "submission_id" in data

    def test_missing_name_returns_400(self, client):
        payload = {"email": "test@example.com", "message": "Hello"}
        response = _post_json(client, "/api/contact", payload)
        assert response.status_code == 400
        data = response.get_json()
        assert "name" in data["error"]

    def test_missing_email_returns_400(self, client):
        payload = {"name": "Test User", "message": "Hello"}
        response = _post_json(client, "/api/contact", payload)
        assert response.status_code == 400

    def test_missing_message_returns_400(self, client):
        payload = {"name": "Test User", "email": "test@example.com"}
        response = _post_json(client, "/api/contact", payload)
        assert response.status_code == 400

    def test_wrong_content_type_returns_400(self, client):
        response = client.post(
            "/api/contact", data="not json", content_type="text/plain"
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
        response = _post_json(client, "/api/contact", payload)
        assert response.status_code == 200

    def test_fullName_alias_works(self, client):
        """Frontend sends fullName instead of name."""
        payload = {
            "fullName": "Carlos Ruiz",
            "email": "carlos@corp.com",
            "context": "Necesito orientación en IA"
        }
        response = _post_json(client, "/api/contact", payload)
        assert response.status_code == 200

    def test_empty_body_returns_400(self, client):
        response = _post_json(client, "/api/contact", {})
        assert response.status_code == 400


# ══════════════════════════════════════════════════════════
# 3. EDUCATION FORM  /api/education
# ══════════════════════════════════════════════════════════

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
        response = _post_json(client, "/api/education", payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

    def test_missing_interest_returns_400(self, client):
        payload = {
            "name": "Test", "email": "test@test.com",
            "company": "Test Co", "message": "Test message"
        }
        response = _post_json(client, "/api/education", payload)
        assert response.status_code == 400

    def test_missing_company_returns_400(self, client):
        payload = {
            "name": "Test", "email": "test@test.com",
            "interest": "coaching-equipos", "message": "Test"
        }
        response = _post_json(client, "/api/education", payload)
        assert response.status_code == 400


# ══════════════════════════════════════════════════════════
# 4. SCORECARD  /api/scorecard
# ══════════════════════════════════════════════════════════

class TestScorecard:
    @pytest.fixture
    def valid_scorecard_payload(self):
        return {
            "name": "Pablo Rivas",
            "email": "pablo@corp.cl",
            "company": "Corp Chile",
            "role": "CTO",
            "total_score": 72,
            "maturity_level": "Integrado",
            "maturity_number": 4,
            "dimensions": {
                "estrategia": {"name": "Estrategia IA", "pct": 80},
                "gobierno": {"name": "Gobierno IA", "pct": 60},
                "riesgos": {"name": "Gestión de Riesgos", "pct": 75}
            },
            "answers": [
                {"question": "q1", "answer": 4},
                {"question": "q2", "answer": 3},
                {"question": "q3", "answer": 5}
            ]
        }

    def test_valid_scorecard_submission(self, client, valid_scorecard_payload):
        response = _post_json(client, "/api/scorecard", valid_scorecard_payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "submission_id" in data

    def test_scorecard_missing_name_returns_400(self, client, valid_scorecard_payload):
        del valid_scorecard_payload["name"]
        response = _post_json(client, "/api/scorecard", valid_scorecard_payload)
        assert response.status_code == 400

    def test_scorecard_missing_email_returns_400(self, client, valid_scorecard_payload):
        del valid_scorecard_payload["email"]
        response = _post_json(client, "/api/scorecard", valid_scorecard_payload)
        assert response.status_code == 400

    def test_scorecard_empty_name_returns_400(self, client, valid_scorecard_payload):
        valid_scorecard_payload["name"] = ""
        response = _post_json(client, "/api/scorecard", valid_scorecard_payload)
        assert response.status_code == 400

    def test_scorecard_wrong_content_type(self, client):
        response = client.post(
            "/api/scorecard", data="not json", content_type="text/plain"
        )
        assert response.status_code == 400

    def test_scorecard_bq_fallback(self, client, valid_scorecard_payload):
        """When scorecard table insert fails, it falls back to contact table."""
        with patch("main.get_bq_client") as mock_get_bq:
            mock_bq = MagicMock()
            mock_get_bq.return_value = mock_bq
            # First call fails (scorecard table), second succeeds (contact table)
            mock_bq.insert_rows_json.side_effect = [
                [{"errors": ["table not found"]}],
                []
            ]
            response = _post_json(client, "/api/scorecard", valid_scorecard_payload)
            assert response.status_code == 200


# ══════════════════════════════════════════════════════════
# 5. CHAT  /api/chat
# ══════════════════════════════════════════════════════════

class TestChat:
    # All chat requests must include a trusted Origin header (security gate added in 17f190b).
    TRUSTED_ORIGIN = {"Origin": "https://aif369.com"}

    def test_chat_valid_message_gemini(self, client):
        """Chat with mocked Gemini returns 200 and a response."""
        with patch("main.GEMINI_API_KEY", "test-key"), \
             patch("main.genai") as mock_genai:
            mock_model = MagicMock()
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "AIF369 ofrece servicios de consultoría en IA."
            mock_session.send_message.return_value = mock_response
            mock_model.start_chat.return_value = mock_session
            mock_genai.GenerativeModel.return_value = mock_model

            response = _post_json(client, "/api/chat", {"message": "Hola"},
                                  headers=self.TRUSTED_ORIGIN)
            assert response.status_code == 200
            data = response.get_json()
            assert data["success"] is True
            assert data["provider"] == "gemini"
            assert "response" in data
            assert "session_id" in data

    def test_chat_blocked_without_origin(self, client):
        """Chat without Origin header must be blocked with 403."""
        response = _post_json(client, "/api/chat", {"message": "Hola"})
        assert response.status_code == 403

    def test_chat_empty_message_returns_400(self, client):
        response = _post_json(client, "/api/chat", {"message": ""},
                              headers=self.TRUSTED_ORIGIN)
        assert response.status_code == 400

    def test_chat_missing_message_returns_400(self, client):
        response = _post_json(client, "/api/chat", {},
                              headers=self.TRUSTED_ORIGIN)
        assert response.status_code == 400

    def test_chat_wrong_content_type(self, client):
        response = client.post(
            "/api/chat", data="not json", content_type="text/plain",
            headers=self.TRUSTED_ORIGIN
        )
        assert response.status_code == 400

    def test_chat_with_history(self, client):
        """Chat with conversation history."""
        with patch("main.GEMINI_API_KEY", "test-key"), \
             patch("main.genai") as mock_genai:
            mock_model = MagicMock()
            mock_session = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "El Método 369 tiene 3 capas."
            mock_session.send_message.return_value = mock_response
            mock_model.start_chat.return_value = mock_session
            mock_genai.GenerativeModel.return_value = mock_model

            payload = {
                "message": "Cuéntame del Método 369",
                "history": [
                    {"role": "user", "content": "Hola"},
                    {"role": "assistant", "content": "Hola, soy AIF369 Assistant."}
                ],
                "session_id": "test-session-123",
                "turn_number": 2
            }
            response = _post_json(client, "/api/chat", payload,
                                  headers=self.TRUSTED_ORIGIN)
            assert response.status_code == 200
            data = response.get_json()
            assert data["session_id"] == "test-session-123"

    def test_chat_gemini_failure_fallback_message(self, client):
        """When both Gemini and Ollama fail, returns fallback message."""
        with patch("main.GEMINI_API_KEY", "test-key"), \
             patch("main.genai") as mock_genai, \
             patch("main.http_requests") as mock_requests:
            mock_model = MagicMock()
            mock_session = MagicMock()
            mock_session.send_message.side_effect = Exception("API error")
            mock_model.start_chat.return_value = mock_session
            mock_genai.GenerativeModel.return_value = mock_model
            mock_requests.post.side_effect = Exception("Connection refused")

            response = _post_json(client, "/api/chat", {"message": "Hola"},
                                  headers=self.TRUSTED_ORIGIN)
            assert response.status_code == 200
            data = response.get_json()
            assert data["success"] is False
            assert "WhatsApp" in data["response"]

    def test_chat_no_api_key_returns_fallback(self, client):
        """Without GEMINI_API_KEY, falls back to Ollama then fallback message."""
        with patch("main.GEMINI_API_KEY", None), \
             patch("main.http_requests") as mock_requests:
            mock_requests.post.side_effect = Exception("Connection refused")

            response = _post_json(client, "/api/chat", {"message": "Hola"},
                                  headers=self.TRUSTED_ORIGIN)
            assert response.status_code == 200
            data = response.get_json()
            assert data["success"] is False


# ══════════════════════════════════════════════════════════
# 6. CONTENT GENERATION  /api/generate-content
# ══════════════════════════════════════════════════════════

class TestGenerateContent:
    def test_unauthorized_without_api_key(self, client):
        response = _post_json(
            client, "/api/generate-content",
            {"topic": "IA en Chile"}
        )
        assert response.status_code == 401

    def test_unauthorized_wrong_api_key(self, client):
        response = _post_json(
            client, "/api/generate-content",
            {"topic": "IA en Chile"},
            headers={"X-API-Key": "wrong-key"}
        )
        assert response.status_code == 401

    def test_valid_content_generation(self, client):
        """With correct API key and mocked Gemini, returns content."""
        with patch("main.GEMINI_API_KEY", "test-key"), \
             patch("main.genai") as mock_genai:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "<h1>Artículo sobre IA</h1><p>Contenido...</p>"
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model

            response = _post_json(
                client, "/api/generate-content",
                {"topic": "ROI de IA", "target": "CEO"},
                headers={"X-API-Key": TEST_CONTENT_API_KEY}
            )
            assert response.status_code == 200
            data = response.get_json()
            assert data["success"] is True
            assert "content" in data

    def test_missing_topic_returns_400(self, client):
        response = _post_json(
            client, "/api/generate-content",
            {"angle": "algo"},
            headers={"X-API-Key": TEST_CONTENT_API_KEY}
        )
        assert response.status_code == 400

    def test_wrong_content_type(self, client):
        response = client.post(
            "/api/generate-content",
            data="not json",
            content_type="text/plain",
            headers={"X-API-Key": TEST_CONTENT_API_KEY}
        )
        assert response.status_code == 400


# ══════════════════════════════════════════════════════════
# 7. CONTENT TOPICS  /api/content-topics
# ══════════════════════════════════════════════════════════

class TestContentTopics:
    def test_unauthorized_without_api_key(self, client):
        response = client.get("/api/content-topics")
        assert response.status_code == 401

    def test_valid_topics_list(self, client):
        response = client.get(
            "/api/content-topics",
            headers={"X-API-Key": TEST_CONTENT_API_KEY}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "topics" in data
        assert data["count"] > 0
        assert len(data["topics"]) == data["count"]
        for topic in data["topics"]:
            assert "topic" in topic
            assert "category" in topic
            assert "target" in topic


# ══════════════════════════════════════════════════════════
# 8. BIGQUERY ERROR HANDLING
# ══════════════════════════════════════════════════════════

class TestBigQueryErrors:
    def test_bq_insert_error_is_non_fatal(self, client):
        """When BigQuery insert fails, form still succeeds (BQ is analytics, not critical)."""
        with patch("main.get_bq_client") as mock_get_bq:
            mock_bq = MagicMock()
            mock_get_bq.return_value = mock_bq
            mock_bq.insert_rows_json.return_value = [{"errors": ["insert failed"]}]
            payload = {
                "name": "Test",
                "email": "test@test.com",
                "message": "Test"
            }
            response = _post_json(client, "/api/contact", payload)
            assert response.status_code == 200
            data = response.get_json()
            assert data["success"] is True


# ══════════════════════════════════════════════════════════
# 9. CORS HEADERS
# ══════════════════════════════════════════════════════════

class TestCORS:
    def test_allowed_origin_aif369(self, client):
        response = client.get("/", headers={"Origin": "https://aif369.com"})
        assert response.status_code == 200
        assert response.headers.get("Access-Control-Allow-Origin") in [
            "https://aif369.com", "*"
        ]

    def test_options_preflight(self, client):
        response = client.options(
            "/api/chat",
            headers={
                "Origin": "https://aif369.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        assert response.status_code == 200


# ══════════════════════════════════════════════════════════
# 10. SMOKE TESTS (against deployed service)
# ══════════════════════════════════════════════════════════

class TestSmoke:
    """
    Run against a deployed instance:
      pytest tests/ -v -k smoke --deployed-url=https://aif369-backend-api-dev-830685315001.us-central1.run.app
    """

    @pytest.fixture(autouse=True)
    def _skip_if_no_url(self, deployed_url):
        if deployed_url is None:
            pytest.skip("--deployed-url not provided")
        self.base_url = deployed_url

    def _post(self, path, payload):
        import requests
        return requests.post(
            f"{self.base_url}{path}",
            json=payload,
            headers={"Origin": "https://aif369.com"},
            timeout=30
        )

    def _get(self, path, headers=None):
        import requests
        h = {"Origin": "https://aif369.com"}
        if headers:
            h.update(headers)
        return requests.get(f"{self.base_url}{path}", headers=h, timeout=15)

    def test_smoke_health(self):
        resp = self._get("/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_smoke_contact_validation(self):
        resp = self._post("/api/contact", {})
        assert resp.status_code == 400

    def test_smoke_education_validation(self):
        resp = self._post("/api/education", {})
        assert resp.status_code == 400

    def test_smoke_scorecard_validation(self):
        resp = self._post("/api/scorecard", {"name": "", "email": ""})
        assert resp.status_code == 400

    def test_smoke_chat_returns_200(self):
        resp = self._post("/api/chat", {"message": "Hola"})
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert "session_id" in data

    def test_smoke_chat_empty_message_400(self):
        resp = self._post("/api/chat", {"message": ""})
        assert resp.status_code == 400

    def test_smoke_content_topics_requires_auth(self):
        resp = self._get("/api/content-topics")
        assert resp.status_code == 401

    def test_smoke_generate_content_requires_auth(self):
        resp = self._post("/api/generate-content", {"topic": "test"})
        assert resp.status_code == 401
