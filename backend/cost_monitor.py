"""
AIF369 GCP Cost Monitor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Módulo de monitoreo de costos GCP en tiempo real.
Consulta datos de billing export en BigQuery + métricas de Cloud Monitoring.

Tabla de billing export (auto-creada por GCP):
  {PROJECT_ID}.billing_export.gcp_billing_export_v1_{BILLING_ACCOUNT_ID}

Requiere:
  - Billing export habilitado en GCP Console
  - Service account con roles/bigquery.dataViewer + roles/bigquery.jobUser
  - roles/monitoring.viewer para métricas de uso
"""

import os
import json
from datetime import datetime, timezone, timedelta
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# ── Config ──────────────────────────────────────────────────────
PROJECT_ID = os.getenv("PROJECT_ID", "aif369-backend")
BILLING_ACCOUNT_ID = os.getenv("BILLING_ACCOUNT_ID", "0174A7-3C06E7-A99F49")
BILLING_DATASET = os.getenv("BILLING_DATASET", "billing_export")
BUDGET_AMOUNT_CLP = int(os.getenv("BUDGET_AMOUNT_CLP", "10000"))
BUDGET_AMOUNT_USD = float(os.getenv("BUDGET_AMOUNT_USD", "10.0"))

# Tabla generada automáticamente por GCP billing export
_billing_account_clean = BILLING_ACCOUNT_ID.replace("-", "_")
BILLING_TABLE = f"{PROJECT_ID}.{BILLING_DATASET}.gcp_billing_export_v1_{_billing_account_clean}"

# BigQuery client (singleton)
_bq_client = None


def _get_bq_client():
    global _bq_client
    if _bq_client is None:
        _bq_client = bigquery.Client(project=PROJECT_ID)
    return _bq_client


def _table_exists():
    """Verifica si la tabla de billing export existe."""
    try:
        client = _get_bq_client()
        client.get_table(BILLING_TABLE)
        return True
    except NotFound:
        return False
    except Exception as e:
        print(f"Error checking billing table: {e}")
        return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CAPA 1: BigQuery Billing Export (datos reales detallados)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def get_monthly_summary(year=None, month=None):
    """
    Resumen de costos del mes actual (o especificado).
    Retorna: total_cost, currency, cost_vs_budget_pct, day_of_month, projected_monthly.
    """
    if not _table_exists():
        return _fallback_summary()

    now = datetime.now(timezone.utc)
    year = year or now.year
    month = month or now.month

    query = f"""
    SELECT
        SUM(cost) as total_cost,
        currency,
        SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)) as total_credits,
        MIN(DATE(usage_start_time)) as first_day,
        MAX(DATE(usage_start_time)) as last_day,
        COUNT(DISTINCT DATE(usage_start_time)) as active_days,
        COUNT(DISTINCT service.description) as num_services
    FROM `{BILLING_TABLE}`
    WHERE invoice.month = FORMAT_DATE('%Y%m', DATE({year}, {month}, 1))
      AND project.id = '{PROJECT_ID}'
    GROUP BY currency
    """

    try:
        client = _get_bq_client()
        rows = list(client.query(query).result())
        if not rows or rows[0].total_cost is None:
            return _fallback_summary()

        row = rows[0]
        total_cost = float(row.total_cost)
        total_credits = float(row.total_credits)
        net_cost = total_cost + total_credits  # credits are negative
        currency = row.currency
        active_days = row.active_days
        num_services = row.num_services

        # Calcular proyección mensual
        import calendar
        days_in_month = calendar.monthrange(year, month)[1]
        current_day = min(now.day, days_in_month) if month == now.month else days_in_month
        
        if current_day > 0 and active_days > 0:
            daily_avg = net_cost / current_day
            projected = daily_avg * days_in_month
        else:
            projected = net_cost

        # Budget comparison
        budget = BUDGET_AMOUNT_CLP if currency == "CLP" else BUDGET_AMOUNT_USD
        budget_pct = (net_cost / budget * 100) if budget > 0 else 0

        return {
            "status": "ok",
            "source": "billing_export",
            "period": f"{year}-{month:02d}",
            "total_cost": round(total_cost, 4),
            "total_credits": round(total_credits, 4),
            "net_cost": round(net_cost, 4),
            "currency": currency,
            "budget_amount": budget,
            "budget_pct": round(budget_pct, 2),
            "budget_status": _budget_status(budget_pct),
            "projected_monthly": round(projected, 4),
            "projected_budget_pct": round(projected / budget * 100, 2) if budget > 0 else 0,
            "active_days": active_days,
            "day_of_month": current_day,
            "days_in_month": days_in_month,
            "num_services": num_services,
            "daily_average": round(net_cost / max(current_day, 1), 4),
        }
    except Exception as e:
        print(f"Error querying billing summary: {e}")
        return _fallback_summary(error=str(e))


