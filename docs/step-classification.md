# Step Classification

This document records the four-signal assessment of agentic workflow steps: stability, repeatability, specifiability, and high run rate. A step is recommended for deterministic conversion only when all four signals are supported by evidence.

This document is updated after every calibration cycle. Steps that cross the
stability threshold are promoted to candidate status. A step that has been a
candidate for more than two calibration cycles without meeting all four
signals is reviewed for re-scoping.

## Step: JSON Schema Validation

- **Status:** Converted to deterministic (ADR-001, 2026-06-06). ADR-001 accepted 2026-10-21 (commit `2999335`) after the integrated end-to-end regression check (commit `af60fb7`, 14/14 checks passing, no regressions).
- **Stability:** Harness scores 14/16, 15/16, 14/16 across the last three calibration runs. Consistent.
- **Repeatability:** Three runs on the same holdout input produced identical output.
- **Specifiability:** Validate the output against `schemas/handoff.json`. Reject required fields that are missing, null, or empty.
- **Run rate:** Every workflow invocation: about 2 per day at the team estimate of 2 runs/day (`evidence/run-rate.txt`). High.
- **Preserved edge case:** Present-but-empty required fields are rejected by `scripts/validate_handoff_deterministic.py` and covered by `eval/test_deterministic_step.py`.

## Step: Path-Based Routing
- **Status:** Converted to deterministic sample (ADR-002), implemented in `scripts/route_task_deterministic.py`. This is a separate step from Orchestrator Routing below; the HO-05 runs do not test it.
- **Stability:** Not re-measured in this cycle.
- **Repeatability:** Deterministic code; covered by `eval/test_deterministic_router.py`.
- **Specifiability:** Explicit path rules with a default for unmatched paths.
- **Run rate:** Not yet measured from normal operational usage.
- **Preserved edge case:** Unmatched paths route to `implementer` instead of failing silently.
- **Recommendation:** Already deterministic.

## Step: Project Manager
- **What it does:** First role in every workflow run. It receives the raw task text from `eval/orchestrator.py` (plus an optional canary), is instructed to create a project entry with `write_entry`, and hands a brief to the Planner as a JSON object with `summary` and `citation_list`. Its output is the first handoff every downstream role consumes.
- **Stability — Partial.** Deterministic checks consistent across two calibration cycles (70/70 cycle 1, 84/84 cycle 2, 2026-10-17), but rubric quality is below threshold (46/80 = 57.5%, 59/96 = 61.5%) and several cycle-2 passes were vacuous (`evidence/calibration_results.md`).
- **Repeatability — Pass (structure only).** Three HO-02 runs: `diff` of the extracted output (`evidence/project_manager_run*_output.txt`) reported no differences (`evidence/repeatability_results.md`). Summary prose varied (55 / 62 / 87 words), and all three runs skipped the `write_entry` call the role prompt requires, so the output is consistent but consistently incomplete.
- **Specifiability — Partial.** The mechanical part can be specified: reject an empty task, create one project entry, forward the task text unchanged with no citations. The current spec (`evidence/spec_project_manager.md`) also asks it to "identify the objective and constraints" and summarize, which is prose synthesis and not specifiable in advance.
- **Run rate — High.** Every workflow run (6/6 holdout paths): 2 × 6/6 = 2.0 per day (`evidence/run-rate.txt`).
- **Known agent judgment / edge-case input:** An empty or whitespace-only task. In all three HO-05 repeat runs (`.eval-artifacts/runs/repeat/HO-05-run*.json`, `"task": ""`) the Project Manager asked for clarification instead of creating a project. A deterministic version must reject a blank task with a clear error, not create an empty project entry and pass it downstream.
- **Recommendation:** Weak candidate. Run rate is high and the structure is repeatable, but stability is only partial (rubric below threshold) and only the mechanical half of the step is specifiable. The repeatability result is also weaker than it looks: all three runs consistently skipped the entry write the role is supposed to perform, so a script reproducing current behavior would preserve a defect. First fix the skipped `write_entry` and get the rubric above threshold, then narrow the spec to the mechanical brief and re-measure. If the summary must stay prose, convert only the bounded substep (blank-task rejection plus entry creation) and keep the summary with an agent.
- **Candidate since:** 2026-10-17. **Next review:** 2026-11-18.

