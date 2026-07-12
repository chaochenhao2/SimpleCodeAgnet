# -*- coding: utf-8 -*-
import os
import sys
import json
from datetime import datetime

# 设置控制台编码为 UTF-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleCP(65001)
        kernel32.SetConsoleOutputCP(65001)
    except:
        pass

from config import client, API_MODEL
from tools import tools, function_map
from session_manager import SessionManager

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def show_welcome():
    clear_screen()
    print("=" * 60)
    print("  Code Agent")
    print(f"  {os.getcwd()}")
    print("=" * 60)
    print()

def render_conversation(session):
    clear_screen()
    print("=" * 60)
    print(f"  Code Agent  |  {os.getcwd()}")
    print("=" * 60)
    print()

    for msg in session.messages:
        if msg["role"] == "system":
            continue
        role = msg["role"]
        content = msg.get("content", "")
        if content:
            content = content.strip()

        if role == "user":
            print(f"[你] {content}")
        elif role == "assistant":
            if content:
                print(content)
            if msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    args_summary = str(json.loads(tc["function"]["arguments"]))[:80]
                    print(f"  [调用: {tc['function']['name']}({args_summary})]")
        elif role == "tool":
            preview = (content[:150] + "...") if len(content) > 150 else content
            print(f"  [工具返回] {preview}")

    print("-" * 60)

def print_help():
    print()
    print("可用命令:")
    print("  /sessions        - 列出所有已保存的会话")
    print("  /sessions <num>  - 加载指定编号的会话")
    print("  /history         - 查看完整对话历史")
    print("  /new             - 开始新会话")
    print("  /save            - 手动保存当前会话")
    print("  /clear           - 清屏")
    print("  /exit 或 /quit   - 退出")
    print()

def print_sessions(sessions):
    print()
    print(f"{'#':>3} | 标题                                   | 更新时间")
    print("-" * 70)
    for idx, path, title, updated in sessions:
        try:
            dt = datetime.fromisoformat(updated)
            time_str = dt.strftime("%Y-%m-%d %H:%M")
        except:
            time_str = str(updated)[:16]
        print(f"{idx:>3} | {title:<40} | {time_str}")
    print()

def print_history(session):
    history = [m for m in session.messages if m["role"] != "system"]
    if not history:
        print("无对话历史。")
        return

    print()
    print("=== 对话历史 ===")
    for i, msg in enumerate(history, 1):
        role = msg["role"]
        content = msg.get("content", "")
        if content:
            content = content.strip()

        if role == "user":
            prefix = "你"
        elif role == "assistant":
            prefix = "AI"
        elif role == "tool":
            prefix = "工具"
        else:
            prefix = role

        if len(content) > 500:
            content = content[:500] + "\n...内容过长，已截断"
        print(f"{i}. [{prefix}] {content}")
    print()

def main():
    session = SessionManager()
    show_welcome()

    while True:
        try:
            user_input = input("你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            parts = user_input.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else None

            if cmd in ["/exit", "/quit"]:
                session.save_current()
                print("再见！")
                break

            elif cmd == "/sessions":
                sessions = session.get_session_files()
                if not sessions:
                    print("未找到保存的会话。")
                else:
                    print_sessions(sessions)
                    if arg:
                        try:
                            num = int(arg)
                            if 1 <= num <= len(sessions):
                                _, file_path, _, _ = sessions[num-1]
                                session.load_session(file_path)
                            else:
                                print(f"无效数字，有效范围: 1 ~ {len(sessions)}")
                        except ValueError:
                            print("请提供数字，例如: /sessions 2")

            elif cmd == "/history":
                print_history(session)

            elif cmd == "/new":
                session.save_current()
                session._init_new_session()
                show_welcome()
                continue

            elif cmd == "/save":
                session.save_current()
                print(f"会话已保存到 {session.session_file.name}")

            elif cmd == "/clear":
                show_welcome()
                continue

            elif cmd == "/help":
                print_help()

            else:
                print(f"未知命令: {cmd}，输入 /help 获取帮助")

            input("--- 按 Enter 继续 ---")
            continue

        if len(session.messages) == 1:
            title_candidate = user_input[:20].strip()
            session.title = title_candidate if title_candidate else "未命名会话"

        session.messages.append({"role": "user", "content": user_input})
        render_conversation(session)

        # Agent 内循环：反复调用 AI 直到它给出最终回答（不再调用工具）
        while True:
            content_buffer = ""
            tool_calls_buffer = {}

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
                print(f"\nAPI 调用失败: {e}")
                session.messages.pop()
                break

            try:
                for chunk in stream:
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta

                    if delta.content:
                        char = delta.content
                        content_buffer += char
                        sys.stdout.write(char)
                        sys.stdout.flush()

                    if delta.tool_calls:
                        for tc in delta.tool_calls:
                            idx = tc.index
                            if idx not in tool_calls_buffer:
                                tool_calls_buffer[idx] = {"id": None, "name": None, "arguments": ""}
                            if tc.id:
                                tool_calls_buffer[idx]["id"] = tc.id
                            if tc.function:
                                if tc.function.name:
                                    tool_calls_buffer[idx]["name"] = tc.function.name
                                if tc.function.arguments:
                                    tool_calls_buffer[idx]["arguments"] += tc.function.arguments

            except Exception as e:
                sys.stdout.write(f"\n流式传输错误: {e}")

            sys.stdout.write("\n")
            sys.stdout.flush()

            assistant_message = {"role": "assistant", "content": content_buffer}
            tool_calls = []
            for idx in sorted(tool_calls_buffer.keys()):
                item = tool_calls_buffer[idx]
                if item["id"] and item["name"]:
                    tool_calls.append({
                        "id": item["id"],
                        "type": "function",
                        "function": {
                            "name": item["name"],
                            "arguments": item["arguments"]
                        }
                    })

            if tool_calls:
                assistant_message["tool_calls"] = tool_calls
            session.messages.append(assistant_message)

            if not tool_calls:
                # AI 给出最终回答，Agent 循环结束
                break

            # 执行工具，把结果加入消息后继续 Agent 循环
            for tool_call in tool_calls:
                func_name = tool_call["function"]["name"]
                func_args = json.loads(tool_call["function"]["arguments"])

                print(f"\n[调用工具] {func_name}  参数: {func_args}")

                if func_name not in function_map:
                    result = f"错误: 未知工具 '{func_name}'"
                else:
                    try:
                        result = function_map[func_name](**func_args)
                    except Exception as e:
                        result = f"执行工具时发生错误: {e}"

                preview = (result[:200] + "...") if len(result) > 200 else result
                print(f"[工具返回] {preview}")

                session.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": result
                })

        session.save_current()

if __name__ == "__main__":
    main()
