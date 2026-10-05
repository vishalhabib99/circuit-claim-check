"""Run one Qiskit Python submission and save its circuit as QPY.

Invoked by grader.py in a separate process: `python -I _runner.py SRC OUT`.
The submission must leave a QuantumCircuit in a variable named `qc`.
"""
import runpy
import sys

from qiskit import QuantumCircuit, qpy


def main() -> int:
    src, out = sys.argv[1], sys.argv[2]
    namespace = runpy.run_path(src, run_name="__submission__")
    qc = namespace.get("qc")
    if not isinstance(qc, QuantumCircuit):
        print("submission did not define a QuantumCircuit named `qc`", file=sys.stderr)
        return 2
    with open(out, "wb") as f:
        qpy.dump(qc, f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
