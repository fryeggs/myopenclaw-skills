#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据整理主程序
扫描文件夹，提取文件内容，整理成统一格式输出
自动检测可用的 Python 版本以支持 PaddleOCR
"""

import os
import sys
import subprocess
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

# 自动检测哪个 Python 版本有 PaddleOCR
def _get_python_with_paddleocr():
    """检测哪个 Python 版本有 PaddleOCR，返回版本命令"""
    for version in ['python3.10', 'python3.11', 'python3']:
        try:
            result = subprocess.run(
                [version, '-c', 'from paddleocr import PaddleOCR'],
                capture_output=True, timeout=10
            )
            if result.returncode == 0:
                return version
        except:
            continue
    return None  # 都没有

_PYTHON_FOR_PDF = None  # 缓存结果

def get_python_for_pdf():
    """获取可用于 OCR 的 Python 版本"""
    global _PYTHON_FOR_PDF
    if _PYTHON_FOR_PDF is None:
        _PYTHON_FOR_PDF = _get_python_with_paddleocr()
    return _PYTHON_FOR_PDF

from file_handler import process_file, get_file_type

# 支持的文件类型列表
SUPPORTED_TYPES = [
    '.pdf', '.xlsx', '.xls', '.docx', '.csv', '.json',
    '.txt', '.md', '.log', '.png', '.jpg', '.jpeg', '.gif', '.bmp'
]

# RAG 系统可以直接处理的文件类型（无需转换）
RAG_NATIVE_TYPES = {'.md', '.txt', '.json', '.csv'}


def scan_directory(path: str, recursive: bool = False) -> Tuple[List[str], List[str]]:
    """
    扫描目录获取文件列表

    Args:
        path: 目录路径
        recursive: 是否递归扫描子目录

    Returns:
        (需要转换的文件列表, RAG 原生文件列表)
    """
    dir_path = Path(path)

    if not dir_path.exists():
        raise FileNotFoundError(f"目录不存在: {path}")

    if not dir_path.is_dir():
        raise NotADirectoryError(f"不是目录: {path}")

    if recursive:
        files = [str(f) for f in dir_path.rglob('*') if f.is_file()]
    else:
        files = [str(f) for f in dir_path.glob('*') if f.is_file()]

    # 过滤支持的文件类型
    supported_files = []
    skipped_by_rag = []
    for f in files:
        ext = Path(f).suffix.lower()
        if ext in SUPPORTED_TYPES:
            if ext in RAG_NATIVE_TYPES:
                skipped_by_rag.append(f)
            else:
                supported_files.append(f)

    if skipped_by_rag:
        print(f"[DATA-ORGANIZER] ⏭️ 发现 {len(skipped_by_rag)} 个 RAG 原生文件")

    return sorted(supported_files), sorted(skipped_by_rag)


def get_skipped_files(path: str, recursive: bool = False, exclude: List[str] = None) -> List[str]:
    """
    获取被跳过的 RAG 原生文件列表

    Args:
        path: 目录路径
        recursive: 是否递归扫描子目录
        exclude: 排除的文件列表（输出文件等）

    Returns:
        RAG 原生文件路径列表
    """
    dir_path = Path(path)

    if not dir_path.exists():
        return []

    if recursive:
        files = [str(f) for f in dir_path.rglob('*') if f.is_file()]
    else:
        files = [str(f) for f in dir_path.glob('*') if f.is_file()]

    exclude_set = set(exclude or [])
    return [f for f in files if Path(f).suffix.lower() in RAG_NATIVE_TYPES and f not in exclude_set]


def generate_summary(files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    生成整理结果摘要

    Args:
        files: 文件信息列表

    Returns:
        包含摘要信息的字典
    """
    type_counts = {}
    total_size = 0

    for f in files:
        file_type = f['type']
        type_counts[file_type] = type_counts.get(file_type, 0) + 1
        total_size += f['metadata'].get('size', 0)

    return {
        'total_files': len(files),
        'by_type': type_counts,
        'total_size_bytes': total_size,
    }


