"""部署建议与 Readiness Score 规则引擎。

规则来源：硬件信息 + OpenVINO Runtime 探测 + Smoke Test / Benchmark 实测，
不依赖 LLM 做技术判定；LLM 只负责把结构化结果解释给用户。

Readiness Score 仅对目标平台（Windows/Linux + Intel CPU）评分；
macOS / 非 Intel 平台走 Graceful Degradation：score 为 null，附降级说明。
"""

import platform

# 评分权重（满分 100）
WEIGHTS = {"cpu": 15, "gpu": 20, "npu": 20, "memory": 15,
           "openvino": 15, "benchmark": 15}

# 分数解释
_LEVELS = [(90, "Excellent AI PC"), (75, "AI Ready"), (60, "Basic Local AI"),
           (40, "Limited"), (0, "Not Recommended")]


def is_target_platform(report: dict) -> bool:
    """目标平台 = Windows/Linux + Intel CPU。其余走降级。"""
    if platform.system() == "Darwin":
        return False
    vendor = str(report.get("cpu", {}).get("vendor", "")).lower()
    model = str(report.get("cpu", {}).get("model", "")).lower()
    return "intel" in vendor or "genuineintel" in vendor or "intel" in model


def degradation_note(report: dict) -> str:
    os_name = report.get("system", {}).get("os", "unknown")
    arch = report.get("system", {}).get("architecture", "unknown")
    return (f"当前平台（{os_name} / {arch}）不是主要 Intel AI PC 目标平台，"
            f"进入降级模式：仅输出环境说明，不输出 Readiness Score。")


def _score_by_smoke(smoke: dict, full: int, partial: int, os_bonus: int = 0) -> int:
    """按 smoke 结果折算：PASS 满分，runtime detected 部分分，FAIL/无 0 分。"""
    if smoke.get("compile") == "PASS" and smoke.get("inference") == "PASS":
        return full
    if smoke.get("compile") in ("PASS", "UNSUPPORTED"):
        return partial
    return os_bonus


def _find_smoke(device_tests: list, device: str) -> dict:
    for t in device_tests or []:
        if t.get("device") == device:
            return t
    return {}


def compute_score(report: dict) -> dict:
    """计算 Readiness Score。非目标平台返回 score=null 与降级说明。"""
    if not is_target_platform(report):
        return {
            "score": None,
            "level": None,
            "note": degradation_note(report),
            "disclaimer": "Readiness Score 是工具内部综合评价，不代表 Intel 官方认证。",
        }

    # quick 模式只做环境检测、不做推理实测：GPU/benchmark 项必然得 0 分，
    # 输出低分会误导（同一台机器 quick 与 standard/full 的分数不可比较），
    # 因此 quick 模式不输出评分，引导用户跑 standard/full 获取实测评分。
    if report.get("mode") == "quick":
        return {
            "score": None,
            "level": None,
            "note": "quick 模式仅做环境检测、未做推理实测，不输出 Readiness Score"
                    "（避免与 standard/full 的实测评分混淆）。"
                    "如需评分请运行 standard 或 full 模式。",
            "disclaimer": "Readiness Score 是工具内部综合评价，不代表 Intel 官方认证。",
        }

    device_tests = report.get("device_tests") or []
    devices = (report.get("openvino", {}).get("devices") or {})
    mem = report.get("memory", {})
    benchmarks = report.get("benchmarks") or []

    parts = {}
    # CPU：smoke PASS 满分；runtime 可见给部分分
    smoke_cpu = _find_smoke(device_tests, "CPU")
    parts["cpu"] = _score_by_smoke(
        smoke_cpu, 15, 10,
        os_bonus=5 if devices.get("CPU", {}).get("status") == "runtime_detected" else 0)
    # GPU / NPU：实测 PASS 满分，runtime 可见部分分，OS 可见但 runtime 不可见少量分
    for dev, full in (("GPU", 20), ("NPU", 20)):
        smoke = _find_smoke(device_tests, dev)
        runtime_ok = devices.get(dev, {}).get("status") == "runtime_detected"
        os_ok = report.get(dev.lower(), {}).get("status") == "detected"
        parts[dev.lower()] = _score_by_smoke(
            smoke, full, full // 2,
            os_bonus=5 if os_ok and not runtime_ok else 0)
    # 内存
    total = mem.get("total_gb")
    if isinstance(total, (int, float)):
        parts["memory"] = (15 if total >= 32 else 12 if total >= 16
                           else 8 if total >= 8 else 4 if total >= 4 else 0)
    else:
        parts["memory"] = 0
    # OpenVINO 环境
    ov = report.get("openvino", {})
    n_dev = len(ov.get("available_devices") or [])
    parts["openvino"] = (15 if ov.get("installed") and n_dev >= 1
                         else 10 if ov.get("installed") else 0)
    # Benchmark 实测
    if any(b.get("status") == "PASS" for b in benchmarks):
        parts["benchmark"] = 15
    elif benchmarks:
        parts["benchmark"] = 5
    else:
        parts["benchmark"] = 0

    score = sum(parts.values())
    level = next(name for limit, name in _LEVELS if score >= limit)
    return {
        "score": score,
        "level": level,
        "components": parts,
        "note": "评分为初始经验权重，仅供横向参考。",
        "disclaimer": "Readiness Score 是工具内部综合评价，不代表 Intel 官方认证。",
    }


