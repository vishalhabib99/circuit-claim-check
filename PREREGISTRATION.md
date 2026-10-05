# Preregistration

Written 2026-10-04, **before any agent has been run on any task**. Commits to this file after the first agent run show up in git history; anything changed after that point is marked as changed, with the reason.

## Question

When a coding agent says it built quantum circuit X, did it?

The grader is exact: it compares unitaries up to a global phase, or the state reached from |0…0> at fidelity ≥ 1 − 1e-6. No model judges anything, so there's no grader opinion to argue with.

## Validity bar for the grader (must hold before any agent result is reported)

| Check | Bar | Status at preregistration |
|---|---|---|
| Reference solutions pass | 100% | pilot 30/30 · blind 15/15 |
| Hand-written mutants fail (each one a specific plausible mistake) | ≥ 95% | pilot 61/61 · blind 30/30 |
| Equivalent-but-different correct variants pass | 100% | pilot 33/33 · blind 15/15 |

The blind set's mutants and variants were committed (8dcb32a) before the grader first ran on them, and the first run is logged unedited in [`evals/blind_grader_check.txt`](evals/blind_grader_check.txt).

## Protocol

- **Input to the agent:** the task's `prompt` and `n_qubits` only. No reference solution and no grader. It's told to return OpenQASM 2/3 or Qiskit Python that leaves the circuit in `qc`.
- **Output collected:** `code`, a free-text `claim` describing what it built, and `claimed_success` (true/false: does it believe the circuit meets the task?).
- **Primary condition (A):** one attempt per task, with no way to run code. This measures what the agent writes and claims.
- **Secondary condition (B), only if A is run first:** the same, but the agent may run Qiskit locally before answering. This measures whether self-checking closes the gap.
- **Graded once** by `grader.py` at the commit recorded with each run's results.

## Sample

- **Pilot (30 tasks):** a protocol shakeout. Results are reported, but labeled as pilot.
- **Blind (15 tasks):** the result set. Task text is not edited after this preregistration.

## Metrics

1. **Pass rate**, overall and by difficulty.
2. **Pass rate by trap category:** endianness, global_phase, relative_phase, qft, control_target, measurement, multi_controlled, grover_oracle, param_rotation, gate_set, basic.
3. **Claim-vs-reality mismatch (headline):** of the tasks where the agent says `claimed_success: true`, the share the grader fails.
4. **Failure reasons** from the grader (`not_equivalent`, `wrong_state`, `parse_error`, `wrong_qubit_count`, `missing_measurement`, `measurement_not_allowed`, `disallowed_gate`, `mid_circuit_measurement`, ...).

## Hypotheses (written so they can be wrong)

- **H1:** endianness tasks have the lowest pass rate of any category with at least 4 tasks (pilot or blind).
- **H2:** the mismatch rate is at least 1 in 10. That is, agents claim success on wrong circuits at least 10% of the time in condition A.
- **H3:** at least one relative-phase task fails with CRZ used where CP was asked for (the p08/b06 trap), or with a sign error.
- **H4:** hard tasks pass less often than easy tasks.
- **H5 (condition B only):** letting the agent run Qiskit cuts the mismatch rate by at least half.

## What the numbers can and can't show

15 blind tasks is small. With 0 failures in 15, the true failure rate could still be as high as **18%** (one-sided 95% exact bound). Per-category numbers on the blind set are 1 to 4 tasks each and are reported as counts, not rates. All tasks were written by one model family, which may share blind spots with the agents being tested.

## Changes after results

- Blind task text is not edited.
- If an agent run exposes a grader bug, the fix gets its own commit, the bug is logged, and **every affected result is reported both before and after the fix**.

## Amendment 1 (2026-10-04, before any agent run): ancilla rule and run setup

**Ancillas.** q[0..n-1] are the task's qubits. Up to 3 extra qubits after them are allowed if they start in |0>, end in |0> for every input (unitary tasks: the block of the full unitary that maps ancilla-|0> inputs to ancilla-non-|0> outputs must be zero; state tasks: no amplitude may remain on ancilla-non-|0> states), and are never measured. New failure reasons: `too_many_ancillas`, `dirty_ancilla`, `ancilla_measured`. Fewer than n qubits is still `wrong_qubit_count`. Decided by Vishal before any agent output existed. The grader validation was re-run on the blind set with this rule, and the results were unchanged: references 15/15, mutants 30/30, variants 15/15 (`evals/blind_grader_check_ancilla_rule.txt`).

