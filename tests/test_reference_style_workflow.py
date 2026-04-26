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

    def test_skill_documents_style_template_modes_and_override_policy(self):
        skill = (ROOT / "skills" / "video-master" / "SKILL.md").read_text(encoding="utf-8")
        output_contract = (
            ROOT / "skills" / "video-master" / "references" / "output-contract.md"
        ).read_text(encoding="utf-8")
        prompt_reference = (
            ROOT / "skills" / "video-master" / "references" / "storyboard-and-video-prompts.md"
        ).read_text(encoding="utf-8")

        self.assertIn("style_templates", skill)
        self.assertIn("template_id", skill)
        self.assertIn("template_user_overrides", skill)
        self.assertIn("user ideas override", skill)
        self.assertNotIn("template_strength", skill)
        self.assertIn("template_id", output_contract)
        self.assertIn("template_user_overrides", output_contract)
        self.assertNotIn("template_strength", output_contract)
        self.assertIn("style template", prompt_reference)
        self.assertIn("user ideas override", prompt_reference)
        self.assertNotIn("template_strength", prompt_reference)

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
        self.assertIn("Do not use mixed labels such as `声音/字幕`", skill)
        self.assertIn("Do not include a `Negative prompt` or `负面提示词` field", output_contract)
        self.assertIn("Do not include a `负面提示词` section", skill)
        self.assertIn("不要写“负面提示词”字段", prompt_reference)
        self.assertIn("背景音乐：不要生成背景音乐；整片音乐后期统一处理", prompt_reference)
        self.assertIn("Per-clip background music should stay off", prompt_reference)
        self.assertIn("analysis-only/post-production observations", prompt_reference)
        self.assertIn("must not ask models to reproduce burned subtitles or subtitle styling", skill)
        self.assertIn("Do not ask image or video models to reproduce burned subtitles", prompt_reference)

    def test_title_packaging_is_documented_as_sidecar(self):
        skill = (ROOT / "skills" / "video-master" / "SKILL.md").read_text(encoding="utf-8")
        output_contract = (
            ROOT / "skills" / "video-master" / "references" / "output-contract.md"
        ).read_text(encoding="utf-8")
        prompt_reference = (
            ROOT / "skills" / "video-master" / "references" / "storyboard-and-video-prompts.md"
        ).read_text(encoding="utf-8")

        self.assertIn("optional sidecar branch", skill)
        self.assertIn("does not modify video prompts", skill)
        self.assertIn("main_title", skill)
        self.assertIn("chapter_card", skill)
        self.assertIn("data_callout", skill)
        self.assertIn("Default title packaging output is static transparent PNG", skill)
        self.assertIn("render_title_packaging.py", skill)
        self.assertIn("title_packaging_enabled", output_contract)
        self.assertIn("title_packaging_motion_need", output_contract)
        self.assertIn("07_title_packaging", output_contract)
        self.assertIn("Do not place title-packaging instructions", output_contract)
        self.assertIn("generate_alpha_mov\": false", output_contract)
        self.assertIn("Title Packaging Prompt Sidecar", prompt_reference)
        self.assertIn("Never paste these sidecar prompts", prompt_reference)
        self.assertIn("Default to transparent PNG packaging", prompt_reference)


if __name__ == "__main__":
    unittest.main()