## Step: Planner
- **Stability:** Two cycles (2026-10-17): deterministic 70/70 (cycle 1, 5 tasks; HO-06 missing) and 84/84 (cycle 2, 6 tasks) — consistent. Rubric 46/80 (57.5%) and 59/96 (61.5%); tasks passing both layers 0/5 and 1/6. Scores are consistent across cycles but rubric quality is below threshold, and several cycle-2 passes were vacuous (see `evidence/calibration_results.md`).
- **Repeatability:** Not repeatable. Three runs on HO-02: runs 1–2 made no tool calls; run 3 made four `retrieve` calls. Summary length 43/29/102 words. Runs 1–2 also contradict the role prompt, which requires retrieving before planning.
- **Specifiability:** See `evidence/spec_planner.md`. Task decomposition and prioritization require judgment and synthesis.
- **Run rate:** Once per workflow run: 2 × 6/6 = 2.0 per day. High.
- **Known edge case:** A bug report lacks reproduction steps.
- **Recommendation:** Not a candidate. Needs judgment and synthesis to break a task into subtasks; output is not specifiable in advance. Consider converting narrowly defined substeps (e.g. "always retrieve first") as deterministic guards.
- **Reviewed:** 2026-10-17 against calibration cycles 1–2 and the HO-02 repeat runs; still not a candidate. **Next review:** 2027-01-21.

## Step: Implementer
- **Stability:** Two cycles (2026-10-17): deterministic 70/70 (cycle 1, 5 tasks; HO-06 missing) and 84/84 (cycle 2, 6 tasks) — consistent. Rubric 46/80 (57.5%) and 59/96 (61.5%); tasks passing both layers 0/5 and 1/6. Scores are consistent across cycles but rubric quality is below threshold, and several cycle-2 passes were vacuous (see `evidence/calibration_results.md`).
- **Repeatability:** Not repeatable. Three runs on HO-02: runs 1–2 made no tool calls; run 3 made two `retrieve` and two `write_entry` calls. Summary length 82/71/72 words. Whole-run durations were 18.0, 16.8, and 45.8 seconds.
- **Specifiability:** See `evidence/spec_implementer.md`.
- **Run rate:** Once per workflow run that includes implementation: 2 × 5/6 ≈ 1.7 per day. High.
- **Known edge case:** A planned file changes before implementation begins.
- **Recommendation:** Not a candidate. Not repeatable and requires judgment. Investigate the tool-call variation and consider automating bounded substeps.
- **Next review:** 2027-01-21.

## Step: Reviewer
- **Stability:** Two cycles (2026-10-17): deterministic 70/70 (cycle 1, 5 tasks; HO-06 missing) and 84/84 (cycle 2, 6 tasks) — consistent. Rubric 46/80 (57.5%) and 59/96 (61.5%); tasks passing both layers 0/5 and 1/6. Scores are consistent across cycles but rubric quality is below threshold, and several cycle-2 passes were vacuous (see `evidence/calibration_results.md`).
- **Repeatability:** Not repeatable. Three runs on HO-02 produced three different decisions: `blocker=reject`, no verdict, `planning_phase=approve`. Note: the HO-02 path uses role `reviewer`, which has no entry in `_ROLE_DESCRIPTIONS` or `GRANT_MAP` in `eval/orchestrator.py`, so it runs with a generic prompt and no tools.
- **Specifiability:** See `evidence/spec_reviewer.md`. Explicit acceptance criteria and mechanical checks can be specified, but broader review requires judgment.
- **Run rate:** Once per workflow run that includes review (twice for dual-review tasks): 2 × 4/6 ≈ 1.3 runs per day, about 1.7 reviewer invocations per day. High.
- **Known edge case:** A change meets functional acceptance criteria but introduces a security vulnerability.
- **Recommendation:** Not a candidate. Three runs gave three different decisions, and broader review requires judgment. Automate explicit checks while keeping judgment-based review.
- **Next review:** 2027-01-21.

## Step: Tester
- **Stability:** Two cycles (2026-10-17): deterministic 70/70 (cycle 1, 5 tasks; HO-06 missing) and 84/84 (cycle 2, 6 tasks) — consistent. Rubric 46/80 (57.5%) and 59/96 (61.5%); tasks passing both layers 0/5 and 1/6. Scores are consistent across cycles but rubric quality is below threshold, and several cycle-2 passes were vacuous (see `evidence/calibration_results.md`).
- **Repeatability:** Not repeatable. Three runs on HO-02: runs 1–2 made no tool calls and gave no verdict; run 3 called `read_entry` twice and returned `implementation=reject`.
- **Specifiability:** See `evidence/spec_tester.md`. In this harness the Tester does not execute tests — its only tool is `read_entry`; it reads the implementer's entry and judges it against the task.
- **Run rate:** Once per workflow run that includes testing: 2 × 4/6 ≈ 1.3 per day. High.
- **Known edge case:** An environment failure makes the result inconclusive.
- **Recommendation:** Not a candidate. Not repeatable, and the step is a judgment over the implementer's entry rather than test execution. Assess deterministic test execution separately from agentic interpretation of failures.
- **Next review:** 2027-01-21.

