from hello_agents import SimpoleAgent, HelloAgentsLLM
from dotenv import load_dotenv
from hello_agents.tools import CalculatorTool

load_dotenv()

llm = HelloAgentsLLM()

agent = SimpoleAgent(
    name="AI助手",
    llm=llm,
    system_prompt="你是一个有用的AI助手",
)

response = agent.run("你好！请介绍一下自己")
print(response)

calculator = CalculatorTool()

response = agent.run("帮我计算 2 + 8 * 9")
print(response)

print(f"历史消息数：{len(agent.get_history())}")