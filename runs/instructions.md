# Instructions given to every agent (condition A)

You are given quantum circuit tasks. For each task, write a circuit that does exactly what the task asks.

Rules:
- Qubits q[0] .. q[n-1] are the task's qubits, where n is the task's `n_qubits`. Qiskit's bit-string convention applies: in a label like |01>, the rightmost character is q[0].
- You may add up to 3 extra (ancilla) qubits after q[n-1]. They start in |0>, must end in |0> for every input, and must not be measured.
- Don't add measurements unless the task asks for them.
- Answer in OpenQASM 2.0 (with `include "qelib1.inc";`), OpenQASM 3, or Qiskit Python that leaves the finished circuit in a variable named `qc`.
- You can't run any code or tools to check your work. Answer from your own reasoning.

For each task, give:
- `code`: the circuit.
- `claim`: one or two sentences saying what your circuit does.
- `claimed_success`: true if you believe the circuit exactly meets the task, false if you're unsure or know it doesn't.