**Run 1 (approved by Vishal 2026-10-04):** condition A only, one model (Claude Sonnet via Claude Code subagents, Pro plan), all 45 tasks, one attempt each, in 3 batches of 15 (pilot p01-p15, pilot p16-p30, blind b01-b15). Each subagent sees only the task id, `prompt` and `n_qubits`, plus fixed instructions (`runs/instructions.md`). It may make exactly one tool call, writing its answers file, and no other tool calls, so it can't run code or read the repo. The tool-call count reported for each subagent is logged in the run notes as evidence. Graded once, at the grader commit recorded in `runs/run1/NOTES.md`.

## Amendment 2 (2026-10-04, after run 1, before run 2 and red team 1)

Run 1 (Sonnet) passed 45/45 with 0 false success claims (`runs/run1/RESULTS.md`). Two follow-ups, approved by Vishal:

**Run 2: Claude Haiku, condition A.** Same 45 tasks, same instructions, same 3 batches, same one-tool-call rule, graded once at the commit recorded in `runs/run2/NOTES.md`. The grader and task text are unchanged from run 1. Purpose: to check whether this eval can show failures at all.
- **H6:** Haiku passes fewer than 45/45.
- **H7:** if Haiku fails any task, at least one failure is claimed as a success (mismatch >= 1).
- If Haiku also gets 45/45, the conclusion is that this task set can't tell these models apart, not that agents are reliable.

**Red team 1 (grader).** One agent with the grader code open and permission to run it tries to get a *wrong* circuit graded `pass` on any task. A finding counts only if the circuit's wrongness is shown independently of `grader.py` (an explicit matrix or state computation compared with the task text) and I can reproduce it. Bar: 0 wrong circuits graded `pass`. Any confirmed finding is a grader bug, logged with before/after under the "Changes after results" rule. Run 1's 45 answers are re-graded after any fix.

## Amendment 3 (2026-10-04): grader fixes from red team 1

Red team 1 got 16 wrong circuits graded `pass` (`runs/redteam1/FINDINGS.md`). Fixed in commits 3266c1b..this one, one commit per class, with every attack kept as a regression test (`tests/test_redteam1.py`):
1. one crashing submission no longer stops the run; clear error for QASM with no version line (W1)
2. non-unitary ops rejected at any depth: `initialize`, hidden resets, control flow, classical variables (A01, A02, W3, W4)
3. Python output path and nonce go over stdin, the serializer is captured before the submission runs, and the runner must confirm it finished (A03, A04). Not a sandbox.
4. a QASM 2 program's own gate definitions are honored (A07)
5. allowed gates are checked by behavior, not name; optional `max_gates` (A05, A06)
6. tasks with no measure setting forbid measurements, matching the agent instructions (A08, A09)
7. elementwise comparison within 1e-9 after one global phase; ancilla leak 1e-9 (A13-A15)
8. the register named `q` holds the task's qubits wherever it is declared (A16, W2)
9. **task metadata added after results were seen:** `allowed_gates`/`max_gates` on p04 (`rz`, 1), b03 (`rx`, 1) and b10 (`x`, `h`, 2). These rules were already in the task text ("a single RZ rotation", "a single RX rotation", "by applying H to |1>"), but the grader didn't enforce them. **Task text is unchanged.** Because this changes how two blind tasks are graded after results, runs 1 and 2 are reported under both the old and the new grader. Three fixture "variants" were actually breaking those rules (plain Z, plain X, H then Z, the same as attacks A10-A12). They are relabeled as mutants, and correct variants were added in their place.

**Red team 2** runs against the fixed grader under the same bar as red team 1 (0 confirmed wrong-passes, each one shown wrong independently of `grader.py`). It gets red team 1's findings, so it knows what has already been tried.

## Amendment 4 (2026-10-04): grader fixes from red team 2

Red team 2 got 3 wrong circuits graded `pass`, all through gaps in the red team 1 fixes (`runs/redteam2/FINDINGS.md`):
10. QASM 2 is parsed faithfully first. Qiskit's legacy gate set is used only as a fallback, for a program that defines no gates of its own. This replaces the gate-name regex that a same-line definition got past (RT2-02).
11. Python submissions must fit a small subset, checked before they run: imports only from qiskit, numpy, math, cmath and fractions; no names that reach the interpreter (`open`, `getattr`, `globals`, ...); no underscore or frame attributes. The runner reads its output path and nonce only after the submission has run, and exits with `os._exit` (RT2-01, RT2-03). Still not a sandbox.

