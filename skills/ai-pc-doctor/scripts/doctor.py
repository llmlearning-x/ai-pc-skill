#!/usr/bin/env python3
"""AI PC Doctor CLI 入口。

用法：
    python scripts/doctor.py [--mode quick|standard|full]
                             [--device CPU|GPU|NPU] [--output 目录]

模式：
    quick     硬件检测 + OpenVINO 检测 + 设备检查（< 30s，不输出评分）
    standard  默认。quick + Smoke Test + 基础 Benchmark + 容量估算 + 部署建议 + 报告
    full      standard + 全设备横向 Benchmark + GenAI/LLM Benchmark

full 模式启动前做依赖预检（openvino_genai / modelscope），缺失时跳过
GenAI 环节并给出安装指引，不中断其余体检。

默认输出目录按模式分目录（output/quick/、output/standard/、output/full/），
避免不同模式的报告互相覆盖。

路径均相对脚本位置解析，可从任意工作目录运行。
"""

import argparse
import subprocess
import sys
from pathlib import Path

# 保证从任意工作目录运行时都能 import 同级包
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

MODEL_PATH = BASE_DIR / "models" / "mnist-8.onnx"
MODELS_DIR = BASE_DIR / "models"
DEFAULT_OUTPUT = BASE_DIR / "output"
TOOL_VERSION = "0.3"

from system_probe import cpu_probe, gpu_probe, memory_probe, npu_probe, os_probe
from openvino_probe import device_probe, runtime_probe, smoke_test
from benchmark import genai_benchmark, inference_benchmark
from estimator import model_capacity
from advisor import deployment_advisor
from report import html_report, json_report, markdown_report

VALID_DEVICES = ("CPU", "GPU", "NPU")

# 各模式总步骤数（用于进度显示）
_TOTAL_STEPS = {"quick": 2, "standard": 4, "full": 5}


def _collect_errors(*parts) -> list:
    """从各模块结果中收集结构化错误。"""
    errors = []
    for part in parts:
        if isinstance(part, dict) and isinstance(part.get("error"), dict):
            errors.append(part["error"])
    return errors


def _missing_full_deps(model_override: str = None) -> list:
    """full 模式依赖预检：返回缺失的 Python 包名列表。

    - openvino_genai：LLM 实测必需，始终检查
    - modelscope：仅默认模型未缓存且未指定 --model 时需要（下载用）
    """
    missing = []
    try:
        import openvino_genai  # noqa: F401
    except ImportError:
        missing.append("openvino-genai")

    if not model_override:
        cached = (MODELS_DIR / "genai" /
                  genai_benchmark.DEFAULT_MODEL_DIRNAME / "openvino_model.xml")
        if not cached.exists():
            try:
                import modelscope  # noqa: F401
            except ImportError:
                missing.append("modelscope")
    return missing


def run_probes(data: dict, total_steps: int) -> None:
    """System Probe + OpenVINO Runtime/Device Probe（quick 模式内容）。"""
    print(f"[1/{total_steps}] 系统环境检测 ...")
    data["system"] = os_probe.run()
    data["cpu"] = cpu_probe.run()
    data["gpu"] = gpu_probe.run()
    data["npu"] = npu_probe.run()
    data["memory"] = memory_probe.run()

    print(f"[2/{total_steps}] OpenVINO 环境检测 ...")
    data["openvino"] = runtime_probe.run()
    if data["openvino"].get("installed"):
        data["openvino"].update(device_probe.run())


def _select_devices(data: dict, device_filter: str) -> list:
    """确定参与 smoke/benchmark 的设备列表。"""
    devices = data.get("openvino", {}).get("devices") or {}
    runtime_ok = [d for d in VALID_DEVICES
                  if devices.get(d, {}).get("status") == "runtime_detected"]
    if device_filter:
        if device_filter in runtime_ok:
            return [device_filter]
        return []  # 指定设备 runtime 不可见：记 SKIPPED，由上层写说明
    return runtime_ok


