import os
import asyncio
import pyaudio
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, RichLog, Static
from textual.containers import Vertical, Horizontal
from textual import work
from google import genai
from google.genai import types
from textual.binding import Binding

# ================= Configuration =================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
ACTUAL_LIVE_MODEL = os.environ.get("ACTUAL_LIVE_MODEL", "gemini-2.0-flash-exp")
ACTUAL_THINKING_MODEL = os.environ.get("ACTUAL_THINKING_MODEL", "gemini-2.0-flash-thinking-exp-01-21")

# pyaudio config (from official demo)
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

CONFIG = {
    "response_modalities": ["AUDIO"],
    "system_instruction": "You are a helpful native English tutor. Practice English conversation with the user.",
    "output_audio_transcription": {},
    "input_audio_transcription": {},
}

class EnglishTutorApp(App):
    """Gemini 3.8 Speech-to-Speech English Tutor TUI"""

    CSS = """
    Screen {
        layout: vertical;
    }
    #status-bar {
        height: 3;
        dock: top;
        background: #112233;
        color: white;
        padding: 1;
        content-align: center middle;
    }
    #chat-log {
        height: 1fr;
        border: solid green;
        margin: 1;
    }
    #input-box {
        dock: bottom;
        margin: 1;
        border: solid cyan;
    }
    .status-active { color: #00ff00; text-style: bold; }
    .status-muted { color: #ff0000; text-style: bold; }
    .status-thinking { color: #ffff00; text-style: bold; }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+p", "toggle_mic", "Toggle Mic (Mute/Unmute)"),
        Binding("ctrl+t", "deep_think", "Deep Analyze Last Sentence"),
    ]

    def __init__(self):
        super().__init__()
        self.pya = pyaudio.PyAudio()
        self.audio_queue_output = asyncio.Queue()
        self.audio_queue_mic = asyncio.Queue(maxsize=5)
        self.audio_stream = None
        self.client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

        # State variables
        self.is_mic_muted = False
        self.is_connected = False
        self.last_user_transcription = ""
        self.live_session = None
        self.tasks_group = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        self.status_bar = Static(id="status-bar")
        yield self.status_bar
        self.chat_log = RichLog(id="chat-log", markup=True, wrap=True)
        yield self.chat_log
        self.input_box = Input(placeholder="System instructions / Prompts (Press Enter to send)", id="input-box")
        yield self.input_box
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Gemini 3.8 Live Speech Tutor"
        self.update_status("Initializing...")

        if not self.client:
            self.chat_log.write("[bold red]Error: GEMINI_API_KEY not set.[/bold red]")
            return

        self.chat_log.write(f"[bold green]System Info:[/bold green] macOS 26.6 / Live Audio Mode")
        self.chat_log.write(f"[bold green]Model:[/bold green] {ACTUAL_LIVE_MODEL}")
        self.chat_log.write("---")
        self.chat_log.write("Use your microphone to speak! I will output transcription here.\n")

        self.start_live_session()

    def update_status(self, msg: str, css_class: str = "status-active") -> None:
        mic_state = "[MUTED]" if self.is_mic_muted else "[MIC ACTIVE]"
        self.status_bar.update(f"[{css_class}]Status: {msg} | Mic: {mic_state}[/{css_class}]")

    @work(exclusive=True, thread=True)
    def start_live_session(self) -> None:
        """Runs the main async loop for the Live API in a background thread."""
        asyncio.run(self._async_live_session_runner())

    async def _async_live_session_runner(self):
        try:
            self.app.call_from_thread(self.update_status, "Connecting to Live API...")
            async with self.client.aio.live.connect(model=ACTUAL_LIVE_MODEL, config=CONFIG) as live_session:
                self.live_session = live_session
                self.app.call_from_thread(self.update_status, "Connected! Start speaking.", "status-active")
                self.app.call_from_thread(self.chat_log.write, "[green]Connection established. Awaiting audio...[/green]")

                async with asyncio.TaskGroup() as tg:
                    self.tasks_group = tg
                    tg.create_task(self.listen_audio())
                    tg.create_task(self.send_realtime(live_session))
                    tg.create_task(self.receive_audio(live_session))
                    tg.create_task(self.play_audio())
        except asyncio.CancelledError:
            self.app.call_from_thread(self.chat_log.write, "[yellow]Session cancelled.[/yellow]")
        except Exception as e:
            self.app.call_from_thread(self.chat_log.write, f"[red]Live API Error: {str(e)}[/red]")
        finally:
            self.app.call_from_thread(self.update_status, "Disconnected", "status-muted")
            if self.audio_stream:
                self.audio_stream.close()

    async def listen_audio(self):
        mic_info = self.pya.get_default_input_device_info()
        self.audio_stream = await asyncio.to_thread(
            self.pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=SEND_SAMPLE_RATE,
            input=True,
            input_device_index=mic_info["index"],
            frames_per_buffer=CHUNK_SIZE,
        )
        kwargs = {"exception_on_overflow": False}
        while True:
            data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, **kwargs)
            if not self.is_mic_muted:
                await self.audio_queue_mic.put({"data": data, "mime_type": "audio/pcm"})

    async def send_realtime(self, session):
        while True:
            msg = await self.audio_queue_mic.get()
            if not self.is_mic_muted:
                await session.send_realtime_input(audio=msg)

    async def receive_audio(self, session):
        """Receives responses and manages UI text append correctly without using the unsupported 'end' argument."""
        last_was_input = False
        current_input_buffer = ""
        current_output_buffer = ""

        while True:
            turn = session.receive()
            async for response in turn:
                sc = response.server_content
                if not sc:
                    continue

                # Handle Audio Output
                if sc.model_turn:
                    for part in sc.model_turn.parts:
                        if part.inline_data and isinstance(part.inline_data.data, bytes):
                            self.audio_queue_output.put_nowait(part.inline_data.data)

                # Handle Model Transcription (Output)
                if sc.output_transcription:
                    if last_was_input and current_input_buffer:
                        # Flush input buffer
                        self.app.call_from_thread(self.chat_log.write, f"[cyan]You:[/cyan] [i]{current_input_buffer}[/i]")
                        self.last_user_transcription = current_input_buffer
                        current_input_buffer = ""
                        last_was_input = False

                    t = sc.output_transcription.text
                    current_output_buffer += t
                    if t.rstrip()[-1:] in '.!?':
                        self.app.call_from_thread(self.chat_log.write, f"[green]Tutor:[/green] {current_output_buffer}")
                        current_output_buffer = ""

                # Handle User Transcription (Input)
                if sc.input_transcription:
                    if not last_was_input and current_output_buffer:
                        # Flush output buffer
                        self.app.call_from_thread(self.chat_log.write, f"[green]Tutor:[/green] {current_output_buffer}")
                        current_output_buffer = ""
                        last_was_input = True

                    t = sc.input_transcription.text
                    current_input_buffer += t
                    if t.rstrip()[-1:] in '.!?':
                        self.app.call_from_thread(self.chat_log.write, f"[cyan]You:[/cyan] [i]{current_input_buffer}[/i]")
                        self.last_user_transcription = current_input_buffer
                        current_input_buffer = ""

            # Empty output queue on interruption
            while not self.audio_queue_output.empty():
                self.audio_queue_output.get_nowait()

    async def play_audio(self):
        stream = await asyncio.to_thread(
            self.pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
        )
        while True:
            bytestream = await self.audio_queue_output.get()
            await asyncio.to_thread(stream.write, bytestream)

    def action_toggle_mic(self) -> None:
        self.is_mic_muted = not self.is_mic_muted
        self.update_status("Connected", "status-active")

    def action_deep_think(self) -> None:
        if not self.last_user_transcription:
            self.chat_log.write("[yellow]System: No recent speech transcription to analyze.[/yellow]")
            return

        self.update_status("Extended Thinking...", "status-thinking")
        self.chat_log.write(f"\n[bold magenta]Deep Analysis (Extended Thinking):[/bold magenta]")
        self.chat_log.write(f"[italic]Analyzing: '{self.last_user_transcription}'[/italic]")

        self.run_extended_thinking(self.last_user_transcription)

    @work(exclusive=True, thread=True)
    def run_extended_thinking(self, text_to_analyze: str) -> None:
        try:
            prompt = f"As an expert linguistic analyzer, deeply analyze the following sentence from an English learner: '{text_to_analyze}'. Focus on grammar, syntax structure, vocabulary usage, and native-like phrasing. Provide a detailed, step-by-step thinking process on how you analyze it, and then give suggestions for improvement. Use Chinese."
            response = self.client.models.generate_content(
                model=ACTUAL_THINKING_MODEL,
                contents=prompt,
            )
            self.app.call_from_thread(self.chat_log.write, f"\n[yellow]Analysis Result:[/yellow]\n{response.text}\n")
        except Exception as e:
            self.app.call_from_thread(self.chat_log.write, f"[red]Analysis Error: {str(e)}[/red]")
        finally:
             self.app.call_from_thread(self.update_status, "Connected", "status-active")

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        """允许通过输入框发送文本消息或指令，混合文本与语音"""
        if not message.value.strip():
            return

        user_text = message.value
        self.input_box.value = ""
        self.chat_log.write(f"[cyan]You (Text):[/cyan] {user_text}")

        # 我们可以通过 Live Session 原生发送文本
        if self.live_session:
            asyncio.run_coroutine_threadsafe(
                self.live_session.send_realtime_input(text=user_text),
                self.workers[0].thread.loop # 这是一个稍微 hack 的方式跨线程发送，在更复杂的应用中应该使用专用的队列
            )

    def on_unmount(self) -> None:
        if self.audio_stream:
            self.audio_stream.close()
        self.pya.terminate()

if __name__ == "__main__":
    app = EnglishTutorApp()
    app.run()
