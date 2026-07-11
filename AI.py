import os
import re
import json
import subprocess
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# ================== 配置加载 ==================
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL")
API_MODEL = os.getenv("API_MODEL")

if not all([API_KEY, API_BASE_URL, API_MODEL]):
    raise ValueError("请在 .env 中设置 API_KEY, API_BASE_URL, API_MODEL")

client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)

# ================== 会话存储目录 ==================
SCRIPT_DIR = Path(__file__).parent
SESSION_DIR = SCRIPT_DIR / ".MY_CODE_AGENT"
SESSION_DIR.mkdir(exist_ok=True)

# ================== 工具函数 ==================
def exec_powershell(command: str, timeout: int = 30) -> str:
    try:
        result = subprocess.run(
            ["powershell.exe", "-Command", command],
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False
        )
        output = result.stdout
        if result.stderr:
            output += "\n[stderr]\n" + result.stderr
        return output.strip() or "[命令执行成功，无输出]"
    except subprocess.TimeoutExpired:
        return f"命令执行超时{timeout}秒，已强制中断：{command}"
    except Exception as e:
        return f"执行失败：{str(e)}"







# ================== 工具定义 ==================
tools = [
    {
        "type": "function",
        "function": {
            "name": "exec_powershell",
            "description": "执行一条 PowerShell 命令，并返回命令的输出（包含 stdout 和 stderr）。当前终端环境为 PowerShell。",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "要执行的 PowerShell 命令字符串，例如 'Get-Process'"}
                },
                "required": ["command"]
            }
        }
    },


]

function_map = {
    "exec_powershell": exec_powershell,
}

# ================== 系统提示（动态） ==================
def build_system_prompt():
    cwd = os.getcwd()
    return f"""你是一个运行在 Windows 系统上的 AI 代码助手，当前终端环境为 **PowerShell**。
你的任务是根据用户的需求，使用提供的工具来执行 PowerShell 命令、读取或写入文件。

**当前工作目录是：{cwd}**
所有相对路径都将基于此目录。例如，若你使用相对路径 'data.txt'，实际指向的是 '{cwd}/data.txt'。

**重要规则**：
1. 你必须**严格按照**以下工具定义来调用函数，不要编造函数名或参数。
2. 工具调用结果会以函数返回值的形式反馈给你，你需要根据这些结果继续推理，直到给出最终回答。
3. 当用户的问题可以直接用 PowerShell 解决时，优先使用 `exec_powershell` 工具。
4. **注意：只有 `exec_powershell` 一个工具！** 所有文件操作（读取、写入、编辑）都需要通过 PowerShell 命令完成。例如：
   - 读取文件：`Get-Content "文件路径"`
   - 写入文件：`Set-Content -Path "文件路径" -Value "内容"`
   - 编辑文件：可以先用 `Get-Content` 读取，用 `-replace` 替换，再用 `Set-Content` 写回
5. 在调用工具前，请仔细思考：当前是否缺少信息？是否需要先执行某些命令来获取信息？
6. 你的最终回答应该清晰、简洁，并包含关键信息（例如命令执行结果、文件内容等）。
7. 如果工具返回错误，请根据错误信息调整操作或向用户说明失败原因。
8. **特别注意**：每次调用 `exec_powershell` 都会启动一个**新的 PowerShell 进程**，该进程的工作目录独立于之前的调用。因此，之前的 `cd` 命令不会影响后续命令。若需要在特定目录执行命令，请使用绝对路径，或在命令中显式 `cd` 到目标目录（但只对该命令有效）。

记住：你只负责决定调用哪些工具，工具的实际执行由系统完成。你的输出格式必须符合工具调用的 JSON 规范。
"""

