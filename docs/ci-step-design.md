# CI Agentic Step Design

## Step: Policy test suite

- Does: Confirms `docs/governance-policy.md`, MCP allow-lists, skill scopes, and container permissions agree.
- Input: whole repository.
- Produces: `policy-report.json` artifact.
- Classification: gating, permanent.
- Time limit: 5 minutes.
- Credentials: none.

## Step: Evaluation harness

- Does: Runs deterministic and rubric checks on agent-affecting changes.
- Input: whole repository plus changed-file classifier output.
- Produces: `deterministic-report.json` and `rubric-report.json`.
- Classification: gating, conditional.
- Time limit: 10 minutes.
- Credentials: `ANTHROPIC_API_KEY` only for model-backed rubric runs.

## Step: Agent code review

- Does: Reviewer subagent scores changed files and posts an advisory PR comment.
- Input: changed files from the shared classifier.
- Produces: PR comment, `review-output.md`, and review audit log.
- Classification: advisory; not a required status check.
- Time limit: 15 minutes.
- Credentials: `ANTHROPIC_API_KEY`, scoped to the reviewer step only.

## Step: Audit trail

- Does: Combines policy, harness, and review artifacts into one JSON trail and posts a PR summary.
- Input: CI artifacts from earlier jobs.
- Produces: `ci-audit-trail-[sha].json` artifact and PR comment.
- Classification: required operational evidence; always runs.
- Credentials: GitHub token with pull-request comment permission.

## Step: Automated code review
- Does: Reviewer subagent scores changed files against the rubric and posts a PR comment.
- Input: changed files in the pull request.
- Produces: a structured review comment.
- Classification: advisory (new; promote to gating once stable).
- Time limit: 15 minutes.
- Credentials: OPENROUTER_API_KEY, scoped to this step only.

## Step: Pipeline Integrity Check
- Does: Inspects .github/workflows/ci.yml to ensure policy-gate and eval-gate do not use continue-on-error: true, audit-trail retains if: always(), and change-type-check still exists.
- Input: .github/workflows/ci.yml.
- Produces: pipeline-integrity-report.json, containing job status and detected violations in the existing audit-report schema.
- Classification: gating, permanent; protects agreed-upon pipeline invariants and must never be demoted to advisory.
- Time limit: 5 minutes.
- Credentials: none.
- Audit integration: Included in audit-trail's needs: list. Report generation and upload run even if validation fails.
- Verified: Temporarily added `continue-on-error: true` to `policy-gate`. Pipeline Integrity Check detected the weakened gate and failed with exit code 1. The failure report appeared in the audit trail. Reverted the change and confirmed the workflow passed again.
- Artifact handling: Skipped or not-applicable states must follow the existing audit schema rather than being reported as failures.