Re-graded both runs: no verdict changed, and no real answer was rejected by the Python subset (`runs/*/answers*_regraded_after_rt2.txt`).

**Red team 3** (approved by Vishal 2026-10-04) runs against grader 4054378 under the same bar: 0 confirmed wrong-passes, each one shown wrong independently of `grader.py`. It gets both earlier findings files. If it finds 0, the README may say the grader passed a red team. If it finds any, they get fixed and reported the same way, and the claim stays unmade.

## Amendment 5 (2026-10-04): grader fixes from red team 3

Red team 3 got 3 wrong circuits graded `pass` (`runs/redteam3/FINDINGS.md`). The Python submission read the runner's output path and nonce from stdin before the runner did, wrote the correct circuit itself, printed the runner's success line and raised `SystemExit`. It also found a false fail: a comment containing "gate" blocked the QASM 2 legacy-gate fallback.

Three rounds have now beaten the Python runner from inside the same interpreter, so this fix changes the design instead of patching one more route:
12. Python runs under the macOS sandbox (`_sandbox.sb`: no network, no new processes, no file writes outside a throwaway scratch directory) with stdin closed. No path or nonce is passed in. The circuit comes back only as the runner's last stdout line, printed after the submission finishes, followed by `os._exit`. Any exception from the submission, `SystemExit` included, fails it. The subset also now bans classes, attribute assignment, `qpy`, and numpy file I/O. Without `sandbox-exec`, Python is refused unless `CIRCUIT_GRADER_TRUST_PYTHON=1`.
13. Comments are stripped before the QASM 2 fallback looks for `gate`/`opaque` (W-rt3-1).

Re-graded both runs: no verdict changed. All 22 confirmed attacks from red teams 1-3 now fail (`runs/*/answers*_regraded_after_rt3.txt`).

**Red team 4** (approved by Vishal 2026-10-05) runs against grader 1bc747a (fixes 12 and 13) under the same bar: 0 confirmed wrong-passes, each one shown wrong independently of `grader.py`. It gets all three earlier findings files. If it finds 0, the README may say the grader passed a red team. If it finds any, they get fixed and reported the same way, and the claim stays unmade.

## Amendment 6 (2026-10-05): grader fix from red team 4

