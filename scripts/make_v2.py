"""Write tasks/v2.jsonl and tests/fixtures/v2_cases.jsonl.

The v2 set (30 tasks) is harder than v1: run 1 (Sonnet) scored 45/45 on v1, so
v1 can't show a difference between conditions. v2 targets the mistakes models
actually make: Qiskit bit order, inverse vs forward QFT, CRZ vs CP, operator
order in a matrix product, mixed-polarity controls, and gate-set limits that
force a decomposition instead of a library call.

Same structure as the pilot and blind sets: every task has a reference, two
hand-written mutants that must FAIL and one equivalent variant that must PASS.
Written and committed before any agent sees a v2 task (see PREREGISTRATION.md,
Amendment 7).
"""
import json
from pathlib import Path

import numpy as np

from make_pilot import py, q2

ROOT = Path(__file__).resolve().parent.parent


def stateprep(n, amps):
    """amps: {basis index: amplitude expression}; normalized in the circuit."""
    body = ", ".join(f"{i}: {a}" for i, a in amps.items())
    return py(
        "import numpy as np\nfrom qiskit.circuit.library import StatePreparation\n"
        f"v = np.zeros({2 ** n}, dtype=complex)\nfor i, a in {{{body}}}.items():\n    v[i] = a\n"
        f"v = v / np.linalg.norm(v)\nqc = QuantumCircuit({n})\nqc.append(StatePreparation(v), list(range({n})))"
    )


def qft(n, inverse=False, swaps=True, sign=1):
    """Hand-built QFT from H, CP and SWAP, written as Qiskit Python."""
    s = "-" if sign < 0 else ""
    body = (
        "from math import pi\n"
        f"qc = QuantumCircuit({n})\n"
        f"for j in reversed(range({n})):\n"
        "    qc.h(j)\n"
        "    for k in reversed(range(j)):\n"
        f"        qc.cp({s}pi / 2 ** (j - k), k, j)\n"
    )
    if swaps:
        body += f"for i in range({n} // 2):\n    qc.swap(i, {n} - 1 - i)\n"
    if inverse:
        body += "qc = qc.inverse()\n"
    return py(body)


def lib_qft(n, inverse=False, prep=""):
    inv = ".inverse()" if inverse else ""
    return py(f"from qiskit.circuit.library import QFTGate\nqc = QuantumCircuit({n})\n{prep}"
              f"qc.append(QFTGate({n}){inv}, list(range({n})))")


TOFFOLI_A0_B2_C1 = q2(3, """
h q[1];
cx q[2],q[1];
tdg q[1];
cx q[0],q[1];
t q[1];
cx q[2],q[1];
tdg q[1];
cx q[0],q[1];
t q[2];
t q[1];
h q[1];
cx q[0],q[2];
t q[0];
tdg q[2];
cx q[0],q[2];
""")

