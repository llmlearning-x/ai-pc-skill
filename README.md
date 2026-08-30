<p align="center">
  <img src="https://raw.githubusercontent.com/llmlearning-x/ai-pc-skill/main/assets/AI-PC-Skill-Collection-Logo2.png" alt="AI PC Skill Collection" width="600">
</p>

<p align="center">
  <a href="https://github.com/llmlearning-x/ai-pc-skill">
    <img src="https://img.shields.io/badge/GitHub-仓库-181717?logo=github" alt="GitHub">
  </a>
  <a href="https://modelscope.cn/skills">
    <img src="https://img.shields.io/badge/ModelScope-Skills-624aff?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDJMNCA4djhsOCA2IDgtNnYtOHoiIGZpbGw9IiNmZmYiLz48L3N2Zz4=" alt="ModelScope">
  </a>
  <img src="https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/License-Apache%202.0-orange?logo=apache" alt="License">
  <img src="https://img.shields.io/badge/OpenVINO-推荐-0071C5?logo=intel" alt="OpenVINO">
  <a href="https://modelscope.cn/events/242">
    <img src="https://img.shields.io/badge/赛事-AI%20PC%20Agent%20Skills%20征文-e94560" alt="Competition">
  </a>
</p>

<p align="center"><b>让敏感任务留在本地</b></p>

<p align="center">
面向 AI PC 的 Agent Skill 集合。利用端侧算力（CPU + GPU + NPU），让文件不出电脑就能完成隐私检查、安全审查等敏感任务。
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/llmlearning-x/ai-pc-skill/main/assets/AI-PC-Skill-Collection-Poster.png" alt="AI PC Skill Collection Poster" width="800">
</p>

---

## ✨ 核心理念

```
让 AI 不止于云端
让隐私保护触手可及
让敏感任务留在本地
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- macOS / Linux / Windows

### 运行 Privacy Inspector Skill

```bash
# 克隆仓库
git clone https://github.com/llmlearning-x/ai-pc-skill.git
cd ai-pc-skill/skills/local-privacy-inspector

# 安装依赖
pip install python-docx pypdf openpyxl
pip install rapidocr-onnxruntime

# 扫描单个文件（文本/办公文档/图片）
python scripts/skill.py demo/.env
python scripts/skill.py demo/demo_contract.docx
python scripts/skill.py demo/demo_resume.pdf
python scripts/skill.py demo/demo_id_card.png     # V0.3 图片 OCR
```

### Agent 驱动模式（赛事基准环境）

赛事方统一使用 **Ollama + Qwen3.6-35B-A3B + QwenPaw/Trae** 作为 Skill 是否可以被 Agent 大脑调用的基准测试环境。

**快速开始：**
```bash
# 1. 安装 Ollama 并拉取模型
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3.6-35b-a3b
ollama serve

# 2. 在 QwenPaw 或 Trae 中安装 Skill
# 详见 references/agent-setup-guide.md
```

在支持 Function Calling 的 Agent 工具中（QwenPaw、Trae、Claude、Cursor 等），配置 `scan_privacy_file` 工具后即可通过自然语言调用：

```
用户：帮我检查 demo/.env 有没有敏感信息
Agent：调用 scan_privacy_file → 返回风险报告

用户：我想把 meeting_notes.md 发给客户，先帮我看看
Agent：调用 scan_privacy_file → 给出外发建议

用户：这张身份证照片里有敏感信息吗？
Agent：调用 scan_privacy_file → OCR 提取 → 检测 → 返回报告
```

> 无需在 Skill 中配置 API Key，由用户的 Agent 客户端管理模型连接。
>
> 详细配置指南见 [`references/agent-setup-guide.md`](./skills/local-privacy-inspector/references/agent-setup-guide.md)

## 📦 已收录 Skills

| Skill | 描述 | 版本 | 标签 |
|-------|------|------|------|
| [local-privacy-inspector](./skills/local-privacy-inspector/) | 本地隐私数据检查 Skill，在文件外发前检测敏感信息并生成脱敏报告 | V0.3 | `AIPC` `privacy` `security` `OCR` |
| [ai-pc-doctor](./skills/ai-pc-doctor/) | AI PC 本地部署体检与 OpenVINO 性能评测 Skill，回答"能不能跑、跑多大、跑哪个设备、跑多快" | V0.3 | `AIPC` `openvino` `benchmark` |

### local-privacy-inspector 能力

- **10+ 种文件格式**：txt / md / env / json / yaml / csv / docx / pdf / xlsx / png / jpg / jpeg ...
- **本地 OCR (V0.3)**：驱动 RapidOCR 提取图片中的身份证、银行卡、合同截图、截图密钥等敏感文字，OpenVINO 加速预留
- **18+ 敏感类型**：手机号 / 身份证号 / API Key / Token / 数据库连接串 / 合同金额 ...
- **四级风险分级**：🔴 高风险 / 🟡 中风险 / 🟢 低风险 / 🔵 提示
- **默认脱敏**：所有检测结果脱敏展示，避免二次泄露
- **本地运行**：文件不出电脑，零 API 成本，离线可用

## 🏗️ 项目结构

```
ai-pc-skill/
├── README.md                          # 项目总览
├── AGENTS.md                          # Agent 开发指南
├── 需求文档.md                         # 需求文档 & 设计参考
├── docs/
│   ├── article.md                     # 魔搭研习社技术文章
│   └── images/                        # 文章配图
│       ├── architecture.png
│       ├── workflow.png
│       └── risk-levels.png
├── assets/
│   └── xiaohongshu/                   # 小红书营销素材
├── skills/
│   └── local-privacy-inspector/       # 本地隐私检查 Skill
│       ├── SKILL.md                   # Skill 核心入口
│       ├── README.md                  # 使用说明
│       ├── scripts/                   # 可执行脚本
│       ├── references/                # 参考文档
│       └── demo/                      # 测试用例
└── .gitignore
```

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| **Agent 大脑** | 本地 LLM（Qwen2.5 / Qwen3 / Phi-4 等，OpenVINO™ / Ollama） |
| **推理框架** | OpenVINO™ — 本地 AI 推理加速（OCR 模型加速、意图识别、任务规划、报告总结） |
| **检测引擎** | 规则引擎 — 正则 + 关键词匹配（零模型开销） |
| **运行环境** | Python 3.8+，标准库 + 轻量依赖（docx/pdf/xlsx/ocr） |
| **Skill 标准** | ModelScope Skills / OpenClaw / MS-Agent 兼容 |

## 🏆 参赛信息

本项目为 **[ModelScope AI PC Agent Skills 征文活动](https://modelscope.cn/events/242)** 参赛作品。

- **活动主题**：用 35B 以下小模型作为 Agent 大脑，驱动本地 AI 工具调用
- **技术约束**：纯本地运行，推荐 OpenVINO™ 推理框架
- **Skill 标签**：`AIPC`
- **文章标签**：`Intel AI PC`

## 🤝 贡献指南

欢迎提交新的 AI PC Skill！每个 Skill 应遵循以下规范：

1. **目录命名**：`skills/<kebab-case-skill-name>/`
2. **核心文件**：必须包含 `SKILL.md`（YAML frontmatter + 执行指令）
3. **代码目录**：`scripts/` 存放可执行脚本
4. **文档目录**：`references/` 存放参考文档
5. **测试用例**：`demo/` 存放示例文件
6. **标签要求**：必须包含 `AIPC` 标签

详见 [AGENTS.md](./AGENTS.md)。

## 📜 License

[Apache License 2.0](LICENSE)