def get_cost_by_service(year=None, month=None):
    """
    Desglose de costos por servicio GCP.
    Retorna lista ordenada por costo descendente.
    """
    if not _table_exists():
        return _fallback_services()

    now = datetime.now(timezone.utc)
    year = year or now.year
    month = month or now.month

    query = f"""
    SELECT
        service.description as service_name,
        service.id as service_id,
        SUM(cost) as total_cost,
        SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)) as total_credits,
        currency,
        COUNT(DISTINCT sku.description) as num_skus,
        COUNT(*) as num_records
    FROM `{BILLING_TABLE}`
    WHERE invoice.month = FORMAT_DATE('%Y%m', DATE({year}, {month}, 1))
      AND project.id = '{PROJECT_ID}'
    GROUP BY service.description, service.id, currency
    ORDER BY total_cost DESC
    """

    try:
        client = _get_bq_client()
        rows = list(client.query(query).result())
        
        services = []
        total = 0
        for row in rows:
            cost = float(row.total_cost)
            credits = float(row.total_credits)
            net = cost + credits
            total += net
            services.append({
                "service_name": row.service_name,
                "service_id": row.service_id,
                "cost": round(cost, 4),
                "credits": round(credits, 4),
                "net_cost": round(net, 4),
                "currency": row.currency,
                "num_skus": row.num_skus,
                "num_records": row.num_records,
            })

        # Add percentage
        for svc in services:
            svc["pct_of_total"] = round(svc["net_cost"] / total * 100, 2) if total > 0 else 0

        return {
            "status": "ok",
            "source": "billing_export",
            "period": f"{year}-{month:02d}",
            "total_cost": round(total, 4),
            "services": services,
            "num_services": len(services),
        }
    except Exception as e:
        print(f"Error querying cost by service: {e}")
        return _fallback_services(error=str(e))


def get_daily_costs(year=None, month=None):
    """
    Costos diarios del mes para visualización de tendencia.
    """
    if not _table_exists():
        return _fallback_daily()

    now = datetime.now(timezone.utc)
    year = year or now.year
    month = month or now.month

    query = f"""
    SELECT
        DATE(usage_start_time) as usage_date,
        SUM(cost) as total_cost,
        SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)) as total_credits,
        currency,
        COUNT(DISTINCT service.description) as num_services
    FROM `{BILLING_TABLE}`
    WHERE invoice.month = FORMAT_DATE('%Y%m', DATE({year}, {month}, 1))
      AND project.id = '{PROJECT_ID}'
    GROUP BY usage_date, currency
    ORDER BY usage_date ASC
    """

    try:
        client = _get_bq_client()
        rows = list(client.query(query).result())

        daily = []
        running_total = 0
        for row in rows:
            cost = float(row.total_cost)
            credits = float(row.total_credits)
            net = cost + credits
            running_total += net
            daily.append({
                "date": row.usage_date.isoformat(),
                "cost": round(cost, 4),
                "credits": round(credits, 4),
                "net_cost": round(net, 4),
                "cumulative": round(running_total, 4),
                "currency": row.currency,
                "num_services": row.num_services,
            })

        return {
            "status": "ok",
            "source": "billing_export",
            "period": f"{year}-{month:02d}",
            "daily": daily,
            "total_days": len(daily),
        }
    except Exception as e:
        print(f"Error querying daily costs: {e}")
        return _fallback_daily(error=str(e))


