# AIF369 Agent Operating Policy

This repository is operated under a zero-trust release model.

## Autonomy Boundary

Agents may:

- Develop code and infrastructure as code on `dev` and feature branches.
- Push to `dev` after local checks pass.
- Promote from `dev` to `qa` after DEV checks pass.
- Deploy and validate DEV and QA environments.
- Open a production PR from `qa` to `main` with release notes, QA evidence, risk notes, and rollback plan.
- Execute the production deployment only after the production PR has been approved and merged by Erwin or another named human owner.
- Rotate or create secrets in approved secret managers when explicitly needed for DEV/QA or urgent security response.
- Produce production release candidates, changelogs, rollback plans, and verification evidence.

Agents must not:

- Push directly to `main`.
- Merge `qa` into `main`.
- Approve their own production PR.
- Merge production PRs.
- Bypass PR review for production.
- Approve GitHub production environments.
- Run `gcloud run deploy` against production services.
- Run Terraform apply for production.
- Store secrets, passwords, tokens, private keys, API keys, credentials, production data exports, or raw logs in Git.

## Production Rule

Production deployment requires explicit approval from Erwin or another named human owner on the PR from `qa` to `main`. The approval must be specific to that production release.

Generic prior permission, broad trust, access to credentials, or an approved DEV/QA deployment is not production approval.

## Allowed Promotion Path

```text
feature/local -> dev -> qa -> PR qa-to-main -> human PR approval/merge -> production
```

Agents can complete everything through QA and prepare the production PR. After QA passes, agents must stop for human PR approval and present:

- commit SHA;
- DEV and QA workflow links;
- test summary;
- security scan result;
- production impact;
- rollback plan.

## Secret Handling

- Use Secret Manager, GitHub Environments/Secrets, or an approved vault.
- Prefer short-lived identity and workload identity over static keys.
- Never print secret values in logs or terminal summaries.
- Never write new secrets to `.env`, reports, screenshots, or local artifacts intended for commit.
- If a secret may have been exposed, assume compromise: revoke/rotate first, then close alerts.

## Production Services

The following are production and require human approval:

- direct push to branch: `main`;
- GitHub environments: `production`, `prod`;
- Cloud Run services without `-dev` or `-qa`, including `aif369-backend-api` and `aif369-master-api`;
- BigQuery dataset `aif369_analytics`;
- Terraform var files or targets containing `production`.

## Agent Behavior

When asked to “take it to prod”, the agent may open the production PR and prepare deployment evidence. The agent must not approve or merge the PR; production proceeds only after human PR approval/merge.

When asked to “train the agent”, update this file and enforce the rule in CI/CD wherever possible.
