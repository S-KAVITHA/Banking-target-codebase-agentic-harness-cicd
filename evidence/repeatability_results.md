# Repeatability Results

## Purpose
Record repeatability assessments based on three runs using the same input.

## HO-02: Date Parser Refactor
**Task:** Refactor the date-parsing helper to accept ISO 8601 timestamps in addition to the current format.

**Runs:** `.eval-artifacts/runs/repeat/HO-02-run1.json`, `-run2.json`, `-run3.json` (path `project_manager planner implementer reviewer tester`).
**Method:** `python3 evidence/extract_step.py <run> <role>` → `diff` run1 vs run2 and run1 vs run3. Full output: `evidence/repeatability-diff.txt`.

| Step | diff run1/run2 | diff run1/run3 | What differed | Summary words |
|---|---|---|---|---|
| Project Manager | identical | identical | — (no tool calls in any run) | 55 / 62 / 87 |
| Planner | identical | differs | tools: none / none / `retrieve` ×4 | 43 / 29 / 102 |
| Implementer | identical | differs | tools: none / none / `retrieve` ×2 + `write_entry` ×2 | 82 / 71 / 72 |
| Reviewer | differs | differs | verdicts: `blocker=reject` / none / `planning_phase=approve` | 47 / 47 / 60 |
| Tester | identical | differs | tools: none / none / `read_entry` ×2; verdict: none / none / `implementation=reject` | 36 / 67 / 71 |

* **Project Manager — Repeatable (structure only).** All three runs skipped the `write_entry` call its role prompt asks for.
* **Planner, Implementer, Reviewer, Tester — Not repeatable.**
* **Main source of variation:** runs 1–2 made zero tool calls in every role; run 3 made ten. Durations: 18.0 s, 16.8 s, 45.8 s.
* **Harness note:** the HO-02 path uses role `reviewer`, which has no prompt or tool grant in `eval/orchestrator.py` (only `reviewer_strict` / `reviewer_lenient` do). `token_cost` is recorded as 0 on every run, so cost is not being measured.

---

## HO-05: Independent Reviews and Routing
**Task:** Run two independent reviews and stop for human judgment if the reviewers disagree on whether a section should be approved.

**Runs:** `.eval-artifacts/runs/repeat/HO-05-run1.json`, `-run2.json`, `-run3.json`.

* **Routing — Repeatable:** `diff` of `evidence/routing_run*_output.txt` reported no differences. Every run: path `project_manager planner implementer reviewer_strict reviewer_lenient tester`, `escalated_to_human: False`.
* **But the escalation decision is wrong in substance.** Reviewer verdicts per run:
  * Run 1: strict `blocker_identification=approve`, `action_planning=reject`, `validation_criteria=reject`, `escalation_procedure=reject`; lenient `blocker_identification=approve`, `implementation=approve`.
  * Run 2: strict `project_initialization=reject`, `planner_handoff=reject`; lenient `implementation=approve`.
  * Run 3: strict `completeness=reject`, `project_context=reject`, `work_artifacts=reject`; lenient `workflow_completeness=reject`.

  In runs 1 and 2 the reviewers disagreed (strict rejected, lenient approved) but under different section names, so the exact-name match found no conflict and did not escalate. This is the residual gap recorded in `docs/calibration-log.md` (2026-09-14).
* **Input validity (checked 2026-10-17): invalid.** The first handoff in all three runs has `"task": ""`, and the Project Manager asked for clarification each time. The HO-02 runs used the correct task text. This HO-05 comparison is not valid repeatability evidence; rerun it with the task from `docs/holdout-task-set.md`.
* **Conflict rule fixed (2026-10-17):** With `scripts/reviewer_conflict_deterministic.py`, runs 1–2 now fail the `reviewer_conflict` check (disagreement not escalated) and run 3 passes.

---

## Assessment
* Project Manager passes the repeatability signal, but its repeatable output hides a skipped write. Routing is unconfirmed because its HO-05 runs had an empty task.
* Planner, Implementer, Reviewer, and Tester fail the repeatability signal because their extracted outputs differ across runs.
* A repeatability failure does not automatically mean a step can never be converted. First identify the source of variation and determine whether its meaningful decisions and output contract can be made consistent.

---

## Next Actions
1. Investigate why Planner, Implementer, Reviewer, and Tester outputs vary.
2. Define clearer output formats and decision criteria where appropriate.
3. Rerun each affected step three times on the same valid holdout input.
4. Compare the new extracted outputs and record the actual results.
5. Update `docs/step-classification.md` to reflect these findings.