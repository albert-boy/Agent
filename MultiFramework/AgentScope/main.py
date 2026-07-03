# -*- coding: utf-8 -*-
import asyncio
import os
import random
from typing import List, Dict, Optional
from dotenv import load_dotenv

from agentscope.agent import Agent
from agentscope.model import OpenAIChatModel, StructuredResponse
from agentscope.credential import OpenAICredential
from agentscope.formatter import OpenAIMultiAgentFormatter
from agentscope.message import Msg, UserMsg

from Prompt import Prompts
from GameRoles import GameRoles
from StructuredOutput import (
    DiscussionModel,
    WitchActionModel,
    WerewolfKillModel,
    GameAnalysisModel,
    get_vote_model,
    get_seer_model,
    get_hunter_model,
)
from utils import (
    check_winning,
    majority_vote,
    get_chinese_name,
    format_player_list,
    GameModerator,
    MAX_GAME_ROUND,
    MAX_DISCUSSION_ROUND,
)

load_dotenv()

_LLM_API_KEY = os.getenv("LLM_API_KEY")
_LLM_MODEL_ID = os.getenv("LLM_MODEL_ID")
_LLM_BASE_URL = os.getenv("LLM_BASE_URL")

if not _LLM_API_KEY:
    raise ValueError("环境变量 LLM_API_KEY 未设置，请先设置 API Key")
if not _LLM_MODEL_ID:
    raise ValueError("环境变量 LLM_MODEL_ID 未设置，请先设置模型名称")


