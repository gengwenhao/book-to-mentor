# 📚 Book-to-Mentor — 把书籍变成可追溯的 AI 导师

输入书籍或文档，生成一个可继续使用的导师 Skill：按章查内容、讲解或练习、记录学习证据，再据反馈调整教学方式。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![skills.sh](https://skills.sh/b/gengwenhao/book-to-mentor)](https://skills.sh/gengwenhao/book-to-mentor)

## 能做什么

- **Distill 蒸馏**：提炼材料中的概念、框架与使用条件，附来源定位；按需加载章节。
- **Mentor 教学**：引导、讲解、速查三种方式随用户意图切换。每轮少量问题，卡住或疲惫时转为讲解。
- **Evolve 改进**：记录提示后答对、独立迁移、延迟回忆等不同证据，提出可检验的教学改进。没有真人基线时不声称改进有效。

这是供 agent 执行的生成流程，提取脚本不会自行生成导师。项目没有经过真人长期学习效果验证，也不承诺固定节省比例或学习成绩提升。当前实现与设计边界见 [docs/blueprint.md](docs/blueprint.md)。

## 安装与使用

### Agent Skills 通用安装

```bash
npx skills add gengwenhao/book-to-mentor
```

也可以直接克隆仓库，将整个目录放入宿主实际配置的技能目录：

```bash
git clone https://github.com/gengwenhao/book-to-mentor.git
```

也可以让 agent 直接读取本仓库的 `SKILL.md`。不同宿主的发现方式与安装路径需要按其配置确认；复制目录本身不证明安装成功。

### Codex / ChatGPT 插件市场

```bash
codex plugin marketplace add gengwenhao/book-to-mentor
codex plugin add book-to-mentor@gengwenhao-skills
```

安装或更新后请在新任务中测试，以确保宿主重新加载 skill。仓库内的 `.codex-plugin/plugin.json` 是 Codex 兼容清单；核心工作流仍保持为开放的 Agent Skills 格式。

### Claude Code 插件市场

```bash
claude plugin marketplace add gengwenhao/book-to-mentor
claude plugin install book-to-mentor@gengwenhao-skills
```

仓库同时包含 Claude Code 插件与 marketplace 清单，核心 skill 内容与 Codex、skills.sh 安装方式共用同一来源。

对 agent 说：

```text
用 book-to-mentor 把 /path/to/book.pdf 转成导师 skill，先做第一章，输出到当前工作区。
```

已给出的目标、材料类型、位置不重复询问。默认产物在 `mentors/<slug>-mentor/`。生成后可以说“直接讲解这一节”“问我一道应用题”或“查一下这个术语”。向已有导师补充材料时，只更新书籍内容，保留教学规则和学习记录。

## 提取范围与依赖

需要 Python 3.10 或更新版本；标准库即可运行纯文本、HTML、EPUB、DOCX 提取及状态工具。可选提取器由使用环境单独安装：

| 格式 | 实现/依赖 | 限制 |
|---|---|---|
| TXT、MD、Markdown | 标准库 | 默认 UTF-8；支持 BOM 声明的编码，不猜测未知编码 |
| HTML、HTM | 标准库 | 提取可见文本；不是网页截图或完整表格重建 |
| EPUB | 标准库 | 按 OPF spine 阅读顺序；不处理 DRM，不还原插图 |
| DOCX | 标准库 | 提取正文段落与表格；复杂对象、图片等需核对 |
| PDF（text） | `pypdf` 或 `pdfminer.six` | 文字层提取；扫描件需要另行 OCR |
| PDF（technical） | 优先 `docling` | 不可用时降级为文字提取并警告；复杂公式/表格仍需核对 |
| RTF | `striprtf` | 缺依赖明确失败，不用会吞字的正则回退 |

MOBI/AZW 不受当前脚本支持；先用适合该文件的工具转成支持格式。不要把改后缀视为格式转换。

```bash
python scripts/extract.py --check
python -m pip install pypdf striprtf  # 仅在需要对应格式时安装
python -m pip install docling        # 可选：技术 PDF
python scripts/extract.py /path/to/book.pdf --mode text --workdir /path/to/extraction
```

输出 `full_text.txt` 和 `metadata.json`。状态与退出码：`success` / 0、`partial` / 2、`failed` / 1。混合输入有失败时仍保留成功部分和失败原因；生成导师必须披露实际覆盖，不能称为完整全书。

`total_tokens` 是用于分段规划的保守启发式估算，不是特定模型的准确 token 数、计费结果或严格上界。提取成功也不保证图片、公式和语义完整；请核对来源与警告。

## 生成物与记录

```text
<slug>-mentor/
├── SKILL.md                   # 核心内容、路由、教学与改进协议
├── sources.md                 # 来源、覆盖范围、提取缺口
├── chapters/                  # 按需加载，含来源定位与关键问题
│   └── index.md
├── glossary.md
├── patterns.md
├── cheatsheet.md
├── scripts/mentor_state.py    # 随导师复制，不依赖转换器安装位置
├── references/state-schema.md
├── state/state.json          # 权威观察记录
└── learnings.md               # 派生学习摘要
```

```bash
python scripts/mentor_state.py init /path/to/mentor
python scripts/mentor_state.py record /path/to/mentor --event /path/to/event.json
python scripts/mentor_state.py show /path/to/mentor
python scripts/validate_mentor.py /path/to/mentor
```

`init` 不覆盖已有状态；记录通过唯一事件 ID 防重复。模拟数据与真人证据分开；延迟回忆要求同章节、同概念、同模拟/真实类型已有独立答对记录，并间隔至少 24 小时。字段与例子见 [docs/state-schema.md](docs/state-schema.md)。这是项目的证据规则，不是经过验证的通用掌握标准。

## 开发与评估

```bash
python -m unittest discover -s tests -v
# 可选：补齐真实 PDF/RTF 集成测试（建议在虚拟环境内）
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
```

回归测试验证提取、失败披露、状态持久化和结构约束。另需用真实请求演练教学行为：直接讲解、连续卡住、速查、旧记录续学、材料里含指令等。模拟通过只表示这些行为在样本中符合预期；真人教学效果仍需独立应用题及后续延迟测评，不能由模板、测试数量或生成成功推出。

## 反馈与共建

欢迎分享真实使用反馈，尤其是：输入材料类型、所用 Agent、来源定位是否准确、教学过程中最有帮助或最卡住的部分，以及一周后是否仍愿意继续使用。

- [提交 Bug](https://github.com/gengwenhao/book-to-mentor/issues/new?template=bug.yml)
- [兼容性报告](https://github.com/gengwenhao/book-to-mentor/issues/new?template=compatibility.yml)
- [学习体验反馈](https://github.com/gengwenhao/book-to-mentor/issues/new?template=learning-feedback.yml)
- [参与贡献](CONTRIBUTING.md)

请勿在反馈中上传无权公开的书籍正文、个人笔记、密钥或私人文件路径。项目本身不向作者发送书籍内容、学习记录或分析数据，详见 [隐私说明](PRIVACY.md)。

## 作者

由 [Geng Wenhao](https://github.com/gengwenhao) 创建和维护。

小红书：**宇宙机吴彦祖**（RedNote ID：`292844431`）

欢迎通过小红书分享使用案例，或反馈你希望转换的书籍类型、实际学习体验和改进建议。

<img src="assets/xiaohongshu-qr.jpg" alt="宇宙机吴彦祖的小红书二维码，RedNote ID 292844431" width="360">

## 设计来源

设计受到 [book-to-skill](https://github.com/virgiliojr94/book-to-skill)、[awesome-copilot 的 mentoring-juniors](https://github.com/github/awesome-copilot)、[socratic-method](https://gist.github.com/RalucaNicola/af42f35b54f96252fd0ab5e0920fbd24)、[Bloom](https://github.com/Li-Evan/Bloom) 和 [self-evolve-agent](https://hub.openclaw.ai/mikonos/self-evolve-agent) 启发。引用设计思路不代表本项目复现了这些项目的实现或实证结果。

## License

[MIT](LICENSE)
