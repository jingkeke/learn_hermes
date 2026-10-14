import os
import asyncio
from typing import AsyncGenerator
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Log, Static, RichLog
from textual.containers import Vertical, Horizontal
from textual import work
from google import genai
from google.genai import types

# 读取 API KEY
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 设定模型版本 (2026年设定)
# 注意：为了使代码能在2025年的真实环境中进行演示，这里加了 fallback 机制。
# 如果想体验纯正的 2026 感受，可以将 fallback 均改成未来模型名
LIVE_MODEL = "gemini-3.8-live"
THINKING_MODEL = "gemini-3.8-live-extended-thinking"

# Fallback 对于实际测试非常必要，如果没有设置，将抛出找不到模型的错误
# 为演示顺畅，我们在本地真实调用时使用现有的先进模型。
ACTUAL_LIVE_MODEL = os.environ.get("ACTUAL_LIVE_MODEL", "gemini-2.5-flash")
ACTUAL_THINKING_MODEL = os.environ.get("ACTUAL_THINKING_MODEL", "gemini-2.0-flash-thinking-exp-01-21")


class EnglishTutorApp(App):
    """一个通过 Gemini 3.8 进行英语实时交流和深度解析的终端应用"""

    CSS = """
    Screen {
        layout: vertical;
    }
    #chat-log {
        height: 1fr;
        border: solid green;
        padding: 1;
        margin: 1;
    }
    #input-box {
        dock: bottom;
        margin: 1;
        border: solid cyan;
    }
    .user-msg {
        color: cyan;
    }
    .bot-msg {
        color: green;
    }
    .think-msg {
        color: yellow;
        text-style: italic;
    }
    .error-msg {
        color: red;
    }
    """

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+t", "deep_think", "Deep Analyze (Extended Thinking)"),
    ]

    def __init__(self):
        super().__init__()
        self.chat_history = []
        if GEMINI_API_KEY:
            self.client = genai.Client(api_key=GEMINI_API_KEY)
        else:
            self.client = None

    def compose(self) -> ComposeResult:
        """构建应用界面"""
        yield Header(show_clock=True)
        self.chat_log = RichLog(id="chat-log", markup=True, wrap=True)
        yield self.chat_log
        self.input_box = Input(placeholder="Type your English message here... (Press Enter to send, Ctrl+T to Analyze)", id="input-box")
        yield self.input_box
        yield Footer()

    def on_mount(self) -> None:
        """应用启动时的操作"""
        self.title = "Gemini 3.8 English Tutor"
        self.sub_title = "Powered by Google Live & Extended Thinking API (macOS 26.6)"

        if not self.client:
            self.chat_log.write("[bold red]Error: GEMINI_API_KEY environment variable not set.[/bold red]")
            self.chat_log.write("Please set it and restart the application.")
            self.input_box.disabled = True
            return

        self.chat_log.write(f"[bold green]System Info:[/bold green] macOS 26.6 / M-Series Architecture")
        self.chat_log.write(f"[bold green]Models Loaded:[/bold green] {LIVE_MODEL} (Live), {THINKING_MODEL} (Thinking)")
        self.chat_log.write("---")
        self.chat_log.write("[bold magenta]Tutor:[/bold magenta] Hello! I am your English tutor powered by Gemini 3.8. Let's practice some English!")

        # 初始化对话 session
        self.chat_session = self.client.chats.create(
            model=ACTUAL_LIVE_MODEL,
            config=types.GenerateContentConfig(
                system_instruction="You are an expert English language tutor. Your goal is to engage in a conversation with the user in English. Keep your responses natural, encouraging, and helpful. If the user makes a minor mistake, correct them gently. Reply ONLY in English.",
            )
        )

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        """处理用户按 Enter 发送的消息"""
        if not message.value.strip():
            return

        user_text = message.value
        self.input_box.value = ""

        # 显示用户消息
        self.chat_log.write(f"\n[cyan]You:[/cyan] {user_text}")
        self.chat_history.append({"role": "user", "text": user_text})

        # 异步调用流式 API
        self.stream_response(user_text)

    @work(exclusive=True, thread=True)
    def stream_response(self, user_text: str) -> None:
        """在后台线程中流式获取正常对话响应"""
        try:
            self.app.call_from_thread(self.chat_log.write, "[green]Tutor (Live):[/green] ", end="")

            response_stream = self.chat_session.send_message_stream(user_text)
            full_response = ""
            for chunk in response_stream:
                if chunk.text:
                    self.app.call_from_thread(self.chat_log.write, chunk.text, end="")
                    full_response += chunk.text

            self.app.call_from_thread(self.chat_log.write, "\n")
            self.chat_history.append({"role": "tutor", "text": full_response})

        except Exception as e:
            self.app.call_from_thread(self.chat_log.write, f"\n[red]API Error: {str(e)}[/red]\n")

    def action_deep_think(self) -> None:
        """处理按 Ctrl+T 触发的深度分析逻辑"""
        if not self.chat_history:
            self.chat_log.write("\n[yellow]System:[/yellow] No recent message to analyze.")
            return

        # 获取用户最近发的一条消息
        last_user_msg = None
        for msg in reversed(self.chat_history):
            if msg["role"] == "user":
                last_user_msg = msg["text"]
                break

        if not last_user_msg:
             self.chat_log.write("\n[yellow]System:[/yellow] No recent user message to analyze.")
             return

        self.chat_log.write(f"\n[bold magenta]Deep Analysis ({THINKING_MODEL}):[/bold magenta]")
        self.chat_log.write(f"[italic]Analyzing your last sentence: '{last_user_msg}'[/italic]")

        self.run_extended_thinking(last_user_msg)

    @work(exclusive=True, thread=True)
    def run_extended_thinking(self, text_to_analyze: str) -> None:
        """调用 Extended Thinking 模型对文本进行深度结构分析和语法纠错"""
        try:
            prompt = f"As an expert linguistic analyzer, deeply analyze the following sentence from an English learner: '{text_to_analyze}'. Focus on grammar, syntax structure, vocabulary usage, and native-like phrasing. Provide a detailed, step-by-step thinking process on how you analyze it, and then give suggestions for improvement. Use Chinese to explain the analysis and suggestions."

            # 使用 Thinking Model
            response = self.client.models.generate_content(
                model=ACTUAL_THINKING_MODEL,
                contents=prompt,
            )

            # 由于当前 API 尚未完美暴露出完整的 raw_thinking_process，但模型本身会在文本中包含极长推演
            # 或者如果有 thinking_mode 参数则启用。在这里我们模拟模型输出了大段内容
            self.app.call_from_thread(self.chat_log.write, f"\n[yellow]Thinking Process & Results:[/yellow]")
            self.app.call_from_thread(self.chat_log.write, f"{response.text}\n")

        except Exception as e:
            self.app.call_from_thread(self.chat_log.write, f"\n[red]Extended Thinking Error: {str(e)}[/red]\n")


if __name__ == "__main__":
    app = EnglishTutorApp()
    app.run()
