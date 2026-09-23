<p align="center"><img src="assets/banner.svg" alt="Book to Mentor — Read. Reason. Retain." width="100%"></p>

<p align="center">
  <a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a><br>
  <a href="https://github.com/gengwenhao/book-to-mentor/actions/workflows/tests.yml"><img src="https://github.com/gengwenhao/book-to-mentor/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
  <a href="https://github.com/gengwenhao/book-to-mentor/releases"><img src="https://img.shields.io/github/v/release/gengwenhao/book-to-mentor?color=00bda5" alt="Latest release"></a>
  <a href="https://skills.sh/gengwenhao/book-to-mentor"><img src="https://skills.sh/b/gengwenhao/book-to-mentor" alt="skills.sh"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-62a8ff" alt="MIT license"></a>
</p>

# Your next book can become your next mentor.

Book-to-Mentor turns a book or document into a reusable AI mentor skill: explanations you can trace to the source, practice that adapts to your intent, and a learning record that survives the next conversation.

**Not just a summary. A place to keep learning.**

| Distill | Mentor | Remember |
| --- | --- | --- |
| Map concepts and frameworks to source locations. Load chapters on demand. | Switch between guided practice, direct explanation, and quick lookup. | Separate hinted answers, independent application, and delayed recall. |

You provide the material and learning goal. Your agent organizes the content, builds the mentor, and carries the learning record forward from one conversation to the next.

## Give it a book. Start talking.

Install it once, then give your agent a book or document and say how you want to learn:

```text
Use book-to-mentor to turn the book I just uploaded into my personal mentor.
Start with chapter 1, explain it in English, then give me one application question.
```

Then simply say: “Make that easier”, “Use a real example”, “Quiz me”, or “Resume where we stopped.” The mentor keeps its structure and learning record, so you do not have to re-explain your context every time.

> [!TIP]
> First time here? Pick your platform below. Once installed, come back to this prompt and start. You usually do not need to touch scripts or study dependencies.

## Choose your home

