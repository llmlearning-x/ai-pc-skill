"""本地 LLM 对话服务（AI PC Doctor 内置 Demo）。

加载 OpenVINO IR 格式的生成式模型，提供流式聊天网页。
作为 ai-pc-doctor full 模式的配套体验组件，也可以独立运行。

用法：
    python server.py --model-dir <OpenVINO_IR模型目录> [--device CPU] [--port 8899]
"""

import argparse
import json
import sys
import threading
import warnings
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

warnings.filterwarnings("ignore", category=DeprecationWarning)

import openvino_genai as ov_genai

# 默认从环境变量读取模型路径（doctor.py 启动时会注入）
DEFAULT_MODEL_DIR = Path(
    r"C:\Users\16426\.workbuddy\skills\ai-pc-doctor\models\genai\Qwen2-0.5B-Instruct-int4-ov"
)

HERE = Path(__file__).resolve().parent

SYSTEM_PROMPT = "你是一个运行在本地的轻量级 AI 助手，回答简洁、准确、友好。"


class ChatHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def __init__(self, pipe, config, *args, **kwargs):
        self._pipe = pipe
        self._config = config
        self._tokenizer = pipe.get_tokenizer()
        self._lock = threading.Lock()
        self._chat_started = False
        super().__init__(*args, **kwargs)

    def log_message(self, *args):
        pass

    def _send_html(self):
        html = (HERE / "index.html").read_text(encoding="utf-8")
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, status=200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send_html()
        elif self.path == "/api/info":
            self._json({"model": self._pipe.model_dir_name, "device": self._pipe.device})
        else:
            self._json({"error": "not found"}, status=404)

    def do_POST(self):
        if self.path == "/api/chat":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length) or b"{}")
            except Exception:
                body = {}
            message = (body.get("message") or "").strip()
            if not message:
                self._json({"error": "empty message"}, status=400)
                return
            self._stream_chat(message)
        elif self.path == "/api/reset":
            self._reset_chat()
            self._json({"ok": True})
        else:
            self._json({"error": "not found"}, status=404)

    def _reset_chat(self):
        with self._lock:
            try:
                if self._chat_started:
                    self._pipe.finish_chat()
            except Exception:
                pass
            self._chat_started = False

    def _stream_chat(self, message):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Transfer-Encoding", "chunked")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        try:
            with self._lock:
                if not self._chat_started:
                    self._pipe.start_chat()
                    self._chat_started = True
                self._pipe.generate(message, self._config, streamer=_Streamer(self.wfile))
        except Exception as exc:
            err = f"\n[生成出错] {exc}".encode("utf-8")
            try:
                self.wfile.write(b"%x\r\n" % len(err) + err + b"\r\n")
            except Exception:
                pass
        finally:
            try:
                self.wfile.write(b"0\r\n\r\n")
                self.wfile.flush()
            except Exception:
                pass


class _Streamer:
    """把每个 token 增量按 chunked 编码写回 HTTP 响应。"""

    def __init__(self, wfile):
        self.wfile = wfile

    def __call__(self, subword):
        data = subword.encode("utf-8")
        if data:
            self.wfile.write(b"%x\r\n" % len(data) + data + b"\r\n")
            self.wfile.flush()
        return ov_genai.StreamingStatus.RUNNING


class _PipeWrapper:
    """包装 LLMPipeline，附加 model_dir_name / device 属性供 info 接口用。"""

    def __init__(self, pipeline, model_dir_name, device):
        self._pipeline = pipeline
        self.model_dir_name = model_dir_name
        self.device = device
        self._tokenizer = pipeline.get_tokenizer()

    def get_tokenizer(self):
        return self._tokenizer

    def start_chat(self):
        self._pipeline.start_chat()

    def finish_chat(self):
        self._pipeline.finish_chat()

    def generate(self, *args, **kwargs):
        return self._pipeline.generate(*args, **kwargs)


def build_config(max_new_tokens=256, temperature=0.7, top_p=0.8, top_k=20):
    config = ov_genai.GenerationConfig()
    config.max_new_tokens = max_new_tokens
    config.do_sample = True
    config.temperature = temperature
    config.top_p = top_p
    config.top_k = top_k
    config.repetition_penalty = 1.1
    return config


def main():
    parser = argparse.ArgumentParser(
        prog="demo_chat_server", description="AI PC Doctor 本地 LLM 对话服务")
    parser.add_argument("--model-dir", type=Path, default=None,
                        help="OpenVINO IR 模型目录（默认从环境变量 AIPC_DOCTOR_MODEL_DIR 读取）")
    parser.add_argument("--device", default="CPU", choices=("CPU", "GPU", "NPU"),
                        help="推理设备（默认 CPU）")
    parser.add_argument("--port", type=int, default=8899, help="服务端口（默认 8899）")
    parser.add_argument("--host", default="127.0.0.1", help="绑定地址（默认 127.0.0.1）")
    args = parser.parse_args()

    model_dir = args.model_dir
    if model_dir is None:
        env_dir = Path(__import__("os").environ.get("AIPC_DOCTOR_MODEL_DIR", ""))
        if env_dir.exists():
            model_dir = env_dir
        else:
            model_dir = DEFAULT_MODEL_DIR

    if not model_dir.exists():
        print(f"[错误] 模型目录不存在: {model_dir}", file=sys.stderr)
        return 2

    print(f"正在加载模型: {model_dir.name} ...", flush=True)
    raw_pipe = ov_genai.LLMPipeline(str(model_dir), args.device)
    pipe = _PipeWrapper(raw_pipe, model_dir.name, args.device)
    config = build_config()
    print("模型加载完成。", flush=True)

    def make_handler(*handler_args, **handler_kwargs):
        return ChatHandler(pipe, config, *handler_args, **handler_kwargs)

    server = ThreadingHTTPServer((args.host, args.port), make_handler)
    print(f"对话服务已启动：http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    sys.exit(main())
