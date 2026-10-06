# Python Setup Fixer walkthrough and build log

This script covers what I built, the problem, the solution, a working demonstration, how I built it with AI assistance, the decisions and setbacks, and the evidence behind the result. Read the quoted speech aloud. Bracketed text contains screen actions and pauses. Allow roughly 15 to 18 minutes at a relaxed pace with the live request. This is a rehearsal estimate, not a confirmed submission limit. Use the fillers naturally.

## Before recording

Select Expense demo and click Reset demo. Use a wide browser window. Have the app, fixer.py, gui.py, project_upload.py and VALIDATION.md available in separate tabs. Keep the backend .env file closed and credentials off screen. During the AI segment, explain the diagnosis briefly and use the app controls for the repair; do not copy or execute the suggested terminal snippet. Review the explanation report before sending it. Only the Claude request uses API credits. Do not publish a repository or deployment link in the recording until that link actually exists and has been checked.

## 1 What I built and why

[Show the homepage. Pause for two seconds.]

“Hey, I'm Benjamin. Let me walk you through Python Setup Fixer, and then I'll show you how I built it and what changed along the way.

“You know when you open a Python project, try to run it, and it immediately throws an error? It might be a missing package, the wrong Python version, or a setting that hasn't been supplied. Before you can even use the project, you're trying to work out which of those things is wrong.

“So, I wanted to build something practical around that first-run problem. Something that gives you a specific finding, explains the evidence, and helps you check whether the change you made actually worked.

“The result is a local developer tool with a browser interface and a command-line checker. It checks supported Python requirements, declared dependencies and configuration. It can ask Claude to explain the report, and it lets you run a command before and after a change.

“Just to be clear about the name, it helps you find and verify a fix. It doesn't automatically rewrite your project or install packages.”

[Point to Upload project ZIP and Project source.]

“You can inspect a project from a folder on your computer, import a ZIP, or start with one of the included demos. Importing a ZIP doesn't run its code.

“For this walkthrough, I'm using Expense demo. We created it specifically for testing, with original code and six fictional expense records. It's a small CSV summarizer that runs offline using Python's standard library.

“The problem in this example is deliberate: a setting is missing. That gives us a repeatable failure, a specific change to make, and a result we can compare.”

## 2 How I put it together

[Show the project folder. Keep .env closed. Point to fixer.py, gui.py and project_upload.py, then return to the app.]

“Okay, a quick look at how this is built before I run the demo.

“I built this with Codex as a coding assistant. I used it to help write and revise the implementation, run tests and inspect the interface. My part was choosing the problem, directing the scope and design, and deciding what I wanted the tool to do. This was an iterative, AI-assisted build.

“There are two different uses of AI here. Codex helped during development. Claude is the optional explanation feature inside the finished tool.

“The core is Python. The browser interface is Streamlit, with custom CSS and HTML for the layout. The checking logic lives in fixer.py, the interface is in gui.py, and project_upload.py handles ZIP imports. A small credentials helper loads the backend Anthropic key.

“I started with the checking and command-line workflow, then added the browser interface around it. That meant the same checking logic could support both ways of using the tool.

“The checker looks at supported project files, such as requirements.txt and standard project metadata in pyproject.toml. It asks the selected Python environment which packages are installed, and compares those against the declared requirements.

“For configuration, it looks at .env.example and recognized environment-variable lookups in the Python source. It uses Python's syntax tree to inspect that source. So, it's examining the code structure without running the project during inspection.

“That has limits. It doesn't trace every possible path through the program, and a setting being listed in a file doesn't prove it gets loaded at runtime.”

[Pause. Point to the three workflow stages.]

“The sequence is: inspect the project locally, optionally send the report to Claude, then explicitly run a verification command.

“The Claude feature uses Anthropic's Messages API. The configured default is claude-sonnet-4-5. It receives the report, including verification output when present, rather than the raw source files.

“I kept AI separate from command execution. An explanation can suggest a next step, but it doesn't get to run that step automatically. I wanted the final evidence to come from a real command result.”

## 3 Inspect and reproduce the problem

[Return to the app. Select Expense demo. Click Check project and scroll to Findings.]

“All right, let's use it.

[Pause while the results appear.]

“Here, it found the missing EXPENSE_DEMO_CSV setting. That's what tells this little program where its expense data is.

“The finding shows where that setting is used and gives us a next step. So we have something specific to investigate.

“You'll also notice that dependencies, configuration and the verification command have separate statuses. ‘Not fully checked’ isn't a pass, and an inspection isn't proof that the program runs.”

