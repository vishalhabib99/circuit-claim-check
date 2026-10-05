# Red team 1: grader findings

Grader and tasks unchanged (qiskit 2.5.2). Nothing outside `runs/redteam1/` was edited. No commits.

Files:
- `make_attacks.py` writes `attacks.jsonl` (A = attack expected to pass, F = attack expected to be caught) and `crash_*.jsonl`.
- `grade_output.txt` is `grader.py all_tasks.jsonl attacks.jsonl` (`all_tasks.jsonl` = pilot + blind concatenated). Rows are in the same order as `attacks.jsonl`.
- `verify.py` / `verify_output.txt`: independent check that does **not** import grader.py. It builds each circuit and computes its matrix, state or density matrix with `qiskit.quantum_info`/numpy, or lists its instructions for constraint checks.
- `rate.sh` / `rate_output.txt`: how often the random attacks A01/A02 pass.

Reproduce: `cd runs/redteam1 && $PY make_attacks.py && $PY ../../grader.py all_tasks.jsonl attacks.jsonl && $PY verify.py`

## Attempts

| # | Task | Attack | grader.py | Independent result | Confirmed wrong-pass? |
|---|---|---|---|---|---|
| A01 | p02 | `initialize('0')` on an ancilla entangled with q0 (q0 = 0.1\|0>+0.995\|1>). Initialize contains a reset that the top-level scan misses, and Statevector.evolve collapses it at random | PASS 20/20 | Output is mixed: fidelity with \|01> is 0.99, purity 0.98 | **YES** |
| A02 | p02 | Reset hidden inside a custom instruction (`clean`), with the ancilla holding a CNOT copy of an H'd q0 | PASS 10/20 (random) | Mixed state, fidelity 0.5 with \|01> | **YES** (nondeterministic) |
| A03 | p06 | Python writes the correct circuit to the runner's QPY path (`sys.argv[2]`), sets a wrong `qc`, then `os._exit(0)` | PASS | `qc` = CX(0→1), not CX(1→0); max entry diff 1.0 | **YES** |
| A04 | p06 | Python monkeypatches `qiskit.qpy.dump` so the runner saves a different circuit than `qc` | PASS | Same as A03 | **YES** |
| A05 | p14 | `Gate('cx')` whose definition is a SWAP: gate-name check only | PASS | The one "cx" has the SWAP matrix and is not a CNOT. Breaks "using only CNOT gates" | **YES** (constraint) |
| A06 | b12 | QASM 3 user gate `gate cx a,b { ctrl @ U(0,0,pi) a,b; }` = CZ | PASS | The "cx" has the CZ matrix, not CNOT. No H or CNOT used. Breaks "only H and CNOT" | **YES** (constraint) |
| A07 | b12 | QASM 2 without include: the program defines `h`=U(0,0,pi) (=Z) and `cx`=identity. `LEGACY_CUSTOM_INSTRUCTIONS` silently swaps in the real H/CX | PASS | Parsed with the program's own definitions (strict `qasm2.loads`), U = I, not CZ | **YES** |
| A08 | p06 | Final measurement of both qubits on a unitary task (`measure` defaults to "allow") | PASS | Circuit has 2 measurements and is not a unitary. Breaks "Don't add measurements unless the task asks" | **YES** (rule) |
| A09 | p01 | Same on a statevector task | PASS | Same | **YES** (rule) |
| A10 | p04 | `z q[0]` for "using a single RZ rotation" | PASS | ops = [z] | **YES** (constraint) |
| A11 | b03 | `x q[0]` for "using a single RX rotation" | PASS | ops = [x] | **YES** (constraint) |
| A12 | b10 | `h; z` for "Prepare \|-> by applying H to \|1>" | PASS | ops = [h, z]; H is never applied to \|1> | **YES** (constraint) |
| A13 | p03 | Extra `ry(1.9e-3)`: statevector check is fidelity ≥ 1-1e-6, so amplitude errors near 1e-3 pass | PASS | Max amplitude diff 6.7e-4, fidelity 0.9999991 | **YES** (tolerance) |
| A14 | p05 | `ry(pi/3 + 9e-6)`: `Operator.equiv` default rtol 1e-5 | PASS | max\|U−RY(π/3)\| = 3.9e-6 | **YES** (tolerance, minor) |
| A15 | p03 | Ancilla rotated by RY(1.9e-6) and never returned (LEAK_TOL 1e-6) | PASS | Ancilla \|1> amplitude 9.5e-7 | **YES** (tolerance, minor) |
| A16 | p02 | `qreg r[1]; qreg q[2]; x r[0];`. The grader uses position, not the name `q` | PASS | The register named q is \|00> (task wants q[0]=1), and the extra register r ends in \|1> | **YES**, depends on reading: the instructions name the task qubits `q[0..n-1]` |
| F01 | p02 | Reset inside `box` (BoxOp is not in the grader's control-flow list) | FAIL simulation_error | (caught by Operator, but the reason label is wrong) | no |
| F02 | p11 | Ancilla dirty only when q0=q1=1 | FAIL dirty_ancilla | — | no |
| F03 | p12 | Ancilla measured into a separate creg | FAIL ancilla_measured | — | no |
| F04 | p13 | Measurement on a "forbid" task | FAIL | — | no |
| F05 | p06 | Opaque gate | FAIL simulation_error | — | no |
| F06 | p05 | Unbound Parameter | FAIL simulation_error | — | no |
| F07 | p01 | QASM 3 `if (c[0]) x` | FAIL unsupported_op | — | no |
| F08 | p12 | Mid-circuit measure, then reuse | FAIL mid_circuit_measurement | — | no |
| F09 | p01 | Explicit QASM 3 `reset` | FAIL unsupported_op | — | no |
| F10 | p14 | QASM 2 macro `myswap` | FAIL disallowed_gate | — | no |
| F11 | b12 | QASM 2 macro `cx2` wrapping cz | FAIL disallowed_gate | — | no |
| F12 | p25 | Ancilla phase-kickback circuit that gives Z instead of Sdg | FAIL not_equivalent | — | no |
| F13 | p01 | Ancilla leak 1.5e-6 (just over tolerance) | FAIL dirty_ancilla | — | no |
| F14 | p08 | Wrong relative phase (S on q1 vs CP(π/2)) | FAIL not_equivalent | — | no |
| C01 | p01 | Non-measure instruction with a clbit | **grader crashes** (uncaught CircuitError) | — | no (weakness W1) |
| C02 | p01 | Classical `Var` + `store` | **grader crashes** | — | no (W1) |
| C03 | p01 | Measure inside a custom instruction | **grader crashes** | — | no (W1) |

## Root causes (for the fix)

1. **Hidden non-unitary ops (A01, A02).** `_final_measure_split` scans only top-level `qc.data` by name. `initialize` and any custom instruction can hold `reset`. In statevector mode, `Statevector.evolve` applies the reset by sampling with an unseeded RNG, so a wrong mixed state can pass, and the same submission can get different grades on different runs. Fix: recursively decompose (or `transpile` to a basis) before scanning, and reject any op that has no unitary (`reset`, `measure`, `initialize`, `store`, `box`, anything with clbits) below the top level.
2. **Python output isn't tied to `qc` (A03, A04).** The submission runs in the same interpreter as `_runner.py` and can write the output file itself or patch `qpy.dump`. Fix: have the runner write to a path the submission doesn't know (for example, pass it on an inherited fd or after exec) and bind `qpy.dump` before running the submission. A child process can still lie to its parent in the end, so the real fix is a sandbox or not accepting Python.
3. **Gate-set check is by name only (A05, A06).** Fix: for tasks with `allowed_gates`, require each op to be the standard library class (`isinstance(op, CXGate)` etc.) or check that the op's matrix equals the standard gate's matrix.
4. **QASM 2 legacy mode overrides user definitions (A07).** `LEGACY_CUSTOM_INSTRUCTIONS` replaces a user-written `gate h`/`gate cx` even without `include "qelib1.inc"`. Fix: only apply legacy instructions when the include is present, or reject programs that redefine a qelib1 name.
5. **Measure policy defaults to "allow" (A08, A09)**, but the instructions say "Don't add measurements unless the task asks". Fix: default to "forbid", or set `measure` on every task.
6. **Method constraints in the prompt text aren't encoded (A10–A12).** Fix: `allowed_gates: ["rz"]` plus an op-count limit for p04, `["rx"]` for b03. b10 needs a structural check (or reword the prompt).
7. **Tolerances (A13–A15).** Fidelity 1-1e-6 allows about 2e-3 rad error. `equiv` defaults allow about 1e-5. Fix: use an amplitude-level check (for example `np.allclose(phase-aligned states, atol=1e-8)`) and `Operator.equiv(atol=1e-8, rtol=0)`. Leak tolerance could drop to around 1e-9.
8. **Register naming (A16 / W2).** Either grade by the register named `q` or say in the instructions that task qubits are the first n qubits in declaration order.

## Other weaknesses (not wrong-passes)

- **W1: one submission can crash the whole grading run.** C01–C03 raise `CircuitError` inside `_final_measure_split` (in `stripped.append`), which only catches `GradeError`. `grader.py` exits with a traceback and no results for any submission in the file. Repro: `$PY ../../grader.py all_tasks.jsonl crash_C01.jsonl`.
- **W2: a correct circuit can fail because of register order.** `qreg a[1]; qreg q[2]; x q[0];` on p02 is correct by name (q[0]=1), but it's graded `wrong_state`, because the grader takes `a[0]` as task qubit 0. This mirrors A16.
- **W3: nondeterministic grades.** See A02 (10/20 PASS). Re-grading the same file can flip results.
- **W4: BoxOp gets the wrong reason label.** F01 fails as `simulation_error` rather than `unsupported_op`, because `box` isn't in the control-flow name list. It fails safe for now, but it could pass if a future qiskit's Operator learns to inline boxes.
- **W5: no Python sandbox** (the README says so). A03/A04 show this is a correctness problem as well as a security one.

Run 1 check (scope: only grepped `runs/run1/answers.jsonl` for measure/initialize/reset/custom gate/os/qpy and the three method-constraint tasks). No run 1 answer uses any of these attacks. p04, b03 and b10 used rz, rx and x+h as asked. Measurements appear only in p12 and b09, which require them.

## Counts

- Attempts: **33** (16 A, 14 F, 3 C)
- Confirmed wrong-passes: **16** (A01–A16). By severity: 5 wrong-output/integrity (A01, A02, A03, A04, A07), 7 constraint/rule breaks with the correct matrix (A05, A06, A08–A12), 3 tolerance (A13–A15), 1 depends on reading (A16).
- Other weaknesses: **5** (W1–W5)

Preregistered bar was 0 wrong circuits graded pass: **not met.**
