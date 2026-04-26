import base64
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OVERVIEW = ROOT / "skills" / "video-master" / "scripts" / "make_storyboard_overview.py"
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


class StoryboardOverviewTest(unittest.TestCase):
    def test_generates_html_overview_without_external_dependencies(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            frames = project / "最终交付" / "01_分镜图"
            frames.mkdir(parents=True)
            for name in ["S01.png", "S02.png", "S03.png"]:
                (frames / name).write_bytes(PNG_1X1)

            result = subprocess.run(
                ["python3", str(OVERVIEW), str(project)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            html = project / "qa" / "metadata" / "storyboard_overview.html"
            png = project / "最终交付" / "04_分镜总览" / "分镜总览图.png"
            self.assertTrue(html.is_file())
            self.assertTrue(png.is_file())
            self.assertFalse((project / "deliverables").exists())
            content = html.read_text(encoding="utf-8")
            self.assertIn("S01", content)
            self.assertIn("最终交付/01_分镜图/S01.png", content)
            self.assertIn("Storyboard Overview", content)


if __name__ == "__main__":
    unittest.main()
