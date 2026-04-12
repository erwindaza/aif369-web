#!/usr/bin/env python3
"""
AIF369 — Agente de QA Automatizado
===================================
Ejecuta una batería completa de pruebas contra el entorno desplegado.
Cubre: backend API, frontend pages, formularios, precios, SEO, seguridad.

Uso:
  python qa_agent.py                          # Test QA (default)
  python qa_agent.py --env=prod               # Test producción
  python qa_agent.py --env=dev                # Test desarrollo
  python qa_agent.py --env=prod --fix-report  # Genera reporte con issues

Salida: PASS/FAIL con detalle y reporte final.
"""

import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    print("❌ Falta 'requests'. Instala con: pip install requests")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════
# CONFIGURACIÓN POR ENTORNO
# ═══════════════════════════════════════════════════════════
ENVS = {
    "dev": {
        "backend": "https://aif369-backend-api-dev-830685315001.us-central1.run.app",
        "frontend": None,  # Vercel preview — set manually if needed
    },
    "qa": {
        "backend": "https://aif369-backend-api-qa-830685315001.us-central1.run.app",
        "frontend": None,  # Vercel preview for qa
    },
    "prod": {
        "backend": "https://aif369-backend-api-830685315001.us-central1.run.app",
        "frontend": "https://aif369.com",
    },
}

# Pages to check (relative to frontend URL)
PAGES = [
    ("index.html", "AIF369"),
    ("services.html", "Servicios"),
    ("education.html", "Cursos"),
    ("scorecard.html", "Scorecard"),
    ("blog.html", "Blog"),
    ("metodologia.html", "369"),
    ("encuentra-empleo.html", "empleo"),
    ("coaching-data.html", "Coaching"),
    ("cursos-ia.html", "Inteligencia Artificial"),
    ("big-data-ia.html", "Big Data"),
    ("automatizacion-airflow.html", "Airflow"),
    ("airflow-ia-avanzada.html", "Avanzada"),
    ("course-desarrollo-ia.html", "Desarrollo"),
    ("course-guias-practicas.html", "Guías"),
    ("course-material-caio.html", "CAIO"),
    ("author.html", "Erwin"),
    ("cost-dashboard.html", "Cost"),
]

# ═══════════════════════════════════════════════════════════
# RESULTADO DE TEST
# ═══════════════════════════════════════════════════════════
@dataclass
class TestResult:
    category: str
    name: str
    passed: bool
    detail: str = ""
    severity: str = "medium"  # critical, high, medium, low


@dataclass
class QAReport:
    env: str
    timestamp: str = ""
    results: list = field(default_factory=list)
    duration_s: float = 0

    @property
    def passed(self):
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self):
        return sum(1 for r in self.results if not r.passed)

    @property
    def critical_failures(self):
        return [r for r in self.results if not r.passed and r.severity == "critical"]

    def summary(self):
        total = len(self.results)
        lines = [
            "",
            "═" * 60,
            f"  AIF369 QA Report — {self.env.upper()}",
            f"  {self.timestamp}  ({self.duration_s:.1f}s)",
            "═" * 60,
            f"  Total: {total}  |  ✅ Passed: {self.passed}  |  ❌ Failed: {self.failed}",
        ]
        if self.critical_failures:
            lines.append(f"  🚨 CRITICAL FAILURES: {len(self.critical_failures)}")
        lines.append("═" * 60)

        if self.failed > 0:
            lines.append("\n  FAILURES:")
            for r in self.results:
                if not r.passed:
                    sev = {"critical": "🚨", "high": "🔴", "medium": "🟡", "low": "⚪"}.get(r.severity, "⚪")
                    lines.append(f"    {sev} [{r.category}] {r.name}")
                    if r.detail:
                        lines.append(f"       → {r.detail}")
            lines.append("")

        if self.failed == 0:
            lines.append("\n  ✅ ALL TESTS PASSED — Ready for promotion!")
        elif self.critical_failures:
            lines.append("\n  🚨 BLOCKED — Fix critical issues before promoting.")
        else:
            lines.append("\n  ⚠️  Non-critical issues found. Review before promoting.")

        lines.append("═" * 60)
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
# TEST FUNCTIONS
# ═══════════════════════════════════════════════════════════

