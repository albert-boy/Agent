ConstructFramework/
├── Framework/              # 主包
│   ├── core/                  # 核心组件
│   │   ├── llm.py             # LLM 基类与配置
│   │   ├── llm_adapters.py    # 三种适配器（OpenAI/Anthropic/Gemini）
│   │   ├── agent.py           # Agent 基类（Function Calling 架构）
│   │   ├── session_store.py   # 会话持久化
│   │   ├── lifecycle.py       # 异步生命周期
│   │   └── streaming.py       # SSE 流式输出
│   ├── agents/                # Agent 实现
│   │   ├── simple_agent.py    # SimpleAgent
│   │   ├── react_agent.py     # ReActAgent
│   │   ├── reflection_agent.py # ReflectionAgent
│   │   └── plan_solve_agent.py # PlanAndSolveAgent
│   ├── tools/                 # 工具系统
│   │   ├── registry.py        # 工具注册表
│   │   ├── response.py        # ToolResponse 协议
│   │   ├── circuit_breaker.py # 熔断器
│   │   ├── tool_filter.py     # 工具过滤（子代理机制）
│   │   └── builtin/           # 内置工具
│   │       ├── file_tools.py  # 文件工具（乐观锁）
│   │       ├── task_tool.py   # 子代理工具
│   │       ├── todowrite_tool.py # 进度管理
│   │       ├── devlog_tool.py # 决策日志
│   │       └── skill_tool.py  # Skills 知识外化
│   ├── context/               # 上下文工程
│   │   ├── history.py         # HistoryManager
│   │   ├── token_counter.py   # TokenCounter
│   │   ├── truncator.py       # ObservationTruncator
│   │   └── builder.py         # ContextBuilder
│   ├── observability/         # 可观测性
│   │   └── trace_logger.py    # TraceLogger
│   └── skills/                # Skills 系统
│       └── loader.py          # SkillLoader
├── docs/                      # 文档
├── examples/                  # 示例代码
└── tests/                     # 测试用例