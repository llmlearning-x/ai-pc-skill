"""GPU 探测：名称、驱动、状态。

Windows 用 PowerShell CIM，Linux 用 lspci。
macOS：Apple GPU 不受 OpenVINO 支持，记 not_detected 并附说明。
失败记 unknown。
"""

import platform
import re
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
        "Get-CimInstance Win32_VideoController | Select-Object "
        "Name,DriverVersion,AdapterRAM | ConvertTo-Json",
    ])
    if not out:
        return {}
    try:
        import json
        data = json.loads(out)
        if isinstance(data, dict):
            data = [data]
        # 优先 Intel GPU（AI PC 目标场景）
        gpus = [g for g in data if g.get("Name")]
        if not gpus:
            return {}
        intel = [g for g in gpus if "intel" in g["Name"].lower()]
        gpu = (intel or gpus)[0]
        result = {"gpu": gpu["Name"], "status": "detected"}
        if gpu.get("DriverVersion"):
            result["driver"] = gpu["DriverVersion"]
        ram = gpu.get("AdapterRAM")
        if isinstance(ram, int) and ram > 0:
            result["memory_gb"] = round(ram / (1024 ** 3), 1)
        if len(gpus) > 1:
            result["all_gpus"] = [g["Name"] for g in gpus]
        return result
    except Exception:
        return {}


def _probe_linux() -> dict:
    out = _run_cmd(["lspci"])
    if not out:
        return {}
    lines = [l for l in out.splitlines()
             if re.search(r"VGA|3D controller|Display", l, re.I)]
    if not lines:
        return {}
    # 取第一个 Intel GPU，否则取第一个显卡
    intel = [l for l in lines if "intel" in l.lower()]
    line = (intel or lines)[0]
    name = line.split(":", 2)[-1].strip()
    return {"gpu": name, "status": "detected",
            "all_gpus": [l.split(":", 2)[-1].strip() for l in lines]}


def run() -> dict:
    result = {"gpu": "unknown", "status": "unknown"}
    system = platform.system()
    try:
        if system == "Darwin":
            # Apple GPU 不在 OpenVINO GPU 插件支持范围内
            return {
                "gpu": "not_detected",
                "status": "not_detected",
                "note": "macOS Apple GPU 不受 OpenVINO GPU 插件支持，"
                        "OpenVINO 在 macOS 上仅支持 CPU 推理。",
            }
        probed = _probe_windows() if system == "Windows" else (
            _probe_linux() if system == "Linux" else {})
        if probed:
            result.update(probed)
        elif system in ("Windows", "Linux"):
            result = {"gpu": "not_detected", "status": "not_detected"}
    except Exception as exc:
        result["error"] = str(exc)
    return result