[Open 3 Verify & compare. Leave the suggested command unchanged.]

“Let's run it before changing anything. The command here uses the selected Python interpreter to run app.py.

“For another project, I'd use the command that reproduces its problem. There's guidance in Help me choose a command, but the right command still depends on the project.

“I'm confirming that I trust this code because this is our own test demo.”

[Check I trust this project and want to execute this command. Click Run verification. Scroll to the execution record.]

“Right, exit code one. The program failed, and the output confirms that the setting is missing.

[Pause for two seconds.]

“The tool keeps this failed run as the baseline. That's useful because I want to compare an actual failure with the next result, rather than just say that something looks better.”

## 4 Use Claude to explain the evidence

[Open 2 Claude explanation. Expand Exact report sent to Anthropic, briefly show it, then collapse it.]

“Now, let's ask Claude to explain what we're seeing.

“This is the report that will be sent. Known sensitive values are redacted, but that isn't a guarantee that every private detail is removed. I still review the report, especially command output, before sending it.

“My key is configured on the backend, so I don't have to paste it into this screen. The key is used to authenticate with Anthropic. The local checks are free; this request uses my API credits.”

[Check Send this report to Anthropic using my API credits. Click Explain with Claude once.]

“Let's give that a moment.”

[Wait quietly. Read the returned response before describing it. Do not assume its exact wording.]

“Okay, here's the explanation. I'm checking it against the evidence we already have.

[Pause to scan the response.]

“The confirmed issue is that the demo hasn't been told where to find its data. We already have the included CSV, so we can supply the setting and run the same command again.

“The explanation is guidance, not a verified repair. In rehearsal, it suggested a hidden prompt that then printed the value, which is unsuitable for secrets. I won't use that terminal suggestion. I'll apply the setting through the app and check the result.”

## 5 Make the change and prove the result

[Return to 3 Verify & compare. Expand Configuration for this session.]

“For this demo, I added a shortcut called Use included expense data. It supplies expenses.csv as the value of the missing setting.

“In another project, I could use the variable name and value fields here. These values apply to this session's checks and commands. They aren't written into the project's .env file.”

[Click Use included expense data. Click Run verification with the same command.]

“All right, let's try that again.”

[Pause. Scroll to the execution record.]

“There we go. Exit code zero, and now we have the actual output: six expense records, with a total of fifty in sample units. Food is twenty, supplies are eighteen, and transport is twelve.

[Scroll to Changes from the baseline. Pause for two seconds.]

“The setting went from fail to pass, and the command went from failed to succeeded. That's the repair we can support with evidence.

“A passing command doesn't certify every feature in a project. But for this specific failure, we can see the problem, the change and the result.”

[Open 1 Findings and click Download HTML report.]

“I can download the report to keep the findings and command results. There's a JSON export too if I want the structured evidence.”

## 6 The build log and what changed

[Show VALIDATION.md. Scroll through the sections as you discuss them. This is a summary of recorded milestones, not a replay of the development session.]

“Now, the part behind the demo: how did this get from an idea to this version?

“The first milestone was getting the core checks and verification working. We made controlled examples for missing configuration, a missing dependency and an incompatible Python version.

“For the dependency example, the repair was installing the declared package into an isolated environment. For the Python-version example, it was choosing an interpreter that supported the program. Those changes were made explicitly, then checked. The tool didn't silently fix them in the background.

“A useful turning point came from testing a clean copy of my earlier Prompt Regression Tester project. Its ten unit tests passed even while the application couldn't import Streamlit in the fresh environment.

“So that taught us something quite concrete: passing unit tests and having a runnable application are different claims. We installed the declared dependencies in that isolated environment, then checked the imports and app startup separately. We didn't run its paid AI feature.

“That helped shape the separate readiness statuses you saw earlier. I didn't want one big green badge suggesting everything was ready when we'd only verified one part.”

[Pause. Show the current interface, then the upload controls if helpful. Do not upload private files.]

“The next milestone was making it easier to use. We added the Streamlit interface, and then revised it quite a bit. The earlier version felt too much like my other tool and had too much plain text.

“We moved the project controls into the main workspace, made the welcome header smaller after inspection, and gave findings and command output clearer visual structure. Later, we added the illustrated workflow cards, a visible upload shortcut and a Reset demo button for repeatable testing.

“ZIP upload was another addition. That needed more than a file picker. We added size limits, rejected unsafe paths and links, and excluded things like virtual environments, caches and .env files. The extracted copy is temporary and can be removed from the interface.

