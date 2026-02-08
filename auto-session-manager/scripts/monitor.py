#!/usr/bin/env python3
"""
Auto Session Manager - 主监控进程

功能：
1. 监测对话上下文使用率，超 80% 时触发摘要
2. 管理会话创建与切换
3. Gateway 健康检查与自动重启
4. MiniMax 额度监控与告警

使用方式：
    python monitor.py --mode foreground     # 前台运行（测试）
    python monitor.py --mode daemon          # 后台守护进程
    python monitor.py --mode single          # 单次检查
"""

import argparse
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# 路径配置
BASE_DIR = Path(__file__).parent.parent
SKILLS_DIR = Path.home() / ".openclaw" / "skills"
LOGS_DIR = Path.home() / ".openclaw" / "logs"
STATE_DIR = Path.home() / ".openclaw"
MEMORY_DIR = STATE_DIR / ".session_memory"

# 默认配置
DEFAULT_CONFIG = {
    "context_threshold": 80,          # 上下文阈值 %
    "gateway_timeout": 300,            # Gateway 超时秒（5分钟）
    "monitor_interval": 180,           # 监控间隔秒（3分钟，避免频繁）
    "minimax_quota_threshold": 100,   # MiniMax 额度告警阈值
    "restart_max_attempts": 3,        # 最大重启尝试次数
    "restart_cooldown": 120,           # 重启冷却时间秒（2分钟）
}