class ThreeKingdomsWerewolfGame:
    """三国狼人杀游戏主类"""

    def __init__(self):
        self.players: Dict[str, Agent] = {}
        self.roles: Dict[str, str] = {}
        self.moderator = GameModerator()
        self.alive_players: List[Agent] = []
        self.werewolves: List[Agent] = []
        self.villagers: List[Agent] = []
        self.seer: List[Agent] = []
        self.witch: List[Agent] = []
        self.hunter: List[Agent] = []

        # 女巫道具状态
        self.witch_has_antidote = True
        self.witch_has_poison = True

    async def _broadcast_to_werewolves(self, msg: Msg) -> None:
        """广播消息给所有狼人"""
        for wolf in self.werewolves:
            await wolf.observe(msg)

    async def _broadcast_to_alive(self, msg: Msg) -> None:
        """广播消息给所有存活玩家"""
        for player in self.alive_players:
            await player.observe(msg)

    async def _generate_structured_output(
        self, agent: Agent, prompt: Msg, structured_model: type,
    ) -> Optional[dict]:
        """为指定agent生成结构化输出"""
        await agent.observe(prompt)
        try:
            result: StructuredResponse = await agent.model.generate_structured_output(
                messages=agent.state.context,
                structured_model=structured_model,
            )
            return result.content
        except Exception as e:
            print(f"⚠️ 结构化输出生成失败: {e}")
            return None

    async def werewolf_phase(self, round_num: int):
        """狼人阶段 - 讨论后投票击杀"""
        if not self.werewolves:
            return None

        # 讨论阶段：狼人依次发言，互相广播
        announcement = UserMsg(
            name="游戏主持人",
            content=f"狼人们，请讨论今晚的击杀目标。存活玩家：{format_player_list(self.alive_players)}",
        )
        await self._broadcast_to_werewolves(announcement)

        for _ in range(MAX_DISCUSSION_ROUND):
            for wolf in self.werewolves:
                discussion_prompt = UserMsg(
                    name="游戏主持人",
                    content="请发表你对击杀目标的看法",
                )
                reply = await wolf.reply(discussion_prompt)
                # 将发言广播给其他狼人
                for other_wolf in self.werewolves:
                    if other_wolf.name != wolf.name:
                        await other_wolf.observe(reply)

        # 击杀投票：独立投票，不广播
        kill_votes = {}
        vote_prompt = UserMsg(
            name="游戏主持人",
            content=f"请选择击杀目标，存活玩家：{format_player_list(self.alive_players)}",
        )
        for wolf in self.werewolves:
            result = await self._generate_structured_output(
                wolf, vote_prompt, WerewolfKillModel,
            )
            if result is not None and "target" in result:
                kill_votes[wolf.name] = result["target"]
            else:
                print(f"⚠️ {wolf.name} 的击杀投票无效，随机选择目标")
                valid_targets = [
                    p.name for p in self.alive_players
                    if p.name not in [w.name for w in self.werewolves]
                ]
                kill_votes[wolf.name] = random.choice(valid_targets) if valid_targets else None

        killed_player, _ = majority_vote(kill_votes)
        return killed_player

    async def seer_phase(self):
        """预言家阶段"""
        if not self.seer:
            return

        seer_agent = self.seer[0]
        self.moderator.log("预言家请睁眼，选择要查验的玩家...")

        check_prompt = UserMsg(
            name="游戏主持人",
            content=f"请选择要查验的玩家，存活玩家：{format_player_list(self.alive_players)}",
        )
        result = await self._generate_structured_output(
            seer_agent, check_prompt, get_seer_model(self.alive_players),
        )

        if result is None or "target" not in result:
            print("⚠️ 预言家查验失败，跳过此阶段")
            return

        target_name = result.get("target")
        if not target_name:
            print("⚠️ 预言家没有要查验的玩家，跳过此阶段")
            return

        target_role = self.roles.get(target_name, "村民")

        # 告知查验结果
        result_content = f"查验结果：{target_name}是{'狼人' if target_role == '狼人' else '好人'}"
        await seer_agent.observe(UserMsg(name="游戏主持人", content=result_content))

    async def witch_phase(self, killed_player: str):
        """女巫阶段"""
        if not self.witch:
            return killed_player, None

        witch_agent = self.witch[0]
        self.moderator.log("女巫请睁眼...")

        # 告知女巫死亡信息
        death_info = f"今晚{killed_player}被狼人击杀" if killed_player else "今晚平安无事"
        await witch_agent.observe(UserMsg(name="游戏主持人", content=death_info))

        # 女巫行动
        action_prompt = UserMsg(
            name="游戏主持人",
            content=f"请决定是否使用技能。存活玩家：{format_player_list(self.alive_players)}",
        )
        result = await self._generate_structured_output(
            witch_agent, action_prompt, WitchActionModel,
        )

        saved_player = None
        poisoned_player = None

        if result is None:
            print("⚠️ 女巫行动失败，视为不使用技能")
        else:
            if result.get("use_antidote") and self.witch_has_antidote:
                if killed_player:
                    saved_player = killed_player
                    self.witch_has_antidote = False
                    await witch_agent.observe(
                        UserMsg(name="游戏主持人", content=f"你使用解药救了{killed_player}")
                    )

            if result.get("use_poison") and self.witch_has_poison:
                poisoned_player = result.get("target_name")
                if poisoned_player:
                    self.witch_has_poison = False
                    await witch_agent.observe(
                        UserMsg(name="游戏主持人", content=f"你使用毒药杀死了{poisoned_player}")
                    )

        # 确定最终死亡玩家
        final_killed = killed_player if not saved_player else None

        return final_killed, poisoned_player

    async def hunter_phase(self, shot_by_hunter: str):
        """猎人阶段"""
        if not self.hunter:
            return None

        hunter_agent = self.hunter[0]
        if hunter_agent.name == shot_by_hunter:
            self.moderator.log("猎人发动技能，可以带走一名玩家...")

            action_prompt = UserMsg(
                name="游戏主持人",
                content=f"请决定是否开枪及目标，存活玩家：{format_player_list(self.alive_players)}",
            )
            result = await self._generate_structured_output(
                hunter_agent, action_prompt, get_hunter_model(self.alive_players),
            )

            if result is None:
                print("⚠️ 猎人技能失败，视为放弃开枪")
                return None

            if result.get("shoot"):
                target = result.get("target")
                if target:
                    self.moderator.log(f"猎人{hunter_agent.name}开枪带走了{target}")
                    return target
                else:
                    print("⚠️ 猎人选择开枪但未指定目标，视为放弃")
                    return None

        return None

    async def day_phase(self, round_num: int):
        """白天阶段"""
        self.moderator.log(f"第{round_num}天天亮了，请大家睁眼...")

        # 讨论阶段：玩家依次发言，互相广播
        discussion_announcement = UserMsg(
            name="游戏主持人",
            content=f"现在开始自由讨论。存活玩家：{format_player_list(self.alive_players)}",
        )
        await self._broadcast_to_alive(discussion_announcement)

        for player in self.alive_players:
            discussion_prompt = UserMsg(
                name="游戏主持人",
                content="请发表你的观点和看法",
            )
            reply = await player.reply(discussion_prompt)
            # 将发言广播给其他存活玩家
            for other_player in self.alive_players:
                if other_player.name != player.name:
                    await other_player.observe(reply)

        # 投票阶段：独立投票，不广播
        votes = {}
        vote_prompt = UserMsg(
            name="游戏主持人",
            content=f"请投票选择要淘汰的玩家，存活玩家：{format_player_list(self.alive_players)}",
        )
        for player in self.alive_players:
            result = await self._generate_structured_output(
                player, vote_prompt, get_vote_model(self.alive_players),
            )
            if result is not None and "vote" in result:
                votes[player.name] = result["vote"]
            else:
                print(f"⚠️ {player.name} 的投票无效，视为弃票")
                votes[player.name] = None

        voted_out, vote_count = majority_vote(votes)
        self.moderator.log(f"投票结果：{voted_out}以{vote_count}票被淘汰出局。")

        return voted_out

    def update_alive_players(self, dead_players: List[str]):
        """更新存活玩家列表"""
        for dead_name in dead_players:
            if dead_name:
                self.alive_players = [p for p in self.alive_players if p.name != dead_name]
                self.werewolves = [p for p in self.werewolves if p.name != dead_name]
                self.villagers = [p for p in self.villagers if p.name != dead_name]
                self.seer = [p for p in self.seer if p.name != dead_name]
                self.witch = [p for p in self.witch if p.name != dead_name]
                self.hunter = [p for p in self.hunter if p.name != dead_name]

    async def create_player(self, role: str, character: str) -> Agent:
        """创建具有三国背景的玩家"""
        name = get_chinese_name(character)
        self.roles[name] = role

        agent = Agent(
            name=name,
            system_prompt=Prompts.get_role_prompt(role, character),
            model=OpenAIChatModel(
                credential=OpenAICredential(api_key=_LLM_API_KEY),
                model=_LLM_MODEL_ID,
                stream=False,
                formatter=OpenAIMultiAgentFormatter(),
                client_kwargs={"base_url": _LLM_BASE_URL} if _LLM_BASE_URL else None,
            ),
        )

        # 角色身份确认
        await agent.observe(
            UserMsg(
                name=name,
                content=f"【{name}】你在这场三国狼人杀中扮演{GameRoles.get_role_desc(role)}，"
                        f"你的角色是{character}。{GameRoles.get_role_ability(role)}",
            )
        )

        self.players[name] = agent
        return agent

    async def setup_game(self, player_count: int = 6):
        """设置游戏"""
        print("开始设置三国狼人杀游戏...")

        # 获取角色配置
        roles = GameRoles.get_standard_setup(player_count)
        characters = random.sample([
            "刘备", "关羽", "张飞", "诸葛亮", "赵云",
            "曹操", "司马懿", "周瑜", "孙权"
        ], player_count)

        # 创建玩家
        for role, character in zip(roles, characters):
            agent = await self.create_player(role, character)
            self.alive_players.append(agent)

            # 分配到对应阵营
            if role == "狼人":
                self.werewolves.append(agent)
            elif role == "预言家":
                self.seer.append(agent)
            elif role == "女巫":
                self.witch.append(agent)
            elif role == "猎人":
                self.hunter.append(agent)
            else:
                self.villagers.append(agent)

        # 游戏开始公告
        self.moderator.log(f"三国狼人杀游戏开始！参与者：{format_player_list(self.alive_players)}")

        print(f"游戏设置完成，共{len(self.alive_players)}名玩家")

    async def run_game(self):
        """运行游戏主循环"""
        try:
            await self.setup_game()

            for round_num in range(1, MAX_GAME_ROUND + 1):
                print(f"\n=== 第{round_num}轮游戏开始 ===")

                # 夜晚阶段
                self.moderator.log(f"第{round_num}夜降临，天黑请闭眼...")

                # 狼人击杀
                killed_player = await self.werewolf_phase(round_num)

                # 预言家查验
                await self.seer_phase()

                # 女巫处理
                final_killed, poisoned_player = await self.witch_phase(killed_player)

                # 更新存活玩家列表
                night_deaths = [p for p in [final_killed, poisoned_player] if p]
                self.update_alive_players(night_deaths)

                # 死亡公告
                if not night_deaths:
                    self.moderator.log("昨夜平安无事，无人死亡。")
                else:
                    self.moderator.log(f"昨夜，{'、'.join(night_deaths)}不幸遇害。")

                # 检查胜负
                winner = check_winning(self.alive_players, self.roles)
                if winner:
                    self.moderator.log(f"游戏结束！{winner}")
                    return

                # 白天阶段
                voted_out = await self.day_phase(round_num)

                # 猎人阶段
                hunter_shot = await self.hunter_phase(voted_out)

                # 更新玩家列表
                day_deaths = [p for p in [voted_out, hunter_shot] if p]
                self.update_alive_players(day_deaths)

                # 检查胜负
                winner = check_winning(self.alive_players, self.roles)
                if winner:
                    self.moderator.log(f"游戏结束！{winner}")
                    return

                print(f"第{round_num}轮结束，存活玩家：{format_player_list(self.alive_players)}")

        except Exception as e:
            print(f"游戏运行出错：{e}")
            import traceback
            traceback.print_exc()


async def main():
    print("欢迎来到三国狼人杀！")

    # 创建并运行游戏
    game = ThreeKingdomsWerewolfGame()
    await game.run_game()


if __name__ == "__main__":
    asyncio.run(main())
