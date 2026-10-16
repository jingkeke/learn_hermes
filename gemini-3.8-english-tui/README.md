# Gemini 3.8 Live Speech-to-Speech TUI Demo
> 场景时间设定：2026 年
> 系统环境：macOS 26.6 / M-Series Apple Silicon

本 Demo 旨在利用 Google 最新发布的 `gemini-3.8-live` 模型，在终端内构建一个原生的**纯语音交互 (Speech-to-Speech)** 英语陪练应用。让你在命令行中即可享受极致低延迟的 AI 语音对讲体验！

## 🌟 核心特性介绍

1. **🎤 `gemini-3.8-live` (全双工语音实时对话)**:
   - **体验**：不再需要打字！程序在后台持续监听你的麦克风，模型通过流式音频实时响应并通过扬声器播放。就像用对讲机和 Native Speaker 聊天一样流畅。
   - **TUI 界面**：界面会实时打印出你和模型对话的语音转写（字幕），让你看清每一个单词。

2. **🧠 `gemini-3.8-live-extended-thinking` (深度解析快捷键)**:
   - **体验**：当你在聊天中说了一句英文，觉得“我刚才这句语法对吗？”时，按下 `Ctrl+T`。应用会捕获你**上一句说出的英文转写**，调用思考模型进行深度语法拆解。

## 🛠️ 环境依赖与安装

本项目专门为 macOS 优化，因为涉及到原生音频输入输出，需要安装底层音频库。

### 1. 系统级音频依赖 (macOS)
在运行 Python 代码前，你需要通过 Homebrew 安装 `portaudio`：
```bash
brew install portaudio
```
*(如果你是 Linux，请使用 `sudo apt-get install portaudio19-dev`)*

### 2. 获取代码与依赖安装
使用现代化且极其快速的 Python 包管理器 [uv](https://github.com/astral-sh/uv) 进行部署：

```bash
uv add textual google-genai pyaudio
```

### 3. 配置 API Key

你需要从 [Google AI Studio](https://aistudio.google.com/) 获取 API Key。

```bash
export GEMINI_API_KEY="AIzaSyYourApiKeyHere..."
```

**⚠️ 2025 年的 Fallback 运行说明 (重要)：**
本应用默认调用 `gemini-3.8-live`，并在 2025 年环境自动 fallback 到 `gemini-2.0-flash-exp` 等可用模型。

## 🚀 启动与使用指南

```bash
uv run app.py
```

### 快捷键与操作

- **🎤 直接说话**：启动后，应用会自动连接麦克风。你说话时，屏幕会显示转写字幕，模型会用**语音**回答你。
- **⌨️ 文本输入框 (可选)**：底部的输入框可以用来给模型发送文本指令（比如：“请换成英音” 或 “我们来聊聊科技”）。
- **🎧 `Ctrl+P` (麦克风开关)**：随时暂停/恢复麦克风收音。
- **🧠 `Ctrl+T` (深度分析)**：对你刚才说的**上一句话**进行深度纠错和分析。
- **❌ `Ctrl+Q`**：安全退出应用并释放麦克风。
