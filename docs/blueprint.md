# 万能书籍转导师 Skill 设计蓝图（Book-to-Mentor）

> 版本：v0.1.0 ｜ 日期：2026-09-17 ｜ 状态：设计稿
> 目标：把任意一本书蒸馏成一个「苏格拉底式 + 自适应 + 自我进化」的专属导师 Skill。

---

## 1. 定位与目标

### 1.1 一句话定义

**输入一本（或多本）书 → 输出一个可安装的导师 Skill**：它像作者本人 + 一位苏格拉底家教 + 一名持续改进的教练。

### 1.2 要解决的三类问题

| 问题 | 现有方案痛点 | 本设计解法 |
|------|-------------|-----------|
| 书读一遍就忘，查 PDF 只得到页码 | 问 AI 会幻觉 / 整书塞上下文烧 token | 蒸馏层：结构化作 Skill，按需加载章节（省 24-51× token） |
| 单向讲课，不检验是否真懂 | 普通 AI 给答案，学习者被动接受 | 导师层：诊断差距 → 苏格拉底探询 → 自适应下一课 |
| 导师永远一个套路，不随学习者变好 | Skill 静态，不会迭代 | 进化层：观察教学反馈 → 跑实验 → 胜者固化 |

### 1.3 设计原则（继承自三个开源项目）

1. **提取结构，不是摘要**（book-to-skill）：框架/决策规则/反模式 > 原文复述
2. **密度优于完整**：1,000 token 的总结 > 10,000 token 的摘录
3. **绝不直接给答案**（mentoring-juniors）：引导学习者自己得出
4. **每课针对上轮差距**（Bloom 2-Sigma）：自适应 = 导师的核心价值
5. **写权限互斥**（llm-skill）：蒸馏写书籍内容、进化写教学策略，互不越界
6. **一次只跑一步**（self-evolve）：进化是巡航，不是一次性大改

---

## 2. 总体架构

```
┌────────────────────────────────────────────────────────────────────┐
│                     book-to-mentor（转换器/生成器）                   │
│                                                                    │
│   输入: PDF/EPUB/DOCX/MD/HTML/RTF/MOBI（一本或一批）                  │
│     │                                                              │
│     ▼                                                              │
│  ┌────────────────────────── DISTILL 蒸馏层 ──────────────────────┐ │
│  │ Step 0-1.5  输入校验 + 内容类型识别(technical/text)             │ │
│  │ Step 2      确定性提取器(extract.py) → full_text + metadata    │ │
│  │ Step 2.5-3  成本预估 + 结构分析(章节/作者/核心主题)              │ │
│  │ Step 4      问用途 → DEPTH(参考/研读)                          │ │
│  │ Step 5-9    逐章摘要 + 术语表/模式/速查表 + SKILL.md 骨架        │ │
│  │ Step 10     安装到 TRAE/OpenClaw/Hermes 技能目录                │ │
│  └────────────────────────────────────────────────────────────────┘ │
│     │                                                              │
│     ▼ 生成产物（安装到技能目录）                                        │
│  ┌──────────────────────── MENTOR 导师层 ─────────────────────────┐ │
│  │ 生成的 {book}-mentor/SKILL.md                                    │ │
│  │  ├─ 书籍核心思维模型（蒸馏结果，前置）                            │ │
│  │  ├─ 章节索引（on-demand 按需加载 chapters/*.md）                 │ │
│  │  ├─ 教学引擎（Sensei 人格 + Dialectic 四阶段 + 自适应闭环）       │ │
│  │  └─ 进化协议（self-evolve 四步巡航）                             │ │
│  └────────────────────────────────────────────────────────────────┘ │
│     │                                                              │
│     ▼ 运行期反馈                                                      │
│  ┌──────────────────────── EVOLVE 进化层 ─────────────────────────┐ │
│  │ state.json(活跃实验) + observations/*.jsonl(教学观察)           │ │
│  │ 巡航：感知差距 → 设计实验 → 观察 → 对比基线 → 固化/回滚 → 下一轮  │ │
│  └────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

**两个运行时边界**（关键决策）：
- **Distill 只写书籍内容文件**（SKILL.md 核心模型、chapters/、glossary/patterns/cheatsheet），绝不触碰教学策略与路由
- **Evolve 只写教学策略**（教学引擎段、state.json、observations/），绝不改写书籍原文

---

## 3. 目录结构与产物

### 3.1 转换器项目（本仓库，开发用）

```
reader-skill/                          # 当前工作目录
├── SKILL.md                           # 转换器本身的 Skill 定义（生成器规范）
├── scripts/
│   └── extract.py                     # 确定性提取器（复制/改造自 book-to-skill）
│       └── parsers/                   # pdf / epub / docx / html / rtf / text / calibre
├── templates/                         # 生成模板
│   ├── mentor-skill-skeleton.md       # 导师 Skill 骨架（见 §8）
│   ├── chapter.md                     # 单章文件模板
│   └── evolution-state.json           # 进化状态机初始模板
├── tools/
│   ├── validate_skill.py              # 校验生成的 SKILL.md 格式（TRAE/OpenClaw 双 lens）
│   └── scan_generated_skill.py        # 提示注入扫描（防 PDF 恶意内容）
└── docs/
    └── blueprints.md                  # 本蓝图
