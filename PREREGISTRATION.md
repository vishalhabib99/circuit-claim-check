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

## Cost and approval

Vishal has no paid API access (Claude Code Pro only). **No agent run starts without his explicit approval**, including which models and conditions. One full condition-A run is 45 prompts.
