# AI 代码助手 (PowerShell)

一个在 Windows 系统上使用 PowerShell 终端运行的模块化 AI 代码助手。

## 项目结构

`
My_Agent/
├── AI.py                 # 主入口文件
├── config.py             # 配置和 API 设置
├── tools.py              # 工具定义和执行函数
├── session_manager.py    # 会话管理（保存/加载/历史）
├── response_handler.py   # 流式响应处理器
├── prompt_builder.py     # 动态系统提示词构建器
├── .env                  # 环境变量（API_KEY 等）
└── .MY_CODE_AGENT/       # 会话存储目录
`

## 模块说明

### 1. config.py
- 从 .env 加载环境变量
- 初始化 OpenAI 客户端
- 设置会话存储目录

### 2. tools.py
- exec_powershell(): 执行 PowerShell 命令
- AI 函数调用的工具定义
- 函数映射字典

### 3. session_manager.py
- SessionManager 类管理对话会话
- 功能包括:
  - 自动将会话保存为 JSON 文件
  - 加载/切换会话
  - 查看对话历史
  - 清理会话标题作为文件名

### 4. response_handler.py
- process_stream(): 处理流式 API 响应
- 同时提取文本内容和工具调用
- 实时输出显示

### 5. prompt_builder.py
- uild_system_prompt(): 生成动态系统提示词
- 包含当前工作目录
- 包含使用规则和指南

### 6. AI.py (主程序)
- 交互式命令行界面
- 命令处理（/help, /sessions, /history 等）
- 带工具执行的主对话循环

## 可用命令

- /sessions - 列出所有已保存的会话
- /sessions <num> - 加载特定会话
- /history - 查看完整对话历史
- /new - 开始新会话（自动保存当前会话）
- /save - 手动保存当前会话
- /exit 或 /quit - 退出并保存

## 设置步骤

1. 创建 .env 文件，内容如下:
`
API_KEY=你的_api密钥
API_BASE_URL=你的_api地址
API_MODEL=你的模型名称
`

2. 安装依赖:
`ash
pip install python-dotenv openai
`

3. 运行助手:
`ash
python AI.py
`

## 特性

- 模块化架构
- 会话持久化
- 流式响应
- 工具/函数调用
- PowerShell 集成
- 自动保存功能
- 命令行界面

## 注意事项

- 每次工具调用都会启动新的 PowerShell 进程
- 请使用绝对路径或在命令中显式使用 cd
- 会话以 JSON 格式存储在 .MY_CODE_AGENT/ 目录下
- 文件操作必须通过 exec_powershell 使用 PowerShell 命令完成
