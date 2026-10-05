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

Each task is tagged with the trap it tests: endianness, global vs relative phase, QFT vs inverse QFT, control/target swap, measurement, multi-controlled gates, Grover/Bernstein-Vazirani oracles, parameterized rotations, gate-set limits.

## Is the grader right?

The grader was tested without any model. Every task has a reference solution, at least two **mutants** (a specific plausible mistake each: reversed qubit order, flipped angle sign, swapped control, CRZ for CP, missing QFT swap), and at least one **variant** (a different but correct construction, such as a Clifford+T Toffoli or a gate that differs only by global phase).

| Set | References pass | Mutants killed | Variants pass |
|---|---|---|---|
| Pilot | 30/30 | 61/61 | 33/33 |
| Blind, first run, unedited | 15/15 | 30/30 | 15/15 |

Logs: [`evals/pilot_grader_check.txt`](evals/pilot_grader_check.txt), [`evals/blind_grader_check.txt`](evals/blind_grader_check.txt).

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

- **Python submissions are not sandboxed for security.** They run in a separate `python -I` process with a stripped environment, a temp working directory and a 60-second timeout. That stops hangs and accidental state leaks. It does not stop a hostile submission from reading files or using the network. Only grade code you'd run yourself.
- **Exact comparison builds full matrices,** so it's practical up to roughly 10–12 qubits. Every task here uses 4 or fewer.
- **Statevector tasks grade the output, not the method.** "Prepare GHZ" passes with any circuit that reaches GHZ. Tasks where the method matters are graded as unitaries.
- **Exact qubit count.** A correct circuit that uses an extra ancilla fails as `wrong_qubit_count`.
- **Small and single-author.** 45 tasks, all written by one model family.
