import os
import json
from config import client, API_MODEL
from tools import tools, function_map
from session_manager import SessionManager
from response_handler import process_stream

# ================== 主程序 ==================
def main():
    session = SessionManager()
    print(f"Code Agent (PowerShell) 已启动。当前目录: {os.getcwd()}")
    print("输入 /help 查看可用命令。")

    while True:
        try:
            user_input = input("\n你: ").strip()
        except EOFError:
            print()
            break
            
        if not user_input:
            continue

        # ---------- 处理命令 ----------
        if user_input.startswith("/"):
            parts = user_input.split()
            cmd = parts[0].lower()

            if cmd in ["/exit", "/quit"]:
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
                            print(f"无效数字，有效范围: 1 ~ {len(sessions)}")
                    except ValueError:
                        print("请提供数字，例如: /sessions 2")
                else:
                    sessions = session.get_session_files()
                    if not sessions:
                        print("未找到保存的会话。")
                    else:
                        print("已保存的会话:")
                        for idx, f, title, updated in sessions:
                            print(f"  {idx}. {title} (更新于: {updated})")
                continue

            elif cmd == "/history":
                history = [m for m in session.messages if m["role"] != "system"]
                if not history:
                    print("无对话历史。")
                else:
                    print("\n=== 完整对话历史 ===")
                    for i, msg in enumerate(history, 1):
                        role = msg["role"]
                        content = msg.get("content", "")
                        if role == "user":
                            prefix = f"{i}. 用户"
                        elif role == "assistant":
                            prefix = f"{i}. AI"
                        elif role == "tool":
                            prefix = f"{i}. 工具"
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
                print("开始新会话。")
                continue

            elif cmd == "/save":
                session.save_current()
                print(f"会话已保存到 {session.session_file.name}")
                continue

            elif cmd == "/help":
                print("可用命令:")
                print("  /sessions          - 列出所有已保存的会话")
                print("  /sessions <num>    - 通过编号加载特定会话")
                print("  /history           - 查看完整对话历史")
                print("  /new               - 开始新会话（自动保存当前会话）")
                print("  /save              - 手动保存当前会话")
                print("  /exit 或 /quit    - 退出并保存当前会话")
                continue

            else:
                print(f"未知命令: {cmd}，输入 /help 获取帮助")
                continue

        # ---------- 正常对话 ----------
        if len(session.messages) == 1:
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
                print(f"\nAPI 调用失败: {type(e).__name__}: {e}")
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
                    result = f"错误: 未知工具 '{func_name}'"
                else:
                    print(f"\n调用工具 {func_name}，参数: {func_args}")
                    result = function_map[func_name](**func_args)
                    preview = result[:200] + "..." if len(result) > 200 else result
                    print(f"工具返回: {preview}")

                session.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": result
                })

            session.save_current()

        session.save_current()

if __name__ == "__main__":
    main()
