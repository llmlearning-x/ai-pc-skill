# AI PC Skill Collection — Agent 开发指南

> 本文件为参与此项目的 AI Agent 提供开发上下文和规范指引。

## 项目背景

这是一个面向 **AI PC** 的 Agent Skill 集合项目。AI PC 的核心优势在于：

- **本地算力**：CPU + GPU + NPU 异构计算
- **隐私优先**：敏感数据不出设备
- **离线可用**：不依赖网络连接
- **低延迟**：本地毫秒级响应

## 开发原则

### 1. 本地化优先

- 所有 Skill 应尽可能在本地运行
- 不强制要求云端 API（可选增强）
- 敏感操作（如隐私检查）必须在本地完成

### 2. 轻量依赖

- 优先使用 Python 标准库
- 外部依赖应轻量且易于安装
- 提供明确的依赖安装命令

### 3. 安全边界

- 不扫描用户未授权的目录
- 不上传用户文件到云端
- 不自动修改或删除用户原始文件
- 检测结果默认脱敏

### 4. 渐进式功能

```
V0.1：核心规则 + 基础格式
V0.2：扩展格式 + 场景覆盖
V0.3：模型增强 + 性能优化
V1.0：Agent 完整版 + 自然语言交互
```

## Skill 目录规范

```
skills/<skill-name>/
├── SKILL.md              # ⭐ 核心入口（必需）
│   ├── YAML Frontmatter   # name, description, version, tags
│   └── Markdown 正文      # 触发条件、工作流程、示例
├── README.md             # 使用说明（必需）
├── scripts/              # 可执行脚本（必需）
│   └── *.py              # Python 脚本或其他可执行文件
├── references/           # 参考文档（建议）
│   └── *.md              # 规则说明、API 文档等
├── demo/                 # 示例文件（建议）
│   └── *.*               # 测试用例
└── .gitignore            # 忽略规则
```

### SKILL.md 标准

```yaml
---
name: skill-name                    # kebab-case，最多 64 字符
description: >                     # 最多 1024 字符
  1) 这个 Skill 做什么
  2) 什么时候应该使用它
  3) 核心价值是什么
version: 1.0.0
tags: [AIPC, tag1, tag2]           # 必须包含 AIPC
license: Apache-2.0
---

## 触发条件
- 当用户说...时触发

## 工作流程
1. 步骤一...
2. 步骤二...

## 示例
...
```

## 标签规范

| 标签 | 含义 | 是否必需 |
|------|------|---------|
| `AIPC` | AI PC 相关 Skill | ✅ 必须 |
| `privacy` | 隐私相关 | 可选 |
| `security` | 安全相关 | 可选 |
| `local-ai` | 本地 AI | 可选 |
| `openvino` | 使用 OpenVINO | 可选 |

## 测试要求

每个 Skill 提交前必须：

1. **本地测试通过**：所有 demo 文件扫描正常
2. **Agent 测试通过**：模型能正确调用 Skill 工具
3. **报告生成正常**：Markdown / JSON 格式正确
4. **安全边界满足**：不上传、不脱敏不展示、不自动修改

## 文件模板

### 新 Skill 创建检查清单

```markdown
- [ ] 目录名使用 kebab-case
- [ ] 包含 SKILL.md（YAML frontmatter 完整）
- [ ] 包含 README.md（使用说明）
- [ ] scripts/ 目录有可执行脚本
- [ ] demo/ 目录有测试用例
- [ ] 标签包含 AIPC
- [ ] 本地测试通过
- [ ] 不依赖未声明的外部服务
```

## 参考资料

- [ModelScope Skills 中心](https://modelscope.cn/skills)
- [SKILL.md 编写规范](https://www.knightli.com/2026/03/28/如何创建和使用-skills/)
- [OpenClaw Skill 系统](https://tenten.co/openclaw/zh-Hans/docs/masterclass/module-03-skills-system)
- [Intel AI PC 专区](https://modelscope.cn/brand/view/ai_pc)
