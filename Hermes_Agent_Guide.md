# Hermes Agent 深度使用指南 (2026最新版)

## 背景信息
- **撰写日期**: 2026-05-18
- **适用环境**: macOS 15.6.1 (Apple Silicon, 32GB 内存)
- **本地推理后端**: `omlx` (提供 OpenAI/Anthropic 兼容接口)

---

## 1. 快速安装脚本

由于当前环境为 macOS，且你倾向于使用 `uv` 进行现代化、极速的 Python 包与环境管理，以下是最推荐的纯净安装流程：

```bash
# 1. 安装 uv (如果尚未安装)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 为 Hermes 创建并激活专属的虚拟环境
uv venv hermes-env
source hermes-env/bin/activate

# 3. 极速安装 Hermes Agent 核心
uv pip install hermes-agent

# 4. 安装目前最好用的 Web 管理面板 (Hermes Web UI)
# 需要依赖 Node.js 环境
npm install -g hermes-web-ui

# 5. 启动 Web UI
hermes-web-ui start
```
启动后即可在浏览器打开 `http://localhost:8648`。

---

## 2. 学习手册 (Hermes 核心机制)

Hermes Agent (自 v0.12.0+ 起) 是由 Nous Research 打造的开源自主智能体框架。与早期的“小龙虾”等模型相比，它的核心差异在于**闭环的自我学习与持久化记忆**，它不仅能干活，还能“越用越聪明”。

### 核心概念
- **技能 (Skills) 与策展人 (Curator)**:
  Hermes 会在执行任务的过程中自主创建技能。v0.12 版本引入了强大的自动“策展人”机制，它会以 7 天为周期，在后台自动给技能打分、整合冗余技能并剔除无效技能。
- **持久化记忆 (Memory)**:
  支持跨会话召回。它会不断分析你们的对话，深化对你的了解，并将这些信息固化在 `MEMORY.md` 和 `USER.md` 等内部记忆结构中。
- **自我进化 (Self-Evolution)**:
  基于 DSPy 和 GEPA（提示词架构遗传进化）技术，Hermes 能够回顾它过去失败的执行轨迹，自己找出失败原因，并生成经过优化的新版本技能和提示词。

### 针对 32G Mac 的生存策略
在 32G 内存的 Mac 上勉强运行 qwen3.6-35B 或 Gemma4-26B 这样的大模型，输出速度注定较慢。建议：
1. **拥抱异步与定时任务**：不要盯着终端等它输出。使用 Web UI 的 **Cron 定时任务**，或者通过 Telegram/微信 绑定 Hermes，在睡前给它派发大型任务，醒来收割成果。
2. **控制 Token 消耗**：这是防止它在长任务中“死机”的关键。

---

## 3. 收集网上好用的使用案例

根据 2026 年 5 月最新的 `awesome-hermes-agent` 生态汇总，以下是几个极具价值的使用案例（非常适合挂机执行）：

1. **自主小说与长文创作 (autonovel)**
   - **简介**: 基于 Hermes 构建的自主小说创作管道。设定好大纲后，它能利用智能体循环端到端生成超过 10 万字的长篇内容，极度适合睡前扔给它在后台慢慢跑。
2. **自动化 SRE 运维 (hermes-incident-commander)**
   - **简介**: 运维自愈智能体。通过 Hermes 的 Cron 调度定期检查服务器或服务状态，一旦发现异常会自动诊断并尝试执行修复脚本。
3. **多模态图表生成 (drawio-skill)**
   - **简介**: 从自然语言生成 draw.io 架构图并导出为 PNG/SVG。它让 Hermes 在解释复杂系统时，能直接吐出一张结构清晰的图表。
4. **自我提升道场 (hermes-dojo)**
   - **简介**: 一个自动化的自我改进闭环，专门监控 Hermes 的表现，挑出执行效率低下的任务让其自我复盘并优化。

---

## 4. 收集好用的插件/技能及如何使用

这里精选了近期爆火、对体验提升巨大的生态插件：

