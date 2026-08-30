"""操作系统探测：平台、版本、架构。"""

import platform


def run() -> dict:
    try:
        return {
            "os": platform.system(),            # Windows / Linux / Darwin
            "version": platform.version(),
            "release": platform.release(),
            "architecture": platform.machine(),  # x86_64 / arm64 / AMD64
            "python_version": platform.python_version(),
        }
    except Exception as exc:  # 采集失败记 unknown，不崩溃
        return {
            "os": "unknown",
            "version": "unknown",
            "release": "unknown",
            "architecture": "unknown",
            "python_version": platform.python_version(),
            "error": str(exc),
        }
