"""Smoke Test：对每个设备执行 加载模型 → 编译 → 推理 → 校验输出。

状态：PASS / FAIL / UNSUPPORTED / SKIPPED。
- NPU 只支持静态 Shape，shape 相关编译错误记 UNSUPPORTED（预期行为）而非 FAIL。
- NPU 首次编译很慢，编译超时单独设为 120 秒；其它设备 30 秒。
- 超时用线程实现（OpenVINO 编译不可中断），超时后线程在后台自然结束。
"""

import concurrent.futures
import time
from pathlib import Path

# 编译超时（秒）：NPU 首次编译可能长达数十秒
COMPILE_TIMEOUT_DEFAULT = 30
COMPILE_TIMEOUT_NPU = 120

# shape 相关错误关键词：NPU 上动态 shape 编译失败属预期，记 UNSUPPORTED
_SHAPE_ERROR_KEYWORDS = ("shape", "dynamic", "static", "dimension", "rank")


def _is_shape_error(message: str) -> bool:
    msg = message.lower()
    return any(k in msg for k in _SHAPE_ERROR_KEYWORDS)


def _compile_with_timeout(core, model, device, timeout):
    """在线程中编译模型，超时抛 TimeoutError。

    不能用 with 管理 executor：超时场景下 with 退出的 shutdown(wait=True)
    会阻塞等待编译线程结束，使超时失效。这里显式 shutdown(wait=False)，
    让未完成的后台编译线程自然结束（进程退出时被回收）。
    """
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = pool.submit(core.compile_model, model, device)
    try:
        compiled = future.result(timeout=timeout)
    except BaseException:
        pool.shutdown(wait=False, cancel_futures=False)
        raise
    pool.shutdown(wait=False)
    return compiled


def run_device(model_path: Path, device: str) -> dict:
    """对单个设备执行 smoke test，返回结构化结果。"""
    result = {"device": device, "compile": "SKIPPED", "inference": "SKIPPED"}
    try:
        import numpy as np
        import openvino as ov
    except ImportError:
        result["compile"] = "SKIPPED"
        result["note"] = "openvino 或 numpy 未安装"
        return result

    timeout = COMPILE_TIMEOUT_NPU if device.upper().startswith("NPU") \
        else COMPILE_TIMEOUT_DEFAULT

    try:
        core = ov.Core()
        model = core.read_model(str(model_path))
    except Exception as exc:
        result["compile"] = "FAIL"
        result["error"] = f"模型加载失败: {exc}"
        return result

    # 编译（计时 + 超时保护）
    start = time.perf_counter()
    try:
        compiled = _compile_with_timeout(core, model, device, timeout)
    except concurrent.futures.TimeoutError:
        result["compile"] = "FAIL"
        result["error"] = f"编译超时（>{timeout}s）"
        return result
    except Exception as exc:
        msg = str(exc)
        result["compile"] = "UNSUPPORTED" if _is_shape_error(msg) else "FAIL"
        result["error"] = msg
        if device.upper().startswith("NPU"):
            result["hint"] = ("可能原因：NPU 仅支持静态 Shape，或 NPU 驱动版本 "
                              "与 OpenVINO NPU 插件不匹配。")
        return result
    result["compile"] = "PASS"
    result["compile_time_ms"] = round((time.perf_counter() - start) * 1000, 1)

    # 推理：随机输入，校验输出 shape 与数值合法性
    try:
        input_layer = compiled.inputs[0]
        data = np.random.rand(*input_layer.shape).astype(np.float32)
        output = compiled(data)[compiled.outputs[0]]
        if tuple(output.shape) != tuple(compiled.outputs[0].shape):
            raise ValueError(f"输出 shape 异常: {output.shape}")
        if not np.isfinite(output.sum()):
            raise ValueError("输出包含 NaN/Inf")
        result["inference"] = "PASS"
        result["output_shape"] = list(output.shape)
    except Exception as exc:
        result["inference"] = "FAIL"
        result["error"] = f"推理失败: {exc}"
    return result


def run(model_path: Path, devices: list) -> list:
    """对设备列表逐个执行 smoke test。"""
    return [run_device(model_path, d) for d in devices]
