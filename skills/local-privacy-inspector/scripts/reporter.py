"""
Local Privacy Inspector - Report Generator
生成本地隐私风险报告（Markdown / JSON 格式）
"""

import os
import json
from datetime import datetime
from typing import Optional

from models import FileScanResult, RiskLevel, Finding


def generate_markdown_report(result: FileScanResult, output_path: Optional[str] = None) -> str:
    """
    生成 Markdown 格式的隐私检查报告
    
    Args:
        result: 扫描结果
        output_path: 报告输出路径（默认在当前目录生成）
    
    Returns:
        报告文件路径
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.splitext(result.file_name)[0]
        output_path = f"privacy_report_{base_name}_{timestamp}.md"
    
    lines = []
    lines.append("# 🔒 本地隐私数据检查报告")
    lines.append("")
    lines.append("## 📋 扫描概览")
    lines.append("")
    lines.append(f"| 项目 | 内容 |")
    lines.append(f"|---|---|")
    lines.append(f"| 扫描文件 | `{result.file_name}` |")
    lines.append(f"| 文件路径 | `{result.file_path}` |")
    lines.append(f"| 扫描时间 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |")
    lines.append(f"| 风险等级 | {_risk_level_badge(result.risk_level)} |")
    lines.append(f"| 发现敏感项 | {result.finding_count} 个 |")
    lines.append("")
    
    # 风险统计
    if result.findings:
        lines.append("## 📊 风险统计")
        lines.append("")
        
        high = sum(1 for f in result.findings if f.risk_level == RiskLevel.HIGH)
        medium = sum(1 for f in result.findings if f.risk_level == RiskLevel.MEDIUM)
        low = sum(1 for f in result.findings if f.risk_level == RiskLevel.LOW)
        info = sum(1 for f in result.findings if f.risk_level == RiskLevel.INFO)
        
        lines.append(f"| 风险等级 | 数量 |")
        lines.append(f"|---|---:|")
        lines.append(f"| 🔴 高风险 | {high} |")
        lines.append(f"| 🟡 中风险 | {medium} |")
        lines.append(f"| 🟢 低风险 | {low} |")
        lines.append(f"| 🔵 提示信息 | {info} |")
        lines.append("")
        
        # 按风险等级分组展示
        for level in [RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW, RiskLevel.INFO]:
            level_findings = [f for f in result.findings if f.risk_level == level]
            if level_findings:
                lines.append(f"## {_risk_level_title(level)} 详情")
                lines.append("")
                
                for i, finding in enumerate(level_findings, 1):
                    lines.append(f"### {i}. {finding.type}")
                    lines.append("")
                    lines.append(f"- **所在行**: 第 {finding.line_number} 行")
                    lines.append(f"- **脱敏内容**: `{finding.masked_value}`")
                    if finding.context and finding.line_number > 0:
                        lines.append(f"- **上下文**: `{finding.context}`")
                    lines.append(f"- **建议**: {finding.suggestion}")
                    lines.append("")
    
    # 总体建议
    if result.suggestions:
        lines.append("## 💡 处理建议")
        lines.append("")
        for suggestion in result.suggestions:
            lines.append(f"- {suggestion}")
        lines.append("")
    
    # 安全声明
    lines.append("---")
    lines.append("")
    lines.append("## 🔐 安全声明")
    lines.append("")
    lines.append("- ✅ 本次检查完全在本地完成")
    lines.append("- ✅ 原始文件未上传至任何服务器")
    lines.append("- ✅ 检测结果已默认脱敏展示")
    lines.append("- ✅ 未修改或删除原始文件")
    lines.append("")
    lines.append("*报告由 Local Privacy Inspector Skill 生成*")
    
    report_content = "\n".join(lines)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    return output_path


def generate_json_report(result: FileScanResult, output_path: Optional[str] = None) -> str:
    """
    生成 JSON 格式的隐私检查报告
    
    Args:
        result: 扫描结果
        output_path: 报告输出路径
    
    Returns:
        报告文件路径
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.splitext(result.file_name)[0]
        output_path = f"privacy_report_{base_name}_{timestamp}.json"
    
    report = {
        "scan_info": {
            "file_name": result.file_name,
            "file_path": result.file_path,
            "scan_time": datetime.now().isoformat(),
            "risk_level": result.risk_level.value,
            "finding_count": result.finding_count,
        },
        "risk_summary": {
            "high": sum(1 for f in result.findings if f.risk_level == RiskLevel.HIGH),
            "medium": sum(1 for f in result.findings if f.risk_level == RiskLevel.MEDIUM),
            "low": sum(1 for f in result.findings if f.risk_level == RiskLevel.LOW),
            "info": sum(1 for f in result.findings if f.risk_level == RiskLevel.INFO),
        },
        "findings": [
            {
                "type": f.type,
                "category": f.category.value,
                "risk_level": f.risk_level.value,
                "masked_value": f.masked_value,
                "line_number": f.line_number,
                "context": f.context,
                "suggestion": f.suggestion,
            }
            for f in result.findings
        ],
        "suggestions": result.suggestions,
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    return output_path


def _risk_level_badge(level: RiskLevel) -> str:
    """风险等级徽章"""
    badges = {
        RiskLevel.HIGH: "🔴 高风险",
        RiskLevel.MEDIUM: "🟡 中风险",
        RiskLevel.LOW: "🟢 低风险",
        RiskLevel.INFO: "🔵 提示信息",
    }
    return badges.get(level, "未知")


def _risk_level_title(level: RiskLevel) -> str:
    """风险等级标题"""
    titles = {
        RiskLevel.HIGH: "🔴 高风险",
        RiskLevel.MEDIUM: "🟡 中风险",
        RiskLevel.LOW: "🟢 低风险",
        RiskLevel.INFO: "🔵 提示信息",
    }
    return titles.get(level, "未知")
