#!/usr/bin/env python3
"""Local naturalness scanner for Chinese fiction drafts.

This is not an AI-detector clone. It is a transparent editing aid inspired by
open humanizer/audit projects: measure rhythm, lexical patterning, concrete
texture, and over-smooth prose so revision can target the actual writing.

wenxin-v6 additions:
- Extended pattern word list (Level-3: "像"句式, "暗道", "世界观碎了", fear templates)
- "像" sentence ratio tracking
- POV drift detection (mentions of other characters' internal states)
- Repetition detection within chapter
- Hook strength check at chapter end
"""

from __future__ import annotations

import argparse
import math
import re
import statistics
from collections import Counter
from pathlib import Path


# === Pattern words (L1 一级禁词) ===
PATTERN_WORDS = [
    "仿佛",
    "犹如",
    "宛若",
    "如同",
    "一丝",
    "一抹",
    "深吸一口气",
    "缓缓",
    "微微",
    "轻轻",
    "淡淡",
    "突然",
    "瞬间",
    "好像",
    "不是",
    "眼中闪过",
    "嘴角勾起",
    "眉头微皱",
    "瞳孔微缩",
    "心中一动",
    "心头一震",
    "心中暗道",
    "不容置疑",
    "显而易见",
    "毫无疑问",
]

# === Level-3 banned patterns (wenxin-v6 新增) ===
LEVEL3_PATTERNS = {
    "像句式": r"像[^，,。！？\n]*[的一被了着]",
    "暗道类": r"她暗道|他暗道|心里暗道|心中暗道",
    "世界观碎了": r"世界观.*碎",
    "恐惧模板_腿抖": r"腿.*抖|抖.*腿",
    "恐惧模板_脸色发白": r"脸色.*发白|发白.*脸色",
    "恐惧模板_嘴唇哆嗦": r"嘴唇.*哆|哆嗦",
    "恐惧模板_说不出话": r"说不出话|一个字.*挤不出来",
}

# === "像"句式计数器（单独追踪） ===
LIKE_PATTERN = re.compile(r"像[^。！？\n]{1,30}[的一被了着吗呢吧]")

# === POV 漂移检测（wenxin-v6 新增） ===
# 检测"他感到/他觉得/他心里想/她感到/她觉得"等可能表示其他角色内心活动的模式
POV_DRIFT_PATTERNS = [
    r"他(感到|觉得|想到|意识到|明白|心里想)",
    r"她(感到|觉得|想到|意识到|明白|心里想)",
    r"(他|她)(突然想起|忽然明白|心中暗想|暗自思忖)",
    r"[\u4e00-\u9fff]{2,4}(感到|觉得|想到|意识到|明白|心里想|突然想起|忽然明白|暗自思忖)",
]
POV_DRIFT_RE = [re.compile(p) for p in POV_DRIFT_PATTERNS]

# === 章末钩子强度检测（wenxin-v6 新增） ===
HOOK_INDICATORS = {
    "strong_suspense": [r"推开门|电话响了|看到|发现|听到|门外的|车灯"],
    "abnormal_event": [r"自己翻|浮出来|多出|变了|动了|响了|亮了"],
    "emotional_peak": [r"终于|第一次|三年了|他知道|她明白"],
    "dialogue_hook": [r"确定|结束|你以为|知道|在想"],
    "weak_environment": [r"雨还在|路灯|摇晃|安静|沉默|看着"],
    "weak_repeat": [r"可乐|不凉了|皱了皱眉|放下|看了看"],
}
for k, v in HOOK_INDICATORS.items():
    HOOK_INDICATORS[k] = [re.compile(p) for p in v]

PATTERN_WORDS = list(PATTERN_WORDS)

FUNCTIONAL_WORDS = [
    "异能局",
    "禁忌",
    "污染",
    "符纹",
    "封锁",
    "档案",
    "编号",
    "规则",
    "报告",
    "记录",
    "检测",
    "读数",
    "护盾",
    "结界",
]

PRIVATE_TEXTURE_WORDS = [
    "记得",
    "想起",
    "后悔",
    "讨厌",
    "习惯",
    "小时候",
    "以前",
    "昨晚",
    "没舍得",
    "忍不住",
    "差点",
    "疼",
    "冷",
    "麻",
    "硌",
    "喘",
    "怕",
    "烦",
    "骂",
]

