import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DependenciesTest(unittest.TestCase):
    def test_project_declares_skill_dependencies(self):
        root_requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        skill_requirements = (ROOT / "skills" / "video-master" / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("-r skills/video-master/requirements.txt", root_requirements)
        self.assertIn("Pillow", skill_requirements)
        self.assertIn("openpyxl", skill_requirements)
        self.assertIn("pydantic", skill_requirements)
        self.assertIn("pysubs2", skill_requirements)
        self.assertIn("imageio[ffmpeg]", skill_requirements)
        self.assertIn("numpy", skill_requirements)
        self.assertIn("edge-tts", skill_requirements)


if __name__ == "__main__":
    unittest.main()
