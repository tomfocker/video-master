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

    def test_skill_documents_style_template_modes_and_strengths(self):
        skill = (ROOT / "skills" / "video-master" / "SKILL.md").read_text(encoding="utf-8")
        output_contract = (
            ROOT / "skills" / "video-master" / "references" / "output-contract.md"
        ).read_text(encoding="utf-8")
        prompt_reference = (
            ROOT / "skills" / "video-master" / "references" / "storyboard-and-video-prompts.md"
        ).read_text(encoding="utf-8")

        self.assertIn("style_templates", skill)
        self.assertIn("template_id", skill)
        self.assertIn("template_strength", skill)
        self.assertIn("light", skill)
        self.assertIn("medium", skill)
        self.assertIn("high", skill)
        self.assertIn("template_id", output_contract)
        self.assertIn("template_strength", output_contract)
        self.assertIn("style template", prompt_reference)

    def test_style_template_guardrails_are_documented(self):
        skill = (ROOT / "skills" / "video-master" / "SKILL.md").read_text(encoding="utf-8")
        output_contract = (
            ROOT / "skills" / "video-master" / "references" / "output-contract.md"
        ).read_text(encoding="utf-8")
        prompt_reference = (
            ROOT / "skills" / "video-master" / "references" / "storyboard-and-video-prompts.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "Do not use a draft style template for a final project unless the user explicitly opts in with `allow_draft_template: true`",
            skill,
        )
        self.assertIn("- template_id: <template_id when style_route is use_style_template>", output_contract)
        self.assertNotIn("- template_id: cinematic-flow-racing", output_contract)
        self.assertIn(
            "- template_strength: <light | medium | high when template_id is set>",
            output_contract,
        )
        self.assertIn("Do not use mixed labels such as `声音/字幕`", skill)
        self.assertIn("Do not include a `Negative prompt` or `负面提示词` field", output_contract)
        self.assertIn("Do not include a `负面提示词` section", skill)
        self.assertIn("不要写“负面提示词”字段", prompt_reference)
        self.assertIn("背景音乐：不要生成背景音乐；整片音乐后期统一处理", prompt_reference)
        self.assertIn("Per-clip background music should stay off", prompt_reference)
        self.assertIn("analysis-only/post-production observations", prompt_reference)
        self.assertIn("must not ask models to reproduce burned subtitles or subtitle styling", skill)
        self.assertIn("Do not ask image or video models to reproduce burned subtitles", prompt_reference)


if __name__ == "__main__":
    unittest.main()
