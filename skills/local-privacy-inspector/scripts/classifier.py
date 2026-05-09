"""
Local Privacy Inspector - Risk Classifier
根据发现的敏感信息对文件进行风险分级
"""

from typing import List
from models import Finding, RiskLevel, FileScanResult


def classify_risk(findings: List[Finding]) -> FileScanResult:
    """
    根据发现项对文件进行风险分级
    
    分级规则（优先级从高到低）：
    - 高风险：发现 API Key、SecretKey、AccessKey、Token、数据库连接串、SSH私钥、JWT、
              身份证号、银行卡号、.env密码、生产环境配置密钥
    - 中风险：发现手机号、合同金额、客户名称、项目编号、联系人信息、服务器IP、
              预算金额、内部项目代号、统一社会信用代码
    - 低风险：发现普通邮箱、姓名、非完整地址、公开公司名称、固定电话
    - 提示信息：文件名特征
    """
    if not findings:
        return None
    
    # 统计各级风险数量
    high_count = sum(1 for f in findings if f.risk_level == RiskLevel.HIGH)
    medium_count = sum(1 for f in findings if f.risk_level == RiskLevel.MEDIUM)
    low_count = sum(1 for f in findings if f.risk_level == RiskLevel.LOW)
    info_count = sum(1 for f in findings if f.risk_level == RiskLevel.INFO)
    
    # 确定整体风险等级（取最高）
    if high_count > 0:
        overall_risk = RiskLevel.HIGH
    elif medium_count > 0:
        overall_risk = RiskLevel.MEDIUM
    elif low_count > 0:
        overall_risk = RiskLevel.LOW
    elif info_count > 0:
        overall_risk = RiskLevel.INFO
    else:
        overall_risk = RiskLevel.LOW
    
    # 生成总体建议
    suggestions = _generate_suggestions(findings, overall_risk)
    
    file_path = findings[0].file_path if findings else ""
    file_name = findings[0].file_name if findings else ""
    
    return FileScanResult(
        file_path=file_path,
        file_name=file_name,
        file_type="",
        file_size=0,
        risk_level=overall_risk,
        finding_count=len(findings),
        findings=findings,
        suggestions=suggestions
    )


def _generate_suggestions(findings: List[Finding], risk_level: RiskLevel) -> List[str]:
    """根据发现项生成处理建议"""
    suggestions = []
    
    # 按类别收集发现类型
    finding_types = set(f.type for f in findings)
    categories = set(f.category.value for f in findings)
    
    # 高风险通用建议
    if risk_level == RiskLevel.HIGH:
        suggestions.append("⚠️ 该文件包含高风险敏感信息，请优先处理")
        suggestions.append("建议不要将该文件外发或上传到公开平台")
    elif risk_level == RiskLevel.MEDIUM:
        suggestions.append("该文件包含中风险敏感信息，外发前建议审查")
    elif risk_level == RiskLevel.LOW:
        suggestions.append("该文件包含低风险信息，可根据场景决定是否保留")
    
    # 开发者密钥相关建议
    if "developer_secret" in categories:
        if "API_Key" in finding_types or "AccessKey" in finding_types or "SecretKey" in finding_types:
            suggestions.append("发现明文密钥，建议：")
            suggestions.append("  1. 立即删除代码中的明文密钥")
            suggestions.append("  2. 使用环境变量或密钥管理服务（如 AWS KMS、阿里云 KMS）")
            suggestions.append("  3. 如密钥已上传公开仓库，请立即轮换密钥")
        
        if "数据库连接串" in finding_types:
            suggestions.append("发现数据库连接串，建议将密码部分改为环境变量引用")
        
        if "Password" in finding_types:
            suggestions.append("发现明文密码，建议使用加密存储或密钥管理服务")
        
        if "SSH私钥" in finding_types:
            suggestions.append("发现 SSH 私钥，建议立即删除并重新生成密钥对")
        
        if ".env" in findings[0].file_name or "env" in findings[0].file_name.lower():
            suggestions.append("环境变量文件(.env)不应提交到版本控制，请加入 .gitignore")
    
    # 个人信息相关建议
    if "personal" in categories:
        if "身份证号" in finding_types or "银行卡号" in finding_types:
            suggestions.append("发现高度敏感的个人身份信息，建议删除或替换为脱敏版本")
        if "手机号" in finding_types:
            suggestions.append("发现手机号，外发时建议脱敏处理")
        if "邮箱" in finding_types:
            suggestions.append("发现邮箱地址，公开场景建议脱敏")
        if "详细地址" in finding_types:
            suggestions.append("发现详细地址，建议模糊化处理")
    
    # 企业信息相关建议
    if "enterprise" in categories:
        if "合同金额" in finding_types or "预算金额" in finding_types:
            suggestions.append("发现金额信息，外发建议替换为区间或删除")
        if "客户名称" in finding_types:
            suggestions.append("发现客户名称，外发前确认是否需要保留")
        if "项目编号" in finding_types or "内部项目代号" in finding_types:
            suggestions.append("发现内部项目标识，建议替换为通用描述")
        if "统一社会信用代码" in finding_types:
            suggestions.append("发现统一社会信用代码，建议脱敏处理")
    
    # 文件风险特征建议
    if "file_feature" in categories:
        suggestions.append("文件名或内容存在风险特征，建议检查文件用途和存放位置")
    
    return suggestions