| Channel | What you can use | Update behavior |
| --- | --- | --- |
| [Agent Skills / skills.sh](https://skills.sh/gengwenhao/book-to-mentor) | Self-contained skill from this repository | Reinstall/update through the skills CLI; no silent update of installed copies |
| Codex / ChatGPT plugin host | This repository's custom marketplace | Refresh marketplace and update/reinstall the plugin |
| Claude Code | This repository's plugin marketplace | Marketplace refresh + plugin update; optional host auto-update setting |
| [GitHub Releases](https://github.com/gengwenhao/book-to-mentor/releases) | Versioned skill and plugin ZIPs, checksums | Automatically produced by a release tag |
| [ClawHub / OpenClaw](https://clawhub.ai/gengwenhao/book-to-mentor) | Public registry lists 1.0.0; 1.1.0 submitted for review | Workflow submits each tagged version; installed copies still need updating |
| Third-party directories | Codex community marketplace + two community PRs submitted | Review/PR workflow, **not** automatic synchronization |

Custom marketplace support is not an official OpenAI/Anthropic directory listing. Other Agent Skills hosts may work; their end-to-end compatibility is not certified. [Exact channel status and tracking links →](docs/platforms.md)

<details>
<summary>Agent Skills / skills.sh (universal install)</summary>

```bash
npx skills add gengwenhao/book-to-mentor --skill book-to-mentor
```

This installs the complete skill into a supported agent. After the one-time setup, everyday use is just a conversation about your book and learning goal.

</details>

<details>
<summary>Codex / ChatGPT custom marketplace</summary>

```bash
codex plugin marketplace add gengwenhao/book-to-mentor
```

Select `Geng Wenhao Skills` in your host's plugin directory and install **Book to Mentor**. Where the CLI supports plugin installation:

```bash
codex plugin add book-to-mentor@gengwenhao-skills
```

Start a new task after installation or updates. Available plugin UI and CLI commands depend on the host version.

</details>

<details>
<summary>Claude Code marketplace</summary>

```bash
claude plugin marketplace add gengwenhao/book-to-mentor
claude plugin install book-to-mentor@gengwenhao-skills
```

The plugin uses the same self-contained skill as the other channels.

</details>

<details>
<summary>ClawHub / OpenClaw</summary>

```bash
openclaw skills install @gengwenhao/book-to-mentor
```

The public registry currently lists 1.0.0; the submitted 1.1.0 is awaiting approval. Use the GitHub/skills CLI route for the new multilingual package now. Successful upload does not imply approval.

</details>

<details>
<summary>Manual / offline installation</summary>

Download `book-to-mentor-<version>.zip` from a GitHub Release, extract it, and copy the resulting `book-to-mentor/` into your host's actual skills directory. Or clone the repository and copy **`skills/book-to-mentor/`**, including its support files. Do not copy only `SKILL.md`.

</details>

<details>
<summary>Environment and file support (only if a document will not open)</summary>

The skill's local tools use Python 3.10+. Many developer-focused agent environments already provide it, so there is no need to understand or configure these components up front. If the current environment is missing something, the agent should tell you exactly what it needs.

- Text, Markdown, HTML, EPUB, and DOCX use the Python standard library.
- PDF needs `pypdf` or `pdfminer.six`; scanned PDFs also need OCR.
- RTF needs `striprtf`.
- Formula- or table-heavy technical PDFs can optionally use `docling`; otherwise the workflow discloses the downgrade.

[Full format support, setup, and limitations →](docs/formats.md)

</details>

## What you keep

```text
your-book-mentor/
├── SKILL.md                  # Teaching instructions + chapter routing
├── sources.md                # Source inventory, coverage, extraction gaps
├── chapters/                 # Source locators + practice questions
│   └── index.md
├── glossary.md · patterns.md · cheatsheet.md
├── scripts/mentor_state.py   # Travels with the mentor
├── references/state-schema.md
├── state/state.json          # Authoritative observations
└── learnings.md              # Human-readable learning summary
```

Portable files, not a hosted knowledge silo. State initialization never overwrites history; repeated event IDs prevent duplicate observations. Simulated results never count as real learning evidence. [Learning-record contract →](docs/state-schema.en.md)

## Built for more than one language

- English and 简体中文 READMEs, mentor templates, format guides, and state contracts.
- Teaching follows the learner's requested language, not the book's language. Preserve original terms and source locators when translating explanations.
- New learning summaries support `--language en` and `--language zh-CN`; legacy records retain their language and history.
- Structural checks accept English/Chinese headings. Other teaching languages can use stable section markers; JSON keys and paths stay language-independent.

Some extractor diagnostics and the detailed design blueprint remain Chinese. Additional languages are welcome; we do not claim full localization for every host or CLI message.

## Release once, distribute deliberately

```text
Version tag → tests + package checks → GitHub Release → ClawHub submission
                                   ↘ directory / review checklist
```

The workflow checks version consistency, bundled files, local links, and regression tests. It builds separate skill/plugin packages with checksums and a recorded source commit. Manual workflow runs build artifacts without publishing.

**Pushing code alone does not release a new ClawHub version, approve a directory submission, or update people's installed skills.** [Release guide →](docs/releasing.md)

## Trust, limits, and feedback

Source material is data, not instructions. Scanned PDFs need separate OCR; DRM and MOBI/AZW are unsupported. Partial extraction must be disclosed. Token counts are heuristic estimates, not billing counts. Structural tests cannot prove source fidelity or teaching effectiveness.

This project does not send books or learning records to its author. Your agent/model provider and installation tools have their own data policies. Only use materials you have permission to process. [Privacy](PRIVACY.md) · [Terms](TERMS.md) · [Contributing](CONTRIBUTING.md) · [Design notes (中文)](docs/blueprint.md)

Help shape the next version: what did you read, which agent did you use, where did the mentor help or get stuck, and did you return a week later?

[Report a bug](https://github.com/gengwenhao/book-to-mentor/issues/new?template=bug.yml) · [Host compatibility](https://github.com/gengwenhao/book-to-mentor/issues/new?template=compatibility.yml) · [Learning feedback](https://github.com/gengwenhao/book-to-mentor/issues/new?template=learning-feedback.yml)

Do not upload copyrighted book text, private notes, keys, or personal file paths in public issues.

### Made by Geng Wenhao

[GitHub @gengwenhao](https://github.com/gengwenhao) · RedNote / 小红书 **宇宙机吴彦祖** · ID **292844431**

Share your setup, a learning story, or an idea for the next version. Contact is optional and never a prerequisite for using the skill.

<details>
<summary>Scan to find me on RedNote / 小红书</summary>

<p><img src="assets/xiaohongshu-qr.jpg" alt="RedNote QR code for 宇宙机吴彦祖, ID 292844431" width="260"></p>

</details>

### Acknowledgments

Inspired by [book-to-skill](https://github.com/virgiliojr94/book-to-skill), [mentoring-juniors](https://github.com/github/awesome-copilot), [socratic-method](https://gist.github.com/RalucaNicola/af42f35b54f96252fd0ab5e0920fbd24), [Bloom](https://github.com/Li-Evan/Bloom), and [self-evolve-agent](https://hub.openclaw.ai/mikonos/self-evolve-agent). Inspiration does not imply reproduction of their implementation or results.

[MIT License](LICENSE)