def test_backend_health(base: str) -> list[TestResult]:
    """Test backend health endpoint."""
    results = []
    try:
        r = requests.get(f"{base}/", timeout=15)
        data = r.json()
        results.append(TestResult(
            "Backend", "Health check",
            r.status_code == 200 and data.get("status") == "ok",
            f"HTTP {r.status_code}, status={data.get('status')}",
            severity="critical"
        ))
        results.append(TestResult(
            "Backend", "CORS header present",
            "access-control-allow-origin" in {k.lower() for k in r.headers},
            f"Headers: {dict(r.headers)}",
            severity="high"
        ))
    except Exception as e:
        results.append(TestResult("Backend", "Health check", False, str(e), "critical"))
    return results


def test_backend_contact_form(base: str) -> list[TestResult]:
    """Test contact form validation and submission."""
    results = []
    headers = {"Content-Type": "application/json", "Origin": "https://aif369.com"}

    # Test validation — missing fields should return 400
    r = requests.post(f"{base}/api/contact", json={}, headers=headers, timeout=15)
    results.append(TestResult(
        "Contact Form", "Rejects empty payload",
        r.status_code == 400,
        f"HTTP {r.status_code}",
        severity="high"
    ))

    # Test valid submission
    payload = {
        "name": "QA Bot Test",
        "email": "qa-bot@aif369.com",
        "company": "AIF369 QA",
        "role": "QA Agent",
        "message": "Automated QA test — please ignore.",
        "form_type": "qa_test",
        "source_page": "qa_agent.py"
    }
    r = requests.post(f"{base}/api/contact", json=payload, headers=headers, timeout=30)
    data = r.json() if r.status_code == 200 else {}
    results.append(TestResult(
        "Contact Form", "Valid submission returns 200",
        r.status_code == 200 and data.get("success") is True,
        f"HTTP {r.status_code}, response={json.dumps(data)[:200]}",
        severity="critical"
    ))

    return results


def test_backend_scorecard(base: str) -> list[TestResult]:
    """Test scorecard endpoint."""
    results = []
    headers = {"Content-Type": "application/json", "Origin": "https://aif369.com"}

    # Validation
    r = requests.post(f"{base}/api/scorecard", json={"name": "", "email": ""}, headers=headers, timeout=15)
    results.append(TestResult(
        "Scorecard", "Rejects empty name/email",
        r.status_code == 400,
        f"HTTP {r.status_code}",
        severity="high"
    ))

    # Valid scorecard submission
    payload = {
        "name": "QA Bot",
        "email": "qa-bot@aif369.com",
        "company": "QA Corp",
        "role": "QA Tester",
        "total_score": 55,
        "maturity_level": "Definido",
        "maturity_number": 3,
        "metrics": {
            "1": {"name": "Estrategia IA", "pct": 60, "score": 3},
            "2": {"name": "Gobierno IA", "pct": 40, "score": 2},
        },
        "answers": [{"question": "test", "score": 3}],
        "source_page": "qa_agent.py"
    }
    r = requests.post(f"{base}/api/scorecard", json=payload, headers=headers, timeout=30)
    data = r.json() if r.status_code == 200 else {}
    results.append(TestResult(
        "Scorecard", "Valid submission with metrics",
        r.status_code == 200 and data.get("success") is True,
        f"HTTP {r.status_code}",
        severity="critical"
    ))

    return results


def test_backend_chat(base: str) -> list[TestResult]:
    """Test chat endpoint (Gemini/Ollama)."""
    results = []
    headers = {"Content-Type": "application/json", "Origin": "https://aif369.com"}

    # Valid chat message
    r = requests.post(f"{base}/api/chat", json={"message": "Hola, qué servicios ofrecen?"}, headers=headers, timeout=45)
    data = r.json() if r.status_code == 200 else {}
    results.append(TestResult(
        "Chat", "Returns response to valid message",
        r.status_code == 200 and "response" in data,
        f"HTTP {r.status_code}, has_response={'response' in data}",
        severity="high"
    ))

    # Empty message should fail
    r = requests.post(f"{base}/api/chat", json={"message": ""}, headers=headers, timeout=15)
    results.append(TestResult(
        "Chat", "Rejects empty message",
        r.status_code == 400,
        f"HTTP {r.status_code}",
        severity="medium"
    ))

    return results