## Step: Orchestrator Routing
- **Stability:** Two cycles (2026-10-17): deterministic 70/70 (cycle 1, 5 tasks; HO-06 missing) and 84/84 (cycle 2, 6 tasks) — consistent. Rubric 46/80 (57.5%) and 59/96 (61.5%); tasks passing both layers 0/5 and 1/6. Scores are consistent across cycles but rubric quality is below threshold, and several cycle-2 passes were vacuous (see `evidence/calibration_results.md`).
- **Repeatability:** Unconfirmed end-to-end. The three HO-05 repeat runs (`.eval-artifacts/runs/repeat/HO-05-run*.json`) were started with an empty task (`"task": ""` in the first handoff), and the Project Manager asked for clarification in each. Their `diff` (`evidence/routing_run*_output.txt`) matched only because the old conflict rule never fired. The routing code itself is deterministic: the path comes from `--path`, and the conflict rule is covered by unit tests. The HO-05 runs must be repeated with the real task text.
- **Important finding:** The `False` result is repeatable but wrong in substance. In runs 1 and 2, `reviewer_strict` rejected and `reviewer_lenient` approved, but under different section names (e.g. `action_planning` vs `implementation`), so the exact-name match in `run_orchestrator` found no conflict. This is the residual gap already recorded in `docs/calibration-log.md` (2026-09-14).
- **Fix applied (2026-10-17):** Conflict detection now lives in `scripts/reviewer_conflict_deterministic.py`, shared by `eval/orchestrator.py` and the `reviewer_conflict` check in `eval/test_deterministic.py`. A run escalates when reviewers disagree overall, give opposite verdicts on the same section after name normalization, or return no or invalid verdicts. `eval/test_reviewer_conflict.py` covers the HO-05 case. Re-checking existing transcripts with the fixed checker: HO-05 repeat runs 1–2 and both calibration HO-05 runs now fail `reviewer_conflict` (13/14), which they previously passed vacuously; repeat run 3 still passes.
- **Specifiability:** See `evidence/spec_routing.md`. Already implemented as deterministic code: the path comes from `--path` and escalation is a fixed rule over reviewer verdicts.
- **Run rate:** Every workflow run: 2 × 6/6 = 2.0 per day. High.
- **Known edge case:** Review passes, but tests fail. Also: reviewers disagree under differently named sections.
- **Recommendation:** Weak candidate (closest to strong). Meets specifiability and run rate. Stability is only partially established (deterministic scores consistent across two cycles, rubric consistent but low), and end-to-end repeatability is unconfirmed because the HO-05 repeat runs had an empty task.
- **What must change to qualify as strong:**
  1. ~~Fix reviewer-conflict detection so sections are matched after name normalization.~~ Done 2026-10-17.
  2. ~~Add a regression test for disagreement under different section names.~~ Done: `eval/test_reviewer_conflict.py`.
  3. ~~Confirm the three HO-05 runs used the intended task text.~~ Checked 2026-10-17: they did not (empty task).
  4. Rerun HO-05 three times with the task text from `docs/holdout-task-set.md` (e.g. via `evidence/holdout.sh`) and `diff` the extracted path and escalation flag.
  5. Run one more calibration cycle with the fix in which HO-05's reviewers return non-empty verdicts and the rubric score clears the threshold.
- **Candidate since:** 2026-10-17. **Next review:** 2026-11-04.

## Step: Human Approval
- **Stability:** Not applicable to the human decision itself.
- **Repeatability:** Validate approval, rejection, and pending-state transitions.
- **Specifiability:** Require explicit authorized approval before protected actions proceed.
- **Run rate:** Not yet measured.
- **Known edge case:** Approval is missing or refers to an outdated change.
- **Recommendation:** Not a candidate. The human decision must stay human. Approval-state validation (present, current, authorized) can be automated separately.
- **Next review:** 2027-04-21 (approval-state validation substep only; the human decision stays human).

## Step: Release Note Draft
- **Stability:** Not measured in this cycle.
- **Repeatability:** Previously recorded as not repeatable across runs (prose output).
- **Specifiability:** Required sections and formatting can be specified. Content quality and completeness still require judgment.
- **Run rate:** Not yet measured.
- **Recommendation:** Not a candidate. Re-scoped on 2026-10-17 after more than two cycles as a weak candidate without new evidence: the full draft is prose that needs human review and has never been shown to be repeatable.
- **Narrower substep to assess separately:** a check that a draft has the required sections and formatting. That check is specifiable and repeatable by construction, but its run rate has not been measured.
- **Candidate since:** 2026-06-04. **Reviewed:** 2026-10-17 (re-scoped as above). **Next review:** 2027-01-21.

