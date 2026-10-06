"""Local-only graphical interface for Python Setup Fixer."""
import copy
import html
import hashlib
import inspect
import json
import os
from pathlib import Path
import re
import shlex
import sys

import streamlit as st

import fixer
import project_upload
import credentials

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title='Python Setup Fixer', page_icon='🛠', layout='wide')
if st.session_state.pop('clear_ai_key', False):
    st.session_state.pop('anthropic_key', None)
st.markdown('<style>' + (ROOT/'assets/interface.css').read_text() + '</style>', unsafe_allow_html=True)


def reset_results():
    for key in ('report', 'baseline', 'diagnosis', 'diagnosis_report', 'context', 'env_values', 'last_error', 'ai_error', 'verify_command', 'verify_trusted'):
        st.session_state.pop(key, None)


def select_upload():
    reset_results()
    st.session_state.project_source = 'Upload a project ZIP'


def invalidate_current():
    for key in ('report', 'last_error', 'verify_command', 'verify_trusted'):
        st.session_state.pop(key, None)


def resolve_python(root, explicit):
    if explicit.strip():
        return str(Path(explicit).expanduser())
    candidate = root/'.venv'/('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    return str(candidate) if candidate.is_file() else sys.executable


def accept_report(report):
    previous = st.session_state.get('baseline')
    if previous and previous.get('project_id') == report['project_id']:
        report['comparison'] = fixer.compare_reports(previous, report)
    else:
        st.session_state.baseline = copy.deepcopy(report)
    report['readiness'] = fixer.readiness(report)
    verification = report.get('verification')
    if verification and verification['result'] != 'command succeeded' and not (previous or {}).get('verification'):
        baseline = copy.deepcopy(report)
        baseline.pop('comparison', None)
        st.session_state.baseline = baseline
    st.session_state.report = report
    st.session_state.pop('last_error', None)


def run_checks(root, python, command=None, timeout=20):
    overrides = st.session_state.get('env_values', {})
    report = fixer.check(root, python, env_overrides=overrides)
    if command is not None:
        report['verification'] = fixer.verify(root, command, timeout, env_overrides=overrides)
    accept_report(report)


def show_error(exc):
    st.session_state.last_error = fixer.scrub(str(exc))


st.markdown('<div class="brandbar"><span class="wordmark"><span class="brandmark">/✓</span>Python Setup Fixer <span class="version">0.3</span></span><span class="local-badge">LOCAL WORKSPACE</span></div>', unsafe_allow_html=True)
if st.session_state.get('report'):
    st.markdown('<div class="hero compact"><div><div class="eyebrow">YOUR PROJECT / UNDER INSPECTION</div><h1>Find the fault. <em>See the fix.</em></h1><p>Evidence first. A clear next step. A result you can verify.</p></div><div class="hero-tags"><span>01 Inspect</span><span>02 Explain</span><span>03 Verify</span></div></div>', unsafe_allow_html=True)
else:
    st.markdown('''<div class="hero"><div><div class="eyebrow">FROM SETUP ERROR TO FIRST RUN</div><h1>Less guesswork.<br><em>More running code.</em></h1><p>Find what's stopping your Python project, understand the repair, and verify what changed.</p><div class="hero-tags"><span>Python environments</span><span>Dependencies</span><span>Configuration</span></div></div><div class="diagram" aria-label="Workflow illustration, not a live project result"><div class="diagram-title"><span>THE REPAIR WORKFLOW</span><span>01 / 02 / 03</span></div><div class="diagram-box"><span>project.zip</span><b>Inspect setup</b></div><div class="diagram-arrow">↓ &nbsp; Evidence + optional Claude explanation</div><div class="diagram-box"><span>A targeted change</span><b>You stay in control</b></div><div class="diagram-arrow">↓ &nbsp; Run the same command again</div><div class="diagram-box final"><span>Before → After</span><b>Verify the result</b></div><small>Workflow illustration. Your actual results appear after inspection.</small></div></div>''', unsafe_allow_html=True)
with st.container(key='project_panel'):
    st.markdown('<div class="panel-heading"><span>01</span>Choose your starting point<small class="console-label">PROJECT CONSOLE</small></div>', unsafe_allow_html=True)
    st.button('Upload project ZIP', on_click=select_upload, help='Inspect a local ZIP without installing or running it.')
    project_col, environment_col, action_col = st.columns([2.1, 2, 1.1], gap='large')
    with project_col:
        choice = st.selectbox('Project source', ['Configuration demo', 'Expense demo', 'Dependency demo', 'Python version demo', 'Upload a project ZIP', 'My local project'], key='project_source', on_change=reset_results)
        examples = {'Configuration demo': 'missing-config', 'Expense demo': 'expense-demo', 'Dependency demo': 'missing-package', 'Python version demo': 'wrong-python'}
        if choice in examples:
            project_text = str(ROOT/'examples'/examples[choice])
            st.caption('examples/' + examples[choice])
        elif choice == 'Upload a project ZIP':
            project_text = ''
            upload_options = {'max_upload_size': 20} if 'max_upload_size' in inspect.signature(st.file_uploader).parameters else {}
            upload = st.file_uploader('Project ZIP', type=['zip'], **upload_options, key='project_zip_' + str(st.session_state.get('upload_generation', 0)))
            st.caption('Up to 20 MB. Imported locally, without running code or installing packages. .git, virtual environments, caches, and .env secrets are excluded; .env.example is kept.')
            demo_zip = ROOT/'examples/expense-demo.zip'
            if demo_zip.is_file():
                st.download_button('Download Expense demo ZIP', demo_zip.read_bytes(), file_name='expense-demo.zip', mime='application/zip')
            digest = hashlib.sha256(upload.getbuffer()).hexdigest() if upload else None
            if digest != st.session_state.get('upload_digest'):
                previous_upload = st.session_state.pop('uploaded_project', None)
                if previous_upload:
                    previous_upload.cleanup()
                reset_results()
                st.session_state.upload_digest = digest
                st.session_state.pop('upload_error', None)
                st.session_state.pop('uploaded_folder', None)
                if upload:
                    try:
                        st.session_state.uploaded_project = project_upload.extract_project(upload.getvalue())
                    except ValueError as exc:
                        st.session_state.upload_error = str(exc)
            if st.session_state.get('upload_error'):
                st.error(st.session_state.upload_error)
            imported = st.session_state.get('uploaded_project')
            if imported:
                selected = st.selectbox('Folder to inspect', imported.candidates, key='uploaded_folder', on_change=reset_results)
                project_text = str(Path(imported.workspace.name)/selected)
                st.caption(f'Temporary copy ready. {imported.skipped} excluded entries. Dependencies are checked against the Python environment selected here, not an environment inside the ZIP.')
                if st.button('Remove uploaded project'):
                    imported.cleanup()
                    st.session_state.pop('uploaded_project', None)
                    st.session_state.pop('upload_digest', None)
                    st.session_state.pop('uploaded_folder', None)
                    st.session_state.upload_generation = st.session_state.get('upload_generation', 0) + 1
                    reset_results()
                    st.rerun()
        else:
            project_text = st.text_input('Local project folder', placeholder='/Users/you/projects/my-project', on_change=reset_results)
    with environment_col:
        with st.expander('Python environment', expanded=False):
            interpreter = st.text_input('Python executable (optional)', placeholder='Use project .venv or app Python', key='python_path', on_change=invalidate_current)
            st.caption('Select the Python environment that should run this project.')
        st.caption('Uses the project .venv when available.')
    root = Path(project_text).expanduser().resolve() if project_text.strip() else None
    python = resolve_python(root, interpreter) if root else sys.executable
    with action_col:
        if st.button('Check project', type='primary', use_container_width=True, disabled=root is None):
            try:
                with st.spinner('Inspecting the project and environment...'):
                    run_checks(root, python)
                st.rerun()
            except (ValueError, OSError, TypeError) as exc:
                show_error(exc)
        st.caption('No code execution. No API call.')
        if choice in examples:
            st.button('Reset demo', on_click=reset_results, help='Clear this session’s settings, findings, explanation and comparison. The saved backend API key is kept.')
    if choice == 'Expense demo':
        st.caption('EXPENSE DEMO / Created for testing with fictional data. Runs offline with the standard library.')

if st.session_state.get('last_error'):
    st.error(st.session_state.last_error)
report = st.session_state.get('report')
if not report:
    st.markdown((ROOT/'assets/workflow.html').read_text(), unsafe_allow_html=True)
    st.stop()

st.markdown(f'<div class="inspection-meta">INSPECTION / {html.escape(report["project"])} &nbsp; · &nbsp; Python {html.escape(report["python"])} &nbsp; · &nbsp; {html.escape(report["created_at"][11:19])} UTC</div>', unsafe_allow_html=True)
summary = fixer.readiness(report)
entries = []
for key, title in zip(('dependencies','verification_command','configuration'), ('Dependencies','Verification command','Configuration')):
    item = summary[key]
    status = item['status']
    tone = 'blocked' if status in ('blocked','failed') else 'passed' if status in ('passed','declared dependencies present','observed variables set') else 'review'
    entries.append(f'<div class="status-entry {tone}"><span class="label">{title}</span><strong>{html.escape(status.capitalize())}</strong></div>')
st.markdown('<div class="status-ledger">' + ''.join(entries) + '</div>', unsafe_allow_html=True)
with st.expander('What these results mean'):
    for key in ('dependencies', 'verification_command', 'configuration'):
        st.caption(summary[key]['detail'])
    st.caption(summary['scope'])

inspect_tab, explain_tab, verify_tab = st.tabs(['1  Findings', '2  Claude explanation', '3  Verify & compare'])
with inspect_tab:
    failures = [f for f in report['findings'] if f['status'] == 'fail']
    attention = [f for f in report['findings'] if f['status'] == 'warning' or f['title'].startswith('Configuration: ') and f['status'] == 'note']
    if failures:
        st.subheader(f'{len(failures)} detected failure' + ('s' if len(failures) != 1 else ''))
    elif attention:
        st.subheader('No detected failures. Some settings need review.')
    else:
        st.subheader('No detected failures in the supported checks')
    for f in failures + attention:
        st.markdown(f'<div class="finding {f["status"]}"><span class="tag">{html.escape(f["status"])}</span><h3>{html.escape(f["title"])}</h3><p>{html.escape(f["evidence"])}</p><p class="next">{html.escape(f["action"])}</p></div>', unsafe_allow_html=True)
    remaining = [f for f in report['findings'] if f not in failures + attention]
    with st.expander(f'Other checks and limits ({len(remaining)})'):
        for f in remaining:
            st.markdown('**' + f['title'] + '**')
            st.text(f['evidence'])
            st.caption(f['action'])
    st.markdown('<div class="section-note">Keep a copy of the evidence</div>', unsafe_allow_html=True)
    export_html, export_json = st.columns(2)
    export_html.download_button('Download HTML report', fixer.html_report(report), file_name='setup-report.html', mime='text/html')
    export_json.download_button('Download JSON evidence', json.dumps(report, indent=2), file_name='setup-report.json', mime='application/json')

with explain_tab:
    st.subheader('Ask Claude to explain these findings')
    st.write('Claude receives the report below, not raw source files. Known sensitive values are redacted, but redaction may miss private details in command output. Review the report before sending.')
    request_panel, response_panel = st.columns([1, 1.15], gap='large')
    with request_panel:
        with st.expander('Exact report sent to Anthropic'):
            st.json(report)
        saved_key = credentials.backend_key()
        if saved_key:
            st.success('Backend key loaded. Ready to request an explanation.')
            st.caption('Loaded on the backend and never displayed here. Sent to Anthropic for authentication when you request an explanation.')
        with st.form('claude_request', clear_on_submit=True):
            api_key = saved_key or st.text_input('Anthropic API key', type='password', key='anthropic_key', help='Used for this request. Not saved to a file.')
            model = st.text_input('Model', value='claude-sonnet-4-5')
            consent = st.checkbox('Send this report to Anthropic using my API credits')
            explain = st.form_submit_button('Explain with Claude', type='primary')
        if explain:
            if not consent or not api_key.strip():
                st.session_state.ai_error = 'Enter a key and select the report-sharing checkbox first.'
            else:
                try:
                    with st.spinner('Claude is reviewing the report...'):
                        answer = fixer.diagnose(report, api_key.strip(), model.strip())
                    answer = fixer.scrub(answer.replace(api_key.strip(), '[REDACTED]'), root).replace('\u2014', '; ')
                    st.session_state.diagnosis = answer
                    st.session_state.diagnosis_report = copy.deepcopy(report)
                    st.session_state.pop('ai_error', None)
                except (ValueError, OSError) as exc:
                    st.session_state.ai_error = fixer.scrub(str(exc))
            st.session_state.clear_ai_key = True
            st.rerun()
    with response_panel:
        if not st.session_state.get('diagnosis'):
            st.markdown('<div class="workflow-card"><span class="step-num">CLAUDE / OPTIONAL</span><strong>Turn findings into a clear next step.</strong><p>Your explanation will appear here. Review the report and choose whether to send it using your Anthropic API credits.</p><p>No commands are executed from an explanation. Manually entered keys are cleared after submission.</p></div>', unsafe_allow_html=True)
        if st.session_state.get('ai_error'):
            st.warning(st.session_state.ai_error)
        if st.session_state.get('diagnosis'):
            if st.session_state.get('diagnosis_report') != report:
                st.info('Earlier explanation: the project has been checked again since this response. It describes the earlier report, not the current result.')
            if st.session_state.get('diagnosis_report'):
                with st.expander('Report used for this explanation'):
                    st.json(st.session_state.diagnosis_report)
            st.warning('Suggested next steps, not verified repairs. No commands have been executed from this explanation.')
            st.markdown(st.session_state.diagnosis)

with verify_tab:
    st.subheader('Run a check you can compare')
    st.write('Use a short command that exits, such as an import check, a test, or a small script. A web server that keeps running may time out.')
    st.caption('The first failed verification becomes your baseline automatically if the baseline has no command result. You can also save a baseline manually.')
    with st.expander('Help me choose a command'):
        st.write('Use the command that reproduces your problem, then run that same command after making a change. Commands run from the selected project folder.')
        st.caption('For a project with app.py:')
        st.code(shlex.join([python, 'app.py']), language='bash')
        st.caption('For a project with standard-library unittest tests:')
        st.code(shlex.join([python, '-m', 'unittest', 'discover']), language='bash')
        st.write('Check the project README for its actual entry point. Replace app.py if needed. A passing test only verifies what that test covers. Avoid long-running web-server commands for this comparison.')
    controls, execution = st.columns([1.05, 1], gap='large')
    with controls:
        with st.expander('Configuration for this session'):
            st.caption('These values are passed only to this session’s checks and commands. They are not written to .env files or shared with other sessions.')
            if choice == 'Configuration demo':
                if st.button('Set demo endpoint to local'):
                    st.session_state.setdefault('env_values', {})['FIXER_DEMO_ENDPOINT'] = 'local'
                    st.success('Demo setting added. Run verification to check the repair.')
            if choice == 'Expense demo':
                if st.button('Use included expense data'):
                    st.session_state.setdefault('env_values', {})['EXPENSE_DEMO_CSV'] = 'expenses.csv'
                    st.success('Input file selected for this session. Run verification to check the expense summary.')
            with st.form('environment', clear_on_submit=True):
                env_name = st.text_input('Variable name', placeholder='MY_SETTING')
                env_value = st.text_input('Variable value', type='password')
                add_env = st.form_submit_button('Add session variable')
            if add_env:
                if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', env_name.strip()) and env_value:
                    st.session_state.setdefault('env_values', {})[env_name.strip()] = env_value
                    st.success('Session variable added. Rerun verification to refresh the report.')
                else:
                    st.warning('Enter a valid variable name and a nonempty value.')
            if st.session_state.get('env_values'):
                st.caption('Session variables: ' + ', '.join(st.session_state.env_values))
                if st.button('Clear session variables'):
                    st.session_state.env_values = {}
                    st.info('Session variables cleared. Rerun verification to refresh the report.')
        with st.form('verification'):
            command = st.text_input('Command to run', value=shlex.join([python, 'app.py']) if (root/'app.py').is_file() else '', key='verify_command', placeholder='Enter the project’s verification command')
            st.caption('Runs in the selected project folder with your local permissions. Shell operators and activation commands are not supported. Use the full Python path shown above.')
            timeout = st.slider('Time limit (seconds)', 5, 120, 20)
            trusted = st.checkbox('I trust this project and want to execute this command', key='verify_trusted')
            execute = st.form_submit_button('Run verification', type='primary')
        if execute:
            if not trusted:
                st.warning('Confirm that you trust the project before running its code.')
            else:
                try:
                    argv = shlex.split(command)
                    if not argv:
                        raise ValueError('Enter a command to run')
                    with st.spinner('Running the command, then comparing results...'):
                        run_checks(root, python, argv, timeout)
                    st.rerun()
                except (ValueError, OSError, TypeError) as exc:
                    st.error(fixer.scrub(str(exc)))
    with execution:
        v = report.get('verification')
        if not v:
            st.markdown('<div class="workflow-card"><span class="step-num">EXECUTION RECORD</span><strong>Your evidence will appear here.</strong><p>Confirm the command on the left, then run verification to capture its output and exit code. No project command has run yet.</p></div>', unsafe_allow_html=True)
        if v:
            st.markdown('<div class="section-note">Execution record</div>', unsafe_allow_html=True)
            st.subheader('Command passed' if v['exit_code'] == 0 else 'Command did not pass')
            st.code(v['command'], language='bash')
            st.caption('Exit code: ' + str(v['exit_code']))
            st.code(v['output'] or '(No output)', language=None)
            if v['output_truncated']:
                st.caption('Showing only the last 12 KB of output.')
        if st.button('Use this result as the baseline'):
            baseline = copy.deepcopy(report)
            baseline.pop('comparison', None)
            st.session_state.baseline = baseline
            st.session_state.report.pop('comparison', None)
            st.success('Baseline saved for this browser session. Run verification again after a change.')
        comparison = report.get('comparison')
        if comparison:
            st.subheader('Changes from the baseline')
            if comparison['changes']:
                rows = ['<div class="comparison-row header"><span>Finding</span><span>Before</span><span>After</span></div>']
                for change in comparison['changes']:
                    label = html.escape(change['after']) + (' / Resolved' if change['resolved'] else ' / Unresolved')
                    tone = 'resolved' if change['resolved'] else ''
                    rows.append(f'<div class="comparison-row"><span>{html.escape(change["finding"])}</span><span>{html.escape(change["before"])}</span><span class="{tone}">{label}</span></div>')
                st.markdown(''.join(rows), unsafe_allow_html=True)
            else:
                st.info('No finding statuses changed from the baseline.')
            if 'verification' in comparison:
                st.markdown('<div class="command-change ' + ('failed' if comparison['verification']['after'] != 'command succeeded' else '') + '">Command result: <strong>' + html.escape(comparison['verification']['before']) + ' → ' + html.escape(comparison['verification']['after']) + '</strong></div>', unsafe_allow_html=True)
            st.caption('A missing finding is not counted as resolved. Only an explicit pass is.')
