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
python -S -m unittest discover -s tests -v
python scripts/validate_mentor.py /path/to/generated-mentor
```

Generated mentors and learner state are not test fixtures by default. Use synthetic or properly licensed samples and clearly mark simulated learning evidence.

By contributing, you agree that your contribution is licensed under the repository's MIT License.