def test_backend_paypal_config(base: str) -> list[TestResult]:
    """Test PayPal config endpoint returns client_id without exposing secrets."""
    results = []
    try:
        r = requests.get(f"{base}/api/config/paypal", headers={"Origin": "https://aif369.com"}, timeout=15)
        data = r.json() if r.status_code == 200 else {}
        has_client_id = bool(data.get("client_id"))
        results.append(TestResult(
            "PayPal", "Config returns client_id",
            r.status_code == 200 and has_client_id,
            f"HTTP {r.status_code}, has_client_id={has_client_id}",
            severity="critical"
        ))
        # Ensure no secret key is leaked
        resp_text = json.dumps(data)
        no_secret_leak = "secret" not in resp_text.lower() and "password" not in resp_text.lower()
        results.append(TestResult(
            "Security", "PayPal config does not leak secrets",
            no_secret_leak,
            "Checked for secret/password in response",
            severity="critical"
        ))
    except Exception as e:
        results.append(TestResult("PayPal", "Config endpoint", False, str(e), "critical"))
    return results


def test_backend_education(base: str) -> list[TestResult]:
    """Test education enrollment endpoint."""
    results = []
    headers = {"Content-Type": "application/json", "Origin": "https://aif369.com"}

    r = requests.post(f"{base}/api/education", json={}, headers=headers, timeout=15)
    results.append(TestResult(
        "Education", "Rejects empty payload",
        r.status_code == 400,
        f"HTTP {r.status_code}",
        severity="high"
    ))

    return results


def test_backend_content_auth(base: str) -> list[TestResult]:
    """Test content API requires authentication."""
    results = []
    r = requests.get(f"{base}/api/content-topics", timeout=15)
    results.append(TestResult(
        "Security", "Content topics requires auth",
        r.status_code == 401,
        f"HTTP {r.status_code}",
        severity="high"
    ))
    return results


def test_frontend_pages(frontend_url: str) -> list[TestResult]:
    """Test all frontend pages load correctly."""
    results = []
    if not frontend_url:
        results.append(TestResult("Frontend", "URL not configured", False, "Set frontend URL", "low"))
        return results

    def check_page(page_path, expected_text):
        url = urljoin(frontend_url + "/", page_path)
        try:
            r = requests.get(url, timeout=15)
            has_text = expected_text.lower() in r.text.lower() if r.status_code == 200 else False
            return TestResult(
                "Frontend", f"Page loads: {page_path}",
                r.status_code == 200 and has_text,
                f"HTTP {r.status_code}, contains '{expected_text}': {has_text}",
                severity="critical" if page_path in ("index.html", "scorecard.html", "education.html") else "medium"
            )
        except Exception as e:
            return TestResult("Frontend", f"Page loads: {page_path}", False, str(e), "critical")

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(check_page, p, t): p for p, t in PAGES}
        for f in as_completed(futures):
            results.append(f.result())

    return results


def test_frontend_pricing(frontend_url: str) -> list[TestResult]:
    """Verify pricing is consistent ($10 USD, no Black Week)."""
    results = []
    if not frontend_url:
        return results

    course_pages = [
        "cursos-ia.html", "big-data-ia.html", "automatizacion-airflow.html",
        "airflow-ia-avanzada.html", "course-desarrollo-ia.html",
        "course-guias-practicas.html", "course-material-caio.html",
    ]

    for page in course_pages:
        try:
            r = requests.get(urljoin(frontend_url + "/", page), timeout=15)
            text = r.text
            has_10_usd = "$10" in text or "USD $10" in text or "USD&nbsp;$10" in text
            no_black_week = "black week" not in text.lower()
            no_old_price = "$500" not in text and "$3,000" not in text and "$3.000" not in text

            results.append(TestResult(
                "Pricing", f"Price $10 on {page}",
                has_10_usd,
                f"Found $10: {has_10_usd}",
                severity="critical"
            ))
            results.append(TestResult(
                "Pricing", f"No Black Week on {page}",
                no_black_week and no_old_price,
                f"No BW: {no_black_week}, No old prices: {no_old_price}",
                severity="critical"
            ))
        except Exception as e:
            results.append(TestResult("Pricing", f"Check {page}", False, str(e), "high"))

    return results


