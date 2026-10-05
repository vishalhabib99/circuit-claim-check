# Independent verification. Does NOT import grader.py or _runner.py.
# For each attack: run it under a stand-in runner that mimics _runner's stdin
# protocol, capture (a) the file the grader would load and (b) the qc the
# submission actually declares, and compare BOTH to the task's reference.
import json, subprocess, sys, tempfile, secrets, os
from pathlib import Path
import numpy as np
from qiskit import qasm2, qpy
from qiskit.quantum_info import Operator, Statevector

PY = sys.executable
HERE = Path(__file__).parent
HARNESS = str(HERE / "standalone_runner.py")
TASKS = {json.loads(l)["id"]: json.loads(l)
         for l in open(HERE.parent.parent / "runs" / "all_tasks_v2.jsonl")} \
    if (HERE.parent.parent / "runs" / "all_tasks_v2.jsonl").exists() else {}
# fallback: read tasks from repo
if not TASKS:
    repo = Path(os.path.expanduser("~/code/circuit-claim-check"))
    TASKS = {json.loads(l)["id"]: json.loads(l) for l in open(repo/"runs"/"all_tasks_v2.jsonl")}

def circ(code):
    return qasm2.loads(code)

def op(qc): return Operator(qc).data
def sv(qc): return Statevector.from_label("0"*qc.num_qubits).evolve(qc).data

def eq_phase(a, b):
    a=np.asarray(a); b=np.asarray(b)
    if a.shape!=b.shape: return False
    k=np.unravel_index(np.argmax(np.abs(b)), b.shape)
    if abs(b[k])<1e-12: return False
    ph=a[k]/b[k]; ph/=abs(ph)
    return bool(np.allclose(a, ph*b, atol=1e-9))

attacks=[json.loads(l) for l in open(HERE/"attacks.jsonl") if l.strip()]
results=[]
for atk in attacks:
    tid=atk["id"]; code=atk["code"]; task=TASKS[tid]; mode=task["mode"]
    ref=circ(task["reference"])
    with tempfile.TemporaryDirectory() as tmp:
        src=Path(tmp)/"s.py"; src.write_text(code)
        out=Path(tmp)/(secrets.token_hex(8)+".qpy"); nonce=secrets.token_hex(8)
        subprocess.run([PY,HARNESS,str(src)], input=f"{out}\n{nonce}\n",
            capture_output=True, text=True, cwd=tmp,
            env={"PATH":os.environ.get("PATH","")})
        graded=qpy.load(open(out,"rb"))[0]
    # declared qc: exec only the code BEFORE it reads stdin (no swap happens)
    prefix=code.split("lines = np.loadtxt")[0]
    g={}; exec(prefix,g); declared=g["qc"]
    if mode=="unitary":
        rf=op(ref); gg=op(graded); dd=op(declared)
    else:
        rf=sv(ref); gg=sv(graded); dd=sv(declared)
    graded_ok=eq_phase(gg,rf); declared_ok=eq_phase(dd,rf)
    wrongpass = graded_ok and not declared_ok
    results.append((tid,mode,graded_ok,declared_ok,wrongpass))
    print(f"{tid} [{mode}]: graded_matches_ref={graded_ok}  declared_qc_matches_ref={declared_ok}  -> WRONG-PASS={wrongpass}")

print()
print("confirmed wrong-passes:", sum(r[4] for r in results), "/", len(results))
