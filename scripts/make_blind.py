"""Write tasks/blind.jsonl and tests/fixtures/blind_cases.jsonl.

Written after the grader and the pilot set were committed (f467cea), and
committed before the grader was ever run on it. Same trap categories as the
pilot, new instances. The grader is not changed to make these pass: the
first run is recorded in evals/blind_grader_check.txt as-is.
"""
import json
from pathlib import Path

from make_pilot import py, q2

ROOT = Path(__file__).resolve().parent.parent

INV_QFT3 = py("from qiskit.circuit.library import QFTGate\nqc = QuantumCircuit(3)\nqc.append(QFTGate(3).inverse(), [0, 1, 2])")
QFT3 = py("from qiskit.circuit.library import QFTGate\nqc = QuantumCircuit(3)\nqc.append(QFTGate(3), [0, 1, 2])")


def stateprep(n, idx, sign=1):
    return py(
        "import numpy as np\nfrom qiskit.circuit.library import StatePreparation\n"
        f"v = np.zeros({2 ** n}); v[{idx}] = {sign} / np.sqrt({len(idx)})\n"
        f"qc = QuantumCircuit({n})\nqc.append(StatePreparation(v), list(range({n})))"
    )


TASKS = [
    ("b01", "easy", ["basic", "relative_phase"], "statevector", 2,
     "Prepare the Bell state (|01> - |10>)/sqrt(2) (Qiskit convention: rightmost character is q[0]).",
     q2(2, "h q[0];\ncx q[0],q[1];\nx q[1];\nz q[0];"),
     [("(|01> + |10>)/sqrt(2): sign missing", q2(2, "h q[0];\ncx q[0],q[1];\nx q[1];")),
      ("(|00> - |11>)/sqrt(2)", q2(2, "h q[0];\ncx q[0],q[1];\nz q[0];"))],
     [("X, H, X, CNOT", q2(2, "x q[0];\nh q[0];\nx q[1];\ncx q[0],q[1];"))], {}),
    ("b02", "easy", ["endianness"], "statevector", 3,
     "Prepare the basis state |100> (Qiskit convention: rightmost character is q[0]).",
     q2(3, "x q[2];"),
     [("big-endian reading: flips q[0]", q2(3, "x q[0];")),
      ("flips q[1]", q2(3, "x q[1];"))],
     [("HZH on q[2]", q2(3, "h q[2];\nz q[2];\nh q[2];"))], {}),
    ("b03", "easy", ["global_phase"], "unitary", 1,
     "Implement the Pauli X gate using a single RX rotation. Global phase does not matter.",
     q2(1, "rx(pi) q[0];"),
     [("half the angle", q2(1, "rx(pi/2) q[0];")),
      ("RY(pi) is Y up to phase, not X", q2(1, "ry(pi) q[0];"))],
     [("plain X", q2(1, "x q[0];"))], {}),
    ("b04", "easy", ["param_rotation"], "unitary", 1,
     "Apply RX(-3*pi/4) to q[0].",
     q2(1, "rx(-3*pi/4) q[0];"),
     [("sign flipped", q2(1, "rx(3*pi/4) q[0];")),
      ("wrong axis", q2(1, "rz(-3*pi/4) q[0];"))],
     [("U3(theta, -pi/2, pi/2) equals RX(theta)", q2(1, "u3(-3*pi/4,-pi/2,pi/2) q[0];"))], {}),
    ("b05", "medium", ["control_target"], "unitary", 3,
     "Apply a CNOT with control q[2] and target q[0].",
     q2(3, "cx q[2],q[0];"),
     [("control and target swapped", q2(3, "cx q[0],q[2];")),
      ("wrong target", q2(3, "cx q[2],q[1];"))],
     [("H-CZ-H on the target", q2(3, "h q[0];\ncz q[2],q[0];\nh q[0];"))], {}),
    ("b06", "medium", ["relative_phase", "param_rotation"], "unitary", 2,
     "Apply a controlled-T gate: control q[0], target q[1] (diag(1, 1, 1, e^(i*pi/4))).",
     q2(2, "cp(pi/4) q[0],q[1];"),
     [("CRZ(pi/4): relative phase is wrong", q2(2, "crz(pi/4) q[0],q[1];")),
      ("controlled-T-dagger", q2(2, "cp(-pi/4) q[0],q[1];"))],
     [("CP is symmetric", q2(2, "cp(pi/4) q[1],q[0];"))], {}),
    ("b07", "medium", ["qft"], "unitary", 3,
     "Implement the inverse of the 3-qubit QFT defined by qiskit.circuit.library.QFTGate.",
     INV_QFT3,
     [("forward QFT instead", QFT3),
      ("inverse of the QFT without its final reversal",
       q2(3, "h q[0];\ncp(-pi/2) q[0],q[1];\nh q[1];\ncp(-pi/4) q[0],q[2];\ncp(-pi/2) q[1],q[2];\nh q[2];"))],
     [("hand-built: SWAP first, then the reversed, conjugated QFT",
       q2(3, "swap q[0],q[2];\nh q[0];\ncp(-pi/2) q[0],q[1];\nh q[1];\ncp(-pi/4) q[0],q[2];\ncp(-pi/2) q[1],q[2];\nh q[2];"))], {}),
    ("b08", "medium", ["multi_controlled"], "unitary", 4,
     "Apply an X gate to q[0] controlled on q[1], q[2] and q[3] all being 1.",
     q2(4, "c3x q[1],q[2],q[3],q[0];"),
     [("target is q[3], not q[0]", q2(4, "c3x q[0],q[1],q[2],q[3];")),
      ("one control dropped", q2(4, "ccx q[1],q[2],q[0];"))],
     [("Qiskit mcx", py("qc = QuantumCircuit(4)\nqc.mcx([1, 2, 3], 0)"))], {}),
    ("b09", "medium", ["measurement"], "statevector", 3,
     "Prepare the 3-qubit GHZ state (|000> + |111>)/sqrt(2) and measure every qubit.",
     q2(3, "h q[0];\ncx q[0],q[1];\ncx q[0],q[2];\nmeasure q[0] -> c[0];\nmeasure q[1] -> c[1];\nmeasure q[2] -> c[2];", creg=3),
     [("q[2] not measured", q2(3, "h q[0];\ncx q[0],q[1];\ncx q[0],q[2];\nmeasure q[0] -> c[0];\nmeasure q[1] -> c[1];", creg=3)),
      ("no measurements", q2(3, "h q[0];\ncx q[0],q[1];\ncx q[0],q[2];"))],
     [("measure q -> c in one statement", q2(3, "h q[0];\ncx q[0],q[1];\ncx q[1],q[2];\nmeasure q -> c;", creg=3))],
     {"measure": "require"}),
    ("b10", "medium", ["measurement", "relative_phase"], "statevector", 1,
     "Prepare |-> by applying H to |1>. Return the circuit without any measurement.",
     q2(1, "x q[0];\nh q[0];"),
     [("measured", q2(1, "x q[0];\nh q[0];\nmeasure q[0] -> c[0];", creg=1)),
      ("forgot the X: |+>", q2(1, "h q[0];"))],
     [("H then Z", q2(1, "h q[0];\nz q[0];"))], {"measure": "forbid"}),
    ("b11", "hard", ["grover_oracle", "endianness"], "unitary", 3,
     "Build a phase oracle on 3 qubits that flips the sign of exactly the basis state |011> (Qiskit convention: rightmost character is q[0]).",
     q2(3, "x q[2];\nh q[2];\nccx q[0],q[1],q[2];\nh q[2];\nx q[2];"),
     [("big-endian reading: marks |110>", q2(3, "x q[0];\nh q[2];\nccx q[0],q[1],q[2];\nh q[2];\nx q[0];")),
      ("no X: marks |111>", q2(3, "h q[2];\nccx q[0],q[1],q[2];\nh q[2];"))],
     [("CCZ built around q[0]", q2(3, "x q[2];\nh q[0];\nccx q[1],q[2],q[0];\nh q[0];\nx q[2];"))], {}),
    ("b12", "hard", ["gate_set", "control_target"], "unitary", 2,
     "Implement a CZ gate on q[0], q[1] using only H and CNOT gates.",
     q2(2, "h q[1];\ncx q[0],q[1];\nh q[1];"),
     [("uses CZ directly, which the task disallows", q2(2, "cz q[0],q[1];")),
      ("Hadamards on the control instead of the target", q2(2, "h q[1];\ncx q[1],q[0];\nh q[1];"))],
     [("conjugate the other qubit (CZ is symmetric)", q2(2, "h q[0];\ncx q[1],q[0];\nh q[0];"))],
     {"allowed_gates": ["h", "cx"]}),
    ("b13", "hard", ["param_rotation"], "unitary", 1,
     "Apply U(theta=pi/3, phi=-pi/2, lambda=pi/2) to q[0] (Qiskit's U / U3 parameter order).",
     q2(1, "u3(pi/3,-pi/2,pi/2) q[0];"),
     [("phi and lambda swapped", q2(1, "u3(pi/3,pi/2,-pi/2) q[0];")),
      ("theta sign flipped", q2(1, "u3(-pi/3,-pi/2,pi/2) q[0];"))],
     [("RZ(lambda), RY(theta), RZ(phi), in circuit order", q2(1, "rz(pi/2) q[0];\nry(pi/3) q[0];\nrz(-pi/2) q[0];"))], {}),
    ("b14", "hard", ["multi_controlled", "endianness"], "unitary", 3,
     "Flip q[0] if and only if q[1] = 0 and q[2] = 1.",
     q2(3, "x q[1];\nccx q[1],q[2],q[0];\nx q[1];"),
     [("wrong control negated", q2(3, "x q[2];\nccx q[1],q[2],q[0];\nx q[2];")),
      ("no negation", q2(3, "ccx q[1],q[2],q[0];"))],
     [("Qiskit ctrl_state='10' over controls [q[1], q[2]]",
       py("from qiskit.circuit.library import XGate\nqc = QuantumCircuit(3)\nqc.append(XGate().control(2, ctrl_state='10'), [1, 2, 0])"))], {}),
    ("b15", "hard", ["basic", "endianness"], "statevector", 2,
     "Prepare (|00> + |01> + |10>)/sqrt(3) (Qiskit convention: rightmost character is q[0]).",
     stateprep(2, [0, 1, 2]),
     [("uniform over all four basis states", q2(2, "h q[0];\nh q[1];")),
      ("(|00> + |10> + |11>)/sqrt(3)", stateprep(2, [0, 2, 3]))],
     [("same state times a global phase of -1", stateprep(2, [0, 1, 2], sign=-1))], {}),
]


def main():
    tasks, cases = [], []
    for tid, diff, traps, mode, n, prompt, ref, mutants, variants, extra in TASKS:
        tasks.append({"id": tid, "difficulty": diff, "traps": traps, "mode": mode,
                      "n_qubits": n, "prompt": prompt, "reference": ref, **extra})
        cases += [{"id": tid, "kind": "mutant", "note": note, "code": code} for note, code in mutants]
        cases += [{"id": tid, "kind": "variant", "note": note, "code": code} for note, code in variants]
    (ROOT / "tasks" / "blind.jsonl").write_text("".join(json.dumps(t) + "\n" for t in tasks))
    (ROOT / "tests" / "fixtures" / "blind_cases.jsonl").write_text("".join(json.dumps(c) + "\n" for c in cases))
    print(f"{len(tasks)} tasks, {sum(c['kind'] == 'mutant' for c in cases)} mutants, "
          f"{sum(c['kind'] == 'variant' for c in cases)} variants")


if __name__ == "__main__":
    main()
