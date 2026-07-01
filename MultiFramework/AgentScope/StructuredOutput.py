# -*- coding: utf-8 -*-
"""三国狼人杀游戏的结构化输出模型"""
from typing import Literal, Optional, List
from pydantic import BaseModel, Field
from agentscope.agent import AgentBase

class DiscussionModel(BaseModel):
    """讨论阶段的输出格式"""
    reach_agreement: bool = Field(
        description="是否已达成一致意见",
        default=False
    )
    confidence_level: int = Field(
        description="对当前推理的信心程度(1-10)",
        ge=1, le=10
        default=5
    )
    key_evidence: Optional[str] = Field(
        description="支持你观点的关键证据",
        default=None
    )

class WithActionModel(BaseModel):
    """女巫行动的输出格式"""
    use_antidote: bool = Field(
        description="是否使用解药救人",
        default=False
    )
    use_poison: bool = Field(
        description="是否使用毒药杀人", 
        default=False
    )
    target_name: Optional[str] = Field(
        description="目标玩家姓名（救人或毒杀的对象）",
        default=None
    )
    action_reason: Optional[str] = Field(
        description="行动理由",
        default=None
    )

class WerewolfKillModel(BaseModel):
    """狼人击杀的输出格式"""
    target: str = Field(
        description="要击杀的玩家姓名",
    )
    kill_strategy: str = Field(
        description="击杀策略说明",
    )
    team_coordination: str = Field(
        description="与狼人队友的配合计划",
        default=None,
    )

class GameAnalysisModel(BaseModel):
    """游戏分析模型的输出格式"""
    suspected_werewolves: List[str] = Field(
        description="怀疑的狼人姓名列表",
        default_factory=list
    )
    trusted_players: List[str] = Field(
        description="信任的玩家姓名列表",
        default_factory=list
    )
    key_clues: List[str] = Field(
        description="关键线索列表",
        default_factory=list
    )
    next_strategy: str = Field(
        description="下一步的策略",
    )

def get_vote_model(agents: list[AgentBase]) -> type[BaseModel]:
    """获取投票阶段的输出格式"""
    class VoteModel(BaseModel):
        """投票阶段的输出格式"""
        vote: Literal[tuple(_.name for _ in agents)] = Field(
            description="你要投票淘汰的玩家姓名"
        )
        reason: str = Field(
            description="投票理由，简要说明为什么选择此人",
        )
        suspicion_level: int = Field(
            description="对被投票者的怀疑程度(1-10)",
            ge=1, le=10
        )

    return VoteModel

def get_seer_model(agents: list[AgentBase]) -> type[BaseModel]:
    """获取预言家阶段的输出格式"""
    class SeerModel(BaseModel):
        """预言家阶段的输出格式"""
        target: Literal[tuple(_.name for _ in agents)] = Field(
            description="要查验的玩家姓名"
        )
        check_reason: str = Field(
            description="查验此人的原因，简要说明为什么选择查验此人",
        )
        priority_level: int = Field(
            description="查验优先级(1-10)",
            ge=1, le=10
        )

def get_hunter_model(agents: list[AgentBase]) -> type[BaseModel]:
    """获取猎人阶段的输出格式"""
    class HunterModel(BaseModel):
        """猎人阶段的输出格式"""
        target: Optional[Literal[tuple(_.name for _ in agents)]] = Field(
            description="要射杀的玩家姓名",
            default=None
        )
        shoot_reason: str = Field(
            description="射杀此人的原因，简要说明为什么选择射杀此人",
            default=None
        )
        shoot: bool = Field(
            description="是否使用开枪技能",
        )
