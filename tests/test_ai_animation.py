import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "video-master"
CATALOG = SKILL / "ai_animation" / "typography" / "catalog.json"
RUNTIME = SKILL / "ai_animation" / "typography" / "runtime" / "text-effects-runtime.js"
CATALOG_JS = SKILL / "ai_animation" / "typography" / "runtime" / "text-effects-catalog.js"
MOTION_CATALOG = SKILL / "ai_animation" / "motion_templates" / "catalog.json"
MOTION_SOURCE = SKILL / "ai_animation" / "motion_templates" / "source.json"
MOTION_NOTICE = SKILL / "ai_animation" / "motion_templates" / "UPSTREAM_NOTICE.md"
BUILD = SKILL / "scripts" / "ai_animation" / "build_assets.py"
LIBRARY_VALIDATOR = SKILL / "scripts" / "ai_animation" / "validate_library.py"
PROJECT_VALIDATOR = SKILL / "scripts" / "validate_video_project.py"
INITIALIZER = SKILL / "scripts" / "ai_animation" / "init_project.py"
MOTION_INITIALIZER = SKILL / "scripts" / "ai_animation" / "init_motion_template.py"
MOTION_RENDERER = SKILL / "scripts" / "ai_animation" / "render_motion_template.py"


def load_project_validator():
    scripts_dir = str(PROJECT_VALIDATOR.parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("video_master_project_validator", PROJECT_VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class AiAnimationLibraryTest(unittest.TestCase):
    def test_catalog_is_curated_and_unique(self):
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        effects = catalog["effects"]
        self.assertEqual(len(effects), 12)
        self.assertEqual(len({item["id"] for item in effects}), len(effects))
        self.assertTrue(all(item["cjk_safe"] is True for item in effects))
        self.assertTrue(all(item["frames"][0]["offset"] == 0 for item in effects))
        self.assertTrue(all(item["frames"][-1]["offset"] == 1 for item in effects))

    def test_generated_catalog_and_library_are_valid(self):
        build = subprocess.run(
            [sys.executable, str(BUILD), "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
        validate = subprocess.run(
            [sys.executable, str(LIBRARY_VALIDATOR)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(validate.returncode, 0, validate.stdout + validate.stderr)

    def test_runtime_javascript_parses(self):
        for path in [RUNTIME, CATALOG_JS]:
            result = subprocess.run(
                ["node", "--check", str(path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_motion_template_catalog_is_pinned_and_complete(self):
        catalog = json.loads(MOTION_CATALOG.read_text(encoding="utf-8"))
        source = json.loads(MOTION_SOURCE.read_text(encoding="utf-8"))
        templates = catalog["templates"]
        self.assertEqual(len(templates), 20)
        self.assertEqual(len({item["id"] for item in templates}), 20)
        self.assertEqual(source["template_count"], 20)
        self.assertEqual(source["commit"], "01c393f9f26b5b0d8432fa02682ceb36f6cc3e0f")
        self.assertFalse(source["license_file_present_at_import"])
        self.assertIn("栗噔噔", MOTION_NOTICE.read_text(encoding="utf-8"))
        for item in templates:
            template = SKILL / "ai_animation" / "motion_templates" / item["path"]
            self.assertTrue((template / "index.html").is_file())
            self.assertTrue((template / "presets" / "default.json").is_file())

    def test_motion_initializer_registers_selected_template(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "demo"
            variables = Path(directory) / "variables.json"
            variables.write_text(json.dumps({"term": "视觉注意力", "accent": "#FF7A3D"}), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(MOTION_INITIALIZER),
                    str(project),
                    "--template-id",
                    "concept-spotlight",
                    "--variables",
                    str(variables),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            plan = json.loads((project / "animation" / "ai_animation_plan.json").read_text(encoding="utf-8"))
            selected = plan["motion_templates"]["templates"][0]
            self.assertIn("motion-templates", plan["modules"])
            self.assertEqual(selected["template_id"], "concept-spotlight")
            preset = json.loads(
                (project / "animation" / "compositions" / "concept-spotlight" / "presets" / "project.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(preset["term"], "视觉注意力")
            self.assertEqual(preset["exportMode"], "transparent")
            self.assertTrue(
                (project / "animation" / "compositions" / "concept-spotlight" / "UPSTREAM_NOTICE.md").is_file()
            )
            render = subprocess.run(
                [
                    sys.executable,
                    str(MOTION_RENDERER),
                    str(project),
                    "--composition-id",
                    "concept-spotlight",
                    "--format",
                    "webm",
                    "--dry-run",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(render.returncode, 0, render.stdout + render.stderr)
            render_plan = json.loads(render.stdout)
            self.assertIn("hyperframes@0.6.115", render_plan["command"])
            self.assertIn('"exportMode":"transparent"', " ".join(render_plan["command"]))

    def test_initializer_creates_reusable_project_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "demo"
            result = subprocess.run(
                [
                    sys.executable,
                    str(INITIALIZER),
                    str(project),
                    "--effect-id",
                    "wipe-reveal",
                    "--text",
                    "第一步：找到关键变量",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            plan = json.loads((project / "animation" / "ai_animation_plan.json").read_text(encoding="utf-8"))
            self.assertEqual(plan["typography"]["effects"][0]["effect_id"], "wipe-reveal")
            self.assertTrue((project / "animation" / "runtime" / "text-effects-runtime.js").is_file())
            composition = project / "animation" / "index.html"
            self.assertIn("VideoMasterTextEffects.play", composition.read_text(encoding="utf-8"))


class AiAnimationProjectContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = load_project_validator()

    def make_project(self, root: Path, effect_id: str = "focus-blur-rise") -> Path:
        project = root / "project"
        source = project / "animation" / "compositions" / "main.html"
        output = project / "最终交付" / "08_ai_animation" / "main.mp4"
        source.parent.mkdir(parents=True, exist_ok=True)
        output.parent.mkdir(parents=True, exist_ok=True)
        (project / "qa" / "metadata").mkdir(parents=True, exist_ok=True)
        source.write_text("<!doctype html><title>AI animation</title>", encoding="utf-8")
        output.write_bytes(b"video")
        plan = {
            "schema_version": 1,
            "enabled": True,
            "engine": "hyperframes",
            "execution_mode": "hyperframes",
            "modules": ["typography"],
            "typography": {
                "effects": [
                    {
                        "element_id": "main_title",
                        "effect_id": effect_id,
                        "text_source": "script/script.md",
                        "start_ms": 0,
                        "duration_ms": 900,
                    }
                ]
            },
            "compositions": [
                {
                    "id": "main",
                    "source": "animation/compositions/main.html",
                    "duration_seconds": 6,
                    "aspect_ratio": "16:9",
                }
            ],
        }
        (project / "animation" / "ai_animation_plan.json").write_text(
            json.dumps(plan, ensure_ascii=False), encoding="utf-8"
        )
        manifest = {
            "ai_animation": True,
            "engine": "hyperframes",
            "plan": "animation/ai_animation_plan.json",
            "compositions": [
                {
                    "id": "main",
                    "source": "animation/compositions/main.html",
                    "output": "最终交付/08_ai_animation/main.mp4",
                }
            ],
        }
        (project / "qa" / "metadata" / "ai_animation_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
        )
        return project

    def test_valid_project_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.make_project(Path(directory))
            errors = []
            self.validator.validate_ai_animation(project, {"ai_animation_enabled": "true"}, errors)
            self.assertEqual(errors, [])

    def test_unknown_effect_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.make_project(Path(directory), effect_id="not-in-catalog")
            errors = []
            self.validator.validate_ai_animation(project, {"ai_animation_enabled": "true"}, errors)
            self.assertIn("unknown AI animation typography effect: not-in-catalog", errors)

    def make_motion_project(self, root: Path, template_id: str = "concept-spotlight") -> Path:
        project = root / "motion-project"
        source = project / "animation" / "compositions" / "concept" / "index.html"
        variables = project / "animation" / "compositions" / "concept" / "presets" / "project.json"
        output = project / "最终交付" / "08_ai_animation" / "concept.webm"
        source.parent.mkdir(parents=True, exist_ok=True)
        variables.parent.mkdir(parents=True, exist_ok=True)
        output.parent.mkdir(parents=True, exist_ok=True)
        (project / "qa" / "metadata").mkdir(parents=True, exist_ok=True)
        source.write_text("<!doctype html><title>Motion template</title>", encoding="utf-8")
        variables.write_text(json.dumps({"exportMode": "transparent"}), encoding="utf-8")
        output.write_bytes(b"video")
        plan = {
            "schema_version": 1,
            "enabled": True,
            "engine": "hyperframes",
            "execution_mode": "hybrid",
            "modules": ["motion-templates"],
            "motion_templates": {
                "templates": [
                    {
                        "composition_id": "concept",
                        "template_id": template_id,
                        "variables_file": "animation/compositions/concept/presets/project.json",
                    }
                ]
            },
            "compositions": [
                {
                    "id": "concept",
                    "source": "animation/compositions/concept/index.html",
                    "duration_seconds": 5,
                    "aspect_ratio": "16:9",
                }
            ],
        }
        (project / "animation" / "ai_animation_plan.json").write_text(
            json.dumps(plan, ensure_ascii=False), encoding="utf-8"
        )
        manifest = {
            "ai_animation": True,
            "engine": "hyperframes",
            "plan": "animation/ai_animation_plan.json",
            "compositions": [
                {
                    "id": "concept",
                    "source": "animation/compositions/concept/index.html",
                    "output": "最终交付/08_ai_animation/concept.webm",
                }
            ],
        }
        (project / "qa" / "metadata" / "ai_animation_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
        )
        return project

    def test_valid_motion_template_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.make_motion_project(Path(directory))
            errors = []
            self.validator.validate_ai_animation(project, {"ai_animation_enabled": "true"}, errors)
            self.assertEqual(errors, [])

    def test_unknown_motion_template_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            project = self.make_motion_project(Path(directory), template_id="not-in-catalog")
            errors = []
            self.validator.validate_ai_animation(project, {"ai_animation_enabled": "true"}, errors)
            self.assertIn("unknown AI animation motion template: not-in-catalog", errors)


if __name__ == "__main__":
    unittest.main()
