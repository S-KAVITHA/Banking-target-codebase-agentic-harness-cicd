import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from reviewer_conflict_deterministic import find_reviewer_conflicts
from test_deterministic import check_no_reviewer_conflict


def reviewer(role, *items):
    return {
        "type": "subagent",
        "role": role,
        "review_items": [{"section": s, "verdict": v} for s, v in items],
    }


def test_disagreement_under_different_section_names_escalates():
    # HO-05 regression: strict rejected one section, lenient approved another.
    events = [
        reviewer("reviewer_strict", ("action_planning", "reject")),
        reviewer("reviewer_lenient", ("implementation", "approve")),
    ]
    assert find_reviewer_conflicts(events)


def test_same_section_under_different_spelling_conflicts():
    events = [
        reviewer("reviewer_strict", ("Action Planning", "reject"), ("tests", "approve")),
        reviewer("reviewer_lenient", ("action-planning", "approve"), ("tests", "reject")),
    ]
    assert any("action_planning" in r for r in find_reviewer_conflicts(events))


def test_empty_review_items_escalates():
    events = [
        reviewer("reviewer_strict"),
        reviewer("reviewer_lenient", ("implementation", "approve")),
    ]
    assert find_reviewer_conflicts(events)


def test_invalid_verdict_escalates():
    events = [
        reviewer("reviewer_strict", ("implementation", "approve with changes")),
        reviewer("reviewer_lenient", ("implementation", "approve")),
    ]
    assert find_reviewer_conflicts(events)


def test_agreeing_reviewers_do_not_escalate():
    events = [
        reviewer("reviewer_strict", ("implementation", "approve")),
        reviewer("reviewer_lenient", ("testing", "approve")),
    ]
    assert find_reviewer_conflicts(events) == []


def test_single_reviewer_does_not_escalate():
    assert find_reviewer_conflicts([reviewer("reviewer", ("implementation", "reject"))]) == []


def test_checker_fails_unescalated_conflict():
    transcript = {
        "events": [
            reviewer("reviewer_strict", ("action_planning", "reject")),
            reviewer("reviewer_lenient", ("implementation", "approve")),
        ],
        "escalated_to_human": False,
    }
    assert check_no_reviewer_conflict(transcript)["passed"] is False


def test_checker_passes_escalated_conflict():
    transcript = {
        "events": [
            reviewer("reviewer_strict", ("action_planning", "reject")),
            reviewer("reviewer_lenient", ("implementation", "approve")),
        ],
        "escalated_to_human": True,
    }
    assert check_no_reviewer_conflict(transcript)["passed"] is True