SENSORY_WORDS = [
    "雨",
    "血",
    "疼",
    "麻",
    "冷",
    "热",
    "烫",
    "臭",
    "甜",
    "酸",
    "咔",
    "响",
    "光",
    "黑",
    "红",
    "湿",
    "滑",
    "灰",
]


def cn_len(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def normalized_entropy(items: list[str]) -> float:
    if not items:
        return 1.0
    total = len(items)
    counts = Counter(items)
    entropy = -sum((c / total) * math.log(c / total, 2) for c in counts.values())
    max_entropy = math.log(max(len(counts), 1), 2) or 1.0
    return entropy / max_entropy


def sentence_lengths(text: str) -> list[int]:
    parts = re.split(r"[。！？!?；;]+|\n+", text)
    lengths = [cn_len(part) for part in parts if cn_len(part)]
    return lengths or [0]


def moving_ttr(chars: list[str], window: int = 80) -> float:
    if not chars:
        return 1.0
    if len(chars) <= window:
        return len(set(chars)) / max(len(chars), 1)
    values = []
    step = max(1, window // 2)
    for start in range(0, len(chars) - window + 1, step):
        chunk = chars[start : start + window]
        values.append(len(set(chunk)) / window)
    return statistics.mean(values) if values else 1.0


def short_run_count(lengths: list[int], threshold: int = 8, run_len: int = 3) -> int:
    runs = 0
    streak = 0
    for length in lengths:
        if length <= threshold:
            streak += 1
        else:
            if streak >= run_len:
                runs += 1
            streak = 0
    if streak >= run_len:
        runs += 1
    return runs


# === wenxin-v6 新增：段落相似度检测 ===
def paragraph_similarity(para_a: str, para_b: str) -> float:
    """计算两个段落的相似度（基于字符级 bigram 重叠）。"""
    def bigrams(text: str) -> set:
        chars = re.findall(r"[\u4e00-\u9fff]", text)
        return set(zip(chars, chars[1:])) if len(chars) > 1 else set()

    bg_a = bigrams(para_a)
    bg_b = bigrams(para_b)
    if not bg_a or not bg_b:
        return 0.0
    intersection = bg_a & bg_b
    union = bg_a | bg_b
    return len(intersection) / len(union) if union else 0.0


def detect_repetitions(paras: list[str], threshold: float = 0.8) -> list[dict]:
    """检测段落重复。返回重复段落列表。"""
    reps = []
    for i in range(len(paras)):
        for j in range(i + 1, len(paras)):
            sim = paragraph_similarity(paras[i], paras[j])
            if sim >= threshold and len(paras[i]) > 10:
                reps.append({
                    "para_i": i,
                    "para_j": j,
                    "similarity": sim,
                    "text_i": paras[i][:60],
                    "text_j": paras[j][:60],
                })
    return reps


# === wenxin-v6 新增：重复桥段检测 ===
def detect_bridge_repetition(text: str, bridge_patterns: list[str], max_count: int = 2) -> list[dict]:
    """检测同一桥段在一章内重复出现超过 max_count 次。"""
    results = []
    for pattern in bridge_patterns:
        matches = [(m.start(), m.group()) for m in re.finditer(pattern, text)]
        if len(matches) > max_count:
            results.append({
                "pattern": pattern,
                "count": len(matches),
                "max_allowed": max_count,
                "positions": [pos for pos, _ in matches],
            })
    return results


# === wenxin-v6 新增：POV 漂移检测 ===
def detect_pov_drift(paras: list[str]) -> list[dict]:
    """检测 POV 漂移：检测是否写了其他角色的内心活动。"""
    drifts = []
    for idx, para in enumerate(paras):
        for pattern in POV_DRIFT_RE:
            if pattern.search(para):
                drifts.append({
                    "paragraph_index": idx,
                    "text": para[:80],
                    "reason": "potential internal state of non-POV character",
                })
    return drifts


# === wenxin-v6 新增：章末钩子强度检测 ===
def detect_hook_strength(text: str) -> dict:
    """检测章末最后 3 段的钩子强度。"""
    paras = [p.strip() for p in text.splitlines() if p.strip() and not p.startswith("#")]
    last_paras = paras[-3:] if len(paras) >= 3 else paras
    last_text = "\n".join(last_paras)

    scores = {
        "strong_suspense": 0,
        "abnormal_event": 0,
        "emotional_peak": 0,
        "dialogue_hook": 0,
        "weak_environment": 0,
        "weak_repeat": 0,
    }

    for key, patterns in HOOK_INDICATORS.items():
        for p in patterns:
            matches = p.findall(last_text)
            scores[key] += len(matches)

    total_positive = scores["strong_suspense"] + scores["abnormal_event"] + scores["emotional_peak"] + scores["dialogue_hook"]
    total_negative = scores["weak_environment"] + scores["weak_repeat"]

    if total_positive >= 2:
        strength = "S"
    elif total_positive >= 1 and total_negative == 0:
        strength = "A" if scores["abnormal_event"] or scores["strong_suspense"] else "B"
    elif total_positive >= 1:
        strength = "C"
    else:
        strength = "D"

    return {
        "strength": strength,
        "scores": scores,
        "last_paragraph": last_paras[-1][:80] if last_paras else "",
        "is_weak": strength in ("C", "D"),
    }


# === wenxin-v6 新增：信息密度检测 ===
def detect_info_density(text: str) -> dict:
    """检测每 500 字的信息增量。

    v6 uses sentence-level filtering: pure environment observations are ignored,
    but they no longer discard valid new information in the same paragraph.
    """
    chars = cn_len(text)
    paras = [p for p in text.splitlines() if p.strip() and not p.startswith("#")]
    invalid_observation_re = re.compile(r"^(雨还在下|风还在吹|天色暗了|路灯亮着|四周很安静|他发现雨|她发现雨|看到雨|听到风声)[。！？!?.]*$")
    event_re = re.compile(r"出现|来到|到达|走进|推开|打开|闯进|靠近|离开|冲进|拦住|带来|站着|多出")
    dialogue_re = re.compile(r"承认|拒绝|提醒|警告|命令|反问|要求|答应|威胁")
    turn_re = re.compile(r"但是|然而|却|不过|可是|没想到|偏偏|反而|忽然|突然")
    reveal_re = re.compile(r"原来|终于|竟然|居然|真相|秘密|身份|线索|证据|名单|账本|记录")
    rule_re = re.compile(r"升级|突破|奖励|惩罚|任务|选择|代价|风险|危机|规则|限制|条件")
    relation_re = re.compile(r"合作|背叛|误会|认可|质疑|交易|承诺|敌人|盟友|关系")
    sensory_trigger_re = re.compile(r"发现|看到|听到|收到")
    valid_context_re = re.compile(
        r"新|陌生|不该|不对|异常|反常|敌|血|伤|门外|车|电话|消息|名字|人影|脚步|账本|档案|名单|符号|能力|系统|任务|奖励|惩罚|危机|威胁|秘密|线索|证据|赔偿|记录"
    )

    increments = 0
    for para in paras:
        sentences = [s.strip() for s in re.split(r"[。！？!?]+", para) if s.strip()]
        for sent in sentences:
            if invalid_observation_re.search(sent):
                continue
            if event_re.search(sent) or dialogue_re.search(sent) or turn_re.search(sent):
                increments += 1
                break
            if reveal_re.search(sent) or rule_re.search(sent) or relation_re.search(sent):
                increments += 1
                break
            if sensory_trigger_re.search(sent) and valid_context_re.search(sent):
                increments += 1
                break

    density_per_500 = (increments / max(chars, 1)) * 500
    return {
        "total_indicators": increments,
        "chinese_chars": chars,
        "density_per_500": round(density_per_500, 2),
        "is_watered": density_per_500 < 0.8,
    }


def scan_text(text: str, label: str) -> dict:
    para_rows = [
        (line_no, line.strip())
        for line_no, line in enumerate(text.splitlines(), 1)
        if line.strip() and not line.startswith("#")
    ]
    paras = [p for _, p in para_rows]
    lengths = [len(p) for p in paras] or [0]
    chinese_chars = cn_len(text)
    cn_chars = re.findall(r"[\u4e00-\u9fff]", text)
    sent_lengths = sentence_lengths(text)
    sent_avg = statistics.mean(sent_lengths)
    sent_stdev = statistics.pstdev(sent_lengths)
    sent_cv = sent_stdev / sent_avg if sent_avg else 0
    short_sentence_ratio = sum(x <= 10 for x in sent_lengths) / max(len(sent_lengths), 1)
    long_sentence_ratio = sum(x >= 42 for x in sent_lengths) / max(len(sent_lengths), 1)
    comma_chain_ratio = sum(1 for s in re.split(r"[。！？!?；;]+|\n+", text) if s.count("，") >= 3) / max(
        len(sent_lengths), 1
    )
    char_mattr = moving_ttr(cn_chars)
    paragraph_density = len(paras) / max(chinese_chars / 1000, 1)

    starts = [p[:2] for p in paras if len(p) >= 2 and not p.startswith('"')]
    start_counts = Counter(starts)
    top_start_count = start_counts.most_common(1)[0][1] if start_counts else 0
    top_start_ratio = top_start_count / max(len(starts), 1)
    start_entropy = normalized_entropy(starts)

    dialogue_ratio = sum(p.startswith('"') for p in paras) / max(len(paras), 1)
    pattern_hits = {w: count for w in PATTERN_WORDS if (count := text.count(w))}

    # wenxin-v6: 三级禁词检测
    level3_hits = {}
    for name, pattern in LEVEL3_PATTERNS.items():
        count = len(re.findall(pattern, text))
        if count > 0:
            level3_hits[name] = count

    # wenxin-v6: "像"句式计数
    like_count = len(LIKE_PATTERN.findall(text))

    functional_hits = sum(text.count(w) for w in FUNCTIONAL_WORDS)
    private_hits = sum(text.count(w) for w in PRIVATE_TEXTURE_WORDS)
    sensory_hits = sum(text.count(w) for w in SENSORY_WORDS)
    subject_repeats = sum(text.count(w) for w in set(re.findall(r"[\u4e00-\u9fff]{2,4}(?=说|问|看|想|走|跑|喊|叫|站|坐|拿|放|拉|推)", text)))

    avg_len = statistics.mean(lengths)
    stdev_len = statistics.pstdev(lengths)
    cv = stdev_len / avg_len if avg_len else 0
    short_runs = short_run_count(lengths)
    medium_regular_ratio = sum(10 <= x <= 28 for x in lengths) / max(len(lengths), 1)
    long_para_ratio = sum(x >= 55 for x in lengths) / max(len(lengths), 1)

    top_start_examples = {}
    for start, count in start_counts.most_common(6):
        if count < 2:
            continue
        examples = []
        for line_no, para in para_rows:
            if para.startswith('"'):
                continue
            if para.startswith(start):
                examples.append((line_no, para[:36]))
            if len(examples) >= 4:
                break
        top_start_examples[start] = examples

    # wenxin-v6: 重复段落检测
    repetitions = detect_repetitions(paras, threshold=0.8)

    # wenxin-v6: 重复桥段检测
    bridge_patterns = [
        r"可乐.*不凉|不凉.*可乐",
        r"皱了皱眉|皱眉",
        r"拿起.*喝|喝了一口",
    ]
    bridge_reps = detect_bridge_repetition(text, bridge_patterns, max_count=2)

    # wenxin-v6: POV 漂移检测
    pov_drifts = detect_pov_drift(paras)

    # wenxin-v6: 章末钩子强度
    hook = detect_hook_strength(text)

    # wenxin-v6: 信息密度
    info_density = detect_info_density(text)

    # wenxin-v6: 感叹号计数（L1 标点律：每章不超过 5 个）
    exclamation_count = text.count("！") + text.count("!")

    rhythm_risk = clamp(
        medium_regular_ratio * 45
        + max(0, 1.05 - cv) * 25
        + short_runs * 8
        + (0.08 - long_para_ratio) * 120
    )
    pattern_risk = clamp(
        sum(pattern_hits.values()) * 8
        + top_start_ratio * 55
        + (1 - start_entropy) * 35
        + max(0, subject_repeats / max(chinese_chars, 1) * 1000 - 10) * 2
    )
    texture_risk = clamp(
        max(0, functional_hits - private_hits) * 2.5
        + max(0, 16 - sensory_hits) * 2
        + (0.18 - dialogue_ratio) * 90
    )
    stats_risk = clamp(
        max(0, 0.42 - sent_cv) * 85
        + max(0, 0.09 - short_sentence_ratio) * 180
        + max(0, 0.55 - char_mattr) * 95
        + max(0, comma_chain_ratio - 0.18) * 110
        + max(0, 0.08 - long_sentence_ratio) * 80
    )
    staccato_risk = clamp(
        max(0, short_sentence_ratio - 0.30) * 170
        + max(0, 0.035 - long_sentence_ratio) * 210
        + max(0, paragraph_density - 24) * 2.3
        + max(0, 18 - sent_avg) * 2.0
    )
    stats_risk = max(stats_risk, staccato_risk)

    weighted_risk = clamp(rhythm_risk * 0.28 + pattern_risk * 0.24 + texture_risk * 0.21 + stats_risk * 0.27)
    total_risk = max(weighted_risk, stats_risk * 0.85 if stats_risk >= 35 else weighted_risk)

    # wenxin-v6: 追读力评分
    engagement_score = 0
    engagement_factors = []

    # 信息增量密度 (满分10)
    info_score = min(10, info_density["density_per_500"] * 2)
    engagement_factors.append(("信息增量密度", round(info_score, 2), info_score))

    # 章末钩子强度 (满分10)
    hook_score_map = {"S": 10, "A": 8, "B": 6, "C": 3, "D": 1}
    hook_score = hook_score_map.get(hook["strength"], 0)
    engagement_factors.append(("章末钩子强度", hook["strength"], hook_score))

    # 主角主动性（v6：分权重，避免“说/看”等通用动词虚高）
    high_agency_patterns = [
        r"决定", r"选择", r"拒绝", r"答应", r"承认", r"揭开", r"锁定", r"反击",
        r"拦住", r"挡住", r"追上", r"抢先", r"主动", r"不等.*开口", r"没有等",
    ]
    action_patterns = [
        r"冲", r"挡", r"追", r"拦", r"躲", r"砸", r"踹", r"抓", r"按", r"扣",
        r"拔", r"掀", r"翻", r"递", r"收", r"藏", r"扔", r"抢", r"夺", r"转身",
        r"抬手", r"开口", r"推开", r"打开", r"关上", r"放下", r"拿起",
    ]
    high_agency_count = sum(len(re.findall(p, text)) for p in high_agency_patterns)
    action_count = sum(len(re.findall(p, text)) for p in action_patterns)
    agency_score = min(10, high_agency_count * 2 + action_count * 0.5)
    active_count = round(high_agency_count * 2 + action_count * 0.5, 2)
    engagement_factors.append(("主角主动性", active_count, agency_score))

    # 爽点密度（v6：词组/结构模式，避免“打招呼/打扮/杀气”等单字误判）
    satisfaction_patterns = [
        r"打脸", r"反杀", r"突破", r"升级", r"被认可", r"认可", r"捡漏", r"扮猪吃虎",
        r"揭穿", r"反转", r"惩罚", r"赔偿", r"奖励", r"压制", r"逆转", r"后悔",
        r"威胁[^。！？]*解除", r"质疑[^。！？]*(?:停|消失|哑火|沉默)",
    ]
    pressure_patterns = [r"羞辱", r"质疑", r"威胁", r"逼迫", r"嘲笑", r"看不起", r"不配"]
    payoff_patterns = [r"奖励", r"认可", r"赔偿", r"突破", r"后悔", r"沉默", r"震住", r"退后"]
    satisfaction_count = sum(len(re.findall(p, text)) for p in satisfaction_patterns)
    pressure_count = sum(1 for p in pressure_patterns if re.search(p, text))
    payoff_count = sum(1 for p in payoff_patterns if re.search(p, text))
    structure_bonus = 2 if pressure_count and satisfaction_count and payoff_count else 0
    satisfaction_score = min(10, satisfaction_count * 1.5 + structure_bonus)
    conflict_count = satisfaction_count
    engagement_factors.append(("爽点密度", conflict_count, satisfaction_score))

    engagement_raw = (info_score * 0.3) + (hook_score * 0.3) + (agency_score * 0.2) + (satisfaction_score * 0.2)
    engagement_final = clamp(engagement_raw)
    engagement_factors.append(("综合追读力", f"E={engagement_final:.1f}", engagement_final))

    return {
        "path": label,
        "chars_cn": chinese_chars,
        "paragraphs": len(paras),
        "avg_len": avg_len,
        "stdev_len": stdev_len,
        "cv": cv,
        "sentence_avg": sent_avg,
        "sentence_cv": sent_cv,
        "short_sentence_ratio": short_sentence_ratio,
        "long_sentence_ratio": long_sentence_ratio,
        "comma_chain_ratio": comma_chain_ratio,
        "char_mattr": char_mattr,
        "paragraph_density": paragraph_density,
        "dialogue_ratio": dialogue_ratio,
        "medium_regular_ratio": medium_regular_ratio,
        "long_para_ratio": long_para_ratio,
        "short_runs": short_runs,
        "top_starts": start_counts.most_common(10),
        "top_start_examples": top_start_examples,
        "pattern_hits": pattern_hits,
        "level3_hits": level3_hits,
        "like_count": like_count,
        "functional_hits": functional_hits,
        "private_hits": private_hits,
        "sensory_hits": sensory_hits,
        "subject_repeats": subject_repeats,
        "rhythm_risk": rhythm_risk,
        "pattern_risk": pattern_risk,
        "texture_risk": texture_risk,
        "stats_risk": stats_risk,
        "staccato_risk": staccato_risk,
        "total_risk": total_risk,
        # wenxin-v6 新增
        "repetitions": repetitions,
        "bridge_repetitions": bridge_reps,
        "pov_drifts": pov_drifts,
        "hook_strength": hook,
        "info_density": info_density,
        "exclamation_count": exclamation_count,
        "engagement_factors": engagement_factors,
        "engagement_score": engagement_final,
    }


def scan(path: Path) -> dict:
    return scan_text(path.read_text(encoding="utf-8"), str(path))


def print_report(result: dict) -> None:
    print(f"文件：{result['path']}")
    print(f"中文字符数：{result['chars_cn']}")
    print(f"段落数：{result['paragraphs']}")
    print(f"平均段长：{result['avg_len']:.1f}")
    print(f"段长波动：{result['stdev_len']:.1f}，变异系数：{result['cv']:.2f}")
    print(f"句长均值：{result['sentence_avg']:.1f}，句长变异系数：{result['sentence_cv']:.2f}")
    print(f"短句占比：{result['short_sentence_ratio']:.2%}")
    print(f"长句占比：{result['long_sentence_ratio']:.2%}")
    print(f"逗号链占比：{result['comma_chain_ratio']:.2%}")
    print(f"字符多样性MATTR：{result['char_mattr']:.2f}")
    print(f"千字段落密度：{result['paragraph_density']:.1f}")
    print(f"对话占比：{result['dialogue_ratio']:.2%}")
    print(f"中等规整段占比：{result['medium_regular_ratio']:.2%}")
    print(f"长段占比：{result['long_para_ratio']:.2%}")
    print(f"短句连发组数：{result['short_runs']}")
    print(f"高频开头：{result['top_starts']}")
    if result["top_start_examples"]:
        print("重复起句位置：")
        for start, examples in result["top_start_examples"].items():
            joined = "；".join(f"{line}:{sample}" for line, sample in examples)
            print(f"- {start}: {joined}")
    print(f"模式词：{result['pattern_hits'] or '无'}")
    print(f"三级禁词违规：{result['level3_hits'] or '无'}")
    print(f'"像"句式数量：{result["like_count"]}（限额3）')
    excl_status = "⚠️" if result["exclamation_count"] > 5 else "✅"
    print(f"{excl_status} 感叹号数量：{result['exclamation_count']}（限额5）")
    print(f"设定/功能词密度：{result['functional_hits']}")
    print(f"私人/身体纹理：{result['private_hits']}")
    print(f"感官词：{result['sensory_hits']}")
    print("")
    print("自然度风险估计：")
    print(f"- 节奏规整风险：{result['rhythm_risk']:.1f}/100")
    print(f"- 语言模式风险：{result['pattern_risk']:.1f}/100")
    print(f"- 纹理不足风险：{result['texture_risk']:.1f}/100")
    print(f"- 统计指纹风险：{result['stats_risk']:.1f}/100")
    print(f"- 短促镜头风险：{result['staccato_risk']:.1f}/100")
    print(f"- 综合风险：{result['total_risk']:.1f}/100")
    print("")

    # === wenxin-v6 新增输出 ===
    print("=== wenxin-v6 新增检测 ===")
    print("")

    # 重复段落
    if result["repetitions"]:
        print(f"⚠️ 重复段落检测：发现 {len(result['repetitions'])} 组重复段落")
        for rep in result["repetitions"]:
            print(f"  - 段落 {rep['para_i']+1} ↔ 段落 {rep['para_j']+1}，相似度 {rep['similarity']:.0%}")
            print(f"    段落1: {rep['text_i']}")
            print(f"    段落2: {rep['text_j']}")
    else:
        print("✅ 重复段落检测：无重复")
    print("")

    # 重复桥段
    if result["bridge_repetitions"]:
        print(f"⚠️ 重复桥段检测：")
        for br in result["bridge_repetitions"]:
            print(f"  - 模式 '{br['pattern']}' 出现 {br['count']} 次（允许最多 {br['max_allowed']} 次）")
    else:
        print("✅ 重复桥段检测：无违规")
    print("")

    # POV 漂移
    if result["pov_drifts"]:
        print(f"⚠️ POV 漂移检测：发现 {len(result['pov_drifts'])} 处潜在漂移")
        for pd in result["pov_drifts"]:
            print(f"  - 段落 {pd['paragraph_index']+1}: {pd['text']}")
            print(f"    原因: {pd['reason']}")
    else:
        print("✅ POV 一致性：无漂移")
    print("")

    # 章末钩子
    hook_label = {"S": "S-强悬念", "A": "A-反常事件", "B": "B-情绪高点", "C": "C-对话钩子", "D": "D-弱钩子"}
    hook_status = "⚠️" if result["hook_strength"]["is_weak"] else "✅"
    print(f"{hook_status} 章末钩子强度：{hook_label.get(result['hook_strength']['strength'], '?')} ({result['hook_strength']['strength']})")
    print(f"   最后一段: {result['hook_strength']['last_paragraph']}")
    print("")

    # 信息密度
    info_status = "⚠️" if result["info_density"]["is_watered"] else "✅"
    print(f"{info_status} 信息密度：{result['info_density']['density_per_500']}/500字（最低 0.8）")
    if result["info_density"]["is_watered"]:
        print("   ⚠️ 注水！每500字信息增量不足，需要增加新事件/新冲突/新反转")
    print("")

    # 追读力
    print("📊 追读力评分（L0 阈值检查）：")
    engagement_warnings = []
    for name, label, score in result["engagement_factors"]:
        bar = "█" * int(score / 2) + "░" * (10 - int(score / 2))
        print(f"   [{bar}] {name}: {label}")
    # L0 阈值告警
    if result["info_density"]["density_per_500"] < 0.8:
        engagement_warnings.append(f"信息增量密度 {result['info_density']['density_per_500']}/500字 < 0.8，注水")
    if result["hook_strength"]["is_weak"]:
        engagement_warnings.append(f"章末钩子 {result['hook_strength']['strength']} 级为 C/D 级风险，钩子弱")
    factor_scores = {name: score for name, _, score in result["engagement_factors"]}
    if factor_scores.get("主角主动性", 10) < 2:
        engagement_warnings.append("主角主动性得分 < 2，需要增加主动选择或主动行动")
    if factor_scores.get("爽点密度", 10) < 3:
        engagement_warnings.append("爽点密度得分 < 3，需要补足压抑-爆发-奖励链条")
    e_score = result["engagement_score"]
    if e_score < 6:
        engagement_warnings.append(f"综合追读力 E={e_score:.1f} < 6，需要重写")
    if engagement_warnings:
        print("   ⚠️ 追读力告警：")
        for w in engagement_warnings:
            print(f"      - {w}")
    else:
        print("   ✅ 追读力达标")
    print("")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    print_report(scan(args.file))


if __name__ == "__main__":
    main()
