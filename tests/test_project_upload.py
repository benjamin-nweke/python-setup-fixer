import io
import os
from pathlib import Path
import stat
import sys
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fixer
import project_upload as uploads


def archive(entries):
    data = io.BytesIO()
    with zipfile.ZipFile(data, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, value in entries:
            z.writestr(name, value)
    return data.getvalue()


class UploadTests(unittest.TestCase):
    def test_demo_inspection_and_actual_verification(self):
        data = (Path(fixer.__file__).parent/'examples/expense-demo.zip').read_bytes()
        imported = uploads.extract_project(data)
        base = Path(imported.workspace.name)
        try:
            self.assertEqual(imported.candidates, ['expense-demo'])
            root = base/imported.candidates[0]
            with patch.dict(os.environ, {}, clear=True):
                report = fixer.check(root, sys.executable)
                self.assertTrue(any(f['status'] == 'fail' for f in report['findings']))
                self.assertEqual(fixer.verify(root, [sys.executable, 'app.py'], 5)['exit_code'], 1)
                result = fixer.verify(root, [sys.executable, 'app.py'], 5, {'EXPENSE_DEMO_CSV':'expenses.csv'})
                self.assertEqual(result['exit_code'], 0)
                self.assertIn('50.00', result['output'])
        finally:
            imported.cleanup()
        self.assertFalse(base.exists())

    def test_traversal_links_duplicates_and_invalid_zip(self):
        for path in ['../evil.py', '/tmp/evil.py', 'C:/evil.py', 'a\\evil.py']:
            with self.subTest(path=path), self.assertRaises(ValueError):
                uploads.extract_project(archive([(path, 'pass')]))
        link = zipfile.ZipInfo('link.py')
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        for data in [archive([(link, '/tmp')]), archive([('a.py','pass'),('A.py','pass')]), b'not a zip']:
            with self.assertRaises(ValueError):
                uploads.extract_project(data)

    def test_exclusions_and_multiple_roots(self):
        data = archive([('a/app.py','pass'),('a/requirements.txt',''),('b/pyproject.toml',''),('.git/config','secret'),('a/.venv/bin/python','bad'),('a/.env','secret'),('a/.env.example','X=')])
        imported = uploads.extract_project(data)
        try:
            self.assertEqual(imported.candidates, ['a','b'])
            self.assertEqual(imported.skipped, 3)
            base = Path(imported.workspace.name)
            self.assertTrue((base/'a/.env.example').exists())
            self.assertFalse((base/'a/.env').exists())
        finally:
            imported.cleanup()

    def test_limits_and_no_python(self):
        data = archive([('app.py','x'*100)])
        for constant in ['MAX_ARCHIVE','MAX_TOTAL','MAX_FILE','MAX_ENTRIES']:
            with patch.object(uploads, constant, 0), self.assertRaises(ValueError):
                uploads.extract_project(data)
        with self.assertRaises(ValueError):
            uploads.extract_project(archive([('readme.txt','hello')]))
