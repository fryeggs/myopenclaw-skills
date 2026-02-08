#!/usr/bin/env python3
"""
Session Manager - 会话管理模块

功能：
1. 会话创建、查询、切换
2. 继承原 topic 和历史摘要
3. 新会话自动读取关键信息

使用方式：
    python session_manager.py --list                    # 列出所有会话
    python session_manager.py --create --topic 464        # 创建新会话
    python session_manager.py --switch <session_id>       # 切换到指定会话
    python session_manager.py --info <session_id>        # 查看会话详情
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 路径配置
STATE_DIR = Path.home() / ".openclaw"
SESSIONS_DIR = STATE_DIR / ".sessions"
CURRENT_SESSION_FILE = STATE_DIR / ".current_session.json"


class SessionManager:
    """会话管理器"""

    def __init__(self):
        self.sessions_dir = SESSIONS_DIR
        self.current_session_file = CURRENT_SESSION_FILE
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def list_sessions(self) -> List[Dict]:
        """列出所有会话"""
        sessions = []
        if self.sessions_dir.exists():
            for session_file in sorted(self.sessions_dir.glob("*.json"), reverse=True):
                try:
                    data = json.loads(session_file.read_text())
                    sessions.append(data)
                except Exception:
                    continue
        return sessions

    def create_session(self, topic: Optional[str] = None, 
                       parent_session: Optional[str] = None) -> Dict:
        """创建新会话"""
        session_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()
        
        # 获取父会话的关键信息
        inherited_context = {}
        if parent_session:
            parent_file = self.sessions_dir / f"{parent_session}.json"
            if parent_file.exists():
                parent_data = json.loads(parent_file.read_text())
                inherited_context = parent_data.get("key_points", {})
        
        session = {
            "session_id": session_id,
            "created_at": now,
            "topic": topic or "default",
            "parent_session": parent_session,
            "inherited_context": inherited_context,
            "status": "active",
            "message_count": 0,
            "key_points": inherited_context.copy(),
        }
        
        # 保存会话文件
        session_file = self.sessions_dir / f"{session_id}.json"
        session_file.write_text(json.dumps(session, indent=2, ensure_ascii=False))
        
        # 更新当前会话
        self.set_current_session(session_id)
        
        return session

    def get_session(self, session_id: str) -> Optional[Dict]:
        """获取会话详情"""
        session_file = self.sessions_dir / f"{session_id}.json"
        if session_file.exists():
            return json.loads(session_file.read_text())
        return None

    def set_current_session(self, session_id: str):
        """设置当前会话"""
        self.current_session_file.write_text(json.dumps({
            "session_id": session_id,
            "set_at": datetime.now().isoformat()
        }, ensure_ascii=False))

    def get_current_session(self) -> Optional[Dict]:
        """获取当前会话"""
        if self.current_session_file.exists():
            return json.loads(self.current_session_file.read_text())
        return None

    def update_key_point(self, session_id: str, key: str, value: str):
        """更新关键信息"""
        session = self.get_session(session_id)
        if session:
            session["key_points"][key] = {
                "value": value,
                "updated_at": datetime.now().isoformat()
            }
            session_file = self.sessions_dir / f"{session_id}.json"
            session_file.write_text(json.dumps(session, indent=2, ensure_ascii=False))
            return True
        return False

    def get_inherited_context(self, session_id: str) -> Dict:
        """获取继承的上下文"""
        session = self.get_session(session_id)
        if session:
            return session.get("inherited_context", {})
        return {}


def main():
    parser = argparse.ArgumentParser(description="Session Manager")
    parser.add_argument("--list", action="store_true", help="列出所有会话")
    parser.add_argument("--create", action="store_true", help="创建新会话")
    parser.add_argument("--topic", type=str, help="指定 topic")
    parser.add_argument("--parent", type=str, help="父会话 ID")
    parser.add_argument("--switch", type=str, help="切换到指定会话")
    parser.add_argument("--info", type=str, help="查看会话详情")
    parser.add_argument("--current", action="store_true", help="查看当前会话")
    parser.add_argument("--json", action="store_true", help="JSON 输出模式")

    args = parser.parse_args()

    manager = SessionManager()

    if args.list:
        sessions = manager.list_sessions()
        if args.json:
            print(json.dumps(sessions))
        else:
            print(f"\n📋 会话列表 (共 {len(sessions)} 个):\n")
            for s in sessions:
                print(f"  • {s['session_id']} | {s['topic']} | {s['created_at'][:10]} | {s['status']}")
            print()

    elif args.create:
        session = manager.create_session(topic=args.topic, parent_session=args.parent)
        if args.json:
            print(json.dumps(session))
        else:
            print(f"\n✅ 会话已创建:")
            print(f"  ID: {session['session_id']}")
            print(f"  Topic: {session['topic']}")
            print(f"  继承的关键信息: {len(session['inherited_context'])} 条\n")
    
    elif args.switch:
        session = manager.get_session(args.switch)
        if session:
            manager.set_current_session(args.switch)
            print(f"\n🔄 已切换到会话 {args.switch}")
            print(f"   Topic: {session['topic']}")
            print(f"   继承上下文: {list(session['inherited_context'].keys())}\n")
        else:
            print(f"\n❌ 会话 {args.switch} 不存在\n")
    
    elif args.info:
        session = manager.get_session(args.info)
        if session:
            print(f"\n📝 会话详情:")
            print(f"  ID: {session['session_id']}")
            print(f"  Topic: {session['topic']}")
            print(f"  状态: {session['status']}")
            print(f"  消息数: {session['message_count']}")
            print(f"  创建时间: {session['created_at']}")
            print(f"  继承上下文: {len(session['inherited_context'])} 条\n")
        else:
            print(f"\n❌ 会话 {args.info} 不存在\n")
    
    elif args.current:
        current = manager.get_current_session()
        if current:
            print(f"\n当前会话: {current['session_id']} (设置于 {current['set_at']})\n")
        else:
            print("\n无当前会话\n")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
