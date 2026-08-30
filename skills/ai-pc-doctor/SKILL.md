---
name: ai-pc-doctor
description: AI PC 本地 AI 部署环境体检与 OpenVINO 性能评测。当用户询问"我的电脑适不适合跑本地 AI / 大模型"、"检查 OpenVINO 环境"、"比较 CPU/GPU/NPU 性能"、"我的电脑能跑多大的模型"时触发。
version: 0.3.0
tags: [AIPC, openvino, benchmark, local-ai]
license: Apache-2.0
---

# AI PC Doctor

本地 AI 部署环境体检 + OpenVINO 性能评测工具。回答：这台电脑能不能跑本地 AI、能跑什么模型、应该跑在哪个设备上、实际能跑多快。

## 何时触发

用户询问本机 AI 能力时，例如：

- 帮我检查一下这台电脑适不适合跑本地 AI
- 测试一下 OpenVINO 环境有没有问题
- 我的电脑能跑 7B 模型吗
- 比较一下 CPU / GPU / NPU 的性能
- 这台机器算 AI PC 吗

## 如何调用

脚本位置：`scripts/doctor.py`（相对本 Skill 目录，可从任意工作目录运行）。

### 模式选择交互（重要）

**用户没有明确指定体检模式时，不要直接套用默认模式**——先用
AskUserQuestion 询问用户选择哪种模式，推荐 standard。

**先渲染对比表，再提问（关键）**：直接提问时，用户只能看到 label 一行字，
分不清三种模式的差异。先用 `show_widget` 渲染一张三模式对比表（标题
`AI_PC_Doctor_体检模式对比`），让用户一眼看清「耗时 / 检测项 / 是否出评分 /
是否需要联网下载模型」四个维度；再紧跟一个 AskUserQuestion 收口。
如果当前环境不支持 widget，则退化为在问题描述里附一段纯文本对比。

#### 提问参数模板

- `question`：`选择体检模式（已附对比表）`
- `header`：`体检模式`
- `multiSelect`：`false`
- 每个 option 的 **label 必须同时带「模式名 + 耗时 + 关键差异」三要素**，
  让 label 本身就承担对比功能，不再依赖 description 兜底：
  - 推荐：`standard｜1~3 分钟｜含实测+跑分+评分（推荐）`
  - `quick｜<30 秒｜仅检测，不实测不评分`
  - `full｜5+ 分钟｜含 LLM 实测+模型下载（首次约 370MB）`
- 每个 option 的 **description 必须列出该模式**新增 / 不做的能力**，
  按「✅ 包含 / ❌ 不含」格式，与其他模式形成纵向对比：
  - quick：`✅ 硬件清单 · OpenVINO 设备探测` / `❌ 无冒烟测试 · 无跑分 · 无评分 · 无模型推荐`
  - standard：`✅ quick 全部 · 冒烟测试 · 基础跑分 · 容量估算 · 模型推荐 · 综合评分` / `❌ 不含 LLM 实测 · 不下载模型`
  - full：`✅ standard 全部 · 全设备横向跑分 · GenAI/LLM 真实推理实测（首跑下载 Qwen-0.5B INT4）` / `❌ 需联网下载模型`

label + description 共同保证：**就算用户只扫一眼 label 也能区分三种模式**，
不会因为 description 被折叠 / 截断就分不清差异。

#### 对比表渲染模板（show_widget）

调用 `read_me(modules=["table","diagram"])` 后用 `show_widget` 渲染如下 4
列表格（颜色用 IDE 当前主题色，背景跟随 light/dark），表头与单元格用
显式 `fill` 避免回退到黑：

```
| 模式      | 耗时      | 检测项                                  | 跑分 | 评分 | 联网 |
| --------- | --------- | --------------------------------------- | ---- | ---- | ---- |
| quick     | <30 秒    | 硬件 + OpenVINO + 设备                  | ✗   | ✗   | ✗   |
| standard  | 1~3 分钟  | + 冒烟测试 + 基础跑分 + 容量估算 + 推荐 | ✓   | ✓   | ✗   |
| full      | 5+ 分钟   | + 全设备横向跑分 + LLM 真实推理         | ✓✓  | ✓   | ✓(首次) |
```

> 视觉重点：耗时列用颜色编码（quick=绿、standard=蓝、full=橙），
> 跑分与评分列用 ✓/✗ 直观对比，联网列注明「仅首次下载」避免劝退。

#### 跳过提问的判定

以下情况**无需询问**、直接执行：
- 用户明确说了模式（"跑个 quick" / "full 模式测一下"）
- 用户需求本身就限定了模式（如"实际生成速度多快"→ full；
  "只看环境有没有问题"→ quick）
- 同一会话中用户已经选过模式且无新诉求（继续用上次的模式）

### 命令

