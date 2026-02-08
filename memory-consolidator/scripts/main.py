#!/usr/bin/env python3
"""
Memory Consolidator - 定时增量合并 Claude Memory 文件
支持 MiniMax API（兼容 Anthropic 格式）
"""

import argparse
import hashlib
import json
import logging
import os
import sys
import time
import glob
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from dotenv import load_dotenv


class MemoryConsolidator:
    """记忆精简合并器"""

    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        
        # 加载 .env 文件（支持 cron 运行时）
        env_file = os.path.expanduser(self.config.get('env_file', '~/.claude/.env'))
        if os.path.exists(env_file):
            load_dotenv(env_file)
        
        self.setup_logging()
        self.setup_dirs()

    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.setup_logging()
        self.setup_dirs()

    def _load_config(self, config_path: str = None) -> dict:
        """加载配置文件"""
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), "..", "references", "config.json"
            )

        with open(os.path.expanduser(config_path), 'r') as f:
            return json.load(f)

    def setup_logging(self):
        """配置日志"""
        log_dir = Path(os.path.expanduser(self.config.get('log_dir', '~/.openclaw/qmd_memory/logs')))
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"consolidator_{datetime.now().strftime('%Y%m%d')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_dirs(self):
        """创建必要目录"""
        self.output_dir = Path(os.path.expanduser(self.config['output_dir']))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        (self.output_dir / 'sources').mkdir(exist_ok=True)
        (self.output_dir / 'logs').mkdir(exist_ok=True)

    def calculate_file_hash(self, filepath: str) -> str:
        """计算文件 hash"""
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def get_source_files(self) -> List[Dict]:
        """获取源文件列表"""
        sources = []
        for pattern in self.config['sources']:
            expanded = os.path.expanduser(pattern)
            
            # 使用 glob 处理通配符
            if '*' in expanded:
                matched = glob.glob(expanded)
                for filepath in matched:
                    if os.path.isfile(filepath):
                        sources.append({
                            'path': filepath,
                            'hash': self.calculate_file_hash(filepath),
                            'modified': os.path.getmtime(filepath)
                        })
            elif os.path.exists(expanded):
                sources.append({
                    'path': expanded,
                    'hash': self.calculate_file_hash(expanded),
                    'modified': os.path.getmtime(expanded)
                })
        return sources

    def check_for_changes(self, sources: List[Dict]) -> bool:
        """检查源文件是否有变化"""
        state_file = self.output_dir / '.source_state.json'

        if not state_file.exists():
            return True

        with open(state_file, 'r') as f:
            old_state = json.load(f)

        for source in sources:
            path = os.path.abspath(source['path'])
            if path in old_state:
                if old_state[path]['hash'] != source['hash']:
                    self.logger.info(f"检测到文件变化: {path}")
                    return True
            else:
                self.logger.info(f"发现新文件: {path}")
                return True

        return False

    def save_source_state(self, sources: List[Dict]):
        """保存源文件状态"""
        state_file = self.output_dir / '.source_state.json'
        state = {}
        for source in sources:
            path = os.path.abspath(source['path'])
            state[path] = {
                'hash': source['hash'],
                'modified': source['modified']
            }
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def read_source_files(self, sources: List[Dict]) -> Dict[str, str]:
        """读取源文件内容"""
        contents = {}
        for source in sources:
            try:
                with open(source['path'], 'r', encoding='utf-8') as f:
                    contents[source['path']] = f.read()
                # 保存快照
                snapshot_path = self.output_dir / 'sources' / os.path.basename(source['path'])
                with open(snapshot_path, 'w', encoding='utf-8') as f:
                    f.write(contents[source['path']])
            except Exception as e:
                self.logger.error(f"读取文件失败 {source['path']}: {e}")
        return contents

    def consolidate_with_llm(self, contents: Dict[str, str]) -> str:
        """调用 LLM API 进行精简（支持 MiniMax 兼容 Anthropic 格式）"""
        
        # 重新加载 .env（确保 cron 环境下能获取到）
        from dotenv import load_dotenv
        env_file = os.path.expanduser(self.config.get('env_file', '~/.claude/.env'))
        if os.path.exists(env_file):
            load_dotenv(env_file, override=True)
        
        api_key = os.environ.get(self.config.get('api_key_env', 'ANTHROPIC_AUTH_TOKEN'))
        api_base = self.config.get('api_base_url', 'https://api.minimaxi.com/anthropic')
        model = self.config.get('model', 'minimax/MiniMax-M2.1')

        if not api_key:
            self.logger.warning("未找到 API Key，跳过智能精简")
            return self._simple_merge(contents)

        try:
            import httpx
            client = httpx.Client(timeout=300.0)

            prompt = self._build_consolidation_prompt(contents)

            response = client.post(
                f"{api_base}/v1/messages",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "X-API-Version": "1"
                },
                json={
                    "model": model,
                    "max_tokens": 8192,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )

            response.raise_for_status()
            result = response.json()
            
            self.logger.debug(f"API 响应: {str(result)[:500]}")

            # 兼容不同 API 响应格式
            # 1. MiniMax 格式: content[0].thinking
            if "content" in result and isinstance(result["content"], list) and len(result["content"]) > 0:
                content_item = result["content"][0]
                if isinstance(content_item, dict):
                    # MiniMax 返回 thinking
                    if "thinking" in content_item:
                        return content_item["thinking"]
                    # Anthropic 返回 text
                    if "text" in content_item:
                        return content_item["text"]
            
            # 2. OpenAI 兼容格式: choices[0].message.content
            if "choices" in result and isinstance(result["choices"], list) and len(result["choices"]) > 0:
                choice = result["choices"][0]
                if isinstance(choice, dict) and "message" in choice:
                    return choice["message"].get("content", str(result))
            
            # 3. 直接返回结果字符串
            return str(result)

        except ImportError:
            self.logger.warning("httpx 未安装，尝试使用 anthropic SDK")
            return self._use_anthropic_sdk(contents)
        except Exception as e:
            self.logger.error(f"API 调用失败: {e}")
            return self._simple_merge(contents)

    def _use_anthropic_sdk(self, contents: Dict[str, str]) -> str:
        """备用：使用 anthropic SDK"""
        try:
            from anthropic import Anthropic
            api_key = os.environ.get('ANTHROPIC_AUTH_TOKEN', '')
            client = Anthropic(api_key=api_key, base_url='https://api.minimaxi.com/anthropic')

            prompt = self._build_consolidation_prompt(contents)

            response = client.messages.create(
                model='minimax/MiniMax-M2.1',
                max_tokens=8192,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text
        except Exception as e:
            self.logger.error(f"Anthropic SDK 也失败: {e}")
            return self._simple_merge(contents)

    def _build_consolidation_prompt(self, contents: Dict[str, str]) -> str:
        """构建精简提示"""
        combined = ""
        for path, content in contents.items():
            combined += f"\n\n=== {path} ===\n{content[:10000]}"

        return f"""
请将以下多个记忆文件合并精简，去除重复，保留核心信息：

{combined}

请输出：
1. 核心规则和原则
2. 用户偏好和重要约定
3. 待办事项
4. 重要教训和经验
5. 项目索引和知识库

格式为清晰的 Markdown，保持结构和可读性。
"""

    def _simple_merge(self, contents: Dict[str, str]) -> str:
        """简单合并（无 API）"""
        merged = []
        for path, content in contents.items():
            merged.append(f"\n\n=== {path} ===\n{content}")
        return "\n".join(merged)

    def deduplicate(self, content: str) -> str:
        """去重处理"""
        # 简化版：按行去重
        lines = content.split('\n')
        seen = set()
        result = []

        for line in lines:
            line_stripped = line.strip()
            if line_stripped and line_stripped not in seen:
                seen.add(line_stripped)
                result.append(line)

        return '\n'.join(result)

    def save_output(self, content: str):
        """保存输出文件"""
        output_file = self.output_dir / 'consolidated.md'

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        # 保存元数据
        meta = {
            'last_run': datetime.now().isoformat(),
            'files_processed': len(list((self.output_dir / 'sources').glob('*'))),
            'output_size': len(content)
        }
        with open(self.output_dir / '.last_run', 'w') as f:
            f.write(json.dumps(meta, indent=2))

        self.logger.info(f"输出已保存: {output_file}")

    def run(self):
        """执行完整流程"""
        self.logger.info("=== 开始记忆精简 ===")

        # 1. 获取源文件
        sources = self.get_source_files()
        self.logger.info(f"发现 {len(sources)} 个源文件")

        if not sources:
            self.logger.info("无源文件，退出")
            return

        # 2. 检查变化
        if not self.check_for_changes(sources):
            self.logger.info("无文件变化，跳过处理")
            return

        # 3. 读取内容
        contents = self.read_source_files(sources)
        self.logger.info(f"读取了 {len(contents)} 个文件")

        # 4. LLM 精简（MiniMax）
        consolidated = self.consolidate_with_llm(contents)
        self.logger.info("完成智能精简")

        # 5. 去重
        consolidated = self.deduplicate(consolidated)
        self.logger.info("完成去重")

        # 6. 保存
        self.save_output(consolidated)

        # 7. 保存状态
        self.save_source_state(sources)

        self.logger.info("=== 记忆精简完成 ===")


def main():
    parser = argparse.ArgumentParser(description='Memory Consolidator')
    parser.add_argument('--run-now', action='store_true', help='立即执行')
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')

    args = parser.parse_args()

    consolidator = MemoryConsolidator(args.config)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    consolidator.run()


if __name__ == '__main__':
    main()
