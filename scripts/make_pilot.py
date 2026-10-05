"""Write tasks/pilot.jsonl and tests/fixtures/pilot_cases.jsonl.

Each pilot task carries a reference solution, plus hand-written mutants that
must FAIL (each one is a specific, plausible mistake) and correct variants
that must PASS (a different but equivalent construction). The mutants and
variants test the grader, not an agent.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def q2(n, body, creg=0):
    head = f'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[{n}];\n'
    if creg:
        head += f"creg c[{creg}];\n"
    return head + body.strip() + "\n"


def py(body):
    return "from qiskit import QuantumCircuit\n" + body.strip() + "\n"


QFT2 = py("from qiskit.circuit.library import QFTGate\nqc = QuantumCircuit(2)\nqc.append(QFTGate(2), [0, 1])")
QFT3 = py("from qiskit.circuit.library import QFTGate\nqc = QuantumCircuit(3)\nqc.append(QFTGate(3), [0, 1, 2])")
IQFT2 = py("from qiskit.circuit.library import QFTGate\nqc = QuantumCircuit(2)\nqc.append(QFTGate(2).inverse(), [0, 1])")
W3_REF = py(
    "import numpy as np\nfrom qiskit.circuit.library import StatePreparation\n"
    "v = np.zeros(8); v[[1, 2, 4]] = 1 / np.sqrt(3)\n"
    "qc = QuantumCircuit(3)\nqc.append(StatePreparation(v), [0, 1, 2])"
)

# (id, difficulty, traps, mode, n, prompt, reference, mutants, variants, extra)
TASKS = [
    ("p01", "easy", ["basic"], "statevector", 2,
     "Prepare the Bell state (|00> + |11>)/sqrt(2) on qubits q[0] and q[1].",
     q2(2, "h q[0];\ncx q[0],q[1];"),
     [("only H, no entangling gate", q2(2, "h q[0];")),
      ("extra Z gives (|00> - |11>)/sqrt(2)", q2(2, "h q[0];\ncx q[0],q[1];\nz q[0];"))],
     [("H on q[1], CNOT q[1]->q[0]", q2(2, "h q[1];\ncx q[1],q[0];"))], {}),
    ("p02", "easy", ["endianness"], "statevector", 2,
     "Prepare the computational basis state |01> using Qiskit's bit-string convention (the rightmost character is q[0]).",
     q2(2, "x q[0];"),
     [("big-endian reading: flips q[1]", q2(2, "x q[1];")),
      ("flips both", q2(2, "x q[0];\nx q[1];"))],
     [("HZH = X on q[0]", q2(2, "h q[0];\nz q[0];\nh q[0];"))], {}),
    ("p03", "easy", ["relative_phase"], "statevector", 1,
     "Prepare the single-qubit state |-> = (|0> - |1>)/sqrt(2).",
     q2(1, "x q[0];\nh q[0];"),
     [("|+> instead of |->", q2(1, "h q[0];")),
      ("(|0> + i|1>)/sqrt(2) instead", q2(1, "h q[0];\ns q[0];"))],
     [("H then Z", q2(1, "h q[0];\nz q[0];"))], {}),
    ("p04", "easy", ["global_phase"], "unitary", 1,
     "Implement the Pauli Z gate using a single RZ rotation. Global phase does not matter.",
     q2(1, "rz(pi) q[0];"),
     [("quarter turn: RZ(pi/2) is S up to phase, not Z", q2(1, "rz(pi/2) q[0];")),
      ("wrong axis", q2(1, "rx(pi) q[0];"))],
     [("plain Z gate (differs from RZ(pi) only by global phase)", q2(1, "z q[0];")),
      ("RZ(-pi), same up to global phase", q2(1, "rz(-pi) q[0];"))], {}),
    ("p05", "easy", ["param_rotation"], "unitary", 1,
     "Apply RY(pi/3) to q[0].",
     q2(1, "ry(pi/3) q[0];"),
     [("sign flipped", q2(1, "ry(-pi/3) q[0];")),
      ("wrong axis", q2(1, "rx(pi/3) q[0];"))],
     [("U3(pi/3, 0, 0) equals RY(pi/3)", q2(1, "u3(pi/3,0,0) q[0];"))], {}),
    ("p06", "easy", ["control_target"], "unitary", 2,
     "Apply a CNOT with control q[1] and target q[0].",
     q2(2, "cx q[1],q[0];"),
     [("control and target swapped", q2(2, "cx q[0],q[1];")),
      ("SWAP instead", q2(2, "swap q[0],q[1];"))],
     [("H-CZ-H on the target", q2(2, "h q[0];\ncz q[1],q[0];\nh q[0];")),
      ("reversed CNOT conjugated by Hadamards", q2(2, "h q[0];\nh q[1];\ncx q[0],q[1];\nh q[0];\nh q[1];"))], {}),
    ("p07", "medium", ["basic"], "statevector", 3,
     "Prepare the 3-qubit GHZ state (|000> + |111>)/sqrt(2).",
     q2(3, "h q[0];\ncx q[0],q[1];\ncx q[1],q[2];"),
     [("last CNOT missing", q2(3, "h q[0];\ncx q[0],q[1];")),
      ("extra S: (|000> + i|111>)/sqrt(2)", q2(3, "h q[0];\ncx q[0],q[1];\ncx q[1],q[2];\ns q[0];"))],
     [("fan-out from q[0], other order", q2(3, "h q[0];\ncx q[0],q[2];\ncx q[0],q[1];"))], {}),
    ("p08", "medium", ["relative_phase", "param_rotation"], "unitary", 2,
     "Apply a controlled-phase gate CP(pi/2) between q[0] and q[1] (diag(1, 1, 1, i)).",
     q2(2, "cp(pi/2) q[0],q[1];"),
     [("CRZ(pi/2): the target's global phase becomes a relative phase", q2(2, "crz(pi/2) q[0],q[1];")),
      ("sign flipped", q2(2, "cp(-pi/2) q[0],q[1];"))],
     [("CP is symmetric in its qubits", q2(2, "cp(pi/2) q[1],q[0];")),
      ("CU1 is the legacy name for CP", q2(2, "cu1(pi/2) q[0],q[1];"))], {}),
    ("p09", "medium", ["qft"], "unitary", 2,
     "Implement the 2-qubit quantum Fourier transform as defined by qiskit.circuit.library.QFTGate (including its final qubit reversal).",
     QFT2,
     [("inverse QFT instead", IQFT2),
      ("final swap missing", q2(2, "h q[1];\ncp(pi/2) q[0],q[1];\nh q[0];"))],
     [("hand-built: H, CP, H, SWAP", q2(2, "h q[1];\ncp(pi/2) q[0],q[1];\nh q[0];\nswap q[0],q[1];"))], {}),
    ("p10", "medium", ["qft"], "unitary", 2,
     "Implement the inverse of the 2-qubit QFT defined by qiskit.circuit.library.QFTGate.",
     IQFT2,
     [("forward QFT instead", QFT2),
      ("phase sign not flipped", q2(2, "swap q[0],q[1];\nh q[0];\ncp(pi/2) q[0],q[1];\nh q[1];"))],
     [("hand-built: SWAP, H, CP(-pi/2), H", q2(2, "swap q[0],q[1];\nh q[0];\ncp(-pi/2) q[0],q[1];\nh q[1];"))], {}),
    ("p11", "medium", ["multi_controlled"], "unitary", 3,
     "Apply a Toffoli (CCX) gate with controls q[0], q[1] and target q[2].",
     q2(3, "ccx q[0],q[1],q[2];"),
     [("target and a control swapped", q2(3, "ccx q[0],q[2],q[1];")),
      ("single-control CNOT", q2(3, "cx q[0],q[2];"))],
     [("textbook Clifford+T decomposition", q2(3, """