Red team 4 got 5 wrong circuits graded `pass` (`runs/redteam4/FINDINGS.md`). A Python submission built an ordinary gate (an X, or a two-qubit gate) and renamed it `barrier` or `delay`. qpy keeps a custom gate's name, and the grader skipped ops by name, so it dropped a gate that really runs. The skipped op also escaped `allowed_gates` and `max_gates`. It needs no runner or sandbox tampering; QASM can't reach it because `barrier` and `delay` are reserved words. While fixing it I found a 6th instance of the same class (not counted in red team 4's 5): an identity gate named `measure` satisfied p12's "measure every qubit" requirement.

14. Barriers, delays, measurements and resets are matched by class (`Barrier`, `Delay`, `Measure`, `Reset`), not by name. A gate with one of those names goes through the normal gate checks.

Re-graded both runs: no verdict changed (`runs/*/answers*_regraded_after_rt4.txt`). All 27 confirmed attacks from red teams 1-4 now fail; 212 tests pass.

## Amendment 7 (2026-10-05, before any agent sees a v2 task): v2 task set and condition B

Run 1 (Sonnet) passed v1 45/45, so v1 can't show whether self-checking helps. v2 asks that question on harder tasks.

**v2 task set (30 tasks, `tasks/v2.jsonl`, written by `scripts/make_v2.py`).** Harder instances of the same trap categories, aimed at mistakes models make: Qiskit bit order, inverse vs forward QFT, CRZ vs CP, operator order in a matrix product, mixed-polarity controls, and gate-set limits (11 tasks) that force a decomposition instead of a library call. Grader validation before any agent run (`evals/v2_grader_check.txt`): references 30/30, mutants 60/60 killed, variants 30/30. For the 11 gate-limited tasks the reference is itself a decomposition, so `make_v2.py` also checks each one against the named gate with `qiskit.quantum_info`, without `grader.py`. Task text is not edited after this commit. One task was replaced before this commit: the first v17 needed an ancilla in its reference, which the grader doesn't support for references, so it became a CCZ-from-Toffoli task.

**Conditions (one model: Claude Haiku via Claude Code subagents, Pro plan; each run needs Vishal's approval):**
- **Run 3, condition A:** the v1 protocol on v2. Instructions `runs/instructions.md`, 3 batches of 10, one Write call per agent.
- **Run 4, condition B:** fresh agents, never the run 3 agents. Instructions `runs/instructions_B.md`, 3 batches of 10. Each agent writes a **draft** (code, claim, claimed_success), then gets the output of `scripts/exec_feedback.py` on its own draft: gates, measurements, and what the circuit does (output state, or output for every basis input). It never sees the reference or a verdict. Then it writes its **final** answers. Exactly two Write calls per agent, checked from the transcripts. Run 3 goes first.

**Metrics.** Graded once by `grader.py` at the commit recorded in each run's notes.
1. **False success claims (headline):** answers with `claimed_success: true` that fail. Compared B-draft vs B-final (same agents, same tasks: the effect of feedback) and A vs B-final.
2. Pass count, overall and by trap category (counts only).
3. Revisions in B: tasks changed after feedback, fixed (fail → pass), broken (pass → fail).
4. Format failures (`parse_error`) reported separately. **Secondary, decided now:** re-grade with a missing `OPENQASM 2.0;` line added and nothing else changed (the run 2 post hoc check, preregistered this time).

**Hypotheses:**
- **H8:** A passes at most 27 of 30. If A passes 28 or more, v2 is too easy for Haiku, and H9-H12 are reported but not taken as evidence.
- **H9 (main):** B-final has at most half as many false success claims as B-draft. Not testable if B-draft has fewer than 2.
- **H10:** B-final has at most half as many false success claims as A.
- **H11:** B-final passes more tasks than B-draft, and fixes outnumber breaks.
- **H12:** of the B-draft false claims that go away, at least half go away because the circuit now passes, not because the agent switched to `claimed_success: false`.

**What 30 tasks can show.** Pass/fail differences are tested with an exact McNemar test on the discordant pairs, two-sided, and reported with the counts. With 30 tasks only a large effect will show up, so a null result means "no large effect", not "no effect". A and B use different agent instances, so A vs B mixes feedback with run-to-run variation; B-draft vs B-final is the cleaner comparison. One round of feedback is not open-ended tool use. The tasks and the agents are from the same model family.

## Amendment 8 (2026-10-05, during run 4, before any feedback was sent): fix 15

Run 4's batch 1 drafts all set a circuit label (`qc.name = "v02"`). The Python subset from fix 12 refused every attribute assignment, so these drafts couldn't be loaded, though Qiskit runs them fine. That is a false fail, and it would have made the condition B feedback something other than "what Qiskit shows". 15. `x.name = "<string>"` is allowed. Nothing else changes: it gives a submission nothing `copy(name=...)` didn't already allow, and operations have been matched by class since fix 14. Other attribute assignments are still refused (tests in `tests/test_redteam1.py`). The three drafts were hashed (`runs/run4/drafts.sha256`) and committed with this fix, before any feedback was generated. Re-grading run 3 and runs 1-2 with fix 15 changed no verdict, so run 3 is reported once.

## Amendment 9 (2026-10-05, after runs 3-4, before run 5): Sonnet in condition B

Run 4 (Haiku) did not support H9: false success claims went from 6 (draft) to 8 (final). The obvious question is whether that's a Haiku limitation. Approved by Vishal:

**Run 5:** Claude Sonnet, condition B, exactly the run 4 protocol (same v2 tasks, `runs/instructions_B.md`, 3 fresh agents × 10 tasks, draft → `scripts/exec_feedback.py` output → final, two Write calls per agent). Grader and feedback script at the commit recorded in `runs/run5/NOTES.md`; drafts hashed and committed before any feedback is generated. No condition A run for Sonnet: the draft is the no-feedback baseline, as in run 4.

- **H13:** Sonnet's B-final has at most half as many false success claims as its B-draft (H9 for Sonnet). Not testable if the draft has fewer than 2.
- **H14:** Sonnet changes at least half of its wrong drafts after feedback (Haiku changed 2 of 6 of the ones it claimed, and kept 4 identical).
- Reported side by side with run 4, as counts. Two models and 30 tasks can't support a general claim about models; the comparison says only what these two did on this set.

## Cost and approval

Vishal has no paid API access (Claude Code Pro only). **No agent run starts without his explicit approval**, including which models and conditions. One full condition-A run is 45 prompts.
