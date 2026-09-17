---
name: book-to-mentor
description: Convert a book or document into a dedicated Socratic mentor skill that teaches the book through guided questions and adapts to the learner. Use when the user provides a book file path and asks to make a book mentor, tutor, or study skill, or says 书籍转导师. Do not use for one-off book summaries or generic Q&A.
---

# Book-to-Mentor 转换器

把一本书（或一批文档）转换成一个可安装的「书籍导师」Skill：
蒸馏出核心思维模型 → 按需加载的章节 → 苏格拉底教学引擎 → 自我进化协议。

生成物是一个完整的 `{slug}-mentor/` skill 目录，可安装到 TRAE / OpenClaw / Hermes 技能目录。

## 触发与输入

- 用户给出一个或多个文件/文件夹/glob 路径 + 转换意图（如"书籍转导师"、"把这本做成导师 skill"）
- 无路径 → 停止并给出用法：`book-to-mentor <book-path...> [skill-slug]`
- 最后一个参数若不像存在的文件/路径，当作 `SLUG`（kebab-case）
- 若输入指向已存在的 mentor skill 目录，或 SLUG 已存在 → 进入 Mode 4 增量更新（fold-in）

## 支持格式

PDF, EPUB, DOCX, TXT, MD, Markdown, HTML, RTF
（MOBI/AZW 需要 Calibre，检测到再说）

## 工作流（严格按步骤，勿跳步）

### Step 0 — 出界检查
无有效输入 → 停止，提示用法。

### Step 1 — 校验输入
展开目录/glob，确认至少一个受支持文件，否则报错停止。

### Step 1.5 — 内容类型（问用户）
> 这些内容属于哪种？
> 1. technical — 有代码/表格/公式（如技术书、论文）
> 2. text — 以叙述为主（管理/社科/自传）
> 3. 不确定 → 用 text

technical 用结构感知提取；text 用快速提取。

### Step 2 — 提取文本
运行脚本：

```bash
python <skill>/scripts/extract.py <paths...> --mode <technical|text>
```

- 输出到 `<workdir>/full_text.txt` + `metadata.json`
- 提取器缺失依赖时询问用户是否安装，否则用回退方案
- 读取 metadata.json 确认提取正确（核对 source_file / SOURCE 头）
- 纯 txt/md 可直接用 Read 读取，跳过脚本

### Step 2.5 — 成本预估
基于 metadata 估算 tokens 与费用，向用户展示并确认后再生成：
- 输入 ≈ tokens × 1.3；输出 ≈ 章节数 × 预算 + 4K(SKILL.md) + 4.5K(glossary+patterns+cheatsheet)
- 章节预算：text ≈ 1,000 / technical ≈ 1,800

### Step 2.6 — 大书 REPL 式探测
> 50K tokens 以上用 grep/sed/Read(offset, limit) 按需切片，绝不整本 Read。

### Step 3 — 结构分析
读前 8,000 字符：标题/作者/章节结构/ToC/核心主题/章节数。
（analyze-only 模式：输出提取报告并停止）

### Step 4 — 问用途 → DEPTH
> 这个导师 Skill 主要帮你做什么？
> 1. 应用作者的框架干活
> 2. 用作者的思维模型思考
> 3. 查具体章节/概念
> 4. 全都要

全都要 → DEPTH=study（章节摘要加深）；否则 DEPTH=reference。

### Step 5 — 命名
`{author-lastname}-{core-concept}-mentor` 或 `{book-slug}-mentor`，kebab-case。

### Step 6-8 — 生成 skill 文件（核心产出）
复制 `assets/mentor-template.md` 为 `<workdir>/<slug>-mentor/SKILL.md`，按以下填充：

**6. 核心思维模型（前置，放 SKILL.md 最前）**
- 作者的 2-4 个核心框架：`{名称}：{一句话}。适用：{何时用}`
- 核心决策规则表（场景 → 规则）
- 反模式（作者告诫避免的，注明为什么）

**7. 逐章摘要**
每章生成 `<slug>-mentor/chapters/chNN-<kebab>.md`：
- 本章核心概念/流程（~800-1,200 tokens）
- **关键问题 3-5 个**（供导师提问：覆盖澄清/假设/证据/观点/深层）
- 若 technical：附代码示例与参考表
同时生成 `chapters/index.md`（主题 → 章节映射）。

**8. 术语/模式/速查**
- `glossary.md`：术语按字母序 + 章节引用（~1.5K）
- `patterns.md`：书中的框架/技术/算法（~2K）
- `cheatsheet.md`：决策表/速查规则（~1K）

### Step 9 — 质量自检（全部通过才算完成）
- [ ] 框架保留作者精确命名（"5 Whys" 不写成"多问几次为什么"）
- [ ] 实践者口吻（"Use X when Y"，不写 "The book explains X"）
- [ ] 绝不复制原文长段落（只留结构化合成内容）
- [ ] 每章含 3-5 个关键问题
- [ ] SKILL.md 前置了最重要内容
- [ ] 教学引擎段与进化协议段完整（来自模板）

### Step 10 — 安装与报告
询问用户安装目标（默认当前工作区 `mentors/<slug>-mentor/`）：
- 工作区目录（测试用，默认）
- 项目技能：`<workspace>/.trae/skills/<slug>-mentor/`
- 全局技能：`~/.trae-cn/skills/<slug>-mentor/`（CN）或 `~/.trae/skills/`（国际版）

复制生成目录到目标，报告：

```
✅ 已生成 <slug>-mentor（<N> 章，~<N>K tokens）
📁 位置: <path>
🎓 试一句: "用《书》的框架，苏格拉底式地教我 <某概念>"
```

## 生成物结构（模板见 assets/mentor-template.md）

```
<slug>-mentor/
├── SKILL.md        # 核心模型 + 章节索引 + 教学引擎 + 进化协议
├── chapters/       # 按需加载
├── glossary.md     # 术语
├── patterns.md     # 框架/模式
├── cheatsheet.md   # 决策速查
├── state/          # 进化状态机 + 观察数据
└── learnings.md    # 学习者画像
```

## 写权限边界（防腐化）

- 转换阶段：只写书籍内容文件（核心模型/chapters/glossary/patterns/cheatsheet）
- 教学策略（教学引擎段、state/、learnings.md）由进化协议在运行期更新
- 两个角色不互相改写对方的文件

## 运行期：生成后如何工作（内置在生成物中）

- **导师层**：Sensei 人格 + 四阶段会话（引出→诊断→差距→教学探询）+ 五级提问 + 四级提示 + 自适应下一课
- **回答路由**：概念→chapters/；框架用法→patterns+cheatsheet；术语→glossary；全局→SKILL.md 核心模型；超范围→明确告知
- **进化层**：每次会话结束记录观察（答错率/卡壳点/完成率），定期四步巡航（状态同步→记录→评估固化→启动新实验），胜者固化进教学引擎段

## 维护

- 新书 / 新章节材料 → Mode 4 fold-in：重跑 Step 2 提取新文件，合并到现有 skill（更新章节摘要与索引/术语/速查，不重建）
- 校验提取环境：`python <skill>/scripts/extract.py --check`

## 禁忌

1. 不整本 Read 大文件（>50K tokens 必须切片）
2. 不生成"只有摘要的书评"，必须含教学引擎与章节索引
3. 生成的章节不复制原文长段落
4. 不跳过成本确认
5. 转换阶段不改写已有 mentor skill 的教学策略
