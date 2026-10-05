# Stand-in for _runner.py. Mimics its protocol WITHOUT importing _runner/grader.
# It runs the submission, then (like the real runner) reads out_path+nonce from
# stdin, verifies qiskit.qpy.dump unchanged, and dumps `qc` to out_path.
import io, os, runpy, sys
import qiskit.qpy
from qiskit import QuantumCircuit
_DUMP = qiskit.qpy.dump
src = sys.argv[1]
ns = runpy.run_path(src, run_name="__submission__")
out_path = sys.stdin.readline().rstrip("\n")
nonce = sys.stdin.readline().rstrip("\n")
if qiskit.qpy.dump is not _DUMP:
    print("dump replaced", file=sys.stderr); sys.exit(3)
qc = ns.get("qc")
buf = io.BytesIO(); _DUMP(qc, buf)
with open(out_path, "wb") as f:
    f.write(buf.getvalue())
sys.__stdout__.write("\nRUNNER_OK " + nonce + "\n"); sys.__stdout__.flush()
os._exit(0)
