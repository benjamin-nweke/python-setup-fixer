from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import credentials


class BackendCredentials(unittest.TestCase):
    def test_private_file_and_environment_precedence(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(credentials, 'APP_ROOT', Path(folder)), patch.dict(credentials.os.environ, {}, clear=True):
            self.assertEqual(credentials.backend_key(), '')
            (Path(folder)/'.env').write_text('ANTHROPIC_API_KEY="test-file-key"\n')
            self.assertEqual(credentials.backend_key(), 'test-file-key')
            with patch.dict(credentials.os.environ, {'ANTHROPIC_API_KEY':'test-process-key'}):
                self.assertEqual(credentials.backend_key(), 'test-process-key')
