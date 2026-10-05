"""Stand-in for _runner.py used ONLY by verify.py (does NOT import grader.py
or _runner.py). It reproduces the runner's call-frame layout so we can observe
the integrity gap: a function whose locals are named `out_path` and `nonce`
calls runpy.run_path on the submission. Argv: SRC OUT_PATH QC_PATH.

- OUT_PATH: the "grading" output path the submission tampers with (what the real
  grader would read back).
- QC_PATH: where we honestly serialize the submission's declared `qc`, if the
  submission lets control return (it won't if it calls os._exit).
"""
import sys
from qiskit import qpy
import runpy


def main():
    src = sys.argv[1]
    out_path = sys.argv[2]   # read by the submission via frame inspection
    nonce = "verify_nonce"   # read by the submission via frame inspection
    qc_path = sys.argv[3]
    ns = {}
    try:
        ns = runpy.run_path(src, run_name="__submission__")
    except SystemExit:
        pass
    qc = ns.get("qc")
    if qc is not None:
        with open(qc_path, "wb") as f:
            qpy.dump(qc, f)


if __name__ == "__main__":
    main()
