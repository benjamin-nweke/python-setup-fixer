# First real-project test

## Project and method

Tested a source-only copy of the user's Desktop Prompt Regression Tester v2, associated with https://github.com/benjamin-nweke/Prompt-Regression-Tester. The local repository HEAD was 0cb8151c3dad0000fc3564015f67102575c286c2. This was a local working-copy test, not a fresh checkout of the current GitHub branch.

Copied eight code, test, sample-data and documentation files into work/prompt-regression-test. No credentials or existing environment were copied. SHA-256 checks confirmed both the original and copied files remained unchanged. All new dependencies went into work/prt-test-env with Python 3.12.14.

## Results

| Check | Before installation | After installation |
| --- | --- | --- |
| Declared dependencies | Streamlit and Anthropic missing | Both present |
| Application imports | Failed: no streamlit | Passed |
| Existing unit tests | 10 passed using fake model responses | Not rerun; no source changes |
| Streamlit app screen | Not tested | Loaded with six default cases, no exceptions |
| Evaluation without API key | Not tested | Blocked with expected message |

Installed Streamlit 1.65.0 and Anthropic 1.11.0 from the project's requirements.txt. The before-and-after report marks both dependency findings as explicitly resolved.

## What this taught us

1. Unit tests can pass while the app cannot start. These tests use fake model responses and do not exercise the missing UI or API SDK dependencies. Dependency checks and application startup checks need separate evidence.
2. The application can display its interface without an API key but cannot perform a paid evaluation. Readiness is feature-specific.
3. Setup Fixer detects the API-key lookup, but currently labels it as a non-blocking note because the project uses os.environ.get and enforces the requirement later. It does not follow control flow. This is a limitation, not evidence that credentials are optional for evaluation.
4. The project does not declare a Python version constraint. Setup Fixer reports this as unknown rather than guessing compatibility.

## Limits and evidence

This is one real project with a deliberately fresh environment. It is not a pre-existing failure in the user's Desktop environment and is not a general accuracy benchmark. No source changes were made to repair this setup. No Claude diagnosis or paid evaluation was run. The smoke test blocked outgoing connections and recorded zero attempts.

Reports:
- reports/prt-before.json and reports/prt-before.html
- reports/prt-after.json and reports/prt-after.html
- reports/prt-smoke.json

The existing 10 unit tests passed. App startup was additionally tested through Streamlit AppTest, not a browser screenshot or a live hosted server.
