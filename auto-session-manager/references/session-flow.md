# 会话切换流程

## 1. 触发切换

### 自动触发
- 上下文使用率 > 80%
- Token 接近限制
- 系统空闲时

### 手动触发
- 用户要求"总结并继续"
- 收到 `/continue` 命令

## 2. 切换流程

```
Step 1: 保存当前状态
  ├─ 提炼关键信息
  ├─ 保存到长期记忆
  └─ 标记会话为"待续接"

Step 2: 创建新会话
  ├─ 生成新 session_id
  ├─ 继承原 topic
  └─ 加载历史摘要

Step 3: 注入上下文
  ├─ 系统提示词注入
  ├─ 用户偏好注入
  └─ 未完成任务注入

Step 4: 通知用户
  ├─ 发送切换完成消息
  └─ 新会话 ID
```

## 3. 关键信息继承

### 必继承
- 用户偏好设置
- 当前项目状态
- 重要决策记录
- 未完成任务列表

### 可选继承
- 对话风格
- 工具偏好
- 详细项目背景

## 4. Topic 保持

```python
def inherit_topic(old_topic, new_session):
    """保持原 topic"""
    # Telegram topic ID
    new_session.topic_id = old_topic.telegram_id
    # OpenClaw 会话标签
    new_session.label = old_topic.label
    return new_session
```
