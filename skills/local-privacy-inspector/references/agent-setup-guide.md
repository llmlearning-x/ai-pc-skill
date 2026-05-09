# 本地 Agent 环境使用指南

> **赛事基准环境**：Ollama + Qwen3.6-35B-A3B + QwenPaw/Trae
>
> 本指南帮助你在本地 AI PC 上快速搭建 Agent 环境，让 Qwen3.6-35B-A3B 作为 Agent 大脑，驱动 local-privacy-inspector Skill 完成隐私检查任务。

---

## 一、环境准备

### 1.1 硬件要求

| 配置 | 最低要求 | 推荐配置 |
|------|---------|---------|
| CPU | Intel Core i5 / Apple M1 | Intel Core Ultra / Apple M3+ |
| 内存 | 16 GB | 32 GB+ |
| 存储 | 10 GB 可用空间 | SSD 50 GB+ |
| NPU/GPU | 可选（OpenVINO 加速用） | Intel Arc / NVIDIA RTX |

> Qwen3.6-35B-A3B 是 MoE 模型（35B 总参数 / 3B 激活），本地运行需要约 22GB 内存（Q4 量化）。

### 1.2 安装 Ollama

```bash
# macOS / Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows: 下载安装包 https://ollama.com/download/windows
```

验证安装：
```bash
ollama --version
```

### 1.3 拉取 Qwen3.6-35B-A3B 模型

```bash
# 拉取模型（首次下载约 20GB）
ollama pull qwen3.6-35b-a3b

# 验证模型可用
ollama list
```

启动模型服务：
```bash
ollama serve
# 服务默认运行在 http://localhost:11434
```

### 1.4 安装 Skill 依赖

```bash
cd skills/local-privacy-inspector

# 基础依赖
pip install python-docx pypdf openpyxl

# V0.3 图片 OCR
pip install rapidocr-onnxruntime

# 可选：AI PC OpenVINO 加速
pip install openvino
```

---

## 二、QwenPaw 中使用 Skill

### 2.1 安装 QwenPaw

```bash
# 安装 QwenPaw CLI
npm install -g @qwen-code/qwen-code@latest

# 启动 QwenPaw
qwen
```

### 2.2 配置本地模型

在 QwenPaw 中配置 Ollama 后端：

```bash
/auth
# 选择 "Ollama 本地模型"
# 填写 Model: qwen3.6-35b-a3b
# 填写 Server: http://localhost:11434/v1
```

### 2.3 安装 local-privacy-inspector Skill

**方式一：从 GitHub 直接安装**

```bash
# 在 QwenPaw 中执行
/skills install https://github.com/llmlearning-x/ai-pc-skill
```

**方式二：手动复制**

```bash
# 克隆仓库
git clone https://github.com/llmlearning-x/ai-pc-skill.git

# 复制 Skill 到 QwenPaw skills 目录
mkdir -p ~/.qwenpaw/skills
cp -r ai-pc-skill/skills/local-privacy-inspector ~/.qwenpaw/skills/

# 重启 QwenPaw 加载 Skill
```

### 2.4 使用场景示例

**场景 1：检查文件能否外发**

```
用户：我想把 meeting_notes.md 发给客户，帮我检查一下有没有敏感信息

Agent（Qwen3.6-35B-A3B）思考：
→ 用户要外发文件，涉及隐私检查
→ 触发 local-privacy-inspector Skill
→ 调用 scan_privacy_file(meeting_notes.md)

Agent 回复：
我检查了 meeting_notes.md，发现 4 处敏感信息：
- 手机号 138****5678（第 17 行）
- 合同金额 ¥****（第 12 行）
- 项目编号 Ed****ha（第 11 行）
- 邮箱 z****@xinghe-edu.com

⚠️ 风险等级：中风险。建议脱敏后再外发。
```

**场景 2：扫描图片中的身份证信息**

```
用户：这张员工登记表截图里有敏感信息吗？

Agent 思考：
→ 用户上传了图片，需要 OCR 提取文字后检测
→ 触发 local-privacy-inspector Skill（V0.3 图片 OCR）
→ 调用 scan_privacy_file(demo_id_card.png)

Agent 回复：
图片 OCR 识别完成，发现 11 项敏感信息：
🔴 高风险：身份证号、API Key、数据库连接串
🟡 中风险：手机号、合同金额、服务器 IP
🟢 低风险：邮箱

该图片包含高度敏感信息，不建议分享或存储在公共位置。
```

**场景 3：代码上传前检查**

```
用户：我要 push 这个代码仓库，帮我检查一下有没有泄露密钥

Agent 思考：
→ 用户要上传代码，需要检查密钥泄露
→ 触发 local-privacy-inspector Skill
→ 扫描 .env、config.yaml 等配置文件

Agent 回复：
扫描结果：
- .env：🔴 高风险，发现 API Key 和数据库密码
- config.yaml：🟢 低风险，无敏感信息

建议：
1. 将 .env 加入 .gitignore
2. 轮换已暴露的 API Key
3. 使用环境变量管理数据库密码
```

