import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fixer


class Checks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name, text):
        (self.root/name).write_text(text)

    def report(self):
        return fixer.check(self.root, sys.executable)

    def test_missing_distribution(self):
        self.write('requirements.txt', 'setup-fixer-nonexistent-example==1.0\n')
        self.assertTrue(any(f['status'] == 'fail' and 'absent' in f['evidence'] for f in self.report()['findings']))

    def test_marker_skips_other_platform(self):
        self.write('requirements.txt', 'setup-fixer-nonexistent-example; python_version < "2"\n')
        self.assertFalse(any(f['status'] == 'fail' for f in self.report()['findings']))

    def test_version_mismatch(self):
        self.write('.python-version', '99.0\n')
        self.assertTrue(any(f['status'] == 'fail' and f['title'] == 'Python version' for f in self.report()['findings']))

    def test_nested_requirements_not_silently_passed(self):
        self.write('requirements.txt', '-r production.txt\n')
        self.assertTrue(any(f['status'] == 'warning' for f in self.report()['findings']))

    def test_env_file_presence_not_claimed_as_loaded(self):
        self.write('.env.example', 'FIXER_DEMO_SECRET=\n')
        self.write('.env', 'FIXER_DEMO_SECRET=private-test-value\n')
        with patch.dict(os.environ, {}, clear=True):
            report = self.report()
        finding = next(f for f in report['findings'] if f['title'] == 'Configuration: FIXER_DEMO_SECRET')
        self.assertEqual(finding['status'], 'warning')
        self.assertNotIn('private-test-value', json.dumps(report))

    def test_missing_config_detected_and_fixed(self):
        self.write('.env.example', 'FIXER_DEMO_ENDPOINT=\n')
        self.write('app.py', 'import os\nendpoint = os.environ["FIXER_DEMO_ENDPOINT"]\n')
        with patch.dict(os.environ, {}, clear=True):
            before = self.report()
        with patch.dict(os.environ, {'FIXER_DEMO_ENDPOINT': 'local'}):
            after = self.report()
        self.assertTrue(any(f['status'] == 'fail' for f in before['findings']))
        self.assertFalse(any(f['status'] == 'fail' for f in after['findings']))

    def test_project_code_not_executed_or_imported(self):
        self.write('json.py', 'raise RuntimeError("must not import project files")\n')
        self.write('app.py', 'open("unexpected", "w").write("executed")\n')
        self.report()
        self.assertFalse((self.root/'unexpected').exists())

    def test_syntax_error(self):
        self.write('app.py', 'def broken(\n')
        self.assertTrue(any(f['title'].startswith('Python syntax:') for f in self.report()['findings']))

    def test_optional_config_not_reported_as_blocker(self):
        self.write('.env.example', 'OPTIONAL_COLOR=\n')
        self.write('app.py', 'import os\ncolor = os.getenv("OPTIONAL_COLOR", "blue")\n')
        self.assertFalse(any(f['status'] == 'fail' for f in self.report()['findings']))

    def test_aliased_direct_lookup_without_example(self):
        self.write('app.py', 'from os import environ as settings\nx = settings["FIXER_NEW_REQUIRED"]\n')
        with patch.dict(os.environ, {}, clear=True):
            report = self.report()
        finding = next(f for f in report['findings'] if f['title'] == 'Configuration: FIXER_NEW_REQUIRED')
        self.assertEqual(finding['status'], 'fail')
        self.assertIn('app.py:2', finding['evidence'])

    def test_assignment_is_not_required_configuration(self):
        self.write('app.py', 'import os\nos.environ["FIXER_SET_BY_APP"] = "value"\n')
        self.assertFalse(any(f['title'] == 'Configuration: FIXER_SET_BY_APP' for f in self.report()['findings']))

    def test_compare_does_not_call_disappearance_resolved(self):
        before = self.report()
        before['findings'] = [{'title': 'Removed check', 'status': 'fail'}]
        after = self.report()
        change = next(c for c in fixer.compare_reports(before, after)['changes'] if c['finding'] == 'Removed check')
        self.assertEqual(change['after'], 'not checked')
        self.assertFalse(change['resolved'])

    def test_compare_rejects_other_project(self):
        before = self.report()
        before['project_id'] = 'different'
        with self.assertRaises(ValueError):
            fixer.compare_reports(before, self.report())

    def test_html_escapes_untrusted_output(self):
        report = self.report()
        report['findings'][0]['evidence'] = '<script>alert(1)</script>'
        output = fixer.html_report(report)
        self.assertNotIn('<script>', output)
        self.assertIn('&lt;script&gt;', output)

    def test_report_writes_do_not_overwrite_files(self):
        target = self.root/'report.json'
        fixer.write_report(target, 'first')
        with self.assertRaises(FileExistsError):
            fixer.write_report(target, 'second')
        self.assertEqual(target.read_text(), 'first')
        self.assertEqual(target.stat().st_mode & 0o777, 0o600)

    def test_cli_before_and_after_report(self):
        self.write('app.py', 'import os\nprint(bool(os.environ["FIXER_INTEGRATION"]))\n')
        baseline = self.root/'before.json'
        final = self.root/'after.json'
        page = self.root/'after.html'
        with patch.dict(os.environ, {}, clear=True), contextlib.redirect_stdout(io.StringIO()):
            status = fixer.main([str(self.root), '--save-report', str(baseline), '--verify', sys.executable, 'app.py'])
        self.assertEqual(status, 1)
        with patch.dict(os.environ, {'FIXER_INTEGRATION': 'yes'}), contextlib.redirect_stdout(io.StringIO()):
            status = fixer.main([str(self.root), '--compare', str(baseline), '--save-report', str(final), '--html', str(page), '--verify', sys.executable, 'app.py'])
        self.assertEqual(status, 0)
        report = json.loads(final.read_text())
        self.assertTrue(any(c['resolved'] for c in report['comparison']['changes']))
        self.assertEqual(report['comparison']['verification'], {'before': 'command failed', 'after': 'command succeeded'})
        self.assertIn('Command succeeded', page.read_text())

    def test_symlink_outside_project_not_read(self):
        with tempfile.TemporaryDirectory() as external:
            path = Path(external)/'secret'
            path.write_text('SECRET=value')
            (self.root/'.env.example').symlink_to(path)
            self.assertEqual(fixer.read_local(self.root, '.env.example'), '')

    def test_verify_exit_and_redaction(self):
        self.write('.env', 'SECRET_VALUE=private-example-value\n')
        result = fixer.verify(self.root, [sys.executable, '-c', 'print("private-example-value");raise SystemExit(3)'], 3)
        self.assertEqual(result['exit_code'], 3)
        self.assertIn('[REDACTED]', result['output'])
        self.assertNotIn('private-example-value', json.dumps(result))

    def test_verify_timeout(self):
        result = fixer.verify(self.root, [sys.executable, '-c', 'import time;time.sleep(10)'], 1)
        self.assertTrue(result['timed_out'])
        self.assertEqual(result['result'], 'timed out')

    def test_ai_request_contract_without_network(self):
        body = io.BytesIO(json.dumps({'content': [{'type': 'text', 'text': 'Check the environment.'}]}).encode())
        with patch('urllib.request.urlopen', return_value=body) as call:
            response = fixer.diagnose({'findings': []}, 'fake-test-key', 'test-model')
        request = call.call_args.args[0]
        self.assertEqual(request.full_url, 'https://api.anthropic.com/v1/messages')
        self.assertEqual(json.loads(request.data)['model'], 'test-model')
        self.assertNotIn('fake-test-key', request.data.decode())
        self.assertEqual(response, 'Check the environment.')

    def test_ai_rejects_empty_malformed_and_truncated_responses(self):
        responses = [[], {'content': None}, {'content': []},
                     {'content': [{'type': 'text', 'text': '   '}]},
                     {'content': [{'type': 'text', 'text': 'Partial advice'}], 'stop_reason': 'max_tokens'}]
        for response in responses:
            with self.subTest(response=response):
                body = io.BytesIO(json.dumps(response).encode())
                with patch('urllib.request.urlopen', return_value=body), self.assertRaises(ValueError):
                    fixer.diagnose({'findings': []}, 'fake-test-key', 'test-model')

    def test_successful_command_does_not_clear_unresolved_configuration(self):
        self.write('app.py', 'import os\nkey = os.environ.get("FIXER_FEATURE_KEY")\n')
        with patch.dict(os.environ, {}, clear=True):
            report = self.report()
        report['verification'] = {'exit_code': 0, 'timed_out': False}
        summary = fixer.readiness(report)
        self.assertEqual(summary['verification_command']['status'], 'passed')
        self.assertEqual(summary['configuration']['status'], 'needs review')
        self.assertIn('FIXER_FEATURE_KEY', summary['configuration']['unresolved'])
        finding = next(f for f in report['findings'] if f['title'] == 'Configuration: FIXER_FEATURE_KEY')
        self.assertNotIn('optional', finding['evidence'])

    def test_present_dependencies_without_verification(self):
        report = {'findings': [{'title': 'Dependency: example', 'status': 'pass', 'evidence': 'Installed 1.0.'}]}
        summary = fixer.readiness(report)
        self.assertEqual(summary['dependencies']['status'], 'declared dependencies present')
        self.assertEqual(summary['verification_command']['status'], 'not run')
        self.assertEqual(summary['configuration']['status'], 'unknown')

    def test_partial_dependency_inspection_is_not_ready(self):
        self.write('requirements.txt', '-r extra.txt\n')
        self.assertEqual(self.report()['readiness']['dependencies']['status'], 'not fully checked')

    def test_dependency_failure_survives_successful_test_command(self):
        self.write('requirements.txt', 'setup-fixer-nonexistent-example==1.0\n')
        report = self.report()
        report['verification'] = {'exit_code': 0, 'timed_out': False}
        summary = fixer.readiness(report)
        self.assertEqual(summary['dependencies']['status'], 'blocked')
        self.assertEqual(summary['verification_command']['status'], 'passed')

    def test_command_timeout_and_failure_remain_distinct(self):
        report = {'findings': [], 'verification': {'exit_code': -9, 'timed_out': True}}
        self.assertEqual(fixer.readiness(report)['verification_command']['status'], 'timed out')
        report['verification'] = {'exit_code': 1, 'timed_out': False}
        self.assertEqual(fixer.readiness(report)['verification_command']['status'], 'failed')

    def test_terminal_and_html_keep_scope_visible(self):
        report = self.report()
        with contextlib.redirect_stdout(io.StringIO()) as output:
            fixer.render(report)
        self.assertIn('WHAT IS VERIFIED', output.getvalue())
        self.assertNotIn('0 blocking', output.getvalue())
        self.assertIn('What is verified', fixer.html_report(report))
        self.assertIn('does not prove that every feature is ready', fixer.html_report(report))


if __name__ == '__main__':
    unittest.main()