def format_to_json(files: List[Dict[str, Any]], summary: Dict[str, Any]) -> str:
    """
    格式化为 JSON 输出

    Args:
        files: 文件信息列表
        summary: 摘要信息

    Returns:
        JSON 格式字符串
    """
    output = {
        'generated_at': datetime.now().isoformat(),
        'summary': summary,
        'files': files,
    }
    return json.dumps(output, ensure_ascii=False, indent=2)


def format_to_markdown(files: List[Dict[str, Any]], summary: Dict[str, Any]) -> str:
    """
    格式化为 Markdown 输出

    Args:
        files: 文件信息列表
        summary: 摘要信息

    Returns:
        Markdown 格式字符串
    """
    lines = []

    lines.append("# 文件整理报告\n")
    lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    lines.append("## 统计摘要")
    lines.append(f"- 总文件数: {summary['total_files']}")
    lines.append(f"- 总大小: {summary['total_size_bytes']:,} bytes")

    lines.append("\n### 按类型统计")
    for file_type, count in sorted(summary['by_type'].items()):
        lines.append(f"- {file_type}: {count}")

    lines.append("\n---\n")
    lines.append("## 文件列表\n")

    for i, f in enumerate(files, 1):
        lines.append(f"### {i}. {f['name']}")
        lines.append(f"- **路径**: {f['path']}")
        lines.append(f"- **类型**: {f['type']}")
        lines.append(f"- **大小**: {f['metadata'].get('size', 'N/A')} bytes")

        if f['content']:
            lines.append("\n**内容预览**:")
            content_preview = f['content'][:500]
            if len(f['content']) > 500:
                content_preview += "..."
            lines.append(f"```\n{content_preview}\n```")

        lines.append("\n---\n")

    return '\n'.join(lines)


def interactive_mode() -> Dict[str, Any]:
    """
    交互式模式，引导用户完成整理流程

    Returns:
        包含用户选择的字典
    """
    print("\n=== Data Organizer 交互式模式 ===\n")

    # 1. 输入文件夹路径
    while True:
        input_path = input("请输入要整理的文件夹路径: ").strip()
        if os.path.exists(input_path) and os.path.isdir(input_path):
            break
        print("路径无效，请重新输入。")

    # 2. 选择是否递归
    while True:
        recursive_input = input("是否扫描子目录? (y/n): ").strip().lower()
        if recursive_input in ['y', 'yes']:
            recursive = True
            break
        elif recursive_input in ['n', 'no']:
            recursive = False
            break

    # 3. 选择输出格式
    print("\n请选择输出格式:")
    print("  1. JSON")
    print("  2. Markdown")
    while True:
        format_choice = input("请选择 (1/2): ").strip()
        if format_choice == '1':
            output_format = 'json'
            break
        elif format_choice == '2':
            output_format = 'markdown'
            break

    # 4. 选择输出方式
    print("\n请选择输出方式:")
    print("  1. 保存到文件")
    print("  2. 仅显示内容")
    while True:
        output_choice = input("请选择 (1/2): ").strip()
        if output_choice in ['1', '2']:
            save_to_file = (output_choice == '1')
            break

    output_path = None
    if save_to_file:
        default_name = f"organized_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_path = input(f"请输入输出文件路径 (直接回车使用默认 '{default_name}'): ").strip()
        if not output_path:
            output_path = default_name

    return {
        'input': input_path,
        'recursive': recursive,
        'format': output_format,
        'output': output_path,
        'save_to_file': save_to_file,
    }