# (id, difficulty, traps, mode, n, prompt, reference, mutants, variants, extra)
TASKS = [
    # --- bit order -----------------------------------------------------------
    ("v01", "medium", ["endianness", "basic"], "statevector", 3,
     "Prepare (|100> + |011>)/sqrt(2) (Qiskit convention: the rightmost character is q[0]).",
     q2(3, "h q[0];\ncx q[0],q[1];\ncx q[0],q[2];\nx q[2];"),
     [("big-endian reading: (|001> + |110>)/sqrt(2)", q2(3, "h q[0];\ncx q[0],q[1];\ncx q[0],q[2];\nx q[1];\nx q[2];")),
      ("GHZ: the X is missing", q2(3, "h q[0];\ncx q[0],q[1];\ncx q[0],q[2];"))],
     [("H on q[2], then anti-copy to q[0] and q[1]", q2(3, "h q[2];\ncx q[2],q[0];\ncx q[2],q[1];\nx q[0];\nx q[1];"))], {}),
    ("v02", "easy", ["endianness"], "statevector", 4,
     "Prepare the basis state that encodes the integer 11 on q[0..3], with q[0] as the least significant bit.",
     q2(4, "x q[0];\nx q[1];\nx q[3];"),
     [("q[0] as the most significant bit", q2(4, "x q[0];\nx q[2];\nx q[3];")),
      ("encodes 7", q2(4, "x q[0];\nx q[1];\nx q[2];"))],
     [("same, written in Qiskit Python", py("qc = QuantumCircuit(4)\nqc.x([3, 1, 0])"))], {}),
    ("v03", "medium", ["endianness", "multi_controlled"], "unitary", 3,
     "Implement the 3-bit increment |x> -> |x + 1 mod 8> on q[0..2], with q[0] as the least significant bit.",
     q2(3, "ccx q[0],q[1],q[2];\ncx q[0],q[1];\nx q[0];"),
     [("decrement: the steps in reverse order", q2(3, "x q[0];\ncx q[0],q[1];\nccx q[0],q[1],q[2];")),
      ("q[2] treated as the least significant bit", q2(3, "ccx q[2],q[1],q[0];\ncx q[2],q[1];\nx q[2];"))],
     [("MCX form in Qiskit Python", py("qc = QuantumCircuit(3)\nqc.mcx([0, 1], 2)\nqc.cx(0, 1)\nqc.x(0)"))], {}),
    ("v04", "medium", ["endianness", "control_target"], "unitary", 2,
     "Implement the two-qubit unitary whose matrix, in Qiskit's basis ordering, is "
     "[[1,0,0,0],[0,0,0,1],[0,0,1,0],[0,1,0,0]].",
     q2(2, "cx q[0],q[1];"),
     [("control and target swapped (the textbook big-endian reading)", q2(2, "cx q[1],q[0];")),
      ("SWAP", q2(2, "swap q[0],q[1];"))],
     [("H-CZ-H on q[1]", q2(2, "h q[1];\ncz q[0],q[1];\nh q[1];"))], {}),

    # --- QFT -----------------------------------------------------------------
    ("v05", "hard", ["qft", "gate_set"], "unitary", 3,
     "Implement the inverse of Qiskit's QFTGate(3) on q[0..2], using only H, CP (controlled-phase) and SWAP gates.",
     qft(3, inverse=True),
     [("forward QFT instead of inverse", qft(3)),
      ("inverse QFT without the final swap", qft(3, inverse=True, swaps=False))],
     [("written out gate by gate in QASM", q2(3, "swap q[0],q[2];\nh q[0];\ncp(-pi/2) q[0],q[1];\nh q[1];\ncp(-pi/4) q[0],q[2];\ncp(-pi/2) q[1],q[2];\nh q[2];"))],
     {"allowed_gates": ["h", "cp", "swap"]}),
    ("v06", "hard", ["qft", "gate_set"], "unitary", 4,
     "Implement Qiskit's QFTGate(4) on q[0..3], using only H, CP (controlled-phase) and SWAP gates.",
     qft(4),
     [("no final swaps", qft(4, swaps=False)),
      ("phase signs flipped", qft(4, sign=-1))],
     [("CP arguments in the other order (CP is symmetric)", qft(4).replace("k, j)", "j, k)"))],
     {"allowed_gates": ["h", "cp", "swap"]}),
    ("v07", "medium", ["qft", "endianness"], "statevector", 3,
     "Prepare the state obtained by applying Qiskit's QFTGate(3) to the basis state |110> (Qiskit convention: the rightmost character is q[0]).",
     lib_qft(3, prep="qc.x([1, 2])\n"),
     [("QFT applied to |011>", lib_qft(3, prep="qc.x([0, 1])\n")),
      ("inverse QFT applied to |110>", lib_qft(3, inverse=True, prep="qc.x([1, 2])\n"))],
     [("hand-built QFT after X on q[1], q[2]",
       py("from math import pi\nqc = QuantumCircuit(3)\nqc.x([1, 2])\n"
          "for j in reversed(range(3)):\n    qc.h(j)\n    for k in reversed(range(j)):\n        qc.cp(pi / 2 ** (j - k), k, j)\n"
          "qc.swap(0, 2)"))], {}),

    # --- relative phase and decompositions --------------------------------------
    ("v08", "medium", ["relative_phase", "control_target"], "unitary", 2,
     "Apply a controlled-RZ(pi/2) with control q[1] and target q[0].",
     q2(2, "crz(pi/2) q[1],q[0];"),
     [("controlled-phase CP(pi/2) instead of CRZ", q2(2, "cp(pi/2) q[1],q[0];")),
      ("control and target swapped", q2(2, "crz(pi/2) q[0],q[1];"))],
     [("RZ(pi/4), CX, RZ(-pi/4), CX on the target", q2(2, "rz(pi/4) q[0];\ncx q[1],q[0];\nrz(-pi/4) q[0];\ncx q[1],q[0];"))], {}),
    ("v09", "hard", ["relative_phase", "gate_set"], "unitary", 2,
     "Implement CP(pi/4) (controlled-phase) between q[0] and q[1] using only CX and RZ gates. Global phase does not matter.",
     q2(2, "rz(pi/8) q[0];\nrz(pi/8) q[1];\ncx q[0],q[1];\nrz(-pi/8) q[1];\ncx q[0],q[1];"),
     [("angles doubled: CP(pi/2)", q2(2, "rz(pi/4) q[0];\nrz(pi/4) q[1];\ncx q[0],q[1];\nrz(-pi/4) q[1];\ncx q[0],q[1];")),
      ("second CX missing", q2(2, "rz(pi/8) q[0];\nrz(pi/8) q[1];\ncx q[0],q[1];\nrz(-pi/8) q[1];"))],
     [("mirrored: the CX targets q[0]", q2(2, "rz(pi/8) q[1];\nrz(pi/8) q[0];\ncx q[1],q[0];\nrz(-pi/8) q[0];\ncx q[1],q[0];"))],
     {"allowed_gates": ["cx", "rz"]}),
    ("v10", "medium", ["global_phase", "gate_set"], "unitary", 1,
     "Implement the SX (square root of X) gate using only H and P (phase) gates.",
     q2(1, "h q[0];\np(pi/2) q[0];\nh q[0];"),
     [("SX-dagger: P(-pi/2)", q2(1, "h q[0];\np(-pi/2) q[0];\nh q[0];")),
      ("P(pi/2) alone", q2(1, "p(pi/2) q[0];"))],
     [("H, P(-3pi/2), H", q2(1, "h q[0];\np(-3*pi/2) q[0];\nh q[0];"))],
     {"allowed_gates": ["h", "p"]}),
    ("v11", "easy", ["relative_phase"], "statevector", 2,
     "Prepare (|00> + i|11>)/sqrt(2).",
     q2(2, "h q[0];\ncx q[0],q[1];\ns q[0];"),
     [("phase -i instead of i", q2(2, "h q[0];\ncx q[0],q[1];\nsdg q[0];")),
      ("phase -1 instead of i", q2(2, "h q[0];\ncx q[0],q[1];\nz q[0];"))],
     [("S on q[1] instead of q[0]", q2(2, "h q[0];\ncx q[0],q[1];\ns q[1];"))], {}),
    ("v12", "hard", ["relative_phase", "endianness"], "statevector", 3,
     "Prepare (|001> + i|010> - |100>)/sqrt(3) (Qiskit convention: the rightmost character is q[0]).",
     stateprep(3, {1: "1", 2: "1j", 4: "-1"}),
     [("sign of the |100> term flipped", stateprep(3, {1: "1", 2: "1j", 4: "1"})),
      ("big-endian reading: the i and -1 land on |010> and |001>", stateprep(3, {4: "1", 2: "1j", 1: "-1"}))],
     [("same state times a global phase of i", stateprep(3, {1: "1j", 2: "-1", 4: "-1j"}))], {}),

    # --- controls ---------------------------------------------------------------
    ("v13", "hard", ["multi_controlled", "control_target", "gate_set"], "unitary", 3,
     "Implement a Toffoli gate with controls q[0] and q[2] and target q[1], using only H, T, Tdg and CX gates.",
     TOFFOLI_A0_B2_C1,
     [("standard decomposition with target q[2]", q2(3, """
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
cx q[0],q[1];
""")),
      ("last controlled-phase correction missing", TOFFOLI_A0_B2_C1.replace("cx q[0],q[2];\nt q[0];\ntdg q[2];\ncx q[0],q[2];\n", ""))],
     [("same decomposition with the two controls exchanged", TOFFOLI_A0_B2_C1.replace("q[0]", "q[X]").replace("q[2]", "q[0]").replace("q[X]", "q[2]"))],
     {"allowed_gates": ["h", "t", "tdg", "cx"]}),
    ("v14", "medium", ["multi_controlled"], "unitary", 3,
     "Flip q[2] if and only if q[0] = 1 and q[1] = 0.",
     q2(3, "x q[1];\nccx q[0],q[1],q[2];\nx q[1];"),
     [("the X on q[1] is never undone", q2(3, "x q[1];\nccx q[0],q[1],q[2];")),
      ("plain Toffoli: fires on q[1] = 1", q2(3, "ccx q[0],q[1],q[2];"))],
     [("Qiskit ctrl_state='01' over controls [q[0], q[1]]",
       py("from qiskit.circuit.library import XGate\nqc = QuantumCircuit(3)\nqc.append(XGate().control(2, ctrl_state='01'), [0, 1, 2])"))], {}),
    ("v15", "medium", ["multi_controlled", "relative_phase"], "unitary", 4,
     "Implement CCCZ on q[0..3]: multiply the phase of |1111> by -1 and leave every other basis state unchanged.",
     py("from math import pi\nqc = QuantumCircuit(4)\nqc.mcp(pi, [0, 1, 2], 3)"),
     [("CCZ on q[0..2] only", q2(4, "h q[2];\nccx q[0],q[1],q[2];\nh q[2];")),
      ("phase i instead of -1", py("from math import pi\nqc = QuantumCircuit(4)\nqc.mcp(pi / 2, [0, 1, 2], 3)"))],
     [("H, CCCX, H on q[3]", py("qc = QuantumCircuit(4)\nqc.h(3)\nqc.mcx([0, 1, 2], 3)\nqc.h(3)"))], {}),
    ("v16", "medium", ["control_target"], "unitary", 3,
     "Apply a controlled-SWAP (Fredkin) with control q[2] that swaps q[0] and q[1].",
     q2(3, "cswap q[2],q[0],q[1];"),
     [("control q[0], swapping q[1] and q[2]", q2(3, "cswap q[0],q[1],q[2];")),
      ("unconditional SWAP", q2(3, "swap q[0],q[1];"))],
     [("CX, Toffoli, CX", q2(3, "cx q[1],q[0];\nccx q[2],q[0],q[1];\ncx q[1],q[0];"))], {}),
    ("v17", "medium", ["multi_controlled", "relative_phase", "gate_set"], "unitary", 3,
     "Implement CCZ on q[0..2] (multiply the phase of |111> by -1) using only H and CCX (Toffoli) gates, at most 3 of them.",
     q2(3, "h q[2];\nccx q[0],q[1],q[2];\nh q[2];"),
     [("Toffoli without the Hadamards", q2(3, "ccx q[0],q[1],q[2];")),
      ("Hadamard on a control instead of the target", q2(3, "h q[0];\nccx q[0],q[1],q[2];\nh q[0];"))],
     [("conjugate q[0] instead (CCZ is symmetric)", q2(3, "h q[0];\nccx q[1],q[2],q[0];\nh q[0];"))],
     {"allowed_gates": ["h", "ccx"], "max_gates": 3}),

    # --- oracles and Grover -------------------------------------------------------
    ("v18", "hard", ["grover_oracle", "endianness"], "unitary", 3,
     "Implement a phase oracle that multiplies |100> and |110> by -1 and leaves every other basis state unchanged "
     "(Qiskit convention: the rightmost character is q[0]).",
     q2(3, "x q[0];\ncz q[0],q[2];\nx q[0];"),
     [("big-endian reading: marks |001> and |011>", q2(3, "x q[2];\ncz q[0],q[2];\nx q[2];")),
      ("marks |100> only", q2(3, "x q[0];\nx q[1];\nh q[2];\nccx q[0],q[1],q[2];\nh q[2];\nx q[0];\nx q[1];"))],
     [("open-controlled Z in Qiskit Python",
       py("from qiskit.circuit.library import ZGate\nqc = QuantumCircuit(3)\nqc.append(ZGate().control(1, ctrl_state='0'), [0, 2])"))], {}),
    ("v19", "medium", ["grover_oracle"], "unitary", 2,
     "Implement the 2-qubit Grover diffusion operator 2|s><s| - I, where |s> = |++>. Global phase does not matter.",
     q2(2, "h q[0];\nh q[1];\nx q[0];\nx q[1];\ncz q[0],q[1];\nx q[0];\nx q[1];\nh q[0];\nh q[1];"),
     [("phase flip on |00> without the Hadamards", q2(2, "x q[0];\nx q[1];\ncz q[0],q[1];\nx q[0];\nx q[1];")),
      ("reflects about |11> instead of |00> inside the Hadamards", q2(2, "h q[0];\nh q[1];\ncz q[0],q[1];\nh q[0];\nh q[1];"))],
     [("H, Z, Z, CZ, H", q2(2, "h q[0];\nh q[1];\nz q[0];\nz q[1];\ncz q[0],q[1];\nh q[0];\nh q[1];"))], {}),
    ("v20", "medium", ["grover_oracle", "endianness"], "statevector", 2,
     "Prepare the state left after one Grover iteration that searches for |10>, starting from |++> "
     "(Qiskit convention: the rightmost character is q[0]).",
     q2(2, "x q[1];"),
     [("found |01> instead", q2(2, "x q[0];")),
      ("the starting state |++>", q2(2, "h q[0];\nh q[1];"))],
     [("the full Grover iteration",
       q2(2, "h q[0];\nh q[1];\nx q[0];\ncz q[0],q[1];\nx q[0];\nh q[0];\nh q[1];\nx q[0];\nx q[1];\ncz q[0],q[1];\nx q[0];\nx q[1];\nh q[0];\nh q[1];"))], {}),
    ("v21", "medium", ["grover_oracle", "multi_controlled"], "unitary", 3,
     "Implement the bit-flip oracle for f(x) = x0 OR x1: |x0, x1, y> -> |x0, x1, y XOR f(x)>, with x0 on q[0], x1 on q[1] and y on q[2].",
     q2(3, "cx q[0],q[2];\ncx q[1],q[2];\nccx q[0],q[1],q[2];"),
     [("XOR instead of OR", q2(3, "cx q[0],q[2];\ncx q[1],q[2];")),
      ("AND instead of OR", q2(3, "ccx q[0],q[1],q[2];"))],
     [("NOT(NOT x0 AND NOT x1)", q2(3, "x q[0];\nx q[1];\nccx q[0],q[1],q[2];\nx q[0];\nx q[1];\nx q[2];"))], {}),

    # --- rotations and gate sets ----------------------------------------------------
    ("v22", "medium", ["param_rotation"], "unitary", 1,
     "Implement the single-qubit unitary U = RZ(pi/2) * RY(pi/3) (a matrix product).",
     q2(1, "ry(pi/3) q[0];\nrz(pi/2) q[0];"),
     [("order reversed: RY(pi/3) * RZ(pi/2)", q2(1, "rz(pi/2) q[0];\nry(pi/3) q[0];")),
      ("half angle on RY", q2(1, "ry(pi/6) q[0];\nrz(pi/2) q[0];"))],
     [("same, in Qiskit Python", py("from math import pi\nqc = QuantumCircuit(1)\nqc.ry(pi / 3, 0)\nqc.rz(pi / 2, 0)"))], {}),
    ("v23", "medium", ["global_phase", "gate_set"], "unitary", 1,
     "Implement the Hadamard gate using only RX and RZ rotations. Global phase does not matter.",
     q2(1, "rz(pi/2) q[0];\nrx(pi/2) q[0];\nrz(pi/2) q[0];"),
     [("RX(pi/2) alone", q2(1, "rx(pi/2) q[0];")),
      ("last RZ missing", q2(1, "rz(pi/2) q[0];\nrx(pi/2) q[0];"))],
     [("RX(pi/2), RZ(pi/2), RX(pi/2)", q2(1, "rx(pi/2) q[0];\nrz(pi/2) q[0];\nrx(pi/2) q[0];"))],
     {"allowed_gates": ["rx", "rz"]}),
    ("v24", "medium", ["param_rotation", "gate_set"], "unitary", 2,
     "Implement RZZ(pi/3) on q[0] and q[1] using only CX and RZ gates.",
     q2(2, "cx q[0],q[1];\nrz(pi/3) q[1];\ncx q[0],q[1];"),
     [("half angle: RZ(pi/6)", q2(2, "cx q[0],q[1];\nrz(pi/6) q[1];\ncx q[0],q[1];")),
      ("second CX missing", q2(2, "cx q[0],q[1];\nrz(pi/3) q[1];"))],
     [("mirrored: CX into q[0]", q2(2, "cx q[1],q[0];\nrz(pi/3) q[0];\ncx q[1],q[0];"))],
     {"allowed_gates": ["cx", "rz"]}),
    ("v25", "hard", ["relative_phase", "gate_set"], "unitary", 2,
     "Implement the iSWAP gate on q[0] and q[1] using only S, H and CX gates.",
     q2(2, "s q[0];\ns q[1];\nh q[0];\ncx q[0],q[1];\ncx q[1],q[0];\nh q[1];"),
     [("plain SWAP: the S gates are missing", q2(2, "h q[0];\ncx q[0],q[1];\ncx q[1],q[0];\nh q[1];")),
      ("SWAP from three CX", q2(2, "cx q[0],q[1];\ncx q[1],q[0];\ncx q[0],q[1];"))],
     [("mirrored (iSWAP is symmetric)", q2(2, "s q[1];\ns q[0];\nh q[1];\ncx q[1],q[0];\ncx q[0],q[1];\nh q[0];"))],
     {"allowed_gates": ["s", "h", "cx"]}),
    ("v26", "medium", ["param_rotation", "relative_phase"], "statevector", 1,
     "Prepare cos(pi/8)|0> + e^(i*pi/4) sin(pi/8)|1>.",
     q2(1, "ry(pi/4) q[0];\np(pi/4) q[0];"),
     [("half-angle slip: RY(pi/8)", q2(1, "ry(pi/8) q[0];\np(pi/4) q[0];")),
      ("phase sign flipped", q2(1, "ry(pi/4) q[0];\np(-pi/4) q[0];"))],
     [("RZ instead of P (differs only by global phase)", q2(1, "ry(pi/4) q[0];\nrz(pi/4) q[0];"))], {}),
    ("v27", "easy", ["control_target"], "unitary", 2,
     "Apply a controlled-Hadamard with control q[0] and target q[1].",
     q2(2, "ch q[0],q[1];"),
     [("control and target swapped", q2(2, "ch q[1],q[0];")),
      ("CNOT instead of controlled-H", q2(2, "cx q[0],q[1];"))],
     [("HGate().control(1) in Qiskit Python",
       py("from qiskit.circuit.library import HGate\nqc = QuantumCircuit(2)\nqc.append(HGate().control(1), [0, 1])"))], {}),

    # --- measurement, gate count, hard state prep -------------------------------------
    ("v28", "easy", ["measurement", "basic"], "statevector", 3,
     "Prepare the GHZ state (|000> + |111>)/sqrt(2) on q[0..2], then measure all three qubits into a 3-bit classical register.",
     q2(3, "h q[0];\ncx q[0],q[1];\ncx q[1],q[2];\nmeasure q[0] -> c[0];\nmeasure q[1] -> c[1];\nmeasure q[2] -> c[2];", creg=3),
     [("no measurements", q2(3, "h q[0];\ncx q[0],q[1];\ncx q[1],q[2];", creg=3)),
      ("q[2] not measured", q2(3, "h q[0];\ncx q[0],q[1];\ncx q[1],q[2];\nmeasure q[0] -> c[0];\nmeasure q[1] -> c[1];", creg=3))],
     [("fan-out CNOTs, measured in reverse order",
       q2(3, "h q[0];\ncx q[0],q[1];\ncx q[0],q[2];\nmeasure q[2] -> c[2];\nmeasure q[1] -> c[1];\nmeasure q[0] -> c[0];", creg=3))],
     {"measure": "require"}),
    ("v29", "medium", ["gate_set", "control_target"], "unitary", 3,
     "Swap q[0] and q[2] using only CX gates, at most 3 of them.",
     q2(3, "cx q[0],q[2];\ncx q[2],q[0];\ncx q[0],q[2];"),
     [("only two CX", q2(3, "cx q[0],q[2];\ncx q[2],q[0];")),
      ("swaps q[0] and q[1] instead", q2(3, "cx q[0],q[1];\ncx q[1],q[0];\ncx q[0],q[1];"))],
     [("CX(2,0), CX(0,2), CX(2,0)", q2(3, "cx q[2],q[0];\ncx q[0],q[2];\ncx q[2],q[0];"))],
     {"allowed_gates": ["cx"], "max_gates": 3}),
    ("v30", "hard", ["basic"], "statevector", 4,
     "Prepare the 4-qubit Dicke state D(4,2): the equal superposition of all six basis states with exactly two 1s.",
     stateprep(4, {3: "1", 5: "1", 6: "1", 9: "1", 10: "1", 12: "1"}),
     [("W state (exactly one 1) instead", stateprep(4, {1: "1", 2: "1", 4: "1", 8: "1"})),
      ("|0101> term missing", stateprep(4, {3: "1", 6: "1", 9: "1", 10: "1", 12: "1"}))],
     [("same state times a global phase of -1", stateprep(4, {3: "-1", 5: "-1", 6: "-1", 9: "-1", 10: "-1", 12: "-1"}))], {}),
]


