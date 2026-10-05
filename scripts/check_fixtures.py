"""Grade a task set's references, mutants and variants; print a log.

    python scripts/check_fixtures.py pilot|blind
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import grader  # noqa: E402


def main(name: str) -> int:
    tasks = {t["id"]: t for t in grader.load_jsonl(ROOT / "tasks" / f"{name}.jsonl")}
    cases = grader.load_jsonl(ROOT / "tests" / "fixtures" / f"{name}_cases.jsonl")
    bad = 0
    refs_ok = 0
    for tid, t in tasks.items():
        ok, reason, detail, _ = grader.grade_one(t, t["reference"])
        refs_ok += ok
        if not ok:
            bad += 1
            print(f"REF FAIL      {tid}  {reason} {detail}")
    killed = survived = var_ok = var_bad = 0
    for c in cases:
        ok, reason, detail, _ = grader.grade_one(tasks[c["id"]], c["code"])
        if c["kind"] == "mutant":
            if ok:
                survived += 1
                bad += 1
                print(f"MUTANT LIVED  {c['id']}  {c['note']}")
            else:
                killed += 1
                print(f"killed        {c['id']}  {reason:<24} {c['note']}")
        else:
            if ok:
                var_ok += 1
                print(f"variant ok    {c['id']}  {c['note']}")
            else:
                var_bad += 1
                bad += 1
                print(f"VARIANT FAIL  {c['id']}  {reason} {detail}  {c['note']}")
    print(f"\nreferences pass: {refs_ok}/{len(tasks)}")
    print(f"mutants killed:  {killed}/{killed + survived}")
    print(f"variants pass:   {var_ok}/{var_ok + var_bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
