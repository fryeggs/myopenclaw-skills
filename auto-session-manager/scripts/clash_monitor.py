#!/usr/bin/env python3
"""
Clash Monitor - Clash 核心监控模块

功能：
1. 检测 Clash 核心进程是否运行
2. 自动启动 Clash 核心
3. 通知用户状态

使用方式：
    python clash_monitor.py --status    # 检查状态
    python clash_monitor.py --restart   # 重启 Clash 核心
    python clash_monitor.py --monitor   # 持续监控
"""

import argparse
import json
import logging
import os
import subprocess
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
        logging.FileHandler(LOG_DIR / "clash_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("clash_monitor")


class ClashMonitor:
    """Clash 核心监控器"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = {
            "check_interval": 300,  # 检查间隔（5分钟）
            "restart_attempts": 3,  # 最大重启尝试次数
            "restart_cooldown": 120,  # 重启冷却时间
        }
        self.config.update(config or {})
        self.state_file = Path(STATE_FILE)

    def check_clash_health(self) -> Dict:
        """检查 Clash 核心健康状态"""
        result = {
            "status": "unknown",
            "core_running": False,
            "service_running": False,
            "error": None,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # 1. 检查 clash-verge-service 进程
            result1 = subprocess.run(
                ["pgrep", "-f", "clash-verge-service"],
                capture_output=True,
                text=True
            )
            result["service_running"] = result1.returncode == 0

            # 2. 检查 mihomo 核心进程
            result2 = subprocess.run(
                ["pgrep", "-f", "mihomo"],
                capture_output=True,
                text=True
            )
            result["core_running"] = result2.returncode == 0

            # 3. 检查代理端口（7890, 7891, 7892 等）
            ports = self._check_proxy_ports()
            result["ports_open"] = ports

            # 确定状态
            if result["core_running"] and ports:
                result["status"] = "healthy"
            elif result["service_running"] and not result["core_running"]:
                result["status"] = "service_only"
            else:
                result["status"] = "not_running"

            logger.info(f"Clash 状态: {result['status']}, 核心: {result['core_running']}, 端口: {ports}")

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"检查 Clash 状态失败: {e}")

        return result

    def _check_proxy_ports(self) -> Dict[str, bool]:
        """检查代理端口是否开放"""
        ports = {}
        common_ports = [7890, 7891, 7892, 7893, 8080, 1080]

        try:
            result = subprocess.run(
                ["ss", "-tlnp"],
                capture_output=True,
                text=True,
                timeout=5
            )

            for port in common_ports:
                ports[str(port)] = f":{port}" in result.stdout

        except Exception as e:
            logger.warning(f"检查端口失败: {e}")

        return {k: v for k, v in ports.items() if v}

    def restart_clash(self) -> Dict:
        """尝试启动 Clash 核心"""
        result = {
            "success": False,
            "method": None,
            "error": None,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # 方法1: 通过 systemctl 重启 clash-verge
            svc_result = subprocess.run(
                ["systemctl", "restart", "clash-verge"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if svc_result.returncode == 0:
                result["success"] = True
                result["method"] = "systemctl restart clash-verge"
                logger.info("Clash 核心已通过 systemctl 重启")
                time.sleep(3)
            else:
                # 方法2: 尝试通过用户进程启动
                # 检查是否有 GUI 会话
                display = os.environ.get("DISPLAY")
                if display:
                    # 尝试启动 clash-verge
                    subprocess.run(
                        ["clash-verge", "--minimize"],
                        capture_output=True,
                        timeout=10,
                        env={**os.environ, "DISPLAY": display}
                    )
                    result["method"] = "clash-verge --minimize"
                    result["success"] = True
                    logger.info("Clash 核心已尝试通过 GUI 启动")
                else:
                    result["error"] = "无法找到启动方式"

        except subprocess.TimeoutExpired:
            result["error"] = "启动超时"
            logger.error("Clash 启动超时")
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"重启 Clash 失败: {e}")

        return result

    def notify_clash_status(self, status: Dict) -> bool:
        """通知用户 Clash 状态（通过 feed topic）"""
        try:
            message = f"🔄 Clash 监控: {status['status']}"
            
            if status.get("core_running"):
                ports = status.get("ports_open", {})
                message += f"\n✅ 核心运行中，端口: {list(ports.keys())}"
            else:
                message += "\n❌ 核心未运行"

            # 发送到 feed topic
            subprocess.run(
                ["/usr/bin/openclaw", "message", "send",
                 "--channel", "telegram",
                 "--to", "466",
                 "--message", message],
                capture_output=True,
                timeout=10
            )
            return True

        except Exception as e:
            logger.error(f"通知失败: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Clash Monitor")
    parser.add_argument("--status", action="store_true", help="检查状态")
    parser.add_argument("--restart", action="store_true", help="重启 Clash")
    parser.add_argument("--monitor", action="store_true", help="持续监控")
    parser.add_argument("--notify", action="store_true", help="发送状态通知")
    args = parser.parse_args()

    monitor = ClashMonitor()

    if args.status:
        result = monitor.check_clash_health()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.restart:
        result = monitor.restart_clash()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.monitor:
        print("开始持续监控 Clash 核心... (Ctrl+C 退出)")
        try:
            while True:
                status = monitor.check_clash_health()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {status['status']}")

                if status["status"] == "not_running":
                    print("Clash 核心未运行，尝试重启...")
                    monitor.restart_clash()

                time.sleep(monitor.config["check_interval"])
        except KeyboardInterrupt:
            print("\n监控已停止")

    elif args.notify:
        status = monitor.check_clash_health()
        monitor.notify_clash_status(status)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
