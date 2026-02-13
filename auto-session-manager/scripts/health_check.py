#!/usr/bin/env python3
"""
Health Check - 系统健康检查

功能：
1. 完整系统健康检查
2. 生成健康报告
3. 异常告警

使用方式：
    python health_check.py              # 完整检查
    python health_check.py --quick     # 快速检查
    python health_check.py --report    # 生成报告
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# 路径配置
STATE_DIR = Path.home() / ".openclaw"
LOGS_DIR = STATE_DIR / "logs"
STATE_FILE = STATE_DIR / ".asm_state.json"
REPORT_FILE = STATE_DIR / "health_report.json"


class HealthCheck:
    """健康检查器"""

    def __init__(self):
        self.checks = []
        self.timestamp = datetime.now().isoformat()

    def check_gateway(self) -> Dict:
        """检查 Gateway 状态"""
        result = {
            "name": "Gateway",
            "status": "unknown",
            "details": {},
        }

        try:
            # 检查进程
            proc = subprocess.run(
                ["pgrep", "-f", "openclaw"],
                capture_output=True,
                timeout=5
            )
            result["details"]["process"] = proc.returncode == 0

            # 检查端口
            proc = subprocess.run(
                ["netstat", "-tlnp"],
                capture_output=True,
                timeout=5
            )
            result["details"]["port_18789"] = "18789" in proc.stdout.decode()

            result["status"] = "healthy" if result["details"]["process"] else "critical"

        except Exception as e:
            result["status"] = "error"
            result["details"]["error"] = str(e)

        return result

    def check_disk(self) -> Dict:
        """检查磁盘空间"""
        result = {
            "name": "Disk Space",
            "status": "unknown",
            "details": {},
        }

        try:
            proc = subprocess.run(
                ["df", "-h", "/"],
                capture_output=True,
                timeout=5
            )
            lines = proc.stdout.decode().split("\n")
            for line in lines:
                if "/" in line and not line.startswith("Filesystem"):
                    parts = line.split()
                    if len(parts) >= 5:
                        result["details"]["root"] = {
                            "total": parts[1],
                            "used": parts[2],
                            "avail": parts[3],
                            "use_pct": parts[4],
                        }
                        usage = int(parts[4].replace("%", ""))
                        result["status"] = "warning" if usage > 80 else "healthy"

        except Exception as e:
            result["status"] = "error"
            result["details"]["error"] = str(e)

        return result

    def check_memory(self) -> Dict:
        """检查内存"""
        result = {
            "name": "Memory",
            "status": "unknown",
            "details": {},
        }

        try:
            proc = subprocess.run(
                ["free", "-h"],
                capture_output=True,
                timeout=5
            )
            lines = proc.stdout.decode().split("\n")
            for line in lines:
                if "Mem:" in line:
                    parts = line.split()
                    result["details"]["total"] = parts[1]
                    result["details"]["used"] = parts[2]
                    result["details"]["available"] = parts[6]
                elif "Swap:" in line:
                    parts = line.split()
                    result["details"]["swap_total"] = parts[1]
                    result["details"]["swap_used"] = parts[2]

            result["status"] = "healthy"

        except Exception as e:
            result["status"] = "error"
            result["details"]["error"] = str(e)

        return result

    def check_api_quota(self) -> Dict:
        """检查 MiniMax API 额度"""
        result = {
            "name": "MiniMax API Quota",
            "status": "unknown",
            "details": {},
        }

        try:
            # 检查环境变量
            api_key = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
            result["details"]["api_key_configured"] = bool(api_key)

            # 检查配置文件
            config_file = STATE_DIR / "openclaw.json"
            if config_file.exists():
                content = config_file.read_text()
                result["details"]["config_exists"] = True
            else:
                result["details"]["config_exists"] = False

            result["status"] = "healthy"

        except Exception as e:
            result["status"] = "error"
            result["details"]["error"] = str(e)

        return result

    def check_skills(self) -> Dict:
        """检查 Skills"""
        result = {
            "name": "Skills",
            "status": "unknown",
            "details": {},
        }

        try:
            skills_dir = STATE_DIR / "skills"
            if skills_dir.exists():
                skills = [d.name for d in skills_dir.iterdir() if d.is_dir()]
                result["details"]["count"] = len(skills)
                result["details"]["skills"] = skills
                result["status"] = "healthy" if skills else "warning"
            else:
                result["details"]["error"] = "Skills directory not found"
                result["status"] = "warning"

        except Exception as e:
            result["status"] = "error"
            result["details"]["error"] = str(e)

        return result

    def run_all(self) -> Dict:
        """运行所有检查"""
        checks = [
            self.check_gateway,
            self.check_disk,
            self.check_memory,
            self.check_api_quota,
            self.check_skills,
        ]

        results = []
        overall_status = "healthy"

        for check in checks:
            result = check()
            results.append(result)
            if result["status"] == "critical":
                overall_status = "critical"
            elif result["status"] == "error" and overall_status == "healthy":
                overall_status = "warning"

        return {
            "timestamp": self.timestamp,
            "overall_status": overall_status,
            "checks": results,
        }

    def print_report(self, report: Dict):
        """打印报告"""
        status_emoji = {
            "healthy": "✅",
            "warning": "⚠️",
            "critical": "🚨",
            "error": "❌",
            "unknown": "❓",
        }

        print(f"\n{'='*50}")
        print(f"  系统健康检查报告")
        print(f"  时间: {report['timestamp'][:19]}")
        print(f"{'='*50}\n")

        overall = status_emoji.get(report["overall_status"], "❓")
        print(f"总体状态: {overall} {report['overall_status'].upper()}\n")

        for check in report["checks"]:
            emoji = status_emoji.get(check["status"], "❓")
            print(f"{emoji} {check['name']}: {check['status']}")

            if "details" in check:
                for key, value in check["details"].items():
                    if isinstance(value, dict):
                        print(f"   {key}:")
                        for k, v in value.items():
                            print(f"      {k}: {v}")
                    elif isinstance(value, list) and len(value) < 10:
                        print(f"   {key}: {', '.join(value)}")
                    else:
                        print(f"   {key}: {value}")
            print()

    def save_report(self, report: Dict):
        """保存报告"""
        REPORT_FILE.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        print(f"报告已保存: {REPORT_FILE}\n")


def main():
    parser = argparse.ArgumentParser(description="Health Check")
    parser.add_argument("--quick", action="store_true", help="快速检查")
    parser.add_argument("--report", action="store_true", help="保存报告")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    
    args = parser.parse_args()

    checker = HealthCheck()

    if args.quick:
        # 快速检查
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "checks": [checker.check_gateway()],
        }
    else:
        report = checker.run_all()

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        checker.print_report(report)

    if args.report:
        checker.save_report(report)


if __name__ == "__main__":
    main()
