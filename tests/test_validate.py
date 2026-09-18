"""Validate real mentor-directory fixtures, including deliberately broken variants."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
STATE_SPEC = importlib.util.spec_from_file_location('validator_test_state', SCRIPTS / 'mentor_state.py')
STATE = importlib.util.module_from_spec(STATE_SPEC)
STATE_SPEC.loader.exec_module(STATE)
SPEC = importlib.util.spec_from_file_location('mentor_validator', SCRIPTS / 'validate_mentor.py')
validator = importlib.util.module_from_spec(SPEC)
with patch.dict(sys.modules, {'mentor_state': STATE}):
    SPEC.loader.exec_module(validator)


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='mentor-validator-')
        self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name)
        self.root = self.parent / 'mentor'
        self.root.mkdir()
        files = {
            'SKILL.md': '---\nname: evidence-mentor\ndescription: Teach evidence-based reasoning.\n---\n'
                        '# Evidence mentor\n\nRead [chapters](chapters/index.md).\n',
            'sources.md': '# Sources\n\nFixture notes, first edition, Chapter 1, lines 1–8.\n',
            'chapters/index.md': '# Chapters\n\n[Evidence](ch01-evidence.md)\n',
            'chapters/ch01-evidence.md': '# Evidence\n\n## 来源\n'
                                       'Fixture notes, Chapter 1, lines 1–8.\n\n'
                                       '## 核心概念\nCheck whether the evidence supports the claim.\n\n'
                                       '## 关键问题\n1. What evidence would change this claim?\n',
            'glossary.md': '# Glossary\n\nEvidence: an observation relevant to a claim.\n',
            'patterns.md': '# Patterns\n\nCollect observations before drawing conclusions.\n',
            'cheatsheet.md': '# Quick reference\n\nSeparate observations from assumptions.\n',
            'scripts/mentor_state.py': (SCRIPTS / 'mentor_state.py').read_text(encoding='utf-8'),
            'references/state-schema.md': '# State schema\n\nSchema version 1; observations is a list.\n',
        }
        for name, content in files.items():
            self.write(name, content)
        STATE.initialize(self.root)

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        return path

    def assert_rejected(self, error_fragment):
        result = validator.validate(self.root)
        self.assertFalse(result['passed'], result)
        self.assertTrue(any(error_fragment in error for error in result['errors']), result)
        return result

    def test_complete_fixture_passes_without_claiming_source_or_teaching_quality(self):
        result = validator.validate(self.root)
        self.assertTrue(result['passed'], result)
        self.assertEqual(result['chapters'], 1)
        self.assertEqual(result['errors'], [])
        self.assertIn('source fidelity', result['scope'])
        self.assertIn('separate evaluation', result['scope'])

    def test_missing_source_inventory_is_rejected_even_without_a_link_to_it(self):
        (self.root / 'sources.md').unlink()
        self.assert_rejected('sources.md')

    def test_missing_chapter_source_locator_is_rejected(self):
        self.write('chapters/ch01-evidence.md', '# Evidence\n\n## 关键问题\n1. What supports the claim?\n')
        self.assert_rejected('missing source locator')

    def test_blank_source_section_does_not_borrow_text_from_next_heading(self):
        self.write('chapters/ch01-evidence.md', '# Evidence\n\n## 来源\n\n'
                   '## 核心概念\nThis is a summary, not a source locator.\n\n'
                   '## 关键问题\n1. What supports the claim?\n')
        self.assert_rejected('missing source locator')

    def test_missing_practice_or_question_is_rejected(self):
        self.write('chapters/ch01-evidence.md', '# Evidence\n\n## 来源\nFixture, Chapter 1.\n')
        self.assert_rejected('missing question')

    def test_broken_relative_link_is_rejected(self):
        self.write('chapters/index.md', '# Index\n\n[Missing](ch99-absent.md)\n')
        self.assert_rejected('broken link')

    def test_encoded_relative_link_and_fragment_resolve_inside_mentor(self):
        self.write('notes with spaces.md', '# Evidence\n\nGrounded note.\n')
        self.write('patterns.md', '# Patterns\n\n[Note](notes%20with%20spaces.md#evidence)\n')
        self.assertTrue(validator.validate(self.root)['passed'])

    def test_template_placeholder_in_body_is_rejected(self):
        self.write('patterns.md', '# Patterns\n\n{框架1}\n')
        self.assert_rejected('unfilled scaffold')

    def test_current_template_long_instruction_placeholder_is_rejected(self):
        self.write('patterns.md', '# Patterns\n\n'
                   '{按实际材料列出核心概念或作者框架、定义、适用条件与来源定位。数量不限；不存在明确框架时保留主题，不补造固定数量。}\n')
        self.assert_rejected('unfilled scaffold')

    def test_parent_traversal_link_is_rejected_even_when_file_exists(self):
        (self.parent / 'outside.md').write_text('Private outside note.', encoding='utf-8')
        self.write('patterns.md', '# Patterns\n\n[Outside](../outside.md)\n')
        self.assert_rejected('link escapes mentor')

    def test_percent_encoded_parent_traversal_is_rejected(self):
        (self.parent / 'outside.md').write_text('Private outside note.', encoding='utf-8')
        self.write('patterns.md', '# Patterns\n\n[Outside](%2e%2e/outside.md)\n')
        self.assert_rejected('link escapes mentor')

    def test_required_file_symlink_outside_mentor_is_rejected(self):
        target = self.parent / 'outside.md'
        target.write_text('Outside glossary.', encoding='utf-8')
        path = self.root / 'glossary.md'
        path.unlink()
        path.symlink_to(target)
        self.assert_rejected('escapes mentor')
        self.assertEqual(target.read_text(encoding='utf-8'), 'Outside glossary.')

    def test_corrupt_learning_state_is_rejected(self):
        self.write('state/state.json', '{invalid json')
        self.assert_rejected('invalid learning state')

    def test_invalid_frontmatter_name_is_rejected(self):
        self.write('SKILL.md', '---\nname: invalid Name!\ndescription: Valid description.\n---\n# Mentor\n')
        self.assert_rejected('invalid or empty name')

    def test_invalid_yaml_description_cannot_pass_as_a_plain_scalar(self):
        self.write('SKILL.md', '---\nname: evidence-mentor\ndescription: [unterminated\n---\n# Mentor\n')
        result = validator.validate(self.root)
        self.assertFalse(result['passed'], result)
        self.assertTrue(any('description' in error or 'YAML' in error for error in result['errors']), result)

    def test_cli_returns_structured_failure_and_nonzero_exit(self):
        (self.root / 'chapters/ch01-evidence.md').unlink()
        result = subprocess.run([sys.executable, str(SCRIPTS / 'validate_mentor.py'), str(self.root)],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        diagnostic = json.loads(result.stdout)
        self.assertFalse(diagnostic['passed'])
        self.assertIn('no chapter files', diagnostic['errors'])


if __name__ == '__main__':
    unittest.main()