### 1. 自我进化引擎 (hermes-agent-self-evolution)
- **作用**: 让 Hermes 自己修改自己的代码、技能和系统提示词。不需要 GPU 训练，完全通过 API 调用闭环完成。它能让你的 Hermes 针对你个人的任务越做越顺手。
- **如何使用**:
  ```bash
  # 在你的工作区克隆进化引擎
  git clone https://github.com/NousResearch/hermes-agent-self-evolution.git
  cd hermes-agent-self-evolution
  uv pip install -e ".[dev]"

  # 指定你本地的 hermes 配置目录
  export HERMES_AGENT_REPO=~/.hermes/hermes-agent

  # 针对某个不顺手的技能（例如代码审查）启动 10 轮进化迭代
  python -m evolution.skills.evolve_skill --skill github-code-review --iterations 10
  ```

### 2. 终端输出压缩器 (rtk-hermes)
- **作用**: **(强烈推荐 32G Mac 用户安装！)** 这是一个原生插件。它能拦截 Shell 命令的输出，并压缩 60%-90% 的终端冗余信息，然后再喂给大模型。这不仅省 Context Window，还能大幅减轻本地 35B 模型的阅读负担，间接提升响应速度。
- **如何使用**: 直接作为 Hermes 插件加载，随网关启动自动生效，零配置。

### 3. YouTube 视频转录技能 (youtube-skills)
- **作用**: 让 Hermes 能够稳定提取 YouTube 视频内容和字幕。你可以在微信里发个 YouTube 链接给它，让它慢慢看完并总结。
- **如何使用**: 通过 `hermeshub` 或将技能文件夹拷贝到 `~/.hermes/skills/` 即可。

### 4. 微信/Telegram 桥接模块 (内置于 Web UI)
- **作用**: 摆脱死板的终端交互，让你随时随地通过手机指使 Hermes。
- **如何使用**: 在 `hermes-web-ui` 的控制面板中，找到“平台渠道 (Platform Channels)”，直接浏览器扫码绑定微信，或填入 Telegram Bot Token。

---

## 5. 配置手册 (深度适配 omlx)

既然你主要依靠 `omlx` 在本地跑 qwen3.6-35B 等模型，并且它提供了兼容 OpenAI 的接口，你需要将 Hermes 所有的推理请求全部接管到本地：

### 第一步：配置 omlx 接口
假设你的 `omlx` 服务运行在本地，并暴露了如下端点：
`http://127.0.0.1:8080/v1`

### 第二步：修改 Hermes 配置文件
打开或创建 `~/.hermes/config.yaml`，填入以下配置：

```yaml
# ~/.hermes/config.yaml
providers:
  - name: "omlx-local"
    base_url: "http://127.0.0.1:8080/v1"
    # omlx 本地通常不需要真实 API Key，但由于格式要求，随便填一个即可
    api_key: "sk-omlx-local-key"
    type: "openai"

# 替换为你实际在 omlx 中加载的模型标识符
default_model: "qwen3.6-35b-4bit"
default_provider: "omlx-local"

agent:
  # 针对 Mac 本地慢速输出的优化参数
  max_turns: 15       # 适当限制最大循环轮次，防止无限死循环耗时
  timeout: 600        # 大幅提高超时阈值（10分钟），避免本地大模型思考过久被强杀
```

### 第三步：在 Web UI 中同步与验证
1. 确保 `omlx` 已在后台运行 (`omlx serve ...`)。
2. 打开 `http://localhost:8648` (Hermes Web UI)。
3. 进入 **设置 -> 模型管理**，你会看到系统已经从配置文件中读取了 `omlx-local` Provider。
4. 你可以在 Web UI 的聊天窗口右上角，全局切换模型为你加载的 `qwen3.6-35B`。

### 总结建议
32G 内存跑 35B 量化版本是“小马拉大车”。核心策略是：
1. **重度依赖 Web UI 的“多会话后台执行”**：发起任务后关掉页面，不干预它的进度。
2. **配合 `rtk-hermes` 插件**：大幅度削减送给大模型的 Token 数量，这是本地环境降本增效的命脉。
3. **保持 omlx 常驻**：开启其显存/内存管理优化，避免频繁的模型加载/卸载导致死机。
