import base64
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

from tests.test_validate_video_project import make_project


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "video-master" / "scripts" / "codex_image_generation.py"


def load_module():
    spec = importlib.util.spec_from_file_location("codex_image_generation", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


PNG_1X1 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8"
    "/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
)


class CodexImageGenerationTest(unittest.TestCase):
    def test_codex_responses_payload_forces_high_quality_image_generation_tool(self):
        module = load_module()

        payload = module.create_codex_responses_request_body(
            prompt="电影感武侠分镜，雨夜屋檐，两位高手对峙。",
            size="1920x1088",
            quality="high",
            output_format="png",
            image_model="gpt-image-2",
            orchestrator_model="gpt-5.4",
        )

        self.assertEqual(payload["model"], "gpt-5.4")
        self.assertEqual(payload["store"], False)
        self.assertEqual(payload["stream"], True)
        self.assertEqual(payload["tools"][0]["type"], "image_generation")
        self.assertEqual(payload["tools"][0]["model"], "gpt-image-2")
        self.assertEqual(payload["tools"][0]["size"], "1920x1088")
        self.assertEqual(payload["tools"][0]["quality"], "high")
        self.assertEqual(payload["tools"][0]["output_format"], "png")
        self.assertEqual(payload["tools"][0]["partial_images"], 0)
        self.assertIn("电影感武侠分镜", payload["input"][0]["content"][0]["text"])

    def test_extracts_image_base64_from_codex_stream_events(self):
        module = load_module()
        image_base64 = base64.b64encode(b"fake-image").decode("ascii")
        sse = (
            "data: "
            + json.dumps(
                {
                    "type": "response.output_item.done",
                    "item": {"type": "image_generation_call", "result": image_base64},
                }
            )
            + "\n\n"
        )

        events = module.parse_codex_responses_events_from_sse(sse)
        self.assertEqual(module.extract_codex_image_base64_from_response_events(events), [image_base64])

    def test_codex_device_login_sends_user_agent_header(self):
        module = load_module()
        captured = {}

        class FakeResponse:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self):
                return json.dumps(
                    {
                        "device_auth_id": "deviceauth_test",
                        "user_code": "ABCD-1234",
                        "interval": "5",
                        "expires_in": 900,
                    }
                ).encode("utf-8")

        def fake_urlopen(request, timeout=30):
            captured["headers"] = dict(request.header_items())
            captured["timeout"] = timeout
            return FakeResponse()

        original_urlopen = module.urlopen
        module.urlopen = fake_urlopen
        try:
            response = module.start_codex_device_login()
        finally:
            module.urlopen = original_urlopen

        self.assertEqual(response["deviceAuthId"], "deviceauth_test")
        self.assertIn("User-agent", captured["headers"])
        self.assertIn("video-master", captured["headers"]["User-agent"])

    def test_project_image_size_uses_video_aspect_ratio(self):
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(Path(tmp), durations=[3], extra_spec_lines=["- aspect_ratio: 16:9"])

            self.assertEqual(module.storyboard_size_for_project(project), (1920, 1088))

    def test_saves_storyboard_image_and_manifest_in_project_outputs(self):
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(Path(tmp), durations=[3])
            result = module.save_storyboard_image_result(
                project=project,
                shot_id="S01",
                prompt="电影感分镜图",
                image_base64=PNG_1X1,
                model="gpt-image-2",
                size="1088x1920",
                quality="high",
                output_format="png",
                operation="regenerate_image",
            )

            frame_path = project / "最终交付" / "01_分镜图" / "S01.png"
            manifest_path = project / "qa" / "metadata" / "image_generation_manifest.json"
            self.assertTrue(frame_path.is_file())
            self.assertEqual(frame_path.read_bytes(), base64.b64decode(PNG_1X1))
            self.assertEqual(result["asset"]["path"], "最终交付/01_分镜图/S01.png")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["shots"]["S01"]["status"], "succeeded")
            self.assertEqual(manifest["shots"]["S01"]["operation"], "regenerate_image")
            self.assertEqual(manifest["shots"]["S01"]["model"], "gpt-image-2")

    def test_auth_store_path_can_be_redirected_outside_the_repo(self):
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            auth_path = Path(tmp) / "auth.json"
            previous = os.environ.get("VIDEO_MASTER_CODEX_AUTH_FILE")
            os.environ["VIDEO_MASTER_CODEX_AUTH_FILE"] = str(auth_path)
            try:
                self.assertEqual(module.codex_auth_file(), auth_path)
            finally:
                if previous is None:
                    os.environ.pop("VIDEO_MASTER_CODEX_AUTH_FILE", None)
                else:
                    os.environ["VIDEO_MASTER_CODEX_AUTH_FILE"] = previous


if __name__ == "__main__":
    unittest.main()
