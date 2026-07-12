import subprocess
import os
import sys

# ================== 工具函数 ==================
def execute_command(command: str, timeout: int = 30) -> str:
    '''在系统 Shell 中执行命令（跨平台）'''
    try:
        if sys.platform == "win32":
            cmd = f"[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; $OutputEncoding = [System.Text.Encoding]::UTF8; {command}"
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", cmd],
                capture_output=True,
                encoding='utf-8',
                timeout=timeout,
                shell=False
            )
        else:
            result = subprocess.run(
                ["bash", "-c", command],
                capture_output=True,
                encoding='utf-8',
                timeout=timeout,
                shell=False
            )
        output = result.stdout or ""
        if result.stderr:
            output += "\n[stderr]\n" + result.stderr
        return output.strip() or "[命令执行成功，无输出]"
    except subprocess.TimeoutExpired:
        return f"命令超时 ({timeout} 秒): {command}"
    except Exception as e:
        return f"执行失败: {str(e)}"


def read_file(path: str) -> str:
    '''读取文本文件内容'''
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"读取文件失败: {e}"


def write_file(path: str, content: str) -> str:
    '''写入文本文件（覆盖模式）'''
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"文件已写入: {path}"
    except Exception as e:
        return f"写入文件失败: {e}"


# ================== 工具定义 ==================
tools = [
    {
        "type": "function",
        "function": {
            "name": "execute_command",
            "description": "在系统 Shell 中执行命令并返回输出（Windows 使用 PowerShell，macOS/Linux 使用 bash）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "要执行的 Shell 命令字符串"}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取文本文件内容（UTF-8 编码）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径，例如 'data.txt' 或 '/home/user/file.txt'"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "写入文本文件（UTF-8 编码，覆盖模式）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径，例如 'output.txt'"},
                    "content": {"type": "string", "description": "要写入的文件内容"}
                },
                "required": ["path", "content"]
            }
        }
    }
]

function_map = {
    "execute_command": execute_command,
    "read_file": read_file,
    "write_file": write_file,
}
