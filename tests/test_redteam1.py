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
