"""Regression tests from red team 1 (runs/redteam1/FINDINGS.md).

Every confirmed wrong-pass (A01-A16) must now fail, every attack the grader
already caught (F01-F14) must still fail, and the crash cases (C01-C03) must
fail one submission without taking down the grading run.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import grader  # noqa: E402

RT = ROOT / "runs" / "redteam1"
TASKS = {t["id"]: t for t in grader.load_jsonl(ROOT / "tasks" / "pilot.jsonl") + grader.load_jsonl(ROOT / "tasks" / "blind.jsonl")}
ATTACKS = grader.load_jsonl(RT / "attacks.jsonl")
CRASHES = [c for n in (1, 2, 3) for c in grader.load_jsonl(RT / f"crash_C0{n}.jsonl")]


def _label(a):
    return a.get("attack", a["id"])


@pytest.mark.parametrize("attack", ATTACKS, ids=[_label(a) for a in ATTACKS])
def test_attack_fails(attack):
    # A02 used to pass or fail at random (an unseeded reset), so check it repeatedly.
    for _ in range(5 if _label(attack) == "A02" else 1):
        passed, reason, detail, _ = grader.grade_one(TASKS[attack["id"]], attack["code"])
        assert not passed, f"{_label(attack)} still passes"


@pytest.mark.parametrize("case", CRASHES, ids=["C01", "C02", "C03"])
def test_crash_case_fails_without_crashing_the_run(case):
    results = grader.grade([TASKS["p01"]], [case, {"id": "p01", "code": TASKS["p01"]["reference"]}])
    assert [r.passed for r in results] == [False, True]


def test_qasm_without_version_line_says_so():
    code = 'include "qelib1.inc";\nqreg q[2];\nh q[0];\ncx q[0],q[1];\n'
    passed, reason, detail, _ = grader.grade_one(TASKS["p01"], code)
    assert (passed, reason) == (False, "parse_error")
    assert "OPENQASM" in detail and "Python" not in detail


def test_task_register_named_q_is_used_even_if_declared_second():
    # W2: the mirror of A16, a correct answer that used to fail.
    code = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg a[1];\nqreg q[2];\nx q[0];\n'
    passed, reason, detail, _ = grader.grade_one(TASKS["p02"], code)
    assert passed, f"{reason} {detail}"


def test_tiny_numerical_noise_still_passes():
    # Exact answers written with full double-precision constants must still pass.
    code = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\nry(1.0471975511965976) q[0];\n'
    passed, reason, detail, _ = grader.grade_one(TASKS["p05"], code)
    assert passed, f"{reason} {detail}"


# --- red team 2 (runs/redteam2/FINDINGS.md) --------------------------------

RT2_ATTACKS = grader.load_jsonl(RT.parent / "redteam2" / "attacks.jsonl")


@pytest.mark.parametrize("attack", RT2_ATTACKS, ids=[f"RT2-0{i + 1}" for i in range(len(RT2_ATTACKS))])
def test_redteam2_attack_fails(attack):
    passed, reason, detail, _ = grader.grade_one(TASKS[attack["id"]], attack["code"])
    assert not passed, f"still passes: {reason} {detail}"


def test_qasm2_gate_defined_after_a_statement_on_the_same_line_is_honored():
    code = 'OPENQASM 2.0;\nqreg q[2]; gate cx a,b { U(0,0,0) a; } /* x */\ncx q[1],q[0];\n'
    assert not grader.grade_one(TASKS["p06"], code)[0]


def test_qasm2_c3x_from_legacy_set_still_works():
    code = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[4];\nc3x q[0],q[1],q[2],q[3];\n'
    passed, reason, detail, _ = grader.grade_one(TASKS["p15"], code)
    assert passed, f"{reason} {detail}"


@pytest.mark.parametrize("code", [
    "import sys\nfrom qiskit import QuantumCircuit\nqc = QuantumCircuit(2); qc.cx(1, 0)\n",
    "from qiskit import QuantumCircuit\nimport atexit\nqc = QuantumCircuit(2); qc.cx(1, 0)\n",
    "from qiskit import QuantumCircuit\nqc = QuantumCircuit(2); qc.cx(1, 0)\nf = (lambda: 0).__globals__\n",
    "from qiskit import QuantumCircuit\nqc = QuantumCircuit(2); qc.cx(1, 0)\ng = (x for x in [1]); fr = g.gi_frame\n",
    "from qiskit import QuantumCircuit\nqc = QuantumCircuit(2); qc.cx(1, 0)\nopen('x', 'w')\n",
    "from qiskit import QuantumCircuit\nfrom qiskit.circuit import quantumcircuit\nqc = QuantumCircuit(2); qc.cx(1, 0)\nquantumcircuit.sys\n",
    "from qiskit import QuantumCircuit\nqc = QuantumCircuit(2); qc.cx(1, 0)\ngetattr(qc, 'x')\n",
])
def test_python_outside_the_allowed_subset_is_rejected(code):
    passed, reason, detail, _ = grader.grade_one(TASKS["p06"], code)
    assert (passed, reason) == (False, "disallowed_python"), f"{reason} {detail}"


def test_ordinary_python_answer_still_passes():
    code = ("import math\nimport numpy as np\nfrom qiskit import QuantumCircuit\nfrom qiskit.circuit.library import QFTGate\n"
            "qc = QuantumCircuit(2)\nqc.cx(1, 0)\nqc.rz(2 * math.pi, 0)\nqc.rz(np.pi * 0, 1)\n")
    passed, reason, detail, _ = grader.grade_one(TASKS["p06"], code)
    assert passed, f"{reason} {detail}"


# --- red team 3 (runs/redteam3/FINDINGS.md) --------------------------------

RT3_ATTACKS = grader.load_jsonl(RT.parent / "redteam3" / "attacks.jsonl")


@pytest.mark.parametrize("attack", RT3_ATTACKS, ids=[f"RT3-0{i + 1}" for i in range(len(RT3_ATTACKS))])
def test_redteam3_attack_fails(attack):
    passed, reason, detail, _ = grader.grade_one(TASKS[attack["id"]], attack["code"])
    assert not passed, f"still passes: {reason} {detail}"


def test_qasm2_legacy_gate_with_the_word_gate_in_a_comment_passes():
    # W-rt3-1: a comment must not block the legacy-gate fallback.
    code = 'OPENQASM 2.0;\n// this gate is great\nqreg q[2]; // opaque too\nrzz(pi/4) q[0],q[1];\n'
    passed, reason, detail, _ = grader.grade_one(TASKS["p20"], code)
    assert passed, f"{reason} {detail}"


@pytest.mark.parametrize("code", [
    "from qiskit import QuantumCircuit\nclass G: pass\nqc = QuantumCircuit(2); qc.cx(1, 0)\n",
    "from qiskit import QuantumCircuit\nimport qiskit.qpy\nqc = QuantumCircuit(2); qc.cx(1, 0)\n",
    "from qiskit import QuantumCircuit, qpy\nqc = QuantumCircuit(2); qc.cx(1, 0)\n",
    "import qiskit\nfrom qiskit import QuantumCircuit\nqiskit.QuantumCircuit.cx = None\nqc = QuantumCircuit(2)\n",
    "from qiskit import QuantumCircuit\nimport numpy as np\nqc = QuantumCircuit(2); qc.cx(1, 0)\nnp.zeros(1).tofile('x')\n",
])
def test_python_new_subset_rules(code):
    passed, reason, detail, _ = grader.grade_one(TASKS["p06"], code)
    assert (passed, reason) == (False, "disallowed_python"), f"{reason} {detail}"


def test_python_exit_inside_submission_fails():
    code = "from qiskit import QuantumCircuit\nqc = QuantumCircuit(2); qc.cx(1, 0)\nprint('RUNNER_OK x')\nraise SystemExit(0)\n"
    passed, reason, _, _ = grader.grade_one(TASKS["p06"], code)
    assert (passed, reason) == (False, "parse_error")


def test_python_is_refused_without_a_sandbox(monkeypatch):
    monkeypatch.setattr(grader, "SANDBOX_EXEC", None)
    monkeypatch.delenv("CIRCUIT_GRADER_TRUST_PYTHON", raising=False)
    code = "from qiskit import QuantumCircuit\nqc = QuantumCircuit(2); qc.cx(1, 0)\n"
    passed, reason, _, _ = grader.grade_one(TASKS["p06"], code)
    assert (passed, reason) == (False, "python_needs_sandbox")


# --- red team 4 (runs/redteam4/FINDINGS.md) --------------------------------

RT4_ATTACKS = grader.load_jsonl(RT.parent / "redteam4" / "attacks.jsonl")


@pytest.mark.parametrize("attack", RT4_ATTACKS, ids=[f"RT4-0{i + 1}" for i in range(len(RT4_ATTACKS))])
def test_redteam4_attack_fails(attack):
    passed, reason, detail, _ = grader.grade_one(TASKS[attack["id"]], attack["code"])
    assert not passed, f"still passes: {reason} {detail}"


def test_custom_gate_named_measure_is_not_a_measurement():
    # Same name-vs-class confusion as RT4: an identity gate named "measure" must not
    # satisfy a task that requires measuring every qubit.
    code = (
        "from qiskit import QuantumCircuit\n"
        "fake = QuantumCircuit(1).to_gate().copy(name='measure')\n"
        "qc = QuantumCircuit(2, 2)\nqc.h(0)\nqc.cx(0, 1)\nqc.append(fake, [0])\nqc.append(fake, [1])\n"
    )
    passed, reason, detail, _ = grader.grade_one(TASKS["p12"], code)
    assert (passed, reason) == (False, "missing_measurement"), f"{reason} {detail}"


@pytest.mark.parametrize("tid,code", [
    ("p01", "from qiskit import QuantumCircuit\nqc = QuantumCircuit(2)\nqc.h(0)\nqc.barrier()\nqc.delay(100, 0)\nqc.cx(0, 1)\n"),
    ("p12", "from qiskit import QuantumCircuit\nqc = QuantumCircuit(2, 2)\nqc.h(0)\nqc.cx(0, 1)\nqc.barrier()\nqc.measure([0, 1], [0, 1])\n"),
])
def test_real_barrier_delay_and_measure_still_pass_from_python(tid, code):
    passed, reason, detail, _ = grader.grade_one(TASKS[tid], code)
    assert passed, f"{reason} {detail}"
