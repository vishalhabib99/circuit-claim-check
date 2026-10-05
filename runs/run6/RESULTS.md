# Run 6 results: Haiku with pass/fail checks (condition C)

Preregistered in [Amendment 10](../../PREREGISTRATION.md) (7a11805). Graded once at 734db80. Per-task table: [`analysis.txt`](analysis.txt).

**Short answer:** a pass/fail check fixed formatting, not circuits. Passes rose from 8 to 15, and all 7 new passes were drafts whose circuit was already right but whose file was missing the `OPENQASM` version line. Of the 15 drafts that were wrong as circuits, none was fixed in the final.

| | Draft | Final (after PASS/FAIL per task) |
|---|---|---|
| Passed | 8/30 | 15/30 |
| Claimed success | 22 | 24 |
| Claimed success but failed | 14 | 9 |

## Hypotheses

- **H15 (false claims at least halved): not supported.** 14 → 9; the bar was 7.
- **H16 (main: at least half of the draft's failures pass in the final): not supported.** 7 of 22; the bar was 11. The change is real (exact McNemar p = 0.016, 7 fixed vs 0 broken), but see below for what it consists of.
- **H17 (nothing that passed gets broken): supported.** 0 breaks. A PASS verdict was left alone.

## What the 7 fixes were (post hoc breakdown, decided after seeing the drafts)

| Draft failure | Tasks | Fixed in final |
|---|---|---|
| Format only: missing version line, circuit already right | 7 | **7** |
| Format, and the circuit underneath also wrong | 10 | 0 |
| Wrong circuit (`not_equivalent`, `wrong_state`, `unsupported_op`) | 5 | 0 |

So: **0 of 15 wrong circuits fixed.** Six batch-1 finals added the version line but wrote gates as function calls (`cp(-pi/2, q[2], q[1])`), which isn't valid QASM, so they still fail to parse. One round means the agent never saw that.

Where false claims went: of the 14 draft false claims, 7 became passes (all format fixes), and the rest mostly stayed false claims. Six failed tasks were marked unsure in the final. Three tasks (v23, v25, v27) went the other way: marked unsure in the draft, failed the check, were rewritten, still wrong, and came back claimed as successes.

## Next to run 4 (output feedback, different agents)

| Haiku | Correct, draft → final | Wrong circuits fixed | False claims, draft → final |
|---|---|---|---|
| Run 4: simulator output | 18 → 20 | 3 (and 1 broken) | 6 → 8 |
| Run 6: pass/fail check | 8 → 15 | 0 (7 format-only fixes) | 14 → 9 |

Different agent instances wrote very different drafts (run 6's batch 1 and 3 left out version lines; run 4's wrote Python), so the two runs can't be compared head to head. Within each run, one round of feedback fixed few or no wrong circuits.

**Limits:** one model, one round, 30 tasks. A second round, or a check that also says what the expected output is, could do better; this doesn't test that.
