#!/usr/bin/env python3
"""
RAG to Qdrant - 目录监控、向量化、存储一体化工具

功能：
1. 监控指定目录变化（hash 对比）
2. 读取 .md, .txt, .json 文件
3. 调用 Ollama BGE-M3 生成向量
4. 存入 Qdrant
"""

import argparse
import hashlib
import json
import os
import sys
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 配置
DEFAULT_QDRANT_URL = "http://localhost:6333"
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "bge-m3"
DEFAULT_COLLECTION = "jxh_data_rag"
CONFIG_DIR = Path(os.path.expanduser("~/.config/rag_to_qdrant"))
STATE_FILE = CONFIG_DIR / "processed_files.json"


class FileHasher:
    """文件 hash 计算器"""
    
    @staticmethod
    def calculate_md5(file_path: str) -> str:
        """计算文件 MD5 hash"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    @staticmethod
    def get_file_info(file_path: str) -> Dict:
        """获取文件基本信息"""
        path = Path(file_path)
        return {
            "path": str(path.absolute()),
            "name": path.name,
            "extension": path.suffix.lower(),
            "size": path.stat().st_size,
            "modified": path.stat().st_mtime,
            "md5": FileHasher.calculate_md5(file_path)
        }


class FileScanner:
    """目录扫描器"""
    
    SUPPORTED_EXTENSIONS = {'.md', '.txt', '.json'}
    
    def __init__(self, watch_dir: str):
        self.watch_dir = Path(watch_dir).expanduser().absolute()
        self.state_file = STATE_FILE
        
    def load_processed_state(self) -> Dict[str, str]:
        """加载已处理文件状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载状态文件失败: {e}")
        return {}
    
    def save_processed_state(self, state: Dict[str, str]):
        """保存已处理文件状态"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    
    def scan_directory(self, mode: str = 'incremental') -> Tuple[List[Dict], List[str], List[str]]:
        """
        扫描目录，返回需要处理的文件列表
        
        Returns:
            new_files: 新增/修改的文件
            unchanged_files: 未变化的文件
            deleted_files: 已删除的文件
        """
        if not self.watch_dir.exists():
            logger.error(f"目录不存在: {self.watch_dir}")
            return [], [], []
        
        processed_state = self.load_processed_state()
        new_files = []
        unchanged_files = []
        deleted_files = []
        
        # 遍历目录
        for root, dirs, files in os.walk(self.watch_dir):
            for filename in files:
                file_path = os.path.join(root, filename)
                ext = Path(filename).suffix.lower()
                
                # 只处理支持的文件类型
                if ext not in self.SUPPORTED_EXTENSIONS:
                    continue
                
                try:
                    file_info = FileHasher.get_file_info(file_path)
                    file_md5 = file_info['md5']
                    rel_path = str(Path(file_path).relative_to(self.watch_dir))
                    
                    if mode == 'incremental':
                        if rel_path in processed_state:
                            if processed_state[rel_path] == file_md5:
                                unchanged_files.append(rel_path)
                            else:
                                logger.info(f"文件已修改: {rel_path}")
                                new_files.append(file_info)
                        else:
                            logger.info(f"新增文件: {rel_path}")
                            new_files.append(file_info)
                    else:  # full mode
                        new_files.append(file_info)
                        
                except Exception as e:
                    logger.warning(f"处理文件失败 {file_path}: {e}")
        
        # 检查已删除的文件
        if mode == 'incremental':
            for rel_path in processed_state:
                full_path = self.watch_dir / rel_path
                if not full_path.exists():
                    deleted_files.append(rel_path)
        
        return new_files, unchanged_files, deleted_files
    
    def update_state(self, files: List[Dict], deleted: List[str] = None):
        """更新处理状态"""
        state = self.load_processed_state()
        
        for file_info in files:
            rel_path = str(Path(file_info['path']).relative_to(self.watch_dir))
            state[rel_path] = file_info['md5']
        
        if deleted:
            for rel_path in deleted:
                state.pop(rel_path, None)
        
        self.save_processed_state(state)


class ContentReader:
    """文件内容读取器"""
    
    @staticmethod
    def read_file(file_path: str) -> Optional[str]:
        """读取文件内容"""
        try:
            ext = Path(file_path).suffix.lower()
            
            if ext == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return json.dumps(data, ensure_ascii=False, indent=2)
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
                    
        except Exception as e:
            logger.error(f"读取文件失败 {file_path}: {e}")
            return None
    
    @staticmethod
    def split_text(text: str, max_length: int = 1000) -> List[str]:
        """分割长文本"""
        if len(text) <= max_length:
            return [text]
        
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 <= max_length:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks


class BGEEmbedder:
    """BGE-M3 向量化器"""
    
    def __init__(self, ollama_url: str = DEFAULT_OLLAMA_URL, model: str = DEFAULT_MODEL):
        self.ollama_url = ollama_url
        self.model = model
        self.api_url = f"{ollama_url}/api/embeddings"
    
    def embed(self, text: str) -> Optional[List[float]]:
        """调用 Ollama BGE-M3 生成向量"""
        max_retries = 2
        for attempt in range(max_retries):
            try:
                payload = {
                    "model": self.model,
                    "prompt": text
                }
                
                response = requests.post(self.api_url, json=payload, timeout=180)
                response.raise_for_status()
                
                result = response.json()
                embedding = result.get('embedding')
                if embedding:
                    logger.info(f"Ollama 向量化成功，维度: {len(embedding)}")
                    return embedding
                else:
                    logger.warning(f"Embedding 为空: {result}")
                    return None
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Ollama 调用失败 (尝试 {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                else:
                    logger.error(f"Ollama 调用最终失败")
                    return None
            except (KeyError, json.JSONDecodeError) as e:
                logger.error(f"Ollama 响应格式错误: {e}")
                return None
    
    def embed_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """批量向量化"""
        embeddings = []
        for i, text in enumerate(texts):
            logger.info(f"向量化 [{i+1}/{len(texts)}]: {text[:50]}...")
            embedding = self.embed(text)
            embeddings.append(embedding)
        return embeddings


class QdrantStore:
    """Qdrant 向量存储"""
    
    def __init__(self, qdrant_url: str = DEFAULT_QDRANT_URL, collection: str = DEFAULT_COLLECTION):
        self.qdrant_url = qdrant_url
        self.collection = collection
        self.api_url = f"{qdrant_url}/collections/{collection}"
        self.points_url = f"{qdrant_url}/collections/{collection}/points"
    
    def create_collection(self, vector_size: int = 1024):
        """创建集合"""
        try:
            payload = {
                "name": self.collection,
                "vectors": {
                    "size": vector_size,
                    "distance": "Cosine"
                }
            }
            
            response = requests.put(self.api_url, json=payload)
            response.raise_for_status()
            logger.info(f"集合 {self.collection} 创建成功")
            
        except requests.exceptions.RequestException as e:
            if "already exists" in str(e):
                logger.info(f"集合 {self.collection} 已存在")
            else:
                logger.error(f"创建集合失败: {e}")
    
    def upsert_points(self, points: List[Dict]):
        """批量写入向量"""
        try:
            # 确保 point ID 是整数
            for p in points:
                if isinstance(p.get('id'), str):
                    try:
                        p['id'] = int(p['id'])
                    except ValueError:
                        # 如果不是数字，使用 hash
                        p['id'] = abs(hash(p['id'])) % (10**8)
            
            payload = {
                "points": points
            }
            
            response = requests.put(self.points_url, json=payload)
            response.raise_for_status()
            logger.info(f"成功写入 {len(points)} 个向量")
            logger.info(f"成功写入 {len(points)} 个向量")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"写入向量失败: {e}")
    
    def search(self, query_vector: List[float], limit: int = 5) -> List[Dict]:
        """向量检索"""
        try:
            payload = {
                "vector": query_vector,
                "limit": limit,
                "with_payload": True
            }
            
            response = requests.post(f"{self.points_url}/search", json=payload)
            response.raise_for_status()
            
            return response.json().get('result', [])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"检索失败: {e}")
            return []


class RAGToQdrant:
    """主控制器"""
    
    def __init__(self, watch_dir: str, mode: str = 'incremental',
                 qdrant_url: str = DEFAULT_QDRANT_URL,
                 collection: str = DEFAULT_COLLECTION,
                 model: str = DEFAULT_MODEL):
        
        self.scanner = FileScanner(watch_dir)
        self.reader = ContentReader()
        self.embedder = BGEEmbedder(model=model)
        self.store = QdrantStore(qdrant_url, collection)
        
    def run(self):
        """执行全流程"""
        logger.info(f"开始扫描目录: {self.scanner.watch_dir}")
        
        # 1. 扫描目录
        new_files, unchanged, deleted = self.scanner.scan_directory()
        
        if not new_files and not deleted:
            logger.info("没有需要处理的文件")
            return
        
        logger.info(f"新增/修改: {len(new_files)}, 未变化: {len(unchanged)}, 已删除: {len(deleted)}")
        
        # 2. 创建集合
        self.store.create_collection()
        
        # 3. 处理新文件
        points = []
        for file_info in new_files:
            content = self.reader.read_file(file_info['path'])
            if not content:
                continue
            
            # 分割文本
            chunks = self.reader.split_text(content)
            
            for i, chunk in enumerate(chunks):
                embedding = self.embedder.embed(chunk)
                if embedding:
                    point_id = hashlib.md5(f"{file_info['path']}_{i}".encode()).hexdigest()[:16]
                    point = {
                        "id": point_id,
                        "vector": embedding,
                        "payload": {
                            "source": file_info['path'],
                            "filename": file_info['name'],
                            "chunk_index": i,
                            "content": chunk[:500],  # 保留部分内容用于展示
                            "processed_at": datetime.now().isoformat()
                        }
                    }
                    points.append(point)
        
        # 4. 写入 Qdrant
        if points:
            self.store.upsert_points(points)
            logger.info(f"成功处理 {len(new_files)} 个文件")
        
        # 5. 更新状态
        self.scanner.update_state(new_files, deleted)
        logger.info("处理完成")


def main():
    parser = argparse.ArgumentParser(description='RAG to Qdrant - 目录监控向量化工具')
    parser.add_argument('-d', '--watch-dir', required=True, help='监控的目录路径')
    parser.add_argument('-m', '--mode', choices=['full', 'incremental'], 
                        default='incremental', help='运行模式')
    parser.add_argument('-q', '--qdrant-url', default=DEFAULT_QDRANT_URL, 
                        help='Qdrant 服务器地址')
    parser.add_argument('-c', '--collection', default=DEFAULT_COLLECTION, 
                        help='Qdrant 集合名称')
    parser.add_argument('-M', '--model', default=DEFAULT_MODEL, 
                        help='Ollama 模型名称')
    
    args = parser.parse_args()
    
    rag = RAGToQdrant(
        watch_dir=args.watch_dir,
        mode=args.mode,
        qdrant_url=args.qdrant_url,
        collection=args.collection,
        model=args.model
    )
    
    rag.run()


if __name__ == '__main__':
    main()
