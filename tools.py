import subprocess
import os

# ================== 工具函数 ==================
def exec_powershell(command: str, timeout: int = 30) -> str:
    '''执行 PowerShell 命令'''
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
            output += "\n[标准错误]\n" + result.stderr
        return output.strip() or "[命令执行成功，无输出]"
    except subprocess.TimeoutExpired:
        return f"命令超时 ({timeout} 秒): {command}"
    except Exception as e:
        return f"执行失败: {str(e)}"


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
    }
]

function_map = {
    "exec_powershell": exec_powershell,
}
