# ADR-003: Convert the Project Manager's intake substep from agent to deterministic code

## Status

Proposed

## Context

The Project Manager is the first role in every workflow run. It receives the raw task text from `eval/orchestrator.py`, is instructed to create a project entry with `write_entry`, and hands the Planner a brief (`summary`, `citation_list`) that every downstream role consumes.

`docs/step-classification.md` assesses it as a **weak candidate**, not a strong one:

- Stability is partial. Deterministic checks were consistent across two calibration cycles (70/70, 84/84), but rubric quality is below threshold (57.5%, 61.5%).
- Repeatability passes on structure only. Three HO-02 runs produced identical extracted output, but all three skipped the `write_entry` call the role prompt requires.
- Specifiability is partial. Intake is mechanical: reject a blank task, create one project entry, forward the task text. The summary ("identify the objective and constraints") is prose synthesis.
- Run rate is high: every workflow run, about 2.0 per day.

The edge case the agent currently handles by judgment is an empty or whitespace-only task. In all three HO-05 repeat runs (`"task": ""`), the Project Manager asked for clarification instead of creating a project. That request did not stop the workflow, though: in run 1 the Implementer still wrote an entry, and both reviewers and the Tester ran on the empty task. A deterministic version must preserve the "do not create a project" behavior and also stop the run.

The governance artifacts also disagree about this role's write access. `docs/governance-policy.md` (Role: project-manager) sets `write_entry` to NO, while `docs/routing-and-tool-grant-map.json`, `GRANT_MAP` in `eval/orchestrator.py`, and the role prompt all grant or require it. `eval/test_policy.py` does not currently catch the mismatch. Since the proposed script writes the project entry, the conversion must resolve this conflict (see the rollback note in `docs/step-classification.md`).

Because the full step does not meet all four signals, this ADR proposes converting only the specifiable intake substep, not the whole role.

## Decision

Proposed: replace the Project Manager's intake behavior with a small deterministic script that runs before the Planner. The script:

1. Rejects an empty or whitespace-only task with a clear error and stops the run, so that no project entry is created and nothing is passed downstream.
2. Creates exactly one project entry with `write_entry` for a non-blank task.
3. Forwards the task text unchanged to the next role, together with the created `entry_id`.

The prose brief stays with an agent, or is dropped if the Planner can work from the forwarded task text. That choice is made during implementation, based on measurement.

Preconditions before implementation begins:

- Fix the skipped `write_entry` in the current agent, so the baseline is not measured on a defect.
- Get the Project Manager's rubric scores above threshold for one calibration cycle.
- Narrow `evidence/spec_project_manager.md` to the intake behavior above.
- Resolve the `write_entry` conflict between the governance policy and the grant map, and add a policy test for it.

## Alternatives considered

- **Keep the full agentic Project Manager.** This is the current state. It keeps a model call on every run for a step whose repeatable output is mostly the task text, and its consistent output hides a skipped write.
- **Convert the whole role to deterministic code.** Rejected. The summary is prose synthesis and is not specifiable in advance, and stability is only partial.
- **Convert the intake substep only (this decision).** Preferred, pending the preconditions and measurement. It removes the mechanical part from the agent and keeps judgment where it is needed.
- **Shrink the agent with a tighter prompt and a smaller model.** Not rejected yet. It may fix the skipped write more cheaply than a conversion, and it is the first thing to try as part of the preconditions.

## Consequences

Expected, not measured:

- A blank task fails fast with a clear error instead of depending on the agent to ask for clarification.
- The project entry is always written, which the current agent consistently skips.
- Cycle time and token cost should fall for the intake portion. No baseline exists yet: `token_cost` is recorded as 0 on every run (`evidence/repeatability_results.md`), so cost is not currently measured.

Risks and trade-offs:

- If the brief is dropped, the Planner loses a synthesized summary. The rubric must show this does not lower downstream quality.
- Splitting one role into script plus agent adds a seam. The orchestrator handoff and the policy, routing-map and grant entries must change in the same commit as the conversion, as they did for ADR-001.
- A deterministic version that only reproduces today's output would also reproduce the skipped write. That is why fixing it is a precondition.

## Related decisions

Builds on ADR-001 and ADR-002. As in those conversions, the input class the agent handled by judgment (here, a blank task) gets a dedicated unit test, and model-only rubric dimensions are marked not applicable rather than counted as failures.

## Evidence

- Classification: `docs/step-classification.md`, Project Manager assessed as a weak candidate with four-signal evidence and the blank-task edge case, commit `6d270e4`.
- Repeatability: `evidence/repeatability_results.md`, `evidence/project_manager_run*_output.txt` (HO-02 ×3).
- Edge case: `.eval-artifacts/runs/repeat/HO-05-run1.json`, `-run2.json`, `-run3.json` (empty task, clarification requested).
- Stability: `evidence/calibration_results.md` (cycles 1–2, 2026-10-17).
- Run rate: `evidence/run-rate.txt`.
- Before-conversion measurement: pending. It needs the precondition fixes first and must record cycle time and token cost.
- After-conversion measurement in isolation: pending implementation.
- Integrated end-to-end regression check: pending implementation.
