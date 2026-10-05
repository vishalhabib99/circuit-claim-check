"""Run one Qiskit Python submission and print its circuit as base64 QPY.

Invoked by grader.py as `sandbox-exec -f _sandbox.sb ... python -I -B
_runner.py SRC`, with stdin closed. The submission must leave a QuantumCircuit
in a variable named `qc`.

The result is the last stdout line, `RUNNER_OK <base64 qpy>`, printed by this
runner after the submission has finished, followed at once by os._exit. A
submission that exits early (SystemExit included) makes the runner exit 2,
so a forged RUNNER_OK line it printed is rejected. Nothing is passed in that
the submission could steal: no output path, no nonce, no stdin (red teams 1-3:
A03, A04, RT2-01, RT2-03, RT3-01..03). The OS sandbox blocks file writes
outside a throwaway scratch directory, new processes and network access.
"""
import base64
import io
import os
import runpy
import sys

import qiskit.qpy
from qiskit import QuantumCircuit

_DUMP = qiskit.qpy.dump
_QC_TYPE = QuantumCircuit
_OUT = sys.__stdout__


def main() -> None:
    src = sys.argv[1]
    try:
        namespace = runpy.run_path(src, run_name="__submission__")
    except BaseException as e:  # noqa: BLE001 - SystemExit too: an early exit is a failure
        print(f"submission raised {type(e).__name__}: {e}", file=sys.stderr)
        os._exit(2)
    if qiskit.qpy.dump is not _DUMP:
        print("submission replaced qiskit.qpy.dump", file=sys.stderr)
        os._exit(3)
    qc = namespace.get("qc")
    if type(qc) is not _QC_TYPE:
        print("submission did not define a QuantumCircuit named `qc`", file=sys.stderr)
        os._exit(2)
    buf = io.BytesIO()
    _DUMP(qc, buf)
    _OUT.write("\nRUNNER_OK " + base64.b64encode(buf.getvalue()).decode("ascii") + "\n")
    _OUT.flush()
    # Exit at once: no atexit handlers, no waiting on threads (red team 2: RT2-03).
    os._exit(0)


if __name__ == "__main__":
    main()
