#!/usr/bin/env python3
"""
快速验证脚本
"""
import sys
from pathlib import Path

# 添加 scripts 目录
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

def quick_test():
    print("=== Memory Consolidator 快速验证 ===\n")
    
    # 1. 检查配置
    from pathlib import Path
    script_dir = Path(__file__).parent / "scripts"
    config_path = script_dir.parent / "references" / "config.json"
    if config_path.exists():
        print("✅ 配置文件存在")
    else:
        print("❌ 配置文件不存在")
        return
    
    # 2. 导入模块
    try:
        import collector
        import analyzer
        import deduplicator
        import storage
        print("✅ 所有模块导入成功")
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return
    
    # 3. 测试收集器
    from collector import MemoryCollector
    import json
    with open(config_path) as f:
        config = json.load(f)
    
    collector = MemoryCollector(config)
    files = collector.collect()
    print(f"✅ 发现 {len(files)} 个源文件")
    
    print("\n=== 验证完成 ===")

if __name__ == "__main__":
    quick_test()
