# AI PC Skill Collection

> 面向 AI PC 的 Agent Skill 集合，聚焦"文件不出电脑"的本地化 AI 场景。

## 项目定位

这是一个**AI PC Agent Skill 集合项目**，旨在探索和利用 Intel 酷睿™ Ultra 处理器的本地算力（CPU + GPU + NPU），配合 OpenVINO™ 推理框架，构建能在端侧运行的实用 Agent Skills。

核心理念：

```
让 AI 不止于云端
让隐私保护触手可及
让敏感任务留在本地
```

## 已收录 Skills

| Skill | 描述 | 版本 | 标签 |
|-------|------|------|------|
| [local-privacy-inspector](./skills/local-privacy-inspector/) | 本地隐私数据检查 Skill，在文件外发前检测敏感信息并生成脱敏报告 | V0.2 | `AIPC` `privacy` `security` |

## 项目结构

```
ai-pc-skill/
├── README.md                          # 项目总览（本文档）
├── AGENTS.md                          # Agent 开发指南
├── 需求文档.md                         # 需求文档 & 设计参考
├── docs/                              # 技术文章 & 文档
│   └── article.md                     # 魔搭研习社技术文章
├── skills/                            # Skill 集合
│   └── local-privacy-inspector/       # 本地隐私检查 Skill
│       ├── SKILL.md                   # Skill 核心入口文件
│       ├── README.md                  # Skill 使用说明
│       ├── scripts/                   # 可执行脚本
│       ├── references/                # 参考文档
│       └── demo/                      # 示例文件 & 测试用例
└── .gitignore
```

## 快速开始

### 环境要求

- Python 3.8+
- macOS / Linux / Windows

### 运行 Privacy Inspector Skill

```bash
# 进入 Skill 目录
cd skills/local-privacy-inspector

# 安装 V0.2 办公文档依赖
pip install python-docx pypdf openpyxl

# 扫描单个文件
python scripts/skill.py demo/.env
python scripts/skill.py demo/demo_contract.docx
python scripts/skill.py demo/demo_resume.pdf

# Agent 驱动模式（在支持 Function Calling 的 Agent 工具中使用）
# "帮我检查 demo/.env 有没有敏感信息"
# "我想把 meeting_notes.md 发给客户，先帮我看看"
```

## 技术栈

| 层级 | 技术 |
|------|------|
| **Agent 大脑** | Qwen3.6-35B-A3B（本地 Ollama / 线上 API） |
| **推理框架** | OpenVINO™（V0.3 OCR 阶段接入） |
| **运行环境** | Python 3.8+，纯标准库 + 轻量依赖 |
| **Skill 标准** | ModelScope Skills / OpenClaw / MS-Agent 兼容 |

## 参赛信息

本项目为 **ModelScope AI PC Agent Skills 征文活动**参赛作品。

- **活动主题**：用 35B 以下小模型作为 Agent 大脑，驱动本地 AI 工具调用
- **技术约束**：纯本地运行，推荐 OpenVINO™ 推理框架
- **Skill 标签**：`AIPC`
- **文章标签**：`Intel AI PC`

## 贡献指南

欢迎提交新的 AI PC Skill！每个 Skill 应遵循以下规范：

1. **目录命名**：`skills/<kebab-case-skill-name>/`
2. **核心文件**：必须包含 `SKILL.md`（YAML frontmatter + 执行指令）
3. **代码目录**：`scripts/` 存放可执行脚本
4. **文档目录**：`references/` 存放参考文档
5. **测试用例**：`demo/` 存放示例文件
6. **标签要求**：必须包含 `AIPC` 标签

## License

Apache License 2.0