def build_recommendations(report: dict) -> list:
    """结合实测结果生成设备推荐。CPU=兼容/fallback，GPU=大吞吐，NPU=低功耗轻量。"""
    recs = []
    device_tests = report.get("device_tests") or []
    benchmarks = {b.get("device"): b for b in (report.get("benchmarks") or [])}

    smoke_map = {}
    for t in device_tests:
        dev = t.get("device")
        if dev not in smoke_map or (
                t.get("compile") == "PASS" and t.get("inference") == "PASS"):
            smoke_map[dev] = t

    # CPU：兼容性基准与 fallback
    cpu = smoke_map.get("CPU", {})
    if cpu.get("compile") == "PASS" and cpu.get("inference") == "PASS":
        lat = benchmarks.get("CPU", {}).get("avg_latency_ms")
        text = "CPU 实测可用，适合兼容性任务、小型模型与兜底（fallback）推理"
        if lat is not None:
            text += f"；实测平均延迟 {lat} ms"
        recs.append({"device": "CPU", "recommendation": text + "。"})
    elif cpu:
        recs.append({"device": "CPU", "recommendation":
                     f"CPU smoke test 未通过（compile={cpu.get('compile')}），"
                     "请检查 OpenVINO 安装。"})

    # GPU：大吞吐（必须实测通过才推荐）
    gpu = smoke_map.get("GPU", {})
    if gpu.get("compile") == "PASS" and gpu.get("inference") == "PASS":
        recs.append({"device": "GPU", "recommendation":
                     "GPU 实测可用，推荐用于 LLM/VLM、大吞吐与批量推理。"})
    elif gpu.get("compile") == "UNSUPPORTED":
        recs.append({"device": "GPU", "recommendation":
                     "GPU 被 Runtime 检测到但模型编译不支持，"
                     "建议检查模型 shape 与 GPU 驱动版本。"})
    elif report.get("gpu", {}).get("status") == "detected":
        recs.append({"device": "GPU", "recommendation":
                     "系统检测到 GPU，但 OpenVINO Runtime 未能实测通过，"
                     "可能原因：驱动未正确安装或 OpenVINO 版本过旧。"})

    # NPU：低功耗轻量任务（必须实测通过才推荐）
    npu = smoke_map.get("NPU", {})
    if npu.get("compile") == "PASS" and npu.get("inference") == "PASS":
        recs.append({"device": "NPU", "recommendation":
                     "NPU 实测可用，推荐用于低功耗、长期运行的轻量任务"
                     "（Embedding / OCR / 轻量 Transformer）。"})
    elif npu.get("compile") == "UNSUPPORTED":
        recs.append({"device": "NPU", "recommendation":
                     "NPU 编译报 shape 相关错误：NPU 仅支持静态 Shape 模型，"
                     "建议使用静态输入的模型重新测试。"})
    elif report.get("npu", {}).get("status") == "detected":
        recs.append({"device": "NPU", "recommendation":
                     "系统检测到 NPU，但 OpenVINO 实测未通过，"
                     "可能原因：NPU 驱动版本与 OpenVINO NPU 插件不匹配。"})

    # 非 Intel 独立显卡：OpenVINO GPU 插件不管理，需明确告知用户
    all_gpus = report.get("gpu", {}).get("all_gpus") or []
    _NON_INTEL = ("nvidia", "geforce", "quadro", "amd", "radeon")
    discrete = [g for g in all_gpus
                if any(k in str(g).lower() for k in _NON_INTEL)]
    if discrete:
        recs.append({"device": "独立显卡", "recommendation":
                     f"检测到 {discrete[0]} 等非 Intel 显卡：OpenVINO 的 GPU 插件"
                     "仅支持 Intel 显卡，该显卡未参与本次体检与评分；"
                     "如需利用它运行本地大模型，请使用 CUDA 生态工具"
                     "（如 Ollama / llama.cpp 的 CUDA 后端）。"})

    if not recs:
        recs.append({"device": None, "recommendation":
                     "未获取到可用的实测结果，请先完成 OpenVINO 环境配置后重新运行。"})
    return recs


