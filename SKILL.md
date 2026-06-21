---
name: wenxin-v6
description: |
  文心 v6 — 番茄中文网小说创作工作流。用于新书选题、爆款对标、书名简介、开书体检、黄金三章、前10章追读梯度、世界观、伏笔、长线规划、章纲、写章、续写、改写、自然度质检、情绪值检查、素材搜索、追读复盘、低质风险检查和数据复盘。只支持简体中文。用户提到“去AI味”“低质风险”“追读差”“番茄爆款”时，按“故事诱因 + 追读质量 + 自然度 + 低质治理”串行检查。
---

# /wenxin-v6 — 文心 v6 番茄小说工作流

兼容入口：用户输入 `/wenxin` 或 `/wenxin-v6` 都按本技能执行。

系统架构、阈值、公式和等级以 `principles.md` 为唯一事实源。

## 总原则

1. 先确认平台承诺，再写正文。
2. 第一章必须兑现书名和简介的核心承诺。
3. 每章必须有信息增量、主角主动性、爽点或明确过渡功能、章末钩子。
4. 结构问题优先于语言问题；P0/P1 低质风险不能靠润色修。
5. 追读检测、重复检测、POV 检测全部走 `scripts/naturalness_scan.py`，不调用独立脚本。
6. 每一步串行执行：当前模块未校核通过，不进入下一模块。
7. 默认使用番茄爆款风格；每卷可重新声明风格，同一章不得混搭风格。

## 命令路由

| 用户意图 | 执行动作 | 必读参考 |
| --- | --- | --- |
| 新建项目 | 创建标准目录和追踪模板 | `README.md`, `project-templates/追踪模板.md` |
| 选题/故事体检 | 检查前提、欲望、阻力、类型承诺 | `story-craft/story-architecture.md`, `platform-growth-model.md` |
| 爆款对标 | 拆解对标作品结构，不复制桥段 | `story-craft/benchmark-analysis.md` |
| 开书体检/书名简介 | 检查吸量承诺和第一章兑现 | `platform-growth-model.md`, `story-craft/opening-strategy.md` |
| 黄金三章审稿 | 审前三章留存、爽点、钩子 | `story-craft/opening-strategy.md`, `hook-cheatsheet.md` |
| 人物网络/角色卡 | 设计欲望、弱点、关系压力、声音 | `story-craft/character-engine.md` |
| 世界观/势力 | 设计力量体系、势力压力、规则一致性 | `story-craft/world-building.md` |
| 伏笔管理 | 建立短中长线伏笔和回收计划 | `story-craft/foreshadowing.md` |
| 长线规划 | 检查卷间衔接、节点和反派梯队 | `story-craft/long-term-planning.md` |
| 生成章纲 | 生成带信息增量、爽点、钩子的章纲 | `story-craft/beat-outline.md`, `story-craft/scene-design.md` |
| 写第X章/续写 | 执行完整写章流程 | `story-craft/integrated-fiction-workflow.md`, `satisfaction-engine.md`, `hook-cheatsheet.md` |
| 情绪值检查 | 检查情绪起点、触发事件、终点和外化动作 | `emotion-system.md`, `project-templates/追踪模板.md` |
| 素材搜索/感官素材补强 | 搜索或复用真实感官细节，补私人纹理 | `material-search-workflow.md`, `scraped-sensory-details.md` |
| 改写/审稿 | 先归因，再按严重程度修改 | `story-craft/revision-checklist.md`, `quality-governance.md` |
| 自然度质检 | 运行本地扫描，检查自然度、POV、重复、追读 | `naturalness-workflow.md`, `scripts/naturalness_scan.py` |
| 追读复盘 | 检查信息密度、爽点兑现、章末钩子 | `satisfaction-engine.md`, `hook-cheatsheet.md` |
| 低质风险检查 | 检查水化、模板堆砌、逻辑割裂 | `quality-governance.md` |
| 数据复盘 | 将读完率、追读、互动变化转为修改动作 | `platform-growth-model.md`, `project-templates/追踪模板.md` |

## 本地质检命令

```bash
python3 /Users/tony01/Desktop/wenxin-v6/scripts/naturalness_scan.py <正文文件>
python3 /Users/tony01/Desktop/wenxin-v6/scripts/naturalness_batch_scan.py <正文目录>
python3 /Users/tony01/Desktop/wenxin-v6/scripts/naturalness_segment_queue.py <正文目录> --output <报告目录>/自然度分段修订队列.md
python3 /Users/tony01/Desktop/wenxin-v6/scripts/naturalness_pipeline.py --project-dir <项目目录>
```

输出时只报告关键结果：结构是否通过、追读是否通过、低质风险等级、已更新哪些追踪表、下一章钩子。