# For tasks that limit the gate set, the reference is itself a decomposition, so it
# is checked here against the gate the task names, without using grader.py.
INTENT = {
    "v05": lib_qft(3, inverse=True),
    "v06": lib_qft(4),
    "v09": q2(2, "cp(pi/4) q[0],q[1];"),
    "v10": q2(1, "sx q[0];"),
    "v13": q2(3, "ccx q[0],q[2],q[1];"),
    "v17": py("qc = QuantumCircuit(3)\nqc.ccz(0, 1, 2)"),
    "v18": py("from qiskit.circuit.library import DiagonalGate\nd = [1] * 8\nd[4] = -1\nd[6] = -1\n"
              "qc = QuantumCircuit(3)\nqc.append(DiagonalGate(d), [0, 1, 2])"),
    "v23": q2(1, "h q[0];"),
    "v24": q2(2, "rzz(pi/3) q[0],q[1];"),
    "v25": py("qc = QuantumCircuit(2)\nqc.iswap(0, 1)"),
    "v29": q2(3, "swap q[0],q[2];"),
}


def _circuit(code):
    from qiskit import qasm2
    if code.startswith("OPENQASM"):
        return qasm2.loads(code, custom_instructions=qasm2.LEGACY_CUSTOM_INSTRUCTIONS)
    env = {}
    exec(code, env)
    return env["qc"]


