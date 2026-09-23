# Release guide

[简体中文](releasing.zh-CN.md) · [Channel status](platforms.md)

## One-time setup

Enable GitHub Actions. Add a repository Actions secret named `CLAWHUB_TOKEN`, containing a ClawHub token authorized to publish for `gengwenhao`. Never put it in a tracked file, command argument, release archive, or issue. Rotate/revoke it in ClawHub if compromised. GitHub Release publishing uses the workflow's temporary `GITHUB_TOKEN`; no personal GitHub token is needed in CI.

The ClawHub publishing CLI is pinned in `release.json`. Publishing to ClawHub is subject to its current terms (including its MIT-0 redistribution requirements); the repository itself is MIT. Only publish material you have authority to distribute. The package contains instructions and tools, not anyone's books or learning records.

## Source layout

- `skills/book-to-mentor/SKILL.md` is the canonical skill instruction file.
- Root `scripts/`, `assets/mentor-template*.md`, format guides and state contracts are editable source files.
- `python scripts/release.py sync` copies an explicit allowlist into `skills/book-to-mentor/`. Do not hand-edit those generated copies.
- `release.json` is the version source. `bump` updates it and both plugin manifests together.
- `README.md` is English; `README.zh-CN.md` is its Chinese counterpart. Keep capabilities and limitations aligned.

There is intentionally no root `SKILL.md`: installers should discover the self-contained nested skill, not an incomplete wrapper.

## Prepare the next version

Example for the release after 1.1.0 (choose an unused higher semantic version):

```bash
python scripts/release.py bump 1.1.1
# Add a matching `## 1.1.1` section to CHANGELOG.md; review the changes.
python -m pip install -r requirements-test.txt
python scripts/release.py check
python -m unittest discover -s tests -v
git add <reviewed-files>
git commit -m "Release 1.1.1"
git push origin master
```

After normal source edits without a version bump, use `python scripts/release.py sync` before checking/committing. Both manifests, the bundled resources, and release notes must match before CI can pass.

## Dry run, then publish

Open [Actions → Release](https://github.com/gengwenhao/book-to-mentor/actions/workflows/release.yml) and choose **Run workflow** on `master`. This runs tests and builds a downloadable `release-payload` artifact. It does not create a public release or contact ClawHub. Inspect the ZIPs, checksums, and distribution checklist.

From the exact reviewed commit on `master`:

```bash
git tag v1.1.1
git push origin v1.1.1
```

Tags must match `release.json`; their commit must be an ancestor of `origin/master`. The workflow then:

1. Tests extraction, state, localization, and packaging; checks version/resource/link integrity.
2. Builds the self-contained skill ZIP and the complete plugin ZIP, with `manifest.json`, `SHA256SUMS`, release notes, and a directory follow-up checklist.
3. Creates the GitHub Release and uploads assets without overwriting conflicting files.
4. Submits that exact version's text-only bundle to ClawHub using a temporary private config file. Saves `clawhub-result.json` as a workflow artifact.

QR and banner assets live in the GitHub/plugin distribution; ClawHub receives text files only. Contact information in the skill links back to GitHub. The build allowlist excludes private books, state, secrets, unrelated files, and the full repository history.

## Verify and recover

- Check every workflow job, not just the GitHub Release page. A GitHub success can coexist with a failed ClawHub job.
- `pending-publication` or `submitted` means accepted for processing, **not** approved/public. Inspect the receipt and listing.
- GitHub publishing is safe to rerun: existing assets must match byte-for-byte, or the job stops. It will not silently overwrite a public artifact.
- On a ClawHub error, inspect whether the exact version was already accepted before retrying that job. An ambiguous response is not permission to create another version. The script always sends an explicit version and will not auto-bump on retry.
- If a version is already published and needs content changes, create a new version. Do not move a public tag.
- Missing/expired `CLAWHUB_TOKEN`: repair the repository secret, then rerun the failed job only after checking the version's status. No secrets are needed for manual build-only runs.
- If your local `dist/v<version>` already exists, build into another explicit output directory via `--output`; the builder will not overwrite it.

The workflow does not post to communities, merge PRs, approve directory reviews, or alter installed skills. Follow the generated checklist and [platform tracking](platforms.md). User-local updates and public discovery are separate from release publishing.

References: [GitHub Actions secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions), [ClawHub publishing](https://docs.openclaw.ai/clawhub/cli).
