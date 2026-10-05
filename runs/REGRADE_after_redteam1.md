# Re-grade after the red team 1 fixes (grader ed3cf51)

| Run | Old grader (b62e019) | Fixed grader (ed3cf51) | Verdicts changed |
|---|---|---|---|
| Run 1, Sonnet | 45/45, 0/45 false success claims | 45/45, 0/45 | none |
| Run 2, Haiku (official) | 28/45, 13/41 | 28/45, 13/41 | none |
| Run 2, Haiku (header added, post hoc) | 39/45, 2/41 | 39/45, 2/41 | none |

No answer in either run used any of the 16 holes. The only difference is the error message for the 13 Haiku answers with no version line. It now names the missing `OPENQASM` line instead of reporting a Python syntax error.

Outputs: `run1/answers_regraded_ed3cf51.txt`, `run2/answers_regraded_ed3cf51.txt`, `run2/answers_header_added_regraded_ed3cf51.txt`.
