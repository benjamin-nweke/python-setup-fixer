"""Bounded ZIP extraction for local project inspection. Never executes files."""
import io
from pathlib import Path, PurePosixPath
import stat
import tempfile
import zipfile

MAX_ARCHIVE = 20 * 1024 * 1024
MAX_TOTAL = 60 * 1024 * 1024
MAX_FILE = 5 * 1024 * 1024
MAX_ENTRIES = 2000
SKIP_DIRS = {'.git', '.venv', 'venv', 'env', '__pycache__', 'node_modules', '__MACOSX'}
MARKERS = {'pyproject.toml', 'requirements.txt', 'setup.py', 'setup.cfg', '.python-version'}


class UploadedProject:
    def __init__(self, workspace, candidates, skipped):
        self.workspace = workspace
        self.candidates = candidates
        self.skipped = skipped

    def cleanup(self):
        self.workspace.cleanup()


def extract_project(data):
    if len(data) > MAX_ARCHIVE:
        raise ValueError('ZIP exceeds the 20 MB upload limit.')
    workspace = tempfile.TemporaryDirectory(prefix='python-setup-upload-')
    base = Path(workspace.name)
    skipped = 0
    total = 0
    seen = set()
    files = []
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_ENTRIES:
                raise ValueError('ZIP contains more than 2,000 entries.')
            for entry in entries:
                name = entry.orig_filename
                parts = PurePosixPath(name).parts
                if not parts or '\x00' in name or '\\' in name or ':' in name or name.startswith('/') or '..' in parts:
                    raise ValueError('ZIP contains an unsafe file path.')
                kind = stat.S_IFMT(entry.external_attr >> 16)
                if kind not in (0, stat.S_IFREG, stat.S_IFDIR):
                    raise ValueError('ZIP links and special files are not supported.')
                if entry.flag_bits & 1:
                    raise ValueError('Password-protected ZIP files are not supported.')
                if any(part in SKIP_DIRS for part in parts) or (parts[-1].startswith('.env') and parts[-1] != '.env.example') or parts[-1] == '.DS_Store':
                    skipped += 1
                    continue
                normalized = '/'.join(parts).casefold()
                if normalized in seen:
                    raise ValueError('ZIP contains duplicate file paths.')
                seen.add(normalized)
                if entry.is_dir():
                    continue
                if entry.file_size > MAX_FILE or total + entry.file_size > MAX_TOTAL:
                    raise ValueError('ZIP exceeds the 5 MB per-file or 60 MB extracted limit.')
                target = base.joinpath(*parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(entry) as source, target.open('xb') as destination:
                    count = 0
                    while True:
                        chunk = source.read(65536)
                        if not chunk:
                            break
                        count += len(chunk)
                        total += len(chunk)
                        if count > MAX_FILE or total > MAX_TOTAL:
                            raise ValueError('ZIP exceeds the extraction limit.')
                        destination.write(chunk)
                target.chmod(0o600)
                files.append(target)
        if not any(path.suffix == '.py' or path.name in MARKERS for path in files):
            raise ValueError('No Python source or supported project metadata found in this ZIP.')
        roots = {path.parent for path in files if path.name in MARKERS}
        if not roots:
            roots = {path.parent for path in files if path.suffix == '.py'}
        candidates = sorted((str(path.relative_to(base)) for path in roots), key=lambda path: (len(Path(path).parts), path))
        return UploadedProject(workspace, candidates, skipped)
    except (ValueError, OSError, RuntimeError, zipfile.BadZipFile, NotImplementedError) as exc:
        workspace.cleanup()
        raise ValueError('Could not import project: ' + str(exc)) from exc