def get_top_skus(year=None, month=None, limit=20):
    """
    Top SKUs por costo — muestra qué operaciones específicas cuestan más.
    """
    if not _table_exists():
        return {"status": "no_billing_export", "skus": [], "message": "Billing export no configurado"}

    now = datetime.now(timezone.utc)
    year = year or now.year
    month = month or now.month

    query = f"""
    SELECT
        service.description as service_name,
        sku.description as sku_name,
        SUM(cost) as total_cost,
        SUM(usage.amount) as total_usage,
        usage.unit as usage_unit,
        currency
    FROM `{BILLING_TABLE}`
    WHERE invoice.month = FORMAT_DATE('%Y%m', DATE({year}, {month}, 1))
      AND project.id = '{PROJECT_ID}'
      AND cost > 0
    GROUP BY service_name, sku_name, usage_unit, currency
    ORDER BY total_cost DESC
    LIMIT {limit}
    """

    try:
        client = _get_bq_client()
        rows = list(client.query(query).result())

        skus = []
        for row in rows:
            skus.append({
                "service": row.service_name,
                "sku": row.sku_name,
                "cost": round(float(row.total_cost), 6),
                "usage": round(float(row.total_usage), 4) if row.total_usage else 0,
                "unit": row.usage_unit,
                "currency": row.currency,
            })

        return {
            "status": "ok",
            "source": "billing_export",
            "period": f"{year}-{month:02d}",
            "skus": skus,
        }
    except Exception as e:
        print(f"Error querying top SKUs: {e}")
        return {"status": "error", "skus": [], "error": str(e)}


def get_cost_trend(months=6):
    """
    Tendencia de costos por mes (últimos N meses).
    """
    if not _table_exists():
        return {"status": "no_billing_export", "months": [], "message": "Billing export no configurado"}

    query = f"""
    SELECT
        invoice.month as invoice_month,
        SUM(cost) as total_cost,
        SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)) as total_credits,
        currency,
        COUNT(DISTINCT service.description) as num_services,
        COUNT(DISTINCT DATE(usage_start_time)) as active_days
    FROM `{BILLING_TABLE}`
    WHERE project.id = '{PROJECT_ID}'
      AND DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL {months} MONTH)
    GROUP BY invoice_month, currency
    ORDER BY invoice_month DESC
    """

    try:
        client = _get_bq_client()
        rows = list(client.query(query).result())

        trend = []
        for row in rows:
            cost = float(row.total_cost)
            credits = float(row.total_credits)
            net = cost + credits
            trend.append({
                "month": row.invoice_month,
                "cost": round(cost, 4),
                "credits": round(credits, 4),
                "net_cost": round(net, 4),
                "currency": row.currency,
                "num_services": row.num_services,
                "active_days": row.active_days,
            })

        return {
            "status": "ok",
            "source": "billing_export",
            "trend": trend,
        }
    except Exception as e:
        print(f"Error querying cost trend: {e}")
        return {"status": "error", "trend": [], "error": str(e)}


