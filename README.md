# 📚 Book-to-Mentor — 把任意一本书变成你的专属 AI 导师

> 输入一本（或一批）书 → 输出一个可安装的「书籍导师」Skill：苏格拉底式教学 + 自适应课程 + 自我进化。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## 这是什么

一个将书籍蒸馏成「导师 Skill」的转换器。与单纯的书评/摘要不同，它生成的 Skill 会：

- **蒸馏**：提炼作者的核心思维模型、决策规则、反模式；章节按需加载（比整书塞上下文省 24-51× token）
- **教学**：Sensei 人格 + 四阶段诊断（引出→诊断→差距→教学探询）+ 五级提问 + 四级提示，绝不直接给答案
- **自适应**：每课针对学习者上轮的薄弱点生成下一课（Bloom 2-Sigma）
- **进化**：记录教学反馈（答错率/卡壳点/完成率），定期跑 A/B 实验，胜者固化，越教越懂你

## 设计

三合一架构：**Distill 蒸馏层 → Mentor 导师层 → Evolve 进化层**，蒸馏层与进化层写权限互斥，防止系统腐化。完整设计见 [docs/blueprint.md](docs/blueprint.md)。

```
书籍 PDF/EPUB/DOCX/...
  → [蒸馏层] 提取 → 结构分析 → 核心模型 + 章节 + 术语/模式/速查
  → [导师层] 生成 SKILL.md（教学引擎：诊断→差距→苏格拉底探询→自适应下一课）
  → [进化层] 会话观察 → A/B 实验 → 胜者固化进教学引擎
```

## 快速开始

### 安装

```bash
git clone https://github.com/gengwenhao/book-to-mentor.git
```

把 `book-to-mentor/` 整个目录复制到你的技能目录：

| 宿主 | 位置 |
|------|------|
| TRAE（项目级） | `<workspace>/.trae/skills/book-to-mentor/` |
| TRAE / Claude Code（全局） | `~/.claude/skills/book-to-mentor/` |
| Hermes Agent | `$HERMES_HOME/skills/book-to-mentor/` |

### 使用

对支持 Skills 的 agent 说：

```
用 book-to-mentor 把 <书.pdf> 转成导师 skill
```

流程会依次询问：内容类型（technical / text）→ 确认生成成本 → 选择安装位置，然后生成完整导师 Skill 并报告路径。

### 支持格式

PDF · EPUB · DOCX · TXT · MD · HTML · RTF（MOBI/AZW 需 Calibre）

### 提取器依赖

```bash
pip install pypdf                    # 纯文字 PDF（快速）
pip install ebooklib beautifulsoup4  # EPUB
pip install python-docx              # DOCX
pip install docling                  # technical PDF（保留表格/代码块，~1.5s/页）
```

检查已安装的提取器：

```bash
python scripts/extract.py --check
```

## 生成的 Skill 结构

```
<slug>-mentor/
├── SKILL.md        # 核心思维模型 + 章节索引 + 教学引擎 + 进化协议
├── chapters/       # 按需加载的章节文件（每章含 3-5 个关键问题，供导师提问）
├── glossary.md     # 术语表
├── patterns.md     # 书中的框架/模式
├── cheatsheet.md   # 决策速查表
├── state/          # 进化状态机 + 观察数据
└── learnings.md    # 学习者画像
```

## 致谢

本项目的三个模块分别受以下开源项目启发：

- **蒸馏层**：[book-to-skill](https://github.com/virgiliojr94/book-to-skill)（MIT）
- **导师层**：[mentoring-juniors](https://github.com/github/awesome-copilot)（MIT）· [socratic-method](https://gist.github.com/RalucaNicola/af42f35b54f96252fd0ab5e0920fbd24) · [Bloom](https://github.com/Li-Evan/Bloom)（MIT）
- **进化层**：[self-evolve-agent](https://hub.openclaw.ai/mikonos/self-evolve-agent)（MIT-0）

## License

[MIT](LICENSE)
