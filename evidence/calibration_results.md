# Calibration Results

## Calibration Cycle 1
- **Run folder:** `.eval-artifacts/runs/calib-20261017-181805/`
- **Date:** 2026-10-17
- **Status:** Partially completed; HO-06 failed during orchestration.

---

## Deterministic Holdout Results
* **HO-01:** 14/14 checks passed.
* **HO-02:** 14/14 checks passed.
* **HO-03:** 14/14 checks passed.
* **HO-04:** 14/14 checks passed.
* **HO-05:** 14/14 checks passed.
* **HO-06:** Failed before producing a complete transcript because the write operation encountered a missing classification field.

**Aggregate** (`evidence/calib-20261017-181805-holdout.txt`): 70/70 deterministic checks across 5 tasks. Rubric suite 46/80, with 9/20 dimension checks passing threshold. Tasks passing both layers: 0/5. The rubric judge failed in the original run; this score comes from rerunning `eval/run_holdout.py` from a separate shell.

**Vacuous pass:** HO-05 `reviewer_conflict` passed because both reviewers returned empty `review_items`.

---

## Calibration Cycle 2
- **Run folder:** `.eval-artifacts/runs/calib-20261017-183312/`
- **Date:** 2026-10-17
- **Status:** Completed; all six holdout tasks produced transcripts.

## Deterministic Holdout Results
Source: `evidence/calib-20261017-183312-score.txt`
* **HO-01:** 14/14 checks passed (11.6s).
* **HO-02:** 14/14 checks passed (42.2s).
* **HO-03:** 14/14 checks passed (13.7s).
* **HO-04:** 14/14 checks passed (26.6s).
* **HO-05:** 14/14 checks passed (24.4s).
* **HO-06:** 14/14 checks passed (27.5s).

**Aggregate** (`evidence/calib-20261017-183312-holdout.txt`): 84/84 deterministic checks across 6 tasks. Rubric suite 59/96, with 14/24 dimension checks passing threshold. Tasks passing both layers: 1/6.

**Vacuous passes** (verified from the run transcripts):
* **HO-03:** No storage write; the only tool calls were four Planner `retrieve` calls.
* **HO-05:** `reviewer_strict` and `reviewer_lenient` both returned empty `review_items`, so `reviewer_conflict` had nothing to compare.
* **HO-06:** The Implementer made no tool calls.

---

## Stability Assessment
| Cycle | Tasks | Deterministic | Rubric | Both layers |
|---|---|---|---|---|
| 1 | 5 (HO-06 failed) | 70/70 | 46/80 (57.5%) | 0/5 |
| 2 | 6 | 84/84 | 59/96 (61.5%) | 1/6 |

Stability is partially established. Deterministic scores are consistent across both cycles, and rubric scores are consistent with each other but below threshold. Cycle 1 is missing HO-06, and tool-use behavior changed between cycles. Several passes in both cycles were vacuous.

---

## Known Issues
* HO-06 failed in cycle 1 with a missing classification input; it completed in cycle 2, but the root cause was not confirmed fixed.
* The rubric judge failed in the original shell for both cycles; scores above come from a rerun in a separate shell.
* No rubric score should be inferred from the deterministic check results.
* HO-05's reviewer-conflict check passed vacuously in both cycles (empty `review_items`). With the fixed rule in `scripts/reviewer_conflict_deterministic.py`, both HO-05 transcripts now score 13/14 because their reviewers gave no verdicts and the run was not escalated. The 70/70 and 84/84 above are the scores recorded at the time.

---

## Next Actions
1. Confirm the root cause of the cycle 1 HO-06 missing-classification failure.
2. Rerun HO-05 with the intended task explicitly supplied (the three repeat runs had an empty task).
3. ~~Fix reviewer-conflict detection so empty or differently named review items cannot pass vacuously.~~ Done 2026-10-17.
4. Run a third calibration cycle after those fixes and compare against cycles 1 and 2.