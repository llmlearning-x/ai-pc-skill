"""模型容量估算：按可用 RAM 估算 1B~32B 模型 × FP16/INT8/INT4 的可运行性。

估算规则（依据见 references/model_memory_reference.md）：
- 权重 ≈ 参数量 × 每参数字节数（FP16=2B, INT8=1B, INT4=0.5B）
- 总需求 ≈ 权重 × 1.5 运行时开销系数（KV cache、运行时缓冲、tokenizer 等）
- 与可用 RAM 对比给出推荐等级，全部标记 ESTIMATED（非实测）。
"""

# 每参数字节数
BYTES_PER_PARAM = {"FP16": 2.0, "INT8": 1.0, "INT4": 0.5}

# 运行时开销系数：KV cache + 运行时 buffer + tokenizer + 框架开销
RUNTIME_OVERHEAD = 1.5

# 估算的模型规模（十亿参数）
MODEL_SIZES_B = [1, 3, 7, 14, 32]

# 推荐等级：总需求占可用 RAM 的比例阈值
# EXCELLENT ≤30% / RECOMMENDED ≤50% / LIMITED ≤80% / 其余 NOT_RECOMMENDED
_THRESHOLDS = [(0.30, "EXCELLENT"), (0.50, "RECOMMENDED"), (0.80, "LIMITED")]


def _grade(required_gb: float, available_gb: float) -> str:
    ratio = required_gb / available_gb
    for limit, level in _THRESHOLDS:
        if ratio <= limit:
            return level
    return "NOT_RECOMMENDED"


def run(available_ram_gb) -> dict:
    """按可用内存（GB）估算各规模模型的可运行性。

    available_ram_gb 为 None/unknown 时整体记 UNKNOWN。
    """
    if not isinstance(available_ram_gb, (int, float)) or available_ram_gb <= 0:
        return {
            "status": "UNKNOWN",
            "label": "ESTIMATED",
            "note": "可用内存未知，无法估算。",
            "models": [],
        }

    models = []
    for size_b in MODEL_SIZES_B:
        for quant, bpp in BYTES_PER_PARAM.items():
            weights_gb = size_b * bpp  # 1B 参数 × bytes/param ≈ GB（十进制近似）
            required_gb = weights_gb * RUNTIME_OVERHEAD
            models.append({
                "model_size": f"{size_b}B",
                "quantization": quant,
                "weights_gb_estimated": round(weights_gb, 1),
                "required_ram_gb_estimated": round(required_gb, 1),
                "recommendation": _grade(required_gb, available_ram_gb),
                "label": "ESTIMATED",
            })
    return {
        "status": "OK",
        "label": "ESTIMATED",
        "available_ram_gb": available_ram_gb,
        "runtime_overhead_factor": RUNTIME_OVERHEAD,
        "note": "容量估算基于可用内存与每参数字节数，"
                "实际性能以 Benchmark 实测为准。",
        "models": models,
    }
