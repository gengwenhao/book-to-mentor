<p align="center"><img src="assets/banner.svg" alt="Book to Mentor — 把书籍变成可持续学习的 AI 导师" width="100%"></p>

<p align="center">
  <a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a><br>
  <a href="https://github.com/gengwenhao/book-to-mentor/actions/workflows/tests.yml"><img src="https://github.com/gengwenhao/book-to-mentor/actions/workflows/tests.yml/badge.svg" alt="回归测试"></a>
  <a href="https://github.com/gengwenhao/book-to-mentor/releases"><img src="https://img.shields.io/github/v/release/gengwenhao/book-to-mentor?color=00bda5" alt="最新版本"></a>
  <a href="https://skills.sh/gengwenhao/book-to-mentor"><img src="https://skills.sh/b/gengwenhao/book-to-mentor" alt="skills.sh"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-62a8ff" alt="MIT 开源协议"></a>
</p>

# 让下一本书，成为你的下一位导师。

Book-to-Mentor 把书籍或文档转成可反复使用的 AI 导师 Skill：讲解有出处，练习跟随你的意图，学习记录跨对话保留。

**不止读出一份摘要，而是拥有一个可以继续学习的地方。**

| 蒸馏 Distill | 教学 Mentor | 记录 Remember |
| --- | --- | --- |
| 提炼概念与框架，标注来源位置，按需加载章节。 | 自由切换引导练习、直接讲解和快速查阅。 | 区分提示后答对、独立应用和延迟回忆。 |

你只需要提供材料和学习目标；Agent 会完成内容整理、导师生成和学习记录，让一次转换可以变成持续的对话。

## 给它一本书，接着开口学

安装一次后，把书籍或文档交给 Agent，告诉它你想怎么学：

```text
用 book-to-mentor 把我刚上传的这本书变成我的专属导师。
先从第一章开始，用中文讲解；讲完后问我一道应用题。
```

之后可以直接说：“讲简单一点”“换个真实案例”“考考我”“接着上次继续学”。导师会保留内容结构和学习记录，不需要每次重新解释背景。

> [!TIP]
> 第一次使用？在下面选择你正在使用的平台，安装完成后就可以回到这句话开始。通常不需要手动操作脚本或研究依赖。

## 选择你的使用平台

