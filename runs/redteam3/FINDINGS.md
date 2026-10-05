# Red team 3: grader findings (against grader fix 11)

Grader at commit `4054378` (Amendment 4; fixes 10 and 11 applied), qiskit 2.5.2.
Nothing outside `runs/redteam3/` was edited. No commits.

Files:
- `attacks.jsonl` — the attacks (`{"id","code"}`), 3 rows (p06, p01, p11).
- `grade_output.txt` — `grader.py ../all_tasks_v2.jsonl attacks.jsonl`.
- `verify.py` / `verify_output.txt` — independent check that does **not** import
  `grader.py` or `_runner.py`. It runs each submission under `standalone_runner.py`
  (a stand-in that reproduces `_runner.py`'s stdin protocol without importing it),
  loads the file the grader would load, separately reconstructs the `qc` the
  submission actually declares, and compares **both** with the task reference it
  computes itself with `qiskit.quantum_info`.
- `standalone_runner.py` — the stand-in runner, used only by `verify.py`.

Reproduce:
```
cd runs/redteam3
<python> ../../grader.py ../all_tasks_v2.jsonl attacks.jsonl
<python> verify.py
```

## Summary

**1 new wrong-pass class, 3 confirmed instances.** Fix 11 (the Python allowed-subset
check) was meant to close the red-team-1/2 runner-integrity holes (RT2-01 frame-steal,
RT2-03 atexit overwrite). It does block those specific routes, but it does **not** make
the Python runner a sandbox, and the submission still runs *before* `_runner.py` reads
its output path and nonce from stdin. A submission can read stdin itself, through an
allowed module, and impersonate the runner — writing the correct circuit to the stolen
path while its declared `qc` is wrong. Fix 10 (faithful QASM 2 parse) held against the
probes tried; one QASM-2 false-fail is noted under weaknesses.

## Attempts

| # | task | mode | idea | grader.py | independent result | confirmed wrong-pass |
|---|---|---|---|---|---|---|
| RT3-01 | p06 | unitary | **Python runner, stdin-steal + numpy write.** The subset blocks `open`, `sys`, `os`, frame/underscore attrs, and all RT2 routes. But it allows `numpy`, `print`, custom classes, and `raise SystemExit`. The submission reads the runner's `out_path`/`nonce` from `/dev/stdin` with `numpy.loadtxt` (consuming the pipe the runner will later read), serializes the **correct** circuit with `qiskit.qpy.dump` into a hand-written in-memory file object (no `io`/`open` needed — a class with `write`/`tell`/`flush`), writes it to the stolen path with `numpy.ndarray.tofile`, prints `RUNNER_OK <nonce>` as the last stdout line, and `raise SystemExit(0)` so `_runner.main()` never runs its own (now-broken) dump. Declared `qc` is `cx(0,1)`. | **PASS** | graded file = `cx(1,0)` (= ref); declared `qc` = `cx(0,1)` != ref | **YES** |
| RT3-02 | p01 | statevector | Same technique, statevector task. Declared `qc` = `h(0)` only (= `|+0>`); file = Bell `(|00>+|11>)/sqrt2`. Shows the class is mode-independent. | **PASS** | graded = Bell (= ref); declared `qc` = `|+0>` != ref | **YES** |
| RT3-03 | p11 | unitary | Same technique, 3-qubit Toffoli. Declared `qc` = `ccx(0,2,1)` (wrong target); file = `ccx(0,1,2)`. | **PASS** | graded = CCX(0,1,2) (= ref); declared `qc` = CCX(0,2,1) != ref | **YES** |

`verify_output.txt`: confirmed wrong-passes **3/3**.

## Root cause (for a future fix)

**The Python runner still shares its process and stdin with the submission, and the
submission runs first.** Fix 3/RT2 moved `out_path`/`nonce` out of `argv` and into
stdin, read *after* the submission runs, so the submission couldn't have them in a
local. Fix 11 then blocked frame inspection and exit handlers. Neither prevents the
submission from **reading stdin itself before the runner does**: `_runner.main()` calls
`runpy.run_path(submission)` *before* its `sys.stdin.readline()`, so the bytes
`"<out_path>\n<nonce>\n"` are already on fd 0 and unread while the submission runs. The
subset does not (and practically cannot, while allowing `numpy`) block file reads/writes:

- `numpy.loadtxt("/dev/stdin", dtype=str)` reads the pipe line-by-line (unlike
  `numpy.fromfile`, which needs a seekable file), handing the submission the exact
  path and nonce.
- `numpy.ndarray.tofile(path)` writes arbitrary bytes to any path.
- `qiskit.qpy.dump` serializes to any object with `write`/`tell`/`flush`; a plain
  user-defined class supplies those with no `io`, `open`, or underscore attributes.
- `raise SystemExit(0)` exits the process cleanly (it propagates through
  `runpy.run_path` and out of `main()`), so the real runner never executes its dump or
  its `qiskit.qpy.dump is _DUMP` check, and `returncode` is 0.

`RUNNER_OK <nonce>` proves the runner-protocol ran, **not** that the graded bytes came
from `qc` — the RT2 root cause, reached by a route the subset does not cover.

Real fixes: a true sandbox (no shared fd 0); or have the **parent**, not a child the
submission shares, build the Operator/Statevector from bytes the submission can never
see or write (e.g. stream qpy over a pipe the parent owns and closes, with the child
given no filesystem write access); or stop accepting Python. Delivering the path/nonce
over stdin does not help while the submission can drain stdin first.

## Other weaknesses (not wrong-passes)

- **W-rt3-1 (false fail, fix 10): a comment or string containing the word `gate`
  blocks the legacy fallback.** `_load_qasm2` falls back to `LEGACY_CUSTOM_INSTRUCTIONS`
  only when faithful parse fails *and* `re.search(r"\b(?:gate|opaque)\b", code)` finds
  nothing. The regex scans raw source, so a correct program that needs a legacy-only
  gate (e.g. `rzz`, `csx`, `c3x`) without `include "qelib1.inc"` and that happens to
  contain a comment like `// prepare the gate` is rejected as `parse_error`, though the
  identical program without that word parses and grades fine. Repro:
  `OPENQASM 2.0;\n// this gate is great\nqreg q[2];\nrzz(pi/4) q[0],q[1];` -> blocked;
  drop the comment -> OK. (A correct answer, wrongly failed.)

- **W-rt3-2 (persists, same as RT1 W5 / RT2 W-rt2-1): no Python sandbox.** RT3-01..03
  show this remains a *correctness* hole, not only a security one: any in-process Python
  submission can make the grader grade a circuit other than its `qc`. The subset raises
  the bar but does not close the class.

## Things that held (checked, no finding)

- **qpy is faithful.** A `Gate` named `cx` with an identity definition round-trips
  through `qpy.dump`/`qpy.load` as identity (not reconstructed into the standard CX), so
  a qpy name-collision cannot silently swap in a correct gate.
- **QASM 2 legacy fallback gives the real gates.** Every entry of
  `LEGACY_CUSTOM_INSTRUCTIONS` is the genuine qiskit gate class; none has a matrix that
  differs from the standard mapping of the same name, so the fallback cannot grade a
  wrong matrix as correct. (It can wrongly *fail* a correct program — W-rt3-1.)
- **QASM 3 register aliasing (`let q = a[{1,0}]`) is honest relabeling, not a
  wrong-pass.** `_task_register_first` honoring the register named `q` matches the
  instructions; an alias only renames which physical qubit is `q[0]`, and the task-frame
  matrix must still equal the reference to pass.
- Behavior-based `allowed_gates` + `max_gates` (p04/b03/b10/p14/b12), the recursive
  non-unitary rejection, the measure-policy default (forbid), the 1e-9 tolerance, and
  the ancilla leak check all held against the probes tried.

## Counts

- Attempts: **3** (all expected-pass; the same new class on different tasks/modes).
- Confirmed wrong-passes: **3** (RT3-01 p06, RT3-02 p01, RT3-03 p11).
- Distinct new bug classes: **1** (Python runner integrity via stdin-steal, past the
  fix-11 subset).
- Other weaknesses: **2** (W-rt3-1 QASM-2 legacy-fallback false fail; W-rt3-2 no sandbox).

Preregistered bar was 0 wrong circuits graded pass: **not met** (3 confirmed).
