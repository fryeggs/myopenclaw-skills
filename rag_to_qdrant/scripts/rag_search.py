#!/usr/bin/env python3
"""
RAG Search - Telegram RAG 检索模块

功能：
1. 从 Qdrant 检索相关文档
2. 支持 Telegram 集成
"""

import argparse
import json
import os
from typing import List, Dict, Optional

import requests


DEFAULT_QDRANT_URL = "http://localhost:6333"
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "bge-m3"
DEFAULT_COLLECTION = "jxh_data_rag"


class RAGSearch:
    """RAG 检索器"""
    
    def __init__(self, qdrant_url: str = DEFAULT_QDRANT_URL,
                 ollama_url: str = DEFAULT_OLLAMA_URL,
                 model: str = DEFAULT_MODEL,
                 collection: str = DEFAULT_COLLECTION):
        
        self.qdrant_url = qdrant_url
        self.ollama_url = ollama_url
        self.model = model
        self.collection = collection
        self.embedder_url = f"{ollama_url}/api/embeddings"
        self.search_url = f"{qdrant_url}/collections/{collection}/points/search"
    
    def embed_query(self, query: str) -> Optional[List[float]]:
        """将查询文本向量化"""
        try:
            payload = {
                "model": self.model,
                "prompt": query
            }
            
            response = requests.post(self.embedder_url, json=payload, timeout=60)
            response.raise_for_status()
            
            return response.json().get('embedding')
            
        except Exception as e:
            print(f"向量化查询失败: {e}")
            return None
    
    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """语义检索"""
        embedding = self.embed_query(query)
        if not embedding:
            return []
        
        try:
            payload = {
                "vector": embedding,
                "limit": limit,
                "with_payload": True
            }
            
            response = requests.post(self.search_url, json=payload)
            response.raise_for_status()
            
            return response.json().get('result', [])
            
        except Exception as e:
            print(f"检索失败: {e}")
            return []
    
    def format_results(self, results: List[Dict], query: str) -> str:
        """格式化检索结果"""
        if not results:
            return f"未找到与「{query}」相关的内容"
        
        lines = [f"🔍 搜索: 「{query}」\n", "---"]
        
        for i, r in enumerate(results, 1):
            payload = r.get('payload', {})
            score = r.get('score', 0)
            
            lines.append(f"**[{i}] {payload.get('filename', 'Unknown')}** (相似度: {score:.2f})")
            lines.append(f"来源: `{payload.get('source', '')}`")
            lines.append(f"内容预览: {payload.get('content', '')[:200]}...")
            lines.append("")
        
        return "\n".join(lines)


def rag_search(query: str, limit: int = 5) -> str:
    """快速搜索接口"""
    searcher = RAGSearch()
    results = searcher.search(query, limit)
    return searcher.format_results(results, query)


def main():
    parser = argparse.ArgumentParser(description='RAG 搜索工具')
    parser.add_argument('query', help='搜索查询')
    parser.add_argument('-l', '--limit', type=int, default=5, help='返回结果数量')
    parser.add_argument('-q', '--qdrant-url', default=DEFAULT_QDRANT_URL, help='Qdrant 地址')
    parser.add_argument('-o', '--ollama-url', default=DEFAULT_OLLAMA_URL, help='Ollama 地址')
    parser.add_argument('-c', '--collection', default=DEFAULT_COLLECTION, help='集合名称')
    parser.add_argument('-m', '--model', default=DEFAULT_MODEL, help='模型名称')
    parser.add_argument('--json', action='store_true', help='输出 JSON 格式')
    
    args = parser.parse_args()
    
    searcher = RAGSearch(
        qdrant_url=args.qdrant_url,
        ollama_url=args.ollama_url,
        model=args.model,
        collection=args.collection
    )
    
    results = searcher.search(args.query, args.limit)
    
    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print(searcher.format_results(results, args.query))


if __name__ == '__main__':
    main()
