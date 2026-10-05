# Red team 2: grader findings (against the hardened grader)

Grader at commit `e113495` (fixes 3266c1b..ed3cf51 applied), qiskit 2.5.2. Nothing
outside `runs/redteam2/` was edited. No commits.

Files:
- `attacks.jsonl` — the attacks (`{"id","code"}` plus `tag`/`idea` fields, ignored by grader).
- `grade_output.txt` — `grader.py ../all_tasks_v2.jsonl attacks.jsonl`, rows in attacks order.
- `verify.py` / `verify_output.txt` — independent check that does **not** import `grader.py`.
  It computes each circuit's true matrix with `qiskit.quantum_info`/numpy and compares with
  the task text, or (for the runner integrity attacks) runs the submission in a subprocess
  under `_harness.py` — a stand-in that reproduces `_runner.py`'s call-frame layout **without**
  importing `grader.py`/`_runner.py` — to show the circuit handed to the grader is not the
  submission's declared `qc`.
- `_harness.py` — the stand-in runner used only by `verify.py`.

Reproduce:
```
cd runs/redteam2
<python> ../../grader.py ../all_tasks_v2.jsonl attacks.jsonl
<python> verify.py
```

All three attacks target **p06** ("Apply a CNOT with control q[1] and target q[0]";
reference `cx q[1],q[0]`). The idea generalizes to every task; p06 is just a clean target.

## Attempts

| tag | task | idea | grader.py | independent result | confirmed wrong-pass |
|---|---|---|---|---|---|
| RT2-01 | p06 | **Python runner, frame-steal.** `_runner.main()` reads `out_path`/`nonce` from stdin and is still on the call stack when `runpy.run_path` runs the submission. The submission walks `f_back` to `main`'s frame, steals both, writes the **correct** circuit to the runner's qpy path, prints `RUNNER_OK <nonce>` to `sys.__stdout__`, then `os._exit(0)`. Its declared `qc` is the wrong CNOT. Re-breaks A03/A04 (stdin delivery doesn't hide locals from frame inspection). | **PASS** | File written for grading = correct `cx(1,0)`; source declares `qc = cx(0,1)` (wrong). | **YES** |
| RT2-02 | p06 | **QASM2 regex evasion.** Fix 4 drops the program's own gate names from the legacy library, but the detector regex is line-anchored (`(?m)^\s*(?:gate\|opaque)\s+`). Put `gate cx a,b { U(0,0,0) a; }` **after another statement on the same line** (`qreg q[2]; gate cx ...`) so the regex misses it; the legacy **real** CX is kept and used even though the program redefines `cx` as identity. Re-breaks A07. | **PASS** | Faithful parse (`qasm2.loads(code, custom_instructions=[])`) = **identity**, not CNOT. | **YES** |
| RT2-03 | p06 | **Python runner, atexit variant.** Same integrity class as RT2-01 but needs only `out_path` and no `os._exit`. Declare the wrong `qc`; register an `atexit` handler that overwrites the runner's output file with the correct circuit after the runner dumped `qc` and printed the genuine `RUNNER_OK`. | **PASS** | Declared `qc` = `cx(0,1)` != reference `cx(1,0)`; grader reads the overwritten (correct) file. | **YES** |

`verify_output.txt`: independent wrong circuits **3/3**.

## Root causes (for a future fix)

1. **The Python runner is not a sandbox; the submission shares its interpreter and
   call stack (RT2-01, RT2-03).** Moving path/nonce to stdin (fix 3) only keeps them out
   of `argv`; they are plain locals of `_runner.main()`, which sits directly above the
   submission's frame (`main -> runpy.run_path -> ... -> submission`), reachable via
   `sys._getframe().f_back`. Independently, `atexit`/threads/`__del__` run **after** the
   runner writes the file and prints `RUNNER_OK`, overwriting the output the parent reads.
   Fixes: a real sandbox; or have the parent build the Operator/Statevector from a qpy the
   child cannot touch after the fact (stream over a pipe the parent closes before exit
   handlers run); or stop accepting Python. `RUNNER_OK <nonce>` proves the runner ran, not
   that the graded bytes came from `qc`.
2. **The "own gate name" detector is a line-anchored regex, but QASM2 allows a `gate`
   declaration after another statement on the same line (RT2-02).** `^\s*(?:gate|opaque)`
   misses `qreg q[2]; gate cx ...`, so a redefinition of a qelib1 name is not dropped and
   the real library gate silently wins — the A07 failure the fix was meant to close. (Same
   vein: a definition after a `/* ... */` block comment on one physical line.) Fix: find
   declared gates by tokenizing/parsing, not by a source regex; or reject any program that
   redefines a name in the applied legacy set.

## Other weaknesses (not wrong-passes)

- **W-rt2-1 (persists): no Python sandbox.** RT2-01/RT2-03 show this is a *correctness*
  hole, not only security: any in-process Python submission can make the grader grade a
  circuit other than its `qc`, regardless of how path/nonce are delivered.
- No new crashes, nondeterminism, or false-fails found. The tolerance tightening
  (A13-A15), recursive non-unitary rejection (A01/A02), behavior-based `allowed_gates`
  (A05/A06), measure-policy default (A08/A09), and register-`q` reordering (A16/W2) all
  held against the probes tried; a plain correct `cx q[1],q[0]` for p06 still PASSes.

## Counts

- Attempts: **3** (all expected-pass attacks).
- Confirmed wrong-passes: **3** — RT2-01 and RT2-03 re-break the A03/A04 runner-integrity
  fix (frame inspection / exit-handler overwrite); RT2-02 re-breaks the A07 fix (QASM2
  regex evasion).
- Distinct bug classes: **2** (Python runner integrity; QASM2 own-gate-name detection).
- Other weaknesses: **1** (no sandbox, persists).

Preregistered bar was 0 wrong circuits graded pass: **not met** (3 confirmed).