```

### 3.2 转换产物（每本书生成一个，安装到技能目录）

```
{book-slug}-mentor/                    # 如: designing-data-intensive-apps-mentor
├── SKILL.md                           # 核心：书籍模型 + 章节索引 + 教学引擎 + 进化协议（~5-6K tokens）
├── chapters/                          # 按需加载，问到才读
│   ├── ch01-*.md … chNN-*.md          # 每章 ~1,000 tokens（含"本章关键问题"字段，供导师提问）
│   └── index.md                       # 主题 → 章节映射
├── glossary.md                        # 术语表（~1.5K）
├── patterns.md                        # 书中的框架/技术/模式（~2K）
├── cheatsheet.md                      # 决策规则/速查（~1K）
├── state/                             # 进化层专属
│   ├── state.json                     # 活跃实验状态机
│   └── observations/                  # 教学观察 jsonl（按日期）
└── learnings.md                       # 学习者画像与已固化的教学策略
```

**Token 预算**：主 SKILL.md 前置 ~5K，章节按需加载 ~1K/章。一次问答 ≈ 5-6K tokens，远小于整书 100K+。

---

## 4. 模块 A：蒸馏层（Distill）

> 直接继承 book-to-skill 的 Step 0-10 管线，做三处适配：① 章节摘要增加「关键问题」字段供导师层使用；② 增加「作者语气/思维特征」提取（Voice Calibration）；③ 输出目标目录支持 TRAE/OpenClaw。

### 4.1 工作流（Step 0-10）

| Step | 动作 | 要点 |
|------|------|------|
| 0 | 出界检查 | 无参数 → 提示用法；识别 Update/Fold-in 模式 |
| 1 | 输入校验 | 展开目录/glob，确认有受支持文件 |
| 1.5 | 内容类型识别 | 问用户 technical（Docling）还是 text（pdftotext），不猜 |
| 2 | 提取 | `extract.py <paths> --mode <type>` → full_text.txt + metadata.json |
| 2.5 | 成本预估 | 基于 metadata 估算 tokens/费用，用户确认后再生成 |
| 2.6 | REPL 式探测 | >50K tokens 的书用 grep/sed 按需切片，绝不整书 Read |
| 3 | 结构分析 | 标题/作者/章节/ToC/核心主题（读前 8K 字符） |
| 4 | 问用途 | 应用框架 / 思维模型 / 查章节 / 全都要 → 决定 DEPTH 与高亮权重 |
| 5 | 确定 skill 名 | `{author-lastname}-{core-concept}` 或 `{book-slug}-mentor` |
| 6 | 生成 SKILL.md 骨架 | 前置核心思维模型 + 章节索引 |
| 7 | 逐章摘要 | 每章 ~1,000-1,800 tokens（technical 含代码/表格），**新增：每章提炼 3-5 个「关键问题」** |
| 8 | 术语/模式/速查 | glossary（排序+章节引用）、patterns（技术/算法/设计模式）、cheatsheet（决策表） |
| 9 | 质量自检 | 校验：不复制原文段落、框架名保持作者精确命名、实践者口吻 |
| 10 | 安装 | 写入目标技能目录 + 可选发布 |

### 4.2 蒸馏质量规则（Quality Rules）

1. **框架保留原名**："5 Whys" 不能写成"多问几次为什么"
2. **实践者口吻**：写 "Use X when Y"，不写 "The book explains X"
3. **绝不复制原文**：生成的 SKILL.md/chapters 是结构化合成产物，不是摘录
4. **前置加载**：最重要的内容放 SKILL.md 最前面（上下文压缩从尾部截断）
5. **优雅降级**：一个坏文件跳过不致命；扫描 PDF 先提示 OCR

### 4.3 防注入（安全）

- 提取时剥离零宽字符（U+200B 等）与 Unicode Tag Block
- 生成后跑 `scan_generated_skill.py` 做提示注入扫描
- 版权：仅处理用户自有文件，产物视为个人笔记，不传播

---

## 5. 模块 B：导师层（Mentor/Teach）

> 三源融合：Sensei 人格与金规则（mentoring-juniors）+ 四阶段诊断（Dialectic Engine）+ 自适应闭环（Bloom）。

### 5.1 人格与金规则

**Persona：Sensei**——精通本书领域 + 15 年经验的资深导师，苏格拉底式提问，绝不代答。

| # | 金规则 | 落地 |
|---|--------|------|
| 1 | 绝不给无法解释的答案 | 学习者必须能解释每一行/每个结论 |
| 2 | 绝不允许盲目接受 | 每个概念学习者都要能用自己的话复述 |
| 3 | 绝不居高临下 | 任何问题都正当，无评判 |
| 4 | 绝不不耐烦 | 卡住时减速，疲劳时收尾 |

**错误反馈话术**：禁说 "That's wrong" / "No"；改说 "Not yet" / "Almost!" / "这是个好起点，但…"。

### 5.2 四阶段会话协议（Dialectic Engine）

每次新会话开始教学时，用隐藏标签 `[PHASE:N]` 跟踪，**绝不跳阶段**：

```
PHASE 1 — 话题引出：只问一个问题"你想学这本书的什么？"（不做别的）
PHASE 2 — 诊断：最多 5 个递进问题（基础→概念→应用→分析→综合）
          · 连续 2 题答错/说不知道 → 提前停止（到顶了）
          · 5 题全对 → 记为进阶学习者
          · 每轮只问 1 题，不做评价（"Got it." 而非 "Great!"）