“Those rules reduce what gets imported, but they don't turn the app into a sandbox. Verification still runs code with the local user's permissions.”

## 7 Bugs and lessons from testing

[Return to VALIDATION.md or show the final comparison screen.]

“There were a few less obvious problems that testing caught.

“One was the baseline. After a successful run, the comparison needed to keep pointing back to the earlier failure. We added automatic capture of the first failed verification and checked that later successful runs didn't replace it.

“Another was the Claude explanation. If I reran the checks after changing a setting, an older explanation could look like advice about the new report. We kept the original report with the explanation and added a label when it's from an earlier check.

“We also fixed clipped command output, a failed comparison that had the wrong colour, and controls that picked up the wrong theme. Those were things we needed to see in the browser, not just in a unit test.

“And the AI needed review too. In a live test, Claude correctly identified the missing expense setting, but described the static inspection in a way that could imply imports had been verified.

“That was too strong. We tightened the prompt, and the next live response correctly said static inspection does not execute imports. But that response also suggested printing a value entered through a hidden prompt. That advice is unsuitable for secrets and remains a known issue. This is why I review AI advice and use the app's session controls for this repair.

“We also added checks for empty, malformed and cut-off AI responses. Those should produce a clear error rather than look like a complete explanation.

“So, yeah, a lot of the build was about making the evidence and the wording agree. A polished screen isn't enough if it implies something the tool hasn't actually checked.”

## 8 Validation limits and closing

[Show the latest validation notes, then finish on the successful demo comparison.]

“The final local test suite passed all forty-one tests. That includes checks for configuration and dependencies, command failures and timeouts, comparisons, report handling, upload validation and the main interface flows.

“The automated API tests use mocked responses, so they don't spend credits. Separately, we made a real Anthropic request and confirmed that the saved backend key works.

“I also walked through the demo myself in Chrome: the failed command, a live Claude explanation, the session setting, and the successful rerun with six records totalling fifty. Then I downloaded and opened the HTML report. That validates this workflow, not every Python project.

“There are still clear boundaries. It doesn't automatically install packages or edit source code. It doesn't support every dependency format or trace every configuration path. And this version is a local application. Public hosting would need isolated execution for uploaded code and controls around API spending.

[Pause for two seconds.]

“My biggest takeaway is that the AI explanation is only one part of the product. The more useful outcome is being able to trace a finding to a change, run the same command again, and keep the evidence.

“So that's Python Setup Fixer: what I built, how it works, and what I learned while building it.

“Thanks for watching.”

[Hold the result screen for two seconds, then stop recording.]

## Backup line if the live API request fails

Use this only if an error actually appears, then continue to section 5.

“The explanation request hasn't gone through this time. The local findings and command results are still available, so I'll continue from that evidence and verify the repair.”

Do not describe a response that did not appear or present a saved response as a new live request.

## Evidence notes for the presenter

These are preparation notes, not spoken narration. Milestones are recorded in project documentation; no exact development durations or commit-by-commit timeline are claimed.

- Core checks and three controlled repairs: VALIDATION.md and reports/config-before.json, config-after.json, package-before.json, package-after.json, python-before.json and python-after.json.
- Earlier real-project test and its limits: REAL_PROJECT_TEST.md. This used a clean local copy of the user's existing project, not an unrelated downloaded project. It is supporting development evidence, not the on-screen Expense demo.
- Runtime architecture: fixer.py, gui.py, project_upload.py, credentials.py and launch.py. UI assets are in assets. The verification runner uses an explicit subprocess command with a timeout, not an AI-controlled shell.
- Expense data: examples/expense-demo/app.py and expenses.csv. The six records are fictional. The app uses csv, decimal, os and pathlib from the standard library.
- AI review: reports/backend-live-check.txt and the audit notes in VALIDATION.md. The user rehearsal produced a new live response that correctly distinguished static parsing from import execution, but suggested printing a hidden input. The latter remains a known advice issue; the script uses the session controls instead.
- Current verification: 41 automated tests passed on 5 October 2026. The user rehearsal completed on 6 October 2026 confirmed exit 1 before configuration, exit 0 afterwards, six records totalling 50.00 and a failed-to-succeeded comparison. The user downloaded and opened the report. Its latest local-file contents were not independently inspected because browser policy blocked access.
- Final usability additions: direct upload button, Reset demo and verification-command guidance, with regression coverage for the reset and upload shortcut.
- Before submission: check the current submission form for any duration, link or supporting-material requirements. This document does not assert editorial acceptance or a verified video-length requirement.
