import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/mentor_state.py'
spec = importlib.util.spec_from_file_location('mentor_state', SCRIPT)
state = importlib.util.module_from_spec(spec)
spec.loader.exec_module(state)


class StateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        state.initialize(self.root)

    def event(self, **overrides):
        event = dict(event_id='s1-q1', session_id='s1', timestamp='2026-09-18T09:00:00+08:00',
                     concept='反例', chapter='chapters/ch02.md', evidence_level='hinted',
                     outcome='correct', simulation=True, note='Test observation')
        event.update(overrides)
        return event

    def test_init_preserves_existing_state_and_notes(self):
        state.record(self.root, self.event())
        files = [self.root / 'state/state.json', self.root / 'learnings.md']
        before = [p.read_bytes() for p in files]
        self.assertEqual(state.initialize(self.root)['status'], 'existing')
        self.assertEqual(before, [p.read_bytes() for p in files])

    def test_idempotent_retry_and_conflicting_id(self):
        event = self.event()
        state.record(self.root, event)
        self.assertEqual(state.record(self.root, event)['status'], 'already_recorded')
        self.assertEqual(len(state.load_state(self.root)['observations']), 1)
        with self.assertRaisesRegex(ValueError, 'conflict'):
            state.record(self.root, self.event(note='Changed answer'))

    def test_simulation_never_counts_as_real(self):
        state.record(self.root, self.event(evidence_level='independent'))
        current = state.load_state(self.root)
        self.assertEqual(state.summarize(current), [])
        self.assertEqual(state.summarize(current, True)[0]['status'], 'independent')

    def test_wrong_answer_clears_current_mastery(self):
        state.record(self.root, self.event(evidence_level='independent', simulation=False))
        state.record(self.root, self.event(event_id='s2-q1', timestamp='2026-09-19T10:00:00+08:00',
                                          outcome='incorrect', simulation=False))
        self.assertEqual(state.summarize(state.load_state(self.root))[0]['status'], 'needs_review')

    def test_delayed_requires_independent_24_hours_earlier(self):
        state.record(self.root, self.event(evidence_level='independent'))
        with self.assertRaisesRegex(ValueError, '24 hours'):
            state.record(self.root, self.event(event_id='s2-q1', evidence_level='delayed',
                                              timestamp='2026-09-19T08:59:00+08:00'))
        state.record(self.root, self.event(event_id='s2-q1', evidence_level='delayed',
                                          timestamp='2026-09-19T09:00:00+08:00'))
        self.assertEqual(state.summarize(state.load_state(self.root), True)[0]['status'], 'delayed')

    def test_hinted_and_simulation_cannot_qualify_real_delayed(self):
        state.record(self.root, self.event())
        with self.assertRaises(ValueError):
            state.record(self.root, self.event(event_id='later', evidence_level='delayed',
                                              timestamp='2026-09-20T09:00:00+08:00'))
        state.record(self.root, self.event(event_id='independent', evidence_level='independent'))
        with self.assertRaises(ValueError):
            state.record(self.root, self.event(event_id='later', evidence_level='delayed', simulation=False,
                                              timestamp='2026-09-20T09:00:00+08:00'))

    def test_bad_event_leaves_state_unchanged(self):
        before = (self.root / 'state/state.json').read_bytes()
        for overrides in [dict(timestamp='2026-09-18T09:00:00'), dict(simulation='false'),
                          dict(evidence_level='mastered'), dict(outcome='not_assessed')]:
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                state.record(self.root, self.event(**overrides))
            self.assertEqual((self.root / 'state/state.json').read_bytes(), before)

    def test_locked_state_refuses_write(self):
        (self.root / 'state/.write-lock').mkdir()
        with self.assertRaisesRegex(ValueError, 'locked'):
            state.record(self.root, self.event())
        self.assertEqual(state.load_state(self.root)['observations'], [])

    def test_retry_recovers_derived_write_interruption(self):
        real_write = state.atomic_write
        def interrupted(path, text):
            if path.name == 'learnings.md':
                raise OSError('simulated interruption')
            return real_write(path, text)
        with patch.object(state, 'atomic_write', side_effect=interrupted):
            with self.assertRaises(OSError):
                state.record(self.root, self.event())
        state.record(self.root, self.event())
        self.assertEqual(len(state.load_state(self.root)['observations']), 1)
        self.assertIn('s1-q1', (self.root / 'learnings.md').read_text())

    def test_corrupt_state_is_not_replaced(self):
        path = self.root / 'state/state.json'
        path.write_text('{broken')
        with self.assertRaises(ValueError):
            state.initialize(self.root)
        self.assertEqual(path.read_text(), '{broken')

    def test_existing_legacy_learnings_not_destroyed(self):
        (self.root / 'state/state.json').unlink()
        (self.root / 'learnings.md').write_text('legacy learner')
        with self.assertRaisesRegex(ValueError, 'migrate'):
            state.initialize(self.root)
        self.assertEqual((self.root / 'learnings.md').read_text(), 'legacy learner')

    def test_separate_process_reads_persisted_observation(self):
        state.record(self.root, self.event())
        result = subprocess.run([sys.executable, str(SCRIPT), 'show', str(self.root)],
                                capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout)['simulation'][0]['event_id'], 's1-q1')

    def test_independent_process_records_then_another_resumes_without_mutating(self):
        event = self.event(simulation=False, evidence_level='independent')
        event_file = self.root / 'event.json'
        event_file.write_text(json.dumps(event), encoding='utf-8')
        recorded = subprocess.run(
            [sys.executable, str(SCRIPT), 'record', str(self.root), '--event', str(event_file)],
            capture_output=True, text=True, check=True, timeout=20)
        self.assertEqual(json.loads(recorded.stdout)['status'], 'recorded')
        files = [self.root / 'state/state.json', self.root / 'learnings.md']
        before = [path.read_bytes() for path in files]
        shown = subprocess.run([sys.executable, str(SCRIPT), 'show', str(self.root)],
                               capture_output=True, text=True, check=True, timeout=20)
        summary = json.loads(shown.stdout)
        self.assertEqual(summary['observations'], 1)
        self.assertEqual(summary['simulation'], [])
        self.assertEqual(summary['real'][0]['status'], 'independent')
        self.assertEqual(summary['real'][0]['event_id'], event['event_id'])
        self.assertEqual(before, [path.read_bytes() for path in files])

    def test_earlier_correct_record_cannot_repromote_after_later_wrong_answer(self):
        state.record(self.root, self.event(event_id='wrong', simulation=False,
                     timestamp='2026-09-19T09:00:00+08:00', outcome='incorrect'))
        state.record(self.root, self.event(event_id='old-correct', simulation=False,
                     timestamp='2026-09-18T09:00:00+08:00', evidence_level='independent'))
        item = state.summarize(state.load_state(self.root))[0]
        self.assertEqual(item['status'], 'needs_review')
        self.assertEqual(item['event_id'], 'wrong')

    def test_simulated_success_cannot_replace_real_needs_review(self):
        state.record(self.root, self.event(event_id='real-wrong', simulation=False, outcome='incorrect'))
        state.record(self.root, self.event(event_id='simulated-right', simulation=True,
                     evidence_level='independent', timestamp='2026-09-20T09:00:00+08:00'))
        current = state.load_state(self.root)
        self.assertEqual(state.summarize(current)[0]['status'], 'needs_review')
        self.assertEqual(state.summarize(current)[0]['event_id'], 'real-wrong')
        self.assertEqual(state.summarize(current, True)[0]['status'], 'independent')

    def test_delayed_requirement_uses_actual_elapsed_time_across_timezones(self):
        state.record(self.root, self.event(evidence_level='independent'))
        # The baseline is September 18 01:00 UTC, regardless of local date labels.
        too_soon = self.event(event_id='early', evidence_level='delayed',
                             timestamp='2026-09-19T00:59:59Z')
        with self.assertRaisesRegex(ValueError, '24 hours'):
            state.record(self.root, too_soon)
        state.record(self.root, self.event(event_id='on-time', evidence_level='delayed',
                     timestamp='2026-09-19T01:00:00Z'))
        self.assertEqual(state.summarize(state.load_state(self.root), True)[0]['status'], 'delayed')

    def test_other_chapter_or_concept_cannot_qualify_delayed_evidence(self):
        state.record(self.root, self.event(evidence_level='independent'))
        for overrides in [{'chapter': 'chapters/ch03.md'}, {'concept': '另一个概念'}]:
            with self.subTest(overrides=overrides), self.assertRaisesRegex(ValueError, '24 hours'):
                state.record(self.root, self.event(event_id='later', evidence_level='delayed',
                             timestamp='2026-09-20T09:00:00+08:00', **overrides))
        self.assertEqual(len(state.load_state(self.root)['observations']), 1)

    def test_failed_authoritative_write_preserves_history_and_releases_lock(self):
        state.record(self.root, self.event())
        files = [self.root / 'state/state.json', self.root / 'learnings.md']
        before = [path.read_bytes() for path in files]
        next_event = self.event(event_id='next', timestamp='2026-09-20T09:00:00+08:00')
        real_write = state.atomic_write
        def interrupted(path, text):
            if path.name == 'state.json':
                raise OSError('simulated disk failure')
            return real_write(path, text)
        with patch.object(state, 'atomic_write', side_effect=interrupted):
            with self.assertRaises(OSError):
                state.record(self.root, next_event)
        self.assertEqual(before, [path.read_bytes() for path in files])
        self.assertFalse((self.root / 'state/.write-lock').exists())
        self.assertEqual(state.record(self.root, next_event)['observations'], 2)

    def test_initialization_retry_repairs_interrupted_derived_file_creation(self):
        root = self.root / 'new-mentor'
        real_write = state.atomic_write
        def interrupted(path, text):
            if path.name == 'learnings.md':
                raise OSError('simulated interruption after state creation')
            return real_write(path, text)
        with patch.object(state, 'atomic_write', side_effect=interrupted):
            with self.assertRaises(OSError):
                state.initialize(root)
        authoritative = (root / 'state/state.json').read_bytes()
        self.assertFalse((root / 'learnings.md').exists())
        state.initialize(root)
        self.assertEqual((root / 'state/state.json').read_bytes(), authoritative)
        self.assertEqual((root / 'learnings.md').read_text(encoding='utf-8'),
                         state.render_learnings(state.load_state(root)))

    def test_symlink_state_is_rejected_without_overwriting_target(self):
        path = self.root / 'state/state.json'
        original = path.read_bytes()
        path.unlink()
        external = self.root / 'external-state.json'
        external.write_bytes(original)
        path.symlink_to(external)
        with self.assertRaises(ValueError):
            state.record(self.root, self.event())
        self.assertEqual(external.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
