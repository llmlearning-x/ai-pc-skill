#!/usr/bin/env python3
"""
Local Privacy Inspector Skill
基于 AI PC 的本地隐私数据检查 Skill - MVP 单文件版本

用法:
    python skill.py <文件路径>
    python skill.py ./demo/.env
    python skill.py ./demo/meeting_notes.md

功能:
    1. 解析用户指定的单个文件
    2. 本地识别敏感信息（手机号、身份证号、API Key、Token、数据库连接串等）
    3. 风险分级（高/中/低/提示）
    4. 默认脱敏展示
    5. 生成本地 Markdown / JSON 报告

安全原则:
    - 只扫描用户指定的单个文件
    - 不上传原始文件
    - 不自动修改或删除原文件
    - 检测结果默认脱敏
"""

import sys
import os
import argparse

# 确保能找到同目录下的其他模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extractor import extract_text, get_file_type, SUPPORTED_EXTENSIONS
from detector import SensitiveInfoDetector
from masker import mask_value
from classifier import classify_risk
from reporter import generate_markdown_report, generate_json_report
from models import RiskLevel
from ocr_engine import get_ocr_engine, is_image_file, get_supported_image_extensions


def scan_file(file_path: str, output_format: str = "markdown") -> str:
    """
    扫描单个文件的隐私风险
    
    Args:
        file_path: 要扫描的文件路径
        output_format: 报告格式，可选 "markdown" 或 "json"
    
    Returns:
        生成的报告文件路径
    """
    # 安全检查提示
    print("=" * 60)
    print("🔒 本地隐私数据检查 Skill")
    print("=" * 60)
    print()
    print("📋 安全声明:")
    print("   • 只检查你指定的这一个文件")
    print("   • 检查过程完全在本地完成")
    print("   • 原始文件不会上传")
    print("   • 检测结果将默认脱敏展示")
    print("   • 不会自动修改或删除你的原始文件")
    print()
    
    # 1. 验证文件
    if not os.path.exists(file_path):
        print(f"❌ 错误: 文件不存在: {file_path}")
        sys.exit(1)
    
    if not os.path.isfile(file_path):
        print(f"❌ 错误: 路径不是文件: {file_path}")
        sys.exit(1)
    
    file_name = os.path.basename(file_path)
    file_name = os.path.basename(file_path)
    ext = os.path.splitext(file_path)[1].lower()
    
    # 特殊处理以点开头的文件（如 .env）
    if file_name.startswith('.') and '.' in file_name[1:]:
        ext = os.path.splitext(file_name)[1].lower()
    elif file_name.startswith('.'):
        ext = file_name.lower()
    
    if ext not in SUPPORTED_EXTENSIONS:
        print(f"❌ 错误: 不支持的文件类型 '{ext}'")
        print(f"   MVP 版本支持的文件类型: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")
        sys.exit(1)
    
    file_size = os.path.getsize(file_path)
    if file_size > 10 * 1024 * 1024:
        print(f"❌ 错误: 文件超过 10MB 限制 ({file_size / 1024 / 1024:.1f} MB)")
        sys.exit(1)
    
    print(f"📁 扫描文件: {file_name}")
    print(f"📂 文件路径: {file_path}")
    print(f"📏 文件大小: {file_size} 字节")
    
    # V0.3: 显示 OCR 引擎状态（如果是图片文件）
    if is_image_file(file_path):
        ocr = get_ocr_engine()
        if ocr.is_available:
            print(f"🖼️  文件类型: 图片 (将使用 OCR 提取文字)")
            print(f"🔧 OCR 引擎: {ocr.backend_name}")
            if ocr.openvino_ready:
                ov_info = ocr.get_openvino_info()
                print(f"⚡ OpenVINO: 已就绪 (版本 {ov_info.get('version', 'unknown')}, 设备: {', '.join(ov_info.get('devices', []))})")
            else:
                print(f"⚡ OpenVINO: 未安装 (当前使用 ONNX Runtime)")
                print(f"   提示: 在 Intel AI PC 上安装 OpenVINO 可启用 NPU/GPU 加速")
        else:
            print(f"❌ OCR 引擎不可用，请执行: pip install rapidocr-onnxruntime")
            sys.exit(1)
    print()
    
    # 2. 提取文本
    print("📝 正在提取文件内容...")
    text, error = extract_text(file_path)
    if error:
        print(f"❌ 文件解析失败: {error}")
        sys.exit(1)
    
    print(f"   ✓ 成功提取 {len(text)} 字符")
    
    # V0.3: 如果是图片，显示 OCR 提取详情
    if is_image_file(file_path):
        # 提取 OCR 元信息行
        ocr_meta_lines = []
        content_lines = text.split('\n')
        for line in content_lines:
            if line.startswith('# [OCR提取]'):
                ocr_meta_lines.append(line.replace('# [OCR提取] ', '   • '))
            elif line.strip() == '':
                break
        if ocr_meta_lines:
            for meta in ocr_meta_lines:
                print(f"{meta}")
    print()
    
    # 3. 检测敏感信息
    print("🔍 正在检测敏感信息...")
    detector = SensitiveInfoDetector()
    findings = detector.detect(text, file_path, file_name)
    
    # 4. 脱敏处理
    for finding in findings:
        finding.masked_value = mask_value(finding.raw_value, finding.type)
    
    # 4.5 对上下文进行二次脱敏：确保所有敏感值都被替换
    # 收集所有 (raw_value, masked_value) 映射
    mask_map = {}
    for finding in findings:
        if finding.raw_value and finding.masked_value:
            mask_map[finding.raw_value] = finding.masked_value
    
    # 按长度降序排列键，避免部分匹配问题（先替换长的，再替换短的）
    sorted_keys = sorted(mask_map.keys(), key=len, reverse=True)
    
    # 对每个 finding 的 context 应用所有替换
    for finding in findings:
        if finding.context:
            for raw in sorted_keys:
                masked = mask_map[raw]
                if raw in finding.context:
                    finding.context = finding.context.replace(raw, masked)
    
    # 5. 风险分级
    result = classify_risk(findings)
    if result is None:
        result = type('obj', (object,), {
            'file_path': file_path,
            'file_name': file_name,
            'file_type': get_file_type(file_path),
            'file_size': file_size,
            'risk_level': RiskLevel.LOW,
            'finding_count': 0,
            'findings': [],
            'suggestions': ["未检测到敏感信息，该文件看起来是安全的。"],
        })()
    else:
        result.file_type = get_file_type(file_path)
        result.file_size = file_size
    
    # 6. 输出结果摘要
    print()
    print("=" * 60)
    print("📊 扫描结果")
    print("=" * 60)
    print()
    
    risk_labels = {
        RiskLevel.HIGH: "🔴 高风险",
        RiskLevel.MEDIUM: "🟡 中风险",
        RiskLevel.LOW: "🟢 低风险",
        RiskLevel.INFO: "🔵 提示信息",
    }
    
    print(f"风险等级: {risk_labels.get(result.risk_level, '未知')}")
    print(f"发现敏感项: {result.finding_count} 个")
    print()
    
    if result.findings:
        # 按风险等级分组统计
        high = sum(1 for f in result.findings if f.risk_level == RiskLevel.HIGH)
        medium = sum(1 for f in result.findings if f.risk_level == RiskLevel.MEDIUM)
        low = sum(1 for f in result.findings if f.risk_level == RiskLevel.LOW)
        
        print(f"  🔴 高风险: {high}")
        print(f"  🟡 中风险: {medium}")
        print(f"  🟢 低风险: {low}")
        print()
        
        # 简要展示发现项
        print("发现的敏感信息:")
        for i, finding in enumerate(result.findings[:10], 1):  # 最多展示10条
            level_icon = "🔴" if finding.risk_level == RiskLevel.HIGH else \
                        "🟡" if finding.risk_level == RiskLevel.MEDIUM else "🟢"
            print(f"  {i}. {level_icon} [{finding.type}] {finding.masked_value}")
        
        if len(result.findings) > 10:
            print(f"  ... 还有 {len(result.findings) - 10} 项")
    else:
        print("✅ 未检测到敏感信息")
    
    print()
    
    # 7. 生成报告
    print("📄 正在生成报告...")
    if output_format == "json":
        report_path = generate_json_report(result)
    else:
        report_path = generate_markdown_report(result)
    
    print(f"   ✓ 报告已生成: {report_path}")
    print()
    print("=" * 60)
    print("✅ 检查完成")
    print("=" * 60)
    
    return report_path


def main():
    parser = argparse.ArgumentParser(
        description="Local Privacy Inspector - 本地隐私数据检查 Skill",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python skill.py ./demo/.env
  python skill.py ./demo/meeting_notes.md --format json
  python skill.py ./demo/customer_list.csv
  python skill.py ./demo/demo_id_card.png        # V0.3 图片 OCR
        """
    )
    parser.add_argument("file_path", help="要扫描的文件路径")
    parser.add_argument(
        "--format", "-f",
        choices=["markdown", "json"],
        default="markdown",
        help="报告输出格式 (默认: markdown)"
    )
    
    args = parser.parse_args()
    
    try:
        scan_file(args.file_path, args.format)
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户取消操作")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 运行出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