---

# Four-Signal Assessment

### Stability
Cycle 1 (2026-10-17, `.eval-artifacts/runs/calib-20261017-181805`): HO-01 to HO-05 each passed 14/14 deterministic checks (70/70). HO-06 crashed with `KeyError: 'classification'` in `_sim_write_entry` (the gap already recorded in `docs/calibration-log.md`, 2026-09-21). `eval/run_holdout.py` failed in the rubric judge call, so no rubric score was obtained. HO-05's `reviewer_conflict` pass is vacuous: both reviewers returned empty `review_items`. Details: `evidence/calibration_results.md`.

Cycle 2 (2026-10-17, `.eval-artifacts/runs/calib-20261017-183312`): all six tasks passed 14/14 (84/84). The rubric judge failed in the original shell; rerun from a separate shell it scored cycle 1 46/80 and cycle 2 59/96. Vacuous passes: HO-03 made no storage write, HO-05's reviewers again returned no verdicts, and the HO-06 Implementer made no tool calls.

Stability is partially established. Deterministic scores are consistent across both cycles (70/70, 84/84), but cycle 1 is missing HO-06, tool-use behavior changed between cycles, and rubric scores, while consistent (46/80 = 57.5%, 59/96 = 61.5%), leave only 0/5 and 1/6 tasks passing both layers.

### Repeatability
The recorded per-agent comparisons identify the following results:
* **Repeatable:** Project Manager (structure only).
* **Not repeatable:** Planner, Implementer, Reviewer, and Tester.
* **Unconfirmed:** Routing. The HO-05 repeat runs had an empty task.

Method: each step's role, tool-call sequence, output keys, verdicts, and decision were extracted with `evidence/extract_step.py` and compared with `diff`; summary length was compared separately. Results are in `evidence/repeatability-diff.txt` and `evidence/repeatability_results.md`.

In HO-02, runs 1–2 made zero tool calls in every role and run 3 made ten — the main source of variation. The HO-02 repeat runs used the correct task text. The HO-05 repeat runs did not (`"task": ""`), so the Routing comparison is not valid evidence and must be rerun (see Orchestrator Routing).

### Specifiability
Specifications are maintained in:
* `evidence/spec_project_manager.md`
* `evidence/spec_planner.md`
* `evidence/spec_implementer.md`
* `evidence/spec_reviewer.md`
* `evidence/spec_tester.md`
* `evidence/spec_routing.md`

Each specification must accurately describe the implemented behavior and be detailed enough for a developer unfamiliar with the workflow to implement the step without clarification.

### High Run Rate
Team estimate: 2 workflow runs per day (`evidence/run-rate.txt`). Step rates are runs per day × the share of holdout paths that include the step: Routing, Project Manager, Planner, and JSON Schema Validation 2.0/day; Implementer 1.7/day; Reviewer and Tester 1.3/day. Every assessed workflow step clears the high-run-rate threshold. Human Approval and Release Note Draft are not part of the holdout paths and remain unmeasured.

More than one execution per day is a clear high-run-rate signal under the exercise criteria. Less than one execution per week indicates a lower run rate.

---

# Strong Candidate Summary
* **Existing deterministic conversions:** JSON Schema Validation (ADR-001) and Path-Based Routing (ADR-002).
* **Repeatability passed:** Project Manager (structure only).
* **Repeatability unconfirmed:** Orchestrator Routing (HO-05 repeat runs had an empty task).
* **Repeatability failed:** Planner, Implementer, Reviewer, and Tester.
* **New strong candidate:** None. 10 steps assessed: 2 already deterministic, 2 weak candidates (Project Manager, Orchestrator Routing), 6 not candidates.
* **Closest candidate:** Orchestrator Routing. It meets specifiability and run rate (2.0/day), and the reviewer-conflict fix and regression test are in place. To qualify, it needs three HO-05 reruns with the real task that produce identical routing output, and one calibration cycle with non-empty reviewer verdicts and a rubric score above threshold (see Orchestrator Routing).
* **Next step:** Complete the missing evidence before recommending a new deterministic conversion.

---

# Next Actions
1. Verify existing calibration reports and record actual scores.
2. Preserve the three-run per-agent output comparisons and diff results.
3. ~~Confirm the validity of the three HO-05 task inputs.~~ Checked: empty task; rerun HO-05 ×3 with the real task text.
4. Review each specification against the implementation.
5. ~~Document normal operational run rates.~~ Done: 2 runs/day team estimate.
6. Update candidate recommendations when all four signals have evidence.
7. Commit the verified document.

> **Note:** Do not convert another agentic step until at least one new candidate meets all four signals. Preserve existing deterministic conversions, their edge cases, and their regression tests.