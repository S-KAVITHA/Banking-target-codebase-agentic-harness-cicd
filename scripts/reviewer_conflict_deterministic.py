"""Deterministic reviewer-conflict detection.

Shared by eval/orchestrator.py (to set escalated_to_human) and
eval/test_deterministic.py (to check it), so the two cannot drift apart.

A run needs human escalation when two or more reviewers ran and:
  - any reviewer returned no review_items or a verdict other than approve/reject,
  - the reviewers' overall verdicts differ (any reject = reject), or
  - the reviewers gave opposite verdicts on the same section, compared after
    normalizing section names (case, spaces, hyphens).
"""

VALID_VERDICTS = {"approve", "reject"}


def normalize_section(name):
    return "_".join(str(name).strip().lower().replace("-", " ").split())


def find_reviewer_conflicts(reviewer_events):
    """Return a list of conflict reasons; an empty list means no escalation needed."""
    if len(reviewer_events) < 2:
        return []

    reasons = []
    overall = {}
    by_section = {}
    for rev in reviewer_events:
        role = rev.get("role", "reviewer")
        items = rev.get("review_items") or []
        if not items:
            reasons.append(f"{role} returned no review_items")
            continue
        verdicts = [item.get("verdict") for item in items]
        if any(v not in VALID_VERDICTS for v in verdicts):
            reasons.append(f"{role} returned an invalid verdict")
            continue
        overall[role] = "reject" if "reject" in verdicts else "approve"
        for item in items:
            section = normalize_section(item.get("section", ""))
            by_section.setdefault(section, set()).add(item["verdict"])

    if len(set(overall.values())) > 1:
        summary = ", ".join(f"{role}={v}" for role, v in overall.items())
        reasons.append(f"reviewers disagree overall ({summary})")

    for section, verdicts in by_section.items():
        if VALID_VERDICTS <= verdicts:
            reasons.append(f"opposite verdicts on section '{section}'")

    return reasons