class ASMMonitor:
    """Auto Session Manager 主监控类"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.state_file = STATE_DIR / ".asm_state.json"
        self.running = False
        self.last_gateway_check = None
        self.restart_attempts = 0
        self.last_restart_time = None

        # 初始化日志
        self._init_logging()
        self.logger = logging.getLogger("asm_monitor")

        # 加载状态
        self.state = self._load_state()

    def _init_logging(self):
        """初始化日志配置"""
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_file = LOGS_DIR / f"asm_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

    def _load_state(self) -> Dict:
        """加载运行状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载状态文件失败: {e}")
        return {
            "last_context_check": None,
            "last_session_id": None,
            "gateway_downtime_start": None,
            "minimax_quota_low": False,
            "failed_restarts": 0,
            "sessions_processed": []
        }

    def _save_state(self):
        """保存运行状态"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)

    def check_context_usage(self) -> Optional[Dict]:
        """
        检查当前 OpenClaw 所有会话的上下文使用率

        Returns:
            Dict: 包含各会话的使用率信息
        """
        sessions_json = Path.home() / ".openclaw" / "agents" / "main" / "sessions" / "sessions.json"

        if not sessions_json.exists():
            self.logger.warning("会话文件不存在")
            return None

        try:
            with open(sessions_json, 'r', encoding='utf-8') as f:
                sessions = json.load(f)

            results = []
            highest_usage = 0
            highest_session = None

            # sessions.json 格式是字典: {session_key: session_data}
            for key, session_data in sessions.items():
                if 'agent:main' not in key:
                    continue

                total_tokens = session_data.get('totalTokens', 0)
                context_limit = session_data.get('contextTokens', 200000)
                usage_percent = (total_tokens / context_limit * 100) if context_limit > 0 else 0

                # 提取 topic
                topic_id = ""
                if 'topic' in key:
                    topic_id = key.split('topic:')[-1] if 'topic:' in key else ""

                results.append({
                    "session_key": key,
                    "session_id": session_data.get('sessionId', key),
                    "total_tokens": total_tokens,
                    "context_limit": context_limit,
                    "usage_percent": round(usage_percent, 2),
                    "topic_id": topic_id,
                    "needs_summary": usage_percent >= self.config["context_threshold"]
                })

                if usage_percent > highest_usage:
                    highest_usage = usage_percent
                    highest_session = results[-1]

            return {
                "all_sessions": results,
                "highest": highest_session,
                "overall_usage": highest_usage,
                "needs_summary": highest_usage >= self.config["context_threshold"]
            }

        except Exception as e:
            self.logger.error(f"检查上下文失败: {e}")
            return None

    # ==================== Claude Code / OpenCode 监测 ====================

    def check_all_cc_context(self) -> List[Dict]:
        """
        检查所有 Coding Agents 的上下文使用率

        Returns:
            List[Dict]: 各 CC 的使用率信息列表
        """
        results = []

        # 检查 Claude Code
        cc_result = self._check_claude_code_usage()
        if cc_result:
            results.append(cc_result)

        # 检查 OpenCode
        oc_result = self._check_opencode_usage()
        if oc_result:
            results.append(oc_result)

        return results

    def _check_claude_code_usage(self) -> Optional[Dict]:
        """
        检查 Claude Code 上下文使用率

        Returns:
            Dict: {name, usage_percent, needs_summary, session_id}
        """
        try:
            # 方法1: 检查 Claude Code 配置文件
            settings_file = Path.home() / ".claude" / "settings.json"
            if settings_file.exists():
                with open(settings_file, 'r') as f:
                    settings = json.load(f)

                # Claude Code 没有直接的使用率，通过会话估算
                # 检查最近活动时间
                last_activity = settings.get("lastActivity")
                sessions_dir = Path.home() / ".claude" / "sessions"

                if sessions_dir.exists():
                    session_files = list(sessions_dir.glob("*.json"))
                    # 估算：每会话约 10000 tokens
                    estimated_tokens = len(session_files) * 10000
                    max_tokens = 200000
                    usage_percent = min(100, (estimated_tokens / max_tokens) * 100)

                    return {
                        "name": "Claude Code",
                        "usage_percent": usage_percent,
                        "needs_summary": usage_percent >= self.config["context_threshold"],
                        "session_id": session_files[0].stem if session_files else "",
                        "sessions_count": len(session_files),
                        "source": "claude-code"
                    }

        except Exception as e:
            self.logger.debug(f"Claude Code 检查失败: {e}")

        return None

    def _check_opencode_usage(self) -> Optional[Dict]:
        """
        检查 OpenCode 上下文使用率

        Returns:
            Dict: {name, usage_percent, needs_summary, session_id}
        """
        try:
            # 检查 OpenCode 配置
            opencode_dir = Path.home() / ".opencode"

            if opencode_dir.exists():
                # 检查会话目录
                sessions_dir = opencode_dir / "sessions"
                if sessions_dir.exists():
                    session_files = list(sessions_dir.glob("*.json"))
                    # 估算：每会话约 8000 tokens
                    estimated_tokens = len(session_files) * 8000
                    max_tokens = 200000
                    usage_percent = min(100, (estimated_tokens / max_tokens) * 100)

                    return {
                        "name": "OpenCode",
                        "usage_percent": usage_percent,
                        "needs_summary": usage_percent >= self.config["context_threshold"],
                        "session_id": session_files[0].stem if session_files else "",
                        "sessions_count": len(session_files),
                        "source": "opencode"
                    }

        except Exception as e:
            self.logger.debug(f"OpenCode 检查失败: {e}")

        return None

    def handle_cc_over_threshold(self, cc_info: Dict):
        """
        处理 CC 超过阈值的情况

        Args:
            cc_info: CC 信息
        """
        name = cc_info.get("name", "Unknown")
        usage = cc_info.get("usage_percent", 0)

        self.logger.warning(f"{name} 上下文使用率 ({usage:.1f}%) 超过阈值!")

        # 发送 Feed 通知
        self.notify_feed(
            f"⚠️ {name} 上下文使用率达 {usage:.1f}%，已触发摘要切换",
            topic_id=466
        )

        # 记录状态
        if "cc_over_threshold" not in self.state:
            self.state["cc_over_threshold"] = []

        self.state["cc_over_threshold"].append({
            "name": name,
            "usage_percent": usage,
            "timestamp": datetime.now().isoformat()
        })
        self._save_state()

    def trigger_summary(self, session_info: Dict) -> bool:
        """
        触发关键信息摘要提取

        Args:
            session_info: 会话信息

        Returns:
            bool: 是否成功
        """
        session_id = session_info.get("session_id")
        if not session_id:
            return False

        mem_script = Path(__file__).parent / "memory_manager.py"

        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, str(mem_script),
                 "--action", "extract",
                 "--session-id", session_id],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                self.logger.info(f"会话 {session_id} 摘要提取成功")
                return True
            else:
                self.logger.error(f"摘要提取失败: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error("摘要提取超时")
            return False
        except Exception as e:
            self.logger.error(f"摘要提取异常: {e}")
            return False

    def create_new_session(self, session_info: Dict) -> Optional[Dict]:
        """
        创建新会话并继承上下文

        Args:
            session_info: 原会话信息

        Returns:
            Dict: 新会话信息，失败返回 None
        """
        session_script = Path(__file__).parent / "session_manager.py"

        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, str(session_script),
                 "--create",
                 "--topic", str(session_info.get("topic_id", "")),
                 "--parent", session_info.get("session_id", ""),
                 "--json"],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                self.logger.info(f"新会话创建成功")
                return json.loads(result.stdout)
            else:
                self.logger.error(f"创建会话失败: {result.stderr}")
                return None

        except Exception as e:
            self.logger.error(f"创建会话异常: {e}")
            return None

    def check_gateway_health(self) -> Dict:
        """
        检查 Gateway 服务健康状态

        Returns:
            Dict: {status, response_time, message}
        """
        import subprocess

        try:
            start = time.time()
            result = subprocess.run(
                [str("/usr/bin/openclaw"), "status"],
                capture_output=True,
                text=True,
                timeout=30
            )
            response_time = (time.time() - start) * 1000  # ms

            output = result.stdout + result.stderr

            # 检查 Gateway 状态（兼容不同输出格式）
            # 格式1: "Gateway: reachable" 或 "Gateway: ok"
            # 格式2: "reachable Xms" (openclaw status 输出格式)
            if ("Gateway: reachable" in output or "Gateway: ok" in output.lower() or
                "reachable" in output.lower()):
                return {
                    "status": "healthy",
                    "response_time": response_time,
                    "message": "Gateway 正常"
                }
            elif "unreachable" in output.lower() or "timeout" in output.lower():
                return {
                    "status": "unreachable",
                    "response_time": response_time,
                    "message": "Gateway 无法访问"
                }
            else:
                return {
                    "status": "unknown",
                    "response_time": response_time,
                    "message": output[:200]
                }

        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "response_time": -1,
                "message": "检查超时"
            }
        except FileNotFoundError:
            return {
                "status": "not_found",
                "response_time": -1,
                "message": "openclaw 命令未找到"
            }
        except Exception as e:
            return {
                "status": "error",
                "response_time": -1,
                "message": str(e)
            }

    def restart_gateway(self) -> bool:
        """
        尝试重启 Gateway 服务

        Returns:
            bool: 是否成功
        """
        import subprocess

        self.logger.warning("尝试重启 Gateway 服务...")

        # 检查是否在冷却期
        if self.last_restart_time:
            elapsed = (datetime.now() - self.last_restart_time).total_seconds()
            if elapsed < self.config["restart_cooldown"]:
                self.logger.info(f"重启冷却中，剩余 {int(self.config['restart_cooldown'] - elapsed)} 秒")
                return False

        try:
            # 停止 gateway
            subprocess.run(
                [str("/usr/bin/openclaw"), "gateway", "stop"],
                capture_output=True,
                timeout=10
            )
            time.sleep(2)

            # 启动 gateway
            result = subprocess.run(
                [str("/usr/bin/openclaw"), "gateway", "start"],
                capture_output=True,
                timeout=30
            )

            if result.returncode == 0:
                self.logger.info("Gateway 重启成功")
                self.last_restart_time = datetime.now()
                self.restart_attempts = 0
                self.state["failed_restarts"] = 0
                self._save_state()
                return True
            else:
                self.logger.error(f"Gateway 重启失败: {result.stderr}")
                self.restart_attempts += 1
                self.state["failed_restarts"] = self.restart_attempts
                self._save_state()
                return False

        except Exception as e:
            self.logger.error(f"Gateway 重启异常: {e}")
            self.restart_attempts += 1
            return False

    def notify_feed(self, message: str, topic_id: int = 466) -> bool:
        """
        发送通知到 feed topic

        Args:
            message: 通知内容
            topic_id: feed topic ID (默认 466)

        Returns:
            bool: 是否发送成功
        """
        import subprocess

        try:
            result = subprocess.run(
                ["/usr/bin/openclaw", "message", "send",
                 "--channel", "telegram",
                 "--target", "-1003856805564",
                 "--thread-id", str(topic_id),
                 "--message", f"[ASM] {message}"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                self.logger.info(f"Feed 通知已发送: {message}")
                return True
            else:
                self.logger.error(f"Feed 通知失败: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"发送通知异常: {e}")
            return False

    def check_minimax_quota(self) -> Dict:
        """
        检查 MiniMax API 额度

        Returns:
            Dict: {remaining, threshold_reached, status}
        """
        config_file = Path.home() / ".openclaw" / "openclaw.json"

        if not config_file.exists():
            return {"remaining": -1, "threshold_reached": False, "status": "unknown"}

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 获取 MiniMax 配置和预估使用量
            minimax_config = config.get("models", {}).get("minimax", {})

            # 尝试从日志估算使用量
            log_dir = Path.home() / ".openclaw"
            usage_estimate = 0

            # 简单估算：基于最近的对话次数
            sessions_json = log_dir / "agents" / "main" / "sessions" / "sessions.json"
            if sessions_json.exists():
                with open(sessions_json, 'r') as f:
                    sessions = json.load(f)
                    active = sessions.get("active", [])
                    usage_estimate = len(active) * 5  # 假设每次调用消耗约 5 个单位

            # 阈值判断
            threshold = self.config["minimax_quota_threshold"]
            return {
                "remaining": threshold - usage_estimate,
                "threshold_reached": usage_estimate >= threshold,
                "status": "low" if usage_estimate >= threshold else "ok"
            }

        except Exception as e:
            self.logger.error(f"检查 MiniMax 额度失败: {e}")
            return {"remaining": -1, "threshold_reached": False, "status": "error"}

    def trigger_claude_code_fix(self):
        """
        触发 Claude Code 自动修复（重启失败超过阈值时调用）
        """
        self.logger.error("Gateway 重启失败，触发 Claude Code 介入修复...")

        # 发送紧急通知
        self.notify_feed(
            "⚠️ Gateway 连续重启失败，需要人工介入！请检查服务状态。",
            topic_id=466
        )

        # 生成修复报告
        fix_script = Path(__file__).parent.parent.parent.parent / "usr" / "bin" / "claude"

        if fix_script.exists():
            import subprocess
            try:
                subprocess.run(
                    [sys.executable, str(fix_script), "-p",
                     "OpenClaw Gateway 服务持续故障，请诊断并修复。执行 `systemctl --user restart openclaw-gateway` 并验证恢复。"],
                    timeout=60
                )
            except Exception as e:
                self.logger.error(f"Claude Code 修复调用失败: {e}")

    def run_single_check(self):
        """执行单次检查"""
        self.logger.info("=== 执行单次健康检查 ===")

        results = {
            "timestamp": datetime.now().isoformat(),
            "context": None,
            "cc_contexts": [],  # Claude Code / OpenCode
            "gateway": None,
            "minimax": None
        }

        # 1. 检查 OpenClaw 上下文
        context_info = self.check_context_usage()
        results["context"] = context_info

        if context_info and context_info.get("all_sessions"):
            # 打印所有会话状态
            for session in context_info["all_sessions"]:
                self.logger.info(
                    f"会话 {session['session_key'][-8:]}: "
                    f"{session['usage_percent']:.1f}% ({session['total_tokens']} tokens)"
                )

            # 最高使用率的会话
            highest = context_info["highest"]
            self.logger.info(f"最高使用率: {highest['session_key']} - {highest['usage_percent']:.1f}%")

            if context_info["needs_summary"]:
                self.logger.info("触发上下文摘要...")
                # 使用最高使用率的会话信息
                context_for_summary = {
                    "session_id": highest.get("session_key", ""),
                    "topic_id": highest.get("topic_id", ""),
                    "usage_percent": highest.get("usage_percent", 0)
                }
                if self.trigger_summary(context_for_summary):
                    self.logger.info("创建新会话...")
                    self.create_new_session(context_for_summary)
                    # 摘要切换后通知 feed
                    self.notify_feed(
                        f"OpenClaw 上下文使用率达 {highest['usage_percent']:.1f}%，已切换新会话",
                        topic_id=466
                    )

        # 2. 检查 Claude Code / OpenCode 上下文
        cc_results = self.check_all_cc_context()
        results["cc_contexts"] = cc_results
        for cc in cc_results:
            self.logger.info(f"{cc['name']} 上下文使用率: {cc['usage_percent']:.1f}%")

            if cc.get("needs_summary"):
                self.logger.info(f"触发 {cc['name']} 摘要切换...")
                self.handle_cc_over_threshold(cc)

        # 3. 检查 Gateway
        gw_status = self.check_gateway_health()
        results["gateway"] = gw_status
        self.logger.info(f"Gateway 状态: {gw_status['status']} ({gw_status['response_time']:.0f}ms)")

        if gw_status["status"] != "healthy":
            if self.state.get("gateway_downtime_start") is None:
                self.state["gateway_downtime_start"] = datetime.now().isoformat()

            downtime = datetime.now() - datetime.fromisoformat(self.state["gateway_downtime_start"])
            if downtime.total_seconds() > self.config["gateway_timeout"]:
                self.logger.warning("Gateway 超时，尝试重启...")
                if not self.restart_gateway():
                    if self.restart_attempts >= self.config["restart_max_attempts"]:
                        self.trigger_claude_code_fix()
        else:
            self.state["gateway_downtime_start"] = None

        # 3. 检查 MiniMax 额度
        quota = self.check_minimax_quota()
        results["minimax"] = quota
        self.logger.info(f"MiniMax 额度状态: {quota['status']}")

        if quota["threshold_reached"] and not self.state.get("minimax_quota_low"):
            self.state["minimax_quota_low"] = True
            self.notify_feed("MiniMax API 额度不足，已暂停工作", topic_id=466)
        elif not quota["threshold_reached"]:
            self.state["minimax_quota_low"] = False

        self._save_state()
        return results

    def run_daemon(self):
        """守护进程模式运行"""
        self.logger.info("=== 启动 ASM 守护进程 ===")
        self.running = True

        # 设置信号处理
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        while self.running:
            try:
                self.run_single_check()
                time.sleep(self.config["monitor_interval"])
            except Exception as e:
                self.logger.error(f"监控循环异常: {e}")
                time.sleep(10)  # 异常时短暂休眠

        self.logger.info("ASM 守护进程已停止")

    def _signal_handler(self, signum, frame):
        """信号处理"""
        self.logger.info(f"收到信号 {signum}，正在停止...")
        self.running = False


def main():
    parser = argparse.ArgumentParser(description="Auto Session Manager 监控进程")
    parser.add_argument(
        "--mode",
        choices=["foreground", "daemon", "single"],
        default="foreground",
        help="运行模式: foreground=前台, daemon=后台, single=单次检查"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="监控间隔（秒）"
    )
    parser.add_argument(
        "--context-threshold",
        type=int,
        default=80,
        help="上下文触发阈值（%%）"
    )
    parser.add_argument(
        "--gateway-timeout",
        type=int,
        default=180,
        help="Gateway 无响应超时（秒）"
    )

    args = parser.parse_args()

    config = {
        "monitor_interval": args.interval,
        "context_threshold": args.context_threshold,
        "gateway_timeout": args.gateway_timeout
    }

    monitor = ASMMonitor(config)

    if args.mode == "daemon":
        # 守护进程模式
        pid = os.fork()
        if pid == 0:
            os.setsid()
            monitor.run_daemon()
        else:
            print(f"ASM 守护进程已启动 (PID: {pid})")
    elif args.mode == "single":
        result = monitor.run_single_check()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # 前台模式
        monitor.run_daemon()


if __name__ == "__main__":
    main()
