#!/usr/bin/env python3
"""Check, synchronize and build explicit release payloads. No network or publishing."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SKILL = Path('skills/book-to-mentor')
MANIFESTS = ('.codex-plugin/plugin.json', '.claude-plugin/plugin.json')
# Only these resources are copied into the independently installable skill.
RESOURCES = (
    'scripts/extract.py', 'scripts/mentor_state.py', 'scripts/validate_mentor.py',
    'assets/mentor-template.md', 'assets/mentor-template.en.md',
    'docs/formats.md', 'docs/formats.zh-CN.md',
    'docs/state-schema.md', 'docs/state-schema.en.md', 'LICENSE',
)
PLUGIN_FILES = (
    *MANIFESTS, '.agents/plugins/marketplace.json', '.claude-plugin/marketplace.json',
    'README.md', 'README.zh-CN.md', 'CHANGELOG.md', 'LICENSE', 'PRIVACY.md',
    'TERMS.md', 'CONTRIBUTING.md', 'assets/banner.svg', 'assets/xiaohongshu-qr.jpg',
    'docs/releasing.md', 'docs/releasing.zh-CN.md', 'docs/platforms.md',
    'docs/formats.md', 'docs/formats.zh-CN.md', 'docs/state-schema.md',
    'docs/state-schema.en.md', 'docs/blueprint.md',
)


def config(root):
    return json.loads((root / 'release.json').read_text(encoding='utf-8'))


def stable_version(version):
    if not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', version):
        raise ValueError('use a stable version such as 1.2.3 (no v prefix)')
    return tuple(map(int, version.split('.')))


def source_bytes(root, relative):
    path = root / relative
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f'release source must be a regular in-repository file: {relative}')
    return path.read_bytes()


def sync(root):
    if (root / SKILL).is_symlink() or not (root / SKILL).resolve().is_relative_to(root.resolve()):
        raise ValueError('skill directory must be inside the repository')
    for relative in RESOURCES:
        data = source_bytes(root, relative)
        target = root / SKILL / relative
        if target.is_symlink() or not target.resolve().is_relative_to((root / SKILL).resolve()):
            raise ValueError(f'unsafe generated resource: {target}')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def bump(root, version):
    settings = config(root)
    if stable_version(version) <= stable_version(settings['version']):
        raise ValueError('new version must be greater than the current version')
    settings['version'] = version
    for relative in ('release.json', *MANIFESTS):
        payload = settings if relative == 'release.json' else json.loads((root / relative).read_text())
        payload['version'] = version
        (root / relative).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    sync(root)


def release_notes(root, version):
    changelog = (root / 'CHANGELOG.md').read_text(encoding='utf-8')
    section = re.search(r'^## ' + re.escape(version) + r'\s*\n(.*?)(?=^## |\Z)', changelog, re.M | re.S)
    if not section or not section.group(1).strip():
        raise ValueError(f'CHANGELOG.md needs release notes for {version}')
    return section.group(1).strip() + '\n'


def check_links(root, files):
    for relative in files:
        # Mentor templates deliberately reference files the agent creates later.
        if not str(relative).endswith('.md') or '/mentor-template' in str(relative):
            continue
        content = source_bytes(root, relative).decode('utf-8')
        targets = re.findall(r'\[[^\]\n]*\]\(([^\s)]+)\)', content)
        targets += re.findall(r'(?:src|href)="([^"]+)"', content)
        for target in targets:
            parts = urlsplit(target)
            if parts.scheme or target.startswith('#'):
                continue
            path = ((root / relative).parent / unquote(parts.path)).resolve()
            if not path.is_relative_to(root.resolve()) or not path.is_file():
                raise ValueError(f'broken local link in {relative}: {target}')


def skill_files():
    return (SKILL / 'SKILL.md', *(SKILL / relative for relative in RESOURCES))


def check(root, tag=None):
    settings = config(root)
    version = settings['version']
    stable_version(version)
    if tag and tag != f'v{version}':
        raise ValueError(f'tag {tag} does not match release version v{version}')
    for relative in MANIFESTS:
        manifest = json.loads(source_bytes(root, relative))
        if manifest.get('name') != settings['skill'] or manifest.get('version') != version:
            raise ValueError(f'{relative}: name/version mismatch')
    for relative in RESOURCES:
        if source_bytes(root, relative) != source_bytes(root, SKILL / relative):
            raise ValueError(f'outdated bundled {relative}; run python scripts/release.py sync')
    entry = source_bytes(root, SKILL / 'SKILL.md').decode('utf-8')
    if not entry.startswith('---\nname: book-to-mentor\n') or '../../' in entry:
        raise ValueError('skill entrypoint must be self-contained with valid frontmatter')
    expected = {str(p.relative_to(SKILL)) for p in skill_files()}
    actual = {str(p.relative_to(root / SKILL)) for p in (root / SKILL).rglob('*')
              if p.is_file() and '__pycache__' not in p.parts}
    if actual != expected:
        raise ValueError(f'unexpected or missing bundled files: {actual ^ expected}')
    for relative in (*PLUGIN_FILES, *skill_files()):
        source_bytes(root, relative)
    check_links(root, (*PLUGIN_FILES, *skill_files()))
    release_notes(root, version)
    return settings


def archive(path, files):
    with zipfile.ZipFile(path, 'x', compression=zipfile.ZIP_DEFLATED) as stream:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(f'book-to-mentor/{name}', date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            stream.writestr(info, data)


def build(root, output, tag=None):
    settings = check(root, tag)
    version = settings['version']
    destination = output / f'v{version}'
    destination.mkdir(parents=True, exist_ok=False)
    source_commit = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    skill = {str(p.relative_to(SKILL)): source_bytes(root, p) for p in skill_files()}
    plugin = {str(p): source_bytes(root, p) for p in (*PLUGIN_FILES, *skill_files())}
    # ClawHub accepts text bundles. QR and SVG branding stay in the GitHub/plugin package.
    bundle = destination / 'clawhub' / 'book-to-mentor'
    for name, data in skill.items():
        path = bundle / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    archive(destination / f'book-to-mentor-{version}.zip', skill)
    archive(destination / f'book-to-mentor-plugin-{version}.zip', plugin)
    report = {'version': version, 'source_commit': source_commit,
              'skill_files': {name: hashlib.sha256(data).hexdigest() for name, data in sorted(skill.items())}}
    (destination / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    (destination / 'release-notes.md').write_text(release_notes(root, version), encoding='utf-8')
    checklist = f'''# Distribution follow-up / 分发后续 — v{version}

Source commit: `{source_commit}`

- [ ] Confirm GitHub Release archives and SHA256SUMS are attached.
- [ ] Check clawhub-result.json: accepted/pending is not the same as public/approved.
- [ ] Review https://www.codex-marketplace.com/submit and submit the new revision if needed (third-party review).
- [ ] Review/update https://github.com/agentskillexchange/skills/pull/76 if listing content changed.
- [ ] Review/update https://github.com/skillcreatorai/Awesome-Agent-Skills/pull/17 if the copied workflow changed.
- [ ] Ask Claude Code users to refresh the marketplace and update the plugin, or enable its auto-updates.
- [ ] Ask skills CLI users to run `npx skills update book-to-mentor`.

需人工审核的平台不会被此工作流自动批准。目录副本更新仍需 PR；审核监控不等于发布同步。
'''
    (destination / 'distribution-checklist.md').write_text(checklist, encoding='utf-8')
    sums = ''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n'
                   for p in sorted(destination.iterdir()) if p.is_file())
    (destination / 'SHA256SUMS').write_text(sums, encoding='utf-8')
    return destination


def verify_payload(root, directory):
    """Fail before any network write if an artifact is incomplete or mismatched."""
    settings = check(root)
    version = settings['version']
    manifest = json.loads((directory / 'manifest.json').read_text())
    commit = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    if manifest.get('version') != version or manifest.get('source_commit') != commit:
        raise ValueError('artifact version/source commit mismatch')
    expected = {f'book-to-mentor-{version}.zip', f'book-to-mentor-plugin-{version}.zip',
                'manifest.json', 'release-notes.md', 'distribution-checklist.md'}
    entries = (directory / 'SHA256SUMS').read_text().splitlines()
    checksums = dict(line.split('  ', 1)[::-1] for line in entries)
    if set(checksums) != expected or len(entries) != len(expected):
        raise ValueError('unexpected checksum manifest file set')
    actual = {p.name for p in directory.iterdir() if p.is_file()}
    if actual - {'SHA256SUMS', 'clawhub-result.json'} != expected:
        raise ValueError('unexpected release asset file set')
    for name, digest in checksums.items():
        if hashlib.sha256(source_bytes(directory, name)).hexdigest() != digest:
            raise ValueError(f'artifact checksum mismatch: {name}')
    bundle = directory / 'clawhub/book-to-mentor'
    bundled = {str(p.relative_to(bundle)): hashlib.sha256(source_bytes(bundle, p.relative_to(bundle))).hexdigest()
               for p in bundle.rglob('*') if p.is_file()}
    source = {str(p.relative_to(SKILL)): hashlib.sha256(source_bytes(root, p)).hexdigest()
              for p in skill_files()}
    if bundled != manifest.get('skill_files') or bundled != source:
        raise ValueError('artifact skill content mismatch')
    return settings, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('sync')
    prepare = sub.add_parser('bump')
    prepare.add_argument('version')
    validate = sub.add_parser('check')
    validate.add_argument('--tag')
    package = sub.add_parser('build')
    package.add_argument('--tag')
    package.add_argument('--output', type=Path, default=ROOT / 'dist')
    args = parser.parse_args()
    try:
        if args.command == 'sync':
            sync(ROOT)
            print('Bundled resources synchronized.')
        elif args.command == 'bump':
            bump(ROOT, args.version)
            print(f'Prepared {args.version}; add CHANGELOG notes, then run check.')
        elif args.command == 'check':
            print(json.dumps(check(ROOT, args.tag), indent=2))
        else:
            print(build(ROOT, args.output, args.tag))
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f'error: {exc}\n')


if __name__ == '__main__':
    main()
