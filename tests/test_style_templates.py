import os
import tempfile
import unittest
from pathlib import Path

import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "video-master" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from style_templates import TemplateError, load_template, list_templates


REQUIRED_PACKAGE_FILES = [
    "template.md",
    "template.json",
    "rhythm_rules.json",
    "prompt_rules.md",
    "reference_notes.md",
    "director_notes.md",
    "shot_motifs.json",
    "editing_craft.md",
    "example_shot_list.md",
]


def write_package(root, template_id="fixture", required_files=None):
    package = root / template_id
    package.mkdir()
    for filename in REQUIRED_PACKAGE_FILES:
        if filename.endswith(".json"):
            content = "{}"
        else:
            content = "# Fixture\n"
        (package / filename).write_text(content, encoding="utf-8")

    if required_files is None:
        required_files = list(REQUIRED_PACKAGE_FILES)
    template_json = {
        "id": template_id,
        "display_name": "Fixture",
        "status": "official",
        "version": "1.0.0",
        "updated_at": "2026-04-26",
        "tags": ["fixture"],
        "best_for": ["fixture"],
        "not_for": ["fixture"],
        "supported_video_modes": ["narrative-short"],
        "supported_aspect_ratios": ["16:9"],
        "duration_range_seconds": {"min": 1, "max": 2},
        "user_override_policy": ["User project ideas override template defaults."],
        "visual_rules": ["visual"],
        "rhythm_rules": ["rhythm"],
        "camera_rules": ["camera"],
        "sound_rules": ["sound"],
        "storyboard_prompt_rules": ["storyboard"],
        "video_prompt_rules": ["video"],
        "safety_boundaries": ["safety"],
        "required_files": required_files,
    }
    import json

    (package / "template.json").write_text(
        json.dumps(template_json),
        encoding="utf-8",
    )
    return package


class StyleTemplateLoaderTest(unittest.TestCase):
    def test_loads_official_cinematic_flow_racing_template(self):
        template = load_template("cinematic-flow-racing")

        self.assertEqual(template["id"], "cinematic-flow-racing")
        self.assertEqual(template["status"], "official")
        self.assertIn("意识流", template["display_name"])
        self.assertIn("高压职业", template["tags"])
        self.assertIn("user_override_policy", template)
        self.assertNotIn("strengths", template)

    def test_cinematic_flow_racing_includes_director_archive_files(self):
        package_dir = ROOT / "skills" / "video-master" / "style_templates" / "cinematic-flow-racing"

        for filename in REQUIRED_PACKAGE_FILES:
            self.assertTrue((package_dir / filename).is_file(), filename)

        import json

        motifs = json.loads((package_dir / "shot_motifs.json").read_text(encoding="utf-8"))
        self.assertIn("motifs", motifs)
        self.assertGreaterEqual(len(motifs["motifs"]), 6)

        rhythm = json.loads((package_dir / "rhythm_rules.json").read_text(encoding="utf-8"))
        self.assertEqual(len(rhythm["timeline_model_60s"]), 5)
        self.assertEqual(rhythm["timeline_model_60s"][0]["editing_logic"], "concept montage")
        self.assertEqual(len(rhythm["three_act_pressure_model"]), 3)
        self.assertIn("audio_design_model", rhythm)
        self.assertIn("gearbox scream", rhythm["audio_design_model"]["environmental_noise"])

        director_notes = (package_dir / "director_notes.md").read_text(encoding="utf-8")
        self.assertIn("五段时间线情绪动线", director_notes)
        self.assertIn("极动转极静", director_notes)
        self.assertIn("Chiaroscuro", director_notes)
        self.assertIn("主观声场", director_notes)

    def test_lists_templates_with_status_and_name(self):
        templates = list_templates()

        ids = {template["id"] for template in templates}
        self.assertIn("cinematic-flow-racing", ids)
        for template in templates:
            self.assertIn("display_name", template)
            self.assertIn(template["status"], {"draft", "official"})

    def test_rejects_missing_template(self):
        with self.assertRaisesRegex(TemplateError, "template not found"):
            load_template("missing-template")

    def test_rejects_unsafe_template_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            absolute_path = str(root / "fixture")

            for template_id in [".", "..", "../outside", "a/b", "a\\b", absolute_path]:
                with self.subTest(template_id=template_id):
                    with self.assertRaises(TemplateError):
                        load_template(template_id, template_root=root)

    def test_rejects_symlink_escape_template_id(self):
        if not hasattr(os, "symlink"):
            self.skipTest("os.symlink is unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            root.mkdir()
            outside = Path(tmp) / "outside"
            outside.mkdir()
            write_package(outside, template_id="escape")
            try:
                os.symlink(outside / "escape", root / "escape", target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlink creation is not permitted: {exc}")

            with self.assertRaises(TemplateError):
                load_template("escape", template_root=root)

    def test_rejects_incomplete_official_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "broken"
            package.mkdir()
            (package / "template.json").write_text(
                '{"id":"broken","display_name":"Broken","status":"official"}',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(TemplateError, "missing required metadata"):
                load_template("broken", template_root=root)

    def test_rejects_deprecated_strengths_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = write_package(root)
            template_path = package / "template.json"
            import json

            data = json.loads(template_path.read_text(encoding="utf-8"))
            data["strengths"] = {"medium": {"behavior": "deprecated"}}
            template_path.write_text(json.dumps(data), encoding="utf-8")

            with self.assertRaisesRegex(TemplateError, "strengths metadata is no longer supported"):
                load_template("fixture", template_root=root)

    def test_rejects_invalid_required_file_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            invalid_entries = [123, str(root / "absolute.md"), "nested/file.md", ".", ".."]

            for index, entry in enumerate(invalid_entries):
                with self.subTest(entry=entry):
                    template_id = f"fixture-{index}"
                    required_files = list(REQUIRED_PACKAGE_FILES)
                    required_files[1] = entry
                    write_package(root, template_id=template_id, required_files=required_files)

                    with self.assertRaises(TemplateError):
                        load_template(template_id, template_root=root)

    def test_rejects_unknown_required_file_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            required_files = list(REQUIRED_PACKAGE_FILES) + ["extra.md"]
            write_package(root, required_files=required_files)

            with self.assertRaises(TemplateError):
                load_template("fixture", template_root=root)


if __name__ == "__main__":
    unittest.main()
