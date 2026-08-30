"""CPU 探测：型号、厂商、物理/逻辑核心数。

macOS 用 sysctl，Linux 读 /proc/cpuinfo，Windows 用 CIM/wmic。
全部 try/except + subprocess timeout，失败记 unknown。
"""

import platform
import re
import subprocess

_TIMEOUT = 10


def _run_cmd(cmd: list) -> str:
    """执行命令并返回 stdout，失败返回空串。"""
    try:
        out = subprocess.run(
            cmd, capture_output=True, text=True, timeout=_TIMEOUT
        )
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""


def _probe_macos() -> dict:
    info = {}
    brand = _run_cmd(["sysctl", "-n", "machdep.cpu.brand_string"])
    if brand:
        info["model"] = brand
    vendor = _run_cmd(["sysctl", "-n", "machdep.cpu.vendor"])
    if vendor:
        info["vendor"] = vendor
    phys = _run_cmd(["sysctl", "-n", "hw.physicalcpu"])
    if phys.isdigit():
        info["physical_cores"] = int(phys)
    logical = _run_cmd(["sysctl", "-n", "hw.logicalcpu"])
    if logical.isdigit():
        info["logical_cores"] = int(logical)
    return info


def _probe_linux() -> dict:
    info = {}
    try:
        with open("/proc/cpuinfo", encoding="utf-8", errors="ignore") as fh:
            text = fh.read()
        m = re.search(r"model name\s*:\s*(.+)", text)
        if m:
            info["model"] = m.group(1).strip()
        v = re.search(r"vendor_id\s*:\s*(.+)", text)
        if v:
            info["vendor"] = v.group(1).strip()
        info["logical_cores"] = len(re.findall(r"^processor\s*:", text, re.M)) or None
        phys = re.findall(r"^core id\s*:\s*(\d+)", text, re.M)
        if phys:
            info["physical_cores"] = len(set(phys))
    except Exception:
        pass
    return info


def _probe_windows() -> dict:
    info = {}
    out = _run_cmd([
        "powershell", "-NoProfile", "-Command",
        "Get-CimInstance Win32_Processor | Select-Object -First 1 "
        "Name,Manufacturer,NumberOfCores,NumberOfLogicalProcessors "
        "| ConvertTo-Json",
    ])
    if out:
        try:
            import json
            data = json.loads(out)
            info["model"] = data.get("Name")
            info["vendor"] = data.get("Manufacturer")
            info["physical_cores"] = data.get("NumberOfCores")
            info["logical_cores"] = data.get("NumberOfLogicalProcessors")
        except Exception:
            pass
    if "model" not in info:
        # wmic 兜底（老系统）
        out = _run_cmd(["wmic", "cpu", "get", "name", "/value"])
        m = re.search(r"Name=(.+)", out)
        if m:
            info["model"] = m.group(1).strip()
    return info


def run() -> dict:
    result = {
        "vendor": "unknown",
        "model": "unknown",
        "physical_cores": "unknown",
        "logical_cores": "unknown",
        "architecture": platform.machine(),
    }
    try:
        system = platform.system()
        if system == "Darwin":
            probed = _probe_macos()
        elif system == "Linux":
            probed = _probe_linux()
        elif system == "Windows":
            probed = _probe_windows()
        else:
            probed = {}
        for key, value in probed.items():
            if value not in (None, ""):
                result[key] = value
    except Exception as exc:
        result["error"] = str(exc)
    return result
