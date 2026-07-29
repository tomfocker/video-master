import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
VIDEO_MASTER = SKILLS / "video-master"


class SkillArchitectureTest(unittest.TestCase):
    def test_specialists_are_sibling_skills(self):
        for name in ["seedance-storyboard-director", "midjourney-storyboard-prompts"]:
            self.assertTrue((SKILLS / name / "SKILL.md").is_file())
            self.assertFalse((VIDEO_MASTER / name).exists())

    def test_video_master_keeps_optional_specialist_routing(self):
        skill = (VIDEO_MASTER / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("$seedance-storyboard-director", skill)
        self.assertIn("$midjourney-storyboard-prompts", skill)
        self.assertIn("Video Master remains self-contained", skill)
        self.assertIn("otherwise continue with Video Master's internal references", skill)

    def test_main_skill_stays_concise(self):
        lines = (VIDEO_MASTER / "SKILL.md").read_text(encoding="utf-8").splitlines()
        self.assertLessEqual(len(lines), 350)

    def test_specialized_scripts_are_grouped(self):
        self.assertTrue((VIDEO_MASTER / "scripts" / "ai_animation" / "validate_library.py").is_file())
        self.assertTrue((VIDEO_MASTER / "scripts" / "demos" / "render_paper_cut_collage.py").is_file())
        self.assertFalse((VIDEO_MASTER / "scripts" / "validate_ai_animation_library.py").exists())


if __name__ == "__main__":
    unittest.main()