PHASE 3 — 差距分析：诚实列出「已懂/缺口」，按基础性排序，最后以一个问题收尾
PHASE 4 — 教学-探询循环：交替直接讲授与苏格拉底提问，直到缺口闭合
```

### 5.3 自适应闭环（Bloom 2-Sigma）

```
lesson N（基于章节内容 + 针对上轮差距）
   → 学习者阅读/划线/回答问题
   → feedback（回答质量、卡壳点、用时）
   → lesson N+1（重新评估差距，只补薄弱处）
   → 全部 mastery 项打勾 ✅
   → 生成 evaluation（掌握度报告）+ summary（学习总结）
```

关键：**每一课开始时先做 spaced retrieval**（回顾上轮要点），再讲新课。

### 5.4 提问层级与提示系统

**五级提问**（难度动态调整，答错降级给提示，答对升级追问原理/trade-off）：

| 级别 | 示例 |
|------|------|
| L1 澄清 | "你说的 X 是指什么？它和 Y 有什么区别？" |
| L2 假设探查 | "这个结论的前提是什么？情况变了还成立吗？" |
| L3 证据检验 | "支持这个观点的证据是什么？" |
| L4 观点探询 | "还有别的可能性吗？从作者的角度看呢？" |
| L5 深层追问 | "作者为什么这样设计？有什么 trade-off？" |

**四级提示系统**（卡壳时按需给，**最高级也绝不直接给答案**）：

| 阻塞程度 | 帮助形式 |
|----------|---------|
| 🟢 轻 | 引导性问题 + 指向具体章节 |
| 🟡 中 | 类比/图示/伪代码 |
| 🟠 强 | 带 `___` 空白的残缺推导 |
| 🔴 严重 | 详细分步提示 + 建议求助人类导师 |

### 5.5 回答问题的知识路由

学习者的任意提问按此路由（不整书塞上下文）：

```
问"某概念/某章内容" → 查 chapters/index.md 主题映射 → 加载对应章节文件
问"某框架怎么用"   → 读 patterns.md + cheatsheet.md 决策表
问"术语"           → 读 glossary.md
问"全书写了什么"   → 只读 SKILL.md 核心模型区
超出本书 → 明确告知"这超出本书范围"，不硬编
```

---

## 6. 模块 C：进化层（Evolve）

> 继承 self-evolve-agent 的巡航模型：**meta-skill 定位**——不解决教学问题本身，而是让"教学方式"越来越好。

### 6.1 核心循环

```
感知差距 → 搜索方案 → 设计实验 → 跑实验(观察) → 对比基线 → 固化/回滚 → 下一轮
```

类比生物进化：**变异（实验）→ 选择（对比基线）→ 保留（固化）**。

### 6.2 四步巡航协议（每次触发只跑一步）

| Step | 动作 | 数据 |
|------|------|------|
| 1. Status Sync | 扫描 state.json 活跃实验，处理到期项 | `state.json` |
| 2. Record Observations | 把本次会话的教学观察降噪写入 | `observations/YYYY-MM-DD.jsonl` |
| 3. Evaluate & Solidify | 到期限的实验对比基线：胜者固化进 SKILL.md 教学引擎段；败者回滚并记录 | 基线 = 固化前策略的累计指标 |
| 4. Launch New Experiment | 并发 <10 时寻找新瓶颈，设计实验并注册为 `OBSERVING`，**本轮强制结束** | `state.json` |

**关键纪律**：部署新实验并更新状态锁后，本巡航立即停止，等待下一次唤醒（用户触发/定时触发）。禁止一次跑完全流程。

### 6.3 观察指标（教学场景定制）

每次会话采集（降噪后写 jsonl）：
- 诊断正确率：学习者答对/总题数 → 判断诊断阶段是否有效
- 卡壳点分布：集中在哪章哪概念（→ 可能是蒸馏层章节质量问题）
- 提示升级率：多少人从 🟢 升到 🔴（→ 提问难度是否过陡）
- 会话完成率 / 平均轮次（→ 节奏是否合适）
- 学习者主动提问质量（→ 是否从"问是什么"进步到"问为什么"）
- 明确反馈：学习者说"这样讲我懂了" / "别讲太细"

### 6.4 实验池（示例，固化后成为候选实验）

| 实验方向 | 假设 | 观测指标 |
|---------|------|---------|
| 类比开场 vs 定义开场 | 类比降低首次卡壳率 | 诊断通过率 |
| 每章 5 题 vs 3 题 | 少题提高完成率 | 会话完成率 |
| 间隔回顾频率 | 频繁回顾提升掌握度 | 最终 evaluation 得分 |
| 提示降级阈值 | 更早给提示减少挫败 | 卡壳退出率 |

### 6.5 反伪进化红线

1. **禁止无目标空转**：每个实验必须有假设 + 观测指标
2. **禁止为改排版而进化**：不因"换个标题风格"跑实验
3. **禁止一次改太多**：一个时间窗内一个实验变量
4. **写权限边界**：Evolve 永不改写 chapters/（书籍内容），只动教学策略段

---

## 7. 数据流与状态机

### 7.1 一次完整生命周期

```
用户提供书
  → [Distill 一次性] 提取→蒸馏→生成 {book}-mentor skill
  → 安装进技能目录
  → [Mentor 每会话] 诊断→差距→教学→评估→总结
  → [Evolve 每次触发] 观察记录 → 到期评估 → 固化/回滚
  → 教学策略随会话数持续变好（skill 自我完善）
