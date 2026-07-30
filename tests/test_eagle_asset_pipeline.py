import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "video-master" / "scripts"
INTAKE = SCRIPTS / "eagle_asset_intake.py"
MCP = SCRIPTS / "eagle_mcp_client.py"
STAGE = SCRIPTS / "ai_animation" / "init_eagle_media_stage.py"
RENDERER = SCRIPTS / "ai_animation" / "render_motion_template.py"
COMPOSER_RENDERER = SCRIPTS / "ai_animation" / "render_composer.py"
PROJECT_ASSETS = SCRIPTS / "eagle_project_assets.py"


def load_module(name: str, path: Path):
    if str(path.parent) not in sys.path:
        sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class EagleMcpClientTest(unittest.TestCase):
    def test_decodes_official_sse_tool_response(self):
        client = load_module("eagle_mcp_client", MCP)
        response = 'event: message\ndata: {"jsonrpc":"2.0","id":1,"result":{"content":[{"type":"text","text":"{\\n  \\"success\\": true, \\"data\\": []\\n}"}]}}\n'
        self.assertEqual(client.decode_tool_result(client.decode_mcp_message(response)), [])


class EagleAssetPipelineTest(unittest.TestCase):
    def write_composer_plan(self, project: Path) -> None:
        composition = project / "animation" / "compositions" / "intro"
        preset = composition / "presets" / "project.json"
        preset.parent.mkdir(parents=True, exist_ok=True)
        (composition / "index.html").write_text("<!doctype html><title>Intro</title>", encoding="utf-8")
        preset.write_text(json.dumps({"exportMode": "mp4"}), encoding="utf-8")
        plan = {
            "schema_version": 2,
            "enabled": True,
            "engine": "hyperframes",
            "execution_mode": "hyperframes",
            "composer": "ai-animation-composer-v1",
            "modules": ["motion-templates"],
            "total_duration_seconds": 4,
            "timeline": [
                {
                    "beat_id": "intro",
                    "composition_id": "intro",
                    "intent": "hook",
                    "template_id": "number-impact",
                    "start_seconds": 0,
                    "end_seconds": 4,
                    "duration_seconds": 4,
                }
            ],
            "compositions": [
                {
                    "id": "intro",
                    "source": "animation/compositions/intro/index.html",
                    "variables_file": "animation/compositions/intro/presets/project.json",
                    "duration_seconds": 4,
                    "aspect_ratio": "16:9",
                    "formats": ["mp4"],
                }
            ],
        }
        path = project / "animation" / "ai_animation_plan.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")

    def test_manifest_record_and_hyperframes_stage_are_created(self):
        intake = load_module("eagle_asset_intake", INTAKE)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            source = root / "hero.png"
            source.write_bytes(b"not-rendered-in-this-test")
            record = intake.item_record(
                {"id": "EAGLE001", "name": "Hero image", "ext": "png", "filePath": str(source)},
                "visual_asset",
                mcp_url="http://127.0.0.1:41596/mcp",
            )
            manifest = intake.new_manifest("http://127.0.0.1:41596/mcp")
            intake.merge_assets(manifest, [record], project=project, copy_files=False)
            manifest_path = project / "sources" / "eagle_assets_manifest.json"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")

            stage = subprocess.run(
                [sys.executable, str(STAGE), str(project), "--asset-id", "EAGLE001", "--title", "Hero"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(stage.returncode, 0, stage.stdout + stage.stderr)
            plan = json.loads((project / "animation" / "ai_animation_plan.json").read_text(encoding="utf-8"))
            composition_id = "eagle-media-eagle001"
            self.assertIn("eagle-media", plan["modules"])
            self.assertEqual(plan["eagle_media"]["stages"][0]["asset_id"], "EAGLE001")
            self.assertTrue((project / "animation" / "compositions" / composition_id / "assets" / "hero.png").is_file())

            render = subprocess.run(
                [sys.executable, str(RENDERER), str(project), "--composition-id", composition_id, "--dry-run"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(render.returncode, 0, render.stdout + render.stderr)
            self.assertIn("hyperframes@0.6.115", render.stdout)

    def test_eagle_stage_can_join_composer_timeline_and_use_manifest_bgm(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            source = root / "hero.png"
            source.write_bytes(b"not-rendered-in-this-test")
            music = project / "sources" / "eagle" / "bgm.wav"
            music.parent.mkdir(parents=True, exist_ok=True)
            music.write_bytes(b"not-decoded-in-dry-run")
            manifest = {
                "schema_version": 1,
                "source": "official-eagle-mcp",
                "assets": [
                    {
                        "id": "EAGLE001",
                        "name": "Hero image",
                        "kind": "image",
                        "ext": "png",
                        "roles": ["visual_asset"],
                        "original_path": str(source),
                    },
                    {
                        "id": "EAGLEBGM1",
                        "name": "Approved BGM",
                        "kind": "audio",
                        "ext": "wav",
                        "roles": ["background_music"],
                        "original_path": str(music),
                        "project_path": "sources/eagle/bgm.wav",
                        "materialization": "copied",
                    },
                ],
            }
            manifest_path = project / "sources" / "eagle_assets_manifest.json"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
            self.write_composer_plan(project)

            stage = subprocess.run(
                [
                    sys.executable,
                    str(STAGE),
                    str(project),
                    "--asset-id",
                    "EAGLE001",
                    "--duration-seconds",
                    "6",
                    "--append-to-composer",
                    "--insert-after",
                    "intro",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(stage.returncode, 0, stage.stdout + stage.stderr)
            plan = json.loads((project / "animation" / "ai_animation_plan.json").read_text(encoding="utf-8"))
            self.assertEqual([item["composition_id"] for item in plan["timeline"]], ["intro", "eagle-media-eagle001"])
            self.assertEqual(plan["timeline"][1]["start_seconds"], 4.0)
            self.assertEqual(plan["timeline"][1]["end_seconds"], 10.0)
            self.assertEqual(plan["total_duration_seconds"], 10.0)

            render = subprocess.run(
                [
                    sys.executable,
                    str(COMPOSER_RENDERER),
                    str(project),
                    "--eagle-background-music-id",
                    "EAGLEBGM1",
                    "--dry-run",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(render.returncode, 0, render.stdout + render.stderr)
            self.assertIn("-stream_loop", render.stdout)
            self.assertIn(music.name, render.stdout)

    def test_resolves_approved_manifest_bgm_for_renderers(self):
        project_assets = load_module("eagle_project_assets", PROJECT_ASSETS)
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "project"
            music = project / "sources" / "eagle" / "approved.wav"
            music.parent.mkdir(parents=True, exist_ok=True)
            music.write_bytes(b"audio-placeholder")
            manifest = {
                "schema_version": 1,
                "source": "official-eagle-mcp",
                "assets": [
                    {
                        "id": "EAGLEBGM1",
                        "name": "Approved BGM",
                        "kind": "audio",
                        "ext": "wav",
                        "roles": ["background_music"],
                        "original_path": str(music),
                        "project_path": "sources/eagle/approved.wav",
                        "materialization": "copied",
                    }
                ],
            }
            manifest_path = project / "sources" / "eagle_assets_manifest.json"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
            resolved = project_assets.resolve_eagle_audio_asset(project, item_id="EAGLEBGM1")
            self.assertIsNotNone(resolved)
            assert resolved is not None
            self.assertEqual(resolved[0], music.resolve())
            self.assertEqual(resolved[1]["type"], "eagle_manifest")
            self.assertEqual(resolved[1]["item_id"], "EAGLEBGM1")


if __name__ == "__main__":
    unittest.main()
