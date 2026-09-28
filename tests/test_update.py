import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from urllib.error import HTTPError, URLError

spec = importlib.util.spec_from_file_location('check_update', Path(__file__).resolve().parents[1] / 'scripts/check_update.py')
update = importlib.util.module_from_spec(spec)
spec.loader.exec_module(update)


class UpdateTests(unittest.TestCase):
    def release(self, tag):
        return {'tag_name': tag, 'draft': False, 'prerelease': False, 'body': 'Release notes'}

    def test_numeric_comparison_and_no_downgrade(self):
        for current, remote, status in [('1.9.0', 'v1.10.0', 'update_available'),
                                        ('1.1.0', 'v1.1.0', 'up_to_date'),
                                        ('2.0.0', 'v1.1.0', 'ahead_of_release')]:
            self.assertEqual(update.compare_release(current, self.release(remote))['status'], status)

    def test_reject_nonstable_or_invalid_metadata(self):
        for payload in [self.release('v1.2.0-beta'), self.release('../../bad'),
                        {**self.release('v1.2.0'), 'draft': True},
                        {**self.release('v1.2.0'), 'prerelease': True}, {}]:
            with self.assertRaises(ValueError):
                update.compare_release('1.1.0', payload)

    def test_check_uses_bundled_version_and_bounded_public_request(self):
        with tempfile.TemporaryDirectory() as folder:
            metadata = Path(folder) / 'release.json'
            metadata.write_text('{"version": "1.0.0"}')
            def opener(request, timeout):
                self.assertEqual(timeout, 10)
                self.assertEqual(request.full_url, update.API)
                self.assertFalse(request.has_header('Authorization'))
                return io.StringIO(json.dumps(self.release('v1.1.0')))
            self.assertEqual(update.check(folder, opener)['status'], 'update_available')
            self.assertEqual(metadata.read_text(), '{"version": "1.0.0"}')

    def test_failures_are_unknown_not_current(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(update.check(folder)['status'], 'check_unavailable')
            (Path(folder) / 'release.json').write_text('{"version": "1.0.0"}')
            for error in [URLError('offline'), TimeoutError(), HTTPError(update.API, 403, 'limit', {}, None),
                          HTTPError(update.API, 404, 'missing', {}, None)]:
                def opener(*args, **kwargs):
                    raise error
                self.assertEqual(update.check(folder, opener)['status'], 'check_unavailable')
            self.assertEqual(update.check(folder, lambda *a, **kw: io.StringIO('bad json'))['status'], 'check_unavailable')