| 渠道 | 当前支持 | 更新方式 |
| --- | --- | --- |
| [Agent Skills / skills.sh](https://skills.sh/gengwenhao/book-to-mentor) | 从本仓库安装自包含 Skill | 通过 skills CLI 更新或重新安装，不会静默覆盖用户副本 |
| Codex / ChatGPT 插件宿主 | 本仓库的自建 marketplace | 刷新市场，再更新或重装插件 |
| Claude Code | 本仓库的插件 marketplace | 刷新市场并更新插件；可在宿主中选择自动更新 |
| [GitHub Releases](https://github.com/gengwenhao/book-to-mentor/releases) | 带版本的 Skill、插件 ZIP 和校验和 | 发布标签自动生成 |
| [ClawHub / OpenClaw](https://clawhub.ai/gengwenhao/book-to-mentor) | 公开目录已显示 1.0.0；1.1.0 已提交审核 | 工作流自动提交标签版本，用户仍需更新本地安装 |
| 第三方目录 | Codex 社区市场及两个社区 PR 已提交 | 人工审核或 PR，**不承诺自动同步** |

自建市场支持不等于进入 OpenAI / Anthropic 官方公共目录。其他 Agent Skills 宿主可能可用，但尚未逐一完成端到端验证。[渠道状态与跟进链接 →](docs/platforms.md)

### 安装完成后，全平台都这样用

无论通过哪个平台安装，都可以把下面这段话和书籍或文档一起交给 Agent：

```text
请使用 book-to-mentor，把我刚提供的材料变成一个可以长期使用的专属导师。
用中文教学，先整理内容结构和来源位置，再从第一章开始讲解。
每次只推进一个小主题：先解释，再用真实案例帮助我理解，最后问我一道应用题。
请保存我的学习进度，之后我说“继续学习”时，从上次停下的位置继续。
```

<details>
<summary>继续学习、追加材料和读取失败时的提示词</summary>

**继续学习**

```text
请使用这个导师继续上次的学习。先简短回顾我的进度，再开始下一个主题。
```

**追加材料**

```text
请把我刚提供的新材料加入现有导师，保留原有教学规则和学习记录，并告诉我新增或更新了哪些内容。
```

**文件读取失败**

```text
请检查这份材料为什么无法读取，告诉我缺少的格式支持或依赖，并给出当前环境下最简单的解决办法；不要静默跳过内容。
```

</details>

<details>
<summary>Agent Skills / skills.sh（通用安装）</summary>

```bash
npx skills add gengwenhao/book-to-mentor --skill book-to-mentor
```

这条命令会把完整 Skill 安装到支持的 Agent。安装一次后，日常使用只需要用自然语言说出书籍和学习目标。

</details>

<details>
<summary>Codex / ChatGPT 自建插件市场</summary>

```bash
codex plugin marketplace add gengwenhao/book-to-mentor
```

在宿主插件目录里选择 `Geng Wenhao Skills`，安装 **Book to Mentor**。支持命令行安装的版本也可运行：

```bash
codex plugin add book-to-mentor@gengwenhao-skills
```

安装或更新后开启新任务测试。插件界面及可用命令以实际宿主版本为准。

</details>

<details>
<summary>Claude Code 插件市场</summary>

```bash
claude plugin marketplace add gengwenhao/book-to-mentor
claude plugin install book-to-mentor@gengwenhao-skills
```

与其他渠道使用同一份自包含 Skill。

</details>

<details>
<summary>ClawHub / OpenClaw</summary>

```bash
openclaw skills install @gengwenhao/book-to-mentor
```

公开目录当前显示 1.0.0，新提交的 1.1.0 尚待批准。如需立即使用新版多语言包，请走 GitHub / skills CLI 渠道。上传成功不等于审核通过。

</details>

<details>
<summary>手动 / 离线安装</summary>

从 GitHub Release 下载 `book-to-mentor-<version>.zip`，解压后将 `book-to-mentor/` 放进宿主实际配置的技能目录。也可以克隆仓库，只复制 **`skills/book-to-mentor/` 完整目录**。不要只复制 `SKILL.md`，它需要随附脚本与模板。

</details>

<details>
<summary>环境与格式支持（遇到文件读取问题时再看）</summary>

Skill 的本地工具使用 Python 3.10+。不少开发型 Agent 环境已经具备，正常使用时无需先理解或手动配置下面这些组件；如果当前环境缺少某项能力，Agent 应明确告诉你缺什么。

- 文本、Markdown、HTML、EPUB、DOCX：使用 Python 标准库。
- PDF：需要 `pypdf` 或 `pdfminer.six`；扫描版 PDF 还需要 OCR。
- RTF：需要 `striprtf`。
- 公式、表格较多的技术型 PDF：可选 `docling`，否则会明确提示降级。

[查看完整的格式、依赖和限制 →](docs/formats.zh-CN.md)

</details>

## 你会得到什么

```text
your-book-mentor/
├── SKILL.md                  # 教学指令与章节路由
├── sources.md                # 来源清单、覆盖范围和提取缺口
├── chapters/                 # 来源定位与练习问题
│   └── index.md
├── glossary.md · patterns.md · cheatsheet.md
├── scripts/mentor_state.py   # 随导师一起移动
├── references/state-schema.md
├── state/state.json          # 权威观察记录
└── learnings.md              # 可读的学习摘要
```

文件可迁移，不依赖作者托管服务。初始化不覆盖历史；唯一事件 ID 防止重复记录；模拟结果不计入真人学习证据。[学习记录契约 →](docs/state-schema.md)

## 不只是翻译 README

- README、导师模板、格式指南、状态契约提供 English / 简体中文。
- 教学跟随学习者指定语言，不被书籍语言绑定；翻译讲解时保留原始术语与来源定位。
- 新学习摘要可选 `--language en` 或 `--language zh-CN`；旧记录的语言与历史不被改写。
- 结构校验支持中英文标题；其他教学语言可用稳定标记，JSON 字段和文件路径保持统一。

部分提取器提示与详细设计蓝图仍为中文。欢迎贡献其他语言；不声称所有宿主及命令行提示已经完整本地化。

## 一次发布，分渠道交付

```text
版本标签 → 测试与打包校验 → GitHub Release → ClawHub 提交
                        ↘ 社区目录 / 审核跟进清单
```

工作流检查版本一致性、随包资源、相对链接和回归测试；生成 Skill / 插件两种包、校验和与来源提交记录。手动启动工作流只构建，不发布。

**仅推送代码，不会产生新的 ClawHub 版本、自动通过目录审核，也不会更新别人已经安装的 Skill。** [发布指南 →](docs/releasing.zh-CN.md)

## 边界、信任与反馈

材料中的内容只作为数据，不作为指令。扫描 PDF 需另行 OCR；不支持 DRM 和 MOBI/AZW；部分提取必须披露范围。Token 数是启发式估算，不是计费结果。结构测试不能证明内容忠实度或教学效果。

本项目不会向作者发送书籍或学习记录；你使用的 Agent、模型提供商和安装工具各有自己的数据政策。请只处理你有权使用的材料。[隐私说明](PRIVACY.md) · [使用条款](TERMS.md) · [参与贡献](CONTRIBUTING.md) · [设计蓝图](docs/blueprint.md)

最想听到你的真实体验：读了什么、用了哪个 Agent、哪一步有帮助或卡住、一周后是否还愿意回来继续学？

[报告问题](https://github.com/gengwenhao/book-to-mentor/issues/new?template=bug.yml) · [兼容性反馈](https://github.com/gengwenhao/book-to-mentor/issues/new?template=compatibility.yml) · [学习体验](https://github.com/gengwenhao/book-to-mentor/issues/new?template=learning-feedback.yml)

请勿在公开反馈中上传无权分发的书籍正文、私人笔记、密钥或个人文件路径。

### 作者 Geng Wenhao

[GitHub @gengwenhao](https://github.com/gengwenhao) · 小红书 **宇宙机吴彦祖** · ID **292844431**

欢迎分享使用案例、学习故事和改进建议。联系作者完全自愿，不是使用 Skill 的前提。

<details>
<summary>扫码在小红书找到我</summary>

<p><img src="assets/xiaohongshu-qr.jpg" alt="宇宙机吴彦祖的小红书二维码，ID 292844431" width="260"></p>

</details>

### 致谢

设计受 [book-to-skill](https://github.com/virgiliojr94/book-to-skill)、[mentoring-juniors](https://github.com/github/awesome-copilot)、[socratic-method](https://gist.github.com/RalucaNicola/af42f35b54f96252fd0ab5e0920fbd24)、[Bloom](https://github.com/Li-Evan/Bloom) 和 [self-evolve-agent](https://hub.openclaw.ai/mikonos/self-evolve-agent) 启发。引用思路不代表复现其实现或实证结果。

[MIT 开源协议](LICENSE)
