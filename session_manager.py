import os
import re
import json
from pathlib import Path
from datetime import datetime
from config import SESSION_DIR
from prompt_builder import build_system_prompt

# ================== 会话管理器 ==================
class SessionManager:
    def __init__(self):
        self.messages = []
        self.title = "未命名会话"
        self.session_file = None
        self._init_new_session()

    def _init_new_session(self):
        """初始化新会话（清空历史，保留系统提示词）"""
        self.messages = [{"role": "system", "content": build_system_prompt()}]
        self.title = "未命名会话"
        self.session_file = None

    def get_session_files(self):
        """返回所有会话文件信息，按修改时间排序"""
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
        """加载指定会话文件并显示近期历史"""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.title = data.get("title", "未命名会话")
        system_prompt = build_system_prompt()
        self.messages = [{"role": "system", "content": system_prompt}] + data.get("messages", [])
        self.session_file = file_path
        print(f"已恢复会话: {self.title}")
        history = [m for m in self.messages if m["role"] != "system"]
        if history:
            print("\n=== 近期对话（最近5条消息）===")
            for msg in history[-5:]:
                role = msg["role"]
                content = msg.get("content", "")
                if role == "user":
                    prefix = "用户"
                elif role == "assistant":
                    prefix = "AI"
                elif role == "tool":
                    prefix = "工具"
                else:
                    prefix = role
                if len(content) > 150:
                    content = content[:150] + "..."
                print(f"  [{prefix}] {content}")
        else:
            print("  (无历史消息)")
        print("(输入消息以继续，或输入 /history 查看完整历史)")

    def _sanitize_filename(self, name: str) -> str:
        """将标题转换为有效的文件名（移除非法字符）"""
        illegal_chars = r'[<>:\"/\\\\|?*]'
        name = re.sub(illegal_chars, '', name)
        name = name.strip('. ')
        if not name:
            name = "未命名会话"
        if len(name) > 50:
            name = name[:50]
        return name

    def save_current(self):
        """保存当前会话到文件，如果标题改变则自动重命名"""
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
            current_name = self.session_file.stem
            if current_name.startswith("未命名会话") and safe_title != "未命名会话":
                new_path = SESSION_DIR / new_filename
                counter = 1
                while new_path.exists():
                    name, ext = os.path.splitext(new_filename)
                    new_path = SESSION_DIR / f"{name}_{counter}{ext}"
                    counter += 1
                self.session_file.rename(new_path)
                self.session_file = new_path
                print(f"会话文件已重命名为: {self.session_file.name}")

        save_data = {
            "title": self.title,
            "messages": self.messages[1:],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        with open(self.session_file, "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