def check_intent(tasks):
    from qiskit.quantum_info import Operator
    for t in tasks:
        if t["id"] in INTENT:
            ref, want = Operator(_circuit(t["reference"])), Operator(_circuit(INTENT[t["id"]]))
            if ref.num_qubits > t["n_qubits"]:
                # Ancillas start in |0>, so only those input columns are promised.
                cols = 2 ** t["n_qubits"]
                a, b = ref.data[:, :cols], want.data[:, :cols]
                k = np.unravel_index(np.argmax(np.abs(b)), b.shape)
                assert np.allclose(a, a[k] / b[k] * b, atol=1e-9), f"{t['id']}: reference is not the intended gate"
                continue
            assert ref.equiv(want), f"{t['id']}: reference is not the intended gate"
    print(f"{len(INTENT)} gate-set references match the intended gate")


def main():
    tasks, cases = [], []
    for tid, diff, traps, mode, n, prompt, ref, mutants, variants, extra in TASKS:
        tasks.append({"id": tid, "difficulty": diff, "traps": traps, "mode": mode,
                      "n_qubits": n, "prompt": prompt, "reference": ref, **extra})
        cases += [{"id": tid, "kind": "mutant", "note": note, "code": code} for note, code in mutants]
        cases += [{"id": tid, "kind": "variant", "note": note, "code": code} for note, code in variants]
    check_intent(tasks)
    (ROOT / "tasks" / "v2.jsonl").write_text("".join(json.dumps(t) + "\n" for t in tasks))
    (ROOT / "tests" / "fixtures" / "v2_cases.jsonl").write_text("".join(json.dumps(c) + "\n" for c in cases))
    print(f"{len(tasks)} tasks, {sum(c['kind'] == 'mutant' for c in cases)} mutants, "
          f"{sum(c['kind'] == 'variant' for c in cases)} variants")


if __name__ == "__main__":
    main()
