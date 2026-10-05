# Red team 4: grader findings (against grader fix 12 + 13)

Grader at commit `1bc747a` (Amendment 5; fixes 12 and 13 applied), repo HEAD `258a50b`,
qiskit 2.5.2. Nothing outside `runs/redteam4/` was edited. No commits.

Files:
- `attacks.jsonl` — the attacks (`{"id","code"}`), 5 rows (p06, p01, p11, p25, p14).
- `grade_output.txt` — `../../.venv/bin/python ../../grader.py ../all_tasks_v2.jsonl attacks.jsonl`.
- `verify.py` / `verify_output.txt` — independent check that does **not** import
  `grader.py` or `_runner.py`. For each attack it reconstructs the submitted circuit,
  round-trips it through `qiskit.qpy` exactly as the grader's runner channel does (so it
  holds the *same* circuit object the grader receives), computes that circuit's **full**
  operator/state with `qiskit.quantum_info` (no op stripping), independently recomputes
  the task reference from `all_tasks_v2.jsonl`, and shows the submitted circuit is not the
  reference while naming the op the grader silently dropped.

Reproduce:
```
cd runs/redteam4
../../.venv/bin/python ../../grader.py ../all_tasks_v2.jsonl attacks.jsonl
../../.venv/bin/python verify.py
```

## Summary

