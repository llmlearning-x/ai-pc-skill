# OpenVINO 设备插件说明

## CPU 插件

- 所有平台可用，兼容性最好，是 fallback 设备。
- 支持 Intel / AMD x86-64 与 ARM64（含 Apple Silicon，仅 CPU 推理）。

## GPU 插件

- 面向 Intel 核显 / Arc 独显（Windows / Linux）。
- 需要正确的 Intel 显卡驱动；Linux 需要安装 compute-runtime（intel-opencl-icd 等）。
- **macOS 不支持**：Apple GPU 不在 OpenVINO GPU 插件支持范围内。

## NPU 插件

- 面向 Intel AI Boost（Core Ultra 系列），主要支持 Windows 11，Linux 视驱动状态。
- **只支持静态 Shape**：动态 Shape 模型编译失败属预期行为，应记 UNSUPPORTED，使用静态输入模型重测。
- **首次编译慢**：可能长达数十秒，编译超时建议 ≥ 120 秒。
- macOS 不支持。

## 常见故障与排查

| 现象 | 可能原因 |
| --- | --- |
| OS 检测到 NPU，但 OpenVINO 不可用 | NPU 驱动未正确安装；OpenVINO 版本过旧；Python 环境不一致；当前系统不支持该 NPU 插件 |
| NPU 编译报 shape 错误 | 模型含动态 Shape，NPU 仅支持静态 Shape（记 UNSUPPORTED） |
| NPU 编译极慢 | 首次编译正常现象，需独立的长超时（≥120s） |
| GPU 设备缺失 | 显卡驱动未安装；Linux 缺 compute-runtime；macOS 属预期不支持 |
| `import openvino` 失败 | 未安装或动态库问题：建议 `python -m venv .venv && pip install openvino` |

## 状态用语约定

- 硬件探测只用 `detected` / `not_detected` / `unknown`。
- Runtime 探测用 `runtime_detected` / `runtime_not_detected`。
- 检测到硬件 ≠ 支持推理，以 Smoke Test 实测（PASS / FAIL / UNSUPPORTED / SKIPPED）为准。
