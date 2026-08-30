"""Markdown 报告：由报告数据渲染 report.md。"""

from pathlib import Path


def _fmt(value, unit=""):
    if value is None or value == "unknown":
        return "unknown"
    return f"{value}{unit}"


def render(report: dict) -> str:
    sysinfo = report.get("system", {})
    cpu = report.get("cpu", {})
    gpu = report.get("gpu", {})
    npu = report.get("npu", {})
    mem = report.get("memory", {})
    ov = report.get("openvino", {})
    readiness = report.get("readiness_score") or {}
    capacity = report.get("capacity", {})
    genai = report.get("genai")

    lines = ["# AI PC Readiness Report", ""]
    meta = report.get("meta", {})
    lines.append(f"- 模式：{meta.get('mode')}　生成时间：{meta.get('generated_at')}")
    lines.append("")

    # 设备概览
    lines += ["## Device Overview", "",
              f"- OS：{_fmt(sysinfo.get('os'))} {_fmt(sysinfo.get('release'))}"
              f"（{_fmt(sysinfo.get('architecture'))}）",
              f"- CPU：{_fmt(cpu.get('model'))} "
              f"（物理 {_fmt(cpu.get('physical_cores'))} 核 / "
              f"逻辑 {_fmt(cpu.get('logical_cores'))} 核）",
              f"- GPU：{_fmt(gpu.get('gpu'))}"
              + (f"（{gpu['note']}）" if gpu.get("note") else ""),
              f"- NPU：{_fmt(npu.get('status'))}"
              + (f"（{npu['note']}）" if npu.get("note") else ""),
              f"- RAM：{_fmt(mem.get('total_gb'), ' GB')} "
              f"（可用 {_fmt(mem.get('available_gb'), ' GB')}）", ""]

    # Readiness
    lines += ["## AI PC Readiness", ""]
    if readiness.get("score") is not None:
        lines.append(f"**{readiness['score']} / 100（{readiness.get('level')}）**")
        comp = readiness.get("components", {})
        if comp:
            lines.append("")
            lines.append("| 项目 | 得分 |")
            lines.append("| --- | ---: |")
            for k, v in comp.items():
                lines.append(f"| {k} | {v} |")
        lines.append("")
        lines.append(f"> {readiness.get('disclaimer', '')}")
    else:
        lines.append(f"未评分。{readiness.get('note', '')}")
    lines.append("")

    # OpenVINO
    lines += ["## OpenVINO Status", ""]
    if ov.get("installed"):
        lines.append(f"- 版本：{ov.get('version')}")
        devices = ov.get("devices") or {}
        for name, d in devices.items():
            lines.append(f"- {name}：{d.get('status')}")
    else:
        lines.append("- 未安装")
        for step in ov.get("install_guide", []):
            lines.append(f"  - `{step}`")
    lines.append("")

    # Device Compatibility（smoke test）
    lines += ["## Device Compatibility（Smoke Test）", ""]
    tests = report.get("device_tests") or []
    if tests:
        lines += ["| 设备 | 编译 | 推理 | 说明 |", "| --- | --- | --- | --- |"]
        for t in tests:
            note = t.get("error") or t.get("hint") or t.get("note") or ""
            lines.append(f"| {t.get('device')} | {t.get('compile')} | "
                         f"{t.get('inference')} | {note} |")
    else:
        lines.append("未执行（quick 模式不运行 Smoke Test）。")
    lines.append("")

    # Benchmark
    lines += ["## Benchmark（BENCHMARKED）", ""]
    benches = [b for b in (report.get("benchmarks") or [])
               if b.get("status") == "PASS"]
    if benches:
        note = benches[0].get("measurement_note")
        if note:
            lines += [f"> {note}", ""]
        lines += ["| 设备 | 编译 ms | 中位延迟 ms | 平均延迟 ms | 最小/最大 ms "
                  "| 标准差 ms | 吞吐 infer/s "
                  "| 峰值内存增量 MB | 平均 CPU% |",
                  "| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |"]
        for b in benches:
            lines.append(
                f"| {b['device']} | {b['compile_time_ms']} "
                f"| {b.get('median_latency_ms', '-')} "
                f"| {b['avg_latency_ms']} "
                f"| {b['min_latency_ms']} / {b['max_latency_ms']} "
                f"| {b.get('stddev_ms', '-')} "
                f"| {b['throughput_infer_per_s']} "
                f"| {b.get('peak_rss_delta_mb', '-')} "
                f"| {b.get('avg_cpu_percent', '-')} |")
    else:
        lines.append("未执行或无实测数据。")
    lines.append("")

    # GenAI
    lines += ["## GenAI Performance", ""]
    if isinstance(genai, dict) and genai.get("results"):
        lines.append(f"模型：{genai.get('model')}（{genai.get('model_size_mb')} MB，"
                     f"来源 {genai.get('model_source')}）　**BENCHMARKED**")
        lines.append("")
        lines += ["| 设备 | 加载 s | TTFT ms | TPOT ms | 吞吐 tokens/s "
                  "| 输入/输出 tokens | 峰值内存增量 MB | 状态 |",
                  "| --- | ---: | ---: | ---: | ---: | --- | ---: | --- |"]
        for g in genai["results"]:
            if g.get("status") == "PASS":
                lines.append(
                    f"| {g['device']} | {g['model_load_time_s']} "
                    f"| {g['ttft_ms']} | {g['tpot_ms']} "
                    f"| {g['throughput_tokens_per_s']} "
                    f"| {g['input_tokens']} / {g['output_tokens']} "
                    f"| {g.get('peak_rss_delta_mb', '-')} | PASS |")
            else:
                err = (g.get("error") or {}).get("message", "")
                lines.append(f"| {g.get('device')} | - | - | - | - | - | - "
                             f"| {g.get('status')}（{err}）|")
    elif isinstance(genai, dict):
        if genai.get("status") == "SKIPPED":
            err = (genai.get("error") or {}).get("message", "")
            lines.append(f"未执行（SKIPPED）：{err}")
        else:
            err = (genai.get("error") or {}).get("message", "未执行")
            lines.append(f"执行失败：{err}")
    else:
        lines.append("未执行（GenAI/LLM Benchmark 仅在 full 模式运行）。")
    lines.append("")

    # Demo Chat 本地体验
    demo = report.get("demo_chat")
    lines += ["## 本地体验（Live Demo）", ""]
    if demo and demo.get("running"):
        lines.append(f"✅ **本地对话服务已启动**")
        lines.append(f"- 地址：**{demo['url']}**")
        lines.append(f"- 模型：{demo['model']}　·　设备：{demo['device']}")
        lines.append(f"- {demo.get('note', '')}")
    elif demo:
        lines.append(f"⏹ 未启动：{demo.get('reason', '未知原因')}")
    else:
        lines.append("仅在 full 模式且 GenAI benchmark 通过时可用。")
    lines.append("")

    # Model Capacity
    lines += ["## Model Capacity（ESTIMATED）", ""]
    models = capacity.get("models") or []
    if models:
        lines.append(f"> {capacity.get('note', '')}")
        lines.append("")
        lines += ["| 模型规模 | 量化 | 权重估算 GB | 需求内存估算 GB | 推荐等级 |",
                  "| --- | --- | ---: | ---: | --- |"]
        for m in models:
            lines.append(f"| {m['model_size']} | {m['quantization']} "
                         f"| {m['weights_gb_estimated']} "
                         f"| {m['required_ram_gb_estimated']} "
                         f"| {m['recommendation']} |")
    else:
        lines.append(capacity.get("note", "未执行。"))
    lines.append("")

    # Deployment Recommendation
    lines += ["## Deployment Recommendation", ""]
    model_recs = report.get("model_recommendations") or []
    if model_recs:
        lines += ["| 模型 | 推荐 | 推荐设备 | 依据 | 理由 |",
                  "| --- | --- | --- | --- | --- |"]
        stars = {"EXCELLENT": "★★★★★", "RECOMMENDED": "★★★★",
                 "LIMITED": "★★★", "NOT_RECOMMENDED": "不建议",
                 "UNKNOWN": "未知"}
        for m in model_recs:
            grade = m.get("grade", "UNKNOWN")
            lines.append(f"| {m['name']} | {stars.get(grade, grade)} {grade} "
                         f"| {m.get('device')} | {m.get('label')} "
                         f"| {m.get('reason')} |")
        lines.append("")
    for r in report.get("recommendations") or []:
        prefix = f"- **{r['device']}**" if r.get("device") else "-"
        lines.append(f"{prefix} {r.get('recommendation')}")
    lines.append("")

    # Issues & Fixes
    lines += ["## Issues & Fixes", ""]
    errors = report.get("errors") or []
    if errors:
        for e in errors:
            lines.append(f"- [{e.get('severity')}] {e.get('code')}：{e.get('message')}")
    else:
        lines.append("未发现问题。")
    lines.append("")
    return "\n".join(lines)


def write(report: dict, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "report.md"
    path.write_text(render(report), encoding="utf-8")
    return path
