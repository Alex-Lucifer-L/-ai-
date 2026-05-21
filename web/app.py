"""Local web frontend for the Xiamen policy AI assistant."""

from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AI_SOURCE_ROOT = PROJECT_ROOT / "ai"
STATIC_ROOT = Path(__file__).resolve().parent / "static"

sys.path.insert(0, str(AI_SOURCE_ROOT))

from ai.config import load_ai_config  # noqa: E402
from ai.qa_service import QAService  # noqa: E402


class PolicyWebHandler(SimpleHTTPRequestHandler):
    server_version = "PolicyAIWeb/0.1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_ROOT), **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._send_json(
                {
                    "ok": True,
                    "service": "xiamen-policy-ai",
                    "llm_model": self.server.qa_service.llm.config.model,
                    "llm_provider": self.server.qa_service.llm.config.provider,
                }
            )
            return

        if parsed.path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/ask":
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return

        try:
            payload = self._read_json()
            question = str(payload.get("question", "")).strip()
            top_k = int(payload.get("top_k", 5))
            dry_run = bool(payload.get("dry_run", False))
        except (json.JSONDecodeError, ValueError, TypeError):
            self._send_json({"error": "请求格式不正确。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if not question:
            self._send_json({"error": "请输入你的政策问题。"}, status=HTTPStatus.BAD_REQUEST)
            return
        if top_k < 1 or top_k > 10:
            self._send_json({"error": "top_k 需要在 1 到 10 之间。"}, status=HTTPStatus.BAD_REQUEST)
            return

        try:
            result = self.server.qa_service.answer_with_references(
                question=question,
                top_k=top_k,
                dry_run=dry_run,
            )
        except Exception as exc:  # Keep local UI readable while debugging.
            self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        self._send_json(result)

    def log_message(self, format: str, *args) -> None:
        print(f"[web] {self.address_string()} - {format % args}")

    def _read_json(self) -> dict[str, object]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def _send_json(self, payload: dict[str, object], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class PolicyWebServer(ThreadingHTTPServer):
    def __init__(self, server_address):
        super().__init__(server_address, PolicyWebHandler)
        self.qa_service = QAService(load_ai_config())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run local web UI for policy AI.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind.")
    parser.add_argument("--port", type=int, default=7860, help="Port to bind.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    server = PolicyWebServer((args.host, args.port))
    url = f"http://{args.host}:{args.port}"
    print(f"Policy AI web UI running at {url}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping web UI.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