def get_budget_status():
    """
    Estado del presupuesto con alertas y recomendaciones.
    """
    summary = get_monthly_summary()

    budget_amount = summary.get("budget_amount", BUDGET_AMOUNT_CLP)
    net_cost = summary.get("net_cost", 0)
    projected = summary.get("projected_monthly", 0)
    budget_pct = summary.get("budget_pct", 0)
    currency = summary.get("currency", "USD")

    alerts = []
    if budget_pct >= 100:
        alerts.append({
            "level": "critical",
            "message": f"⚠️ Presupuesto SUPERADO: {budget_pct:.1f}% del límite mensual",
            "action": "Revisar servicios activos y reducir uso inmediatamente"
        })
    elif budget_pct >= 80:
        alerts.append({
            "level": "warning",
            "message": f"⚡ Presupuesto al {budget_pct:.1f}% — acercándose al límite",
            "action": "Monitorear uso diario y considerar optimizaciones"
        })
    elif budget_pct >= 50:
        alerts.append({
            "level": "info",
            "message": f"📊 Presupuesto al {budget_pct:.1f}% — en rango normal",
            "action": "Seguir monitoreando"
        })
    else:
        alerts.append({
            "level": "ok",
            "message": f"✅ Presupuesto saludable: {budget_pct:.1f}% usado",
            "action": "Sin acciones requeridas"
        })

    # Alerta de proyección
    projected_pct = summary.get("projected_budget_pct", 0)
    if projected_pct > 100:
        alerts.append({
            "level": "warning",
            "message": f"📈 Proyección mensual: {projected_pct:.1f}% del presupuesto",
            "action": "Al ritmo actual, se superará el presupuesto a fin de mes"
        })

    return {
        "status": "ok",
        "budget": {
            "amount": budget_amount,
            "currency": currency,
            "current_spend": net_cost,
            "spend_pct": round(budget_pct, 2),
            "projected_spend": projected,
            "projected_pct": round(projected_pct, 2),
            "remaining": round(budget_amount - net_cost, 4),
        },
        "alerts": alerts,
        "thresholds": [
            {"pct": 50, "status": "ok" if budget_pct < 50 else "triggered"},
            {"pct": 80, "status": "ok" if budget_pct < 80 else "triggered"},
            {"pct": 100, "status": "ok" if budget_pct < 100 else "triggered"},
        ],
        "summary": summary,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CAPA 2: Fallbacks — estimaciones cuando billing export no existe
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Estimaciones de costo del free tier GCP para los servicios de AIF369
_SERVICE_ESTIMATES = {
    "Cloud Run": {
        "monthly_estimate_usd": 0.00,
        "note": "Free tier: 2M requests/month, 360K vCPU-sec. Uso AIF369 < 1% del free tier.",
    },
    "BigQuery": {
        "monthly_estimate_usd": 0.00,
        "note": "Free tier: 1TB queries/month, 10GB storage. Uso AIF369 < 1MB datos.",
    },
    "Cloud Storage": {
        "monthly_estimate_usd": 0.02,
        "note": "5GB free, ~$0.02/GB extra. AIF369 usa ~3 buckets con < 100MB total.",
    },
    "Secret Manager": {
        "monthly_estimate_usd": 0.00,
        "note": "6 secret versions free. AIF369 usa 3 secrets.",
    },
    "Artifact Registry / GCR": {
        "monthly_estimate_usd": 0.10,
        "note": "~500MB de imágenes Docker. $0.10/GB/month.",
    },
    "Cloud Build": {
        "monthly_estimate_usd": 0.00,
        "note": "120 build-min/day free. Builds esporádicos.",
    },
    "Gemini API": {
        "monthly_estimate_usd": 0.50,
        "note": "~$0.075/1K input tokens. Uso estimado: ~5K tokens/day.",
    },
    "Cloud Logging": {
        "monthly_estimate_usd": 0.00,
        "note": "50GB/month free ingest. AIF369 genera < 100MB/month.",
    },
    "IAM & Admin": {
        "monthly_estimate_usd": 0.00,
        "note": "Sin costo directo.",
    },
}


def _fallback_summary(error=None):
    """Estimación cuando no hay billing export."""
    total_estimate = sum(s["monthly_estimate_usd"] for s in _SERVICE_ESTIMATES.values())
    budget = BUDGET_AMOUNT_USD
    now = datetime.now(timezone.utc)
    import calendar
    days_in_month = calendar.monthrange(now.year, now.month)[1]

    return {
        "status": "estimated",
        "source": "static_estimates",
        "message": "Billing export no habilitado. Datos son estimaciones estáticas.",
        "setup_url": "https://console.cloud.google.com/billing/exports?project=" + PROJECT_ID,
        "period": f"{now.year}-{now.month:02d}",
        "total_cost": round(total_estimate, 2),
        "total_credits": 0,
        "net_cost": round(total_estimate, 2),
        "currency": "USD",
        "budget_amount": budget,
        "budget_pct": round(total_estimate / budget * 100, 2) if budget > 0 else 0,
        "budget_status": "ok",
        "projected_monthly": round(total_estimate, 2),
        "projected_budget_pct": round(total_estimate / budget * 100, 2) if budget > 0 else 0,
        "active_days": now.day,
        "day_of_month": now.day,
        "days_in_month": days_in_month,
        "num_services": len(_SERVICE_ESTIMATES),
        "daily_average": round(total_estimate / days_in_month, 4),
        "error": error,
    }


def _fallback_services(error=None):
    """Estimaciones por servicio cuando no hay billing export."""
    services = []
    total = sum(s["monthly_estimate_usd"] for s in _SERVICE_ESTIMATES.values())
    
    for name, info in _SERVICE_ESTIMATES.items():
        cost = info["monthly_estimate_usd"]
        services.append({
            "service_name": name,
            "service_id": name.lower().replace(" ", "_"),
            "cost": cost,
            "credits": 0,
            "net_cost": cost,
            "currency": "USD",
            "num_skus": 0,
            "num_records": 0,
            "pct_of_total": round(cost / total * 100, 2) if total > 0 else 0,
            "note": info["note"],
        })

    services.sort(key=lambda x: x["net_cost"], reverse=True)

    return {
        "status": "estimated",
        "source": "static_estimates",
        "message": "Billing export no habilitado. Datos son estimaciones.",
        "setup_url": "https://console.cloud.google.com/billing/exports?project=" + PROJECT_ID,
        "period": datetime.now(timezone.utc).strftime("%Y-%m"),
        "total_cost": round(total, 2),
        "services": services,
        "num_services": len(services),
        "error": error,
    }


def _fallback_daily(error=None):
    """Data diaria estimada cuando no hay billing export."""
    now = datetime.now(timezone.utc)
    total = sum(s["monthly_estimate_usd"] for s in _SERVICE_ESTIMATES.values())
    import calendar
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    daily_avg = total / days_in_month

    daily = []
    cumulative = 0
    for day in range(1, min(now.day + 1, days_in_month + 1)):
        cumulative += daily_avg
        daily.append({
            "date": f"{now.year}-{now.month:02d}-{day:02d}",
            "cost": round(daily_avg, 4),
            "credits": 0,
            "net_cost": round(daily_avg, 4),
            "cumulative": round(cumulative, 4),
            "currency": "USD",
            "num_services": len(_SERVICE_ESTIMATES),
        })

    return {
        "status": "estimated",
        "source": "static_estimates",
        "message": "Billing export no habilitado.",
        "period": now.strftime("%Y-%m"),
        "daily": daily,
        "total_days": len(daily),
        "error": error,
    }


def _budget_status(pct):
    """Determina el estado del presupuesto."""
    if pct >= 100:
        return "critical"
    elif pct >= 80:
        return "warning"
    elif pct >= 50:
        return "caution"
    return "ok"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Utility: Health check del sistema de monitoreo
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def check_monitoring_health():
    """
    Verifica el estado completo del sistema de monitoreo de costos.
    """
    checks = {
        "bigquery_client": False,
        "billing_export_dataset": False,
        "billing_export_table": False,
        "data_freshness": None,
    }

    try:
        client = _get_bq_client()
        checks["bigquery_client"] = True
    except Exception as e:
        return {"status": "error", "checks": checks, "error": f"BigQuery client: {e}"}

    try:
        client.get_dataset(f"{PROJECT_ID}.{BILLING_DATASET}")
        checks["billing_export_dataset"] = True
    except NotFound:
        checks["billing_export_dataset"] = False
    except Exception as e:
        checks["billing_export_dataset"] = f"error: {e}"

    if _table_exists():
        checks["billing_export_table"] = True
        # Check data freshness
        try:
            query = f"""
            SELECT MAX(export_time) as latest
            FROM `{BILLING_TABLE}`
            WHERE project.id = '{PROJECT_ID}'
            """
            rows = list(client.query(query).result())
            if rows and rows[0].latest:
                latest = rows[0].latest
                age = datetime.now(timezone.utc) - latest.replace(tzinfo=timezone.utc)
                checks["data_freshness"] = {
                    "latest_export": latest.isoformat(),
                    "age_hours": round(age.total_seconds() / 3600, 1),
                    "status": "ok" if age.total_seconds() < 86400 else "stale",
                }
        except Exception:
            pass
    else:
        checks["billing_export_table"] = False
        checks["data_freshness"] = "N/A — billing export not enabled"

    overall = "ok" if all([
        checks["bigquery_client"],
        checks["billing_export_dataset"],
        checks["billing_export_table"] is True,
    ]) else "degraded"

    return {
        "status": overall,
        "checks": checks,
        "billing_table": BILLING_TABLE,
        "project_id": PROJECT_ID,
        "budget_clp": BUDGET_AMOUNT_CLP,
        "budget_usd": BUDGET_AMOUNT_USD,
    }
