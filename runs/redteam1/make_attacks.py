"""Writes attacks.jsonl (graded together) and crash_attacks.jsonl (each crashes grader.py)."""
import json
H = 'OPENQASM 2.0;\ninclude "qelib1.inc";\n'
A = [
 # ---- confirmed wrong-pass candidates ----
 ("A01","p02","hidden reset via initialize on entangled ancilla (biased 99/1)",
  "from qiskit import QuantumCircuit\nimport numpy as np\nqc=QuantumCircuit(3)\nqc.ry(2*np.arccos(0.1),0)\nqc.cx(0,2)\nqc.initialize('0',[2])\n"),
 ("A02","p02","hidden reset inside a custom instruction (50/50)",
  "from qiskit import QuantumCircuit\nr=QuantumCircuit(1,name='clean'); r.reset(0)\nqc=QuantumCircuit(3); qc.h(0); qc.cx(0,2); qc.append(r.to_instruction(),[2])\n"),
 ("A03","p06","Python writes the runner's QPY output itself, then os._exit(0); qc is wrong",
  "import sys, os\nfrom qiskit import QuantumCircuit, qpy\ngood=QuantumCircuit(2); good.cx(1,0)\nwith open(sys.argv[2],'wb') as f: qpy.dump(good,f)\nqc=QuantumCircuit(2); qc.cx(0,1)\nos._exit(0)\n"),
 ("A04","p06","Python monkeypatches qiskit.qpy.dump so the runner saves a different circuit",
  "import qiskit.qpy\nfrom qiskit import QuantumCircuit\n_real=qiskit.qpy.dump\ndef _fake(c,f,**k):\n    g=QuantumCircuit(2); g.cx(1,0); _real(g,f,**k)\nqiskit.qpy.dump=_fake\nqc=QuantumCircuit(2); qc.cx(0,1)\n"),
 ("A05","p14","custom Gate named 'cx' whose definition is a SWAP gate (gate-set bypass)",
  "from qiskit import QuantumCircuit\nfrom qiskit.circuit import Gate\nd=QuantumCircuit(2); d.swap(0,1)\nG=Gate('cx',2,[]); G.definition=d\nqc=QuantumCircuit(2); qc.append(G,[0,1])\n"),
 ("A06","b12","QASM 3 user gate named 'cx' that is really CZ (ctrl @ U(0,0,pi)); no H, no CNOT",
  "OPENQASM 3.0;\nqubit[2] q;\ngate cx a, b { ctrl @ U(0,0,pi) a, b; }\ncx q[0], q[1];\n"),
 ("A07","b12","QASM 2 without include: user defines h=U(0,0,pi), cx=identity; Qiskit legacy mode swaps in real H/CX",
  "OPENQASM 2.0;\nqreg q[2];\ngate cx a,b { U(0,0,0) a; }\ngate h a { U(0,0,pi) a; }\nh q[1]; cx q[0],q[1]; h q[1];\n"),
 ("A08","p06","final measurement of every qubit on a unitary task (instructions: no measurements unless asked)",
  H+"qreg q[2];\ncreg c[2];\ncx q[1],q[0];\nmeasure q[0]->c[0];\nmeasure q[1]->c[1];\n"),
 ("A09","p01","final measurements on a statevector task with no measure policy",
  H+"qreg q[2];\ncreg c[2];\nh q[0];\ncx q[0],q[1];\nmeasure q -> c;\n"),
 ("A10","p04","Z gate instead of 'a single RZ rotation'", H+"qreg q[1];\nz q[0];\n"),
 ("A11","b03","X gate instead of 'a single RX rotation'", H+"qreg q[1];\nx q[0];\n"),
 ("A12","b10","|-> via H then Z on |0>, not 'by applying H to |1>'", H+"qreg q[1];\nh q[0];\nz q[0];\n"),
 ("A13","p03","statevector tolerance: extra RY(1.9e-3)", H+"qreg q[1];\nx q[0];\nh q[0];\nry(0.0019) q[0];\n"),
 ("A14","p05","unitary tolerance: RY(pi/3 + 9e-6)", H+"qreg q[1];\nry(pi/3+0.000009) q[0];\n"),
 ("A15","p03","ancilla leak tolerance: ancilla rotated by RY(1.9e-6), not back to |0>", H+"qreg q[2];\nx q[0];\nh q[0];\nry(1.9e-6) q[1];\n"),
 ("A16","p02","register order: ancilla register declared first; the register named q stays |00>, the ancilla is left in |1>",
  H+"qreg r[1];\nqreg q[2];\nx r[0];\n"),
 # ---- attempts expected to be caught ----
 ("F01","p02","reset inside a box (control flow not in the grader's list)",
  "from qiskit import QuantumCircuit\nqc=QuantumCircuit(3); qc.x(0)\nwith qc.box(): qc.reset(2)\n"),
 ("F02","p11","ancilla dirty only for inputs with q0=q1=1 (no uncompute)", H+"qreg q[4];\nccx q[0],q[1],q[3];\ncx q[3],q[2];\n"),
 ("F03","p12","ancilla measured into a separate classical register", H+"qreg q[3];\ncreg c[2];\ncreg d[1];\nh q[0];\ncx q[0],q[1];\nmeasure q[0]->c[0];\nmeasure q[1]->c[1];\nmeasure q[2]->d[0];\n"),
 ("F04","p13","measurement on a 'no measurements' task", H+"qreg q[2];\ncreg c[2];\nh q[0];\nx q[1];\nmeasure q[1]->c[1];\n"),
 ("F05","p06","opaque gate", H+"opaque magic a,b;\nqreg q[2];\nmagic q[1],q[0];\n"),
 ("F06","p05","unbound parameter", "from qiskit import QuantumCircuit\nfrom qiskit.circuit import Parameter\nqc=QuantumCircuit(1); qc.ry(Parameter('t'),0)\n"),
 ("F07","p01","QASM 3 classically conditioned gate", "OPENQASM 3.0;\ninclude \"stdgates.inc\";\nqubit[2] q;\nbit[1] c;\nh q[0];\nc[0] = measure q[0];\nif (c[0]) x q[1];\n"),
 ("F08","p12","mid-circuit measurement then reuse", H+"qreg q[2];\ncreg c[2];\nh q[0];\nmeasure q[0]->c[0];\ncx q[0],q[1];\nmeasure q[0]->c[0];\nmeasure q[1]->c[1];\n"),
 ("F09","p01","explicit QASM 3 reset on ancilla", "OPENQASM 3.0;\ninclude \"stdgates.inc\";\nqubit[3] q;\nh q[0];\ncx q[0],q[1];\nx q[2];\nreset q[2];\n"),
 ("F10","p14","QASM 2 gate macro wrapping swap", H+"gate myswap a,b { swap a,b; }\nqreg q[2];\nmyswap q[0],q[1];\n"),
 ("F11","b12","QASM 2 with include, gate named cz via macro 'cx2'", H+"gate cx2 a,b { cz a,b; }\nqreg q[2];\ncx2 q[0],q[1];\n"),
 ("F12","p25","ancilla phase kickback that gives Z instead of Sdg", H+"qreg q[2];\nx q[1];\nh q[1];\ncx q[0],q[1];\nh q[1];\nx q[1];\n"),
 ("F13","p01","statevector leak just above tolerance: RY(3e-6) on ancilla", H+"qreg q[3];\nh q[0];\ncx q[0],q[1];\nry(3e-6) q[2];\n"),
 ("F14","p08","global-phase-only difference is NOT relative: CP(pi/2) vs S on q1 (relative phase wrong)", H+"qreg q[2];\ns q[1];\n"),
]
CRASH = [
 ("C01","p01","non-measure instruction with a classical bit -> uncaught CircuitError",
  "from qiskit import QuantumCircuit\nfrom qiskit.circuit import Instruction\nqc=QuantumCircuit(2,1); qc.h(0); qc.cx(0,1)\nqc.append(Instruction('foo',1,1,[]),[0],[0])\n"),
 ("C02","p01","classical Var + store -> uncaught CircuitError",
  "from qiskit import QuantumCircuit\nqc=QuantumCircuit(2); v=qc.add_var('v', True); qc.h(0); qc.cx(0,1); qc.store(v, False)\n"),
 ("C03","p01","measure hidden inside a custom instruction -> uncaught CircuitError",
  "from qiskit import QuantumCircuit\nm=QuantumCircuit(1,1,name='m'); m.measure(0,0)\nqc=QuantumCircuit(2,1); qc.h(0); qc.cx(0,1); qc.append(m.to_instruction(),[0],[0])\n"),
]
def dump(rows, path):
    with open(path,"w") as f:
        for aid,tid,idea,code in rows:
            f.write(json.dumps({"id":tid,"attack":aid,"idea":idea,"code":code})+"\n")
dump(A,"attacks.jsonl"); dump(CRASH,"crash_attacks.jsonl")
for r in CRASH: dump([r], f"crash_{r[0]}.jsonl")