# ================== 会话管理 ==================
class SessionManager:
    def __init__(self):
        self.messages = []
        self.title = "未命名会话"
        self.session_file = None
        self._init_new_session()

    def _init_new_session(self):
        """初始化新会话（清空历史，保留系统提示）"""
        self.messages = [{"role": "system", "content": build_system_prompt()}]
        self.title = "未命名会话"
        self.session_file = None

    def get_session_files(self):
        """返回所有会话文件信息，按修改时间排序，每个为 (序号, 路径, 标题, 更新时间)"""
        files = sorted(SESSION_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime)
        sessions = []
        for idx, f in enumerate(files, 1):
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    title = data.get("title", "未命名")
                    updated = data.get("updated_at", datetime.fromtimestamp(f.stat().st_mtime).isoformat())
            except:
                title = "损坏的会话"
                updated = datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            sessions.append((idx, f, title, updated))
        return sessions

    def load_session(self, file_path: Path):
        """加载指定会话文件，并显示最近历史"""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(fp)
        self.title = data.get("title", "未命名会话")
        system_prompt = build_system_prompt()
        self.messages = [{"role": "system", "content": system_prompt}] + data.get("messages", [])
        self.session_file = file_path
        print(f"✅ 已恢复会话：{self.title}")
        history = [m for m in self.messages if m["role"] != "system"]
        if history:
            print("\n📜 最近对话（显示最后5条）：")
            for msg in history[-5:]:
                role = msg["role"]
                content = msg.get("content", "")
                if role == "user":
                    prefix = "👤 用户"
                elif role == "assistant":
                    prefix = "🤖 AI"
                elif role == "tool":
                    prefix = "🔧 工具"
                else:
                    prefix = role
                if len(content) > 150:
                    content = content[:150] + "..."
                print(f"  {prefix}: {content}")
        else:
            print("  （暂无历史消息）")
        print("（输入消息继续对话，或输入 /history 查看完整历史）")

    def _sanitize_filename(self, name: str) -> str:
        """将标题转换为合法文件名（保留中文，移除非法字符）"""
        illegal_chars = r'[<>:"/\\|?*]'
        name = re.sub(illegal_chars, '', name)
        name = name.strip('. ')
        if not name:
            name = "未命名会话"
        if len(name) > 50:
            name = name[:50]
        return name

    def save_current(self):
        """保存当前会话到文件，如果标题已更新且文件名仍为'未命名会话'则自动重命名"""
        if not self.messages:
            return

        safe_title = self._sanitize_filename(self.title)
        if safe_title == "未命名会话":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"{safe_title}_{timestamp}.json"
        else:
            new_filename = f"{safe_title}.json"

        if self.session_file is None:
            base_path = SESSION_DIR / new_filename
            counter = 1
            while base_path.exists():
                name, ext = os.path.splitext(new_filename)
                base_path = SESSION_DIR / f"{name}_{counter}{ext}"
                counter += 1
            self.session_file = base_path
        else:
            # 如果已有文件，但文件名以"未命名会话"开头，且当前标题已更新，则重命名
            current_name = self.session_file.stem
            if current_name.startswith("未命名会话") and safe_title != "未命名会话":
                new_path = SESSION_DIR / new_filename
                counter = 1
                while new_path.exists():
                    name, ext = os.path.splitext(new_filename)
                    new_path = SESSION_DIR / f"{name}_{counter}{ext}"
                    counter += 1
                # 重命名文件
                self.session_file.rename(new_path)
                self.session_file = new_path
                print(f"📝 会话文件已重命名为：{self.session_file.name}")

        save_data = {
            "title": self.title,
            "messages": self.messages[1:],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        with open(self.session_file, "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)

# ================== 流式响应处理 ==================
def process_stream(stream):
    content = ""
    tool_calls_dict = {}

    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta

        if delta.content:
            print(delta.content, end="", flush=True)
            content += delta.content

        if delta.tool_calls:
            for tc in delta.tool_calls:
                idx = tc.index
                if idx not in tool_calls_dict:
                    tool_calls_dict[idx] = {"id": None, "name": None, "arguments": ""}
                if tc.id:
                    tool_calls_dict[idx]["id"] = tc.id
                if tc.function:
                    if tc.function.name:
                        tool_calls_dict[idx]["name"] = tc.function.name
                    if tc.function.arguments:
                        tool_calls_dict[idx]["arguments"] += tc.function.arguments

    if content:
        print()

    tool_calls = []
    for idx in sorted(tool_calls_dict.keys()):
        item = tool_calls_dict[idx]
        if item["id"] and item["name"]:
            tool_calls.append({
                "id": item["id"],
                "type": "function",
                "function": {
                    "name": item["name"],
                    "arguments": item["arguments"]
                }
            })
    return content, tool_calls

# ================== 主程序 ==================
def main():
    session = SessionManager()
    print(f"🤖 Code Agent (PowerShell) 已启动。当前工作目录：{os.getcwd()}")
    print("输入 '/help' 查看命令。")

    while True:
        user_input = input("\n你: ").strip()
        if not user_input:
            continue

        # ---------- 处理命令 ----------
        if user_input.startswith("/"):
            parts = user_input.split()
            cmd = parts[0].lower()

            if cmd == "/exit" or cmd == "/quit":
                session.save_current()
                print("再见！")
                break

            elif cmd == "/sessions":
                if len(parts) > 1:
                    try:
                        num = int(parts[1])
                        sessions = session.get_session_files()
                        if 1 <= num <= len(sessions):
                            _, file_path, _, _ = sessions[num-1]
                            session.load_session(file_path)
                        else:
                            print(f"❌ 无效序号，有效范围 1 ~ {len(sessions)}")
                    except ValueError:
                        print("❌ 请提供数字序号，例如 /sessions 2")
                else:
                    sessions = session.get_session_files()
                    if not sessions:
                        print("📭 暂无会话记录。")
                    else:
                        print("📋 已保存的会话：")
                        for idx, f, title, updated in sessions:
                            print(f"  {idx}. {title} (更新于 {updated})")
                continue

            elif cmd == "/history":
                history = [m for m in session.messages if m["role"] != "system"]
                if not history:
                    print("📭 暂无对话历史。")
                else:
                    print("\n📜 === 完整对话历史 ===")
                    for i, msg in enumerate(history, 1):
                        role = msg["role"]
                        content = msg.get("content", "")
                        if role == "user":
                            prefix = f"{i}. 👤 用户"
                        elif role == "assistant":
                            prefix = f"{i}. 🤖 AI"
                        elif role == "tool":
                            prefix = f"{i}. 🔧 工具"
                        else:
                            prefix = f"{i}. {role}"
                        if len(content) > 500:
                            content = content[:500] + "..."
                        print(f"{prefix}: {content}")
                    print("=====================")
                continue

            elif cmd == "/new":
                session.save_current()
                session._init_new_session()
                print("✨ 已开始新会话。")
                continue

            elif cmd == "/save":
                session.save_current()
                print(f"💾 当前会话已保存至 {session.session_file.name}")
                continue

            elif cmd == "/help":
                print("可用命令：")
                print("  /sessions          - 列出所有已保存的会话")
                print("  /sessions <序号>   - 恢复到指定会话")
                print("  /history           - 查看当前会话完整历史")
                print("  /new               - 开始新会话（当前会话自动保存）")
                print("  /save              - 手动保存当前会话")
                print("  /exit 或 /quit     - 退出并保存当前会话")
                continue

            else:
                print(f"❌ 未知命令：{cmd}，输入 /help 查看帮助")
                continue

        # ---------- 正常对话 ----------
        # 如果是第一条消息（当前只有系统提示），则用用户输入的前10个字符作为标题
        if len(session.messages) == 1:
            # 截取前10个字符（支持中文，一个汉字算一个字符）
            title_candidate = user_input[:10].strip()
            session.title = title_candidate if title_candidate else "未命名会话"

        session.messages.append({"role": "user", "content": user_input})

        while True:
            try:
                stream = client.chat.completions.create(
                    model=API_MODEL,
                    messages=session.messages,
                    tools=tools,
                    tool_choice="auto",
                    stream=True,
                    timeout=60
                )
            except Exception as e:
                print(f"\n❌ API 调用失败：{type(e).__name__}: {e}")
                break

            assistant_content, tool_calls = process_stream(stream)

            assistant_message = {"role": "assistant", "content": assistant_content}
            if tool_calls:
                assistant_message["tool_calls"] = tool_calls
            session.messages.append(assistant_message)

            if not tool_calls:
                break

            for tool_call in tool_calls:
                func_name = tool_call["function"]["name"]
                func_args = json.loads(tool_call["function"]["arguments"])

                if func_name not in function_map:
                    result = f"错误：未知工具 '{func_name}'"
                else:
                    print(f"\n🔧 调用工具 {func_name} 参数：{func_args}")
                    result = function_map[func_name](**func_args)
                    print(f"📤 工具返回：{result[:200]}{'...' if len(result)>200 else ''}")

                session.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": result
                })

            session.save_current()

        session.save_current()

if __name__ == "__main__":
    main()

