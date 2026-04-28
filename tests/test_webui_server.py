import importlib.util
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from tests.test_validate_video_project import make_project, write


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "video-master" / "scripts" / "serve_webui.py"
WEBUI = ROOT / "skills" / "video-master" / "webui" / "index.html"
INTRO_BACKGROUND_VIDEO = ROOT / "skills" / "video-master" / "webui" / "assets" / "intro-background-20260427-v2.mp4"


def load_module():
    spec = importlib.util.spec_from_file_location("serve_webui", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def read_json(url: str):
    with urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(url: str, payload: dict):
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


class WebUIServerTest(unittest.TestCase):
    def test_webui_page_is_connected_to_state_apis(self):
        html = WEBUI.read_text(encoding="utf-8")

        self.assertIn("/api/projects", html)
        self.assertIn("/api/project", html)
        self.assertIn("/api/hero-media", html)
        self.assertIn("/api/file", html)
        self.assertIn("/api/shot-request", html)
        self.assertIn("workflow_mode", html)
        self.assertIn("videomaster", html)
        self.assertIn("把想法变成可编辑的影像工作流", html)
        self.assertIn("从分镜图、视频提示词、文字包装到最终交付", html)
        self.assertIn("进入节点编辑器", html)
        self.assertIn("选择项目", html)
        self.assertIn('src="/assets/intro-background-20260427-v2.mp4"', html)
        self.assertIn('INTRO_BACKGROUND_VIDEO = "/assets/intro-background-20260427-v2.mp4"', html)
        self.assertTrue(INTRO_BACKGROUND_VIDEO.is_file())
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
        self.assertIn("文案绑定", html)
        self.assertIn("包装绑定", html)
        self.assertIn("只看框架", html)
        self.assertIn("显示完整", html)
        self.assertIn("frameworkOnly", html)
        self.assertIn("toggleFrameworkOnly", html)
        self.assertIn("storyboard-frame-only", html)
        self.assertIn("renderShotBindings", html)
        self.assertIn("最终交付包", html)
        self.assertIn("画布内编辑", html)
        self.assertIn("新增分镜想法", html)
        self.assertIn("交给 Codex 生成", html)
        self.assertIn("canvasContextMenu", html)
        self.assertIn("openIdeaNodeAt", html)
        self.assertIn("renderIdeaNodeBody", html)
        self.assertIn("submitIdeaToCodex", html)
        self.assertIn("data-idea-submit", html)
        self.assertIn("canvasEdges", html)
        self.assertIn("nearestShotIdForPoint", html)
        self.assertIn("updateIdeaNodeLink", html)
        self.assertIn("data-idea-insert-after", html)
        self.assertIn("idea-link", html)
        self.assertIn("待生成分支", html)
        self.assertIn("data-connect-port", html)
        self.assertIn("flow-port-out", html)
        self.assertIn("flow-port-in", html)
        self.assertIn("startConnectionDrag", html)
        self.assertIn("finishConnectionDrag", html)
        self.assertIn("manualEdgesKey", html)
        self.assertIn("saveManualEdge", html)
        self.assertIn("manualEdges", html)
        self.assertIn("connection-preview", html)
        self.assertIn("edge-path.manual", html)
        self.assertIn("marker-end", html)
        self.assertNotIn("data-shot-add-after", html)
        self.assertIn("复制图片", html)
        self.assertIn("复制提示词", html)
        self.assertIn("data-copy-image", html)
        self.assertIn("data-copy-prompt", html)
        self.assertIn("copyShotImage", html)
        self.assertIn("copyShotPrompt", html)
        self.assertIn("ClipboardItem", html)
        self.assertIn("分镜图提示词种子", html)
        self.assertIn("视频提示词种子", html)
        self.assertIn("openShotEditor", html)
        self.assertIn("saveShotFromCanvas", html)
        self.assertIn("adaptive-shot-media", html)
        self.assertIn("shot-media-top", html)
        self.assertIn("shot-details", html)
        self.assertIn("SHOT_CARD_HEIGHT = 470", html)
        self.assertNotIn("grid-template-columns: minmax(132px, 42%) minmax(0, 1fr)", html)
        self.assertNotIn("aspect-ratio: 9 / 16", html)
        self.assertIn("startCanvasPan", html)
        self.assertIn("startNodeDrag", html)
        self.assertIn("requestNodeDragFrame", html)
        self.assertIn("updateConnectedEdgesDuringDrag", html)
        self.assertIn("edgeElementKey", html)
        self.assertIn("data-edge-key", html)
        self.assertIn("startNodeInertia", html)
        self.assertIn("cancelNodeInertia", html)
        self.assertIn("DRAG_INERTIA_FRICTION", html)
        self.assertIn("translate3d", html)
        self.assertIn(".graph-node.inertia", html)
        self.assertIn("setZoomAt", html)
        self.assertIn("saveNodeLayout", html)
        self.assertIn("loadHeroMedia", html)
        self.assertIn("showIntro", html)
        self.assertIn("character_lock", html)
        self.assertIn("人物形象锁定", html)
        self.assertIn('<div class="app side-hidden inspector-hidden">', html)
        self.assertIn("sideHidden: true", html)
        self.assertIn("inspectorHidden: true", html)
        self.assertIn("canvasModeSelect", html)
        self.assertNotIn('id="toggleSideButton"', html)
        self.assertNotIn('id="toggleInspectorButton"', html)
        self.assertNotIn('id="reloadCanvasButton"', html)
        self.assertNotIn('id="showAllButton"', html)
        self.assertNotIn('id="showShotsButton"', html)
        self.assertNotIn('id="showPackagingButton"', html)
        self.assertNotIn("output_${shot.shot_id}", html)

    def test_server_lists_project_and_serves_frame_file(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = make_project(root, durations=[3, 4, 4, 6, 5, 3, 5])
            write(
                project / "audio" / "voiceover_script.md",
                "# Voiceover\n\n- VO01 (0-3s): 这一刻，光先认出了她。\n",
            )
            write(
                project / "audio" / "music_sfx_cue_sheet.md",
                "# Music SFX\n\n- S01 00:00-00:03: 闪光灯与红毯人群低语。\n",
            )
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
                self.assertEqual(state["copywriting"]["status"], "complete")
                self.assertTrue(state["copywriting"]["files"]["voiceover"]["exists"])
                self.assertTrue(state["copywriting"]["files"]["captions"]["exists"])
                self.assertEqual(state["shot_requests"], [])
                self.assertIn("这一刻", state["shots"][0]["copywriting"]["voiceover"])
                self.assertIn("闪光灯", state["shots"][0]["copywriting"]["sfx"])
                self.assertEqual(state["shots"][0]["packaging"]["role"], "片头标题/主视觉钩子")
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

                queued = post_json(
                    f"{base_url}/api/shot-request",
                    {
                        "project": str(project),
                        "idea": "补一个粉底液滴落到皮肤上的微距镜头。",
                        "x": 620,
                        "y": 480,
                        "insert_after_shot_id": "S02",
                    },
                )
                self.assertTrue(queued["ok"])
                self.assertEqual(queued["request"]["status"], "pending")
                self.assertEqual(queued["request"]["idea"], "补一个粉底液滴落到皮肤上的微距镜头。")
                self.assertEqual(queued["request"]["insert_after_shot_id"], "S02")
                self.assertEqual(queued["request"]["x"], 620)
                self.assertEqual(queued["request"]["y"], 480)
                request_file = project / "qa" / "metadata" / "codex_shot_requests.json"
                self.assertTrue(request_file.is_file())
                queued_requests = json.loads(request_file.read_text(encoding="utf-8"))
                self.assertEqual(queued_requests[0]["request_id"], queued["request"]["request_id"])
                self.assertIn("粉底液滴落", queued["state"]["shot_requests"][0]["idea"])

                updated = post_json(
                    f"{base_url}/api/shot",
                    {
                        "project": str(project),
                        "mode": "update",
                        "shot": {
                            "shot_id": "S01",
                            "beat": "画布改稿",
                            "duration_seconds": 4,
                            "visual_action": "直接在画布卡片中修改画面说明。",
                            "framing": "近景",
                            "camera": "slow dolly in",
                            "movement": "轻微推进",
                            "lighting": "柔和金色边缘光",
                            "image_prompt_seed": "canvas image seed",
                            "video_prompt_seed": "canvas video seed",
                        },
                    },
                )
                self.assertEqual(updated["shot"]["beat"], "画布改稿")
                shots = json.loads((project / "storyboard" / "shot_list.json").read_text(encoding="utf-8"))
                self.assertEqual(shots[0]["beat"], "画布改稿")
                self.assertEqual(shots[0]["duration_seconds"], 4)
                self.assertEqual(shots[0]["image_prompt_seed"], "canvas image seed")
                self.assertEqual(shots[0]["video_prompt_seed"], "canvas video seed")

                added = post_json(
                    f"{base_url}/api/shot",
                    {
                        "project": str(project),
                        "mode": "add",
                        "after_shot_id": "S01",
                        "shot": {
                            "beat": "补充分镜",
                            "duration_seconds": 2,
                            "visual_action": "新加一张过渡分镜。",
                            "video_prompt_seed": "新增分镜的视频动势",
                        },
                    },
                )
                self.assertEqual(added["shot"]["shot_id"], "S08")
                shots = json.loads((project / "storyboard" / "shot_list.json").read_text(encoding="utf-8"))
                self.assertEqual(len(shots), 8)
                self.assertEqual(shots[1]["shot_id"], "S08")
                self.assertEqual(shots[1]["beat"], "补充分镜")
                self.assertEqual(shots[1]["video_prompt_seed"], "新增分镜的视频动势")
            finally:
                module.HERO_MEDIA_OVERRIDE = None
                server.shutdown()
                server.server_close()
                thread.join(timeout=10)


if __name__ == "__main__":
    unittest.main()
