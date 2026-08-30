"""基础推理 Benchmark：mnist-8 逐设备 warmup 3 次 + 计时 50 次。

输出 compile_time_ms / min/median/avg/max latency_ms / stddev_ms /
throughput，并用 psutil 记录 peak RAM（本进程 RSS 峰值增量）与平均 CPU%。
所有结果为实测，标记 BENCHMARKED。

注意：单次运行的数值受当时系统负载影响，跨运行波动属正常；
对比设备性能建议以中位数（median）为准，标准差（stddev）反映波动幅度。
"""

import statistics
import time
from pathlib import Path

WARMUP_RUNS = 3
TIMED_RUNS = 50


def run_device(model_path: Path, device: str) -> dict:
    """对单个设备执行推理 benchmark。psutil/numpy/openvino 延迟导入。"""
    result = {"device": device, "status": "SKIPPED", "label": "BENCHMARKED"}
    try:
        import numpy as np
        import openvino as ov
        import psutil
    except ImportError as exc:
        result["note"] = f"依赖缺失: {exc}"
        return result

    proc = psutil.Process()
    try:
        core = ov.Core()
        model = core.read_model(str(model_path))

        start = time.perf_counter()
        compiled = core.compile_model(model, device)
        compile_ms = (time.perf_counter() - start) * 1000

        input_layer = compiled.inputs[0]
        data = np.random.rand(*input_layer.shape).astype(np.float32)

        base_rss = proc.memory_info().rss
        cpu_samples = []
        rss_samples = []
        proc.cpu_percent(interval=None)  # 初始化计数器

        # warmup
        for _ in range(WARMUP_RUNS):
            compiled(data)

        # 计时
        latencies = []
        for _ in range(TIMED_RUNS):
            t0 = time.perf_counter()
            compiled(data)
            latencies.append((time.perf_counter() - t0) * 1000)
            cpu_samples.append(proc.cpu_percent(interval=None))
            rss_samples.append(proc.memory_info().rss)

        avg = sum(latencies) / len(latencies)
        peak_rss_mb = round((max(rss_samples) - base_rss) / (1024 ** 2), 1)
        result.update({
            "status": "PASS",
            "compile_time_ms": round(compile_ms, 1),
            "min_latency_ms": round(min(latencies), 3),
            "median_latency_ms": round(statistics.median(latencies), 3),
            "avg_latency_ms": round(avg, 3),
            "max_latency_ms": round(max(latencies), 3),
            "stddev_ms": round(statistics.stdev(latencies), 3),
            "throughput_infer_per_s": round(1000.0 / avg, 1) if avg > 0 else 0,
            "warmup_runs": WARMUP_RUNS,
            "timed_runs": TIMED_RUNS,
            "peak_rss_delta_mb": max(peak_rss_mb, 0.0),
            "avg_cpu_percent": round(sum(cpu_samples) / len(cpu_samples), 1)
            if cpu_samples else None,
            "measurement_note": "数值受运行时系统负载影响，跨运行波动属正常；"
                                "设备对比建议以中位数为准。",
        })
    except Exception as exc:
        result["status"] = "FAIL"
        result["error"] = str(exc)
    return result


def run(model_path: Path, devices: list) -> list:
    return [run_device(model_path, d) for d in devices]