# 模型推荐清单（V0.2）：结合可用 RAM 估算 + 实测 benchmark。
# 推荐规则详见 references/model_memory_reference.md「模型推荐规则」一节。
MODEL_CATALOG = [
    {"name": "Qwen2.5-0.5B-Instruct", "size_b": 0.5, "quant": "INT4"},
    {"name": "Qwen2.5-1.5B-Instruct", "size_b": 1.5, "quant": "INT4"},
    {"name": "Qwen2.5-3B-Instruct", "size_b": 3, "quant": "INT4"},
    {"name": "Qwen2.5-7B-Instruct", "size_b": 7, "quant": "INT4"},
]

# 与 estimator/model_capacity.py 保持一致的估算参数
_INT4_BYTES_PER_PARAM = 0.5
_RUNTIME_OVERHEAD = 1.5
_GRADE_THRESHOLDS = [(0.30, "EXCELLENT"), (0.50, "RECOMMENDED"),
                     (0.80, "LIMITED")]


def _grade(required_gb: float, available_gb: float) -> str:
    ratio = required_gb / available_gb
    for limit, level in _GRADE_THRESHOLDS:
        if ratio <= limit:
            return level
    return "NOT_RECOMMENDED"


def _smoke_passed(report: dict, device: str) -> bool:
    for t in report.get("device_tests") or []:
        if (t.get("device") == device and t.get("compile") == "PASS"
                and t.get("inference") == "PASS"):
            return True
    return False


def _pick_device(report: dict, size_b: float) -> str:
    """推荐设备：GPU 实测过优先（大吞吐）；轻量模型可用 NPU（低功耗）；
    CPU 兜底（兼容性）。未实测的设备不推荐。"""
    if _smoke_passed(report, "GPU"):
        return "GPU"
    if size_b <= 1.5 and _smoke_passed(report, "NPU"):
        return "NPU"
    if _smoke_passed(report, "CPU"):
        return "CPU"
    return "unknown"


def build_model_recommendations(report: dict) -> list:
    """输出具体模型推荐清单，标注 ESTIMATED / BENCHMARKED。

    BENCHMARKED：full 模式 GenAI Benchmark 实测通过的同规模模型。
    其余按可用 RAM 估算（ESTIMATED）。
    """
    available = report.get("memory", {}).get("available_gb")
    if not isinstance(available, (int, float)) or available <= 0:
        return []

    # GenAI 实测过的模型规模（默认 0.5B）
    benchmarked_sizes = set()
    genai = report.get("genai")
    if isinstance(genai, dict):
        for res in genai.get("results") or []:
            if res.get("status") == "PASS":
                benchmarked_sizes.add(0.5)  # 默认模型 Qwen 0.5B INT4

    recs = []
    for m in MODEL_CATALOG:
        required = m["size_b"] * _INT4_BYTES_PER_PARAM * _RUNTIME_OVERHEAD
        grade = _grade(required, available)
        label = "BENCHMARKED" if m["size_b"] in benchmarked_sizes else "ESTIMATED"
        device = _pick_device(report, m["size_b"])
        if grade == "NOT_RECOMMENDED":
            reason = (f"估算需 {required:.1f} GB 内存（可用 {available:.1f} GB），"
                      "不推荐在本机运行")
        elif label == "BENCHMARKED":
            reason = "已在本机完成真实生成式 Benchmark 实测"
        else:
            reason = (f"估算需 {required:.1f} GB 内存（可用 {available:.1f} GB），"
                      "容量上可运行，实际体验以实测为准")
        recs.append({
            "name": f"{m['name']} {m['quant']}",
            "size_b": m["size_b"],
            "grade": grade,
            "device": device,
            "label": label,
            "reason": reason,
        })
    return recs


def run(report: dict) -> dict:
    return {
        "readiness_score": compute_score(report),
        "recommendations": build_recommendations(report),
        "model_recommendations": build_model_recommendations(report),
    }
