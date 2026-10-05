"""Condition B feedback: simulate an agent's draft circuits and print what they do.

    python scripts/exec_feedback.py tasks/v2.jsonl draft_answers.jsonl > feedback.txt

For each draft it prints what running the circuit in Qiskit would show: the gates
used, any measurements, and the circuit's action (the output state from |0...0>
for state tasks, or the output for every basis input for unitary tasks). It never
prints the reference, a pass/fail verdict, or anything about the task beyond the
qubit count. That is the point: the agent sees what its own circuit does, the way
it would after running it, and judges for itself whether that is what was asked.

Python drafts are loaded the same way the grader loads submissions (allowed
subset, macOS sandbox), so feedback can't be used to run arbitrary code.
"""
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import grader  # noqa: E402
from qiskit.circuit import Barrier, Delay, Measure  # noqa: E402
from qiskit.quantum_info import Operator, Statevector  # noqa: E402

TOL = 1e-6


def _amp(z: complex) -> str:
    re, im = round(z.real, 4) + 0.0, round(z.imag, 4) + 0.0
    if abs(im) < 1e-4:
        return f"{re:+.4f}"
    if abs(re) < 1e-4:
        return f"{im:+.4f}i"
    return f"({re:+.4f}{im:+.4f}i)"


def _ket(i: int, n: int) -> str:
    return "|" + format(i, f"0{n}b") + ">"


def _state_lines(vec: np.ndarray, n: int) -> list[str]:
    return [f"    {_ket(i, n)}  {_amp(a)}" for i, a in enumerate(vec) if abs(a) > TOL]


def describe(task: dict, code: str) -> list[str]:
    try:
        qc = grader.load_circuit(code)
    except grader.GradeError as e:
        return [f"  could not load the circuit: {e.reason}: {e.detail}"]
    lines = [f"  qubits: {qc.num_qubits} (task has {task['n_qubits']}), classical bits: {qc.num_clbits}"]
    ops = Counter(inst.operation.name for inst in qc.data)
    lines.append("  gates: " + (", ".join(f"{k} x{v}" for k, v in sorted(ops.items())) or "none"))
    try:
        qc = grader._task_register_first(qc)
        unitary_part, measured = grader._final_measure_split(qc)
    except grader.GradeError as e:
        return lines + [f"  can't simulate as a pure circuit: {e.reason}: {e.detail}"]
    if measured:
        lines.append(f"  measured at the end: q{sorted(measured)} (shown below before measurement)")
    if any(not isinstance(i.operation, (Barrier, Delay, Measure)) and not hasattr(i.operation, "to_matrix")
           and i.operation.definition is None for i in unitary_part.data):
        return lines + ["  can't simulate: contains an operation with no matrix"]
    n = unitary_part.num_qubits
    try:
        if task["mode"] == "statevector":
            out = Statevector.from_label("0" * n).evolve(unitary_part).data
            lines.append("  output state from |" + "0" * n + "> (rightmost bit is q[0]):")
            lines += _state_lines(out, n)
        else:
            u = Operator(unitary_part).data
            lines.append("  output for each basis input (rightmost bit is q[0]):")
            for col in range(2 ** n):
                outs = ", ".join(f"{_amp(u[r, col])}{_ket(r, n)}" for r in range(2 ** n) if abs(u[r, col]) > TOL)
                lines.append(f"    {_ket(col, n)} -> {outs}")
    except Exception as e:  # noqa: BLE001 - e.g. an opaque gate
        lines.append(f"  simulation failed: {type(e).__name__}: {e}")
    return lines


def main(tasks_path: str, answers_path: str) -> None:
    tasks = {t["id"]: t for t in grader.load_jsonl(tasks_path)}
    for a in grader.load_jsonl(answers_path):
        print(f"== {a['id']} ==")
        print("\n".join(describe(tasks[a["id"]], a.get("code", ""))))
        print()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