def run_tests(data: dict, device_filter: str, errors: list, total_steps: int) -> None:
    """Smoke Test + 基础 Benchmark（standard 模式内容）。"""
    print(f"[3/{total_steps}] Smoke Test（加载模型 → 编译 → 推理 → 校验）...")
    devices = _select_devices(data, device_filter)
    if device_filter and not devices:
        data["device_tests"] = [{
            "device": device_filter, "compile": "SKIPPED", "inference": "SKIPPED",
            "note": f"{device_filter} 未被 OpenVINO Runtime 检测到。",
        }]
        data["benchmarks"] = []
        return

    data["device_tests"] = smoke_test.run(MODEL_PATH, devices)
    for t in data["device_tests"]:
        print(f"      {t['device']}: compile={t['compile']} "
              f"inference={t['inference']}")

    # benchmark 只跑 smoke 编译通过的设备，避免重复编译失败的开销
    bench_devices = [t["device"] for t in data["device_tests"]
                     if t.get("compile") == "PASS" and t.get("inference") == "PASS"]
    print(f"[4/{total_steps}] 基础推理 Benchmark（warmup 3 + 计时 50）...")
    data["benchmarks"] = inference_benchmark.run(MODEL_PATH, bench_devices)
    for b in data["benchmarks"]:
        if b.get("status") == "PASS":
            print(f"      {b['device']}: avg={b['avg_latency_ms']}ms "
                  f"throughput={b['throughput_infer_per_s']} infer/s")


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="doctor.py", description="AI PC Doctor：本地 AI 部署环境体检与性能评测")
    parser.add_argument("--mode", choices=["quick", "standard", "full"],
                        default="standard", help="体检模式（默认 standard）")
    parser.add_argument("--device", choices=VALID_DEVICES, default=None,
                        help="只测试指定设备")
    parser.add_argument("--output", type=Path, default=None,
                        help="报告输出目录（默认按模式分目录：output/<mode>/，"
                             "避免不同模式报告互相覆盖）")
    parser.add_argument("--model", type=str, default=None,
                        help="GenAI Benchmark 使用的本地模型路径"
                        "（OpenVINO IR 格式，默认自动下载 Qwen 0.5B INT4）")
    args = parser.parse_args()

    if not MODEL_PATH.exists():
        print(f"[错误] Smoke Test 模型缺失: {MODEL_PATH}", file=sys.stderr)
        return 2

    print(f"AI PC Doctor v{TOOL_VERSION} — mode={args.mode}"
          + (f" device={args.device}" if args.device else ""))

    total_steps = _TOTAL_STEPS[args.mode]
    # 默认输出目录按模式分目录，避免不同模式的报告互相覆盖
    output_dir = args.output or (DEFAULT_OUTPUT / args.mode)

    data: dict = {"mode": args.mode}  # mode 供评分/报告模块判断模式语义
    run_probes(data, total_steps)
    errors = _collect_errors(data.get("openvino", {}))

    # OpenVINO 缺失：输出结构化错误 + 引导步骤，非零退出（不自动安装）
    if not data["openvino"].get("installed"):
        err = data["openvino"].get("error", {})
        print(f"\n[错误] {err.get('code')}: {err.get('message')}")
        print("引导步骤：")
        for step in data["openvino"].get("install_guide", []):
            print(f"  {step}")
        data["genai"] = None  # 报告 GenAI 节显示占位
        advisor_out = deployment_advisor.run(data)
        data.update(advisor_out)
        data["errors"] = errors
        report = json_report.build_report(args.mode, args.device, data)
        _write_reports(report, output_dir)
        return 2

    if args.mode in ("standard", "full"):
        run_tests(data, args.device, errors, total_steps)
        data["capacity"] = model_capacity.run(
            data.get("memory", {}).get("available_gb"))
    else:
        data["device_tests"] = []
        data["benchmarks"] = []
        data["capacity"] = {}

    # GenAI / LLM Benchmark：full 模式真正执行；quick/standard 输出占位
    if args.mode == "full":
        devices = _select_devices(data, args.device)
        if args.device and not devices:
            data["genai"] = {
                "status": "SKIPPED", "label": "NOT_RUN", "results": [],
                "error": {"code": "DEVICE_NOT_AVAILABLE", "module": "benchmark",
                          "message": f"{args.device} 未被 OpenVINO Runtime 检测到，"
                                     "GenAI Benchmark 跳过。",
                          "severity": "warning"},
            }
        else:
            # 依赖预检：缺失时不启动 GenAI 环节（记 SKIPPED 并给出安装指引），
            # 其余体检结果照常输出
            missing = _missing_full_deps(args.model)
            if missing:
                print(f"[5/{total_steps}] GenAI / LLM Benchmark 跳过"
                      f"（依赖缺失: {', '.join(missing)}）")
                data["genai"] = {
                    "status": "SKIPPED", "label": "NOT_RUN", "results": [],
                    "error": {
                        "code": "GENAI_DEP_MISSING", "module": "benchmark",
                        "message": "依赖缺失: " + ", ".join(missing)
                                   + "。安装后重跑 full 模式可启用 LLM 实测："
                                   "pip install " + " ".join(missing),
                        "severity": "warning",
                    },
                }
            else:
                print(f"[5/{total_steps}] GenAI / LLM Benchmark"
                      "（模型可能需首次下载）...")
                data["genai"] = genai_benchmark.run(MODELS_DIR, devices, args.model)
            for r in data["genai"].get("results", []):
                if r.get("status") == "PASS":
                    print(f"      {r['device']}: load={r['model_load_time_s']}s "
                          f"TTFT={r['ttft_ms']}ms TPOT={r['tpot_ms']}ms "
                          f"throughput={r['throughput_tokens_per_s']} tokens/s")
                else:
                    print(f"      {r.get('device')}: {r.get('status')}")
            gerr = data["genai"].get("error")
            if isinstance(gerr, dict):
                errors.append(gerr)
            for r in data["genai"].get("results", []):
                if isinstance(r.get("error"), dict):
                    errors.append(r["error"])
    else:
        data["genai"] = None  # 报告 GenAI 节显示占位（规划中已落地，full 模式可用）

    # full 模式：GenAI benchmark 成功后，自动启动本地对话体验服务
    data["demo_chat"] = _launch_demo_chat(data)
    if data["demo_chat"].get("running"):
        print(f"\n[体验] 本地对话服务已启动: {data['demo_chat']['url']}")
        print(f"        模型: {data['demo_chat']['model']}")
        print(f"        设备: {data['demo_chat']['device']}")
        print("        在浏览器中打开上述地址即可与模型对话\n")

    advisor_out = deployment_advisor.run(data)
    data.update(advisor_out)
    data["errors"] = errors + _collect_errors(data.get("openvino", {}))

    report = json_report.build_report(args.mode, args.device, data)
    paths = _write_reports(report, output_dir)

    score = report.get("readiness_score") or {}
    if score.get("score") is not None:
        print(f"\nAI PC Readiness Score: {score['score']} / 100"
              f"（{score.get('level')}）")
    else:
        print(f"\n{score.get('note', '')}")
    print("报告：")
    for p in paths:
        print(f"  {p}")
    return 0


