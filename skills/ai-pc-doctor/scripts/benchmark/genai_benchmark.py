"""GenAI / LLM Benchmark：用 openvino_genai 实测小型 LLM 的生成性能。

指标（定义见 references/benchmark_metrics.md）：
model_load_time / TTFT / TPOT / throughput / input_tokens / output_tokens /
peak RAM / device。结果标 BENCHMARKED。

模型来源策略（设计文档 49 节）：
- 默认 ModelScope；环境变量 AIPC_DOCTOR_MODEL_SOURCE=huggingface 可切换。
- 缓存到 models/genai/ 下专属子目录，已存在（含 openvino_model.xml）则跳过下载。
- < 1GB 免确认；> 1GB 需用户确认（size check 钩子见 _check_download_size）。
- 下载失败 / 设备不支持记结构化错误，不崩溃；NPU 不支持时记 UNSUPPORTED。
"""

import os
import time
from pathlib import Path

# 默认模型：Qwen 0.5B INT4（OpenVINO 版，约 370MB，< 1GB 免确认）
DEFAULT_MODEL_IDS = {
    "modelscope": "OpenVINO/Qwen2-0.5B-Instruct-int4-ov",
    "huggingface": "OpenVINO/Qwen2-0.5B-Instruct-int4-ov",
}
DEFAULT_MODEL_DIRNAME = "Qwen2-0.5B-Instruct-int4-ov"

# 安全设计：> 1GB 的模型下载必须先征得用户同意（V0.2 默认模型远低于此值）
CONFIRM_THRESHOLD_MB = 1024

# 固定 prompt 与生成参数：控制测试时长，full 模式整体保持在几分钟内
PROMPT = ("请用中文简要介绍人工智能在个人电脑上的三个典型应用场景，"
          "每个场景用一句话说明，并给出对应的英文术语。" * 2)
MAX_NEW_TOKENS = 64
WARMUP_RUNS = 1

_GB = 1024 ** 3


def _model_source() -> str:
    return os.environ.get("AIPC_DOCTOR_MODEL_SOURCE", "modelscope").lower()


def _check_download_size(size_mb: float) -> None:
    """size check 钩子：> 1GB 的模型下载需用户确认（V0.2 不支持交互，直接拒绝）。"""
    if size_mb > CONFIRM_THRESHOLD_MB:
        raise RuntimeError(
            f"模型大小约 {size_mb:.0f}MB，超过 {CONFIRM_THRESHOLD_MB}MB，"
            "按安全设计需用户确认后下载，请改用更小的模型或 --model 指定本地路径。")


def _download_modelscope(model_id: str, target_dir: Path) -> None:
    from modelscope import snapshot_download
    # 预估大小（size check 钩子）
    from modelscope.hub.api import HubApi
    files = HubApi().get_model_files(model_id, recursive=True)
    total_mb = sum(f.get("Size", 0) for f in files) / (1024 ** 2)
    _check_download_size(total_mb)
    snapshot_download(model_id, local_dir=str(target_dir))


def _download_huggingface(model_id: str, target_dir: Path) -> None:
    from huggingface_hub import snapshot_download
    snapshot_download(model_id, local_dir=str(target_dir))


def ensure_model(models_dir: Path, model_override: str = None) -> Path:
    """确保 LLM 可用：--model 指定的本地路径优先，否则按来源策略下载/复用缓存。"""
    if model_override:
        p = Path(model_override).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"--model 指定的路径不存在: {p}")
        return p

    target = models_dir / "genai" / DEFAULT_MODEL_DIRNAME
    if (target / "openvino_model.xml").exists():
        return target  # 缓存命中，零下载

    source = _model_source()
    model_id = DEFAULT_MODEL_IDS.get(source, DEFAULT_MODEL_IDS["modelscope"])
    target.parent.mkdir(parents=True, exist_ok=True)
    if source == "huggingface":
        _download_huggingface(model_id, target)
    else:
        _download_modelscope(model_id, target)
    return target


class _MetricsStreamer:
    """streamer 回调：记录首 token 时间与全部 token 到达时刻（测 TTFT/TPOT）。"""

    def __init__(self):
        self.token_times = []

    def __call__(self, _subword):
        self.token_times.append(time.perf_counter())
        import openvino_genai as ov_genai
        return ov_genai.StreamingStatus.RUNNING


def _err(code: str, message: str, severity: str = "warning") -> dict:
    return {"code": code, "module": "benchmark", "message": message,
            "severity": severity}


