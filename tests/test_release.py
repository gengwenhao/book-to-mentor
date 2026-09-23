"""Offline release checks: no registry credentials or external writes required."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

REPO = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('release', REPO / 'scripts/release.py')
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)
PUB_SPEC = importlib.util.spec_from_file_location('publish_clawhub', REPO / 'scripts/publish_clawhub.py')
publisher = importlib.util.module_from_spec(PUB_SPEC)
with patch.dict(sys.modules, {'release': release}):
    PUB_SPEC.loader.exec_module(publisher)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='mentor-release-test-')
        self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name)
        self.root = self.parent / 'repository'
        files = {*release.PLUGIN_FILES, *release.RESOURCES, *release.skill_files(), 'release.json'}
        for relative in files:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / relative, target)

    def test_actual_repository_and_matching_tag_pass(self):
        settings = release.check(REPO)
        release.check(REPO, f'v{settings["version"]}')

    def test_wrong_tag_and_mismatched_manifest_fail(self):
        with self.assertRaisesRegex(ValueError, 'does not match'):
            release.check(self.root, 'v0.0.0')
        manifest = self.root / release.MANIFESTS[0]
        payload = json.loads(manifest.read_text())
        payload['version'] = '0.0.0'
        manifest.write_text(json.dumps(payload))
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            release.check(self.root)

    def test_outdated_bundle_is_rejected_and_sync_repairs_it(self):
        path = self.root / 'scripts/mentor_state.py'
        path.write_text(path.read_text() + '\n# source change\n')
        with self.assertRaisesRegex(ValueError, 'outdated bundled'):
            release.check(self.root)
        release.sync(self.root)
        release.check(self.root)

    def test_unlisted_file_inside_skill_is_rejected(self):
        (self.root / release.SKILL / 'private-book.txt').write_text('private')
        with self.assertRaisesRegex(ValueError, 'unexpected or missing'):
            release.check(self.root)

    def test_symlink_source_and_generated_destination_are_rejected(self):
        path = self.root / 'scripts/extract.py'
        path.unlink()
        path.symlink_to(REPO / 'scripts/extract.py')
        with self.assertRaisesRegex(ValueError, 'in-repository'):
            release.sync(self.root)
        path.unlink()
        shutil.copyfile(REPO / 'scripts/extract.py', path)
        generated = self.root / release.SKILL / 'scripts/extract.py'
        generated.unlink()
        generated.symlink_to(path)
        with self.assertRaisesRegex(ValueError, 'unsafe generated'):
            release.sync(self.root)

    def test_broken_local_markdown_and_image_links_fail(self):
        for link in ('[bad](absent.md)', '<img src="assets/absent.svg">'):
            (self.root / 'README.md').write_text(link)
            with self.subTest(link=link), self.assertRaisesRegex(ValueError, 'broken local link'):
                release.check(self.root)

    def test_bump_updates_both_manifests_but_requires_changelog(self):
        release.bump(self.root, '999.0.0')
        for relative in ('release.json', *release.MANIFESTS):
            self.assertEqual(json.loads((self.root / relative).read_text())['version'], '999.0.0')
        with self.assertRaisesRegex(ValueError, 'release notes'):
            release.check(self.root)
        with self.assertRaisesRegex(ValueError, 'greater'):
            release.bump(self.root, '999.0.0')

    def test_build_is_deterministic_allowlisted_and_independently_runnable(self):
        (self.root / 'PRIVATE.txt').write_text('must never ship')
        with patch.object(release.subprocess, 'check_output', return_value='a' * 40):
            first = release.build(self.root, self.parent / 'first')
            second = release.build(self.root, self.parent / 'second')
        for path in first.iterdir():
            if path.is_file():
                self.assertEqual(path.read_bytes(), (second / path.name).read_bytes())
        version = release.config(self.root)['version']
        skill_zip = first / f'book-to-mentor-{version}.zip'
        with zipfile.ZipFile(skill_zip) as stream:
            self.assertEqual(set(stream.namelist()), {f'book-to-mentor/{p.relative_to(release.SKILL)}'
                                                    for p in release.skill_files()})
            stream.extractall(self.parent / 'installed')
        installed = self.parent / 'installed/book-to-mentor'
        shutil.rmtree(self.root)  # Isolated synthetic fixture, not the user's repository.
        mentor = self.parent / 'new-mentor'
        result = subprocess.run([sys.executable, '-S', str(installed / 'scripts/mentor_state.py'),
                                 'init', str(mentor), '--language', 'en'],
                                cwd=self.parent, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('# Learning record', (mentor / 'learnings.md').read_text())
        source = self.parent / 'source.txt'
        source.write_text('Public domain synthetic fixture.\n')
        extracted = subprocess.run([sys.executable, '-S', str(installed / 'scripts/extract.py'),
                                    str(source), '--workdir', str(self.parent / 'extracted')],
                                   cwd=self.parent, capture_output=True, text=True, timeout=20)
        self.assertEqual(extracted.returncode, 0, extracted.stderr)
        for line in (first / 'SHA256SUMS').read_text().splitlines():
            digest, name = line.split('  ', 1)
            self.assertEqual(digest, hashlib.sha256((first / name).read_bytes()).hexdigest())

    def test_receipts_distinguish_pending_and_real_publication(self):
        for status in ('published', 'pending-publication', 'submitted'):
            self.assertEqual(publisher.validate_receipt({'status': status, 'version': '1.1.0'},
                                                       '1.1.0', False)['status'], status)
        for receipt in ({'status': 'failed', 'version': '1.1.0'},
                        {'status': 'published', 'version': '1.0.0'}):
            with self.assertRaises(ValueError):
                publisher.validate_receipt(receipt, '1.1.0', False)
        with self.assertRaises(ValueError):
            publisher.validate_receipt({'status': 'would-publish', 'version': '1.1.0'}, '1.1.0', False)

    def test_publishing_rejects_tampered_assets_and_wrong_commits(self):
        with patch.object(release.subprocess, 'check_output', return_value='a' * 40):
            output = release.build(self.root, self.parent / 'output')
            release.verify_payload(self.root, output)
            (output / 'release-notes.md').write_text('altered notes')
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                release.verify_payload(self.root, output)
        with patch.object(release.subprocess, 'check_output', return_value='b' * 40):
            with self.assertRaisesRegex(ValueError, 'source commit mismatch'):
                release.verify_payload(self.root, output)

    def test_publishing_rejects_extra_asset_before_any_upload(self):
        with patch.object(release.subprocess, 'check_output', return_value='a' * 40):
            output = release.build(self.root, self.parent / 'output')
            (output / 'secret.txt').write_text('synthetic private value')
            with self.assertRaisesRegex(ValueError, 'asset file set'):
                release.verify_payload(self.root, output)


if __name__ == '__main__':
    unittest.main()
