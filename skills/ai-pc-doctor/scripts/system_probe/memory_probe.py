"""内存与磁盘探测：总/可用 RAM、磁盘空间。基于 psutil。

psutil 延迟导入：未安装时记 unknown，不影响其它探测与 OpenVINO 引导流程。
"""

_GB = 1024 ** 3


def run() -> dict:
    result = {}
    try:
        import psutil
    except ImportError:
        return {
            "total_gb": "unknown",
            "available_gb": "unknown",
            "error": "psutil 未安装，内存信息不可知（pip install psutil）",
        }
    try:
        vm = psutil.virtual_memory()
        result.update({
            "total_gb": round(vm.total / _GB, 1),
            "available_gb": round(vm.available / _GB, 1),
            "used_percent": vm.percent,
        })
    except Exception as exc:
        result.update({
            "total_gb": "unknown",
            "available_gb": "unknown",
            "error": str(exc),
        })
    try:
        disk = psutil.disk_usage("/")
        result["disk"] = {
            "total_gb": round(disk.total / _GB, 1),
            "free_gb": round(disk.free / _GB, 1),
        }
    except Exception as exc:
        result["disk"] = {"error": str(exc)}
    return result