def test_frontend_enrollment_forms(frontend_url: str) -> list[TestResult]:
    """Verify all 7 course pages have enrollment forms."""
    results = []
    if not frontend_url:
        return results

    course_pages = [
        "cursos-ia.html", "big-data-ia.html", "automatizacion-airflow.html",
        "airflow-ia-avanzada.html", "course-desarrollo-ia.html",
        "course-guias-practicas.html", "course-material-caio.html",
    ]

    for page in course_pages:
        try:
            r = requests.get(urljoin(frontend_url + "/", page), timeout=15)
            has_form = "enrollment-wrapper" in r.text
            has_paypal = "paypal-btn-container" in r.text
            results.append(TestResult(
                "Enrollment", f"Form present on {page}",
                has_form and has_paypal,
                f"Has form: {has_form}, Has PayPal: {has_paypal}",
                severity="critical"
            ))
        except Exception as e:
            results.append(TestResult("Enrollment", f"Check {page}", False, str(e), "high"))

    return results


def test_frontend_seo(frontend_url: str) -> list[TestResult]:
    """Check OpenGraph meta tags on key pages."""
    results = []
    if not frontend_url:
        return results

    key_pages = ["index.html", "education.html", "services.html", "blog.html", "scorecard.html"]
    for page in key_pages:
        try:
            r = requests.get(urljoin(frontend_url + "/", page), timeout=15)
            has_og = 'og:title' in r.text
            has_canonical = 'rel="canonical"' in r.text
            results.append(TestResult(
                "SEO", f"OG tags on {page}",
                has_og and has_canonical,
                f"OG: {has_og}, Canonical: {has_canonical}",
                severity="medium"
            ))
        except Exception as e:
            results.append(TestResult("SEO", f"Check {page}", False, str(e), "low"))

    return results


def test_frontend_security(frontend_url: str) -> list[TestResult]:
    """Check no hardcoded secrets or XSS vectors in frontend."""
    results = []
    if not frontend_url:
        return results

    # Check scripts.js for hardcoded keys
    try:
        r = requests.get(urljoin(frontend_url + "/", "scripts.js"), timeout=15)
        text = r.text
        no_paypal_key = "AQ68vCh" not in text  # sandbox key fragment
        no_hardcoded_secret = "secret" not in text.lower() or "secretmanager" in text.lower()
        results.append(TestResult(
            "Security", "No hardcoded PayPal key in scripts.js",
            no_paypal_key,
            f"PayPal key absent: {no_paypal_key}",
            severity="critical"
        ))

        # Check no innerHTML in job rendering (XSS fix)
        no_innerhtml_jobs = "card.innerHTML" not in text
        results.append(TestResult(
            "Security", "No innerHTML XSS in job board",
            no_innerhtml_jobs,
            f"innerHTML absent: {no_innerhtml_jobs}",
            severity="high"
        ))

        # Check backend URLs are consistent
        wrong_project = "944757324945" in text
        results.append(TestResult(
            "Config", "No wrong project ID in scripts.js",
            not wrong_project,
            f"Wrong ID absent: {not wrong_project}",
            severity="critical"
        ))
    except Exception as e:
        results.append(TestResult("Security", "Check scripts.js", False, str(e), "high"))

    return results


def test_frontend_chat_widget(frontend_url: str) -> list[TestResult]:
    """Check chat widget has updated pricing."""
    results = []
    if not frontend_url:
        return results

    try:
        r = requests.get(urljoin(frontend_url + "/", "chat-widget.js"), timeout=15)
        text = r.text
        no_black_week = "BLACK WEEK" not in text
        no_old_price = "$3,000" not in text and "$500" not in text
        has_10 = "$10" in text
        results.append(TestResult(
            "Chat Widget", "No Black Week pricing",
            no_black_week and no_old_price,
            f"No BW: {no_black_week}, No $500/$3k: {no_old_price}",
            severity="critical"
        ))
        results.append(TestResult(
            "Chat Widget", "Has $10 pricing",
            has_10,
            f"$10 found: {has_10}",
            severity="high"
        ))
    except Exception as e:
        results.append(TestResult("Chat Widget", "Check pricing", False, str(e), "high"))

    return results


