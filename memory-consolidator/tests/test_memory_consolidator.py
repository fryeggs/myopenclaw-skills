#!/usr/bin/env python3
"""
测试用例 - memory-consolidator
"""
import unittest
import os
import sys
import json
import tempfile
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from main import MemoryConsolidator


class TestMemoryConsolidator(unittest.TestCase):
    
    def test_config_loading(self):
        """测试配置加载"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")
            with open(config_path, 'w') as f:
                json.dump({
                    "sources": [],
                    "output_dir": tmpdir
                }, f)
            
            consolidator = MemoryConsolidator(config_path)
            self.assertEqual(consolidator.config['output_dir'], tmpdir)
    
    def test_hash_calculation(self):
        """测试 hash 计算"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.md")
            with open(test_file, 'w') as f:
                f.write("test content")
            
            consolidator = MemoryConsolidator()
            consolidator.setup_dirs()
            
            hash1 = consolidator.calculate_file_hash(test_file)
            
            # 再次计算应该相同
            hash2 = consolidator.calculate_file_hash(test_file)
            self.assertEqual(hash1, hash2)
            
            # 修改后 hash 应该不同
            with open(test_file, 'a') as f:
                f.write(" more")
            
            hash3 = consolidator.calculate_file_hash(test_file)
            self.assertNotEqual(hash1, hash3)
    
    def test_deduplication(self):
        """测试去重"""
        content = """
# Test
line 1
line 2
line 1
line 3
line 2
"""
        consolidator = MemoryConsolidator()
        result = consolidator.deduplicate(content)
        
        # line1 和 line2 应该只出现一次
        self.assertEqual(result.count("line 1"), 1)
        self.assertEqual(result.count("line 2"), 1)
    
    def test_output_saving(self):
        """测试输出保存"""
        with tempfile.TemporaryDirectory() as tmpdir:
            consolidator = MemoryConsolidator()
            consolidator.output_dir = Path(tmpdir)
            
            test_content = "# 测试内容\n这是精简后的内容"
            consolidator.save_output(test_content)
            
            output_file = os.path.join(tmpdir, "consolidated.md")
            self.assertTrue(os.path.exists(output_file))
            
            # 检查内容
            with open(output_file, 'r') as f:
                saved = f.read()
            self.assertIn("测试内容", saved)
    
    def test_sources_detection(self):
        """测试源文件检测"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "sources": [os.path.join(tmpdir, "*.md")],
                "output_dir": tmpdir
            }
            config_path = os.path.join(tmpdir, "config.json")
            with open(config_path, 'w') as f:
                json.dump(config, f)
            
            # 创建测试文件
            test_file = os.path.join(tmpdir, "test.md")
            with open(test_file, 'w') as f:
                f.write("# Test")
            
            consolidator = MemoryConsolidator(config_path)
            sources = consolidator.get_source_files()
            
            self.assertGreaterEqual(len(sources), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
