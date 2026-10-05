from pathlib import Path


ROOT = Path(".")


def test_governed_artifacts_exist():
    required = [
        "docs/governance-policy.md",
        "docs/ci-step-design.md",
    ]

    missing = [path for path in required if not (ROOT / path).exists()]
    assert not missing, f"Missing governed artifacts: {missing}"


def test_governed_directories_are_versioned_when_present():
    # These do not all have to exist in every starter repo, but if they do,
    # they should be real directories rather than generated CI output.
    optional_dirs = [
        ".agents",
        ".skills",
        "mcp-servers",
        "eval",
        "scripts",
    ]

    for dirname in optional_dirs:
        path = ROOT / dirname
        if path.exists():
            assert path.is_dir(), f"{dirname} should be a directory"


def test_reviewer_script_exists():
    assert (ROOT / "scripts" / "run-reviewer.py").exists(), (
        "Missing scripts/run-reviewer.py"
    )


def test_audit_script_exists():
    assert (ROOT / "scripts" / "build-audit-trail.py").exists(), (
        "Missing scripts/build-audit-trail.py"
    )
