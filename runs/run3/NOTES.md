# Run 3 (v2 set, condition A, Claude Haiku via Claude Code subagents)

- Date: 2026-10-05. Preregistered in Amendment 7 (369fcb4); approved by Vishal.
- 3 subagents (model: haiku), 10 tasks each (`batchN_tasks.jsonl`: id, n_qubits, prompt only). Prompt = `runs/instructions.md` plus the task lines plus an output section naming the answers file and allowing exactly one Write call.
- Tool calls per subagent, from the session transcripts: batch1 Write x1 + SubagentHandback x1; batch2 same; batch3 same. Valid condition A.
- Answers frozen in this commit, before any grading. Grader commit for grading: recorded in RESULTS.md.
