# Run 4 (v2 set, condition B, Claude Haiku via Claude Code subagents)

- Date: 2026-10-05. Preregistered in Amendment 7 (369fcb4); approved by Vishal. Fresh agents, not the run 3 agents.
- 3 subagents (model: haiku), 10 tasks each (`batchN_tasks.jsonl`). Round 1 prompt = `runs/instructions_B.md` plus file paths plus task lines, one Write allowed (the draft).
- Drafts hashed (`drafts.sha256`) and committed with grader fix 15 (7c3b313, Amendment 8) before any feedback was generated. Hashes re-checked after the run: unchanged.
- Feedback: `scripts/exec_feedback.py` at 7c3b313 on each draft (`batchN_feedback.txt`), sent to the same agent in a round 2 message that allowed one Write (the final answers).
- Tool calls per subagent, from the session transcripts: each Write x2 + SubagentHandback x2. Valid condition B.
- Final answers frozen in this commit, before any grading of drafts or finals.
