"""Run with the GUI requirements installed; no API calls are made."""
from pathlib import Path
import os
import io
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fixer
try:
    from streamlit.testing.v1 import AppTest
except ImportError:
    AppTest = None


@unittest.skipIf(AppTest is None, 'Install requirements-gui.txt to run GUI tests')
class GuiFlow(unittest.TestCase):
    def setUp(self):
        backend = patch('credentials.backend_key', return_value='')
        backend.start()
        self.addCleanup(backend.stop)

    def app(self):
        return AppTest.from_file(str(Path(fixer.__file__).with_name('gui.py'))).run(timeout=30)

    def button(self, app, label):
        return next(b for b in app.button if b.label == label)

    def checkbox(self, app, label):
        return next(b for b in app.checkbox if b.label == label)

    def test_zip_upload_and_removal(self):
        app = self.app()
        self.button(app, 'Upload project ZIP').click().run()
        self.assertEqual(app.selectbox[0].value, 'Upload a project ZIP')
        data = (Path(fixer.__file__).parent/'examples/expense-demo.zip').read_bytes()
        with patch('streamlit.file_uploader', return_value=io.BytesIO(data)):
            app.selectbox[0].select('Upload a project ZIP').run()
            self.assertFalse(app.exception)
            imported_path = Path(app.session_state['uploaded_project'].workspace.name)
            self.button(app, 'Check project').click().run(timeout=30)
            self.assertEqual(app.session_state['report']['project'], 'expense-demo')
            self.assertFalse(app.exception)
        with patch('streamlit.file_uploader', side_effect=[io.BytesIO(data), None]):
            self.button(app, 'Remove uploaded project').click().run()
            self.assertFalse(imported_path.exists())
            self.assertNotIn('report', app.session_state)
            self.assertFalse(app.exception)

    def test_backend_key_keeps_consent_and_stays_out_of_report(self):
        with patch('credentials.backend_key', return_value='test-backend-key'), patch.object(fixer, 'diagnose', return_value='Review the setting.') as diagnose:
            app = self.app()
            self.button(app, 'Check project').click().run(timeout=30)
            self.assertFalse(any(t.label == 'Anthropic API key' for t in app.text_input))
            self.button(app, 'Explain with Claude').click().run()
            diagnose.assert_not_called()
            self.checkbox(app, 'Send this report to Anthropic using my API credits').check()
            self.button(app, 'Explain with Claude').click().run()
            diagnose.assert_called_once()
            self.assertEqual(diagnose.call_args.args[1], 'test-backend-key')
            self.assertNotIn('test-backend-key', str(app.session_state['report']))
            self.assertFalse(app.exception)

    def test_empty_and_invalid_folder(self):
        app = self.app()
        self.assertFalse(app.exception)
        app.selectbox[0].select('My local project').run()
        self.assertTrue(self.button(app, 'Check project').disabled)
        next(t for t in app.text_input if t.label == 'Local project folder').set_value('/nonexistent/fixer-project').run()
        self.button(app, 'Check project').click().run()
        self.assertTrue(any('does not exist' in e.value for e in app.error))
        self.assertFalse(app.exception)

    def test_complete_demo_and_comparison(self):
        with patch.dict(os.environ, {}, clear=True):
            app = self.app()
            self.button(app, 'Check project').click().run(timeout=30)
            self.assertFalse(app.exception)
            self.assertEqual(sum('finding fail' in item.value for item in app.markdown), 1)
            self.assertEqual(app.session_state['report']['readiness']['configuration']['status'], 'needs review')
            with patch.object(fixer, 'verify', side_effect=AssertionError('No trust checkbox')):
                self.button(app, 'Run verification').click().run()
                self.assertTrue(app.warning)
            self.checkbox(app, 'I trust this project and want to execute this command').check()
            self.button(app, 'Run verification').click().run(timeout=30)
            self.assertEqual(app.session_state['report']['verification']['exit_code'], 1)
            self.button(app, 'Use this result as the baseline').click().run()
            self.button(app, 'Set demo endpoint to local').click().run()
            self.button(app, 'Run verification').click().run(timeout=30)
            report = app.session_state['report']
            self.assertEqual(report['verification']['exit_code'], 0)
            self.assertTrue(any(c['resolved'] for c in report['comparison']['changes']))
            self.assertEqual(report['comparison']['verification']['before'], 'command failed')
            self.assertNotIn('FIXER_DEMO_ENDPOINT', os.environ)
            self.assertFalse(app.exception)

    def test_expense_demo_repair_and_totals(self):
        project = Path(fixer.__file__).parent / 'examples/expense-demo'
        original = (project / 'expenses.csv').read_bytes()
        with patch.dict(os.environ, {}, clear=True):
            app = self.app()
            app.selectbox[0].select('Expense demo').run()
            self.button(app, 'Check project').click().run(timeout=30)
            self.assertTrue(any(f['status'] == 'fail' and 'EXPENSE_DEMO_CSV' in f['title']
                                for f in app.session_state['report']['findings']))
            self.checkbox(app, 'I trust this project and want to execute this command').check()
            self.button(app, 'Run verification').click().run(timeout=30)
            self.assertEqual(app.session_state['report']['verification']['exit_code'], 1)
            self.assertEqual(app.session_state['baseline']['verification']['exit_code'], 1)
            self.button(app, 'Use included expense data').click().run()
            self.button(app, 'Run verification').click().run(timeout=30)
            report = app.session_state['report']
            self.assertEqual(report['verification']['exit_code'], 0)
            output = report['verification']['output']
            self.assertIn('Records: 6', output)
            for name, total in [('Food', '20.00'), ('Supplies', '18.00'), ('Transport', '12.00'), ('TOTAL', '50.00')]:
                self.assertRegex(output, name + r'\s+' + total.replace('.', r'\.'))
            self.assertTrue(any(c['resolved'] for c in report['comparison']['changes']))
            self.assertEqual(report['comparison']['verification']['before'], 'command failed')
            self.button(app, 'Run verification').click().run(timeout=30)
            self.assertEqual(app.session_state['report']['comparison']['verification']['before'], 'command failed')
            self.assertNotIn('EXPENSE_DEMO_CSV', os.environ)
            self.assertFalse(app.exception)
            self.button(app, 'Reset demo').click().run()
            self.assertNotIn('report', app.session_state)
            self.assertNotIn('baseline', app.session_state)
            self.assertNotIn('env_values', app.session_state)
            self.assertEqual(app.selectbox[0].value, 'Expense demo')
            self.button(app, 'Check project').click().run(timeout=30)
            self.assertFalse(self.checkbox(app, 'I trust this project and want to execute this command').value)
            self.assertTrue(any(f['status'] == 'fail' and 'EXPENSE_DEMO_CSV' in f['title']
                                for f in app.session_state['report']['findings']))
            self.assertFalse(app.exception)
        self.assertEqual((project / 'expenses.csv').read_bytes(), original)

    def test_claude_requires_consent_and_clears_key(self):
        app = self.app()
        self.button(app, 'Check project').click().run(timeout=30)
        with patch.object(fixer, 'diagnose', return_value='Suggested check. No repairs executed.') as diagnose:
            self.button(app, 'Explain with Claude').click().run()
            diagnose.assert_not_called()
            next(t for t in app.text_input if t.label == 'Anthropic API key').set_value('fake-gui-key')
            self.checkbox(app, 'Send this report to Anthropic using my API credits').check()
            self.button(app, 'Explain with Claude').click().run(timeout=30)
            diagnose.assert_called_once()
            self.assertNotIn('fake-gui-key', str(diagnose.call_args.args[0]))
            self.assertEqual(next(t for t in app.text_input if t.label == 'Anthropic API key').value, '')
            self.assertIn('Suggested check', app.session_state['diagnosis'])
            self.assertFalse(app.exception)
            original_report = app.session_state['diagnosis_report']
            self.button(app, 'Set demo endpoint to local').click().run()
            self.checkbox(app, 'I trust this project and want to execute this command').check()
            self.button(app, 'Run verification').click().run(timeout=30)
            self.assertIn('Suggested check', app.session_state['diagnosis'])
            self.assertEqual(app.session_state['diagnosis_report'], original_report)
            self.assertTrue(any('Earlier explanation:' in item.value for item in app.info))
            diagnose.assert_called_once()
            app.selectbox[0].select('Expense demo').run()
            self.assertNotIn('diagnosis', app.session_state)


class SessionEnvironment(unittest.TestCase):
    def test_values_are_isolated_and_redacted(self):
        project = Path(fixer.__file__).parent/'examples/missing-config'
        with patch.dict(os.environ, {}, clear=True):
            report = fixer.check(project, sys.executable, {'FIXER_DEMO_ENDPOINT': 'private-session-value'})
            self.assertEqual(report['readiness']['configuration']['status'], 'observed variables set')
            result = fixer.verify(project, [sys.executable, '-c', 'import os;print(os.environ["FIXER_DEMO_ENDPOINT"])'], 5,
                                  {'FIXER_DEMO_ENDPOINT': 'private-session-value'})
            self.assertEqual(result['exit_code'], 0)
            self.assertNotIn('private-session-value', str(report) + str(result))
            self.assertIn('[REDACTED]', result['output'])
            self.assertNotIn('FIXER_DEMO_ENDPOINT', os.environ)


if __name__ == '__main__':
    unittest.main()
