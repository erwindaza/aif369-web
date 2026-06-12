"""
Cloud Function: stop_billing
Triggered by Pub/Sub when GCP budget threshold is hit.

- At ~50% ($10 USD): solo alerta (email via budget config)
- At 100% ($20 USD): deshabilita billing en ambos proyectos para detener TODOS los servicios.
"""
import base64
import json
import logging

from googleapiclient import discovery

logger = logging.getLogger(__name__)

PROJECT_IDS = ["aif369-backend", "bejoby-ai-app"]
BILLING_ACCOUNT = "billingAccounts/0174A7-3C06E7-A99F49"


def stop_billing(event, context):
    """
    Pub/Sub trigger. Payload from GCP Budget Notifications:
    {
      "budgetDisplayName": "Mi cuenta $20",
      "alertThresholdExceeded": 1.0,  # or 0.5
      "costAmount": 20.12,
      "costIntervalStart": "2026-05-01T00:00:00Z",
      "budgetAmount": 20.0,
      "budgetAmountType": "SPECIFIED_AMOUNT",
      "currencyCode": "USD"
    }
    """
    pubsub_data = base64.b64decode(event["data"]).decode("utf-8")
    notification = json.loads(pubsub_data)

    cost = notification.get("costAmount", 0)
    budget = notification.get("budgetAmount", 0)
    threshold = notification.get("alertThresholdExceeded", 0)
    currency = notification.get("currencyCode", "USD")

    logger.info(
        f"Budget notification: cost={cost} {currency}, budget={budget} {currency}, threshold={threshold}"
    )

    if cost < budget:
        logger.info(
            f"Cost ${cost} is below budget ${budget} — no action (threshold alert at {threshold*100:.0f}%)"
        )
        return f"Alert only: ${cost:.2f} of ${budget:.2f} spent ({threshold*100:.0f}%)"

    # Cost >= budget: disable billing on all projects
    logger.warning(
        f"BUDGET EXCEEDED: ${cost:.2f} >= ${budget:.2f} — disabling billing on all projects"
    )

    billing = discovery.build("cloudbilling", "v1", cache_discovery=False)
    results = []

    for project_id in PROJECT_IDS:
        try:
            response = (
                billing.projects()
                .updateBillingInfo(
                    name=f"projects/{project_id}",
                    body={"billingAccountName": ""},  # empty = disable billing
                )
                .execute()
            )
            msg = f"Billing DISABLED for {project_id}: {response}"
            logger.warning(msg)
            results.append(msg)
        except Exception as e:
            msg = f"ERROR disabling billing for {project_id}: {e}"
            logger.error(msg)
            results.append(msg)

    return "\n".join(results)
