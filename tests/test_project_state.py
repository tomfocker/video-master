import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.test_validate_video_project import make_project, write


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "video-master" / "scripts" / "project_state.py"


def load_module():
    spec = importlib.util.spec_from_file_location("project_state", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ProjectStateTest(unittest.TestCase):
    def test_builds_workflow_state_for_autopilot_project(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(
                Path(tmp),
                durations=[3, 4, 4, 6, 5, 3, 5],
                extra_spec_lines=[
                    "",
                    "## workflow",
                    "- workflow_mode: autopilot",
                    "- confirmation_policy: ask_only_blockers",
                    "- assumption_policy: auto_fill_with_log",
                    "- assumption_log: qa/metadata/workflow_events.jsonl",
                    "",
                    "## visual_style",
                    "- visual_style_lock: confirmed",
                    "- visual_style_preset_id: photoreal_commercial",
                    "- visual_style_preset_name: Photoreal Commercial",
                ],
                shot_overrides={
                    "S01": {
                        "purpose": "Open with a product reveal.",
                        "visual_action": "Slow push into reflective packaging.",
                        "camera_movement": "controlled dolly in",
                    }
                },
            )
            write(
                project / "prompts" / "storyboard_image_prompts.md",
                "# Image Prompts\n\n## S01\nPhotoreal commercial product hero frame.\n",
            )
            write(
                project / "audio" / "voiceover_script.md",
                "# Voiceover\n\n"
                "- VO01 (0-3s): 这一刻，光先认出了她。\n"
                "- VO07 (24-30s): 留住这一刻的光。\n",
            )
            write(
                project / "audio" / "music_sfx_cue_sheet.md",
                "# Music SFX\n\n"
                "- S01 00:00-00:03: 闪光灯与红毯人群低语。\n"
                "- S07 00:24-00:30: 品牌落版音效。\n",
            )
            write(
                project / "qa" / "metadata" / "codex_shot_requests.json",
                json.dumps(
                    [
                        {
                            "request_id": "idea_001",
                            "status": "pending",
                            "idea": "补一个粉底液滴落到皮肤上的微距镜头。",
                            "x": 620,
                            "y": 480,
                            "insert_after_shot_id": "S02",
                        }
                    ],
                    ensure_ascii=False,
                ),
            )

            state = module.build_project_state(project)

            self.assertEqual(state["schema_version"], 1)
            self.assertEqual(state["workflow"]["workflow_mode"], "autopilot")
            self.assertEqual(state["workflow"]["confirmation_policy"], "ask_only_blockers")
            self.assertEqual(state["visual_style"]["visual_style_preset_id"], "photoreal_commercial")
            self.assertEqual(len(state["shots"]), 7)
            self.assertEqual(state["shots"][0]["shot_id"], "S01")
            self.assertIn("product reveal", state["shots"][0]["purpose"])
            self.assertIn("Photoreal commercial", state["shots"][0]["image_prompt"])
            self.assertEqual(state["copywriting"]["status"], "complete")
            self.assertTrue(state["copywriting"]["files"]["voiceover"]["exists"])
            self.assertTrue(state["copywriting"]["files"]["captions"]["exists"])
            self.assertIn("这一刻", state["copywriting"]["voiceover_preview"])
            self.assertIn("这一刻", state["shots"][0]["copywriting"]["voiceover"])
            self.assertIn("闪光灯", state["shots"][0]["copywriting"]["sfx"])
            self.assertEqual(state["shots"][0]["packaging"]["role"], "片头标题/主视觉钩子")
            self.assertEqual(state["shots"][-1]["packaging"]["role"], "品牌落版/CTA")
            self.assertEqual(state["shot_requests"][0]["request_id"], "idea_001")
            self.assertEqual(state["shot_requests"][0]["status"], "pending")
            self.assertIn("粉底液滴落", state["shot_requests"][0]["idea"])

            nodes = {node["id"]: node for node in state["flow_nodes"]}
            self.assertEqual(nodes["visual_style"]["status"], "complete")
            self.assertEqual(nodes["storyboard_images"]["frame_count"], 7)

    def test_builds_character_lock_state_before_storyboard_images(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(
                Path(tmp),
                durations=[3, 4, 4, 6, 5, 3, 5],
                extra_spec_lines=[
                    "",
                    "## visual_style",
                    "- visual_style_lock: confirmed",
                    "- visual_style_preset_id: photoreal_commercial",
                    "",
                    "## character_design",
                    "- character_lock_enabled: true",
                    "- character_lock_status: confirmed",
                    "- fixed_characters: host_a",
                    "- character_reference_dir: characters/",
                    "- character_prompt_rules: every storyboard prompt must reference host_a from the character bible",
                ],
            )
            write(project / "characters" / "character_bible.md", "# Character Bible\n\n## host_a\n")
            write(
                project / "characters" / "character_manifest.json",
                json.dumps({"characters": [{"id": "host_a", "name": "主持人 A"}]}, ensure_ascii=False),
            )

            state = module.build_project_state(project)

            self.assertEqual(state["character_design"]["character_lock_enabled"], "true")
            self.assertEqual(state["character_design"]["fixed_characters"], "host_a")
            self.assertIn("host_a", state["character_design"]["character_prompt_rules"])

            nodes = {node["id"]: node for node in state["flow_nodes"]}
            self.assertEqual(nodes["character_lock"]["status"], "complete")
            self.assertEqual(nodes["character_lock"]["label"], "Character Design Lock")
            self.assertLess(
                [node["id"] for node in state["flow_nodes"]].index("character_lock"),
                [node["id"] for node in state["flow_nodes"]].index("storyboard_plan"),
            )

    def test_project_state_cli_writes_metadata_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(Path(tmp), durations=[3, 4, 4, 6, 5, 3, 5])

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(project), "--write"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            output = project / "qa" / "metadata" / "project_state.json"
            self.assertTrue(output.is_file())
            state = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(state["project"]["name"], "sample_project")
            self.assertEqual(state["workflow"]["workflow_mode"], "guided")


if __name__ == "__main__":
    unittest.main()
