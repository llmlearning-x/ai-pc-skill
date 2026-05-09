<p align="center">
  <img src="https://raw.githubusercontent.com/llmlearning-x/ai-pc-skill/main/assets/AI-PC-Skill-Collection-Logo2.png" alt="AI PC Skill Collection" width="500">
</p>

# 让敏感文件不出电脑：基于 AI PC 的本地隐私数据检查 Skill

> 本文介绍一个运行在 AI PC 本地的隐私数据检查 Skill，帮助用户在文件外发、上传或共享前，发现文件中的敏感信息并生成脱敏报告。核心原则是：**原始文件不上传，只扫用户指定路径，检测结果默认脱敏。**

---

## 一、背景：为什么隐私检查更适合本地 AI PC

在 AI 技术快速发展的今天，我们习惯把各种问题抛给云端大模型：写代码、改文章、做翻译、生成图片。但有一类任务，天生就不适合上传云端——**隐私数据检查**。

试想一下这些场景：

- 你准备把一份合同发给客户，但不确定里面是否包含对方的手机号、身份证号或合同金额
- 你准备把代码项目 push 到 GitHub，但担心 `.env` 文件里还有没清理的 API Key
- 你准备把简历上传到招聘平台，但不确定是否暴露了详细家庭住址
- 你准备把会议纪要转发给项目组外的人员，但不确定是否提到了内部项目代号或预算

**传统方案的困境：**

| 方案 | 问题 |
|------|------|
| 人工检查 | 效率低、容易遗漏、无法识别技术类敏感信息 |
| 云端工具检查 | 需要先上传文件，反而增加泄露风险 |
| 企业安全软件 | 权限重、配置复杂、不适合个人用户 |

这时，**AI PC 的本地化算力**就成为了一个完美的解决方案：

- **模型运行在本地** — 35B 以下小模型完全可以驱动一个隐私检查 Agent
- **文件不出电脑** — 原始数据永远不离开设备
- **NPU/GPU 加速** — OpenVINO 可以进一步加速文件解析和 OCR
- **用户完全可控** — 扫描范围、检测规则、报告输出都由用户决定

这正是我们设计 **Local Privacy Inspector Skill** 的出发点。

---

## 二、问题：文件外发中的敏感信息风险

在日常工作中，我们经常需要处理包含敏感信息的文件。这些文件在发送、上传、共享、归档之前，用户往往并不知道里面隐藏了什么。

### 典型风险场景

**场景 1：合同外发**

一份 `contract_sample.docx` 中可能包含：
```
甲方名称：南京某某科技有限公司
联系人：张三
手机号：13812345678
合同金额：280000 元
统一社会信用代码：91320100MA1XXXXXXX
```

如果直接转发给不需要这些信息的人，就造成了客户信息和商业信息的泄露。

**场景 2：代码上传**

开发者经常把项目上传到 GitHub。一个看似干净的代码仓库中，可能隐藏着：
```
# .env
API_KEY=sk-test-1234567890abcdef
DATABASE_URL=mysql://admin:password123@127.0.0.1:3306/demo
DB_PASSWORD=123456
```

这些密钥一旦暴露，攻击者可以直接访问数据库或云服务。

**场景 3：简历投递**

简历中适合保留手机号和邮箱，但不一定适合保留：
```
身份证号：32010619990101001X
详细住址：南京市建邺区某某路 88 号 1802 室
银行卡号：6222021234567890123
```

上传到公开平台后，这些信息可能被不法分子利用。

**核心痛点：** 用户不是故意泄露，而是**没有意识到文件中存在敏感字段**。

---

## 三、设计原则：只扫描用户指定的文件

基于上述问题，我们确定了五个核心设计原则：

```
原始文件不上传
只扫描用户指定文件
检测结果默认脱敏
不自动修改原文件
生成本地风险报告
```

### 产品边界：做什么 & 不做什么

**做：**
- 检查用户指定的单个文件
- 识别常见敏感信息（手机号、身份证号、API Key、合同金额等）
- 生成脱敏风险报告
- 给出处理建议

**不做（MVP 阶段）：**
- 不扫描整台电脑
- 不后台自动扫描
- 不实时监控文件变化
- 不自动删除或修改文件
- 不上传报告到云端

这个定位让我们聚焦于一个明确的问题：**在用户主动选择的文件上，完成一次快速、安全、可控的隐私检查。**

