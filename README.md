# wenxin-v6 — 番茄中文网小说创作工作流

wenxin-v6 是重建后的串行小说生产线，目标是让作品更符合番茄中文网的吸量、留存、追读和低质治理要求。

v6 不承诺必然爆款。它提供的是严格流程：先确认承诺，再设计黄金三章，再写章，再质检，再追踪，再复盘。

## 核心变化

- 从旧追读模型升级为“五维模型”：突发性、困惑度、信息熵、追读力、平台留存力。
- 架构采用 L0-L7：理论内核、创作律、风格库、开书策略、章级追读、长线资产、质量治理、数据复盘。
- 统一脚本口径：重复段落、POV、钩子、信息密度和追读力检测全部内嵌在 `scripts/naturalness_scan.py`。
- 新增开书策略、平台增长模型、世界观、伏笔、长线规划、对标分析、情绪追踪、素材触发和低质风险治理。

## 工作流

```text
选题/对标
  -> 书名/简介/标签承诺
  -> 开书体检/黄金三章
  -> 前10章追读梯度
  -> 卷纲/章纲/细纲
  -> 正文三维编织
  -> 结构 + 追读 + 自然度 + 低质风险质检
  -> 追踪表更新
  -> 数据复盘
```

## 常用命令

| 命令 | 说明 |
| --- | --- |
| `/wenxin-v6 新建项目` | 创建标准项目与追踪模板 |
| `/wenxin-v6 开书体检` | 检查书名、简介、标签、第一章承诺 |
| `/wenxin-v6 爆款对标` | 拆解对标作品的结构、爽点、钩子 |
| `/wenxin-v6 黄金三章审稿` | 审查前三章留存与追读梯度 |
| `/wenxin-v6 生成章纲` | 生成带信息增量、爽点、钩子的章纲 |
| `/wenxin-v6 写第X章` | 执行完整写章流程 |
| `/wenxin-v6 自然度质检` | 运行本地自然度与追读扫描 |
| `/wenxin-v6 情绪值检查` | 检查情绪起点、触发事件、终点和外化动作 |
| `/wenxin-v6 素材搜索` | 搜索或复用真实感官细节，补私人纹理 |
| `/wenxin-v6 追读复盘` | 检查信息密度、爽点兑现、章末钩子 |
| `/wenxin-v6 长线规划` | 检查卷间衔接、伏笔、势力和升级曲线 |
| `/wenxin-v6 低质风险检查` | 检查水化、模板堆砌、逻辑割裂和批量感 |

## 目录结构

```text
wenxin-v6/
├── SKILL.md
├── principles.md
├── references/
│   ├── platform-growth-model.md
│   ├── quality-governance.md
│   ├── fanqie-style.md
│   ├── fangxiang-style.md
│   ├── tianmo-style.md
│   ├── emotion-system.md
│   ├── material-search-workflow.md
│   ├── scraped-sensory-details.md
│   ├── satisfaction-engine.md
│   ├── hook-cheatsheet.md
│   ├── naturalness-workflow.md
│   ├── project-templates/追踪模板.md
│   └── story-craft/
│       ├── README.md
│       ├── opening-strategy.md
│       ├── story-architecture.md
│       ├── beat-outline.md
│       ├── character-engine.md
│       ├── world-building.md
│       ├── foreshadowing.md
│       ├── long-term-planning.md
│       ├── benchmark-analysis.md
│       ├── scene-design.md
│       ├── dialogue-craft.md
│       ├── revision-checklist.md
│       ├── patterns.md
│       ├── core-frameworks.md
│       ├── source-map.md
│       ├── cheatsheet.md
│       ├── glossary.md
│       └── integrated-fiction-workflow.md
└── scripts/
    ├── naturalness_scan.py
    ├── naturalness_batch_scan.py
    ├── naturalness_segment_queue.py
    └── naturalness_pipeline.py
```

## 质检顺序

1. 结构是否成立。
2. 信息增量是否达标。
3. 爽点是否兑现。
4. 章末钩子是否合格。
5. POV 是否一致。
6. 是否重复或水化。
7. 自然度是否达标。
8. 情绪连续性和素材纹理是否可靠。
9. 低质风险是否可接受。

任一 P0/P1 级问题出现，先修细纲或结构，不做表层润色。
