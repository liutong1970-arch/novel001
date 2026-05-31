# 素材搜索扩写功能

> 当章节字数不足（<2000字）时，通过网络搜索获取素材，扩写现有场景。

---

## 触发条件

- 章节字数 < 2000字
- 某个场景明显偏短（<300字）

---

## 搜索工具

### 第一优先：Scrapling

[Scrapling](https://github.com/D4Vinci/Scrapling) 是一个自适应 Web 抓取框架。

**使用方式**：

```python
from scrapling.fetchers import PlayWrightFetcher
from scrapling.parser import Adaptor

# 搜索素材（需要 headless=True）
page = PlayWrightFetcher.fetch(
    'https://www.baidu.com/s?wd=古代渔村+傍晚+收网+描写',
    headless=True, timeout=60000
)

# 解析 HTML
selector = Adaptor(page.body)
results = selector.css('.result')

for result in results[:5]:
    h3 = result.css('h3')
    if h3:
        print(f"标题: {h3[0].get_all_text()}")
```

**注意事项**：
- 百度等搜索引擎需要 `PlayWrightFetcher`（JavaScript 渲染）
- 页面内容在 `body` 属性中，`text` 可能返回 `None`
- 使用 `Adaptor` 解析，`get_all_text()` 获取文本

### 备用方案

1. **WebFetch**：直接获取指定 URL 的内容
2. **WebSearch**：使用内置搜索功能
3. **本地素材库**：使用 `参考资料/` 目录中的素材文件

---

## 搜索关键词策略

根据场景类型提取关键词：

| 场景类型 | 搜索关键词 |
|---------|-----------|
| 古代渔村 | 古代渔村生活、渔民日常、海边村庄描写 |
| 天劫灾难 | 古代天灾描写、雷电灾害、火灾现场 |
| 战斗场面 | 古代战斗描写、冷兵器战斗、战场细节 |
| 修炼场景 | 修仙小说修炼描写、灵气涌动、突破境界 |
| 情感场景 | 离别场景、重逢场景、悲痛描写 |
| 环境描写 | 古代建筑、山水景色、市井街道 |
| 饮食场景 | 古代饮食、地方小吃、烹饪描写 |
| 医药场景 | 中医草药、伤痛描写、疗伤过程 |

---

## 素材筛选原则

1. **真实性**：优先选择有历史依据的描写
2. **感官丰富**：选择包含视觉、听觉、嗅觉、触觉的素材
3. **符合时代**：素材需符合小说的时代背景
4. **去AI味**：避免使用模板化的描写

---

## 素材融入方法

1. 提取素材中的感官细节（非原文照搬）
2. 转换为三维编织格式（发生+感知+反应）
3. 融入原有情节，不破坏节奏
4. 保持每段 ≤ 60字的格式要求
5. 融入后必须再次执行去AI味检查

---

## 扩写原则

- ✅ 符合细纲要求
- ✅ 符合角色性格
- ✅ 符合情节逻辑
- ✅ 不破坏原有节奏
- ✅ 增加感官细节
- ✅ 推进情节或深化角色
- ❌ 不添加无关情节
- ❌ 不破坏人物设定
- ❌ 不与前后章矛盾
