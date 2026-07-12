# AI 代码助手 (PowerShell)

一个在 Windows 系统上使用 PowerShell 终端运行的模块化 AI 代码助手。

## 项目结构

`
My_Agent/
├── AI.py                 # 主入口文件（Rich TUI）
├── config.py             # 配置和 API 设置
├── tools.py              # 工具定义（PowerShell / 文件读写）
├── session_manager.py    # 会话管理（保存/加载/历史）
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
- read_file(): 读取文本文件
- write_file(): 写入文本文件
- AI 函数调用的工具定义和映射

### 3. session_manager.py
- SessionManager 类管理对话会话
- 功能包括:
  - 自动将会话保存为 JSON 文件
  - 加载/切换会话
  - 查看对话历史
  - 清理会话标题作为文件名

### 4. prompt_builder.py
- build_system_prompt(): 生成动态系统提示词
- 包含当前工作目录
- 包含使用规则和指南

### 5. AI.py (主程序)
- Rich 增强的 TUI 界面（色彩 / 面板 / 表格 / Markdown 渲染）
- 命令处理（/help, /sessions, /history 等）
- 流式显示 AI 回复，支持 Markdown 实时渲染
- 带工具执行的主对话循环

## 可用命令

- `/sessions` - 列出所有已保存的会话
- `/sessions <num>` - 加载特定会话
- `/history` - 查看完整对话历史
- `/new` - 开始新会话（自动保存当前会话）
- `/save` - 手动保存当前会话
- `/clear` - 清屏
- `/exit` 或 `/quit` - 退出并保存

## 设置步骤

1. 创建 `.env` 文件，内容如下:
```
API_KEY=你的_api密钥
API_BASE_URL=你的_api地址
API_MODEL=你的模型名称
```

2. 安装依赖:
```bash
pip install python-dotenv openai rich
```

3. 运行助手:
```bash
python AI.py
```

## 特性

- 模块化架构
- 会话持久化（JSON 格式自动保存）
- Rich TUI 界面（色彩 / 面板 / 表格 / Markdown 渲染）
- 流式响应 + Markdown 实时渲染
- 工具/函数调用（PowerShell 命令 + 文件读写）
- 多会话管理（新建 / 保存 / 加载 / 切换）
- 自动保存功能

## 注意事项

- 每次 `exec_powershell` 调用都会启动新的 PowerShell 进程，之前的 `cd` 不影响后续调用
- 请使用绝对路径或在命令中显式使用 `cd`
- 会话以 JSON 格式存储在 `.MY_CODE_AGENT/` 目录下
- 文件读写请使用 `read_file` / `write_file` 工具（比 PowerShell 方式更可靠）
