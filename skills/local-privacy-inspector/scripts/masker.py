"""
Local Privacy Inspector - Sensitive Data Masker
对检测到的敏感信息进行脱敏处理
"""

import re


def mask_value(value: str, sensitive_type: str) -> str:
    """
    对敏感值进行脱敏处理
    
    Args:
        value: 原始敏感值
        sensitive_type: 敏感信息类型
    
    Returns:
        脱敏后的值
    """
    if not value:
        return ""
    
    # 身份证号
    if sensitive_type == "身份证号":
        return _mask_id_card(value)
    
    # 手机号
    elif sensitive_type == "手机号":
        return _mask_phone(value)
    
    # 银行卡号
    elif sensitive_type == "银行卡号":
        return _mask_bank_card(value)
    
    # 邮箱
    elif sensitive_type == "邮箱":
        return _mask_email(value)
    
    # API Key / AccessKey / SecretKey / Token
    elif sensitive_type in ["API_Key", "AccessKey", "SecretKey", "Token", "JWT"]:
        return _mask_generic(value, keep_start=4, keep_end=4)
    
    # Password
    elif sensitive_type == "Password":
        return "****"
    
    # 数据库连接串
    elif sensitive_type == "数据库连接串":
        return _mask_database_url(value)
    
    # 服务器 IP
    elif sensitive_type == "服务器IP":
        return _mask_ip(value)
    
    # 统一社会信用代码
    elif sensitive_type == "统一社会信用代码":
        return value[:6] + "************"
    
    # 合同金额 / 金额
    elif sensitive_type in ["合同金额", "报价金额", "预算金额"]:
        return _mask_amount(value)
    
    # 项目编号
    elif sensitive_type == "项目编号":
        return _mask_generic(value, keep_start=2, keep_end=2)
    
    # 护照号
    elif sensitive_type == "护照号":
        return value[:2] + "********"
    
    # 固定电话
    elif sensitive_type == "固定电话":
        return _mask_generic(value, keep_start=3, keep_end=2)
    
    # 客户名称 / 公司名称
    elif sensitive_type in ["客户名称", "公司名称"]:
        return _mask_company_name(value)
    
    # SSH私钥
    elif sensitive_type == "SSH私钥":
        return "-----BEGIN PRIVATE KEY-----\n****\n-----END PRIVATE KEY-----"
    
    # 云厂商密钥
    elif sensitive_type == "云厂商密钥":
        return _mask_generic(value, keep_start=4, keep_end=4)
    
    # 密码相关配置 / 风险文件名
    elif sensitive_type in ["密码相关配置", "风险文件名"]:
        # 对配置行进行脱敏：将 = 后面的值替换为 ****
        if '=' in value:
            parts = value.split('=', 1)
            return parts[0].strip() + "=****"
        return "****"
    
    # 默认脱敏
    else:
        return _mask_generic(value, keep_start=2, keep_end=2)


def _mask_phone(value: str) -> str:
    """手机号脱敏：138****5678"""
    digits = re.sub(r'\D', '', value)
    if len(digits) == 11:
        return digits[:3] + "****" + digits[-4:]
    return _mask_generic(value, keep_start=3, keep_end=4)


def _mask_id_card(value: str) -> str:
    """身份证号脱敏：320***********001X"""
    if len(value) >= 14:
        return value[:3] + "***********" + value[-4:]
    return _mask_generic(value, keep_start=3, keep_end=4)


def _mask_email(value: str) -> str:
    """邮箱脱敏：h****@example.com"""
    if '@' in value:
        local, domain = value.split('@', 1)
        if len(local) <= 2:
            masked_local = local[0] + "*"
        else:
            masked_local = local[0] + "****"
        return f"{masked_local}@{domain}"
    return _mask_generic(value, keep_start=2, keep_end=2)


def _mask_bank_card(value: str) -> str:
    """银行卡号脱敏：6222********7890"""
    digits = re.sub(r'\D', '', value)
    if len(digits) >= 16:
        return digits[:4] + "********" + digits[-4:]
    return _mask_generic(value, keep_start=4, keep_end=4)


def _mask_database_url(value: str) -> str:
    """数据库连接串脱敏"""
    # mysql://user:pass@host/db → mysql://user:****@host/db
    return re.sub(r'(://[^:]+:)[^@]+(@)', r'\1****\2', value)


def _mask_ip(value: str) -> str:
    """IP地址脱敏：192.168.*.*"""
    parts = value.split('.')
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.*.*"
    return _mask_generic(value, keep_start=3, keep_end=2)


def _mask_amount(value: str) -> str:
    """金额脱敏：¥**** 元"""
    # 保留货币符号和单位，替换数字
    return re.sub(r'\d[\d,\.]*', '****', value)


def _mask_company_name(value: str) -> str:
    """公司名称脱敏"""
    if len(value) <= 4:
        return value[:1] + "****"
    # 保留前两个和后两个字符
    return value[:2] + "****" + value[-2:] if len(value) > 6 else value[:2] + "****"


def _mask_generic(value: str, keep_start: int = 2, keep_end: int = 2) -> str:
    """通用脱敏：保留前后若干字符，中间替换为*"""
    if len(value) <= keep_start + keep_end:
        return "*" * len(value)
    return value[:keep_start] + "****" + value[-keep_end:]
