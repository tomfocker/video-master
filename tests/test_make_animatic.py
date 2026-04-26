import base64
import importlib.util
import json
import subprocess
import tempfile
import unittest
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANIMATIC = ROOT / "skills" / "video-master" / "scripts" / "make_animatic.py"
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_animatic_module():
    spec = importlib.util.spec_from_file_location("make_animatic", ANIMATIC)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class MakeAnimaticTest(unittest.TestCase):
    def test_center_zoom_keeps_crop_center_anchored_when_enabled(self):
        animatic = load_animatic_module()
        output_size = (720, 1280)
        source_size = (941, 1672)
        for progress in [0.0, 0.25, 0.5, 0.75, 1.0]:
            crop = animatic.calculate_crop(source_size, output_size, progress, True, "center-zoom")
            crop_center_x = crop["left"] + output_size[0] / 2
            crop_center_y = crop["top"] + output_size[1] / 2
            resized_center_x = crop["resized_width"] / 2
            resized_center_y = crop["resized_height"] / 2
            self.assertLessEqual(abs(crop_center_x - resized_center_x), 0.5)
            self.assertLessEqual(abs(crop_center_y - resized_center_y), 0.5)

    def test_default_profile_is_lightweight_and_smoother(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            frames = project / "最终交付" / "01_分镜图"
            frames.mkdir(parents=True)
            (frames / "S01.png").write_bytes(PNG_1X1)
            write(
                project / "storyboard" / "shot_list.json",
                json.dumps(
                    [{"shot_id": "S01", "start": "00:00", "end": "00:01", "duration_seconds": 1}],
                    ensure_ascii=False,
                ),
            )

            result = subprocess.run(
                [
                    "python3",
                    str(ANIMATIC),
                    str(project),
                    "--title-card-seconds",
                    "0",
                    "--end-card-seconds",
                    "0",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            manifest = json.loads((project / "qa" / "metadata" / "preview_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["preview_profile"], "draft")
            self.assertEqual(manifest["fps"], 12)
            self.assertEqual(manifest["size"], "720x1280")
            self.assertEqual(manifest["motion_style"], "none")
            self.assertFalse(manifest["ken_burns_motion"])

    def test_default_size_follows_project_aspect_ratio(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            frames = project / "最终交付" / "01_分镜图"
            frames.mkdir(parents=True)
            (frames / "S01.png").write_bytes(PNG_1X1)
            write(
                project / "brief" / "spec_lock.md",
                "# Spec Lock\n\n## format\n- aspect_ratio: 16:9\n",
            )
            write(
                project / "storyboard" / "shot_list.json",
                json.dumps(
                    [{"shot_id": "S01", "start": "00:00", "end": "00:01", "duration_seconds": 1}],
                    ensure_ascii=False,
                ),
            )

            result = subprocess.run(
                [
                    "python3",
                    str(ANIMATIC),
                    str(project),
                    "--title-card-seconds",
                    "0",
                    "--end-card-seconds",
                    "0",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            manifest = json.loads((project / "qa" / "metadata" / "preview_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["size"], "1280x720")

    def test_preview_profile_off_skips_mp4_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            write(
                project / "storyboard" / "shot_list.json",
                json.dumps(
                    [{"shot_id": "S01", "start": "00:00", "end": "00:01", "duration_seconds": 1}],
                    ensure_ascii=False,
                ),
            )

            result = subprocess.run(
                ["python3", str(ANIMATIC), str(project), "--preview-profile", "off"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse((project / "最终交付" / "05_预览视频" / "分镜预览.mp4").exists())
            manifest = json.loads((project / "qa" / "metadata" / "preview_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["preview_profile"], "off")
            self.assertTrue(manifest["skipped"])
            self.assertFalse(manifest["output"])

    def test_generates_packaged_animatic_preview_video(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            frames = project / "最终交付" / "01_分镜图"
            frames.mkdir(parents=True)
            for shot_id in ["S01", "S02"]:
                (frames / f"{shot_id}.png").write_bytes(PNG_1X1)
            write(
                project / "storyboard" / "shot_list.json",
                json.dumps(
                    [
                        {"shot_id": "S01", "start": "00:00", "end": "00:01", "duration_seconds": 1},
                        {"shot_id": "S02", "start": "00:01", "end": "00:02", "duration_seconds": 1},
                    ],
                    ensure_ascii=False,
                ),
            )
            write(
                project / "audio" / "captions.srt",
                "1\n00:00:00,000 --> 00:00:01,000\n打开清晨第一束光\n\n"
                "2\n00:00:01,000 --> 00:00:02,000\n产品成为画面主角\n",
            )

            result = subprocess.run(
                [
                    "python3",
                    str(ANIMATIC),
                    str(project),
                    "--fps",
                    "2",
                    "--size",
                    "180x320",
                    "--title",
                    "美妆精华广告",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            output = project / "最终交付" / "05_预览视频" / "分镜预览.mp4"
            self.assertTrue(output.is_file())
            self.assertGreater(output.stat().st_size, 0)
            manifest = json.loads((project / "qa" / "metadata" / "preview_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["title"], "美妆精华广告")
            self.assertTrue(manifest["title_card"])
            self.assertTrue(manifest["end_card"])
            self.assertTrue(manifest["shot_overlays"])
            self.assertTrue(manifest["burned_captions"])
            self.assertFalse(manifest["ken_burns_motion"])
            self.assertFalse(manifest["voiceover_audio"])

    def test_muxes_voiceover_audio_when_provided(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            frames = project / "最终交付" / "01_分镜图"
            frames.mkdir(parents=True)
            (frames / "S01.png").write_bytes(PNG_1X1)
            write(
                project / "storyboard" / "shot_list.json",
                json.dumps(
                    [{"shot_id": "S01", "start": "00:00", "end": "00:01", "duration_seconds": 1}],
                    ensure_ascii=False,
                ),
            )
            voiceover = project / "audio" / "voiceover.wav"
            voiceover.parent.mkdir(parents=True)
            with wave.open(str(voiceover), "wb") as handle:
                handle.setnchannels(1)
                handle.setsampwidth(2)
                handle.setframerate(8000)
                handle.writeframes(b"\x00\x00" * 8000)

            result = subprocess.run(
                [
                    "python3",
                    str(ANIMATIC),
                    str(project),
                    "--fps",
                    "2",
                    "--size",
                    "180x320",
                    "--voiceover-audio",
                    str(voiceover),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            output = project / "最终交付" / "05_预览视频" / "分镜预览.mp4"
            self.assertTrue(output.is_file())
            self.assertGreater(output.stat().st_size, 0)
            manifest = json.loads((project / "qa" / "metadata" / "preview_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["voiceover_audio"], str(voiceover.resolve()))


if __name__ == "__main__":
    unittest.main()
