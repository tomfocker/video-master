import json
import http.server
import subprocess
import sys
import tempfile
import threading
import unittest
from contextlib import contextmanager
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TTS = ROOT / "skills" / "video-master" / "scripts" / "generate_voiceover_tts.py"
WAV_BYTES = (
    b"RIFF"
    + (36).to_bytes(4, "little")
    + b"WAVEfmt "
    + (16).to_bytes(4, "little")
    + (1).to_bytes(2, "little")
    + (1).to_bytes(2, "little")
    + (48000).to_bytes(4, "little")
    + (96000).to_bytes(4, "little")
    + (2).to_bytes(2, "little")
    + (16).to_bytes(2, "little")
    + b"data"
    + (0).to_bytes(4, "little")
)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class RecordingVoxCPMServer(http.server.ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self):
        super().__init__(("127.0.0.1", 0), VoxCPMHandler)
        self.requests = []


class VoxCPMHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        self.server.requests.append(
            {
                "path": self.path,
                "headers": dict(self.headers),
                "body": json.loads(body.decode("utf-8")),
            }
        )
        self.send_response(200)
        self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Disposition", 'attachment; filename="voiceover.wav"')
        self.end_headers()
        self.wfile.write(WAV_BYTES)

    def log_message(self, format, *args):
        return


@contextmanager
def voxcpm_server():
    server = RecordingVoxCPMServer()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server, f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


class GenerateVoiceoverTTSTest(unittest.TestCase):
    def test_dry_run_exports_voiceover_text_and_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            write(
                project / "audio" / "tts_lines.json",
                json.dumps(
                    [
                        {"id": "VO01", "start": "00:00", "end": "00:02", "text": "第一句开场。"},
                        {"id": "VO02", "start": "00:02", "end": "00:05", "text": "第二句介绍产品。"},
                    ],
                    ensure_ascii=False,
                ),
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(TTS),
                    str(project),
                    "--voice",
                    "zh-CN-XiaoxiaoNeural",
                    "--dry-run",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            text = (project / "最终交付" / "03_口播与字幕" / "口播文本.txt").read_text(encoding="utf-8")
            self.assertIn("第一句开场。", text)
            self.assertIn("第二句介绍产品。", text)
            manifest = json.loads(
                (project / "qa" / "metadata" / "tts_manifest.json").read_text(encoding="utf-8")
            )
            self.assertTrue(manifest["dry_run"])
            self.assertEqual(manifest["voice"], "zh-CN-XiaoxiaoNeural")
            self.assertEqual(manifest["line_count"], 2)

    def test_voxcpm2_engine_posts_lines_to_local_api_and_writes_wav_manifest(self):
        with tempfile.TemporaryDirectory() as tmp, voxcpm_server() as (server, base_url):
            project = Path(tmp) / "project"
            write(
                project / "audio" / "tts_lines.json",
                json.dumps(
                    [
                        {"id": "VO01", "start": "00:00", "end": "00:02", "text": "第一句开场。"},
                        {"id": "VO02", "start": "00:02", "end": "00:05", "text": "第二句介绍产品。"},
                    ],
                    ensure_ascii=False,
                ),
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(TTS),
                    str(project),
                    "--engine",
                    "voxcpm2",
                    "--tts-base-url",
                    f"{base_url}/ui/",
                    "--persona",
                    "小潮院长",
                    "--control-instruction",
                    "中文男声，自然口播，清晰稳定。",
                    "--cfg-value",
                    "1.5",
                    "--dit-steps",
                    "12",
                    "--api-key",
                    "test-key",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            output = project / "最终交付" / "03_口播与字幕" / "口播音频.wav"
            self.assertEqual(output.read_bytes(), WAV_BYTES)
            self.assertEqual(len(server.requests), 1)
            request = server.requests[0]
            self.assertEqual(request["path"], "/api/tts")
            headers = {key.lower(): value for key, value in request["headers"].items()}
            self.assertEqual(headers["x-api-key"], "test-key")
            payload = request["body"]
            self.assertIn("第一句开场。", payload["text"])
            self.assertIn("第二句介绍产品。", payload["text"])
            self.assertEqual(payload["persona"], "小潮院长")
            self.assertEqual(payload["control_instruction"], "中文男声，自然口播，清晰稳定。")
            self.assertEqual(payload["cfg_value"], 1.5)
            self.assertFalse(payload["do_normalize"])
            self.assertFalse(payload["denoise"])
            self.assertEqual(payload["dit_steps"], 12)
            manifest = json.loads(
                (project / "qa" / "metadata" / "tts_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["engine"], "voxcpm2")
            self.assertEqual(manifest["voice"], "小潮院长")
            self.assertEqual(manifest["persona"], "小潮院长")
            self.assertEqual(manifest["base_url"], base_url)
            self.assertEqual(manifest["api_endpoint"], f"{base_url}/api/tts")
            self.assertEqual(manifest["content_type"], "audio/wav")
            self.assertEqual(manifest["byte_count"], len(WAV_BYTES))

    def test_voxcpm2_dry_run_records_wav_output_without_calling_service(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            write(
                project / "audio" / "tts_lines.json",
                json.dumps([{"id": "VO01", "text": "只打包文本，不调用服务。"}], ensure_ascii=False),
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(TTS),
                    str(project),
                    "--engine",
                    "voxcpm2",
                    "--tts-base-url",
                    "http://127.0.0.1:9",
                    "--dry-run",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            output = project / "最终交付" / "03_口播与字幕" / "口播音频.wav"
            self.assertFalse(output.exists())
            manifest = json.loads(
                (project / "qa" / "metadata" / "tts_manifest.json").read_text(encoding="utf-8")
            )
            self.assertTrue(manifest["dry_run"])
            self.assertEqual(manifest["engine"], "voxcpm2")
            self.assertEqual(manifest["output"], str(output.resolve()))


if __name__ == "__main__":
    unittest.main()
