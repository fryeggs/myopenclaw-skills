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
        """获取源文件列表（只保留最近3天，去重）"""
        import datetime
        sources = []
        seen_paths = set()
        three_days_ago = datetime.datetime.now() - datetime.timedelta(days=3)
        core_files = ['MEMORY.md', 'CLAUDE.md', 'identity.md', 'bot-ops.md', 'dev-pipeline.md', 'limits.md']
        
        for pattern in self.config['sources']:
            expanded = os.path.expanduser(pattern)
            
            # 使用 glob 处理通配符
            if '*' in expanded:
                matched = glob.glob(expanded)
                for filepath in matched:
                    if os.path.isfile(filepath) and filepath not in seen_paths:
                        mtime = os.path.getmtime(filepath)
                        file_date = datetime.datetime.fromtimestamp(mtime)
                        # 只保留最近3天的文件
                        if file_date >= three_days_ago:
                            sources.append({
                                'path': filepath,
                                'hash': self.calculate_file_hash(filepath),
                                'modified': mtime
                            })
                            seen_paths.add(filepath)
            elif os.path.exists(expanded) and expanded not in seen_paths:
                mtime = os.path.getmtime(expanded)
                file_date = datetime.datetime.fromtimestamp(mtime)
                # 核心文件不受时间限制
                if file_date >= three_days_ago or any(x in expanded for x in core_files):
                    sources.append({
                        'path': expanded,
                        'hash': self.calculate_file_hash(expanded),
                        'modified': mtime
                    })
                    seen_paths.add(expanded)
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
            # 1. MiniMax 格式: content[].text (最终答案)
            if "content" in result and isinstance(result["content"], list) and len(result["content"]) > 0:
                for content_item in result["content"]:
                    if isinstance(content_item, dict):
                        # 优先找 text 类型（最终答案），其次才是 thinking
                        if content_item.get("type") == "text":
                            return content_item.get("text", str(result))
                        # 备用：只有 thinking 没有 text
                        if "thinking" in content_item and len(result["content"]) == 1:
                            return content_item["thinking"]
            
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

**核心原则：合并多个记忆文件并去重，保留所有有价值的内容**

请输出，务必不影响质量：
1. 核心规则和原则
2. 用户偏好和重要约定
3. 待办事项
4. 重要教训和经验
5. 项目索引和知识库
6. 关键步骤、逻辑、技巧等

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

        # 自动提取热记忆（前50行）
        self._extract_hot_memory(content)

        # 保存元数据
        meta = {
            'last_run': datetime.now().isoformat(),
            'files_processed': len(list((self.output_dir / 'sources').glob('*'))),
            'output_size': len(content)
        }
        with open(self.output_dir / '.last_run', 'w') as f:
            f.write(json.dumps(meta, indent=2))

        self.logger.info(f"输出已保存: {output_file}")

    def _extract_hot_memory(self, content: str):
        """从 consolidated.md 自动提取前 50 行作为热记忆"""
        lines = content.split('\n')[:50]
        hot_content = '\n'.join(lines)

        # 保存到 ~/.openclaw/qmd_memory/hot.md（热记忆）
        hot_file = self.output_dir / 'hot.md'
        with open(hot_file, 'w', encoding='utf-8') as f:
            f.write(hot_content)

        self.logger.info(f"热记忆已更新: {hot_file}")

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

        # 3.5 累积模式：将新内容追加到现有的 consolidated.md（不覆盖）
        existing_consolidated = self.output_dir / 'consolidated.md'
        if existing_consolidated.exists():
            try:
                with open(existing_consolidated, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
                # 追加到源文件末尾，作为额外参考
                contents['[累积] 现有 consolidated.md'] = existing_content
                self.logger.info("已加载现有 consolidated.md（累积模式：只增不减）")
            except Exception as e:
                self.logger.warning(f"读取现有 consolidated.md 失败: {e}")

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
    
    # 发送完成通知到 feed
    notify_feed(f"Memory Consolidator 完成，增量合并 {consolidator增量内容}")


def notify_feed(message: str):
    """发送通知到 feed topic"""
    import subprocess
    try:
        subprocess.run(
            ["/usr/bin/openclaw", "message", "send",
             "--channel", "telegram",
             "--target", "-1003856805564",
             "--thread-id", "1816",
             "--message", f"📝 {message}"],
            capture_output=True, timeout=10
        )
    except Exception:
        pass


if __name__ == '__main__':
    main()
