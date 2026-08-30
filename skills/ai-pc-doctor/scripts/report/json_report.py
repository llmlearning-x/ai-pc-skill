"""JSON 报告：汇总所有模块结果写入 report.json。"""

import json
from datetime import datetime, timezone
from pathlib import Path


def build_report(mode: str, device_filter, data: dict) -> dict:
    """按统一结构汇总报告数据。"""
    report = {
        "meta": {
            "tool": "AI PC Doctor",
            "version": "0.3",
            "mode": mode,
            "device_filter": device_filter,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "system": data.get("system", {}),
        "cpu": data.get("cpu", {}),
        "gpu": data.get("gpu", {}),
        "npu": data.get("npu", {}),
        "memory": data.get("memory", {}),
        "openvino": data.get("openvino", {}),
        "device_tests": data.get("device_tests", []),
        "benchmarks": data.get("benchmarks", []),
        "capacity": data.get("capacity", {}),
        "readiness_score": data.get("readiness_score"),
        "recommendations": data.get("recommendations", []),
        "model_recommendations": data.get("model_recommendations", []),
        "genai": data.get("genai"),
        "demo_chat": data.get("demo_chat"),
        "errors": data.get("errors", []),
    }
    return report


def write(report: dict, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "report.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    return path
