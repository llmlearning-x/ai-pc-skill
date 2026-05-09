#!/usr/bin/env python3
"""
Test Agent - 用 SiliconFlow 线上 API 测试 Qwen3.6-35B-A3B 作为 Agent 大脑
驱动 Local Privacy Inspector Skill
"""

import os
import sys
import json

from openai import OpenAI

# 确保能找到同目录下的其他模块
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入 Skill 核心模块
from extractor import extract_text, get_file_type, SUPPORTED_EXTENSIONS
from detector import SensitiveInfoDetector
from masker import mask_value
from classifier import classify_risk
from reporter import generate_markdown_report
from models import RiskLevel


# ============================================================
# 配置
# ============================================================

API_KEY = "sk-sperteeqyafthzvplunpwjryqdakzqufxlqvwfaslqgcccmk"
BASE_URL = "https://api.siliconflow.cn/v1"
MODEL = "Qwen/Qwen3.6-35B-A3B"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


# ============================================================
# Skill 工具函数
# ============================================================

def scan_privacy_file(file_path: str) -> str:
    """
    扫描单个文件的隐私风险，返回结果摘要
    
    Args:
        file_path: 要扫描的文件路径
    
    Returns:
        扫描结果摘要文本
    """
    # 验证文件
    if not os.path.exists(file_path):
        return f"错误: 文件不存在: {file_path}"
    
    if not os.path.isfile(file_path):
        return f"错误: 路径不是文件: {file_path}"
    
    file_name = os.path.basename(file_path)
    ext = os.path.splitext(file_path)[1].lower()
    
    # 特殊处理以点开头的文件
    if file_name.startswith('.') and '.' in file_name[1:]:
        ext = os.path.splitext(file_name)[1].lower()
    elif file_name.startswith('.'):
        ext = file_name.lower()
    
    if ext not in SUPPORTED_EXTENSIONS:
        return f"错误: 不支持的文件类型 '{ext}'，MVP 支持: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
    
    # 提取文本
    text, error = extract_text(file_path)
    if error:
        return f"错误: 文件解析失败: {error}"
    
    # 检测敏感信息
    detector = SensitiveInfoDetector()
    findings = detector.detect(text, file_path, file_name)
    
    # 脱敏
    for finding in findings:
        finding.masked_value = mask_value(finding.raw_value, finding.type)
    
    # 风险分级
    result = classify_risk(findings)
    if result is None:
        return f"✅ 文件 `{file_name}` 检查完成：未检测到敏感信息，该文件看起来是安全的。"
    
    result.file_type = get_file_type(file_path)
    result.file_size = os.path.getsize(file_path)
    
    # 生成结果摘要
    risk_labels = {
        RiskLevel.HIGH: "🔴 高风险",
        RiskLevel.MEDIUM: "🟡 中风险",
        RiskLevel.LOW: "🟢 低风险",
        RiskLevel.INFO: "🔵 提示信息",
    }
    
    lines = []
    lines.append(f"📁 文件: `{file_name}`")
    lines.append(f"📂 路径: `{file_path}`")
    lines.append(f"⚠️ 风险等级: {risk_labels.get(result.risk_level, '未知')}")
    lines.append(f"📊 发现敏感项: {result.finding_count} 个")
    lines.append("")
    
    # 按风险等级分组
    high = [f for f in result.findings if f.risk_level == RiskLevel.HIGH]
    medium = [f for f in result.findings if f.risk_level == RiskLevel.MEDIUM]
    low = [f for f in result.findings if f.risk_level == RiskLevel.LOW]
    
    if high:
        lines.append(f"🔴 高风险 ({len(high)} 项):")
        for f in high[:5]:
            lines.append(f"  - [{f.type}] {f.masked_value} (第{f.line_number}行)")
        if len(high) > 5:
            lines.append(f"  ... 还有 {len(high)-5} 项")
        lines.append("")
    
    if medium:
        lines.append(f"🟡 中风险 ({len(medium)} 项):")
        for f in medium[:5]:
            lines.append(f"  - [{f.type}] {f.masked_value} (第{f.line_number}行)")
        if len(medium) > 5:
            lines.append(f"  ... 还有 {len(medium)-5} 项")
        lines.append("")
    
    if low:
        lines.append(f"🟢 低风险 ({len(low)} 项):")
        for f in low[:5]:
            lines.append(f"  - [{f.type}] {f.masked_value} (第{f.line_number}行)")
        if len(low) > 5:
            lines.append(f"  ... 还有 {len(low)-5} 项")
        lines.append("")
    
    # 处理建议
    if result.suggestions:
        lines.append("💡 处理建议:")
        for suggestion in result.suggestions[:8]:
            lines.append(f"  - {suggestion}")
        lines.append("")
    
    # 生成报告文件
    report_path = generate_markdown_report(result)
    lines.append(f"📄 详细报告已生成: `{report_path}`")
    
    return "\n".join(lines)


