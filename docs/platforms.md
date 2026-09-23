# Distribution status / 分发状态

Recorded 2026-09-23. Status is a snapshot, not a guarantee of approval or availability. / 状态记录于 2026-09-23，不代表平台必然批准或持续可用。

| Channel / 渠道 | Status / 状态 | How updates reach it / 更新路径 |
| --- | --- | --- |
| [GitHub](https://github.com/gengwenhao/book-to-mentor) | Public source and releases / 公开源码与版本 | Push updates source; `v*` tag triggers versioned release / 推送更新源码，版本标签触发发布 |
| [skills.sh](https://skills.sh/gengwenhao/book-to-mentor) | GitHub-backed discovery and install / 基于 GitHub 的发现与安装 | CLI installs from source; indexing timing is external / CLI 从源码安装，索引时间由平台决定 |
| Codex / ChatGPT custom marketplace | Repository manifest provided / 提供仓库自建市场清单 | Refresh marketplace + update/reinstall plugin / 刷新市场并更新或重装插件 |
| Claude Code custom marketplace | Repository manifest provided / 提供仓库自建市场清单 | Refresh marketplace + plugin update, optional host auto-update / 刷新市场并更新，可选宿主自动更新 |
| [ClawHub](https://clawhub.ai/gengwenhao/book-to-mentor) | Public registry lists 1.0.0; 1.1.0 receipt pending-publication / 公开目录已显示 1.0.0；1.1.0 已受理，待发布审核 | Tag workflow submits exact new version; moderation remains external / 标签工作流提交新版本，审核不受本仓库控制 |
| [Codex community marketplace](https://www.codex-marketplace.com/) | Submitted; under review / 已提交，审核中 | Review or resubmission when needed; no assumed webhook / 视审核要求更新或重提，无自动同步保证 |
| [Agent Skill Exchange PR #76](https://github.com/agentskillexchange/skills/pull/76) | Submitted PR, not an approved listing / 已提 PR，不等于已收录 | Maintainer merge; copied content needs another PR / 维护者合并，内容副本需后续 PR |
| [Awesome Agent Skills PR #17](https://github.com/skillcreatorai/Awesome-Agent-Skills/pull/17) | Submitted PR, not an approved listing / 已提 PR，不等于已收录 | Maintainer merge; links follow source but copied prose can go stale / 维护者合并，链接指向源码但介绍副本不会自动更新 |

Codex community submission tracking ID: `53C3B8AF-8F12-44B2-BB37-DB54BED9DA05`. It is a third-party directory, not the official OpenAI directory. / 此为第三方社区市场，并非 OpenAI 官方目录。

No public listing is claimed for channels that have not accepted a submission. / 未实际受理的渠道不标记为已上架。

The unauthenticated [ClawHub registry response](https://clawhub.ai/api/v1/skills/book-to-mentor) returned HTTP 200 with `latestVersion.version: 1.0.0` on 2026-09-23. This is a public-registry check, not an end-to-end OpenClaw host test. / 2026-09-23 无需登录的注册表接口已返回 1.0.0；这证明公开目录可读，不等于完成了 OpenClaw 宿主端到端测试。

## Verified release / 已验证的发布

The [1.1.0 workflow](https://github.com/gengwenhao/book-to-mentor/actions/runs/35869398869) completed all three jobs: build, GitHub, and ClawHub. The [GitHub Release](https://github.com/gengwenhao/book-to-mentor/releases/tag/v1.1.0) contains both install ZIPs and checksums. All 86 regression tests passed with optional format parsers installed. The ClawHub receipt reports version `1.1.0`, status `pending-publication`, and 11 text files; it is saved as the workflow's `clawhub-receipt` artifact. / 1.1.0 的构建、GitHub 发布和 ClawHub 提交三个任务全部成功；86 项回归测试通过。ClawHub 回执为待发布审核，不能据此声称已公开可安装。

## Installed copies are separate / 已安装副本是另一层

- Agent Skills: use the skills CLI's update/reinstall flow. Review local edits first. / 使用 skills CLI 更新或重装前，先检查本地改动。
- Codex: refresh using `codex plugin marketplace upgrade gengwenhao-skills`, then update/reinstall in the host and start a new task. / 刷新市场后在宿主更新或重装，并开启新任务。
- Claude Code: refresh with `claude plugin marketplace update gengwenhao-skills`, then `claude plugin update book-to-mentor@gengwenhao-skills`. Automatic updates depend on the user's marketplace settings. / 自动更新取决于用户配置。
- OpenClaw: once approved, install with `openclaw skills install @gengwenhao/book-to-mentor`; `openclaw skills update --all` updates installed skills (not just this one). / 审核通过后可安装，`--all` 会更新所有已安装技能。
- Generated book mentors are user-owned artifacts. Updating this converter does not rewrite their teaching rules or learning history. / 更新转换器不应自动改写已生成导师的教学规则与学习记录。

## Official references / 官方参考

[Agent Skills CLI](https://www.skills.sh/docs/cli) · [Codex plugin packaging](https://developers.openai.com/plugins/build/plugins) · [Claude Code marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) · [ClawHub quickstart](https://docs.openclaw.ai/clawhub/quickstart)

See [English release guide](releasing.md) / [中文发布指南](releasing.zh-CN.md) for what the workflow actually automates.