```

### 7.2 状态机（进化层）

```
IDLE ──触发──▶ TICK_START
                ├─▶ STEP1_STATUS_SYNC（处理到期）
                │     ├─ 有到期实验 ─▶ STEP3_EVALUATE（固化/回滚）──▶ IDLE
                │     └─ 无到期 ───────────────────┐
                ├─▶ STEP2_RECORD_OBSERVATIONS ─────┤
                └─▶ STEP4_LAUNCH_NEW（额度<10）──▶ LOCK ──▶ 强制退出 ▶ IDLE
```

状态值：`OBSERVING`（实验中）/ `READY`（可评估）/ `SOLIDIFIED`（已固化）/ `ROLLED_BACK`（已回滚）。

---

## 8. 生成模板（{book-slug}-mentor/SKILL.md 产物骨架）

```markdown
---
name: "{book-slug}-mentor"
description: "{Book Title} 的专属导师。基于《{书}》({作者}, {年份})蒸馏而成，提供苏格拉底式教学、自适应课程与自我进化。当用户想学习/复习/讨论这本书的内容时触发。"
version: "0.1.0"
---

# 《{书}》导师

> 由 book-to-mentor 从《{书}》({作者})蒸馏生成。提问教学，不代答；按需加载章节，不整书灌入。

## 一、书籍核心思维模型（前置，最重要）

### 作者的三大核心框架
1. **{框架1}**：{一句话定义}。适用：{何时用}
2. **{框架2}**：…
3. **{框架3}**：…

### 核心决策规则（速查）
| 场景 | 规则 |
|------|------|
| {场景1} | {规则} |

### 反模式（作者告诫避免的）
- {反模式1}：{为什么}

## 二、章节索引（按需加载）

| 章 | 主题 | 文件 | 关键问题 |
|----|------|------|---------|
| 1 | {主题} | [ch01](chapters/ch01-*.md) | {3-5 个教学提问点} |

