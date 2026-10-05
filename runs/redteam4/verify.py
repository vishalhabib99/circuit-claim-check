"""Independent check for red team 4. Does NOT import grader.py or _runner.py.

For each attack, it:
  1. reconstructs the circuit the submission declares (exec in a bare namespace),
  2. round-trips it through qiskit.qpy exactly as the grader's runner channel does,
     so we hold the *same* circuit object the grader receives,
  3. computes that circuit's FULL operator/state with qiskit.quantum_info (no
     stripping of any op), and
  4. independently recomputes the task's reference from all_tasks_v2.jsonl,
  5. shows the submitted circuit is NOT the reference (differs beyond 1e-9 even
     after removing a global phase), and separately prints the hidden op the
     grader dropped.
"""
import io
import json
import numpy as np
from qiskit import QuantumCircuit, qasm2, qasm3, qpy
from qiskit.quantum_info import Operator, Statevector

TASKS = {json.loads(l)["id"]: json.loads(l)
         for l in open("../all_tasks_v2.jsonl") if l.strip()}
IGNORED = {"barrier", "delay"}


def build_from_code(code: str) -> QuantumCircuit:
    s = code.lstrip()
    if s.startswith("OPENQASM 2"):
        return qasm2.loads(code)
    if s.startswith("OPENQASM 3"):
        return qasm3.loads(code)
    ns = {}
    exec(compile(code, "<ref_or_sub>", "exec"), ns, ns)
    return ns["qc"]


def qpy_roundtrip(qc: QuantumCircuit) -> QuantumCircuit:
    buf = io.BytesIO()
    qpy.dump(qc, buf)
    buf.seek(0)
    return qpy.load(buf)[0]


def equal_up_to_phase(a, b, atol=1e-9) -> bool:
    a = np.asarray(a); b = np.asarray(b)
    if a.shape != b.shape:
        return False
    k = np.unravel_index(np.argmax(np.abs(b)), b.shape)
    if abs(b[k]) < 1e-12:
        return False
    ph = a[k] / b[k]
    if abs(ph) < 1e-12:
        return False
    ph /= abs(ph)
    return bool(np.allclose(a, ph * b, rtol=0, atol=atol))


def main():
    n_confirmed = 0
    for line in open("attacks.jsonl"):
        if not line.strip():
            continue
        sub = json.loads(line)
        tid = sub["id"]
        task = TASKS[tid]
        n = task["n_qubits"]
        mode = task["mode"]

        qc = qpy_roundtrip(build_from_code(sub["code"]))          # what the grader receives
        ref = build_from_code(task["reference"])

        dropped = [inst.operation.name for inst in qc.data if inst.operation.name in IGNORED]

        print(f"=== {tid} ({mode}, n_qubits={n}) ===")
        print(f"  submitted circuit ops (full): {[i.operation.name for i in qc.data]}")
        print(f"  grader silently DROPS these ops (IGNORED_OPS): {dropped}")
        print(f"  reference ops:               {[i.operation.name for i in ref.data]}")

        if mode == "unitary":
            sub_u = Operator(qc).data
            ref_u = Operator(ref).data
            same = equal_up_to_phase(sub_u, ref_u)
            diff = float(np.max(np.abs(sub_u - (sub_u.flat[np.argmax(np.abs(ref_u))] /
                         ref_u.flat[np.argmax(np.abs(ref_u))]) * ref_u)))
            print(f"  submitted FULL unitary == reference (up to phase)? {same}  (max elementwise diff after phase-align ~{diff:.3f})")
        else:
            sub_s = Statevector.from_label("0" * qc.num_qubits).evolve(qc).data
            ref_s = Statevector.from_label("0" * ref.num_qubits).evolve(ref).data
            same = equal_up_to_phase(sub_s, ref_s)
            print(f"  submitted FULL state: {np.round(sub_s,3)}")
            print(f"  reference      state: {np.round(ref_s,3)}")
            print(f"  submitted FULL state == reference (up to phase)? {same}")

        confirmed = (not same) and len(dropped) > 0
        print(f"  => submitted circuit is NOT the task's circuit, yet grader PASSED it: "
              f"CONFIRMED WRONG-PASS = {confirmed}\n")
        n_confirmed += confirmed

    print(f"Independent confirmed wrong-passes: {n_confirmed}/5")


if __name__ == "__main__":
    main()
