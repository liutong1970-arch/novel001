# story-craft 技法层

这是 `wenxin-v6` 的上游故事设计与结构诊断层。它借用 book-to-skill 的组织方式：把参考书编译成可按需读取的工作模块，而不是把理论塞进主 `SKILL.md`。

关键要求：story-craft 必须嵌入创作流程，不作为外部书评单独判断。分析章节时，要同时指出细纲问题、正文问题和下一步修改动作。

## 总路由

优先读取顺序：

1. `integrated-fiction-workflow.md`：统一创作流程。
2. `cheatsheet.md`：快速判断问题归因。
3. 依据任务读取具体模块。

## 何时读取

| 用户任务 | 读取 |
| --- | --- |
| 写作、审稿、修订需要统一判断 | `integrated-fiction-workflow.md` + `cheatsheet.md` |
| 快速判断问题归因 | `cheatsheet.md` |
| 查常见创作模式/反模式 | `patterns.md` |
| 查术语 | `glossary.md` |
| 故事体检、前提审查、主题判断 | `story-architecture.md` |
| 开书体检、黄金三章、前10章追读梯度 | `opening-strategy.md` |
| 爆款对标、竞品拆解、题材参考 | `benchmark-analysis.md` |
| 15节拍、卷纲、章纲、五星细纲 | `beat-outline.md` |
| 人物卡、人物关系、主角弧光 | `character-engine.md` |
| 世界观、力量体系、势力设计 | `world-building.md` |
| 伏笔埋设、推进、回收 | `foreshadowing.md` |
| 卷间衔接、长线节点、反派梯队 | `long-term-planning.md` |
| 写某章前检查2-3个场景是否有戏 | `scene-design.md` |
| 对白生成、对白审查、去说明腔 | `dialogue-craft.md` |
| 完成章节后综合审稿 | `revision-checklist.md` |
| 不确定整体原则 | `core-frameworks.md` |
| 查某规则来自哪本书 | `source-map.md` |

## 工作原则

- 先判断故事是否成立，再润色文字。
- 先修欲望、阻力、价值转变，再扩写感官细节。
- 先用结构发现问题，再用 `wenxin` 的自然度质检与人味儿保护修正文风。
- 所有判断必须回到当前项目文件，指出细纲诱因、正文表现和修改顺序。
- 不复制参考书长段原文，只保留可执行规则、检查表和输出模板。