def organize_files(options: Dict[str, Any], progress_callback=None) -> Dict[str, Any]:
    """
    执行文件整理

    Args:
        options: 包含整理选项的字典
        progress_callback: 进度回调函数，接收 (current, total, filename)

    Returns:
        包含结果和摘要的字典
    """
    input_path = options['input']
    recursive = options['recursive']
    output_format = options['format']
    output_path = options.get('output')
    save_to_file = options.get('save_to_file', True)

    # 输出信息
    print(f"[DATA-ORGANIZER] 开始扫描: {input_path}")
    if recursive:
        print(f"[DATA-ORGANIZER] 模式: 递归扫描")

    # 扫描文件
    files, skipped_by_rag = scan_directory(input_path, recursive)
    total_files = len(files)

    # 处理 RAG 原生文件：移动到 jxh_data 目录
    moved_to_rag = []
    if skipped_by_rag and output_path:
        rag_dir = Path(output_path)
        rag_dir.mkdir(parents=True, exist_ok=True)
        for f in skipped_by_rag:
            try:
                src = Path(f)
                dst = rag_dir / src.name
                import shutil
                shutil.move(str(src), str(dst))
                moved_to_rag.append(str(dst))
                print(f"[DATA-ORGANIZER] → RAG: {src.name}")
            except Exception as e:
                print(f"[DATA-ORGANIZER] 移动失败 {f}: {e}")

    if moved_to_rag:
        print(f"[DATA-ORGANIZER] 已移动 {len(moved_to_rag)} 个文件到 RAG 目录")

    if total_files == 0 and not moved_to_rag:
        result = {"status": "no_files", "message": "未找到需要处理的文件"}
        print(f"[DATA-ORGANIZER] 未找到需要处理的文件")
        return result

    print(f"[DATA-ORGANIZER] 发现 {total_files} 个文件，开始处理...")

    # 处理文件
    file_infos = []
    failed_files = []
    for i, f in enumerate(files, 1):
        filename = Path(f).name
        print(f"[DATA-ORGANIZER] 进度: {i}/{total_files} - {filename}")
        if progress_callback:
            progress_callback(i, total_files, filename)

        try:
            file_info = process_file(f)
            file_infos.append(file_info)
        except Exception as e:
            print(f"[DATA-ORGANIZER] 处理失败: {filename} - {e}")
            failed_files.append({
                "name": filename,
                "path": f,
                "error": str(e)
            })

    print(f"[DATA-ORGANIZER] 文件处理完成，准备生成结果...")

    # 生成摘要
    summary = generate_summary(file_infos)

    # 格式化输出
    if output_format == 'json':
        output_content = format_to_json(file_infos, summary)
    else:
        output_content = format_to_markdown(file_infos, summary)

    # 显示摘要
    print(f"[DATA-ORGANIZER] 完成! 总文件数: {summary['total_files']}")
    for file_type, count in sorted(summary['by_type'].items()):
        print(f"[DATA-ORGANIZER]   - {file_type}: {count}")

    output_full_path = None
    output_files = []  # 保存输出文件列表

    if save_to_file and output_path:
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)  # 确保目录存在

        # 总是输出 MD + JSON
        if len(file_infos) == 1:
            # 单个文件：保留原文件名
            original_name = Path(file_infos[0]['path']).stem  # 去掉扩展名
        else:
            # 多个文件：使用 organized
            original_name = "organized"

        # 保存 Markdown
        md_file = output_path / f"{original_name}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(output_content)

        # 保存 JSON（包含 OCR 结构化数据）
        json_output = {
            'generated_at': datetime.now().isoformat(),
            'summary': summary,
            'files': file_infos,
        }
        json_file = output_path / f"{original_name}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_output, f, ensure_ascii=False, indent=2)

        output_full_path = str(md_file)
        for fi in file_infos:
            output_files.append({
                "original": fi['name'],
                "output": f"{original_name}.md",
                "json_output": f"{original_name}.json"
            })
        print(f"[DATA-ORGANIZER] 结果已保存: {md_file} + {json_file}")

    # 移动到 processed 目录，保留 7 天后由 cron 清理
    cleaned_files = []
    processed_dir = Path(input_path) / ".processed"
    processed_dir.mkdir(exist_ok=True)

    for f in files:
        try:
            src = Path(f)
            dst = processed_dir / src.name
            import shutil
            shutil.move(str(src), str(dst))
            cleaned_files.append(src.name)
        except Exception as e:
            print(f"[DATA-ORGANIZER] 移动文件失败: {f} - {e}")

    if cleaned_files:
        print(f"[DATA-ORGANIZER] 已移动 {len(cleaned_files)} 个文件到 .processed（保留7天）")

    # 返回结果供 Agent 使用
    return {
        "status": "success",
        "total_files": summary['total_files'],
        "by_type": summary['by_type'],
        "output_files": output_files,
        "output_file": output_full_path,
        "cleaned_files": cleaned_files,
        "failed": failed_files,
        "moved_to_rag": moved_to_rag,
        "summary": {
            **summary,
            "files": file_infos
        }
    }


