"""Grader validation with no model calls.

For every pilot task: the reference passes, every hand-written mutant fails,
and every equivalent-but-different variant passes.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import grader  # noqa: E402

TASKS = {t["id"]: t for t in grader.load_jsonl(ROOT / "tasks" / "pilot.jsonl")}
CASES = grader.load_jsonl(ROOT / "tests" / "fixtures" / "pilot_cases.jsonl")
MUTANTS = [c for c in CASES if c["kind"] == "mutant"]
VARIANTS = [c for c in CASES if c["kind"] == "variant"]


def _ids(cases):
    return [f"{c['id']}:{c['note'][:40]}" for c in cases]


@pytest.mark.parametrize("tid", sorted(TASKS))
def test_reference_passes(tid):
    passed, reason, detail, _ = grader.grade_one(TASKS[tid], TASKS[tid]["reference"])
    assert passed, f"{reason} {detail}"


@pytest.mark.parametrize("case", MUTANTS, ids=_ids(MUTANTS))
def test_mutant_fails(case):
    passed, reason, detail, _ = grader.grade_one(TASKS[case["id"]], case["code"])
    assert not passed, f"mutant survived: {case['note']}"
    assert reason not in ("parse_error", "timeout", "simulation_error"), f"failed for the wrong reason: {reason} {detail}"


@pytest.mark.parametrize("case", VARIANTS, ids=_ids(VARIANTS))
def test_variant_passes(case):
    passed, reason, detail, _ = grader.grade_one(TASKS[case["id"]], case["code"])
    assert passed, f"{case['note']}: {reason} {detail}"


def test_every_task_has_two_mutants_and_a_variant():
    for tid in TASKS:
        assert sum(c["id"] == tid for c in MUTANTS) >= 2, tid
        assert sum(c["id"] == tid for c in VARIANTS) >= 1, tid


# --- grader behavior -------------------------------------------------------

BELL = TASKS["p01"]


def test_parse_error_reported():
    passed, reason, _, _ = grader.grade_one(BELL, 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\nhh q[0];\n')
    assert (passed, reason) == (False, "parse_error")


def test_too_few_qubits_reported():
    code = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\nh q[0];\n'
    passed, reason, _, _ = grader.grade_one(BELL, code)
    assert (passed, reason) == (False, "wrong_qubit_count")


def test_idle_clean_ancilla_passes():
    code = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[3];\nh q[0];\ncx q[0],q[1];\n'
    passed, reason, _, _ = grader.grade_one(BELL, code)
    assert (passed, reason) == (True, "pass")


def test_too_many_ancillas_reported():
    code = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[6];\nh q[0];\ncx q[0],q[1];\n'
    passed, reason, _, _ = grader.grade_one(BELL, code)
    assert (passed, reason) == (False, "too_many_ancillas")


def test_dirty_ancilla_fails_statevector():
    # Bell pair on task qubits, but the ancilla is left in |1>.
    code = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[3];\nh q[0];\ncx q[0],q[1];\nx q[2];\n'
    passed, reason, _, _ = grader.grade_one(BELL, code)
    assert (passed, reason) == (False, "dirty_ancilla")


def test_entangled_ancilla_fails_statevector():
    # Copies q[0] into the ancilla and never uncomputes it: task qubits alone are mixed.
    code = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[3];\nh q[0];\ncx q[0],q[1];\ncx q[0],q[2];\n'
    passed, reason, _, _ = grader.grade_one(BELL, code)
    assert (passed, reason) == (False, "dirty_ancilla")


def test_measured_ancilla_fails():
    code = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[3];\ncreg c[3];\nh q[0];\ncx q[0],q[1];\nmeasure q[2] -> c[2];\n'
    passed, reason, _, _ = grader.grade_one(BELL, code)
    assert (passed, reason) == (False, "ancilla_measured")


TOFFOLI_TASK = {
    "id": "t_ccx", "mode": "unitary", "n_qubits": 3,
    "reference": 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[3];\nccx q[0],q[1],q[2];\n',
}
C3X_TASK = {
    "id": "t_c3x", "mode": "unitary", "n_qubits": 4,
    "reference": 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[4];\nc3x q[0],q[1],q[2],q[3];\n',
}


def test_c3x_via_clean_ancilla_passes_unitary():
    # Standard compute / apply / uncompute with one ancilla (q[4]).
    code = ('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[5];\n'
            'ccx q[0],q[1],q[4];\nccx q[2],q[4],q[3];\nccx q[0],q[1],q[4];\n')
    passed, reason, _, _ = grader.grade_one(C3X_TASK, code)
    assert (passed, reason) == (True, "pass")


def test_c3x_without_uncompute_is_dirty_unitary():
    code = ('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[5];\n'
            'ccx q[0],q[1],q[4];\nccx q[2],q[4],q[3];\n')
    passed, reason, _, _ = grader.grade_one(C3X_TASK, code)
    assert (passed, reason) == (False, "dirty_ancilla")


def test_clean_ancilla_but_wrong_gate_is_not_equivalent():
    code = ('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[4];\n'
            'ccx q[0],q[1],q[3];\ncx q[3],q[2];\nccx q[0],q[1],q[3];\ncx q[0],q[2];\n')
    passed, reason, _, _ = grader.grade_one(TOFFOLI_TASK, code)
    assert (passed, reason) == (False, "not_equivalent")


def test_toffoli_via_clean_ancilla_passes():
    code = ('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[4];\n'
            'ccx q[0],q[1],q[3];\ncx q[3],q[2];\nccx q[0],q[1],q[3];\n')
    passed, reason, _, _ = grader.grade_one(TOFFOLI_TASK, code)
    assert (passed, reason) == (True, "pass")


def test_python_without_qc_variable_is_parse_error():
    passed, reason, detail, _ = grader.grade_one(BELL, "from qiskit import QuantumCircuit\ncirc = QuantumCircuit(2)\n")
    assert (passed, reason) == (False, "parse_error")
    assert "qc" in detail


def test_python_exception_is_parse_error():
    passed, reason, _, _ = grader.grade_one(BELL, "raise RuntimeError('boom')\n")
    assert (passed, reason) == (False, "parse_error")


def test_reset_is_unsupported():
    code = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\nreset q[0];\nh q[0];\ncx q[0],q[1];\n'
    passed, reason, _, _ = grader.grade_one(BELL, code)
    assert (passed, reason) == (False, "unsupported_op")


def test_qasm3_supported():
    code = 'OPENQASM 3.0;\ninclude "stdgates.inc";\nqubit[2] q;\nh q[0];\ncx q[0], q[1];\n'
    passed, reason, detail, _ = grader.grade_one(BELL, code)
    assert passed, f"{reason} {detail}"


def test_barrier_ignored():
    code = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\nh q[0];\nbarrier q;\ncx q[0],q[1];\n'
    assert grader.grade_one(BELL, code)[0]


def test_wrong_state_reports_fidelity():
    passed, reason, _, fid = grader.grade_one(BELL, 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\nh q[0];\n')
    assert (passed, reason) == (False, "wrong_state")
    assert fid == pytest.approx(0.25)  # |<Bell|(|00>+|01>)/sqrt2>|^2


def test_summary_counts_claim_mismatches():
    subs = [
        {"id": "p01", "code": BELL["reference"], "claimed_success": True},
        {"id": "p02", "code": 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\nx q[1];\n', "claimed_success": True},
    ]
    tasks = [TASKS["p01"], TASKS["p02"], TASKS["p03"]]
    s = grader.summarize(grader.grade(tasks, subs))
    assert s["overall"] == {"passed": 1, "total": 3}  # p03 counted as no_submission
    assert s["claimed_success_but_failed"] == {"count": 1, "of_claimed": 2}
    assert s["by_trap"]["endianness"] == {"passed": 0, "total": 1}


# --- v2 set and condition B feedback ------------------------------------------

V2 = {t["id"]: t for t in grader.load_jsonl(ROOT / "tasks" / "v2.jsonl")}
V2_CASES = grader.load_jsonl(ROOT / "tests" / "fixtures" / "v2_cases.jsonl")


@pytest.mark.parametrize("tid", sorted(V2))
def test_v2_reference_passes(tid):
    passed, reason, detail, _ = grader.grade_one(V2[tid], V2[tid]["reference"])
    assert passed, f"{reason} {detail}"


@pytest.mark.parametrize("case", V2_CASES, ids=[f"{c['id']}-{c['kind']}-{i}" for i, c in enumerate(V2_CASES)])
def test_v2_fixture(case):
    passed = grader.grade_one(V2[case["id"]], case["code"])[0]
    assert passed == (case["kind"] == "variant"), case["note"]


def test_feedback_never_shows_the_reference_or_a_verdict():
    sys.path.insert(0, str(ROOT / "scripts"))
    import exec_feedback
    for case in V2_CASES:
        out = "\n".join(exec_feedback.describe(V2[case["id"]], case["code"])).lower()
        assert "reference" not in out and "pass" not in out and "fail" not in out, case["note"]
        assert "output" in out
