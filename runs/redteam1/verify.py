"""Independent verification of each attack in attacks.jsonl. Does NOT import grader.py.
Builds each circuit, computes its actual matrix / state / instruction list with
qiskit.quantum_info + numpy, and compares with what the task text asks for."""
import json, os, sys, tempfile
import numpy as np
from qiskit import QuantumCircuit, qasm2, qasm3
from qiskit.quantum_info import Operator, Statevector, DensityMatrix, partial_trace, state_fidelity

ATT = {json.loads(l)["attack"]: json.loads(l) for l in open("attacks.jsonl")}

class _Exit(Exception): pass

def build(code, legacy=True):
    s = code.lstrip()
    if s.startswith("OPENQASM 2"):
        return qasm2.loads(code, custom_instructions=qasm2.LEGACY_CUSTOM_INSTRUCTIONS) if legacy else qasm2.loads(code)
    if s.startswith("OPENQASM 3"):
        return qasm3.loads(code)
    # Python: exec in a namespace we keep, with os._exit neutralised and a scratch argv.
    tmp = tempfile.mkdtemp()
    old_argv, old_exit = sys.argv, os._exit
    sys.argv = ["x", os.path.join(tmp, "src.py"), os.path.join(tmp, "out.qpy")]
    os._exit = lambda c=0: (_ for _ in ()).throw(_Exit())
    ns = {"__name__": "__submission__"}
    try:
        exec(code, ns)
    except _Exit:
        pass
    finally:
        sys.argv, os._exit = old_argv, old_exit
    return ns["qc"]

def ops(qc): return [i.operation.name for i in qc.data]
def cx(c, t, n):
    q = QuantumCircuit(n); q.cx(c, t); return Operator(q).data
def show(aid, verdict, detail):
    print(f"{aid} [{ATT[aid]['id']}] independent verdict: {verdict}\n    {detail}")

# A01/A02: mixed output state; exact density-matrix evolution (reset is deterministic there)
target01 = DensityMatrix(Statevector.from_label("01"))
for aid in ("A01", "A02"):
    qc = build(ATT[aid]["code"])
    rho = DensityMatrix.from_label("000").evolve(qc.decompose(reps=3))
    red = partial_trace(rho, [2])
    anc = partial_trace(rho, [0, 1])
    show(aid, "WRONG", f"ops={ops(qc)}; reduced task state is mixed, purity={np.real(np.trace(red.data@red.data)):.4f}, "
         f"fidelity with |01> = {state_fidelity(red, target01):.4f} (task asks exactly |01>); contains a reset the grader says it rejects")

# A03/A04: the circuit left in `qc` (what the instructions define as the answer)
ref = cx(1, 0, 2)
for aid in ("A03", "A04"):
    qc = build(ATT[aid]["code"])
    U = Operator(qc)
    show(aid, "WRONG", f"qc implements CX(control q0,target q1); equiv to task CX(control q1,target q0)? {U.equiv(Operator(ref))}; "
         f"max|diff|={np.max(np.abs(U.data-ref)):.3f}")

# A05: matrix is SWAP (correct) but the 'cx' is a disguised SWAP gate
qc = build(ATT["A05"]["code"])
_sw = QuantumCircuit(2); _sw.swap(0, 1)
inner = ops(qc.data[0].operation.definition)
show("A05", "WRONG (constraint)", f"top-level ops={ops(qc)}, but that 'cx' is defined as {inner}; one gate whose matrix is "
     f"{'SWAP' if Operator(qc).equiv(Operator(_sw)) else 'not SWAP'}; "
     f"single 'cx' equals a real CNOT? {Operator(qc).equiv(Operator(cx(0,1,2)))}. Task: 'using only CNOT gates'.")

# A06: the 'cx' is a CZ
qc = build(ATT["A06"]["code"])
g = qc.data[0].operation
gm = Operator(g.definition)
cz = np.diag([1, 1, 1, -1])
show("A06", "WRONG (constraint)", f"ops={ops(qc)}; gate named cx has matrix equal to CZ? {gm.equiv(Operator(cz))}; "
     f"equal to CNOT? {gm.equiv(Operator(cx(0,1,2)))}; no H and no real CNOT used. Task: 'using only H and CNOT gates'.")

# A07: the program's own gate definitions (strict OpenQASM 2 semantics) give the identity, not CZ
qc_strict = build(ATT["A07"]["code"], legacy=False)
U = Operator(qc_strict)
show("A07", "WRONG", f"parsed with the program's own definitions: U == I? {U.equiv(Operator(np.eye(4)))}; U == CZ? "
     f"{U.equiv(Operator(cz))}. Qiskit's LEGACY_CUSTOM_INSTRUCTIONS silently replaces the user's 'h'/'cx' with the standard gates.")

# A08/A09: measurements added where instructions forbid them
for aid in ("A08", "A09"):
    qc = build(ATT[aid]["code"])
    try:
        Operator(qc); unit = "is unitary"
    except Exception as e:
        unit = f"is NOT a unitary (Operator raises: {type(e).__name__})"
    show(aid, "WRONG (rule)", f"ops={ops(qc)} -> {ops(qc).count('measure')} measurements; circuit {unit}. Instructions: "
         "'Don't add measurements unless the task asks for them' and the task does not ask.")

# A10-A12: method constraints in task text
for aid, need in (("A10", "a single rz"), ("A11", "a single rx"), ("A12", "H applied to |1> (x then h)")):
    qc = build(ATT[aid]["code"])
    show(aid, "WRONG (constraint)", f"ops={ops(qc)}; task requires {need}.")

# A13: statevector off by RY(1.9e-3)
qc = build(ATT["A13"]["code"])
sv = Statevector(qc).data
minus = np.array([1, -1]) / np.sqrt(2)
show("A13", "WRONG (tolerance)", f"state={np.round(sv,6)}, target={np.round(minus,6)}, max|diff|={np.max(np.abs(sv-minus)):.2e}, "
     f"fidelity={abs(np.vdot(minus, sv))**2:.8f}")

# A14: unitary off by 9e-6 rad
qc = build(ATT["A14"]["code"])
r = QuantumCircuit(1); r.ry(np.pi/3, 0)
d = Operator(qc).data - Operator(r).data
show("A14", "WRONG (tolerance)", f"max|U - RY(pi/3)| = {np.max(np.abs(d)):.2e} (angle off by 9e-6 rad)")

# A15: ancilla not returned to |0>
qc = build(ATT["A15"]["code"])
sv = Statevector(qc)
p1 = sv.probabilities([1])[1]
show("A15", "WRONG (tolerance)", f"ancilla amplitude on |1> = {np.sqrt(p1):.2e}; rule says it must end in |0>")

# A16: the register literally named q
qc = build(ATT["A16"]["code"])
names = [(qc.find_bit(b).registers[0][0].name, qc.find_bit(b).registers[0][1]) for b in qc.qubits]
sv = Statevector(qc)
qidx = [i for i, (n, _) in enumerate(names) if n == "q"]
ridx = [i for i, (n, _) in enumerate(names) if n != "q"]
pq = sv.probabilities(qidx)
pr = sv.probabilities(ridx)
show("A16", "WRONG (by register name)", f"qubit order={names}; register q (q[0],q[1]) probs={pq} -> |00>, task asks q[0]=1 (|01>); "
     f"extra register r ends in |1> with prob {pr[1]:.0f} (ancilla must end |0>)")