```bash
# QUICK：硬件检测 + OpenVINO 检测 + 设备检查（< 30 秒，不输出评分）
python scripts/doctor.py --mode quick

# STANDARD：+ Smoke Test + 基础 Benchmark + 容量估算 + 部署建议（1~3 分钟）
python scripts/doctor.py --mode standard

# FULL：+ 全设备横向 Benchmark + GenAI/LLM Benchmark + 本地对话体验（含模型下载，几分钟）
python scripts/doctor.py --mode full
```

**full 模式新增「本地对话体验」**：GenAI Benchmark 通过后，脚本会自动在后台启动一个本地 HTTP 对话服务（`scripts/demo_chat/server.py` + `index.html`），加载刚测过的模型，让用户直接在浏览器里与模型对话（流式输出、多轮记忆）。服务信息写入报告的 `demo_chat` 字段，HTML/MD 报告中会显示访问链接。

可选参数：

- `--device CPU|GPU|NPU`：只测试指定设备（同时约束 GenAI Benchmark 的设备）
- `--model 路径`：GenAI Benchmark 使用指定的本地 OpenVINO IR 模型，覆盖默认模型
- `--output 目录`：指定报告输出目录（默认按模式分目录 `output/<mode>/`，
  避免不同模式的报告互相覆盖；同一模式重跑会覆盖该模式旧报告）

模型下载：full 模式默认从 ModelScope 下载 Qwen 0.5B INT4（约 370MB）到
`models/genai/`，已缓存则跳过；环境变量 `AIPC_DOCTOR_MODEL_SOURCE=huggingface`
可切换模型源。核心检测（quick/standard）不依赖网络。

### Python 依赖

与 `requirements.txt` 一致，缺什么装什么（装前需征得用户同意）：

- quick / standard 模式：`openvino`、`psutil`、`numpy`
- full 模式追加：`openvino-genai`（LLM 实测）、`modelscope`（模型下载，
  已有模型缓存或指定 `--model` 时不需要）

full 模式启动前会自动做依赖预检；缺失时 GenAI 环节记 SKIPPED 并在
`errors` 里给出安装指引，其余体检照常完成。

### 环境与缓存存放约定

- **Python 依赖 / 虚拟环境：不要装进本 Skill 目录**。依赖装到隔离的运行时
  venv（例如 `~/.workbuddy/binaries/python/envs/<skill名>/`），避免污染系统环境，
  也避免 venv（平台相关、体积大）混入 skill 目录。
- **模型缓存：默认放本 Skill 目录 `models/genai/`**（自包含、开箱即用），
  已缓存则跳过下载。如需改放别处，用 `--model 路径` 指定本地 OpenVINO IR 模型，
  或用环境变量 `AIPC_DOCTOR_MODEL_SOURCE=huggingface` 切换下载源。
- 分享/备份本 Skill 时，可排除 `models/` 与 `output/` 目录（体积大、可重建）。

## 如何解读结果

1. 运行脚本后读取输出目录下的 `report.json`（结构化数据），用户可读版本为 `report.md` 与 `AI_PC_Readiness_Report.html`。
2. 关键字段：`system` / `cpu` / `gpu` / `npu` / `memory` / `openvino` / `device_tests`（Smoke Test）/ `benchmarks` / `genai`（LLM 实测，full 模式）/ `demo_chat`（本地对话服务状态，full 模式）/ `capacity` / `model_recommendations` / `readiness_score` / `recommendations` / `errors`。
3. 用自然语言向用户解释结果。

## 必须遵守的规则

- **禁止猜测硬件**：CPU/GPU/NPU 型号、OpenVINO 版本、可用设备、性能数据一律以 `report.json` 为准；脚本未采集到的字段（unknown / null）就如实说未知，不得编造。
- **区分 ESTIMATED 与 BENCHMARKED**：`capacity` 是容量估算（ESTIMATED），`benchmarks` / `genai` 是本机实测（BENCHMARKED），`model_recommendations` 逐条标注；向用户表述时必须区分开。
- **理论支持 ≠ 实测支持**：NPU/GPU 状态 `detected` 只代表系统检测到硬件；能否推理以 `device_tests` 的 Smoke Test 实测结果为准。
- **Readiness Score 仅对目标平台输出**：macOS / 非 Intel 平台为降级模式，`readiness_score.score` 为 null 属正常，不要编造分数；quick 模式也不输出评分（未做实测），null 属正常；评分是工具内部综合评价，不代表 Intel 官方认证。
- **不自动安装软件**：OpenVINO 缺失时脚本会以非零码退出并输出引导步骤；安装决策必须由用户做出，征得同意后才可代为执行 `pip install`（可建议国内 PyPI 镜像）。依赖范围见上文「Python 依赖」。

## 参考文档

- `references/model_memory_reference.md`：模型内存估算规则
- `references/openvino_devices.md`：CPU/GPU/NPU 插件说明与常见故障
- `references/benchmark_metrics.md`：性能指标定义