# ═══════════════════════════════════════════════════════════
# MAIN RUNNER
# ═══════════════════════════════════════════════════════════

def run_qa(env_name: str, fix_report: bool = False) -> QAReport:
    env = ENVS.get(env_name)
    if not env:
        print(f"❌ Unknown environment: {env_name}. Use: dev, qa, prod")
        sys.exit(1)

    backend_url = env["backend"]
    frontend_url = env.get("frontend")

    report = QAReport(env=env_name, timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    start = time.time()

    print(f"\n🤖 AIF369 QA Agent — Testing {env_name.upper()}")
    print(f"   Backend:  {backend_url}")
    print(f"   Frontend: {frontend_url or '(not configured)'}")
    print("─" * 60)

    # Backend tests
    test_groups = [
        ("Backend Health", test_backend_health, backend_url),
        ("Contact Form", test_backend_contact_form, backend_url),
        ("Scorecard", test_backend_scorecard, backend_url),
        ("Chat", test_backend_chat, backend_url),
        ("PayPal Config", test_backend_paypal_config, backend_url),
        ("Education", test_backend_education, backend_url),
        ("Content Auth", test_backend_content_auth, backend_url),
    ]

    for group_name, test_fn, url in test_groups:
        print(f"\n  📋 {group_name}...")
        try:
            group_results = test_fn(url)
            for r in group_results:
                icon = "✅" if r.passed else "❌"
                print(f"    {icon} {r.name}")
                report.results.append(r)
        except Exception as e:
            print(f"    ❌ {group_name} crashed: {e}")
            report.results.append(TestResult(group_name, "Test execution", False, str(e), "critical"))

    # Frontend tests (if URL available)
    if frontend_url:
        frontend_groups = [
            ("Frontend Pages", test_frontend_pages, frontend_url),
            ("Pricing", test_frontend_pricing, frontend_url),
            ("Enrollment Forms", test_frontend_enrollment_forms, frontend_url),
            ("SEO", test_frontend_seo, frontend_url),
            ("Security", test_frontend_security, frontend_url),
            ("Chat Widget", test_frontend_chat_widget, frontend_url),
        ]

        for group_name, test_fn, url in frontend_groups:
            print(f"\n  📋 {group_name}...")
            try:
                group_results = test_fn(url)
                for r in group_results:
                    icon = "✅" if r.passed else "❌"
                    print(f"    {icon} {r.name}")
                    report.results.append(r)
            except Exception as e:
                print(f"    ❌ {group_name} crashed: {e}")
                report.results.append(TestResult(group_name, "Test execution", False, str(e), "critical"))
    else:
        print(f"\n  ⏭️  Skipping frontend tests (no URL for {env_name})")

    report.duration_s = time.time() - start
    print(report.summary())

    # Save report if requested
    if fix_report:
        report_path = f"qa-report-{env_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        with open(report_path, "w") as f:
            json.dump({
                "env": report.env,
                "timestamp": report.timestamp,
                "duration_s": report.duration_s,
                "passed": report.passed,
                "failed": report.failed,
                "results": [
                    {"category": r.category, "name": r.name, "passed": r.passed,
                     "detail": r.detail, "severity": r.severity}
                    for r in report.results
                ]
            }, f, indent=2)
        print(f"\n  📄 Report saved: {report_path}")

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AIF369 QA Agent")
    parser.add_argument("--env", default="qa", choices=["dev", "qa", "prod"],
                        help="Environment to test (default: qa)")
    parser.add_argument("--fix-report", action="store_true",
                        help="Save JSON report to file")
    args = parser.parse_args()

    report = run_qa(args.env, args.fix_report)
    sys.exit(1 if report.critical_failures else 0)
