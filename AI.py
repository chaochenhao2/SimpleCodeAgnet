# -*- coding: utf-8 -*-
import os
import json
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.live import Live
from rich.text import Text
from rich.rule import Rule

from config import client, API_MODEL, SESSION_DIR
from tools import tools, function_map
from session_manager import SessionManager

console = Console()

def print_help():
    help_text = """
**可用命令:**

- `/sessions`          : 列出所有已保存的会话
- `/sessions <num>`    : 通过编号加载特定会话
- `/history`           : 查看完整对话历史
- `/new`               : 开始新会话（自动保存当前会话）
- `/save`              : 手动保存当前会话
- `/clear`             : 清屏
- `/exit` 或 `/quit`   : 退出并保存当前会话
"""
    console.print(Panel(help_text.strip(), title="[bold blue]帮助[/bold blue]", border_style="blue"))

def print_sessions(sessions):
    table = Table(title="[bold green]已保存的会话[/bold green]", show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=3)
    table.add_column("标题", style="cyan")
    table.add_column("更新时间", style="yellow")
    
    for idx, path, title, updated in sessions:
        try:
            dt = datetime.fromisoformat(updated)
            time_str = dt.strftime("%Y-%m-%d %H:%M")
        except:
            time_str = updated[:19] if len(updated) > 19 else updated
            
        table.add_row(str(idx), title, time_str)
        
    console.print(table)

def print_history(session):
    history = [m for m in session.messages if m["role"] != "system"]
    if not history:
        console.print("[yellow]无对话历史。[/yellow]")
        return

    console.print(Rule("[bold cyan]对话历史[/bold cyan]", style="cyan"))
    
    for i, msg in enumerate(history, 1):
        role = msg["role"]
        content = msg.get("content", "")
        
        if role == "user":
            style = "bold blue"
            prefix = "用户"
        elif role == "assistant":
            style = "bold green"
            prefix = "AI"
        elif role == "tool":
            style = "bold yellow"
            prefix = "工具"
        else:
            style = "bold white"
            prefix = role
            
        if len(content) > 500:
            display_content = content[:500] + "\n[内容过长，已截断...]"
        else:
            display_content = content
            
        console.print(f"[bold]{i}. {prefix}:[/bold] {display_content}")
        
    console.print(Rule(style="cyan"))

def main():
    session = SessionManager()
    
    console.clear()
    console.print(Panel.fit(
        "[bold cyan]Code Agent TUI[/bold cyan]\n"
        "[dim]Powered by Rich & OpenAI API[/dim]\n"
        f"[dim]Working Directory: {os.getcwd()}[/dim]",
        title="[bold green]欢迎使用[/bold green]",
        subtitle="输入 /help 查看命令",
        border_style="green"
    ))
    
    while True:
        try:
            user_input = Prompt.ask("[bold blue]你[/bold blue]")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]退出中...[/yellow]")
            break
            
        if not user_input:
            continue

        if user_input.startswith("/"):
            parts = user_input.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else None

            if cmd in ["/exit", "/quit"]:
                session.save_current()
                console.print("[bold red]再见！[/bold red]")
                break

            elif cmd == "/sessions":
                sessions = session.get_session_files()
                if not sessions:
                    console.print("[yellow]未找到保存的会话。[/yellow]")
                else:
                    print_sessions(sessions)
                    if arg:
                        try:
                            num = int(arg)
                            if 1 <= num <= len(sessions):
                                _, file_path, _, _ = sessions[num-1]
                                session.load_session(file_path)
                            else:
                                console.print(f"[red]无效数字，有效范围: 1 ~ {len(sessions)}[/red]")
                        except ValueError:
                            console.print("[red]请提供数字，例如: /sessions 2[/red]")

            elif cmd == "/history":
                print_history(session)

            elif cmd == "/new":
                session.save_current()
                session._init_new_session()
                console.print("[bold green]已开始新会话。[/bold green]")

            elif cmd == "/save":
                session.save_current()
                console.print(f"[bold green]会话已保存到 {session.session_file.name}[/bold green]")

            elif cmd == "/clear":
                console.clear()
                console.print(Panel.fit(
                    "[bold cyan]Code Agent TUI[/bold cyan]\n"
                    f"[dim]Working Directory: {os.getcwd()}[/dim]",
                    title="[bold green]欢迎使用[/bold green]",
                    subtitle="输入 /help 查看命令",
                    border_style="green"
                ))

            elif cmd == "/help":
                print_help()

            else:
                console.print(f"[red]未知命令: {cmd}，输入 /help 获取帮助[/red]")
            continue

        if len(session.messages) == 1:
            title_candidate = user_input[:20].strip()
            session.title = title_candidate if title_candidate else "未命名会话"

        console.print(f"[bold blue]你:[/bold blue] {user_input}")
        session.messages.append({"role": "user", "content": user_input})

        assistant_content = ""
        tool_calls_dict = {}
        
        display_text = Text()
        display_text.append("AI: ", style="bold green")
        
        with console.status("[bold yellow]AI 正在思考...[/bold yellow]") as status:
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
                console.print(f"\n[bold red]API 调用失败: {e}[/bold red]")
                session.messages.pop()
                continue

            content_buffer = ""
            tool_calls_buffer = {}
            
            with Live(display_text, refresh_per_second=12, vertical_overflow="visible") as live:
                try:
                    for chunk in stream:
                        if not chunk.choices:
                            continue
                        delta = chunk.choices[0].delta

                        if delta.content:
                            char = delta.content
                            content_buffer += char
                            display_text.append(char)
                            live.update(display_text)
                            
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
                    live.update(Text(f"[bold red]流式传输错误: {e}[/bold red]"))
                    console.print()
                    break

        console.print()
            
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
            session.save_current()
            continue

        for tool_call in tool_calls:
            func_name = tool_call["function"]["name"]
            func_args = json.loads(tool_call["function"]["arguments"])

            console.print(f"\n[bold yellow]调用工具: {func_name}[/bold yellow]")
            console.print(f"[dim]参数: {func_args}[/dim]")
            
            if func_name not in function_map:
                result = f"错误: 未知工具 '{func_name}'"
            else:
                try:
                    result = function_map[func_name](**func_args)
                except Exception as e:
                    result = f"执行工具时发生错误: {e}"
                    
            preview = result[:200] + "..." if len(result) > 200 else result
            console.print(Panel(result if len(result) < 200 else preview, title=f"[bold green]{func_name} 返回[/bold green]", border_style="green"))

            session.messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": result
            })

        session.save_current()

if __name__ == "__main__":
    main()