---

## 四、架构：Agent + 工具链

### 整体架构

![系统架构图](https://raw.githubusercontent.com/llmlearning-x/ai-pc-skill/main/docs/images/architecture.png)

架构流程：
```
用户自然语言请求
      ↓
Agent 大脑（Qwen3.6-35B-A3B）
      ↓
理解意图 → 确认文件路径 → 调用检测工具
      ↓
┌─────────────────────────────────────────────┐
│         Local Privacy Inspector Skill        │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐    │
│  │extractor│→ │detector │→ │classifier│    │
│  │文本提取  │  │规则检测  │  │风险分级   │    │
│  └─────────┘  └─────────┘  └──────────┘    │
│       ↓            ↓            ↓           │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐    │
│  │  masker │  │reporter │  │  建议生成  │    │
│  │脱敏处理  │  │报告输出  │  │         │    │
│  └─────────┘  └─────────┘  └──────────┘    │
└─────────────────────────────────────────────┘
      ↓
Agent 生成自然语言总结
      ↓
用户获得：风险评级 + 处理建议 + 本地报告
```

### 工具拆分

Skill 内部拆分为 6 个独立的工具函数，每个职责单一：

| 工具 | 职责 | 函数签名 |
|------|------|---------|
| `extract_text` | 根据文件类型提取纯文本 | `extract_text(file_path) → (text, error)` |
| `detect_sensitive_info` | 正则规则引擎检测敏感信息 | `detect(text, file_path, file_name) → List[Finding]` |
| `mask_sensitive_value` | 对检测结果脱敏 | `mask_value(value, type) → masked_value` |
| `classify_risk` | 根据发现项计算风险等级 | `classify_risk(findings) → FileScanResult` |
| `generate_report` | 生成 Markdown / JSON 报告 | `generate_report(result) → report_path` |
| `scan_privacy_file` | 端到端封装，供 Agent 调用 | `scan_privacy_file(file_path) → summary` |

### 数据模型

```python
@dataclass
class Finding:
    file_path: str
    type: str              # "API_Key", "手机号", "合同金额"...
    category: str          # "personal" / "enterprise" / "developer_secret"
    risk_level: str        # "high" / "medium" / "low"
    raw_value: str         # 原始值（仅内存使用，不输出）
    masked_value: str      # 脱敏后的值（对外展示）
    line_number: int
    suggestion: str
```

---

## 五、实现：规则引擎 + 脱敏策略

![工作流程图](https://raw.githubusercontent.com/llmlearning-x/ai-pc-skill/main/docs/images/workflow.png)

### 5.1 检测规则设计

MVP 阶段采用**规则引擎**而非大模型推理，原因是：

1. **确定性** — 相同输入始终产生相同输出
2. **高性能** — 100 个文本文件 30 秒内完成
3. **零依赖** — 纯 Python 标准库，无需安装额外包
4. **零成本** — 不调用云端 API，完全离线运行

规则分为四大类，覆盖 18+ 种敏感类型：

**个人敏感信息：**
```python
DetectionRule(
    name="手机号",
    category=SensitiveCategory.PERSONAL,
    risk_level=RiskLevel.MEDIUM,
    patterns=[(r'(?:^|[^0-9])(1[3-9]\d{9})(?:$|[^0-9])', 1)],
    keywords=["手机", "电话", "联系方式"],
    suggestion="手机号建议脱敏处理，如 138****1234"
)

DetectionRule(
    name="身份证号",
    category=SensitiveCategory.PERSONAL,
    risk_level=RiskLevel.HIGH,
    patterns=[(r'(?:^|[^0-9A-Za-z])(\d{6}(?:19|20)\d{2}...)[\dXx](?:$|[^0-9A-Za-z])', 1)],
    keywords=["身份证", "身份证号"],
    suggestion="身份证号属于高度敏感信息，建议删除或替换"
)
```

**开发者密钥（高风险）：**
```python
DetectionRule(
    name="API_Key",
    category=SensitiveCategory.DEVELOPER,
    risk_level=RiskLevel.HIGH,
    patterns=[
        (r'(?:api[_\-]?key|apikey)[\s=:]*["\']?([a-zA-Z0-9_\-]{16,64})["\']?', 1),
        (r'(?:sk-)[a-zA-Z0-9]{20,64}', 0),
    ],
    keywords=["API_KEY", "sk-", "apikey"],
    suggestion="API Key 属于高度敏感信息，请立即删除并使用环境变量"
)

DetectionRule(
    name="数据库连接串",
    category=SensitiveCategory.DEVELOPER,
    risk_level=RiskLevel.HIGH,
    patterns=[
        (r'((?:mysql|postgresql|redis)://[^:]+:[^@]+@[^/\s]+)', 1),
    ],
    keywords=["DATABASE_URL", "mysql://"],
    suggestion="数据库连接串包含密码，请使用环境变量管理"
)
```

**文件风险特征：**
```python
# 检测 .env 文件、secrets.json 等高风险文件名
# 检测包含 password/key/secret/token 的配置行
```

### 5.2 脱敏策略

所有检测结果**默认脱敏**，避免在报告中二次泄露：

| 类型 | 原始值 | 脱敏值 |
|------|--------|--------|
| 手机号 | `13812345678` | `138****5678` |
| 身份证号 | `32010619990101001X` | `320***********001X` |
| 邮箱 | `hello@example.com` | `h****@example.com` |
| API Key | `sk-abc123456789` | `sk-********6789` |
| 数据库连接串 | `mysql://user:pass@host/db` | `mysql://user:****@host/db` |
| 合同金额 | `280000 元` | `¥**** 元` |
| IP 地址 | `192.168.1.100` | `192.168.*.*` |

### 5.3 风险分级逻辑

![风险分级规则](https://raw.githubusercontent.com/llmlearning-x/ai-pc-skill/main/docs/images/risk-levels.png)

```python
if 发现 API_Key / SecretKey / AccessKey / Token / 数据库连接串 / SSH私钥 / 身份证号 / 银行卡号:
    risk_level = "高风险"
elif 发现 手机号 / 合同金额 / 客户名称 / 项目编号 / 服务器IP:
    risk_level = "中风险"
elif 发现 邮箱 / 姓名 / 固定电话:
    risk_level = "低风险"
```

分级后自动生成处理建议，例如：
- 发现 `.env` 文件 → 建议加入 `.gitignore`
- 发现 API Key → 建议立即轮换密钥
- 发现合同金额 → 建议替换为区间或删除

---

## 六、Demo：扫描模拟项目资料

我们准备了 5 个测试文件，覆盖不同场景：

```
demo/
├── .env                      # 开发者密钥场景
├── config.yaml               # 生产配置场景
├── meeting_notes.md          # 会议纪要场景
├── customer_list.csv         # 客户清单场景
├── normal_note.txt           # 安全文件对照
├── demo_contract.docx        # 合同外发场景 (V0.2)
├── demo_resume.pdf           # 简历投递场景 (V0.2)
└── demo_budget.xlsx          # 预算表格场景 (V0.2)
```

### 测试 1：.env 文件（高风险）

![扫描结果示例](https://raw.githubusercontent.com/llmlearning-x/ai-pc-skill/main/assets/xiaohongshu/demo_result.png)

```bash
$ python scripts/skill.py demo/.env

🔒 本地隐私数据检查 Skill
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 扫描文件: .env
📂 文件路径: demo/.env
📏 文件大小: 167 字节

📝 正在提取文件内容...
   ✓ 成功提取 155 字符

🔍 正在检测敏感信息...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 扫描结果
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

风险等级: 🔴 高风险
发现敏感项: 9 个

  🔴 高风险: 8
  🟡 中风险: 1
  🟢 低风险: 0

发现的敏感信息:
  1. 🔴 [API_Key] sk-t****cdef
  2. 🔴 [Password] ****
  3. 🔴 [Password] ****
  4. 🔴 [数据库连接串] mysql://admin:****@127.0.0.1:3306/demo
  5. 🟡 [服务器IP] 127.0.*.*
  6. 🔴 [风险文件名] .env
  7. 🔴 [密码相关配置] API_KEY=sk-test-1234567890abcdef
  8. 🔴 [密码相关配置] DATABASE_URL=mysql://admin:password123@127.0.0.1:3306/demo
  9. 🔴 [密码相关配置] DB_PASSWORD=123456

📄 正在生成报告...
   ✓ 报告已生成: privacy_report_.env_20260509_xxxxxx.md
```

### 测试 2：会议纪要（中风险）

```bash
$ python scripts/skill.py demo/meeting_notes.md

风险等级: 🟡 中风险
发现敏感项: 4 个

  🔴 高风险: 0
  🟡 中风险: 3
  🟢 低风险: 1

发现的敏感信息:
  1. 🟡 [手机号] 138****5678
  2. 🟢 [邮箱] z****@xinghe-edu.com
  3. 🟡 [合同金额] ****
  4. 🟡 [项目编号] Ed****ha

💡 处理建议:
  - 外发前确认客户名称是否需要保留
  - 联系人手机号建议脱敏
  - 合同金额如用于公开材料，建议替换为区间或删除
```

### 测试 3：config.yaml（高风险）

```bash
$ python scripts/skill.py demo/config.yaml

风险等级: 🔴 高风险
发现敏感项: 9 个

  🔴 高风险: 7
  🟡 中风险: 2

发现的敏感信息:
  1. 🔴 [AccessKey] AKIA****MPLE
  2. 🔴 [SecretKey] wJal****EKEY
  3. 🔴 [Token] eyJh****wIn0
  4. 🔴 [数据库连接串] mysql://root:****@192.168.1.100:3306/production
  ...

💡 处理建议:
  - 立即删除代码中的明文密钥
  - 使用环境变量或密钥管理服务
  - 如密钥已上传公开仓库，请立即轮换
```

### 测试 4：简历 PDF（高风险）

```bash
$ python scripts/skill.py demo/demo_resume.pdf

风险等级: 🔴 高风险
发现敏感项: 4 个

  🔴 高风险: 1
  🟡 中风险: 2
  🟢 低风险: 1

发现的敏感信息:
  1. 🔴 [身份证号] 320***********001X
  2. 🟡 [手机号] 138****0000
  3. 🟢 [邮箱] z****@test.cn
  4. 🟡 [项目编号] PR****01
```

### 测试 5：合同 Word（中风险）

```bash
$ python scripts/skill.py demo/demo_contract.docx

风险等级: 🟡 中风险
发现敏感项: 6 个

  🔴 高风险: 0
  🟡 中风险: 6

发现的敏感信息:
  1. 🟡 [手机号] 138****5678
  2. 🟡 [手机号] 139****9999
  3. 🟡 [统一社会信用代码] 913201************
  4. 🟡 [合同金额] **** 万元
  5. 🟡 [项目编号] ED****01
  6. 🟡 [项目编号] Ed****ha
```

### 测试 6：安全文件（低风险）

```bash
$ python scripts/skill.py demo/normal_note.txt

风险等级: 🟢 低风险
发现敏感项: 0 个

✅ 未检测到敏感信息
```

---

## 七、Agent 驱动：让模型理解隐私检查

除了命令行直接扫描，我们还测试了 **Agent 驱动模式**：用 Qwen3.6-35B-A3B 作为 Agent 大脑，通过 Function Calling 调用检测工具。

### 交互示例

**用户：** "我想把 meeting_notes.md 发给客户，你先帮我看看里面有没有不能外发的内容"

**Agent 思考：** 用户要外发文件，需要检查敏感信息 → 调用 `scan_privacy_file`

**Agent 回复：**

> 我检查了 `demo/meeting_notes.md`，发现其中包含 **4 处敏感信息**，风险等级为 **中风险**。
>
> ⚠️ **不建议直接外发当前版本的文件！**
>
> **🟡 中风险 (3 项):**
> - 手机号 `138****5678` (第 17 行)
> - 合同金额 `****` (第 12 行)
> - 项目编号 `Ed****ha` (第 11 行)
>
> **🟢 低风险 (1 项):**
> - 邮箱 `z****@xinghe-edu.com`
>
> **💡 处理建议：**
> - 脱敏手机号：替换为"联系人A"
> - 模糊化金额：替换为"XX万元"
> - 隐藏项目编号：替换为通用描述

Agent 不仅返回了检测结果，还针对**"外发"这个具体场景**给出了可操作的建议。这体现了 **Agent + Skill** 组合的价值：模型负责理解场景和生成建议，Skill 负责精确执行检测任务。

---

## 八、本地价值：原始文件不出电脑

这个 Skill 的核心价值，可以用一句话概括：

> **让"不适合上传云端"的任务，在本地 AI PC 上安全完成。**

### 为什么是 AI PC？

| 维度 | 云端方案 | 本地 AI PC 方案 |
|------|---------|----------------|
| 隐私性 | 需要上传文件 | ❌ 文件不出电脑 |
| 可控性 | 扫描范围由服务商决定 | ✅ 只扫用户指定文件 |
| 成本 | 按次或按量计费 | ✅ 零 API 成本 |
| 速度 | 网络延迟 | ✅ 本地毫秒级响应 |
| 可用性 | 依赖网络 | ✅ 离线可用 |

### 与 OpenVINO 的结合点

本项目基于 **OpenVINO™** 推理框架设计，充分利用 Intel 酷睿™ Ultra 处理器的异构算力（CPU + GPU + NPU），实现端侧高效推理。

**当前版本的 OpenVINO 应用：**

- **规则引擎本地运行** — 纯 Python 实现，零外部依赖，已在本地完成验证。核心检测逻辑可直接通过 OpenVINO 的 Python API 接入，为后续异构加速预留接口。
- **文本解析性能优化** — 大文件（>1MB）的文本提取和预处理可通过 OpenVINO 工具链进行性能分析，识别 CPU/GPU/NPU 的最佳负载分配策略。

**V0.3 的 OpenVINO 增强计划：**

- **OpenVINO OCR 加速** — 接入 OpenVINO™ 优化后的 OCR 模型（如 PaddleOCR-OpenVINO），利用 NPU 实现图片、截图、扫描版 PDF 的本地文字识别，敏感信息检测从纯文本扩展到视觉内容。
- **Optimum-Intel 模型量化** — 通过 Optimum-Intel 将 Qwen3.6-35B-A3B 等 ≤35B 模型转换为 INT8 格式，在 NPU 上运行 Agent 推理，降低延迟和内存占用。
- **异构执行调度** — 使用 OpenVINO 的 `AUTO` 设备插件，自动在 CPU/GPU/NPU 之间分配任务：规则匹配用 CPU、OCR 推理用 NPU、模型推理用 GPU，最大化端侧算力利用率。

这是 AI PC 从"硬件概念"走向"生产力工具"的核心跨越：**OpenVINO 让 35B 小模型在本地跑起来，让隐私检查从规则匹配升级为"模型+规则"的混合智能。**

---

<p align="center">
  <img src="https://raw.githubusercontent.com/llmlearning-x/ai-pc-skill/main/assets/AI-PC-Skill-Collection-Poster.png" alt="AI PC Skill Collection 项目海报" width="800">
</p>

## 九、总结与展望

### 核心成果

我们构建了一个**轻量级、本地化、可复用**的隐私检查 Skill：

- ✅ **18+ 种敏感类型**检测规则（个人/企业/开发者/文件特征）
- ✅ **四级风险分级** + 自动脱敏 + 场景化建议
- ✅ **纯本地运行**，零外部依赖，零 API 成本
- ✅ **Agent 可调用**，支持自然语言交互
- ✅ 符合 **ModelScope Skills** 开放标准

### 参赛标签

- **Skill 标签**: `AIPC` `privacy` `security` `local-ai`
- **文章标签**: `Intel AI PC`

### 后续规划

| 版本 | 目标 | OpenVINO 作用 |
|------|------|---------------|
| **V0.1** | ✅ 规则引擎 + 文本文件检测 | 本地运行验证，预留加速接口 |
| **V0.2** | ✅ docx/pdf/xlsx 解析，覆盖办公场景 | 文本提取性能分析与优化 |
| **V0.3** | OpenVINO OCR + 图片/扫描版 PDF 敏感信息识别 | **NPU 加速 OCR 推理**，视觉内容检测 |
| **V1.0** | Optimum-Intel 量化 Qwen3.6-35B，Agent 完整版 | **NPU 运行 35B 模型**，异构调度（CPU/GPU/NPU） |

## 附录：项目信息

- **项目名称**: Local Privacy Inspector Skill
- **项目类型**: AI PC Agent Skill
- **代码仓库**: [github.com/llmlearning-x/ai-pc-skill](https://github.com/llmlearning-x/ai-pc-skill)
- **适用场景**: 文件外发前检查、代码上传前检查、合同共享前检查、简历投递前检查
- **技术栈**: Python 3.8+（纯标准库）
- **License**: Apache-2.0

---

> **让 AI 不止于云端，让隐私保护触手可及。**
>
> 如果你也认同"本地 AI 适合处理不适合上传云端的任务"这个理念，欢迎在评论区交流你的想法，或者去 GitHub 给这个项目一颗 ⭐。
