# Run 5 results: Sonnet in condition B

Preregistered in [Amendment 9](../../PREREGISTRATION.md) (bfa5497). Same protocol as run 4, model Sonnet. Graded once at 77923fb.

| | Haiku (run 4) draft | Haiku final | Sonnet (run 5) draft | Sonnet final |
|---|---|---|---|---|
| Passed | 18/30 | 20/30 | **30/30** | **30/30** |
| Claimed success | 21 | 28 | 30 | 30 |
| Claimed success but failed | 6 | 8 | **0** | **0** |
| Circuits changed after feedback | | 10 | | 0 |

- **H13 (feedback halves Sonnet's false claims): not testable.** Its draft had none.
- **H14 (Sonnet changes at least half of its wrong drafts): not testable.** It had no wrong drafts; it changed nothing.

**What this shows:** on v2, the model mattered far more than the self-check step. Sonnet was right on every task before any feedback. Haiku with feedback still had 10 wrong answers, 8 of them claimed as right. One round of execution feedback didn't close that gap.

**What it doesn't show:** whether feedback helps Sonnet. Sonnet made no mistakes here, so that needs harder tasks. Two models, 30 tasks, one round of feedback.