def run_device(model_dir: Path, device: str) -> dict:
    """在指定设备上执行 LLM 生成式 benchmark。psutil/openvino_genai 延迟导入。"""
    result = {"status": "SKIPPED", "label": "BENCHMARKED", "device": device}
    try:
        import psutil
        import openvino_genai as ov_genai
    except ImportError as exc:
        # 依赖缺失属于"未运行"而非"测试失败"：记 SKIPPED / NOT_RUN
        result["status"] = "SKIPPED"
        result["label"] = "NOT_RUN"
        result["error"] = _err("GENAI_DEP_MISSING", f"依赖缺失: {exc}")
        return result

    proc = psutil.Process()
    try:
        # 模型加载时间
        base_rss = proc.memory_info().rss
        t0 = time.perf_counter()
        pipe = ov_genai.LLMPipeline(str(model_dir), device)
        load_s = time.perf_counter() - t0

        tokenizer = pipe.get_tokenizer()
        # encode 返回 TokenizedInputs，input_ids 是 ov.Tensor（shape [1, N]）
        encoded = tokenizer.encode(PROMPT)
        input_tokens = int(encoded.input_ids.get_shape()[-1])

        config = ov_genai.GenerationConfig()
        config.max_new_tokens = MAX_NEW_TOKENS

        # warmup（不计入指标）
        for _ in range(WARMUP_RUNS):
            pipe.generate(PROMPT, config)

        # 计时运行：streamer 回调记录 token 到达时刻
        streamer = _MetricsStreamer()
        peak_rss = base_rss
        t_start = time.perf_counter()
        gen_result = pipe.generate(PROMPT, config, streamer=streamer)
        t_end = time.perf_counter()
        peak_rss = max(peak_rss, proc.memory_info().rss)

        times = streamer.token_times
        output_tokens = len(times)
        # 优先用 perf_metrics 的精确 token 数
        try:
            output_tokens = int(
                gen_result.perf_metrics.get_num_generated_tokens())
        except Exception:
            pass

        if not times:
            raise RuntimeError("streamer 未收到任何 token，无法计算 TTFT/TPOT")
        ttft_ms = (times[0] - t_start) * 1000
        gen_s = t_end - times[0]
        tpot_ms = (gen_s / (output_tokens - 1) * 1000) if output_tokens > 1 else None
        throughput = output_tokens / (t_end - t_start)

        result.update({
            "status": "PASS",
            "model": model_dir.name,
            "model_path": str(model_dir),
            "model_load_time_s": round(load_s, 2),
            "ttft_ms": round(ttft_ms, 1),
            "tpot_ms": round(tpot_ms, 1) if tpot_ms is not None else None,
            "throughput_tokens_per_s": round(throughput, 1),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "max_new_tokens": MAX_NEW_TOKENS,
            "peak_rss_delta_mb": round((peak_rss - base_rss) / (1024 ** 2), 1),
        })
    except Exception as exc:
        msg = str(exc)
        # NPU 上 LLM 不支持属预期（静态 shape / 插件限制）
        if device.upper().startswith("NPU"):
            result["status"] = "UNSUPPORTED"
            result["error"] = _err("GENAI_NPU_UNSUPPORTED",
                                   f"NPU 上 LLM 推理不支持: {msg}")
        else:
            result["status"] = "FAIL"
            result["error"] = _err("GENAI_BENCH_FAILED",
                                   f"{device} 上 LLM benchmark 失败: {msg}")
    return result


def run(models_dir: Path, devices: list, model_override: str = None) -> dict:
    """GenAI benchmark 入口：准备模型（下载/缓存），逐设备实测。"""
    try:
        model_dir = ensure_model(models_dir, model_override)
    except Exception as exc:
        return {
            "status": "SKIPPED",
            "label": "NOT_RUN",
            "results": [],
            "error": _err("MODEL_DOWNLOAD_FAILED",
                          f"模型获取失败（检查网络或模型源）: {exc}"),
        }

    size_mb = round(
        sum(f.stat().st_size for f in model_dir.rglob("*") if f.is_file())
        / (1024 ** 2), 1)
    results = [run_device(model_dir, d) for d in devices]
    # 只有真实尝试过推理（PASS/FAIL/UNSUPPORTED）才标 BENCHMARKED；
    # 纯依赖缺失导致的 SKIPPED 标 NOT_RUN
    attempted = [r for r in results
                 if r.get("status") in ("PASS", "FAIL", "UNSUPPORTED")]
    if any(r.get("status") == "PASS" for r in results):
        status = "PASS"
    elif attempted:
        status = "FAIL"
    else:
        status = "SKIPPED"
    return {
        "status": status,
        "label": "BENCHMARKED" if attempted else "NOT_RUN",
        "model": model_dir.name,
        "model_size_mb": size_mb,
        "model_source": "local" if model_override else _model_source(),
        "results": results,
    }
