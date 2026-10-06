import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import live_retest


class RetestEvidence(unittest.TestCase):
    def test_request_is_saved_without_key_and_never_self_certified(self):
        report = {'findings': [], 'project': 'example'}
        key = 'fake-private-test-key'
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder)/'run'
            with patch.object(live_retest.fixer, 'diagnose', return_value='Unverified advice ' + key) as call:
                result = live_retest.run_retest(report, key, 'test-model', destination)
            call.assert_called_once_with(report, key, 'test-model')
            self.assertEqual(result['review_status'], 'pending human review')
            self.assertFalse(result['commands_executed'])
            self.assertEqual(json.loads((destination/'input-report.json').read_text()), report)
            for path in destination.iterdir():
                self.assertNotIn(key, path.read_text())
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_failed_request_does_not_create_success_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder)/'run'
            with patch.object(live_retest.fixer, 'diagnose', side_effect=ValueError('Key rejected')):
                with self.assertRaises(ValueError):
                    live_retest.run_retest({'findings': []}, 'fake-key', 'test-model', destination)
            self.assertTrue((destination/'input-report.json').exists())
            self.assertFalse((destination/'result.json').exists())


if __name__ == '__main__':
    unittest.main()
