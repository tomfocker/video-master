import importlib.util
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from tests.test_validate_video_project import make_project


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "video-master" / "scripts" / "serve_webui.py"
WEBUI = ROOT / "skills" / "video-master" / "webui" / "index.html"


def load_module():
    spec = importlib.util.spec_from_file_location("serve_webui", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def read_json(url: str):
    with urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


class WebUIServerTest(unittest.TestCase):
    def test_webui_page_is_connected_to_state_apis(self):
        html = WEBUI.read_text(encoding="utf-8")

        self.assertIn("/api/projects", html)
        self.assertIn("/api/project", html)
        self.assertIn("/api/hero-media", html)
        self.assertIn("/api/file", html)
        self.assertIn("workflow_mode", html)
        self.assertIn("videomaster", html)
        self.assertIn("把想法变成可编辑的影像工作流", html)
        self.assertIn("从分镜图、视频提示词、文字包装到最终交付", html)
        self.assertIn("进入节点编辑器", html)
        self.assertIn("选择项目", html)
        self.assertNotIn("AI VIDEO CASE LOOP", html)
        self.assertNotIn("introMediaLabel", html)
        self.assertNotIn("intro-media-label", html)
        self.assertIn("节点式分镜预览编辑器", html)
        self.assertIn("分镜流程", html)
        self.assertIn("分镜制作卡", html)
        self.assertIn("renderShotBody", html)
        self.assertIn("shotGridPosition", html)
        self.assertIn("SHOT_GRID_COLUMNS", html)
        self.assertIn("edgeOrientation", html)
        self.assertIn("最终分镜图", html)
        self.assertIn("视频提示词", html)
        self.assertIn("最终交付包", html)
        self.assertIn("修改草稿", html)
        self.assertIn("隐藏项目库", html)
        self.assertIn("隐藏检查器", html)
        self.assertIn("startCanvasPan", html)
        self.assertIn("startNodeDrag", html)
        self.assertIn("setZoomAt", html)
        self.assertIn("saveNodeLayout", html)
        self.assertIn("loadHeroMedia", html)
        self.assertIn("showIntro", html)
        self.assertIn("character_lock", html)
        self.assertIn("人物形象锁定", html)
        self.assertNotIn("output_${shot.shot_id}", html)

    def test_server_lists_project_and_serves_frame_file(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = make_project(root, durations=[3, 4, 4, 6, 5, 3, 5])
            (project / "preview_demo.mp4").write_bytes(b"fake-video")
            server = ThreadingHTTPServer(("127.0.0.1", 0), module.VideoMasterHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                projects = read_json(f"{base_url}/api/projects?{urlencode({'root': str(root)})}")
                self.assertEqual(len(projects["projects"]), 1)
                self.assertEqual(projects["projects"][0]["name"], "sample_project")

                hero_media = read_json(f"{base_url}/api/hero-media?{urlencode({'root': str(root)})}")
                self.assertEqual(hero_media["kind"], "video")
                self.assertEqual(hero_media["project_name"], "sample_project")
                self.assertIn("/api/file", hero_media["url"])

                module.HERO_MEDIA_OVERRIDE = project / "preview_demo.mp4"
                override_media = read_json(f"{base_url}/api/hero-media?{urlencode({'root': str(root)})}")
                self.assertEqual(override_media["kind"], "video")
                self.assertEqual(override_media["source"], "override")
                self.assertEqual(override_media["url"], "/api/hero-file")

                hero_request = Request(f"{base_url}/api/hero-file", headers={"Range": "bytes=0-3"})
                with urlopen(hero_request, timeout=10) as response:
                    self.assertEqual(response.status, 206)
                    self.assertEqual(response.read(), b"fake")

                state = read_json(f"{base_url}/api/project?{urlencode({'path': str(project), 'write': 'true'})}")
                self.assertEqual(state["project"]["name"], "sample_project")
                self.assertTrue((project / "qa" / "metadata" / "project_state.json").is_file())

                frame_path = state["shots"][0]["frame"]["path"]
                with urlopen(
                    f"{base_url}/api/file?{urlencode({'project': str(project), 'path': frame_path})}",
                    timeout=10,
                ) as response:
                    self.assertEqual(response.read(), b"fakepng")

                request = Request(
                    f"{base_url}/api/file?{urlencode({'project': str(project), 'path': frame_path})}",
                    headers={"Range": "bytes=0-3"},
                )
                with urlopen(request, timeout=10) as response:
                    self.assertEqual(response.status, 206)
                    self.assertEqual(response.read(), b"fake")
            finally:
                module.HERO_MEDIA_OVERRIDE = None
                server.shutdown()
                server.server_close()
                thread.join(timeout=10)


if __name__ == "__main__":
    unittest.main()