h q[2];
cx q[1],q[2];
tdg q[2];
cx q[0],q[2];
t q[2];
cx q[1],q[2];
tdg q[2];
cx q[0],q[2];
t q[1];
t q[2];
h q[2];
cx q[0],q[1];
t q[0];
tdg q[1];
cx q[0],q[1];"""))], {}),
    ("p12", "medium", ["measurement"], "statevector", 2,
     "Prepare the Bell state (|00> + |11>)/sqrt(2) and measure both qubits into classical bits.",
     q2(2, "h q[0];\ncx q[0],q[1];\nmeasure q[0] -> c[0];\nmeasure q[1] -> c[1];", creg=2),
     [("no measurements", q2(2, "h q[0];\ncx q[0],q[1];", creg=2)),
      ("only q[0] measured", q2(2, "h q[0];\ncx q[0],q[1];\nmeasure q[0] -> c[0];", creg=2)),
      ("measured before the CNOT (mid-circuit)", q2(2, "h q[0];\nmeasure q[0] -> c[0];\ncx q[0],q[1];\nmeasure q[1] -> c[1];", creg=2))],
     [("classical bits in the other order", q2(2, "h q[0];\ncx q[0],q[1];\nmeasure q[0] -> c[1];\nmeasure q[1] -> c[0];", creg=2))],
     {"measure": "require"}),
    ("p13", "medium", ["measurement"], "statevector", 2,
     "Prepare |+> on q[0] and |1> on q[1]. Return only the state-preparation circuit: no measurements.",
     q2(2, "h q[0];\nx q[1];"),
     [("measured anyway", q2(2, "h q[0];\nx q[1];\nmeasure q[0] -> c[0];\nmeasure q[1] -> c[1];", creg=2)),
      ("qubits swapped", q2(2, "x q[0];\nh q[1];"))],
     [("gates in the other order", q2(2, "x q[1];\nh q[0];"))], {"measure": "forbid"}),
    ("p14", "medium", ["gate_set"], "unitary", 2,
     "Swap the states of q[0] and q[1] using only CNOT gates.",
     q2(2, "cx q[0],q[1];\ncx q[1],q[0];\ncx q[0],q[1];"),
     [("uses the SWAP gate, which the task disallows", q2(2, "swap q[0],q[1];")),
      ("only two CNOTs", q2(2, "cx q[0],q[1];\ncx q[1],q[0];"))],
     [("mirror-image CNOT order", q2(2, "cx q[1],q[0];\ncx q[0],q[1];\ncx q[1],q[0];"))],
     {"allowed_gates": ["cx"]}),
    ("p15", "medium", ["multi_controlled"], "unitary", 4,
     "Apply an X gate to q[3] controlled on q[0], q[1] and q[2] all being 1.",
     q2(4, "c3x q[0],q[1],q[2],q[3];"),
     [("one control dropped", q2(4, "ccx q[0],q[1],q[3];")),
      ("target is q[2], not q[3]", q2(4, "c3x q[0],q[1],q[3],q[2];"))],
     [("Qiskit mcx", py("qc = QuantumCircuit(4)\nqc.mcx([0, 1, 2], 3)"))], {}),
    ("p16", "medium", ["grover_oracle", "endianness"], "unitary", 3,
     "Build a phase oracle on 3 qubits that flips the sign of exactly the basis state |110> (Qiskit convention: rightmost character is q[0]) and leaves every other basis state unchanged.",
     q2(3, "x q[0];\nh q[2];\nccx q[0],q[1],q[2];\nh q[2];\nx q[0];"),
     [("big-endian reading: marks |011>", q2(3, "x q[2];\nh q[0];\nccx q[1],q[2],q[0];\nh q[0];\nx q[2];")),
      ("bit-flip oracle instead of phase oracle", q2(3, "x q[0];\nccx q[0],q[1],q[2];\nx q[0];"))],
     [("CCZ built around a different target qubit", q2(3, "x q[0];\nh q[1];\nccx q[0],q[2],q[1];\nh q[1];\nx q[0];"))], {}),
    ("p17", "hard", ["grover_oracle", "global_phase"], "unitary", 2,
     "Implement the 2-qubit Grover diffusion operator 2|s><s| - I, where |s> is the uniform superposition. Global phase does not matter.",
     q2(2, "h q[0];\nh q[1];\nx q[0];\nx q[1];\ncz q[0],q[1];\nx q[0];\nx q[1];\nh q[0];\nh q[1];"),
     [("X layer missing", q2(2, "h q[0];\nh q[1];\ncz q[0],q[1];\nh q[0];\nh q[1];")),
      ("closing Hadamards missing", q2(2, "h q[0];\nh q[1];\nx q[0];\nx q[1];\ncz q[0],q[1];\nx q[0];\nx q[1];"))],
     [("Z on each qubit plus CZ in place of the X sandwich", q2(2, "h q[0];\nh q[1];\nz q[0];\nz q[1];\ncz q[0],q[1];\nh q[0];\nh q[1];"))], {}),
    ("p18", "hard", ["basic"], "statevector", 3,
     "Prepare the 3-qubit W state (|001> + |010> + |100>)/sqrt(3).",
     W3_REF,
     [("GHZ instead", q2(3, "h q[0];\ncx q[0],q[1];\ncx q[1],q[2];")),
      ("two excitations instead of one: (|011> + |101> + |110>)/sqrt(3)",
       py("import numpy as np\nfrom qiskit.circuit.library import StatePreparation\n"
          "v = np.zeros(8); v[[3, 5, 6]] = 1 / np.sqrt(3)\n"
          "qc = QuantumCircuit(3)\nqc.append(StatePreparation(v), [0, 1, 2])"))],
     [("explicit gates: RY, CH, CX, then a 00-controlled X", q2(3, """
