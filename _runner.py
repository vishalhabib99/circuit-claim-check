"""Run one Qiskit Python submission and save its circuit as QPY.

Invoked by grader.py in a separate process: `python -I _runner.py SRC`, with
"<output path>\\n<nonce>\\n" on stdin. The submission must leave a
QuantumCircuit in a variable named `qc`.

grader.py first checks the source against a small allowed subset (no sys/os,
no frame or underscore attributes). The output path and nonce are read only
after the submission has run, the serializer is captured before it runs, and
the process exits with os._exit so no exit handler or thread runs afterwards
(red team 1: A03, A04; red team 2: RT2-01, RT2-03). This raises the bar for a
submission that tampers with the runner; it is not a sandbox. See README.
"""
import io
import os
import runpy
import sys

import qiskit.qpy
from qiskit import QuantumCircuit

_DUMP = qiskit.qpy.dump
_QC_TYPE = QuantumCircuit


def main() -> int:
    src = sys.argv[1]
    namespace = runpy.run_path(src, run_name="__submission__")
    # Read the output path and nonce only after the submission has finished, so
    # they're never in this process's memory while it runs (red team 2: RT2-01).
    out_path = sys.stdin.readline().rstrip("\n")
    nonce = sys.stdin.readline().rstrip("\n")
    if qiskit.qpy.dump is not _DUMP:
        print("submission replaced qiskit.qpy.dump", file=sys.stderr)
        return 3
    qc = namespace.get("qc")
    if type(qc) is not _QC_TYPE:
        print("submission did not define a QuantumCircuit named `qc`", file=sys.stderr)
        return 2
    buf = io.BytesIO()
    _DUMP(qc, buf)
    with open(out_path, "wb") as f:
        f.write(buf.getvalue())
    sys.__stdout__.write(f"\nRUNNER_OK {nonce}\n")
    sys.__stdout__.flush()
    # Exit without running atexit handlers or waiting on threads, so nothing the
    # submission registered can touch the output afterwards (red team 2: RT2-03).
    os._exit(0)


if __name__ == "__main__":
    sys.exit(main())
