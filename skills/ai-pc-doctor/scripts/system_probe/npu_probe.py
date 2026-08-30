"""NPU 探测：仅报告 detected / not_detected / unknown。

检测到硬件 ≠ 支持推理，是否可用需 OpenVINO Runtime 后续验证。
Windows 查 PnP 设备名（单词边界匹配 "AI Boost"/"NPU"/"Neural"，
避免 "Input" 之类普通词的子串误匹配），Linux 查 /dev/accel 或 lspci
含 neural，macOS 记 not_detected。
"""

import os
import platform
import subprocess

_TIMEOUT = 15


def _run_cmd(cmd: list) -> str:
    try:
        out = subprocess.run(
            cmd, capture_output=True, text=True, timeout=_TIMEOUT
        )
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""


def _probe_windows() -> dict:
    out = _run_cmd([
        "powershell", "-NoProfile", "-Command",
        "Get-PnpDevice | Where-Object { $_.FriendlyName -match "
        "'\\bNPU\\b|\\bNeural\\b|AI Boost' } | Select-Object FriendlyName,Status "
        "| ConvertTo-Json",
    ])
    if not out:
        return {"status": "not_detected"}
    try:
        import json
        data = json.loads(out)
        if isinstance(data, dict):
            data = [data]
        if data:
            return {
                "status": "detected",
                "name": data[0].get("FriendlyName", "unknown"),
                "device_status": data[0].get("Status", "unknown"),
            }
        return {"status": "not_detected"}
    except Exception:
        return {"status": "unknown"}


def _probe_linux() -> dict:
    try:
        if os.path.isdir("/dev/accel") and os.listdir("/dev/accel"):
            return {"status": "detected", "name": "/dev/accel accel device"}
    except Exception:
        return {"status": "unknown"}
    out = _run_cmd(["lspci"])
    if out:
        for line in out.splitlines():
            if "neural" in line.lower() or "npu" in line.lower():
                return {"status": "detected", "name": line.split(":", 2)[-1].strip()}
        return {"status": "not_detected"}
    return {"status": "unknown"}


def run() -> dict:
    system = platform.system()
    try:
        if system == "Darwin":
            # Apple Neural Engine 不受 OpenVINO NPU 插件支持
            return {"status": "not_detected",
                    "note": "macOS 无 OpenVINO 支持的 Intel NPU。"}
        if system == "Windows":
            return _probe_windows()
        if system == "Linux":
            return _probe_linux()
        return {"status": "unknown"}
    except Exception as exc:
        return {"status": "unknown", "error": str(exc)}
