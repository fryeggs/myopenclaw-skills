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
