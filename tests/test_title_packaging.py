import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tests.test_validate_video_project import make_project


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "video-master" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from delivery_paths import video_prompt_path

RENDERER = ROOT / "skills" / "video-master" / "scripts" / "render_title_packaging.py"
VALIDATOR = ROOT / "skills" / "video-master" / "scripts" / "validate_video_project.py"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_renderer_module():
    spec = importlib.util.spec_from_file_location("render_title_packaging", RENDERER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TitlePackagingTest(unittest.TestCase):
    def test_render_frame_preserves_transparent_background(self):
        renderer = load_renderer_module()
        image = renderer.render_frame(
            {
                "id": "main_title",
                "type": "title_card",
                "text": "TITLE",
                "subtitle": "Commercial film",
                "position": "center",
            },
            (640, 360),
        )

        self.assertEqual(image.mode, "RGBA")
        alpha = image.getchannel("A")
        self.assertEqual(alpha.getpixel((0, 0)), 0)
        self.assertGreater(alpha.getextrema()[1], 0)

    def test_renders_transparent_png_sidecar_without_alpha_mov(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            write(
                project / "packaging" / "title_packaging_plan.json",
                json.dumps(
                    {
                        "aspect_ratio": "16:9",
                        "generate_alpha_mov": False,
                        "items": [
                            {
                                "id": "main_title",
                                "type": "title_card",
                                "text": "追光少年",
                                "subtitle": "BRAND FILM",
                                "position": "center",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
            )

            result = subprocess.run(
                [sys.executable, str(RENDERER), str(project), "--skip-alpha-mov"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            manifest_path = project / "qa" / "metadata" / "title_packaging_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertTrue(manifest["title_packaging"])
            item = manifest["items"][0]
            self.assertIsNone(item["alpha_mov"])
            png_path = project / item["transparent_png"]
            self.assertTrue(png_path.is_file())
            with Image.open(png_path) as image:
                self.assertEqual(image.mode, "RGBA")
                alpha = image.getchannel("A")
                self.assertEqual(alpha.getpixel((0, 0)), 0)
            self.assertGreater(alpha.getextrema()[1], 0)

    def test_defaults_to_static_packaging_images_without_mov(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            write(
                project / "packaging" / "title_packaging_plan.json",
                json.dumps(
                    {
                        "aspect_ratio": "16:9",
                        "items": [
                            {
                                "id": "chapter_01",
                                "type": "chapter_card",
                                "text": "第一章 启程",
                                "subtitle": "CHAPTER 01",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
            )

            result = subprocess.run(
                [sys.executable, str(RENDERER), str(project)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            manifest = json.loads(
                (project / "qa" / "metadata" / "title_packaging_manifest.json").read_text(encoding="utf-8")
            )
            item = manifest["items"][0]
            self.assertEqual(item["type"], "chapter_card")
            self.assertIsNone(item["alpha_mov"])
            self.assertTrue((project / item["transparent_png"]).is_file())
            self.assertFalse((project / "最终交付" / "07_title_packaging" / "chapter_01.mov").exists())

    def test_renders_meaningful_alpha_mov_template_when_requested(self):
        renderer = load_renderer_module()
        try:
            renderer.ffmpeg_executable()
        except renderer.PackagingError:
            self.skipTest("ffmpeg is not available")

        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            write(
                project / "packaging" / "title_packaging_plan.json",
                json.dumps(
                    {
                        "canvas": {"width": 320, "height": 180},
                        "fps": 8,
                        "duration_seconds": 0.5,
                        "generate_alpha_mov": True,
                        "items": [
                            {
                                "id": "annotation",
                                "type": "data_callout",
                                "text": "NOTE",
                                "motion_template": "marker_annotation",
                                "motion_supersample": 1,
                                "alpha_mov": True,
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
            )

            result = subprocess.run(
                [sys.executable, str(RENDERER), str(project)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            manifest = json.loads(
                (project / "qa" / "metadata" / "title_packaging_manifest.json").read_text(encoding="utf-8")
            )
            item = manifest["items"][0]
            self.assertEqual(item["motion_template"], "marker_annotation")
            self.assertIsNotNone(item["alpha_mov"])
            mov_path = project / item["alpha_mov"]
            self.assertTrue(mov_path.is_file())
            self.assertGreater(mov_path.stat().st_size, 0)

    def test_validator_treats_title_packaging_as_optional_sidecar(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(
                Path(tmp),
                durations=[3, 4, 4, 6, 5, 3, 5],
                extra_spec_lines=["- title_packaging_enabled: true"],
            )
            write(
                project / "packaging" / "title_packaging_plan.json",
                json.dumps(
                    {
                        "aspect_ratio": "9:16",
                        "items": [{"id": "main_title", "type": "title_card", "text": "追光少年"}],
                    },
                    ensure_ascii=False,
                ),
            )

            render = subprocess.run(
                [sys.executable, str(RENDERER), str(project), "--skip-alpha-mov"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(render.returncode, 0, render.stdout + render.stderr)

            result = subprocess.run(
                [sys.executable, str(VALIDATOR), str(project)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            write(
                video_prompt_path(project),
                "# Copy Ready\n\n"
                "## S01\n"
                "title_packaging: use alpha_mov after generation\n"
                "澹伴煶/鍙ｆ挱锛氬閮ㄧ敾澶栭煶锛屽悗鏈熸坊鍔犮€俓n"
                "鑳屾櫙闊充箰锛氫笉瑕佺敓鎴愯儗鏅煶涔愩€俓n"
                "SFX闊虫晥锛氶洦澹般€俓n"
                "鐢婚潰鏂囧瓧绛栫暐锛氭ā鍨嬬敓鎴愮敾闈笉娣诲姞瀛楀箷銆俓n",
            )
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), str(project)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("title packaging must stay out of copy-ready video prompts", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
