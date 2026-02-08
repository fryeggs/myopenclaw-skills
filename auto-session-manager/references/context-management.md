# 上下文管理详细设计

## 1. 上下文监测机制

### 1.1 阈值检测

| 阈值 | 说明 | 触发动作 |
|------|------|---------|
| 60% | 警告 | 记录日志 |
| 80% | 警告 | 提炼关键信息 |
| 90% | 严重 | 创建新会话 |

### 1.2 关键信息提取

```python
def extract_key_points(conversation_text):
    """从对话中提取关键信息"""
    key_points = {
        "topics": [],          # 讨论的主题
        "decisions": [],        # 做出的决策
        "tasks": [],           # 待完成的任务
        "preferences": [],      # 用户偏好
        "context": {},          # 其他上下文
    }
    return key_points
```

### 1.3 记忆保存路径

```
~/.openclaw/.session_memory/{session_id}.json
~/.openclaw/.longterm_memory/{type}_{hash}.json
```

## 2. 会话继承机制

### 2.1 创建新会话

```python
def create_session(topic, parent_session):
    """创建新会话，继承父会话上下文"""
    session = {
        "session_id": generate_uuid(),
        "topic": topic,
        "parent_session": parent_session,
        "inherited_context": load_session_memory(parent_session),
        "created_at": now(),
    }
    save_session(session)
    return session
```

### 2.2 上下文注入

新会话创建时，自动注入：
- 父会话的关键决策
- 用户偏好设置
- 当前项目状态
- 未完成任务列表

## 3. 触发条件

### 3.1 上下文超限

- OpenClaw 内部上下文计数器
- Token 使用率监测
- 自动触发无需用户干预

### 3.2 手动触发

```bash
~/.openclaw/skills/auto-session-manager/scripts/memory_manager.py \
  --action extract \
  --session-id <会话ID>
```
