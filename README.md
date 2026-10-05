# circuit-claim-check

Checks whether a quantum circuit an AI agent says it built **is the circuit it was asked for**, with exact ground truth and no model in the loop.

Agents now write Qiskit code and call quantum MCP tools. A wrong circuit still runs: it returns measurement counts that look plausible, and nothing errors. The mistakes are specific and easy to make. Qiskit orders bits little-endian, so `|01>` means q[0]=1. A controlled-RZ is not a controlled-phase gate. The inverse QFT isn't the QFT. Control and target get swapped. This grades the circuit itself, not the agent's description of it.

> Status: **v0, grader and task sets only. No agent has been run yet.** The [preregistration](PREREGISTRATION.md) (hypotheses, metrics, pass bars) was committed before any agent run.

## How it grades

| Mode | Pass condition |
|---|---|
| `unitary` | The submission's operator equals the reference's, **up to a global phase** (`Operator.equiv`). A relative phase still counts. |
| `statevector` | The state reached from \|0…0> has fidelity ≥ 1 − 1e-6 with the reference's. |

Some tasks add constraints: `measure: require` (every qubit measured at the end), `measure: forbid`, or `allowed_gates` (e.g. "swap using only CNOTs"). Final measurements and barriers are stripped before comparing. A qubit that's measured and then used again fails as `mid_circuit_measurement`. Resets and classical control flow fail as `unsupported_op`.

Submissions can be OpenQASM 2, OpenQASM 3, or Qiskit Python that leaves the circuit in a variable named `qc`.

## Task sets

| Set | Tasks | Easy / medium / hard | Purpose |
|---|---|---|---|
| [`tasks/pilot.jsonl`](tasks/pilot.jsonl) | 30 | 8 / 14 / 8 | Used while building the grader |
| [`tasks/blind.jsonl`](tasks/blind.jsonl) | 15 | 4 / 6 / 5 | Written after the grader was committed, held out for results |
| [`tasks/v2.jsonl`](tasks/v2.jsonl) | 30 | 4 / 18 / 8 | Harder set for the self-checking question (condition A vs B, [Amendment 7](PREREGISTRATION.md)); committed before any agent saw it |

Each task is tagged with the trap it tests: endianness, global vs relative phase, QFT vs inverse QFT, control/target swap, measurement, multi-controlled gates, Grover/Bernstein-Vazirani oracles, parameterized rotations, gate-set limits.

## Results

| Run | Model, condition | Tasks | Passed | Claimed success but failed |
|---|---|---|---|---|
| [1](runs/run1/RESULTS.md) | Sonnet, no tools | v1 (45) | 45/45 | 0/45 |
| [2](runs/run2/RESULTS.md) | Haiku, no tools | v1 (45) | 28/45 (39 with missing header line added, post hoc) | 13/41 (2) |
| [3](runs/run4/RESULTS.md) | Haiku, no tools | v2 (30) | 7/30 (13 with header line added, preregistered) | 20/27 (14) |
| [4](runs/run4/RESULTS.md) | Haiku, draft → simulator feedback → final | v2 (30) | draft 18/30 → final 20/30 | draft 6/21 → final **8/28** |

**Main v2 finding:** one round of simulator feedback didn't reduce false success claims; they went from 6 to 8. In 4 of the 6 wrong drafts it claimed were right, the feedback showed the wrong behavior and the agent kept the same circuit and the same claim. Execution output isn't verification unless something compares it with the spec. The preregistered main hypothesis (H9) was not supported; details and limits in [`runs/run4/RESULTS.md`](runs/run4/RESULTS.md).

## Is the grader right?

The grader was tested without any model. Every task has a reference solution, at least two **mutants** (a specific plausible mistake each: reversed qubit order, flipped angle sign, swapped control, CRZ for CP, missing QFT swap), and at least one **variant** (a different but correct construction, such as a Clifford+T Toffoli or a gate that differs only by global phase).

| Set | References pass | Mutants killed | Variants pass |
|---|---|---|---|
| Pilot | 30/30 | 61/61 | 33/33 |
| Blind, first run, unedited | 15/15 | 30/30 | 15/15 |
| v2 | 30/30 | 60/60 | 30/30 |

Logs: [`evals/pilot_grader_check.txt`](evals/pilot_grader_check.txt), [`evals/blind_grader_check.txt`](evals/blind_grader_check.txt), [`evals/v2_grader_check.txt`](evals/v2_grader_check.txt). The 11 gate-limited v2 references are also checked against the named gate without the grader (`scripts/make_v2.py`).

What that does and doesn't show: the mutants were written by the same author as the grader, so a 100% kill rate means the grader catches the mistakes we thought of. It doesn't show it catches every mistake an agent will make. The real test is the first agent run.

## Run it

```bash
pip install qiskit qiskit-qasm3-import pytest
python grader.py tasks/blind.jsonl submissions.jsonl          # per-task PASS/FAIL + summary
python grader.py tasks/blind.jsonl submissions.jsonl --json   # machine-readable
pytest tests                                                   # grader validation
```

A submission line: `{"id": "b01", "code": "OPENQASM 2.0; ...", "claim": "Prepared |Psi->", "claimed_success": true}`. The summary reports **claimed success but failed**: the agent said it worked, and it didn't.

## Limits

- **Python submissions run in an OS sandbox, macOS only.** They are checked against a small allowed subset (imports only from qiskit, numpy, math, cmath, fractions; no `open`/`getattr`/`globals`-style names, no underscore or frame attributes, no classes, no attribute assignment), then run under `sandbox-exec` (`_sandbox.sb`): no network, no new processes, no file writes outside a throwaway scratch directory, stdin closed. The circuit comes back only as the runner's last stdout line, printed after the submission finishes. Red teams 1–3 got a wrong circuit graded `pass` by tampering with the runner from inside the submission, and all those routes are closed. Without `sandbox-exec` (Linux, Windows), Python submissions are refused (`python_needs_sandbox`) unless you set `CIRCUIT_GRADER_TRUST_PYTHON=1` for code you trust. OpenQASM needs no sandbox.
- **Barriers, delays and measurements are recognized by type, not name.** Red team 4 hid a real X gate inside a custom gate named `barrier`, and the grader dropped it as a no-op (5 wrong circuits graded `pass`). A gate named `measure` likewise counted as a measurement. Both now go through the normal gate checks.
- **Exact comparison builds full matrices,** so it's practical up to roughly 10–12 qubits. Every task here uses 4 or fewer.
- **Statevector tasks grade the output, not the method.** "Prepare GHZ" passes with any circuit that reaches GHZ. Tasks where the method matters are graded as unitaries.
- **Ancillas.** Up to 3 extra qubits after the task's qubits are allowed if they start and end in |0> for every input and are never measured (`dirty_ancilla`, `ancilla_measured`, `too_many_ancillas` otherwise). More would make the full unitary too large to build exactly.
- **Small and single-author.** 45 tasks, all written by one model family.
