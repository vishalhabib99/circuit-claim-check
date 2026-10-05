# Run 1 results: Claude Sonnet, condition A (no code execution)

**45 of 45 passed. Sonnet claimed success on all 45, and none of those claims were wrong.**

| Set | Passed | Claimed success | Claimed success but failed |
|---|---|---|---|
| Pilot (30) | 30 | 30 | 0 |
| Blind (15) | 15 | 15 | 0 |

Graded once at grader commit b62e019 (answers frozen in 9e736c9 before grading). Each subagent made one Write call and its hand-back call, and nothing else, so no code was run.

## Hypotheses (preregistered)

- **H1** (endianness lowest pass rate): **not supported.** Every category passed 100%, so no category was lowest.
- **H2** (mismatch rate at least 1 in 10): **rejected.** It was 0 of 45.
- **H3** (a relative-phase task fails with CRZ for CP, or a sign error): **rejected.** p08 and b06 both passed.
- **H4** (hard tasks pass less than easy): **not supported.** Every difficulty level passed 100%.
- **H5** (condition B): not run. With 0 mismatches in condition A, there is nothing for self-checking to fix.

## Checks on the perfect score

A 100% score is a reason to check the grader first. Four of the trickiest answers (p02, p18, b01, b15) were checked against target states written from the task text, without the reference solutions. All four overlaps were 1.0. The grader's validation is unchanged: 91 of 91 mutants killed.

One answer used a shortcut the rules allow: b07 (the inverse QFT) appended `QFTGate(3).inverse()` from Qiskit's library instead of building it from gates. The task didn't forbid this. A harder version should.

## What this means

This task set is too easy to tell anything apart for this model. These are textbook circuits with exact answers, and Sonnet knows the textbook. The traps I expected to work (qubit ordering, CP vs CRZ, inverse vs forward QFT) caught nothing. That's a negative result, reported as-is under the "no edits after results" rule. It doesn't show that agents build circuits correctly in general.

Bounds: 0 misses in 45 still allows a true miss rate up to about 6.4% (one-sided 95% exact bound), and the tasks are short and well specified.

## What would make the next run informative (needs a new preregistration first)

1. Harder tasks of the kind the current set lacks: bigger circuits (5-10 qubits), arithmetic (adders, modular multiplication), Hamiltonian simulation with a stated Trotter order, restricted gate sets with no library calls, and tasks whose spec is ambiguous unless read carefully.
2. A weaker model as a contrast (Haiku), to check that the eval can show failures at all.
3. Red-team the grader: try to get a wrong circuit graded as correct.
