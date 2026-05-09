---
name: local-privacy-inspector
description: 
  本地隐私数据检查 Skill。帮助用户在文件外发、上传或共享前，
  检查指定文件中是否包含手机号、身份证号、API Key、Token、
  数据库连接串、合同金额、客户名称等敏感信息，并生成默认脱敏的风险报告。
  当用户提到"检查文件隐私"、"扫描敏感信息"、"外发前审查"、
  "代码上传前检查"、"简历隐私检查"时使用此 Skill。
  核心价值：原始文件不出电脑，检测范围由用户主动指定，结果默认脱敏。
version: 0.1.0
tags: [privacy, security, AIPC, local-ai, file-scan, sensitive-data]
license: Apache-2.0
author: AI PC Developer
agent_created: true
allowed-tools:
  - Bash(python:*)
  - Read
  - Write
---

# 🔒 Local Privacy Inspector Skill

> **让敏感文件不出电脑：基于 AI PC 的本地隐私数据检查 Skill**

## 触发条件

当用户表达以下意图时，触发此 Skill：

- "帮我检查这个文件有没有敏感信息"
- "这个文件能外发吗？"
- "扫描一下代码里的密钥"
- "简历里有没有隐私泄露风险"
- "会议纪要分享前检查一下"
- "检查 .env 文件是否安全"
- "文件发出去之前帮我审一遍"
- "隐私检查"
- "数据脱敏"
- "敏感数据扫描"
- "检查隐私泄露"
- "文件脱敏处理"
- "检查配置文件中的密码"
- "扫描文档中的个人信息"

## 核心能力

1. **单文件本地扫描** — 只扫描用户指定的单个文件，不上传云端
2. **敏感信息识别** — 覆盖个人/企业/开发者三大类 18+ 种敏感类型
3. **风险分级** — 高/中/低/提示 四级风险，快速定位问题
4. **默认脱敏** — 所有检测结果默认脱敏展示，避免二次泄露
5. **报告生成** — 输出 Markdown / JSON 格式本地报告

## 工作流程

```
用户指定文件路径
    ↓
解析文件内容（txt/md/env/json/yaml/csv）
    ↓
规则引擎检测敏感信息
    ↓
脱敏处理 + 风险分级
    ↓
生成本地隐私检查报告
    ↓
返回自然语言总结和处理建议
```

## 检测范围

### 个人敏感信息
- 手机号、身份证号、银行卡号
- 邮箱、固定电话、护照号

### 企业敏感信息
- 统一社会信用代码、合同金额
- 项目编号、客户名称

### 开发者密钥（高风险）
- API Key、AccessKey、SecretKey
- Token、Password、JWT、数据库连接串
- SSH 私钥、云厂商密钥、服务器 IP

### 文件风险特征
- `.env` 文件、`secrets.json`
- 包含 password/key/secret 的配置文件

## 执行步骤

### Step 1: 确认扫描目标

询问用户要检查的文件路径，确认文件存在且可访问。

支持的文件类型：
- `.txt` `.md` `.env` `.json` `.yaml` `.yml` `.csv` `.docx` `.pdf` `.xlsx`

### Step 2: 调用检测脚本

执行 `scripts/skill.py` 进行本地扫描。**必须使用绝对路径**调用脚本：

```bash
python /Users/fanghua/code/ai-pc-skill/local_privacy_inspector/scripts/skill.py <文件路径>
```

或指定 JSON 输出格式：

```bash
python /Users/fanghua/code/ai-pc-skill/local_privacy_inspector/scripts/skill.py <文件路径> --format json
```

**路径说明：**
- `<文件路径>` 可以是绝对路径或相对于当前工作目录的路径
- 脚本路径必须使用绝对路径：`/Users/fanghua/code/ai-pc-skill/local_privacy_inspector/scripts/skill.py`
- 或者使用相对于工作目录的路径：`scripts/skill.py`（仅在当前工作目录为技能根目录时有效）

### Step 3: 解析结果并生成建议

读取脚本输出的风险报告，用自然语言向用户解释：

1. **风险等级** — 文件整体是高/中/低风险
2. **发现项** — 具体发现了什么类型的敏感信息（已脱敏）
3. **处理建议** — 针对不同场景给出可操作的建议
4. **报告位置** — 告知用户本地报告文件路径

