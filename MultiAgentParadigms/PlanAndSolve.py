import os
import ast
from dotenv import load_dotenv
from rich.console import Console
from typing import List, Dict
from BasicClient import HelloAgentLLM
from ToolsExecutor import ToolExecutor
from SearchTools import search
from GenerateFileTools import save_console_to_markdown

try:
    load_dotenv()
except FileNotFoundError:
    console.print("警告：未找到 .env 文件，将使用系统环境变量。")
except Exception as e:
    console.print(f"警告：加载 .env 文件时出错: {e}")

console = Console(record=True)

# 假定 BasicCLient.py 中的 HelloAgentLLM 类已经定义好
# from BasicClient import HelloAgentLLM

PLANNER_PROMPT_TEMPLATE = """
你是一个拥有能力调用外部工具的顶级的AI规划专家。你的任务是将用户提出的复杂问题分解成一个由多个简单步骤组成的行动计划并指定需要用到的外部工具。
请确保计划中的每个步骤都是一个独立的、可执行的子任务，并且严格按照逻辑顺序排列。
你的输出必须是一个Python列表，其中每个元素都是一个描述子任务的字符串。

可用工具如下:
{tools}

问题: {question}

请严格按照以下格式输出你的计划,```python与```作为前后缀是必要的:
```python
["步骤1", "步骤2", "步骤3", ...]
```
"""

class Planner:
    def __init__(self, llm_client: HelloAgentLLM, tool_executor: ToolExecutor):
        self.llm_client = llm_client
        self.tool_executor = tool_executor

    def plan(self, question: str) -> list[str]:
        """
        根据用户问题生成一个行动计划
        """
        tools_desc = self.tool_executor.getAvailableTools()
        prompt = PLANNER_PROMPT_TEMPLATE.format(tools=tools_desc, question=question)

        # 为了生成计划，我们构建一个简单的消息列表
        messages = [{"role": "user", "content": prompt}]

        console.print("--- 正在生成计划 ---")
        # 使用流式输出来获取完整计划
        response_text = self.llm_client.think(messages=messages) or ""

        console.print(f"✅ 计划已生成:\n{response_text}")

        # 解析LLM输出列表字符串
        try:
            # 找到```python和```之间的内容
            plan_str = response_text.split("```python")[1].split("```")[0].strip()
            # 使用ast.literal_eval来安全的执行字符串，将其转换为Python列表
            plan = ast.literal_eval(plan_str)
            return plan if isinstance(plan, list) else []
        except (ValueError, SyntaxError, IndexError) as e:
            console.print(f"❌ 解析计划时出错: {e}")
            console.print(f"原始响应: {response_text}")
            return []
        except Exception as e:
            console.print(f"❌ 解析计划时发生未知错误: {e}")
            return []

EXECUTOR_PROMPT_TEMPLATE = """
你是一位有能力调用外部工具的顶级的AI执行专家。你的任务是严格按照给定的计划，一步步地解决问题。
你将收到原始问题、完整的计划、以及到目前为止已经完成的步骤和结果。
请你专注于解决“当前步骤”，并仅输出该步骤的最终答案，不要输出任何额外的解释或对话。

可用工具如下:
{tools}

# 原始问题:
{question}

# 完整计划:
{plan}

# 历史步骤与结果:
{history}

# 当前步骤:
{current_step}

请仅输出针对“当前步骤”的回答:
"""

class Executor:
    def __init__(self, llm_client: HelloAgentLLM, tool_executor: ToolExecutor):
        self.llm_client = llm_client
        self.tool_executor = tool_executor

    def execute(self, question: str, plan: list[str]) -> str:
        """
        根据计划，逐步执行并解决问题
        """
        history = "" #用于存储历史步骤和结果的字符串

        console.print("\n--- 正在执行计划 ---")

        for i, step in enumerate(plan):
            console.print(f"\n-> 正在执行步骤 {i+1}/{len(plan)}: {step}")

            tools_desc = self.tool_executor.getAvailableTools()
            prompt = EXECUTOR_PROMPT_TEMPLATE.format(
                tools=tools_desc,
                question=question,
                plan=plan,
                history=history if history else "无",
                current_step=step
            )

            messages = [{"role": "user", "content": prompt}]

            response_text = self.llm_client.think(messages=messages) or ""

            # 更新历史记录，为下一步做准备
            history += f"步骤 {i+1}: {step}\n结果: {response_text}\n\n"

            console.print(f"✅ 步骤 {i+1} 已完成:\n{response_text}")

        # 循环结束后，最后一步的响应就是最终答案
        final_answer = response_text
        return final_answer

class PlanAndSolveAgent:
    def __init__(self, llm_client: HelloAgentLLM, tool_executor: ToolExecutor):
        """
        初始化智能体，同时创建规划器和执行器示例
        """
        self.llm_client = llm_client
        self.planner = Planner(self.llm_client, tool_executor)
        self.executor = Executor(self.llm_client, tool_executor)

    def run(self, question: str):
        """
        运行智能体的完整流程：先规划，后执行。
        """
        console.print(f"\n--- 开始处理问题 ---\n问题: {question}")

        # 1. 调用规划器生成计划
        plan = self.planner.plan(question)

        # 检查计划是否成功生成
        if not plan:
            console.print("\n--- 任务终止 --- \n无法生成有效的行动计划。")
            return

        # 2. 调用执行器执行计划并获取结果
        final_answer = self.executor.execute(question, plan)

        console.print(f"\n--- 任务处理完毕 --- \n最终答案: {final_answer}")

if __name__ == "__main__":
    try:
        llm_client = HelloAgentLLM()
        tool_executor = ToolExecutor()
        # search_desc = "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
        # tool_executor.registerTool("Search", search_desc, search)
        save_markdown_desc = "一个markdown文件生成工具，使用时为工具传递保存时的文件夹与文件名。当你需要将控制台整体的输出形成一个markdown文件并保存在指定目录中时，应使用此工具。"
        tool_executor.registerTool("SaveMarkdown", save_markdown_desc, save_console_to_markdown)
        agent = PlanAndSolveAgent(llm_client, tool_executor)
        question = "上交所所有上市公司或者根据上市公司编号或名称的日内k线数据的官方接口是什么？将控制台整体的输出形成一个可直接保存在/Users/a6666/learn/agent/charpter4/文件夹的markdown文件并将形成的markdown文件保存在/Users/a6666/learn/agent/charpter4/文件夹中"
        agent.run(question)
    except Exception as e:
        console.print(f"❌ 错误：{e}")

