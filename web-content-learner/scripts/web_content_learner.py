#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Content Learner - 网页内容提取 + 视频转文字
需要 Python 3.12+ (CUDA 支持)
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

import requests
import yt_dlp
from bs4 import BeautifulSoup
import whisper

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JinaExtractor:
    """Jina AI 内容提取"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.api_url = "https://r.jina.ai/http://{url}"
    
    def extract(self, url: str) -> Dict[str, Any]:
        """提取网页内容"""
        try:
            response = requests.get(
                self.api_url.format(url=url),
                timeout=30
            )
            response.raise_for_status()
            
            return {
                "success": True,
                "content": response.text,
                "extractor": "jina-ai",
                "url": url
            }
        except Exception as e:
            logger.error(f"Jina extraction failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "extractor": "jina-ai"
            }


class BraveExtractor:
    """Brave Search 回退提取"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.api_url = "https://api.brave.com/v1/search"
    
    def extract(self, url: str) -> Dict[str, Any]:
        """提取网页内容"""
        try:
            headers = {
                "Accept": "text/html",
                "X-Subscription-Token": self.api_key
            } if self.api_key else {}
            
            response = requests.get(
                url,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            # 解析 HTML
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 提取正文
            text = soup.get_text(separator='\n', strip=True)
            
            return {
                "success": True,
                "content": text,
                "extractor": "brave-search",
                "url": url
            }
        except Exception as e:
            logger.error(f"Brave extraction failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "extractor": "brave-search"
            }


class VideoDownloader:
    """视频下载器"""
    
    def __init__(self, output_dir: str = "/media/qingshan/D/videodown"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def download(self, url: str) -> Dict[str, Any]:
        """下载视频"""
        output_path = self.output_dir / f"video_{int(time.time())}.mp4"
        
        ydl_opts = {
            'format': 'best',
            'outtmpl': str(output_path),
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            return {
                "success": True,
                "path": str(output_path),
                "url": url
            }
        except Exception as e:
            logger.error(f"Video download failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class Transcriber:
    """Whisper GPU 转文字"""
    
    def __init__(self, model_name: str = "medium", device: str = "cuda"):
        self.model_name = model_name
        self.device = device
        self.model = None
    
    def load_model(self):
        """加载模型"""
        if self.model is None:
            logger.info(f"Loading Whisper {self.model_name} on {self.device}...")
            self.model = whisper.load_model(self.model_name, device=self.device)
            logger.info("Model loaded successfully")
    
    def transcribe(self, video_path: str) -> Dict[str, Any]:
        """转文字"""
        try:
            self.load_model()
            
            start_time = time.time()
            result = self.model.transcribe(video_path)
            elapsed = time.time() - start_time
            
            return {
                "success": True,
                "text": result["text"],
                "language": result.get("language", "unknown"),
                "duration": elapsed,
                "device": self.device
            }
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class ContentLearner:
    """主控制器"""
    
    def __init__(
        self,
        output_dir: str = "/media/qingshan/D/videodown",
        jina_api_key: Optional[str] = None,
        brave_api_key: Optional[str] = None,
        whisper_model: str = "medium",
        use_gpu: bool = True
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.jina_extractor = JinaExtractor(jina_api_key)
        self.brave_extractor = BraveExtractor(brave_api_key)
        self.video_downloader = VideoDownloader(output_dir)
        self.transcriber = Transcriber(
            model_name=whisper_model,
            device="cuda" if use_gpu else "cpu"
        )
        # 智能搜索
        self.smart_searcher = SmartSearcher(brave_api_key)
    
    def smart_search(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """智能搜索（类似 Tavily）"""
        return self.smart_searcher.search(query, top_k=top_k)
    
    def process_url(self, url: str) -> Dict[str, Any]:
        """处理网页 URL"""
        logger.info(f"Processing URL: {url}")
        
        # 优先使用 Jina AI
        result = self.jina_extractor.extract(url)
        
        if result["success"]:
            return self._save_result(result, "url")
        
        # 回退到 Brave Search
        logger.info("Falling back to Brave Search...")
        result = self.brave_extractor.extract(url)
        
        if result["success"]:
            return self._save_result(result, "url")
        
        return result
    
    def process_video(self, url: str) -> Dict[str, Any]:
        """处理视频 URL"""
        logger.info(f"Processing video: {url}")
        
        # 下载视频
        download_result = self.video_downloader.download(url)
        if not download_result["success"]:
            return download_result
        
        # 转文字
        video_path = download_result["path"]
        transcribe_result = self.transcriber.transcribe(video_path)
        
        if transcribe_result["success"]:
            result = {
                "success": True,
                "content": transcribe_result["text"],
                "metadata": {
                    "source": "video",
                    "url": url,
                    "video_path": video_path,
                    "language": transcribe_result["language"],
                    "transcribe_duration": transcribe_result["duration"],
                    "device": transcribe_result["device"]
                }
            }
            return self._save_result(result, "video")
        
        return transcribe_result
    
    def _save_result(self, result: Dict[str, Any], type_: str) -> Dict[str, Any]:
        """保存结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = "url" if type_ == "url" else "video"
        filename = f"{prefix}_{timestamp}.json"
        
        output_path = self.output_dir / filename
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
        
        logger.info(f"Result saved to: {output_path}")
        result["saved_path"] = str(output_path)
        
        return result


if __name__ == "__main__":
    # 示例
    learner = ContentLearner()
    
    # 测试网页
    # result = learner.process_url("https://example.com")
    
    # 测试视频
    # result = learner.process_video("https://youtube.com/watch?v=...")


class BraveSearcher:
    """Brave Search API 搜索"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("BRAVE_API_KEY", "")
        # 正确的 API 端点
        self.api_url = "https://api.search.brave.com/res/v1/web/search"
    
    def search(self, query: str, count: int = 5) -> Dict[str, Any]:
        """搜索网页，返回结果列表"""
        if not self.api_key:
            return {"success": False, "error": "No Brave API key"}
        
        try:
            headers = {
                "Accept": "application/json",
                "X-Subscription-Token": self.api_key
            }
            params = {
                "q": query,
                "count": count
            }
            
            response = requests.get(
                self.api_url,
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            results = []
            for item in data.get("web", {}).get("results", [])[:count]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "description": item.get("description", "")
                })
            
            return {
                "success": True,
                "results": results,
                "query": query
            }
        except Exception as e:
            logger.error(f"Brave search failed: {e}")
            return {"success": False, "error": str(e)}


class SmartSearcher:
    """智能搜索 - 类似 Tavily 的工作方式
    
    1. 用 Brave 搜索相关网页
    2. 抓取前 N 个结果的内容
    3. 用 LLM 总结答案
    """
    
    def __init__(
        self,
        brave_api_key: Optional[str] = None,
        llm_api_key: Optional[str] = None,
        llm_base_url: str = "https://api.minimaxi.com/anthropic"
    ):
        self.brave_searcher = BraveSearcher(brave_api_key)
        self.jina_extractor = JinaExtractor()
        self.llm_api_key = llm_api_key or os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
        self.llm_base_url = llm_base_url
    
    def search(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """智能搜索并总结"""
        
        # 1. 用 Brave 搜索
        logger.info(f"SmartSearch: Searching for '{query}'...")
        search_result = self.brave_searcher.search(query, count=top_k)
        
        if not search_result.get("success"):
            return search_result
        
        results = search_result.get("results", [])
        if not results:
            return {"success": True, "answer": "未找到相关信息", "sources": []}
        
        # 2. 抓取每个结果的内容
        logger.info(f"SmartSearch: Fetching {len(results)} pages...")
        contents = []
        
        for i, item in enumerate(results):
            url = item.get("url", "")
            if not url:
                continue
            
            logger.info(f"SmartSearch: Fetching {i+1}/{len(results)}: {url}")
            extract_result = self.jina_extractor.extract(url)
            
            if extract_result.get("success"):
                contents.append({
                    "title": item.get("title", ""),
                    "url": url,
                    "content": extract_result.get("content", "")[:5000]  # 限制长度
                })
        
        # 3. 用 LLM 总结
        logger.info("SmartSearch: Summarizing with LLM...")
        summary = self._summarize(query, contents)
        
        return {
            "success": True,
            "query": query,
            "answer": summary,
            "sources": [
                {"title": c["title"], "url": c["url"]}
                for c in contents
            ],
            "raw_contents": contents
        }
    
    def _summarize(self, query: str, contents: list) -> str:
        """用 LLM 总结内容"""
        
        if not self.llm_api_key:
            # 没有 API key，返回简单汇总
            return self._simple_summarize(contents)
        
        # 构建 prompt
        context = "\n\n---\n\n".join([
            f"【{i+1}】{c['title']}\n{c['content'][:2000]}"
            for i, c in enumerate(contents)
        ])
        
        prompt = f"""请根据以下搜索结果，用中文回答用户的问题。

用户问题：{query}

搜索结果：
{context}

请：
1. 直接给出答案
2. 如果有多个来源，合并信息
3. 保持简洁但完整

回答："""
        
        try:
            import httpx
            client = httpx.Client(timeout=60.0)
            
            response = client.post(
                f"{self.llm_base_url}/v1/messages",
                headers={
                    "Authorization": f"Bearer {self.llm_api_key}",
                    "Content-Type": "application/json",
                    "X-API-Version": "1"
                },
                json={
                    "model": "minimax/MiniMax-M2.1",
                    "max_tokens": 1000,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("content", [{}])[0].get("text", "")[:2000]
            else:
                logger.error(f"LLM API error: {response.status_code}")
                return self._simple_summarize(contents)
                
        except Exception as e:
            logger.error(f"LLM summary failed: {e}")
            return self._simple_summarize(contents)
    
    def _simple_summarize(self, contents: list) -> str:
        """简单总结（无 LLM 时）"""
        if not contents:
            return "未找到相关信息"
        
        summary_parts = []
        for c in contents[:3]:
            title = c.get("title", "")
            content = c.get("content", "")[:500]
            summary_parts.append(f"**{title}**\n{content}\n")
        
        return "\n\n---\n\n".join(summary_parts)[:2000]


class IntelligentHandler:
    """智能处理器 - 自动判断用户意图，调用对应功能
    
    用 LLM 判断用户意图，然后调用对应的处理方法。
    支持：
    - 智能搜索（类似 Tavily）
    - 网页抓取
    - 视频下载
    - 视频转文字
    """
    
    def __init__(
        self,
        brave_api_key: Optional[str] = None,
        llm_api_key: Optional[str] = None,
        output_dir: str = "/media/qingshan/D/videodown"
    ):
        self.brave_api_key = brave_api_key
        self.llm_api_key = llm_api_key or os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
        self.output_dir = output_dir
        
        # 初始化各个处理器
        self.content_learner = ContentLearner(
            output_dir=output_dir,
            brave_api_key=brave_api_key
        )
        self.smart_searcher = SmartSearcher(
            brave_api_key=brave_api_key,
            llm_api_key=llm_api_key
        )
    
    def process(self, user_input: str) -> Dict[str, Any]:
        """处理用户输入，自动判断意图并处理
        
        Args:
            user_input: 用户的输入（可以是 URL、问题、搜索请求等）
            
        Returns:
            处理结果，包含意图、答案、来源等
        """
        
        # 1. 判断用户意图
        intent = self._detect_intent(user_input)
        logger.info(f"Detected intent: {intent}")
        
        # 2. 根据意图调用对应功能
        if intent == "search":
            # 智能搜索
            return self._handle_search(user_input)
        
        elif intent == "webpage":
            # 网页抓取
            return self._handle_webpage(user_input)
        
        elif intent == "video_download":
            # 视频下载
            return self._handle_video_download(user_input)
        
        elif intent == "video_transcribe":
            # 视频转文字
            return self._handle_video_transcribe(user_input)
        
        elif intent == "question":
            # 回答问题（可能需要搜索+总结）
            return self._handle_question(user_input)
        
        else:
            # 默认尝试搜索
            return self._handle_search(user_input)
    
    def _detect_intent(self, user_input: str) -> str:
        """用 LLM 判断用户意图
        
        返回意图类型：
        - search: 搜索请求
        - webpage: URL/网页相关
        - video_download: 下载视频
        - video_transcribe: 视频转文字
        - question: 问答
        """
        
        # 快速判断（无需 LLM）
        user_input_lower = user_input.lower()
        
        # URL 检测
        if user_input.startswith("http://") or user_input.startswith("https://"):
            if "youtube.com" in user_input or "youtu.be" in user_input or "bilibili.com" in user_input:
                # 可能是视频
                return "video_transcribe"
            return "webpage"
        
        # 关键词快速判断
        search_keywords = ["搜索", "search", "找", "查"]
        download_keywords = ["下载", "download"]
        transcribe_keywords = ["转文字", "字幕", " transcript", "说了什么"]
        question_keywords = ["什么是", "怎么", "如何", "为什么", "?", "多少", "哪里"]
        
        for kw in download_keywords:
            if kw in user_input_lower:
                return "video_download"
        
        for kw in transcribe_keywords:
            if kw in user_input_lower:
                return "video_transcribe"
        
        for kw in search_keywords:
            if kw in user_input_lower:
                return "search"
        
        for kw in question_keywords:
            if kw in user_input_lower:
                return "question"
        
        # 没有明显特征，用 LLM 判断
        return self._llm_detect_intent(user_input)
    
    def _llm_detect_intent(self, user_input: str) -> str:
        """用 LLM 精确判断意图"""
        
        if not self.llm_api_key:
            return "search"  # 默认搜索
        
        prompt = f"""判断用户输入的意图，返回以下一种：
- search: 用户想要搜索信息
- webpage: 用户给了一个网页 URL 要抓取
- video_download: 用户要下载视频
- video_transcribe: 用户要给视频转文字/要字幕/问视频说了什么
- question: 用户问了一个问题（可能需要搜索+总结）

用户输入：{user_input}

只返回一个词，不要其他内容。"""
        
        try:
            import httpx
            client = httpx.Client(timeout=30.0)
            
            response = client.post(
                "https://api.minimaxi.com/anthropic/v1/messages",
                headers={
                    "Authorization": f"Bearer {self.llm_api_key}",
                    "Content-Type": "application/json",
                    "X-API-Version": "1"
                },
                json={
                    "model": "minimax/MiniMax-M2.1",
                    "max_tokens": 50,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                intent = data.get("content", [{}])[0].get("text", "").strip().lower()
                
                # 映射到支持的意图
                intent_map = {
                    "搜索": "search",
                    "搜索信息": "search",
                    "网页": "webpage",
                    "视频下载": "video_download",
                    "下载视频": "video_download",
                    "视频转文字": "video_transcribe",
                    "转文字": "video_transcribe",
                    "字幕": "video_transcribe",
                    "问答": "question",
                    "问题": "question"
                }
                
                return intent_map.get(intent, "search")
            
        except Exception as e:
            logger.error(f"Intent detection failed: {e}")
        
        return "search"
    
    def _handle_search(self, query: str) -> Dict[str, Any]:
        """处理搜索"""
        result = self.smart_searcher.search(query, top_k=3)
        result["intent"] = "search"
        return result
    
    def _handle_webpage(self, url: str) -> Dict[str, Any]:
        """处理网页抓取"""
        result = self.content_learner.process_url(url)
        result["intent"] = "webpage"
        
        # 如果有内容，用 LLM 总结
        if result.get("success") and result.get("content"):
            summary = self._summarize_content(result["content"])
            result["summary"] = summary
        
        return result
    
    def _handle_video_download(self, url: str) -> Dict[str, Any]:
        """处理视频下载"""
        result = self.content_learner.process_video(url)
        result["intent"] = "video_download"
        return result
    
    def _handle_video_transcribe(self, user_input: str) -> Dict[str, Any]:
        """处理视频转文字"""
        # 提取 URL
        url = self._extract_url(user_input)
        
        if not url:
            return {
                "success": False,
                "error": "未检测到视频 URL，请提供视频链接",
                "intent": "video_transcribe"
            }
        
        # 下载 + 转文字
        result = self.content_learner.process_video(url)
        result["intent"] = "video_transcribe"
        return result
    
    def _handle_question(self, question: str) -> Dict[str, Any]:
        """处理问答 - 搜索 + 总结"""
        # 先搜索
        search_result = self.smart_searcher.search(question, top_k=3)
        search_result["intent"] = "question"
        return search_result
    
    def _extract_url(self, text: str) -> str:
        """从文本中提取 URL"""
        import re
        url_pattern = r'https?://[^\s]+'
        matches = re.findall(url_pattern, text)
        return matches[0] if matches else ""
    
    def _summarize_content(self, content: str, max_len: int = 2000) -> str:
        """用 LLM 总结内容"""
        
        if not self.llm_api_key:
            return content[:500]
        
        prompt = f"""请用简洁的中文总结以下内容的主要信息：

{content[:max_len]}

总结："""
        
        try:
            import httpx
            client = httpx.Client(timeout=60.0)
            
            response = client.post(
                "https://api.minimaxi.com/anthropic/v1/messages",
                headers={
                    "Authorization": f"Bearer {self.llm_api_key}",
                    "Content-Type": "application/json",
                    "X-API-Version": "1"
                },
                json={
                    "model": "minimax/MiniMax-M2.1",
                    "max_tokens": 500,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("content", [{}])[0].get("text", "")[:500]
        
        except Exception as e:
            logger.error(f"Summarize failed: {e}")
        
        return content[:500]