完整主题→章节映射见 [chapters/index.md](chapters/index.md)；术语表 [glossary.md](glossary.md)；框架/模式 [patterns.md](patterns.md)；决策速查 [cheatsheet.md](cheatsheet.md)。

## 三、教学引擎（Sensei 协议）

### 金规则
1. 绝不给无法解释的答案 — 学习者必须能复述每个结论
2. 绝不允许盲目接受 — 每概念用自己的话讲一遍
3. 绝不居高临下 / 绝不不耐烦

### 会话阶段
[PHASE:1] 引出话题 → [PHASE:2] 诊断(≤5 题递进，可提前停止)
→ [PHASE:3] 差距分析 → [PHASE:4] 教学-探询循环(讲+问交替)

### 提问与提示
- 五级提问（澄清→假设→证据→观点→深层），答错降级给提示，答对升级追问
- 四级提示（引导/类比/空白推导/分步提示），🔴 也绝不给完整答案

### 回答路由
概念→chapters/；框架用法→patterns+cheatsheet；术语→glossary；全局→本文件核心模型；超范围→明确告知。

### 学习状态（存 learnings.md）
- 学习者画像：已懂 / 缺口 / 偏好(深度、节奏、类比偏好)
- 每次会话结束更新；下一课基于此自适应生成

## 四、进化协议（Evolve 巡航）

### 触发
- 每次教学会话结束自动记录观察
- 用户说"进化一下" / 达到评估周期时执行评估

### 四步巡航
1. Status Sync：读 state/state.json 处理到期实验
2. Record Observations：写 state/observations/YYYY-MM-DD.jsonl
3. Evaluate & Solidify：胜者固化到"教学引擎"段，败者回滚
4. Launch New Experiment：并发<10 注册新实验，然后停止

### 红线
- 不空转（每实验须有假设+指标）/ 不伪进化（不因排版跑实验）
- 不改写"书籍核心思维模型"与 chapters/（那是蒸馏层的）

## 五、会话收尾模板

📝 学习总结：本轮掌握 {概念} / 卡壳 {点} / 下次先补 {gap}
🎯 掌握度：{evaluation 摘要}
📚 推荐实践：{一个可立即上手的小练习}
🔁 已记录：{已更新的学习者画像}
```

---

## 9. 落地路线图

| 里程碑 | 内容 | 验收标准 |
|--------|------|---------|
| M1 蒸馏层 | 复制 book-to-skill 管线（extract.py + SKILL.md 生成器），适配 TRAE 技能目录 | 一本技术书 PDF → 生成合法 {book}-mentor skill，能按需答问 |
| M2 导师层 | 注入 Sensei 人格 + 四阶段协议 + 五级提问 + 章节路由 | 新手学习者能走完 诊断→教学→评估 闭环 |
| M3 自适应 | Bloom 式 lesson→feedback→next-lesson + learnings.md 画像 | 第 3 课明显针对第 1 课的薄弱点 |
| M4 进化层 | state.json 状态机 + jsonl 观察 + 固化/回滚 | 连续 3 次会话产生观察记录，一次固化实验 |
| M5 打磨 | validate/scan 工具 + 反伪红线 + 多书验证 | 三本不同类型书（技术/管理/社科）全部通过 |

**M1 是最短可行路径**：先让"书 → 可答问的 Skill"跑通，导师层与进化层在其上叠加。

---

## 10. 参考来源

| 模块 | 项目 | 地址 | License |
|------|------|------|---------|
| 蒸馏 | book-to-skill (virgiliojr94) | https://github.com/virgiliojr94/book-to-skill | MIT |
| 蒸馏 | llm-skill (hanyuancheung) | https://github.com/hanyuancheung/llm-skill | — |
| 导师 | mentoring-juniors (github/awesome-copilot) | https://github.com/github/awesome-copilot/tree/main/skills/mentoring-juniors | MIT |
| 导师 | socratic-method Dialectic Engine (RalucaNicola) | https://gist.github.com/RalucaNicola/af42f35b54f96252fd0ab5e0920fbd24 | — |
| 导师 | Bloom (Li-Evan) | https://github.com/Li-Evan/Bloom | MIT |
| 进化 | self-evolve-agent (mikonos, OpenClaw SkillHub) | https://hub.openclaw.ai/mikonos/self-evolve-agent | MIT-0 |
| 进化 | self-improving-agent (pskoett, ClawHub) | https://imclaw.ai/en/lessons/09 | — |