### Step 4: 场景化处理建议

根据用户的使用场景，给出针对性建议：

| 场景 | 建议重点 |
|------|---------|
| **外发/分享** | 哪些信息需要脱敏、删除或替换 |
| **代码上传** | 密钥是否已暴露、是否需要轮换、.gitignore 配置 |
| **简历投递** | 身份证号/住址是否应删除 |
| **归档整理** | 风险文件分类、加密建议 |

## 安全原则

- ✅ **只扫描用户指定的单个文件**，不主动扫描其他路径
- ✅ **不上传原始文件**，检测过程完全在本地完成
- ✅ **不保存完整敏感字段**，检测结果默认脱敏展示
- ✅ **不自动修改或删除原文件**
- ❌ 不扫描整台电脑
- ❌ 不后台自动扫描
- ❌ 不读取系统隐私目录
- ❌ 不上传报告到云端

## 参考文档

- `references/detection-rules.md` — 完整检测规则说明
- `references/usage-guide.md` — 使用指南和常见问题

## 示例

### 示例 1: 检查 .env 文件

**用户**: "帮我检查一下 demo/.env，看看有没有敏感信息"

**执行**:
```bash
python /Users/fanghua/code/ai-pc-skill/local_privacy_inspector/scripts/skill.py /Users/fanghua/code/ai-pc-skill/local_privacy_inspector/demo/.env
```

**输出**:
```
📁 扫描文件: .env
⚠️ 风险等级: 🔴 高风险
📊 发现敏感项: 9 个

🔴 高风险 (8 项):
  - API_Key sk-t****cdef
  - Password ****
  - 数据库连接串 mysql://admin:****@127.0.0.1:3306/demo
  - 风险文件名 .env

💡 处理建议:
  - 立即删除明文密钥，使用环境变量或密钥管理服务
  - 将 .env 加入 .gitignore
  - 如密钥已上传公开仓库，请立即轮换
```

### 示例 2: 会议纪要外发前检查

**用户**: "我想把 meeting_notes.md 发给客户，先帮我看看有没有不能外发的内容"

**执行**:
```bash
python /Users/fanghua/code/ai-pc-skill/local_privacy_inspector/scripts/skill.py /Users/fanghua/code/ai-pc-skill/local_privacy_inspector/demo/meeting_notes.md
```

**输出**:
```
📁 扫描文件: meeting_notes.md
⚠️ 风险等级: 🟡 中风险
📊 发现敏感项: 4 个

🟡 中风险 (3 项):
  - 手机号 138****5678
  - 合同金额 ****
  - 项目编号 Ed****ha

🟢 低风险 (1 项):
  - 邮箱 z****@xinghe-edu.com

💡 处理建议:
  - 脱敏手机号：将具体号码替换为"联系人A"
  - 模糊化金额：替换为"XX万元"或直接删除
  - 隐藏项目编号：替换为通用描述
```

## 故障排查

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| "不支持的文件类型" | 文件格式不在支持列表中 | 目前 MVP 只支持 txt/md/env/json/yaml/csv，请将内容复制到支持的格式中再检查 |
| "文件不存在" | 路径错误或文件被删除 | 确认文件路径正确，使用绝对路径或相对于 scripts/ 目录的相对路径 |
| "文件超过 10MB" | 文件太大 | MVP 限制单文件 10MB，可拆分文件或只检查关键部分 |
| 检测结果为空 | 文件确实不包含已知敏感信息 | 可手动检查是否包含业务特有的敏感字段 |

## 扩展说明

### 后续版本规划

- **V0.2**: 支持 docx/pdf/xlsx 解析
- **V0.3**: 支持图片 OCR（配合 OpenVINO 加速）
- **V1.0**: 接入本地模型（Qwen3.6-35B-A3B），支持自然语言任务输入和场景化建议

### 与 AI PC 的关系

此 Skill 专为 AI PC 场景设计：
- **本地运行** — 不需要网络连接，保护隐私
- **轻量化** — 纯 Python 标准库，零外部依赖
- **NPU/GPU 加速预留** — OCR 版本可接入 OpenVINO 利用异构算力
