"""
Local Privacy Inspector - Data Models
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class RiskLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SensitiveCategory(str, Enum):
    PERSONAL = "personal"
    ENTERPRISE = "enterprise"
    DEVELOPER = "developer_secret"
    FILE_FEATURE = "file_feature"


@dataclass
class Finding:
    """单个敏感信息发现项"""
    file_path: str
    file_name: str
    type: str
    category: SensitiveCategory
    risk_level: RiskLevel
    raw_value: str
    masked_value: str
    line_number: int
    context: str
    suggestion: str


@dataclass
class FileScanResult:
    """单个文件的扫描结果"""
    file_path: str
    file_name: str
    file_type: str
    file_size: int
    risk_level: RiskLevel
    finding_count: int
    findings: List[Finding] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class ScanReport:
    """扫描报告"""
    file_path: str
    file_name: str
    scan_time: str
    risk_level: RiskLevel
    finding_count: int
    findings: List[Finding] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    report_path: Optional[str] = None