---

## 三、Trae 中使用 Skill

### 3.1 安装 Trae

下载 Trae IDE：https://www.trae.ai/

### 3.2 配置本地模型

1. 打开 Trae → 设置 → 模型
2. 选择 "添加本地模型"
3. 填写：
   - 模型名称：`qwen3.6-35b-a3b`
   - API 地址：`http://localhost:11434/v1`
   - API Key：`ollama`（或留空）

### 3.3 安装 local-privacy-inspector Skill

**方式一：通过 .agents/skills/ 目录**

```bash
# 在项目根目录创建 skills 目录
mkdir -p .agents/skills

# 克隆 Skill
git clone https://github.com/llmlearning-x/ai-pc-skill.git
cp -r ai-pc-skill/skills/local-privacy-inspector .agents/skills/

# 在 Trae 中启用 .agents 技能目录
# 设置 → 技能与命令 → 导入设置 → 启用 .agents 技能目录
```

**方式二：通过 .trae/skills/ 目录（项目级）**

```bash
mkdir -p .trae/skills
cp -r ai-pc-skill/skills/local-privacy-inspector .trae/skills/
```

**方式三：通过 find-skills 安装**

在 Trae 对话中输入：
```
使用 find-skills 搜索并安装 local-privacy-inspector
```

### 3.4 使用场景示例

在 Trae 的 Builder 模式下（推荐，支持工具调用）：

```
用户：@local-privacy-inspector 检查这个合同文件能不能发给客户

Agent 思考：
→ 用户要求检查合同文件
→ 加载 local-privacy-inspector Skill
→ 调用 scan_privacy_file(demo_contract.docx)
→ 解析 docx → 规则检测 → 生成报告

Agent 回复：
合同扫描结果：
- 客户名称：星河教育科技有限公司
- 合同金额：¥2,580,000
- 联系人手机号：138****5678

⚠️ 该文件包含商业敏感信息，建议：
1. 将客户名称替换为"客户A"
2. 金额替换为"XX万元"
3. 手机号替换为"联系人"
```

---

## 四、验证 Skill 是否被 Agent 正确调用

### 4.1 测试清单

| 测试项 | 输入 | 预期结果 |
|--------|------|---------|
| 触发词识别 | "检查敏感信息" | Agent 自动调用 Skill |
| 文本文件扫描 | "扫描 demo/.env" | 返回风险报告 |
| 办公文档扫描 | "检查 demo_contract.docx" | 返回风险报告 |
| 图片 OCR 扫描 | "检查 demo_id_card.png" | OCR 提取 → 返回风险报告 |
| 场景化建议 | "这个文件能发给客户吗？" | 返回脱敏建议 |
| 报告生成 | 任意扫描 | 生成 Markdown/JSON 报告 |

### 4.2 常见问题排查

**问题 1：Agent 没有调用 Skill**

- 检查 Skill 是否正确安装到 skills 目录
- 检查 SKILL.md 中的触发词是否包含你的输入
- 尝试显式调用：`使用 local-privacy-inspector 检查 xxx`

**问题 2：OCR 引擎不可用**

```bash
pip install rapidocr-onnxruntime
```

**问题 3：Office 文档解析失败**

```bash
pip install python-docx pypdf openpyxl
```

**问题 4：Ollama 模型加载失败**

- 检查内存是否足够（需要 22GB+）
- 尝试更小的量化版本：
  ```bash
  ollama pull qwen3.6-35b-a3b:q4_k_m
  ```

---

## 五、进阶：OpenVINO 加速（可选）

在 Intel AI PC 上，可以启用 OpenVINO 加速 OCR 推理：

```bash
# 安装 OpenVINO
pip install openvino

# 验证 OpenVINO 检测到 NPU/GPU
python -c "from ocr_engine import get_ocr_engine; print(get_ocr_engine().get_openvino_info())"
```

当 OCR 引擎检测到 OpenVINO 可用时，会显示：
```
⚡ OpenVINO: 已就绪 (版本 2024.x, 设备: CPU, GPU, NPU)
```

---

## 六、总结

| 步骤 | 操作 |
|------|------|
| 1 | 安装 Ollama 并拉取 Qwen3.6-35B-A3B |
| 2 | 安装 Skill 依赖（python-docx / pypdf / rapidocr-onnxruntime） |
| 3 | 在 QwenPaw 或 Trae 中安装 local-privacy-inspector Skill |
| 4 | 通过自然语言触发 Skill（"检查敏感信息" / "这个文件能外发吗"） |
| 5 | 查看 Agent 返回的脱敏报告和处理建议 |

**核心原则**：原始文件不出电脑，Agent 大脑理解意图，Skill 执行检测，结果默认脱敏。
