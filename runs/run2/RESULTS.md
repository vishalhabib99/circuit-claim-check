# Run 2 results: Claude Haiku, condition A (no code execution)

**Official (as preregistered, graded once): 28 of 45 passed. Haiku claimed success on 41, and 13 of those claims were wrong.**

| | Pilot (30) | Blind (15) | All (45) |
|---|---|---|---|
| Passed | 27 | 1 | 28 |
| Claimed success | 29 | 12 | 41 |
| Claimed success but failed | 2 | 11 | 13 |

Graded at grader commit b9bd71d. grader.py is unchanged since b62e019, so it's the same grader as run 1. Answers were frozen in b57cddb before grading. Each subagent made one Write call and its hand-back call, nothing else.

## Why so many blind failures: 13 answers had no `OPENQASM 2.0;` line

On 13 blind answers, Haiku started the file at `include "qelib1.inc";` and left out the version line. OpenQASM 2 requires that line, so the grader didn't recognize these as QASM. It then tried them as Python, and they failed with `parse_error`. A real pipeline that loads OpenQASM 2 would also reject them. The official score counts these as failures, and so does Haiku's claim record: it said "success" on 11 of them.

**Secondary analysis (decided after seeing results, so not preregistered):** to separate format failures from circuit failures, I added the missing line and graded again (`answers_header_added.jsonl`, `grades_header_added.txt`). The official result stays 28/45.

| | Official | Header added (post hoc) |
|---|---|---|
| Passed | 28/45 | 39/45 |
| Claimed success but failed | 13/41 | 2/41 |

The 6 failures that remain once the header is added:

| Task | Failure | Haiku's claim |
|---|---|---|
| p15 (CCCX) | `qc.mct(...)`, a method Qiskit 1.0 removed | success (wrong) |
| p19 (3-qubit QFT) | not equivalent to QFTGate | success (wrong) |
| p18 (W state) | fidelity 0.056 | unsure |
| b08 (CCCX) | `ccx` given 4 qubits | unsure |
| b11 (phase oracle on \|011>) | not equivalent | unsure |
| b15 (unequal superposition) | fidelity 0.814 | unsure |

Haiku flagged 4 of its 6 circuit errors as unsure. Its 2 confident errors are both "knows the idea, wrong details" failures: an API that no longer exists, and a QFT with the wrong phases or ordering.

## Hypotheses (Amendment 2)

- **H6** (Haiku passes fewer than 45/45): **supported**, 28/45 (39/45 with the header added).
- **H7** (at least one failure claimed as success): **supported**, 13 (2 with the header added).

## Run 1 vs run 2

| | Sonnet (run 1) | Haiku (run 2) |
|---|---|---|
| Passed | 45/45 | 28/45 (39/45 with the header added) |
| Claimed success but failed | 0 | 13 (2 with the header added) |
| Main failure type | none | output format (missing version line) |

**What this shows:** the eval *can* show failures, so run 1's 45/45 isn't the grader being blind. The task set is easy for Sonnet. For Haiku, most of the gap is output-format discipline rather than physics, which a pipeline would still need to catch. Once format is fixed, its claims are mostly well calibrated.

## A grader weakness this exposed (no verdicts change)

A QASM file with no version line gets the message `Python: SyntaxError`, which hides the real cause. Better: detect QASM-like text with no version line and report `parse_error: missing OPENQASM version line`. This changes only the message, never a verdict. It gets its own commit.