ry(1.9106332362490186) q[0];
ch q[0],q[1];
cx q[1],q[0];
x q[0];
x q[1];
ccx q[0],q[1],q[2];
x q[0];
x q[1];"""))], {}),
    ("p19", "hard", ["qft"], "unitary", 3,
     "Implement the 3-qubit quantum Fourier transform as defined by qiskit.circuit.library.QFTGate.",
     QFT3,
     [("inverse QFT instead", py("from qiskit.circuit.library import QFTGate\nqc = QuantumCircuit(3)\nqc.append(QFTGate(3).inverse(), [0, 1, 2])")),
      ("final reversal missing", q2(3, "h q[2];\ncp(pi/2) q[1],q[2];\ncp(pi/4) q[0],q[2];\nh q[1];\ncp(pi/2) q[0],q[1];\nh q[0];"))],
     [("hand-built with the final SWAP", q2(3, "h q[2];\ncp(pi/2) q[1],q[2];\ncp(pi/4) q[0],q[2];\nh q[1];\ncp(pi/2) q[0],q[1];\nh q[0];\nswap q[0],q[2];"))], {}),
    ("p20", "hard", ["param_rotation"], "unitary", 2,
     "Apply RZZ(pi/4) between q[0] and q[1].",
     q2(2, "rzz(pi/4) q[0],q[1];"),
     [("sign flipped", q2(2, "rzz(-pi/4) q[0],q[1];")),
      ("controlled phase instead", q2(2, "cp(pi/4) q[0],q[1];"))],
     [("CNOT-RZ-CNOT", q2(2, "cx q[0],q[1];\nrz(pi/4) q[1];\ncx q[0],q[1];"))], {}),
    ("p21", "medium", ["param_rotation"], "unitary", 1,
     "Apply the gate U(theta=pi/2, phi=pi/4, lambda=pi/8) to q[0] (Qiskit's U / U3 parameter order).",
     q2(1, "u3(pi/2,pi/4,pi/8) q[0];"),
     [("phi and lambda swapped", q2(1, "u3(pi/2,pi/8,pi/4) q[0];")),
      ("theta halved", q2(1, "u3(pi/4,pi/4,pi/8) q[0];"))],
     [("RZ(lambda), RY(theta), RZ(phi), in circuit order", q2(1, "rz(pi/8) q[0];\nry(pi/2) q[0];\nrz(pi/4) q[0];"))], {}),
    ("p22", "medium", ["control_target"], "unitary", 2,
     "Apply a controlled-Hadamard with control q[1] and target q[0].",
     q2(2, "ch q[1],q[0];"),
     [("control and target swapped", q2(2, "ch q[0],q[1];")),
      ("uncontrolled H", q2(2, "h q[0];"))],
     [("RY(pi/4), CNOT, RY(-pi/4) on the target", q2(2, "ry(pi/4) q[0];\ncx q[1],q[0];\nry(-pi/4) q[0];"))], {}),
    ("p23", "easy", ["endianness"], "statevector", 3,
     "Prepare the basis state |110> (Qiskit convention: rightmost character is q[0]).",
     q2(3, "x q[1];\nx q[2];"),
     [("big-endian reading: |011>", q2(3, "x q[0];\nx q[1];")),
      ("only one bit set", q2(3, "x q[2];"))],
     [("same gates, other order", q2(3, "x q[2];\nx q[1];"))], {}),
    ("p24", "hard", ["multi_controlled", "endianness"], "unitary", 3,
     "Flip q[2] if and only if q[0] = 1 and q[1] = 0. Leave every other case unchanged.",
     q2(3, "x q[1];\nccx q[0],q[1],q[2];\nx q[1];"),
     [("plain Toffoli: fires on q[0]=1, q[1]=1", q2(3, "ccx q[0],q[1],q[2];")),
      ("wrong control negated: fires on q[0]=0, q[1]=1", q2(3, "x q[0];\nccx q[0],q[1],q[2];\nx q[0];"))],
     [("Qiskit ctrl_state='01' (little-endian: q[0]=1, q[1]=0)",
       py("from qiskit.circuit.library import XGate\nqc = QuantumCircuit(3)\nqc.append(XGate().control(2, ctrl_state='01'), [0, 1, 2])"))], {}),
    ("p25", "easy", ["global_phase"], "unitary", 1,
     "Apply S-dagger (the inverse of the S gate) to q[0]. Global phase does not matter.",
     q2(1, "sdg q[0];"),
     [("S instead of S-dagger", q2(1, "s q[0];")),
      ("T-dagger instead", q2(1, "tdg q[0];"))],
     [("RZ(-pi/2), same up to global phase", q2(1, "rz(-pi/2) q[0];"))], {}),
    ("p26", "medium", ["relative_phase"], "statevector", 1,
     "Prepare the state (|0> + i|1>)/sqrt(2).",
     q2(1, "h q[0];\ns q[0];"),
     [("|+> instead", q2(1, "h q[0];")),
      ("(|0> - i|1>)/sqrt(2): S-dagger instead of S", q2(1, "h q[0];\nsdg q[0];"))],
     [("RX(-pi/2) from |0>", q2(1, "rx(-pi/2) q[0];"))], {}),
    ("p27", "hard", ["multi_controlled", "relative_phase"], "unitary", 3,
     "Apply a doubly-controlled Z (CCZ) on q[0], q[1], q[2].",
     q2(3, "h q[2];\nccx q[0],q[1],q[2];\nh q[2];"),
     [("Toffoli without the Hadamards", q2(3, "ccx q[0],q[1],q[2];")),
      ("only CZ on two qubits", q2(3, "cz q[0],q[1];"))],
     [("same gate built around q[0] (CCZ is symmetric)", q2(3, "h q[0];\nccx q[1],q[2],q[0];\nh q[0];"))], {}),
    ("p28", "hard", ["grover_oracle", "endianness"], "unitary", 3,
     "Build the Bernstein-Vazirani phase oracle |x> -> (-1)^(s.x) |x> for secret s = 110 (Qiskit convention: the rightmost bit of s goes with q[0]).",
     q2(3, "z q[1];\nz q[2];"),
     [("big-endian reading of s", q2(3, "z q[0];\nz q[1];")),
      ("CZ instead of two Zs", q2(3, "cz q[1],q[2];"))],
     [("RZ(pi) on each, same up to global phase", q2(3, "rz(pi) q[1];\nrz(pi) q[2];"))], {}),
    ("p29", "medium", ["control_target"], "unitary", 3,
     "In a 3-qubit register, swap the states of q[0] and q[2] and leave q[1] untouched.",
     q2(3, "swap q[0],q[2];"),
     [("swaps q[0] and q[1]", q2(3, "swap q[0],q[1];")),
      ("swaps q[1] and q[2]", q2(3, "swap q[1],q[2];"))],
     [("three CNOTs", q2(3, "cx q[0],q[2];\ncx q[2],q[0];\ncx q[0],q[2];"))], {}),
    ("p30", "hard", ["control_target", "param_rotation"], "unitary", 2,
     "Apply a controlled-RY(pi/2) with control q[0] and target q[1].",
     q2(2, "cry(pi/2) q[0],q[1];"),
     [("control and target swapped", q2(2, "cry(pi/2) q[1],q[0];")),
      ("sign flipped", q2(2, "cry(-pi/2) q[0],q[1];"))],
     [("RY(pi/4), CX, RY(-pi/4), CX", q2(2, "ry(pi/4) q[1];\ncx q[0],q[1];\nry(-pi/4) q[1];\ncx q[0],q[1];"))], {}),
]


def main():
    tasks, cases = [], []
    for tid, diff, traps, mode, n, prompt, ref, mutants, variants, extra in TASKS:
        tasks.append({"id": tid, "difficulty": diff, "traps": traps, "mode": mode,
                      "n_qubits": n, "prompt": prompt, "reference": ref, **extra})
        cases += [{"id": tid, "kind": "mutant", "note": note, "code": code} for note, code in mutants]
        cases += [{"id": tid, "kind": "variant", "note": note, "code": code} for note, code in variants]
    (ROOT / "tasks" / "pilot.jsonl").write_text("".join(json.dumps(t) + "\n" for t in tasks))
    (ROOT / "tests" / "fixtures" / "pilot_cases.jsonl").write_text("".join(json.dumps(c) + "\n" for c in cases))
    print(f"{len(tasks)} tasks, {sum(c['kind'] == 'mutant' for c in cases)} mutants, "
          f"{sum(c['kind'] == 'variant' for c in cases)} variants")


if __name__ == "__main__":
    main()
