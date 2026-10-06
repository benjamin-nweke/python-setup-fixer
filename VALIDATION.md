# Repair validation

Three controlled repair demonstrations are complete. These are small fixtures we created, not an independent real-world benchmark.

| Case | Exit before | Exit after | Result |
| --- | --- | --- | --- |
| Missing configuration | 1 | 0 | Verified |
| Missing dependency | 1 | 0 | Verified |
| Incompatible Python version | 1 | 0 | Verified |

## What changed

- Configuration: set `FIXER_DEMO_ENDPOINT=local` in the demo process environment. No configuration value was inferred by AI.
- Dependency: created an isolated Python 3.12.14 virtual environment. Before installation, Rich was absent and app.py failed. Installed the declared `rich>=13,<15` requirement from PyPI, resolving to Rich 14.3.4. The same interpreter then ran app.py successfully.
- Python version: app.py uses standard-library tomllib. It failed under Python 3.9.6 and succeeded under Python 3.12.14, satisfying the declared >=3.11 requirement.

The dependency installation also brought in markdown-it-py 4.2.0, Pygments 2.21.0, and mdurl 0.1.2. Packages were installed only in the workspace's work/repair-demo-env, not into system Python.

## Evidence

Each pair contains the findings, selected Python version, verification command, captured output, exit code, and a comparison. The HTML copies are readable without running the app.

- Configuration: reports/config-before.json and reports/config-after.json
- Dependency: reports/package-before.json and reports/package-after.json
- Python version: reports/python-before.json and reports/python-after.json

All three pairs were checked for a nonzero exit before, exit zero after, no timeout after, an explicitly resolved finding, and no remaining failure findings.

## Limits

These results validate the local diagnostic and verification workflow for three controlled cases. They do not demonstrate general repair accuracy or automatic fixing. Repairs were performed explicitly, then checked by the app. No source code changes were needed for these repairs.

A separate real-project validation and live Claude report replay are documented in REAL_PROJECT_TEST.md and README.md. The latest prompt corrections have offline coverage only. Do not claim an AI accuracy rate from these fixtures.

## Browser interface validation

The configuration demo was exercised in the actual local browser interface: inspect the missing setting, run the failing command, save that result as the baseline, add the demo setting, and verify the same command again. The result changed from exit code 1 to exit code 0, with the comparison showing the change.

All 33 automated tests passed. Interface tests also cover invalid folders, explicit command confirmation, report-sharing consent, clearing the API key field, and isolated session configuration. The interface's Claude request was tested with a mock response, not a new paid API call. The existing backend has separate live API evidence.


## Expense demo

Created a standard-library CSV expense summarizer and six fictional records specifically for this project. No external project code or dataset was copied. An unset `EXPENSE_DEMO_CSV` produces exit code 1. Supplying `expenses.csv` produces exit code 0, with Food 20.00, Supplies 18.00, Transport 12.00, and total 50.00.

The Streamlit AppTest workflow verified detection, the failing command, saving a baseline, selecting the included data, the successful command, and an explicitly resolved finding. It also verified the CSV was unchanged and the setting did not leak into the process environment. Separate actual command runs produced `reports/expense-before` and `reports/expense-after` in JSON and HTML. No API calls were made.

## Rehearsal flow fixes

All 33 tests pass after adding automatic capture of the first failed verification baseline and preserving earlier Claude explanations. Regression coverage verifies a second successful run still compares against the failed baseline, that the explanation retains its original report and displays an earlier-report label, and that changing projects clears it. No additional Claude request was made.

## Interface redesign validation

All 33 automated tests passed after replacing the sidebar with a top project bar and restyling findings, forms, results, and comparison rows. Browser checks covered the main interface at a narrow viewport and at 1280 pixels, including correcting selector contrast. The Claude form controls were confirmed in the browser accessibility snapshot, but the remaining visual form inspection was interrupted by repeated browser approval timeouts. Temporary viewport sizing was reset. No live Claude call was made.

## ZIP upload validation

All 38 tests pass. New coverage includes traversal and absolute path rejection, links, case-insensitive duplicate names, invalid ZIP data, each extraction limit, excluded secret and environment files, multiple project roots, cleanup, and the actual expense command before and after configuration. Streamlit AppTest covers upload inspection and explicit removal, with its file picker input supplied by a mock. The native browser file picker has not yet been exercised. No package installation or API call occurs on upload.

## Final local build check

Build 0.2 adds a consistent `launch.py` entry point, automatic source reload on startup, a visible build label, and a corrected manual baseline action that removes the old comparison immediately. All 38 automated tests passed. The actual browser file chooser successfully uploaded `expense-demo.zip`; Check project then detected the missing `EXPENSE_DEMO_CSV` setting in the extracted copy. This supersedes the earlier note that the native file picker was untested. The latest live Claude response still needs review before recording.

## Build 0.3 visual audit

Reviewed the home, findings, Claude request, ZIP upload, and verification screens in the browser. Verified the expense command fails with exit 1 and succeeds with exit 0 after configuration; the comparison records command failed to command succeeded and the setting as resolved. Corrected clipped console output, an incorrectly green failed-command comparison, dark-theme control inheritance, and an oversized welcome header after inspection. Verified ZIP controls at a 390-pixel viewport and desktop layout at 1360 pixels. No live Claude call was made; response retention and consent remain covered by automated tests. The server was restarted using the launcher and corrected theme.

## Audit: 5 October 2026

- 41 automated tests passed on Python 3.12.14 with Streamlit 1.65. Tests cover configuration and dependency checks, command timeouts, report escaping and redaction, comparisons, upload validation and cleanup, GUI demo flows, and backend credential handling.
- Isolated GUI tests from the real backend key. No automated test makes a paid request.
- Added rejection of malformed, empty, and token-truncated Claude responses.
- Corrected UI privacy wording and removed the manual-key instruction when a backend key is available.
- One separate live Anthropic request succeeded using the saved backend key and the original Expense demo report. No credential was printed. Response saved in reports/backend-live-check.txt.
- The live response identified EXPENSE_DEMO_CSV and the expected expenses.csv setting correctly. It described static inspection as completing without import errors, which overstates the evidence. The system prompt now explicitly distinguishes static parsing from executing imports. That additional prompt sentence has not been live retested; AI advice still needs verification.
- Browser inspection confirmed the updated privacy copy and backend-key status.

This validates the tested local workflows, not every possible Python project or a public deployment. Recommended next polish: prominent upload entry, a reset-demo action, and clearer guidance for choosing the verification command. Public hosting must isolate uploaded-code execution and protect the shared API budget before being enabled.