**1 new wrong-pass class, 5 confirmed instances.** A Qiskit `Gate` whose `.name` is
`"barrier"` or `"delay"` (both in the grader's `IGNORED_OPS`) but whose matrix is an
arbitrary non-trivial unitary is **silently dropped** by the grader before comparison,
in both `_check_only_gates` (skipped, never checked) and `_final_measure_split` (removed
from the stripped circuit). The grader therefore grades a circuit that is not the one
submitted. A custom, *definition-based* gate renamed to `"barrier"`/`"delay"` survives
`qiskit.qpy` with that exact name (unlike a library singleton such as `XGate`, which qpy
normalizes back to `"x"`), so the hidden gate reaches the grader intact. The attack needs
nothing banned by the Python subset — just `QuantumCircuit`, `to_gate()`, `copy(name=...)`
and `append` — and does not touch the runner, the sandbox, stdin or stdout, so fixes
1-13 (runner integrity, QASM parsing, tolerances, measure policy, ancilla, register
naming) are all irrelevant to it. The circuit really executes the hidden gate; it is a
genuinely wrong circuit, not a no-op.

## Attempts

| # | task | mode | idea | grader.py | independent result | confirmed wrong-pass |
|---|---|---|---|---|---|---|
| RT4-01 | p06 | unitary | Visible `cx q[1],q[0]` (= reference). Append a custom `to_gate()` wrapping `X`, renamed `"barrier"`, on q[0]. Grader drops the `"barrier"`, grades `cx(1,0)`. Real circuit = `X.CX(1,0)`. | **PASS** | full unitary != ref (max diff 1.0); dropped op `barrier` | **YES** |
| RT4-02 | p01 | statevector | Visible `h(0); cx(0,1)` (= Bell ref). Hidden `X` renamed `"barrier"` on q[0]. Grader grades Bell. Real state = `(\|01>+\|10>)/sqrt2` (Psi+, a different Bell state). | **PASS** | full state `(\|01>+\|10>)/sqrt2` != ref `(\|00>+\|11>)/sqrt2` | **YES** |
| RT4-03 | p11 | unitary | Visible `ccx(0,1,2)` (= ref). Hidden `X` renamed **`"delay"`** (the other `IGNORED_OPS` name) on q[2]. Real = `X_2.CCX`. Shows both ignored names work. | **PASS** | full unitary != ref (max diff 1.0); dropped op `delay` | **YES** |
| RT4-04 | p25 | unitary | Visible `sdg(0)` (= ref, "Apply S-dagger"). Hidden `X` renamed `"barrier"`. Real = `X.Sdg`. | **PASS** | full unitary != ref (max diff 1.0) | **YES** |
| RT4-05 | p14 | unitary, `allowed_gates=['cx']` | Visible three `cx` (= SWAP ref, "swap using only CNOTs"). Hidden **two-qubit** gate wrapping `cx`, renamed `"barrier"`, on (q0,q1). Shows the hidden op can be multi-qubit and also slips past the `allowed_gates`/`max_gates`/behavior checks (they iterate the stripped circuit, which no longer contains it). Real = `CX(0,1).SWAP`. | **PASS** | full unitary != ref (max diff 1.0); dropped op `barrier` | **YES** |

`verify_output.txt`: independent confirmed wrong-passes **5/5**.

## Root cause (for a future fix)

`IGNORED_OPS = {"barrier", "delay"}` is matched by **op name only**, in two places:

- `_check_only_gates`: `if op.name in IGNORED_OPS: continue` — the op is never checked
  for being a unitary/standard gate, and its definition is never recursed into.
- `_final_measure_split`: the stripped circuit skips `inst.operation.name in IGNORED_OPS`,
  so the op is removed before `Operator`/`Statevector` is built.

The grader assumes anything named `"barrier"`/`"delay"` is a true `Barrier`/`Delay`
(a genuine no-op). But a name is not a class: `SomeCircuit.to_gate().copy(name="barrier")`
is an ordinary unitary `Gate` whose `.name` happens to be `"barrier"`, and
`qiskit.qpy.dump`/`load` preserves that custom name verbatim (it only normalizes *library
singletons* back to their canonical name — that is why `XGate().copy(name="barrier")`
comes back as `"x"` and fails, while a definition-based custom gate comes back as
`"barrier"` and succeeds). Dropping by name therefore deletes a real gate from the graded
circuit.

Fixes, any one of which closes the class:
1. **Match by type, not name.** Treat an op as ignorable only when it is an instance of
   `qiskit.circuit.Barrier` / `qiskit.circuit.Delay` (`isinstance`), not when its `.name`
   string matches. A `Gate` named `"barrier"` would then fall through to the normal
   unitary path and be graded.
2. **Don't strip by name at all; strip by semantics.** Keep every `Gate` in the operator
   and only drop instructions that are genuinely non-unitary book-keeping (`Barrier`,
   `Delay`, final `Measure`), identified by class.
3. Reject any submission whose op `.name` collides with a reserved book-keeping name
   (`barrier`, `delay`, `measure`, `reset`) but whose type is not the corresponding
   built-in class.

Same-vein note (not exploited into a wrong-pass): `_final_measure_split` and
`_check_only_gates` also special-case the name `"measure"`. A custom unitary `Gate` named
`"measure"` is likewise handled as a measurement (dropped, and routed through the measure
policy) rather than graded — on a `forbid` task it fails `measurement_not_allowed`, so it
is caught today, but the same name-vs-class confusion is present and should be fixed the
same way (match `Measure` by class).

## Other weaknesses (not wrong-passes)

- **No new false fails found.** A real `Barrier`/`Delay` (the proper class) is still a
  correct no-op and is handled correctly.
- **W-rt4-note (no severity):** the attack only needs `to_gate()`, `copy(name=...)` and
  `append`, all inside the current Python subset — so the subset cannot be tightened to
  block it; the fix must be in how ops are classified during grading, not in the parser.

## Things that held (checked, no finding)

- **Library-singleton rename is normalized by qpy.** `XGate().copy(name="barrier")`
  round-trips through qpy as `"x"`, so the naive "rename a standard gate" route fails;
  only a definition-based custom gate keeps the injected name. (This is why only one
  construction works — documented for the fix.)
- **QASM cannot reach this class.** `barrier`/`delay` are reserved words in OpenQASM 2/3;
  `gate barrier a { x a; }` is a parse error. The hole is Python-submission-only.
- **Runner / sandbox integrity (RT1 A03/A04, RT2 RT2-01/03, RT3 RT3-01..03) held.** The
  new attack does not go near the runner: it declares a wrong `qc` honestly and lets the
  runner serialize it faithfully. The grader's own stripping is what drops the op, so no
  stdout/stdin/frame/exit trickery was needed or attempted. The `RUNNER_OK` last-line
  channel, `os._exit`-on-any-exit, and the sandbox were not bypassed.
- **QASM 2 faithful-parse + legacy fallback (fix 10/13), behavior-based `allowed_gates`
  (A05/A06), recursive non-unitary rejection (A01/A02), measure-policy default (A08/A09),
  1e-9 tolerance (A13-A15), ancilla leak, and register-`q` reordering (A16)** all held
  against the probes tried; a plain correct answer for each of the five tasks still
  PASSes, and removing the hidden op from each attack turns it into a correct, legitimately
  passing submission.

## Counts

- Attempts: **5** (all expected-pass; one new class on 4 tasks/2 modes + a multi-qubit
  hidden op and an `allowed_gates` task, plus the `"delay"` name variant).
- Confirmed wrong-passes: **5** (RT4-01..05).
- Distinct new bug classes: **1** (name-based `IGNORED_OPS` drop of a custom gate renamed
  `barrier`/`delay`, preserved through qpy).
- Other weaknesses: **0 new** (the `"measure"`-name analogue is caught today but shares
  the root cause).

Preregistered bar was 0 wrong circuits graded pass: **not met** (5 confirmed).


## Addendum (2026-10-05, after the red team, while writing fix 14)

Not part of red team 4's count. The `"measure"` name check flagged above as "not exploited" is exploitable on a `require` task: on p12, `QuantumCircuit(1).to_gate().copy(name='measure')` appended to both qubits after a correct Bell circuit graded `pass` on grader 258a50b, with no real measurement. The state is right, but the task's explicit constraint (measure every qubit) is broken, so it is a wrong-pass under the same bar. Fixed by fix 14 and covered by `test_custom_gate_named_measure_is_not_a_measurement`.
