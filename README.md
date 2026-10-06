# Python Setup Fixer

Find out why your Python project will not run, then verify the fix.

A local app with a browser interface, a command-line checker, and optional Claude diagnosis. Checks do not call an API, install packages, or execute project code. AI suggestions are never executed automatically.

## Start the browser interface

Use Python 3.11 or newer for the interface. From this project folder, run:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-gui.txt
.venv/bin/python launch.py
```

Open http://127.0.0.1:8501 in your browser. Keep the terminal running; Control+C stops the app. To restart later, run only the final command. The interface is local to this computer.

### Try the complete demo

1. Choose **Configuration demo** in the project bar and click **Check project**.
2. In **Findings**, inspect the missing `FIXER_DEMO_ENDPOINT` setting.
3. Open **Verify & compare**, confirm that you trust the included demo, and click **Run verification**. The command fails with exit code 1.
4. The first failed verification is saved as the baseline automatically. You can also use **Use this result as the baseline** to choose one manually.
5. Expand **Configuration for this session** and click **Set demo endpoint to local**.
6. Click **Run verification** again. The command succeeds with exit code 0, and the comparison shows the repaired setting and changed command result.
7. Download the HTML report from **Findings** if you want a shareable record.

No API key is needed for this demo. To explain a report with Claude, open **Claude explanation**, inspect the exact report, enter your Anthropic key in the password field, and select the report-sharing checkbox before submitting. The key field clears after submission and the key is not saved to disk. This optional request uses your Anthropic credits.

Session configuration values are held in memory and passed only to that session's checks and commands. They do not edit your project's `.env` file. Changing projects or refreshing the browser resets session state. For your own project, choose **My local project**, enter its folder, and select its Python executable when needed.

## Start the command-line checker

Run from this folder using Python 3.9 or newer with pip available. Python 3.11+ is recommended for built-in TOML support. The checker uses `packaging`, falling back to pip's bundled parser. Missing parser support is explicitly reported.

```sh
python3 fixer.py /path/to/project
```

The checker selects the project's `.venv` when present. Override the project interpreter explicitly:

```sh
python3 fixer.py /path/to/project --python /path/to/venv/bin/python
```

## Claude diagnosis and key entry

```sh
python3 fixer.py /path/to/project --ai
```

First review the exact report that will be sent to Anthropic. Confirm with `y`, then paste your API key into the hidden terminal prompt and press Return. Characters do not appear while pasting. The app does not save the key. It can also use `ANTHROPIC_API_KEY` from the process environment. Do not put keys in chat, source code, screenshots, or recordings.

AI diagnosis uses your Anthropic API credits. Local checks do not. The default model is `claude-sonnet-4-5`; select an available model with `--model MODEL_ID` or `ANTHROPIC_MODEL`.

The request contains the displayed report, including command output if you requested verification. It does not include raw source or env files. Common secrets and known local env-file values are redacted, but redaction is best effort. Review the payload before sending. Project names, dependency names, configuration names and error details can still be private.

## Verify a fix

Use `--verify` last. Everything following it is the command to run. This explicitly executes the project with your user permissions, so use it only for code you trust. It is not a sandbox. Shell operators such as pipes are not interpreted.

```sh
python3 fixer.py /path/to/project --verify /path/to/venv/bin/python app.py
```

The verification command uses exactly the executable you supply, independently of `--python`. A command is stopped after 20 seconds by default. Change this with `--timeout` before `--verify`, up to 120 seconds. A running web server may time out even when startup worked. Use a finite smoke-test command for verification. Exit zero proves only that command succeeded.

## Try the working before-and-after demo

```sh
python3 fixer.py examples/missing-config --verify python3 app.py
FIXER_DEMO_ENDPOINT=local python3 fixer.py examples/missing-config --verify python3 app.py
```

The first run reports missing configuration and a failed command. The second reports configuration present and successful startup. No API credits required.

Other fixtures deliberately demonstrate missing-package and Python-version detection:

```sh
python3 fixer.py examples/missing-package
python3 fixer.py examples/wrong-python
```

The missing-package example imports Rich, and the wrong-python example imports tomllib, which requires Python 3.11+. All three examples now have verified before-and-after runs. Rich 14.3.4 was installed into an isolated Python 3.12.14 environment for the package repair. Switching from Python 3.9.6 to 3.12.14 repaired the tomllib example. No global packages or source files were changed to make these two examples pass. See VALIDATION.md and the saved reports.

## Current scope

- Python constraints from standard `pyproject.toml` metadata or a numeric `.python-version`.
- Static base dependencies from `requirements.txt` and `[project].dependencies`, including version constraints and environment markers.
- Configuration names from `.env.example` and recognized `os.environ`, `os.getenv`, and imported aliases in source. Direct lookups receive stronger findings than optional lookups. A local `.env` file or a detected `load_dotenv` call is not proof that loading happens before access. Static analysis does not follow control flow, account for reassigned aliases, or support settings frameworks.
- Syntax inspection of up to 100 Python files, using the checker's Python grammar.
- Optional explicit command execution with exit status, timeout, and the last 12 KB of output.
- Optional Claude explanation of the report, with upload review and hidden key entry.

Not yet supported: Poetry metadata, dynamic dependencies, recursive requirements files, extras resolution, transitive conflict analysis, automatic installation, README interpretation, full startup inference, or automatic fixes. Passing the checks does not guarantee the application works. When checker and project Python minor versions differ, syntax failures are warnings rather than confirmed blockers.

Exit codes: 0 for no detected blockers, 1 for detected blockers or failed verification, 2 for checker errors. Warnings and uninspected areas are shown but do not cause exit 1.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

Tests cover diagnosis, environment markers, config changes, no accidental project execution, symlink boundaries, redaction, command exit codes, timeouts, and the mocked Anthropic request. A live Claude diagnosis was successfully tested with user-entered credentials. The guidance was subsequently tightened to avoid assuming .env loading and exposing values. Those prompt changes have offline coverage only, not another live test.

API reference: https://platform.claude.com/docs/en/api/messages/create

## Save a before-and-after report

Run from this folder. Output paths must be new; existing files are never overwritten.

```sh
python3 fixer.py examples/missing-config --save-report before.json --verify python3 app.py
FIXER_DEMO_ENDPOINT=local python3 fixer.py examples/missing-config --compare before.json --save-report after.json --html after.html --verify python3 app.py
```

The HTML report opens in any browser and requires no server or API key. It includes findings, evidence, next steps, command output and status changes. A finding counts as resolved only when it changes to an explicit pass; disappearing findings are marked not checked. Baselines are tied to the same project directory, including across interpreter changes.

Reports are created with owner-only permissions. Redaction is best effort; review reports before sharing. Saved sample reports are in `reports/`.

The current version has 40 passing automated tests when the GUI dependencies are installed, including the complete interface repair flow, consent checks, key-field clearing, and session isolation. The local suite does not require API credits.

## Real-project validation

A clean source copy of Prompt Regression Tester was tested in an isolated Python 3.12 environment. Both declared dependencies were detected as missing, then confirmed present after installation. Application imports and Streamlit AppTest startup passed. Its ten existing unit tests passed even before dependency installation. No API calls were made. See [REAL_PROJECT_TEST.md](REAL_PROJECT_TEST.md) for evidence and limitations.

## Separate readiness results

Reports now show three independent results in the terminal, JSON and HTML:

- Dependencies: declared distributions present, blocked, or not fully checked. This is not proof that imports or native libraries work.
- Verification command: not run, passed, failed, or timed out. The result applies only to the exact command supplied. An import test does not establish full startup or API-feature readiness.
- Configuration: needs review, observed variables set, or unknown. Unset values found in non-raising lookups stay unresolved. The checker does not infer that os.getenv or os.environ.get means a setting is optional.

There is no overall application-ready flag. Exit 0 means no detected failure and no failed verification command, not that all features work. Configuration uncertainty remains visible even when the command passes. Defaults and feature-specific requirements still require review.

The refreshed real-project report is `reports/prt-readiness.html`. It shows dependencies present, import verification passed, and configuration needing review. Claude receives the same separate readiness fields when an AI diagnosis is requested. The revised AI guidance has not been live retested.

## Replay the real-project report through Claude

```sh
python3 live_retest.py
```

This previews the saved `reports/prt-readiness.json`, asks permission to send it, then accepts your Anthropic key at a hidden prompt. It uses one API request. The key is not saved. An existing process-level `ANTHROPIC_API_KEY` can also be used.

The response, input report, timing, requested model, hashes and review checklist are saved in a new owner-only `reports/claude-retest-*` folder. Results are marked pending human review, not automatically graded as correct. No proposed commands are run. Failed requests do not produce a success record. This is a replay of the saved report; run fixer.py again first if fresh project evidence is needed.

Each new live retest needs a key. Automated tests mock the network and use no API credits.

## Latest live retest

The real-project report was successfully replayed through Claude. Review found accurate scope explanations but unsupported model overrides and environment-dependent commands. The response is preserved under `reports/claude-retest-20261003T145019Z-c23fff`; see its `REVIEW.md`. Further prompt corrections have offline coverage only. No model-recommended repair was automatically executed.

## Expense demo for the walkthrough

Select **Expense demo** in the project source menu. This sample was created for testing, with fictional CSV data and standard-library code. No external repository or dataset was copied. It runs offline without package installation or API credits.

Check the project and run verification. The first failed command is saved as the baseline automatically if the current baseline has no command result. Under **Configuration for this session**, click **Use included expense data**, then run verification again. The missing `EXPENSE_DEMO_CSV` setting is supplied for the session, and the program prints six records totaling 50.00 in sample units. The input CSV remains unchanged.

See [the demo instructions](examples/expense-demo/README.md). Saved before-and-after evidence is in `reports/expense-before.html` and `reports/expense-after.html`. This is a controlled demonstration, not independent evidence of general repair accuracy.

## Keeping the explanation and comparison

Claude responses stay visible after subsequent checks of the same project. An earlier response is labeled as describing an earlier report, with that original report available for inspection. Switching projects clears the explanation. Previously cleared responses cannot be recovered.

The first failed verification automatically replaces a baseline that has no command result. Later successful runs retain that failed baseline, so the comparison shows the actual failure followed by success. This does not invent a failed result if the command was never run.

## Interface design

Build 0.3 uses a navy header, blue actions, light workspace panels, and dark command output. Project selection and the Python environment are in the top project bar. Inspection results sit in a compact status summary, followed by findings, Claude explanation, and verification tabs. Before-and-after findings use readable rows with explicit resolved or unresolved labels. No external fonts or image assets are required.

## Upload a project ZIP

Select **Upload a project ZIP** in the project bar and choose a ZIP file. The app creates a private temporary copy on this computer without executing code or installing packages. Choose **Folder to inspect** when there are several candidate Python folders, then click **Check project**.

Limits: 20 MB archive, 60 MB extracted content, 5 MB per file, and 2,000 archive entries. Unsafe paths, links, special files, duplicate paths, and encrypted ZIPs are rejected. `.git`, `.venv`, `venv`, `env`, `node_modules`, caches, and `.env*` files are excluded, except `.env.example`. These exclusions are not a general secret scanner; remove other confidential files before uploading.

Dependencies are checked against the selected local Python environment. The ZIP does not provide an installed environment. Verification still requires explicit confirmation and runs with local user permissions. This is not a sandbox.

**Remove uploaded project** deletes the temporary copy and clears its results. Replacing or clearing the upload also cleans up the old copy. Temporary storage is released when the session object is discarded; use the remove button for immediate cleanup. The original ZIP is never modified.

### Try the upload demo

Download **Expense demo ZIP** from the upload controls (also available at `examples/expense-demo.zip`), then upload it. Check the project and run the default verification command to capture the failure. Under **Configuration for this session**, enter `EXPENSE_DEMO_CSV` as the variable name and `expenses.csv` as its value, then click **Add session variable**. Run verification again to see the six-record summary and total of 50.00. No API call is required.

## Consistent local startup

Use `launch.py` to start the app from this project folder. It sets the local address, port 8501, light theme, 20 MB upload limit, and automatic reload on source changes. The header shows build 0.3 so you can recognize the version. If port 8501 is already in use, stop the earlier app before launching another copy. Each browser tab has its own temporary results and configuration.

Build 0.3 separates verification controls from command evidence on desktop and places Claude requests beside the explanation panel. The welcome header becomes compact after inspection. Long command output wraps, and unsuccessful command comparisons use a distinct warning treatment. Detailed readiness explanations remain available under **What these results mean**.

## Backend Anthropic key

Place your key after `ANTHROPIC_API_KEY=` in the `.env` file beside `gui.py`. This private file is excluded by `.gitignore`. The app reads it only from its own directory, never from an uploaded or selected project. A process-level `ANTHROPIC_API_KEY` takes precedence. The interface shows when the backend key is loaded, but a successful API request is required to establish that it is valid. The key is not included in reports or stored in browser session state.

Explanation still requires the report-sharing checkbox and **Explain with Claude**. If no backend key exists, the temporary password field remains available. Keep `.env` out of manually shared archives as well as Git. No API key has been prefilled by the assistant.
