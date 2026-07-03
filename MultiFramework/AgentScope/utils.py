# -*- coding: utf-8 -*-
"""三国狼人杀游戏工具函数"""
import random
from typing import List, Dict, Optional, Any
from collections import Counter

from agentscope.agent import Agent

# 游戏常量
MAX_GAME_ROUND = 10
MAX_DISCUSSION_ROUND = 3
CHINESE_NAMES = [
    "刘备", "关羽", "张飞", "诸葛亮", "赵云",
    "曹操", "司马懿", "典韦", "许褚", "夏侯惇",
    "孙权", "周瑜", "陆逊", "甘宁", "太史慈",
    "吕布", "貂蝉", "董卓", "袁绍", "袁术"
]


def majority_vote(votes: Dict[str, str]) -> tuple[str, int]:
    """投票结果统计"""
    valid_votes = {k: v for k, v in votes.items() if v is not None}
    if not valid_votes:
        return None, 0
    counter = Counter(valid_votes.values())
    most_voted = counter.most_common(1)[0]
    return most_voted[0], most_voted[1]


def get_chinese_name(character: str = None) -> str:
    """获取中文角色名"""
    if character and character in CHINESE_NAMES:
        return character
    return random.choice(CHINESE_NAMES)


def format_player_list(players: List[Agent], show_roles: bool = False) -> str:
    """格式化玩家列表为中文显示"""
    if not players:
        return "无玩家"

    if show_roles:
        return "、".join([f"{p.name}({getattr(p, 'role', '未知')})" for p in players])
    else:
        return "、".join([p.name for p in players])


def check_winning(alive_players: List[Agent], roles: Dict[str, str]) -> Optional[str]:
    """检查游戏胜利条件"""
    alive_roles = [roles.get(p.name, "村民") for p in alive_players]
    werewolf_count = alive_roles.count("狼人")
    villager_count = len(alive_roles) - werewolf_count

    if werewolf_count == 0:
        return "好人阵营胜利！所有狼人已被淘汰！"
    elif werewolf_count >= villager_count:
        return "狼人阵营胜利！狼人数量已达到或超过好人！"

    return None


def analyze_speech_pattern(speech: str) -> Dict[str, Any]:
    """分析发言模式"""
    analysis = {
        "word_count": len(speech),
        "confidence_keywords": 0,
        "doubt_keywords": 0,
        "emotion_score": 0
    }

    confidence_words = ["确定", "肯定", "一定", "绝对", "必须", "显然"]
    doubt_words = ["可能", "也许", "或许", "怀疑", "不确定", "感觉"]

    for word in confidence_words:
        analysis["confidence_keywords"] += speech.count(word)

    for word in doubt_words:
        analysis["doubt_keywords"] += speech.count(word)

    positive_words = ["好", "棒", "赞", "支持", "同意"]
    negative_words = ["坏", "差", "反对", "不行", "错误"]

    for word in positive_words:
        analysis["emotion_score"] += speech.count(word)

    for word in negative_words:
        analysis["emotion_score"] -= speech.count(word)

    return analysis


class GameModerator:
    """游戏主持人 - 记录游戏日志"""

    def __init__(self) -> None:
        self.name = "游戏主持人"
        self.game_log: List[str] = []

    def log(self, content: str) -> None:
        """记录并打印游戏公告"""
        print(f"[游戏主持人] {content}")
        self.game_log.append(content)


def format_player_list_str(players: List[str]) -> str:
    """格式化玩家姓名列表"""
    if not players:
        return "无人"
    return "、".join(players)


def calculate_suspicion_score(player_name: str, game_history: List[Dict]) -> float:
    """计算玩家可疑度分数"""
    score = 0.0

    for event in game_history:
        if event.get("type") == "vote" and event.get("target") == player_name:
            score += 0.3
        elif event.get("type") == "accusation" and event.get("target") == player_name:
            score += 0.2
        elif event.get("type") == "defense" and event.get("player") == player_name:
            score -= 0.1

    return min(max(score, 0.0), 1.0)
