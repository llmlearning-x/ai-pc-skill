"""OpenVINO 设备探测：通过 ov.Core().available_devices 获取 Runtime 可见设备。

逐设备标记 runtime_detected / runtime_not_detected。
"""

# 目标设备集合（AI PC 三件套）
KNOWN_DEVICES = ("CPU", "GPU", "NPU")


def run() -> dict:
    try:
        import openvino as ov
        core = ov.Core()
        available = list(core.available_devices)
    except ImportError:
        return {
            "available_devices": [],
            "devices": {},
            "error": {
                "code": "OPENVINO_NOT_INSTALLED",
                "module": "openvino_probe",
                "message": "OpenVINO 未安装，无法探测设备。",
                "severity": "error",
            },
        }
    except Exception as exc:
        return {
            "available_devices": [],
            "devices": {},
            "error": {
                "code": "OPENVINO_DEVICE_PROBE_FAILED",
                "module": "openvino_probe",
                "message": f"设备探测失败: {exc}",
                "severity": "warning",
            },
        }

    # available_devices 可能返回如 "GPU.0" 这类带序号的名称，归类到主设备
    devices = {}
    for name in KNOWN_DEVICES:
        matched = [d for d in available if d == name or d.startswith(name + ".")]
        devices[name] = {
            "status": "runtime_detected" if matched else "runtime_not_detected",
            "instances": matched,
        }
    # 其它未归类设备原样列出
    others = [d for d in available
              if not any(d == n or d.startswith(n + ".") for n in KNOWN_DEVICES)]
    return {
        "available_devices": available,
        "devices": devices,
        "other_devices": others,
    }
