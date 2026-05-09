"""
Local Privacy Inspector - Sensitive Information Detector
基于正则和关键词的敏感信息检测引擎
"""

import re
from typing import List, Tuple
from dataclasses import dataclass

from models import Finding, RiskLevel, SensitiveCategory


@dataclass
class DetectionRule:
    """检测规则定义"""
    name: str
    category: SensitiveCategory
    risk_level: RiskLevel
    patterns: List[Tuple[str, int]]  # (正则表达式, 匹配组号)
    keywords: List[str]  # 关键词辅助确认
    suggestion: str


# ============================================================
# 检测规则定义
# ============================================================

RULES = [
    # ---------- 个人敏感信息 ----------
    DetectionRule(
        name="身份证号",
        category=SensitiveCategory.PERSONAL,
        risk_level=RiskLevel.HIGH,
        patterns=[
            (r'(?:^|[^0-9A-Za-z])((?:\d{6})(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx])(?:$|[^0-9A-Za-z])', 1),
        ],
        keywords=["身份证", "身份证号", "身份证号码"],
        suggestion="身份证号属于高度敏感信息，建议删除或替换为脱敏版本"
    ),
    DetectionRule(
        name="手机号",
        category=SensitiveCategory.PERSONAL,
        risk_level=RiskLevel.MEDIUM,
        patterns=[
            (r'(?:^|[^0-9])(1[3-9]\d{9})(?:$|[^0-9])', 1),
        ],
        keywords=["手机", "电话", "联系方式", "联系电话"],
        suggestion="手机号建议脱敏处理，如 138****1234"
    ),
    DetectionRule(
        name="银行卡号",
        category=SensitiveCategory.PERSONAL,
        risk_level=RiskLevel.HIGH,
        patterns=[
            (r'(?:^|[^0-9])((?:\d{16}|\d{19}))(?:$|[^0-9])', 1),
        ],
        keywords=["银行卡", "卡号", "储蓄卡", "信用卡"],
        suggestion="银行卡号属于高度敏感信息，建议删除"
    ),
    DetectionRule(
        name="邮箱",
        category=SensitiveCategory.PERSONAL,
        risk_level=RiskLevel.LOW,
        patterns=[
            (r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', 1),
        ],
        keywords=["邮箱", "电子邮件", "Email", "email", "E-mail"],
        suggestion="公开场景下邮箱建议脱敏处理"
    ),
    DetectionRule(
        name="固定电话",
        category=SensitiveCategory.PERSONAL,
        risk_level=RiskLevel.LOW,
        patterns=[
            (r'(?:^|[^0-9])(0\d{2,3}-?[1-9]\d{6,7})(?:$|[^0-9])', 1),
        ],
        keywords=["电话", "固话", "座机"],
        suggestion="固定电话属于一般敏感信息，可根据场景决定是否保留"
    ),
    DetectionRule(
        name="护照号",
        category=SensitiveCategory.PERSONAL,
        risk_level=RiskLevel.HIGH,
        patterns=[
            (r'(?:^|[^0-9A-Za-z])((?:[EG]\d{8})|(?:[MSP]\d{7}))(?:$|[^0-9A-Za-z])', 1),
        ],
        keywords=["护照", "护照号"],
        suggestion="护照号属于高度敏感信息，建议删除"
    ),
    
    # ---------- 企业敏感信息 ----------
    DetectionRule(
        name="统一社会信用代码",
        category=SensitiveCategory.ENTERPRISE,
        risk_level=RiskLevel.MEDIUM,
        patterns=[
            (r'(?:^|[^0-9A-Za-z])(([0-9A-HJ-NPQRTUWXY]{2}\d{6}[0-9A-HJ-NPQRTUWXY]{10}))(?:$|[^0-9A-Za-z])', 1),
        ],
        keywords=["统一社会信用代码", "信用代码", "社会信用代码"],
        suggestion="统一社会信用代码属于企业敏感信息，建议脱敏处理"
    ),
    DetectionRule(
        name="合同金额",
        category=SensitiveCategory.ENTERPRISE,
        risk_level=RiskLevel.MEDIUM,
        patterns=[
            (r'(?:合同金额|金额|总价|报价|预算)[：:]\s*([¥￥]?\s*\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?\s*(?:元|万元|万|CNY|RMB)?)', 1),
            (r'(?:^|[^0-9.])([¥￥]\s*\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?\s*(?:元|万元|万)?)(?:$|[^0-9.])', 1),
        ],
        keywords=["合同金额", "金额", "总价", "报价", "预算", "预算金额"],
        suggestion="金额信息属于商业敏感信息，外发前建议脱敏或替换为区间"
    ),
    DetectionRule(
        name="项目编号",
        category=SensitiveCategory.ENTERPRISE,
        risk_level=RiskLevel.MEDIUM,
        patterns=[
            (r'(?:项目编号|项目代号|项目代码)[：:]\s*([A-Za-z0-9\-_]{3,30})', 1),
        ],
        keywords=["项目编号", "项目代号", "项目代码"],
        suggestion="项目编号属于内部信息，建议替换为通用描述"
    ),
    
    # ---------- 开发者密钥 ----------
    DetectionRule(
        name="API_Key",
        category=SensitiveCategory.DEVELOPER,
        risk_level=RiskLevel.HIGH,
        patterns=[
            (r'(?:api[_\-]?key|apikey|api_key)[\s=:]*["\']?([a-zA-Z0-9_\-]{16,64})["\']?', 1),
            (r'(?:sk-)[a-zA-Z0-9]{20,64}', 0),
            (r'(?:pk-)[a-zA-Z0-9]{20,64}', 0),
        ],
        keywords=["API_KEY", "api_key", "apikey", "APIKey", "sk-", "pk-"],
        suggestion="API Key 属于高度敏感信息，请立即删除并使用环境变量或密钥管理服务"
    ),
    DetectionRule(
        name="AccessKey",
        category=SensitiveCategory.DEVELOPER,
        risk_level=RiskLevel.HIGH,
        patterns=[
            (r'(?:access[_\-]?key|accesskey|access_key)[\s=:]*["\']?([A-Z0-9]{16,24})["\']?', 1),
            (r'(?:AKIA|ASIA|LTAI)[A-Z0-9]{16}', 0),
        ],
        keywords=["ACCESS_KEY", "access_key", "AccessKey", "AKIA", "LTAI"],
        suggestion="AccessKey 属于高度敏感信息，请立即删除并轮换密钥"
    ),
    DetectionRule(
        name="SecretKey",
        category=SensitiveCategory.DEVELOPER,
        risk_level=RiskLevel.HIGH,
        patterns=[
            (r'(?:secret[_\-]?key|secretkey|secret_key)[\s=:]*["\']?([a-zA-Z0-9/+=]{20,64})["\']?', 1),
        ],
        keywords=["SECRET_KEY", "secret_key", "SecretKey", "secret"],
        suggestion="SecretKey 属于高度敏感信息，请立即删除并轮换密钥"
    ),
    DetectionRule(
        name="Token",
        category=SensitiveCategory.DEVELOPER,
        risk_level=RiskLevel.HIGH,
        patterns=[
            (r'(?:token|auth_token|access_token)[\s=:]*["\']?([a-zA-Z0-9_\-\.]{20,128})["\']?', 1),
            (r'(?:Bearer\s+)([a-zA-Z0-9_\-\.]{20,256})', 1),
        ],
        keywords=["TOKEN", "token", "Bearer", "access_token", "auth_token"],
        suggestion="Token 属于高度敏感信息，请立即删除并轮换"
    ),
    DetectionRule(
        name="Password",
        category=SensitiveCategory.DEVELOPER,
        risk_level=RiskLevel.HIGH,
        patterns=[
            (r'(?:password|passwd|pwd)[\s=:]*["\']?([^\s"\']{4,64})["\']?', 1),
            (r'(?:DB_PASSWORD|DATABASE_PASSWORD|ADMIN_PASSWORD)[\s=:]*["\']?([^\s"\']{4,64})["\']?', 1),
        ],
        keywords=["PASSWORD", "password", "passwd", "pwd"],
        suggestion="密码明文属于高度敏感信息，请使用环境变量或密钥管理服务"
    ),
    DetectionRule(
        name="数据库连接串",
        category=SensitiveCategory.DEVELOPER,
        risk_level=RiskLevel.HIGH,
        patterns=[
            (r'((?:mysql|postgresql|postgres|mongodb|redis|mssql|oracle)://[^:]+:[^@]+@[^/\s]+(?:/[^\s]*)?)', 1),
            (r'(?:DATABASE_URL|DB_URL|DB_HOST)[\s=:]*["\']?([^"\']+://[^"\']+)["\']?', 1),
        ],
        keywords=["DATABASE_URL", "DB_URL", "mysql://", "postgresql://", "mongodb://"],
        suggestion="数据库连接串包含密码，属于高度敏感信息，请使用环境变量管理"
    ),
    DetectionRule(
        name="JWT",
        category=SensitiveCategory.DEVELOPER,
        risk_level=RiskLevel.HIGH,
        patterns=[
            (r'(eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*)', 1),
        ],
        keywords=["JWT", "jwt", "json web token"],
        suggestion="JWT Token 属于高度敏感信息，请立即删除并轮换"
    ),
    DetectionRule(
        name="SSH私钥",
        category=SensitiveCategory.DEVELOPER,
        risk_level=RiskLevel.HIGH,
        patterns=[
            (r'(-----BEGIN (?:OPENSSH |RSA |EC |DSA )?PRIVATE KEY-----[\s\S]*?-----END (?:OPENSSH |RSA |EC |DSA )?PRIVATE KEY-----)', 1),
        ],
        keywords=["PRIVATE KEY", "私钥", "id_rsa"],
        suggestion="SSH 私钥属于极度敏感信息，请立即删除并重新生成密钥对"
    ),
    DetectionRule(
        name="服务器IP",
        category=SensitiveCategory.DEVELOPER,
        risk_level=RiskLevel.MEDIUM,
        patterns=[
            (r'(?:^|[^0-9.])(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?:$|[^0-9.])', 1),
        ],
        keywords=["IP", "地址", "服务器", "host"],
        suggestion="服务器 IP 属于一般敏感信息，可根据场景决定是否保留"
    ),
    
    # ---------- 文件风险特征 ----------
    DetectionRule(
        name="云厂商密钥",
        category=SensitiveCategory.DEVELOPER,
        risk_level=RiskLevel.HIGH,
        patterns=[
            (r'(?:aws[_\-]?secret[_\-]?access[_\-]?key)[\s=:]*["\']?([a-zA-Z0-9/+=]{40})["\']?', 1),
            (r'(?:aliyun[_\-]?access[_\-]?key[_\-]?secret)[\s=:]*["\']?([a-zA-Z0-9]{30,})["\']?', 1),
        ],
        keywords=["AWS", "aliyun", "阿里云", "腾讯云", "华为云"],
        suggestion="云厂商密钥属于高度敏感信息，请立即删除并轮换"
    ),
]


class SensitiveInfoDetector:
    """敏感信息检测器"""
    
    def __init__(self):
        self.rules = RULES
    
    def detect(self, text: str, file_path: str, file_name: str) -> List[Finding]:
        """
        检测文本中的敏感信息
        
        Args:
            text: 文件文本内容
            file_path: 文件完整路径
            file_name: 文件名
        
        Returns:
            发现的敏感信息列表
        """
        findings = []
        lines = text.split('\n')
        
        for rule in self.rules:
            for line_idx, line in enumerate(lines, start=1):
                # 先用正则匹配
                for pattern, group in rule.patterns:
                    for match in re.finditer(pattern, line, re.IGNORECASE):
                        raw_value = match.group(group) if group > 0 else match.group(0)
                        
                        # 去重：避免同一个位置重复匹配
                        if self._is_duplicate(findings, file_path, line_idx, raw_value):
                            continue
                        
                        # 构建上下文
                        context = line.strip()
                        if len(context) > 100:
                            context = context[:100] + "..."
                        
                        finding = Finding(
                            file_path=file_path,
                            file_name=file_name,
                            type=rule.name,
                            category=rule.category,
                            risk_level=rule.risk_level,
                            raw_value=raw_value,
                            masked_value="",  # 后续脱敏处理
                            line_number=line_idx,
                            context=context,
                            suggestion=rule.suggestion
                        )
                        findings.append(finding)
        
        # 额外：检测文件名风险
        findings.extend(self._detect_filename_risk(file_path, file_name, lines))
        
        return findings
    
    def _is_duplicate(self, findings: List[Finding], file_path: str, line_number: int, raw_value: str) -> bool:
        """检查是否重复"""
        for f in findings:
            if (f.file_path == file_path and 
                f.line_number == line_number and 
                f.raw_value == raw_value):
                return True
        return False
    
    def _detect_filename_risk(self, file_path: str, file_name: str, lines: List[str]) -> List[Finding]:
        """检测文件名中的风险特征"""
        findings = []
        
        # 高风险文件名
        high_risk_names = {
            '.env': "环境变量配置文件，通常包含密钥和密码",
            'secrets.json': "密钥配置文件",
            'private_key.pem': "私钥文件",
            'id_rsa': "SSH 私钥文件",
            'application-prod.yml': "生产环境配置文件",
            'config-prod.yaml': "生产环境配置文件",
        }
        
        # 检查文件名是否直接匹配
        if file_name in high_risk_names:
            findings.append(Finding(
                file_path=file_path,
                file_name=file_name,
                type="风险文件名",
                category=SensitiveCategory.FILE_FEATURE,
                risk_level=RiskLevel.HIGH,
                raw_value=file_name,
                masked_value=file_name,
                line_number=0,
                context=f"文件名: {file_name}",
                suggestion=f"{high_risk_names[file_name]}，请确认是否误提交"
            ))
        
        # 检查文件内容中是否包含密码相关配置
        password_keywords = ['password', 'passwd', 'pwd', 'secret', 'key', 'token', 'credential']
        for line_idx, line in enumerate(lines, start=1):
            line_lower = line.lower()
            for keyword in password_keywords:
                if keyword in line_lower and ('=' in line or ':' in line):
                    # 检查是否已经作为其他类型被检测到
                    already_found = False
                    for f in findings:
                        if f.line_number == line_idx and f.category == SensitiveCategory.DEVELOPER:
                            already_found = True
                            break
                    if not already_found:
                        findings.append(Finding(
                            file_path=file_path,
                            file_name=file_name,
                            type="密码相关配置",
                            category=SensitiveCategory.FILE_FEATURE,
                            risk_level=RiskLevel.HIGH,
                            raw_value=line.strip(),
                            masked_value="",
                            line_number=line_idx,
                            context=line.strip()[:100],
                            suggestion="配置文件中发现密码相关字段，建议检查是否为明文密码"
                        ))
                    break  # 每行只报告一次
        
        return findings