def format_to_telegram_summary(result: Dict, processed_count: int = 0) -> str:
    """
    格式化为 Telegram 简洁状态报告

    Args:
        result: organize_files 返回的结果
        processed_count: 已处理的文件数（用于进度显示）

    Returns:
        Telegram 格式字符串
    """
    if result.get('status') == 'no_files':
        return "📭 **没有需要处理的文件**"

    lines = []

    # 处理进度
    total = result.get('total_files', 0)
    if total > 0:
        lines.append(f"🔄 **处理中**: {processed_count}/{total}")
        lines.append("")  # 空行

    # 失败的文件
    failed = result.get('failed', [])
    if failed:
        lines.append("❌ **失败**:")
        for f in failed:
            lines.append(f"   • {f['name']}: {f.get('error', '未知错误')}")
        lines.append("")

    # 成功的文件
    success = result.get('output_files', [])
    if success:
        lines.append("✅ **成功**:")
        for f in success:
            name = f.get('original', f.get('output', f.get('name', 'Unknown')))
            lines.append(f"   • {name}")
        lines.append("")

    # 移动到 RAG 目录的文件
    moved = result.get('moved_to_rag', [])
    if moved:
        lines.append("⏭️ **已移至 RAG 目录**:")
        for f in moved:
            lines.append(f"   • {Path(f).name}")
        lines.append("")

    # 清理的文件
    cleaned = result.get('cleaned_files', [])
    if cleaned:
        lines.append(f"🗑️ **已清理**: {len(cleaned)} 个原始文件")

    return '\n'.join(lines)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='自动整理文件夹中的各类文件，提取内容并统一输出',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '-i', '--input',
        help='待扫描的文件夹路径'
    )

    parser.add_argument(
        '-o', '--output',
        help='输出文件路径（不含扩展名）'
    )

    parser.add_argument(
        '-f', '--format',
        choices=['json', 'markdown'],
        default='json',
        help='输出格式: json 或 markdown (默认: json)'
    )

    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        help='递归扫描子目录'
    )

    parser.add_argument(
        '--interactive',
        action='store_true',
        help='使用交互式模式'
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help='以 JSON 格式输出结果摘要（供 Agent 使用）'
    )

    parser.add_argument(
        '--telegram',
        action='store_true',
        help='以 Telegram 消息格式输出（简洁摘要，不含内容预览）'
    )

    args = parser.parse_args()

    if args.interactive or not args.input:
        # 交互式模式
        options = interactive_mode()
    else:
        # 命令行模式
        options = {
            'input': args.input,
            'output': args.output,
            'format': args.format,
            'recursive': args.recursive,
            'save_to_file': bool(args.output),
        }

    try:
        result = organize_files(options)

        # 如果指定了 --json，输出机器可读的结果
        if args.json and result:
            print(f"[RESULT_START]{json.dumps(result, ensure_ascii=False)}[RESULT_END]")

        # 如果指定了 --telegram，输出简洁摘要
        if args.telegram and result.get('status') == 'success':
            tg_summary = format_to_telegram_summary(result)
            print(tg_summary)

    except KeyboardInterrupt:
        print("\n\n用户取消操作。")
        sys.exit(0)
    except Exception as e:
        print(f"\n错误: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
