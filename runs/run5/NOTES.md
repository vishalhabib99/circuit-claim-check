# Run 5 (v2 set, condition B, Claude Sonnet via Claude Code subagents)

- Date: 2026-10-05. Preregistered in Amendment 9 (bfa5497); approved by Vishal. Exactly the run 4 protocol with model: sonnet.
- Drafts hashed (`drafts.sha256`) and committed (4600836) before any feedback was generated. Hashes re-checked after the run: unchanged.
- Feedback: `scripts/exec_feedback.py` at 4600836 (grader unchanged since 7c3b313) on each draft (`batchN_feedback.txt`), relayed to the same agent with one Write allowed for the final answers.
- Relay check: every non-empty line of each `batchN_feedback.txt` appears in the agent's transcript (run 4 and run 5, all 6 batches, 599/599 lines).
- Tool calls per subagent, from the session transcripts: each Write x2 + SubagentHandback x2. Valid condition B.
- Final answers frozen in this commit, before any grading.
