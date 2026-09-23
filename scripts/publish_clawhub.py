#!/usr/bin/env python3
"""Publish the prepared text bundle with the pinned ClawHub CLI; save its receipt."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

from release import ROOT, verify_payload


def validate_receipt(receipt, version, dry_run):
    allowed = {'would-publish'} if dry_run else {'published', 'pending-publication', 'submitted'}
    if receipt.get('status') not in allowed or receipt.get('version') != version:
        raise ValueError(f'unexpected ClawHub receipt: {receipt.get("status")} / {receipt.get("version")}')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    directory = args.directory.resolve()
    settings, manifest = verify_payload(ROOT, directory)
    version = settings['version']
    bundle = directory / 'clawhub/book-to-mentor'
    token = os.environ.get('CLAWHUB_TOKEN', '')
    if not args.dry_run and not token:
        parser.error('configure the CLAWHUB_TOKEN repository secret before publishing')
    with tempfile.TemporaryDirectory(prefix='clawhub-release-') as temporary:
        auth = Path(temporary) / 'config.json'
        auth.write_text(json.dumps({'registry': 'https://clawhub.ai', 'token': token}))
        auth.chmod(0o600)
        env = {**os.environ, 'CLAWHUB_CONFIG_PATH': str(auth), 'CLAWHUB_DISABLE_TELEMETRY': '1'}
        command = ['npx', '--yes', f'clawhub@{settings["clawhub_cli_version"]}',
                   '--no-input', 'skill', 'publish', str(bundle),
                   '--slug', settings['skill'], '--name', 'Book to Mentor',
                   '--owner', settings['clawhub_owner'], '--version', version,
                   '--changelog', (directory / 'release-notes.md').read_text(),
                   '--tags', 'latest', '--topics', 'books,learning,mentor,agent-skills',
                   '--source-repo', f'https://github.com/{settings["repository"]}',
                   '--source-commit', manifest['source_commit'], '--source-ref', f'v{version}',
                   '--source-path', 'skills/book-to-mentor', '--json']
        if args.dry_run:
            command.append('--dry-run')
        # Explicit versions never silently create a different patch version on retries.
        # A duplicate-version rejection needs receipt inspection; do not overwrite it.
        result = subprocess.run(command, env=env, text=True, capture_output=True, timeout=300)
        if result.returncode:
            detail = result.stderr.replace(token, '[redacted]') if token else result.stderr
            parser.exit(1, 'ClawHub publish failed; inspect the exact version before retrying.\n' + detail)
        receipt = validate_receipt(json.loads(result.stdout), version, args.dry_run)
        (directory / 'clawhub-result.json').write_text(json.dumps(receipt, indent=2) + '\n')
        print(f'ClawHub {version}: {receipt["status"]}')
        summary = os.environ.get('GITHUB_STEP_SUMMARY')
        if summary:
            with open(summary, 'a', encoding='utf-8') as stream:
                stream.write(f'\nClawHub `{version}`: **{receipt["status"]}**. '
                             'Pending/submitted is not public approval.\n')


if __name__ == '__main__':
    main()
