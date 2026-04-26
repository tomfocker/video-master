import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "video-master" / "scripts" / "visual_style_presets.py"
PRESETS = ROOT / "skills" / "video-master" / "references" / "visual_style_presets.json"
PRESET_DOC = ROOT / "skills" / "video-master" / "references" / "visual-style-presets.md"


def load_module():
    spec = importlib.util.spec_from_file_location("visual_style_presets", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class VisualStylePresetsTest(unittest.TestCase):
    def test_visual_style_preset_library_loads(self):
        module = load_module()
        presets = module.load_presets()

        expected = {
            "imax_70mm_realism",
            "photoreal_commercial",
            "eastern_fantasy_3d",
            "hyperreal_3d_render",
            "graphic_2d_editorial",
            "soft_storybook_2d",
            "anime_cinematic_light",
            "noir_gothic",
            "future_tech_clean",
        }
        self.assertTrue(expected.issubset(set(presets)))
        for preset in presets.values():
            self.assertTrue(preset["storyboard_prompt_rules"])
            self.assertTrue(preset["video_prompt_rules"])
            self.assertEqual(preset["status"], "official")

    def test_visual_style_presets_avoid_protected_style_names(self):
        data = json.loads(PRESETS.read_text(encoding="utf-8"))
        text = json.dumps(data, ensure_ascii=False).lower()
        for blocked in ["pixar", "ghibli", "miyazaki", "shinkai"]:
            self.assertNotIn(blocked, text)

    def test_spec_lock_markdown_can_be_generated(self):
        module = load_module()
        preset = module.get_preset("photoreal_commercial")
        markdown = module.build_spec_lock_visual_style(preset)

        self.assertIn("visual_style_preset_id: photoreal_commercial", markdown)
        self.assertIn("storyboard_prompt_rules:", markdown)
        self.assertIn("video_prompt_rules:", markdown)

    def test_visual_style_docs_are_connected_to_workflow(self):
        skill = (ROOT / "skills" / "video-master" / "SKILL.md").read_text(encoding="utf-8")
        output_contract = (
            ROOT / "skills" / "video-master" / "references" / "output-contract.md"
        ).read_text(encoding="utf-8")
        prompt_reference = (
            ROOT / "skills" / "video-master" / "references" / "storyboard-and-video-prompts.md"
        ).read_text(encoding="utf-8")
        preset_doc = PRESET_DOC.read_text(encoding="utf-8")

        self.assertIn("visual_style_preset_id", skill)
        self.assertIn("Step 3.6: Visual Style Preset Lock", skill)
        self.assertIn("before `prompts/storyboard_image_prompts.md` is written", skill)
        self.assertIn("visual_style_preset_id", output_contract)
        self.assertIn("Visual Style Preset Application", prompt_reference)
        self.assertIn("Preset Cards", preset_doc)

    def test_visual_style_cli_lists_presets(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--list"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("photoreal_commercial", result.stdout)
        self.assertIn("IMAX 70mm Cinematic Realism", result.stdout)


if __name__ == "__main__":
    unittest.main()
