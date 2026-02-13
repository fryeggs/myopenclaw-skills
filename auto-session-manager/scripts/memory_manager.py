#!/usr/bin/env python3
"""
Memory Manager - 长期记忆管理模块

功能：
1. 关键信息提炼与保存
2. 长期记忆存取
3. 会话摘要生成

使用方式：
    python memory_manager.py --action extract --session-id <ID>
    python memory_manager.py --action save --type long --content "<内容>"
    python memory_manager.py --action list --type long
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 路径配置
STATE_DIR = Path.home() / ".openclaw"
MEMORY_DIR = STATE_DIR / ".longterm_memory"
SESSION_MEM_DIR = STATE_DIR / ".session_memory"


class MemoryManager:
    """长期记忆管理器"""

    def __init__(self):
        self.memory_dir = MEMORY_DIR
        self.session_mem_dir = SESSION_MEM_DIR
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.session_mem_dir.mkdir(parents=True, exist_ok=True)

    def extract_key_points(self, conversation_text: str) -> Dict:
        """从对话中提取关键信息"""
        key_points = {
            "topics": self._extract_topics(conversation_text),
            "decisions": self._extract_decisions(conversation_text),
            "tasks": self._extract_tasks(conversation_text),
            "preferences": self._extract_preferences(conversation_text),
            "context": self._extract_context(conversation_text),
        }
        return key_points

    def _extract_topics(self, text: str) -> List[str]:
        """提取主题"""
        topics = []
        patterns = [
            r"关于(.+?)的",
            r"讨论(.+?)问题",
            r"项目[:：]\s*(.+)",
            r"技能[:：]\s*(.+)",
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text)
            topics.extend(matches)
        return list(set(topics))[:10]

    def _extract_decisions(self, text: str) -> List[str]:
        """提取决策"""
        decisions = []
        patterns = [
            r"决定(.+?)[\n。]",
            r"确认(.+?)[\n。]",
            r"采用(.+?)[\n。]",
            r"选择(.+?)[\n。]",
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text)
            decisions.extend(matches)
        return list(set(decisions))[:20]

    def _extract_tasks(self, text: str) -> List[str]:
        """提取任务"""
        tasks = []
        patterns = [
            r"需要(.+?)[\n。]",
            r"要(.+?)[\n。]",
            r"任务[:：]\s*(.+)",
            r"todo[:：]\s*(.+)",

        ]
        for pattern in patterns:
            matches = re.findall(pattern, text)
            tasks.extend(matches)
        return list(set(tasks))[:10]

    def _extract_preferences(self, text: str) -> List[str]:
        """提取偏好"""
        prefs = []
        patterns = [
            r"喜欢(.+?)[\n。]",
            r"偏好(.+?)[\n。]",
            r"不喜欢(.+?)[\n。]",
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text)
            prefs.extend(matches)
        return list(set(prefs))[:10]

    def _extract_context(self, text: str) -> Dict:
        """提取上下文"""
        return {
            "message_count": len(text.split("\n")),
            "last_activity": datetime.now().isoformat(),
        }

    def save_session_memory(self, session_id: str, key_points: Dict) -> str:
        """保存会话关键信息"""
        mem_file = self.session_mem_dir / f"{session_id}.json"
        data = {
            "session_id": session_id,
            "key_points": key_points,
            "saved_at": datetime.now().isoformat(),
        }
        mem_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        return str(mem_file)

    def load_session_memory(self, session_id: str) -> Optional[Dict]:
        """加载会话关键信息"""
        mem_file = self.session_mem_dir / f"{session_id}.json"
        if mem_file.exists():
            return json.loads(mem_file.read_text())
        return None

    def save_longterm_memory(self, memory_type: str, content: str, 
                             tags: Optional[List[str]] = None) -> str:
        """保存长期记忆"""
        memory_id = hashlib.md5(f"{memory_type}{content}".encode()).hexdigest()[:12]
        mem_file = self.memory_dir / f"{memory_type}_{memory_id}.json"
        
        data = {
            "id": memory_id,
            "type": memory_type,
            "content": content,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
        }
        mem_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        return memory_id

    def list_longterm_memories(self, memory_type: Optional[str] = None) -> List[Dict]:
        """列出长期记忆"""
        memories = []
        if self.memory_dir.exists():
            for mem_file in sorted(self.memory_dir.glob("*.json"), reverse=True):
                if memory_type and not mem_file.name.startswith(memory_type):
                    continue
                try:
                    data = json.loads(mem_file.read_text())
                    memories.append({
                        "id": data.get("id", mem_file.stem),
                        "type": data.get("type", "unknown"),
                        "preview": data.get("content", "")[:100],
                        "created_at": data.get("created_at", "")[:10],
                    })
                except Exception:
                    continue
        return memories

    def search_memories(self, query: str) -> List[Dict]:
        """搜索记忆 []"""
        results = []
        query_lower = query.lower()
        if self.memory_dir.exists():
            for mem_file in self.memory_dir.glob("*.json"):
                try:
                    data = json.loads(mem_file.read_text())
                    content = data.get("content", "").lower()
                    if query_lower in content:
                        results.append(data)
                except Exception:
                    continue
        return results


def main():
    parser = argparse.ArgumentParser(description="Memory Manager")
    parser.add_argument("--action", choices=["extract", "save", "list", "search"], required=True)
    parser.add_argument("--session-id", help="会话 ID")
    parser.add_argument("--type", help="记忆类型 (long/preference/decision)")
    parser.add_argument("--content", help="记忆内容")
    parser.add_argument("--query", help="搜索关键词")
    parser.add_argument("--tags", help="标签 (逗号分隔)")
    
    args = parser.parse_args()
    
    manager = MemoryManager()
    
    if args.action == "extract" and args.session_id:
        # 提取关键信息需要对话文本
        print(f"\n🔍 提取会话 {args.session_id} 的关键信息")
        print(f"   需要提供对话文本才能提取\n")
    
    elif args.action == "save":
        if not args.content:
            print("\n❌ 需要提供 --content\n")
            return
        mem_type = args.type or "general"
        tags = args.tags.split(",") if args.tags else []
        mem_id = manager.save_longterm_memory(mem_type, args.content, tags)
        print(f"\n✅ 长期记忆已保存: {mem_id}\n")
    
    elif args.action == "list":
        memories = manager.list_longterm_memories(args.type)
        print(f"\n📚 长期记忆 (共 {len(memories)} 条):\n")
        for m in memories:
            print(f"  • [{m['type']}] {m['preview'][:60]}...")
            print(f"    {m['created_at']}\n")
    
    elif args.action == "search":
        if not args.query:
            print("\n❌ 需要提供 --query\n")
            return
        results = manager.search_memories(args.query)
        print(f"\n🔍 搜索 '{args.query}' 结果 ({len(results)} 条):\n")
        for r in results:
            print(f"  • {r.get('content', '')[:80]}...\n")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
