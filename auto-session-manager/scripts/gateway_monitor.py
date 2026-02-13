#!/usr/bin/env python3
"""
Gateway Monitor - Gateway 服务监控模块

功能：
1. Gateway 健康检查
2. 自动重启 Gateway
3. 重启失败时触发 Claude Code 修复

使用方式：
    python gateway_monitor.py --status          # 检查状态
    python gateway_monitor.py --restart         # 重启 Gateway
    python gateway_monitor.py --monitor        # 持续监控
    python gateway_monitor.py --debug           # 调试模式
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# 路径配置
STATE_DIR = Path.home() / ".openclaw"
LOG_DIR = STATE_DIR / "logs"
STATE_FILE = STATE_DIR / ".asm_state.json"

# 日志配置
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "gateway_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GatewayMonitor:
    """Gateway 监控器"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = {
            "timeout": 300,  # 5 分钟无响应超时
            "restart_attempts": 3,  # 最大重启尝试次数
            "restart_cooldown": 120,  # 重启冷却时间
            "check_interval": 90,  # 检查间隔（与 ASM 同步）
            "telegram_stale_threshold": 10,  # Telegram 积压阈值
        }
        self.config.update(config or {})
        self.state_file = Path(STATE_FILE)
        self.state = self._load_state()

    def check_telegram_health(self) -> Dict:
        """检查 Telegram Bot API 健康状态"""
        result = {
            "status": "unknown",
            "pending_updates": 0,
            "error": None,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # 从配置文件读取 Bot Token
            config_path = Path.home() / ".openclaw" / "openclaw.json"
            if config_path.exists():
                config = json.loads(config_path.read_text())
                token = config.get("channels", {}).get("telegram", {}).get("botToken")
            else:
                token = None

            if not token:
                result["error"] = "Bot token not found in config"
                return result

            # 检查未处理的消息数量
            resp = subprocess.run(
                ["curl", "-s", f"https://api.telegram.org/bot{token}/getUpdates?offset=0"],
                capture_output=True,
                timeout=10
            )

            if resp.returncode == 0:
                data = json.loads(resp.stdout)
                if data.get("ok"):
                    pending = len(data.get("result", []))
                    result["pending_updates"] = pending
                    if pending == 0:
                        result["status"] = "healthy"
                    elif pending < 10:
                        result["status"] = "ok"  # 少量积压可接受
                    else:
                        result["status"] = "stale"  # 大量积压
                else:
                    result["status"] = "error"
                    result["error"] = data.get("description", "Unknown error")
            else:
                result["status"] = "error"
                result["error"] = resp.stderr.decode()

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        return result

    def _load_state(self) -> Dict:
        """加载状态"""
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return {
            "last_check": None,
            "last_restart": None,
            "restart_attempts": 0,
            "status": "unknown",
        }

    def _save_state(self):
        """保存状态"""
        self.state_file.write_text(json.dumps(self.state, indent=2))

    def check_health(self) -> Dict:
        """检查 Gateway 健康状态（包含 Telegram API 检查）"""
        result = {
            "status": "unknown",
            "response_time": None,
            "telegram_status": "unknown",
            "pending_updates": 0,
            "error": None,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # 检查进程是否存在
            proc = subprocess.run(
                ["pgrep", "-f", "openclaw"],
                capture_output=True,
                timeout=5
            )
            if proc.returncode == 0:
                result["status"] = "running"
            else:
                result["status"] = "not_running"
                result["error"] = "OpenClaw process not found"

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        # 检查响应时间（尝试连接）
        try:
            proc = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{time_total}", "http://localhost:18789/health"],
                capture_output=True,
                timeout=10
            )
            result["response_time"] = float(proc.stdout) if proc.stdout else None
        except Exception as e:
            result["response_time"] = None

        # 检查 Telegram API 健康状态
        tg_health = self.check_telegram_health()
        result["telegram_status"] = tg_health["status"]
        result["pending_updates"] = tg_health.get("pending_updates", 0)
        if tg_health.get("error"):
            result["telegram_error"] = tg_health["error"]

        # 综合判断：如果 Telegram 积压超过阈值（默认10条），标记为不健康
        stale_threshold = self.config.get("telegram_stale_threshold", 10)
        if result["status"] == "running" and tg_health.get("pending_updates", 0) >= stale_threshold:
            result["status"] = "stale"
            result["error"] = f"Telegram 积压 {tg_health['pending_updates']} 条消息"

        self.state["last_check"] = result["timestamp"]
        self.state["status"] = result["status"]
        self._save_state()

        return result

    def restart(self, max_attempts: Optional[int] = None) -> Dict:
        """重启 Gateway（包含 Chrome 进程清理）"""
        max_attempts = max_attempts or self.config["restart_attempts"]
        result = {
            "success": False,
            "attempts": 0,
            "error": None,
            "timestamp": datetime.now().isoformat(),
        }

        for attempt in range(1, max_attempts + 1):
            result["attempts"] = attempt
            logger.info(f"尝试重启 Gateway ({attempt}/{max_attempts})")

            try:
                # 1. 停止 Gateway
                subprocess.run(
                    ["systemctl", "--user", "stop", "openclaw-gateway"],
                    capture_output=True,
                    timeout=10
                )
                time.sleep(2)

                # 2. 清理 Chrome 进程（Gateway 使用 Chrome 控制 Telegram）
                logger.info("清理卡住的 Chrome 进程...")
                subprocess.run(
                    ["pkill", "-9", "-f", "chrome.*openclaw"],
                    capture_output=True,
                    timeout=5
                )
                time.sleep(2)

                # 3. 清理可能的 Singleton 锁文件
                singleton_lock = Path.home() / ".openclaw" / "browser" / "openclaw" / "SingletonLock"
                if singleton_lock.exists():
                    singleton_lock.unlink()
                    logger.info("已清理 SingletonLock 文件")

                # 4. 重新启动 Gateway
                proc = subprocess.run(
                    ["systemctl", "--user", "start", "openclaw-gateway"],
                    capture_output=True,
                    timeout=30
                )

                if proc.returncode == 0:
                    time.sleep(5)  # 等待 Gateway 启动
                    # 验证 Gateway 健康
                    health = self.check_health()
                    if health["status"] in ["running", "ok"]:
                        result["success"] = True
                        self.state["last_restart"] = result["timestamp"]
                        self.state["restart_attempts"] = 0
                        self._save_state()
                        logger.info("Gateway 重启成功")
                        break
                    else:
                        result["error"] = f"Gateway 启动但健康检查失败: {health.get('status')}"
                else:
                    result["error"] = proc.stderr.decode() if proc.stderr else "Unknown error"

            except Exception as e:
                result["error"] = str(e)
                logger.error(f"重启失败: {e}")

            time.sleep(self.config["restart_cooldown"])

        if not result["success"]:
            self.state["restart_attempts"] = result["attempts"]
            self._save_state()

        return result

    def monitor(self, callback_on_failure=None):
        """持续监控"""
        logger.info("开始 Gateway 监控...")
        consecutive_failures = 0

        while True:
            health = self.check_health()

            if health["status"] != "running":
                consecutive_failures += 1
                logger.warning(f"Gateway 不正常 (连续 {consecutive_failures} 次)")

                if consecutive_failures >= 3:  # 连续 3 次失败
                    logger.error("触发自动重启...")
                    restart_result = self.restart()

                    if restart_result["success"]:
                        consecutive_failures = 0
                        if callback_on_failure:
                            callback_on_failure("restarted")
                    else:
                        logger.error("重启失败，触发 Claude Code 修复...")
                        if callback_on_failure:
                            callback_on_failure("failed")

            else:
                consecutive_failures = 0

            time.sleep(self.config["check_interval"])


def main():
    parser = argparse.ArgumentParser(description="Gateway Monitor")
    parser.add_argument("--status", action="store_true", help="检查状态")
    parser.add_argument("--restart", action="store_true", help="重启 Gateway")
    parser.add_argument("--monitor", action="store_true", help="持续监控")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    
    args = parser.parse_args()
    
    monitor = GatewayMonitor()

    if args.status:
        health = monitor.check_health()
        print(f"\n📊 Gateway 状态: {health['status']}")
        print(f"   检查时间: {health['timestamp']}")
        if health.get('response_time'):
            print(f"   响应时间: {health['response_time']:.2f}s")
        if health.get('telegram_status'):
            tg_emoji = "✅" if health['telegram_status'] == "healthy" else "⚠️"
            print(f"   Telegram: {tg_emoji} {health['telegram_status']} (积压 {health.get('pending_updates', 0)} 条)")
        if health.get('error'):
            print(f"   错误: {health['error']}")
        print()

    elif args.restart:
        result = monitor.restart()
        if result["success"]:
            print(f"\n✅ Gateway 重启成功 (尝试 {result['attempts']} 次)\n")
        else:
            print(f"\n❌ Gateway 重启失败: {result['error']}\n")

    elif args.monitor:
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
        monitor.monitor()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
