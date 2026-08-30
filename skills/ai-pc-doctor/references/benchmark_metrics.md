# Benchmark 指标定义

## 基础推理 Benchmark（BENCHMARKED）

对 mnist-8 模型逐设备执行 warmup 3 次 + 计时 20 次：

| 指标 | 单位 | 含义 |
| --- | --- | --- |
| compile_time_ms | ms | 模型编译（compile_model）耗时 |
| min_latency_ms | ms | 单次推理最小延迟 |
| avg_latency_ms | ms | 单次推理平均延迟 |
| max_latency_ms | ms | 单次推理最大延迟 |
| throughput_infer_per_s | infer/s | 吞吐 = 1000 / 平均延迟 |
| peak_rss_delta_mb | MB | Benchmark 期间本进程 RSS 峰值增量 |
| avg_cpu_percent | % | Benchmark 期间本进程平均 CPU 占用（psutil 语义，多核可超 100%） |

## LLM / GenAI Benchmark 指标

默认模型：Qwen 0.5B INT4（OpenVINO 版，约 370MB，ModelScope 镜像源）。
固定 prompt + max_new_tokens=64，warmup 1 次后计时运行 1 次。

| 指标 | 单位 | 含义与测量方法 |
| --- | --- | --- |
| model_load_time_s | s | `LLMPipeline(model_dir, device)` 构造耗时（磁盘加载+编译） |
| TTFT | ms | Time To First Token。streamer 回调首次被调用的时刻 − generate 开始时刻 |
| TPOT | ms/token | Time Per Output Token。（最后一个 token 时刻 − 首 token 时刻）/（输出 token 数 − 1） |
| throughput_tokens_per_s | tokens/s | 输出 token 数 / 生成总耗时（generate 调用全程） |
| input_tokens | 个 | tokenizer.encode(prompt) 的 token 数 |
| output_tokens | 个 | 实际生成 token 数（优先取 perf_metrics，回退 streamer 计数） |
| peak_rss_delta_mb | MB | 生成期间本进程 RSS 峰值相对加载前的增量 |
| device | - | 运行设备（CPU / GPU / NPU） |

失败处理：下载失败或设备不支持记结构化错误（不崩溃）；NPU 上 LLM 不支持记 UNSUPPORTED。

## 暂不作为核心指标

精确功耗、每 Token 能耗、NPU 实时功耗、GPU Package Power —— 各平台读取方式不统一，无法横向比较，后续有可靠 API 后再加入。
