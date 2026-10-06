# Python Setup Fixer walkthrough

Target rehearsal length: about 3 minutes. This is a suggested presentation length, not a verified ShipAI requirement.

## Before recording

Open the running app in your browser. Select Expense demo and click Reset demo. Keep the backend .env file and terminal credentials off screen. The demo uses original code and fictional data. Local checks are free; requesting a Claude explanation uses Anthropic credits.

## 1. Introduce the problem

Say: “A Python project can look ready but still fail because a setting, dependency or Python version is missing. Python Setup Fixer finds evidence, explains the next step and lets you verify the result.”

Briefly point out Upload project ZIP. For this recording, use the built-in Expense demo so the result is reproducible.

## 2. Inspect the demo

Select Expense demo and click Check project. Show the missing EXPENSE_DEMO_CSV finding.

Say: “Inspection has found a missing setting. It has not run the project or fixed anything.”

## 3. Capture the failure

Open Verify & compare. Leave the suggested app.py command unchanged. Check the trust checkbox and click Run verification. Show exit code 1 and the missing-configuration message. This becomes the failed baseline automatically.

## 4. Explain the evidence

Open Claude explanation. Briefly expand Exact report sent to Anthropic, then collapse it. The backend key should show as loaded. Check the API-credit consent box and click Explain with Claude once. Allow for response time.

Say: “Claude explains this report. It does not run the suggested commands. We still need to verify the repair.”

If the service fails, explain the displayed error honestly and continue with the local finding. Do not present a saved response as a live response.

## 5. Make and verify the change

Return to Verify & compare. Expand Configuration for this session and click Use included expense data. Run the same verification command again.

Show exit code 0, six records, and these totals: Food 20.00, Supplies 18.00, Transport 12.00, TOTAL 50.00. Show the comparison from command failed to command succeeded and the resolved configuration finding.

Say: “The setting was applied only to this session. The same command now succeeds, and the comparison shows what changed.”

## 6. Keep the result

Open Findings and download the HTML report.

Close with: “This demonstrates one verified repair. It does not certify every feature of a project. The useful outcome is a specific blocker, a targeted change and evidence of the result.”

## Rehearsal checklist

- Upload project ZIP is visible without opening the source dropdown.
- Reset demo returns the Expense demo to its missing-setting state.
- The first command fails and the same command succeeds after the session setting.
- The failed baseline survives the second run.
- The report downloads and shows the result.
- No key or private file contents appear in the recording.

Public hosting and current ShipAI submission requirements still need a separate pre-submission check. Do not expose this local command runner publicly without isolating execution and protecting the API budget.
