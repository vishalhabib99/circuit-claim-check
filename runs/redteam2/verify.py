"""Independent verification for red team 2. Does NOT import grader.py.

For each attack it computes the circuit's TRUE meaning with qiskit.quantum_info
and numpy and compares it to the task text, or shows an integrity violation
(the circuit the grader ends up reading is not the submission's answer `qc`).

Run: <python> verify.py
"""
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit, qasm2, qpy
from qiskit.quantum_info import Operator

# p06 ground truth: CNOT with control q[1], target q[0] (little-endian q1 q0).
REF_P06 = QuantumCircuit(2); REF_P06.cx(1, 0)
REF_P06_U = Operator(REF_P06).data


def eq(a, b, atol=1e-9):
    k = np.unravel_index(np.argmax(np.abs(b)), b.shape)
    ph = a[k] / b[k]; ph /= abs(ph)
    return bool(np.allclose(a, ph * b, rtol=0, atol=atol))


def honest_qasm2_matrix(code: str) -> np.ndarray:
    """Parse honoring the program's OWN gate definitions.

    A gate the program defines is detected by trying a strict parse with no
    legacy instructions; whatever that yields is the faithful circuit. (We do
    not reuse the grader's line-anchored regex; we just let the parser use the
    program's own `gate` bodies.)
    """
    qc = qasm2.loads(code, custom_instructions=[])
    return Operator(qc).data


HARNESS = str(Path(__file__).with_name("_harness.py"))


def capture_runner_write(code: str):
    """Run the submission in a SUBPROCESS under _harness.py (not grader/_runner).

    Returns (circuit_written_for_grading, declared_qc). The subprocess isolates
    us from the submission's os._exit. `out_path` is the file the submission
    tampers with (what the real grader reads back); `qc_path` is where the
    harness honestly serializes the submission's own `qc` if control returns.
    """
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "s.py"; src.write_text(code)
        out_path = Path(d) / "out.qpy"
        qc_path = Path(d) / "qc.qpy"
        subprocess.run([sys.executable, "-I", HARNESS, str(src), str(out_path), str(qc_path)],
                       input="", capture_output=True, text=True, timeout=60)
        written = qpy.load(out_path.open("rb"))[0] if out_path.exists() else None
        qc = qpy.load(qc_path.open("rb"))[0] if qc_path.exists() else None
        return written, qc


def main() -> int:
    atts = [json.loads(l) for l in Path(__file__).with_name("attacks.jsonl").read_text().splitlines() if l.strip()]
    rows = []
    for a in atts:
        tag, code = a["tag"], a["code"]
        if tag == "RT2-02":
            u = honest_qasm2_matrix(code)
            wrong = not eq(u, REF_P06_U)
            detail = ("honest matrix == identity, != CNOT" if np.allclose(u, np.eye(4), atol=1e-9)
                      else "honest matrix != reference CNOT")
            rows.append((tag, "p06", wrong, detail))
        else:  # RT2-01, RT2-03 integrity attacks
            written, qc = capture_runner_write(code)
            # The circuit written for grading:
            graded_is_correct = written is not None and eq(Operator(written).data, REF_P06_U)
            # The submission's declared answer qc (when reachable):
            qc_wrong = None
            if qc is not None:
                qc_wrong = not eq(Operator(qc).data, REF_P06_U)
            # Integrity violation: a correct circuit is handed to the grader while
            # the submission's own answer qc is the wrong one (or deliberately hidden).
            if tag == "RT2-01":
                # qc is behind os._exit; show the written file is the correct CNOT,
                # yet the source literally assigns qc = cx(0,1) (wrong) -> integrity gap.
                wrong = bool(graded_is_correct) and ("qc.cx(0,1)" in code)
                detail = "file written for grading = correct CNOT, but declared qc = cx(0,1) (wrong)"
            else:  # RT2-03
                wrong = bool(qc_wrong)
                detail = f"declared qc matrix != reference CNOT (qc_wrong={qc_wrong})"
            rows.append((tag, "p06", wrong, detail))

    print(f"{'tag':<8}{'task':<6}{'independent_wrong':<20}detail")
    for tag, task, wrong, detail in rows:
        print(f"{tag:<8}{task:<6}{str(wrong):<20}{detail}")
    print(f"\nindependent wrong circuits: {sum(1 for r in rows if r[2])}/{len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
