#!/usr/bin/env python3
"""Create a tagged GitHub Release and upload missing assets without overwriting."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from release import ROOT, verify_payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    args = parser.parse_args()
    directory = args.directory.resolve()
    settings, _ = verify_payload(ROOT, directory)
    repo, tag = settings['repository'], f'v{settings["version"]}'
    command = ['gh', 'release', 'view', tag, '--repo', repo, '--json', 'assets,isDraft']
    found = subprocess.run(command, text=True, capture_output=True)
    if found.returncode:
        # gh itself checks existence, so an auth/network error cannot overwrite an existing release.
        subprocess.run(['gh', 'release', 'create', tag, '--repo', repo, '--verify-tag',
                        '--title', f'Book to Mentor {tag}', '--notes-file',
                        str(directory / 'release-notes.md')], check=True)
        found = subprocess.run(command, text=True, capture_output=True, check=True)
    existing = {asset['name'] for asset in json.loads(found.stdout)['assets']}
    assets = sorted(p for p in directory.iterdir() if p.is_file() and p.name != 'clawhub-result.json')
    for asset in assets:
        if asset.name in existing:
            with tempfile.TemporaryDirectory(prefix='release-verify-') as temporary:
                subprocess.run(['gh', 'release', 'download', tag, '--repo', repo,
                                '--pattern', asset.name, '--dir', temporary], check=True)
                remote = Path(temporary) / asset.name
                if hashlib.sha256(remote.read_bytes()).digest() != hashlib.sha256(asset.read_bytes()).digest():
                    raise ValueError(f'existing release asset differs: {asset.name}; publish a new version')
        else:
            subprocess.run(['gh', 'release', 'upload', tag, str(asset), '--repo', repo], check=True)
    print(f'https://github.com/{repo}/releases/tag/{tag}')


if __name__ == '__main__':
    main()
