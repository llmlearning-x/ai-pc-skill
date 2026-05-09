# 🔒 Local Privacy Inspector Skill

> **让敏感文件不出电脑：基于 AI PC 的本地隐私数据检查 Skill**

一个运行在 AI PC 本地的隐私数据检查 Skill，帮助用户在文件外发、上传或共享前，检查指定文件中是否包含手机号、身份证号、API Key、Token、数据库连接串等敏感信息，并生成默认脱敏的风险报告。

## ✨ 核心特点

| 特点 | 说明 |
|------|------|
| 🔒 **纯本地运行** | 文件不上传云端，检查过程完全在本地完成 |
| 🎯 **单文件聚焦** | MVP 版本只检查用户指定的单个文件，范围可控 |
| 🛡️ **默认脱敏** | 所有检测结果默认脱敏展示，避免二次泄露 |
| 📊 **风险分级** | 高/中/低/提示 四级风险，快速定位问题 |
| 📄 **报告输出** | 支持 Markdown / JSON 格式报告 |
| 🤖 **Agent 驱动** | 支持自然语言交互，模型自动调用检测工具 |

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 无需额外依赖（纯标准库实现）

### 安装

```bash
git clone <repo-url>
cd local_privacy_inspector

# V0.2 新增办公文档支持，需要安装依赖
pip install python-docx pypdf openpyxl
```

### 使用方式一：命令行直接扫描

```bash
# 扫描单个文件
python scripts/skill.py <文件路径>

# 文本文件（V0.1）
python scripts/skill.py demo/.env
python scripts/skill.py demo/meeting_notes.md
python scripts/skill.py demo/customer_list.csv

# 办公文档（V0.2 新增）
python scripts/skill.py demo/demo_contract.docx
python scripts/skill.py demo/demo_resume.pdf
python scripts/skill.py demo/demo_budget.xlsx

# JSON 格式输出
python scripts/skill.py demo/config.yaml --format json
```

### 使用方式二：Agent 自然语言交互

在支持 Function Calling 的 Agent 工具中（如 Claude、ChatGPT、Cursor 等），配置 `scan_privacy_file` 工具后即可通过自然语言调用：

```
用户：帮我检查 demo/.env 有没有敏感信息
Agent：调用 scan_privacy_file(demo/.env) → 返回风险报告

用户：我想把 meeting_notes.md 发给客户，先帮我看看
Agent：调用 scan_privacy_file(demo/meeting_notes.md) → 给出外发建议
```

> 无需在 Skill 中配置 API Key，由用户的 Agent 客户端管理模型连接。

## 📁 项目结构（ModelScope Skill 规范）

```
local_privacy_inspector/
├── SKILL.md                          # ⭐ Skill 核心入口文件
├── README.md                         # 项目说明
├── scripts/                          # 可执行脚本
│   ├── skill.py                      # CLI 主入口
│   ├── models.py                     # 数据模型
│   ├── extractor.py                  # 文件文本提取
│   ├── detector.py                   # 敏感信息检测引擎
│   ├── masker.py                     # 脱敏处理器
│   ├── classifier.py                 # 风险分级
│   └── reporter.py                   # 报告生成
├── references/                       # 参考文档
│   ├── detection-rules.md            # 完整检测规则
│   └── usage-guide.md                # 使用指南
└── demo/                             # 示例文件 & 测试用例
    ├── .env
    ├── config.yaml
    ├── meeting_notes.md
    ├── customer_list.csv
    └── normal_note.txt
```

## 🔍 检测能力

### 支持的文件类型

| 版本 | 支持的格式 |
|------|-----------|
| V0.1 (MVP) | `.txt` `.md` `.env` `.json` `.yaml` `.yml` `.csv` |
| V0.2 | `.docx` `.pdf` `.xlsx` |

### 检测的敏感信息

| 类别 | 检测内容 | 风险等级 |
|------|---------|---------|
| **个人敏感信息** | 手机号、身份证号、银行卡号、邮箱、固定电话、护照号 | 高/中/低 |
| **企业敏感信息** | 统一社会信用代码、合同金额、项目编号 | 中 |
| **开发者密钥** | API Key、AccessKey、SecretKey、Token、Password、数据库连接串、JWT、SSH私钥、服务器 IP | **高**/中 |
| **文件风险特征** | `.env` 文件、`secrets.json`、密码相关配置 | **高** |

## 📊 风险分级

| 等级 | 判定条件 |
|------|---------|
| 🔴 **高风险** | API Key / SecretKey / AccessKey / Token / 数据库连接串 / SSH私钥 / JWT / 身份证号 / 银行卡号 |
| 🟡 **中风险** | 手机号 / 合同金额 / 客户名称 / 项目编号 / 服务器IP / 统一社会信用代码 |
| 🟢 **低风险** | 邮箱 / 姓名 / 固定电话 |
| 🔵 **提示信息** | 文件名风险特征 |

## 🛡️ 安全原则

- ✅ 只扫描用户指定的单个文件
- ✅ 不上传原始文件到任何服务器
- ✅ 不保存/输出完整敏感字段
- ✅ 检测结果默认脱敏
- ✅ 不自动修改或删除原始文件
- ❌ 不扫描整台电脑
- ❌ 不后台自动扫描
- ❌ 不读取系统隐私目录

## 📄 报告示例

扫描完成后会在当前目录生成报告文件：

```markdown
# 🔒 本地隐私数据检查报告

## 📋 扫描概览

| 项目 | 内容 |
|---|---|
| 扫描文件 | `.env` |
| 风险等级 | 🔴 高风险 |
| 发现敏感项 | 9 个 |

## 🔴 高风险 详情

### 1. API_Key
- **所在行**: 第 2 行
- **脱敏内容**: `sk-t****cdef`
- **建议**: API Key 属于高度敏感信息，请立即删除并使用环境变量

## 💡 处理建议
- ⚠️ 该文件包含高风险敏感信息，请优先处理
- 发现明文密钥，建议立即删除并轮换
```

## 🎯 适用场景

- 📄 **合同外发前检查** — 客户名称、手机号、合同金额
- 💻 **代码上传前检查** — API Key、.env、数据库连接串
- 📋 **简历投递前检查** — 身份证号、详细住址
- 📝 **会议纪要共享前检查** — 内部项目代号、预算金额

## 🏷️ 标签

`AIPC` `privacy` `security` `local-ai` `file-scan`

## 📜 License

Apache License 2.0