def _launch_demo_chat(data: dict) -> dict:
    """如果 full 模式 GenAI benchmark 成功，启动本地对话体验服务。

    返回结构化信息供报告模块展示。服务在后台子进程运行，
    用户手动关闭终端或发送 SIGTERM 即可停止。
    """
    genai = data.get("genai")
    if not genai or genai.get("status") != "PASS":
        return {"running": False, "reason": "GenAI benchmark 未通过，对话体验不可用"}

    # 取第一个 PASS 结果的模型路径和设备
    pass_results = [r for r in genai.get("results", [])
                    if r.get("status") == "PASS"]
    if not pass_results:
        return {"running": False, "reason": "无可用设备通过 GenAI benchmark"}

    # 优先用最佳设备（throughput 最高）
    best = max(pass_results,
               key=lambda r: r.get("throughput_tokens_per_s", 0))
    model_path = best.get("model_path")
    device = best.get("device", "CPU")
    if not model_path:
        return {"running": False, "reason": "无法获取模型路径"}

    # 启动 demo_chat 服务（后台子进程）
    server_script = SCRIPT_DIR / "demo_chat" / "server.py"
    if not server_script.exists():
        return {"running": False, "reason": f"对话服务脚本缺失: {server_script}"}

    env = dict(__import__("os").environ)
    env["AIPC_DOCTOR_MODEL_DIR"] = str(Path(model_path).resolve())

    try:
        proc = subprocess.Popen(
            [sys.executable, str(server_script),
             "--model-dir", model_path,
             "--device", device,
             "--port", "8899",
             "--host", "127.0.0.1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            creationflags=__import__("subprocess").CREATE_NO_WINDOW if hasattr(__import__("subprocess"), "CREATE_NO_WINDOW") else 0,
        )
        return {
            "running": True,
            "url": "http://127.0.0.1:8899",
            "model": Path(model_path).name,
            "device": device,
            "pid": proc.pid,
            "note": "服务在后台运行，关闭终端或结束进程后自动停止",
        }
    except Exception as exc:
        return {"running": False, "reason": f"启动失败: {exc}"}


def _write_reports(report: dict, output_dir: Path) -> list:
    output_dir = output_dir.resolve()
    return [
        json_report.write(report, output_dir),
        markdown_report.write(report, output_dir),
        html_report.write(report, output_dir),
    ]


if __name__ == "__main__":
    sys.exit(main())
