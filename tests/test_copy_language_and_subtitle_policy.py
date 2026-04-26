import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "video-master"


class CopyLanguageAndSubtitlePolicyTest(unittest.TestCase):
    def test_skill_requires_copy_language_and_subtitle_rendering_lock(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        output_contract = (SKILL_ROOT / "references" / "output-contract.md").read_text(encoding="utf-8")

        for text in [skill, output_contract]:
            self.assertIn("copy_language", text)
            self.assertIn("voiceover_language", text)
            self.assertIn("subtitle_rendering_policy", text)
            self.assertIn("burned_subtitles_allowed", text)

    def test_prompt_templates_separate_external_voiceover_from_generated_text(self):
        prompt_reference = (
            SKILL_ROOT / "references" / "storyboard-and-video-prompts.md"
        ).read_text(encoding="utf-8")
        audio_reference = (SKILL_ROOT / "references" / "audio-and-copy.md").read_text(encoding="utf-8")
        quality_check = (SKILL_ROOT / "references" / "quality-check.md").read_text(encoding="utf-8")

        for text in [prompt_reference, audio_reference, quality_check]:
            self.assertIn("post-production only", text)
            self.assertIn("do not generate subtitles", text)

        self.assertIn("声音/口播", prompt_reference)
        self.assertIn("画面文字策略", prompt_reference)
        self.assertNotIn("声音/字幕", prompt_reference)


if __name__ == "__main__":
    unittest.main()
