"""Condition C feedback: grade an agent's drafts and print only the verdict for each.

    python scripts/verdict_feedback.py tasks/v2.jsonl draft_answers.jsonl > feedback.txt

This is what an agent gets from a unit test or a CI check: PASS, or FAIL with the
grader's reason (and fidelity, for state tasks). It never prints the reference
circuit, the target matrix or the target state.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import grader  # noqa: E402


def verdict(task: dict, code: str) -> str:
    passed, reason, detail, _ = grader.grade_one(task, code)
    if passed:
        return "PASS"
    return f"FAIL: {reason}" + (f" ({detail})" if detail else "")


def main(tasks_path: str, answers_path: str) -> None:
    tasks = {t["id"]: t for t in grader.load_jsonl(tasks_path)}
    for a in grader.load_jsonl(answers_path):
        print(f"{a['id']}: {verdict(tasks[a['id']], a.get('code', ''))}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
