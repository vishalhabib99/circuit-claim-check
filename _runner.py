"""Run one Qiskit Python submission and save its circuit as QPY.

Invoked by grader.py in a separate process: `python -I _runner.py SRC`, with
"<output path>\\n<nonce>\\n" on stdin. The submission must leave a
QuantumCircuit in a variable named `qc`.

The output path and nonce are read from stdin before the submission runs, so
they aren't in argv for it to find, and the serializer is captured before the
submission can replace it (red team 1: A03, A04). This raises the bar for a
submission that tampers with the runner; it is not a sandbox. Code in the same
process can still inspect this process's memory. See README.
"""
import io
import runpy
import sys

import qiskit.qpy
from qiskit import QuantumCircuit

_DUMP = qiskit.qpy.dump
_QC_TYPE = QuantumCircuit


def main() -> int:
    src = sys.argv[1]
    out_path = sys.stdin.readline().rstrip("\n")
    nonce = sys.stdin.readline().rstrip("\n")
    namespace = runpy.run_path(src, run_name="__submission__")
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
