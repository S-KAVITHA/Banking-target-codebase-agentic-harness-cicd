---
name: project_manager
description: >
 First role in every eval-harness workflow run. Takes the raw task, is
 instructed to create a project entry in the store, and hands a brief to
 the Planner. Under assessment for deterministic conversion of its intake
 substep (ADR-003, Proposed).
model: anthropic/claude-haiku-4.5   # via OpenRouter, eval/orchestrator.py MODEL

tools:
 - write_entry
 - read_entry
 - list_entries

disallowedTools:
 - retrieve
 - update_entry
 - delete_entry

max_tokens: 2048
max_tool_iterations: 10
version: 1.0.0
---

# Project Manager (eval-harness role)

This file documents the `project_manager` role as it currently runs in
`eval/orchestrator.py`. It does not define a new agent. The source of truth
is the code:

- Prompt: `_ROLE_DESCRIPTIONS["project_manager"]` (`eval/orchestrator.py`, line 360)
- Tool grant: `GRANT_MAP["project_manager"]` (`eval/orchestrator.py`, line 59), mirrored in
  `docs/routing-and-tool-grant-map.json`
- Output format: `_FINALIZE_INSTRUCTIONS` (`eval/orchestrator.py`)

It is separate from `agents/project-manager.md`, which defines the banking
workflow's issue-status updater (invoked last, `task_tracker` tool).

## Instructions

Role prompt, verbatim:

> You are the Project Manager. Understand the task and create a project entry
> in the store, then hand off a clear brief to the next agent.

The orchestrator adds the task text (`Task: <task>`), the optional canary block
on step 1, and the shared finalize instructions. The role receives no
handoff, because it runs first.

## Orchestration context

- Invoked by: `run_orchestrator`, as step 1 of every role path in
  `docs/holdout-task-set.md` (6 of 6 holdout tasks).
- Input: the raw task text from `--task`, and optionally a canary string.
- Output: a final JSON block with `handoff` (one or two sentences for the
  Planner), `output_document` (`summary`, `citation_list`), and an empty
  `review_items` list.
- Hands off to: Planner.
- Loops back to: nothing. The orchestrator does not stop the run if this role
  asks for clarification.

## Observed behavior (evidence for ADR-003)

- Repeatable in structure across three HO-02 runs, but all three skipped the
  `write_entry` call the prompt requires (`evidence/repeatability_results.md`).
- With an empty task (HO-05 repeat runs, `"task": ""`), it asked for
  clarification instead of writing an entry. The workflow still continued
  downstream (run 1 reached the Implementer, both reviewers, and the Tester).

## Known governance conflict

`docs/governance-policy.md` (Role: project-manager) sets `write_entry` to NO,
while the grant above and the role prompt allow and require it. ADR-003 lists
resolving this conflict as a precondition for conversion.
