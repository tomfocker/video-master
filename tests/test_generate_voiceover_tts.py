import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TTS = ROOT / "skills" / "video-master" / "scripts" / "generate_voiceover_tts.py"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


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
                    "python3",
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


if __name__ == "__main__":
    unittest.main()
