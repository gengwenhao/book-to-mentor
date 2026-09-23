# Contributing to Book-to-Mentor

Thanks for helping improve Book-to-Mentor. The most useful contributions are reproducible reports from real books and real learning sessions.

## Before opening an issue

- Remove copyrighted book content, personal notes, API keys, and private file paths.
- Include the host you used, such as Codex, Claude Code, Cursor, or OpenClaw.
- Include your operating system, Python version, input format, and the exact command or request that failed.
- Share the smallest safe sample that reproduces the problem. Do not upload a book unless you have permission to distribute it.

Use the issue form that best matches your report: Bug report, Compatibility report, or Learning feedback.

## Pull requests

Keep changes focused and add or update tests when behavior changes.

```bash
python scripts/release.py sync
python scripts/release.py check
python -S -m unittest discover -s tests -v
python scripts/validate_mentor.py /path/to/generated-mentor
```

Edit runtime scripts/templates/docs at the repository root, then synchronize their generated copies into `skills/book-to-mentor/`. The nested `SKILL.md` itself is canonical. Keep English and Chinese documentation aligned; preserve source locators, state keys, and existing learner history when adding languages. See the [release guide](docs/releasing.md) for the source layout, versioning, and distribution boundaries.

Generated mentors and learner state are not test fixtures by default. Use synthetic or properly licensed samples and clearly mark simulated learning evidence.

By contributing, you agree that your contribution is licensed under the repository's MIT License.
