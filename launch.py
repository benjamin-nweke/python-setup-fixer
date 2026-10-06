"""Start the local interface with consistent settings, from any folder."""
from pathlib import Path
import importlib.util
import os
import sys


def main():
    if importlib.util.find_spec('streamlit') is None:
        raise SystemExit('GUI dependencies are missing. Install requirements-gui.txt with this Python first.')
    root = Path(__file__).resolve().parent
    os.chdir(root)
    os.execv(sys.executable, [sys.executable, '-m', 'streamlit', 'run', str(root/'gui.py'),
        '--server.address', '127.0.0.1', '--server.port', '8501',
        '--server.runOnSave', 'true', '--server.maxUploadSize', '20',
        '--browser.gatherUsageStats', 'false', '--theme.base', 'light',
        '--theme.primaryColor', '#315bda', '--theme.backgroundColor', '#edf1f7',
        '--theme.secondaryBackgroundColor', '#e4ebf6', '--theme.textColor', '#17243c'])


if __name__ == '__main__':
    main()
