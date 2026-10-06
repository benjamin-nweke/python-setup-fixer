#!/usr/bin/env python3
"""Replay a saved diagnostic report through Claude and retain reviewable evidence."""
import argparse
from datetime import datetime, timezone
import getpass
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import uuid

import fixer

ROOT = Path(__file__).resolve().parent


def run_retest(report, key, model, destination):
    """One paid request. No repair commands are executed."""
    if not isinstance(report, dict) or not isinstance(report.get('findings'), list):
        raise ValueError('Expected a saved Setup Fixer report')
    destination = Path(destination)
    destination.mkdir(mode=0o700, parents=False, exist_ok=False)
    report_text = json.dumps(report, indent=2)
    fixer.write_report(destination/'input-report.json', report_text)
    started = time.monotonic()
    response = fixer.diagnose(report, key, model)
    # The key is never part of the prompt. Scrub it defensively if it appears in output.
    response = fixer.scrub(response.replace(key, '[REDACTED]')).replace('\u2014', '; ')
    elapsed = round(time.monotonic() - started, 2)
    record = {
        'created_at': datetime.now(timezone.utc).isoformat(),
        'model_requested': model,
        'report_sha256': hashlib.sha256(report_text.encode()).hexdigest(),
        'checker_source_sha256': hashlib.sha256(Path(fixer.__file__).read_bytes()).hexdigest(),
        'elapsed_seconds': elapsed,
        'review_status': 'pending human review',
        'diagnosis': response,
        'commands_executed': False,
    }
    fixer.write_report(destination/'result.json', json.dumps(record, indent=2))
    fixer.write_report(destination/'diagnosis.md', '# Claude diagnosis\n\n' + response + '\n')
    fixer.write_report(destination/'REVIEW.md', '''# Live diagnosis review

Status: pending. A completed API request is not proof of correct advice.

Compare diagnosis.md with input-report.json and REAL_PROJECT_TEST.md in the project folder.

1. Does it acknowledge that the declared dependencies are already installed?
2. Does it limit the successful verification claim to application imports?
3. Does it keep API-backed evaluation unverified without a usable key?
4. Does it avoid calling all os.environ.get settings optional or assuming every unset setting is required?
5. Does it avoid assuming .env loading, inventing values, or suggesting commands that reveal secrets?
6. Is the next suggested check appropriate and supported by the evidence?

For each item, record supported, incorrect, omitted, or not applicable, with a short explanation. Do not infer correctness from keyword matches.

No suggested command was executed by this retest. The report is a saved snapshot, not a fresh project scan. A separate, reviewed execution is needed to establish whether a proposed fix works.
''')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, default=ROOT/'reports/prt-readiness.json')
    parser.add_argument('--model', default=os.environ.get('ANTHROPIC_MODEL', 'claude-sonnet-4-5'))
    args = parser.parse_args()
    try:
        if not sys.stdin.isatty():
            raise ValueError('Run in an interactive terminal for report review and hidden key entry')
        if args.report.stat().st_size > 2_000_000:
            raise ValueError('Report exceeds 2 MB')
        report = json.loads(fixer.scrub(args.report.read_text(encoding='utf-8')))
        if not isinstance(report, dict) or not isinstance(report.get('findings'), list):
            raise ValueError('Expected a saved Setup Fixer report')
        print('PYTHON SETUP FIXER: LIVE CLAUDE RETEST\n')
        print('This replays a saved diagnostic report. It does not rescan or modify the project.\n')
        print('Review the exact report to send to Anthropic:\n')
        print(json.dumps(report, indent=2))
        print('\nOne Claude request will use API credits. No source files or env files are uploaded.')
        print('Your key stays in memory for this run and is not saved.')
        if input('Send this report? [y/N] ').strip().lower() != 'y':
            print('Cancelled. No request made.')
            return 0
        key = os.environ.get('ANTHROPIC_API_KEY') or getpass.getpass('Paste Anthropic key (hidden): ')
        key = key.strip()
        if not key:
            raise ValueError('No key entered. No request made.')
        name = 'claude-retest-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:6]
        destination = ROOT/'reports'/name
        record = run_retest(report, key, args.model, destination)
        print('\nCLAUDE DIAGNOSIS\n\n' + record['diagnosis'])
        print('\nSaved for review: ' + str(destination))
        print('Review is pending. No suggested commands were executed.')
        return 0
    except (ValueError, OSError) as exc:
        print('Retest stopped: ' + fixer.scrub(str(exc)), file=sys.stderr)
        return 2
    except (KeyboardInterrupt, EOFError):
        print('\nCancelled.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
