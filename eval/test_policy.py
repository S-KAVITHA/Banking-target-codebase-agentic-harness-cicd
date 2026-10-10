from pathlib import Path
import re
import json
import pytest

ROOT = Path(".")
POLICY_PATH = "docs/governance-policy.md"
STORAGE_PATH = "mcp-servers/storage/allow-list.json"
RETRIEVAL_PATH = "mcp-servers/retrieval/allow-list.json"
CONTAINER_PATH = "scripts/run-agent.sh"

ROLES = [
    "implementer",
    "reviewer",
    "tester",
    "project-manager",
    "orchestrator",
]

def test_governance_policy_exists():
    assert (ROOT / "docs" / "governance-policy.md").exists(), (
        "Missing docs/governance-policy.md"
    )


def test_ci_step_design_exists():
    assert (ROOT / "docs" / "ci-step-design.md").exists(), (
        "Missing docs/ci-step-design.md"
    )


def test_workflow_exists_at_repo_root():
    assert (ROOT / ".github" / "workflows" / "ci.yml").exists(), (
        "Workflow must live at .github/workflows/ci.yml"
    )


def test_workflow_does_not_hardcode_anthropic_key():
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    forbidden_patterns = [
        r"sk-ant-[A-Za-z0-9_\-]+",
        r"ANTHROPIC_API_KEY\s*=\s*sk-",
    ]

    for pattern in forbidden_patterns:
        assert not re.search(pattern, workflow), (
            "Do not hardcode Anthropic keys in the workflow. "
            "Use ${{ secrets.ANTHROPIC_API_KEY }}."
        )


def test_policy_gate_is_not_continue_on_error():
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    policy_section_start = workflow.find("policy-gate:")
    assert policy_section_start != -1, "Missing policy-gate job"

    next_job_start = workflow.find("\n  governed-file-gate:", policy_section_start)
    section = workflow[policy_section_start:next_job_start]

    assert "continue-on-error: true" not in section, (
        "policy-gate must remain a real gate, not advisory."
    )
def role_section(policy, role):
    return re.search(
        rf"## Role: {role}\n(.*?)(?=## Role: |\Z)",
        policy, re.S
    ).group(1)


def grants(section):
    return dict(re.findall(
        r"\|\s*(\w+)\s*\|\s*\w+\s*\|\s*(YES|NO)\s*\|",
        section
    ))


def test_storage_allowlist_matches_policy():
    policy = (ROOT / POLICY_PATH).read_text()
    data = json.loads((ROOT / STORAGE_PATH).read_text())

    for role in ROLES:
        expected = {
            op for op, value in grants(role_section(policy, role)).items()
            if value == "YES" and op != "retrieve"
        }
        actual = {op for op, roles in data.items() if role in roles}
        assert actual == expected, f"Storage mismatch: {role}"


def test_no_storage_overgrant():
    policy = (ROOT / POLICY_PATH).read_text()
    data = json.loads((ROOT / STORAGE_PATH).read_text())

    for op, roles in data.items():
        for role in roles:
            assert grants(role_section(policy, role)).get(op) == "YES", (
                f"Over-grant: {role} has {op}"
            )


def test_container_workspace_matches_policy():
    policy = (ROOT / POLICY_PATH).read_text()
    script = (ROOT / CONTAINER_PATH).read_text()

    expected = {
        "implementer": ("read-write", "mounted"),
        "reviewer": ("read-only", "omitted"),
        "tester": ("read-only", "omitted"),
        "project-manager": ("read-only", "omitted"),
        "orchestrator": ("read-write", "mounted"),
    }

    for role, values in expected.items():
        section = role_section(policy, role)
        match = re.search(
            r"\*\*Container permissions:\*\* workspace "
            r"(read-write|read-only), memory (mounted|omitted)", section
        )
        assert match and match.groups() == values, f"Policy: {role}"

    assert 'WORKSPACE_MODE="rw"' in script
    assert 'WORKSPACE_MODE="ro"' in script
    assert "MOUNT_MEMORY=1" in script
    assert "MOUNT_MEMORY=0" in script


def test_skill_scope_matches_policy():
    policy = (ROOT / POLICY_PATH).read_text()

    for role in ROLES:
        section = role_section(policy, role)
        assert "### Skill activation scope" in section