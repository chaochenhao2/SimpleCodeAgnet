import subprocess
import os

# ================== 工具函数 ==================
def exec_powershell(command: str, timeout: int = 30) -> str:
    '''执行 PowerShell 命令'''
    try:
        # 前置设置 UTF-8 编码，保证输出能被正确解码
        cmd = f"[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; $OutputEncoding = [System.Text.Encoding]::UTF8; {command}"
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", cmd],
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
            "name": "exec_powershell",
            "description": "执行 PowerShell 命令并返回输出（包括标准输出和标准错误）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "PowerShell 命令字符串，例如 'Get-Process'"}
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
                    "path": {"type": "string", "description": "文件路径，例如 'data.txt' 或 'C:/Users/name/file.txt'"}
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
    "exec_powershell": exec_powershell,
    "read_file": read_file,
    "write_file": write_file,
}
