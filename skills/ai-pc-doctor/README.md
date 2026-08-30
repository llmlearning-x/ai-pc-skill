# AI PC Doctor

本地 AI 部署环境体检与 OpenVINO 性能评测工具（V0.3）。

回答四个问题：**这台电脑能不能跑本地 AI、能跑多大的模型、应该跑在哪个设备上、实际能跑多快。**

## 功能

- 系统环境检测：OS / CPU / GPU / NPU / 内存 / 磁盘
- OpenVINO 检测：版本、Runtime 可用设备
- Smoke Test：用随仓库分发的 mnist-8 模型对每个设备实测 编译 + 推理
- 基础推理 Benchmark：warmup 3 次 + 计时 50 次，输出中位/平均/最小/最大延迟、标准差、吞吐 / 峰值内存 / CPU 占用
- GenAI / LLM Benchmark（full 模式）：真实小模型生成实测，输出加载时间 / TTFT / TPOT / tokens/s；启动前自动依赖预检，缺失时记 SKIPPED 并给出安装指引
- 模型容量估算：1B~32B × FP16/INT8/INT4，对照可用内存给出推荐等级（ESTIMATED）
- 模型推荐清单：结合实测给出具体模型 + 推荐设备 + 星级（ESTIMATED/BENCHMARKED）
- 部署建议 + AI PC Readiness Score（仅目标平台；quick 模式不输出评分）
- 报告：JSON + Markdown + 交互式单页 HTML Dashboard（自包含，无 CDN 依赖，可离线打开）

V0.3 变更：修复 NPU 设备名子串误匹配（如 "Input" 误报为 NPU）；安装引导补全 full 模式依赖；full 模式增加依赖预检（缺失记 SKIPPED 而非 FAIL）；quick 模式不再输出易误解的低分；默认输出目录按模式分目录防覆盖；Benchmark 计时 20→50 次并披露中位数/标准差；检测到非 Intel 独立显卡时提示需走 CUDA 生态。

## 安装

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt   # 国内可加 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

依赖：`openvino`、`openvino-genai`、`psutil`、`numpy`、`modelscope`。工具不会自动安装任何软件。

## 使用

```bash
python scripts/doctor.py                  # 默认 standard 模式
python scripts/doctor.py --mode quick     # 快速体检（< 30s）
python scripts/doctor.py --mode full      # 完整模式（含 LLM Benchmark 与 HTML Dashboard）
python scripts/doctor.py --device GPU     # 只测指定设备
python scripts/doctor.py --mode full --model ./models/qwen3b  # 指定本地模型
python scripts/doctor.py --output ./out   # 指定输出目录
```

报告输出到 `output/<mode>/`（或 `--output` 指定目录，不同模式默认分目录、互不覆盖）：`report.json`、`report.md`、`AI_PC_Readiness_Report.html`。

| 模式 | 内容 |
| --- | --- |
| quick | 硬件检测 + OpenVINO 检测 + 设备检查（不评分） |
| standard（默认） | quick + Smoke Test + 基础 Benchmark + 容量估算 + 部署建议 |
| full | standard + 全设备横向 Benchmark + GenAI/LLM Benchmark（TTFT/TPOT/tokens/s） |

## 模型下载

full 模式的 GenAI Benchmark 默认模型为 Qwen 0.5B INT4（OpenVINO 版，约 370MB）：

- 默认从 **ModelScope** 下载，缓存到 `models/genai/`，已存在则跳过（零重复下载）。
- 环境变量 `AIPC_DOCTOR_MODEL_SOURCE=huggingface` 可切换为 HuggingFace 源。
- < 1GB 免确认；> 1GB 的模型按安全设计需用户确认（代码内置 size check）。
- `--model 路径` 可使用任意本地 OpenVINO IR 模型覆盖默认模型。
- 核心环境检测（quick/standard）不依赖网络。

## 平台支持

| 平台 | 行为 |
| --- | --- |
| Windows 11 + Intel Core Ultra（目标平台） | 完整流程，输出 Readiness Score |
| Linux + Intel | 完整流程，NPU 视驱动状态 |
| macOS（Apple Silicon） | Graceful Degradation：仅环境说明，不评分，不崩溃 |

## 设计原则

- 数据全部来自真实环境（系统命令 + OpenVINO Runtime + 实测推理），采集失败记 unknown，不崩溃。
- 理论支持 ≠ 实测支持；容量估算标 ESTIMATED，实测数据标 BENCHMARKED。
- Smoke Test / 基础 Benchmark 使用随仓库分发的 `models/mnist-8.onnx`（约 26KB），离线可跑；full 模式的 LLM Benchmark 需一次性下载约 370MB 默认模型（可缓存复用）。

## 目录结构

```
ai-pc-doctor/
├── SKILL.md            # Skill 定义（供 Agent 调用）
├── requirements.txt
├── models/mnist-8.onnx # Smoke Test 模型（随仓库分发）
├── references/         # 估算规则 / 设备说明 / 指标定义
└── scripts/
    ├── doctor.py       # CLI 入口
    ├── system_probe/   # OS/CPU/GPU/NPU/内存探测
    ├── openvino_probe/ # 运行时/设备/Smoke Test
    ├── benchmark/      # 推理 Benchmark
    ├── estimator/      # 模型容量估算
    ├── advisor/        # 部署建议 + Readiness Score
    └── report/         # JSON / Markdown / HTML 报告
```
