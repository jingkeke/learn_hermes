# Gemini 3.8 Live & Extended Thinking TUI Demo
> 场景时间设定：2026 年
> 系统环境：macOS 26.6 / M-Series Apple Silicon

本 Demo 旨在利用 Google 最新发布的 `gemini-3.8-live` 和 `gemini-3.8-live-extended-thinking` 模型，在终端内构建一个原生的极速英语陪练应用。它是一个精简的 MVP（Minimum Viable Product），让你在命令行中即可享受极致的 AI 英语学习体验。

## 🌟 核心特性介绍

根据 Google 最新的开发者文档，本应用展示了两种截然不同但又互补的 AI 范式：

1. **`gemini-3.8-live` (实时对话模式)**:
   - **特点**：主打超低延迟（Ultra-low latency）的对话流。
   - **体验**：在终端输入内容后，模型几乎在按回车的瞬间流式输出回答，带来如同与真人通过微信/iMessage 高速聊天的爽快感。在此应用中，它扮演你的**“Native English Speaker 聊天搭子”**，专门负责语感和流利度的训练。

2. **`gemini-3.8-live-extended-thinking` (深度解析模式)**:
   - **特点**：允许模型开启内部隐式思维链 (Chain of Thought)，用额外的计算时间换取极高的逻辑深度。
   - **体验**：当你在聊天中不确定自己上一句英语说得对不对时，按下快捷键触发此模型。它会像一位**“资深语言学教授”**，通过详尽的分析过程 (Thinking Process)，从语法、词汇、句法结构到地道表达，对你的句子进行拆解和中文辅导。

## 🛠️ 环境依赖与安装

本项目专门为 macOS 26.6 和 Apple Silicon 优化，并推荐使用现代化且极其快速的 Python 包管理器 [uv](https://github.com/astral-sh/uv) 进行部署。

### 1. 安装 `uv` (如尚未安装)
访问官网按照指示安装: https://github.com/astral-sh/uv

### 2. 获取代码与依赖安装
确保你已经进入了 `gemini-3.8-english-tui` 目录，然后直接通过 `uv` 运行脚本（它会自动处理虚拟环境和依赖）：

```bash
# 如果你想显式安装依赖，可以运行：
uv add textual google-genai
```

### 3. 配置 API Key

你需要从 [Google AI Studio](https://aistudio.google.com/) 获取 API Key。
为了使得应用顺利运行，你需要设置环境变量：

```bash
export GEMINI_API_KEY="AIzaSyYourApiKeyHere..."
```

**⚠️ 2025 年的 Fallback 运行说明 (重要)：**
虽然设定中调用的是 `gemini-3.8-live`，但如果你在当前的真实年份（2025年左右）运行这段代码，官方服务器并没有 3.8 的模型标识。
本应用内置了自动 Fallback 机制：默认使用当前最新的 `gemini-2.5-flash` 模拟实时聊天，使用 `gemini-2.0-flash-thinking-exp-01-21` 模拟深度思考。
如果你想强制改写 fallback 模型进行测试，可配置：
```bash
export ACTUAL_LIVE_MODEL="你的实际聊天模型名称"
export ACTUAL_THINKING_MODEL="你的实际深度模型名称"
```

## 🚀 启动与使用指南

直接使用 `uv` 来极速启动应用：

```bash
uv run app.py
```

### 操作说明

启动后，你将看到一个由 `Textual` 框架驱动的美观终端界面。

- **输入框交互**：直接在底部的输入框用英文与 Tutor 对话。输入完成后按 `Enter` 发送。模型将以极速在主屏幕上流式打印回复。
- **快捷键 `Ctrl+T` (深度分析)**：当你刚发出一句话，觉得“我刚才这句语法对吗？”或者“有没有更地道的表达？”时，按下 `Ctrl+T`。后台将调度 `gemini-3.8-live-extended-thinking` 模型，对你**最后一次发言**进行拆解、纠错并用中文提供长篇的深度学习建议。
- **快捷键 `Ctrl+Q`**：随时退出应用。

## 💡 架构设计理念
本项目遵循了 Google 的 [Live API guidelines](https://ai.google.dev/gemini-api/docs/live-api) 和 MVP 原则。虽然是在文本终端运行，但由于底层依托新一代 SDK (google-genai) 的高效传输和后台线程 (`@work` 装饰器) 处理，UI 绝对不会因为网络 I/O 阻塞而卡顿，展示了真正的终端原生高性能 TUI。
