# 使用指南

## 环境要求

- **操作系统**: macOS / Linux / Windows
- **Python 版本**: 3.8+
- **依赖**: 无（纯标准库实现）

## 安装

```bash
git clone <your-repo-url>
cd local_privacy_inspector
```

无需安装额外依赖，直接可用。

## 基本用法

### 命令行直接扫描

```bash
cd scripts

# 扫描单个文件
python skill.py /path/to/your/file.txt

# 扫描示例文件
python skill.py ../demo/.env
python skill.py ../demo/meeting_notes.md
python skill.py ../demo/customer_list.csv

# JSON 格式输出
python skill.py ../demo/config.yaml --format json
```

### Agent 驱动模式

在支持 Function Calling 的 Agent 客户端（如 Claude、ChatGPT、Cursor）中，配置 `scan_privacy_file` 工具后，通过自然语言调用即可。

无需在 Skill 中配置 API Key，由用户的 Agent 客户端管理模型连接。

## 支持的文件类型

| 格式 | 扩展名 | 说明 | 版本 |
|------|--------|------|------|
| 纯文本 | `.txt` | 直接读取 | V0.1 |
| Markdown | `.md` | 直接读取 | V0.1 |
| 环境变量 | `.env` | 直接读取 | V0.1 |
| JSON | `.json` | 读取并扁平化 | V0.1 |
| YAML | `.yaml` `.yml` | 直接读取 | V0.1 |
| CSV | `.csv` | 读取表格文本 | V0.1 |
| Word | `.docx` | 提取段落文本 | V0.2 |
| PDF | `.pdf` | 提取页面文本 | V0.2 |
| Excel | `.xlsx` | 读取单元格文本 | V0.2 |

V0.2 新增办公文档支持，需要安装依赖：

```bash
pip install python-docx pypdf openpyxl
```

## 输出说明

### 控制台输出

扫描完成后，控制台会显示：
- 文件基本信息
- 风险等级（🔴 高风险 / 🟡 中风险 / 🟢 低风险）
- 敏感信息列表（已脱敏）
- 处理建议

### 报告文件

同时会在当前目录生成报告文件：

```
privacy_report_<文件名>_<时间戳>.md     # Markdown 格式
privacy_report_<文件名>_<时间戳>.json    # JSON 格式（指定 --format json 时）
```

## 常见问题

### Q: 可以扫描整个文件夹吗？

A: MVP 版本只支持单文件扫描。如需批量扫描，可以写一个简单的 shell 脚本循环调用：

```bash
for file in folder/*.{txt,md,env,json,yaml,yml,csv}; do
    python skill.py "$file" 2>/dev/null
done
```

### Q: 检测结果准确吗？

A: 规则引擎基于正则表达式和关键词匹配，对标准格式的敏感信息（如手机号、身份证号、API Key 等）识别率较高。但对于非标准格式或上下文依赖的敏感信息，可能存在漏检或误报。建议将检测结果作为参考，关键文件仍需人工复核。

### Q: 会修改我的文件吗？

A: **绝对不会**。本 Skill 只做只读扫描，不修改、不删除、不上传任何文件。

### Q: 报告会泄露我的敏感信息吗？

A: 不会。所有检测结果在报告中都是**脱敏展示**的，例如手机号显示为 `138****5678`。

### Q: 如何增加自定义检测规则？

A: 编辑 `scripts/detector.py` 中的 `RULES` 列表，添加新的 `DetectionRule` 即可。每个规则包含：
- `name`: 规则名称
- `category`: 所属类别
- `risk_level`: 风险等级
- `patterns`: 正则表达式列表
- `keywords`: 关键词列表
- `suggestion`: 处理建议

## 安全声明

- 本 Skill **只扫描用户明确指定的文件**
- 所有检测在**本地完成**，不上传任何数据
- 结果**默认脱敏**，不输出完整敏感字段
- **不自动修改或删除**原始文件
