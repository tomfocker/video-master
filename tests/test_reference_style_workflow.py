import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReferenceStyleWorkflowTest(unittest.TestCase):
    def test_skill_routes_reference_style_into_image_and_video_prompts(self):
        skill = (ROOT / "skills" / "video-master" / "SKILL.md").read_text(encoding="utf-8")
        prompt_reference = (
            ROOT / "skills" / "video-master" / "references" / "storyboard-and-video-prompts.md"
        ).read_text(encoding="utf-8")

        self.assertIn("reference_style", skill)
        self.assertIn("references/style_analysis.md", skill)
        self.assertIn("references/reference_keyframes/", skill)
        self.assertIn("native image generation", prompt_reference)
        self.assertIn("Style transfer rules", prompt_reference)
        self.assertIn("copy subjects, plot, branding, or protected style", prompt_reference)


if __name__ == "__main__":
    unittest.main()
