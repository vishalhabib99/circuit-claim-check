# Instructions given to every agent (condition B: one round of simulator feedback)

You are given quantum circuit tasks. For each task, write a circuit that does exactly what the task asks.

Rules:
- Qubits q[0] .. q[n-1] are the task's qubits, where n is the task's `n_qubits`. Qiskit's bit-string convention applies: in a label like |01>, the rightmost character is q[0].
- You may add up to 3 extra (ancilla) qubits after q[n-1]. They start in |0>, must end in |0> for every input, and must not be measured.
- Don't add measurements unless the task asks for them.
- Answer in OpenQASM 2.0 (with `include "qelib1.inc";`), OpenQASM 3, or Qiskit Python that leaves the finished circuit in a variable named `qc`.
- You can't run any code or tools yourself. Instead, there are two rounds:
  1. **Draft.** Write your draft answers to the draft file you're given, then stop and say you're done.
  2. **Feedback, then final.** You'll get back what each of your draft circuits does when simulated in Qiskit: the gates it uses, any measurements, and its output (the state it produces from |0...0> for state tasks, or the output for every basis input for unitary tasks). It won't say whether a circuit is right. Compare the output with what the task asks, fix anything that's wrong, and write your final answers to the final file you're given.

For each task, in both files, give:
- `code`: the circuit.
- `claim`: one or two sentences saying what your circuit does.
- `claimed_success`: true if you believe the circuit exactly meets the task, false if you're unsure or know it doesn't.