# ============================================================
# 工具定义（Function Schema）
# ============================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "scan_privacy_file",
            "description": "扫描用户指定的单个文件，检测其中是否包含手机号、身份证号、API Key、Token、数据库连接串、密码等敏感信息，并返回风险报告。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "要扫描的文件完整路径，例如 '/Users/demo/project/.env' 或 './demo/meeting_notes.md'"
                    }
                },
                "required": ["file_path"]
            }
        }
    }
]


# ============================================================
# Agent 核心逻辑
# ============================================================

def run_agent(user_message: str):
    """
    运行 Agent：理解用户请求 → 调用工具 → 返回自然语言结果
    """
    messages = [
        {
            "role": "system",
            "content": """你是一个 AI PC 本地隐私检查助手，名叫 "PrivacyGuard"。

你的职责：
1. 理解用户的自然语言请求，判断用户想要检查哪个文件
2. 如果需要检查文件，调用 `scan_privacy_file` 工具
3. 拿到工具结果后，用自然语言向用户解释风险和给出建议

安全原则：
- 只检查用户明确指定的文件
- 不上传文件到云端
- 检测结果默认脱敏
- 不自动修改或删除原文件

回复风格：
- 简洁、专业、友好
- 用中文回复
- 对高风险问题要突出警告
"""
        },
        {
            "role": "user",
            "content": user_message
        }
    ]
    
    # 第一轮：让模型决定是否调用工具
    print("🧠 Agent 正在思考...")
    print()
    
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
        temperature=0.3,
    )
    
    assistant_message = response.choices[0].message
    
    # 检查是否有工具调用
    if assistant_message.tool_calls:
        # 添加 assistant 的 tool_call 到对话历史
        messages.append({
            "role": "assistant",
            "content": assistant_message.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in assistant_message.tool_calls
            ]
        })
        
        # 执行工具调用
        for tool_call in assistant_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            print(f"🔧 Agent 调用工具: {function_name}({function_args})")
            print()
            
            if function_name == "scan_privacy_file":
                tool_result = scan_privacy_file(**function_args)
            else:
                tool_result = f"未知工具: {function_name}"
            
            # 添加工具结果到对话历史
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result
            })
        
        # 第二轮：让模型基于工具结果生成最终回复
        print("🧠 Agent 正在整理结果...")
        print()
        
        final_response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.5,
        )
        
        return final_response.choices[0].message.content
    else:
        # 模型直接回复，不需要调用工具
        return assistant_message.content


# ============================================================
# 测试用例
# ============================================================

def run_tests():
    """运行测试用例"""
    
    test_cases = [
        {
            "name": "场景1: 检查 .env 文件",
            "input": "帮我检查一下 demo/.env 这个文件，看看里面有没有敏感信息，我担心有密钥泄露"
        },
        {
            "name": "场景2: 检查会议纪要",
            "input": "我想把 meeting_notes.md 发给别人，你先帮我看看里面有没有不能外发的内容，文件在 demo/meeting_notes.md"
        },
        {
            "name": "场景3: 检查简历",
            "input": "请扫描 demo/customer_list.csv，看看有没有隐私问题"
        },
        {
            "name": "场景4: 检查安全文件",
            "input": "帮我看看 demo/normal_note.txt 这个文件安全吗？"
        },
    ]
    
    for test in test_cases:
        print("=" * 70)
        print(f"🧪 {test['name']}")
        print(f"👤 用户: {test['input']}")
        print("=" * 70)
        print()
        
        try:
            result = run_agent(test['input'])
            print("🤖 Agent 回复:")
            print(result)
        except Exception as e:
            print(f"❌ 错误: {e}")
        
        print()
        print()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 自定义输入模式
        user_input = " ".join(sys.argv[1:])
        print("=" * 70)
        print(f"👤 用户: {user_input}")
        print("=" * 70)
        print()
        result = run_agent(user_input)
        print("🤖 Agent 回复:")
        print(result)
    else:
        # 运行预设测试用例
        run_tests()
