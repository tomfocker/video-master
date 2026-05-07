import importlib.util
import json
import os
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import ProxyHandler, Request, build_opener

from tests.test_validate_video_project import make_project, write


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "video-master" / "scripts" / "serve_webui.py"
WEBUI = ROOT / "skills" / "video-master" / "webui" / "index.html"
INTRO_BACKGROUND_VIDEO = ROOT / "skills" / "video-master" / "webui" / "assets" / "intro-background-20260427-v2.mp4"
LOCAL_OPENER = build_opener(ProxyHandler({}))


def load_module():
    spec = importlib.util.spec_from_file_location("serve_webui", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def read_json(url: str):
    with LOCAL_OPENER.open(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(url: str, payload: dict):
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with LOCAL_OPENER.open(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


class WebUIServerTest(unittest.TestCase):
    def test_webui_page_is_connected_to_state_apis(self):
        html = WEBUI.read_text(encoding="utf-8")

        self.assertIn("/api/projects", html)
        self.assertIn("/api/project", html)
        self.assertIn("/api/hero-media", html)
        self.assertIn("/api/file", html)
        self.assertIn("/api/auth/codex/status", html)
        self.assertIn("/api/auth/codex/device/start", html)
        self.assertIn("/api/storyboard-image/generate", html)
        self.assertIn("/api/shot-request", html)
        self.assertIn("/api/shot-operation", html)
        self.assertIn("/api/canvas-sync", html)
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
        self.assertIn("frameworkOnly", html)
        self.assertIn("完整制作", html)
        self.assertIn("包装交付", html)
        self.assertIn('value="framework"', html)
        self.assertIn("projectQuickSelect", html)
        self.assertIn("renderProjectQuickSelect", html)
        self.assertIn("handleProjectQuickSelect", html)
        self.assertIn("syncReviewPanel", html)
        self.assertIn("变更清单", html)
        self.assertIn("交给 Codex 处理", html)
        self.assertIn("collectCanvasChangeSummary", html)
        self.assertIn("openCanvasSyncReview", html)
        self.assertIn("confirmCanvasSyncButton", html)
        self.assertIn("selectedEdgeKey", html)
        self.assertIn("selectCanvasEdge", html)
        self.assertIn("deleteSelectedEdge", html)
        self.assertIn(".edge-path.selected", html)
        self.assertIn("data-edge-select", html)
        self.assertIn("handleCanvasKeydown", html)
        self.assertIn("UI_PREFS_KEY", html)
        self.assertIn("loadUiPreferences", html)
        self.assertIn("saveUiPreferences", html)
        self.assertIn("applyUiPreferences", html)
        self.assertIn("video-master-ui-prefs-v1", html)
        self.assertIn("hasZoomPreference", html)
        self.assertIn("captureCanvasBaseline", html)
        self.assertIn("canvasStateFingerprint", html)
        self.assertIn("canvasHasMeaningfulChanges", html)
        self.assertIn("当前还没有检测到新的画布修改", html)
        self.assertIn("同步完成后会把当前画布作为新的对照版本", html)
        self.assertIn("edge-selection-label", html)
        self.assertIn("拖动黄点调整", html)
        self.assertIn("cardDensitySelect", html)
        self.assertIn("setCardDensity", html)
        self.assertIn("density-thumbnail", html)
        self.assertIn("density-standard", html)
        self.assertIn("density-full", html)
        self.assertIn("缩略", html)
        self.assertIn("标准", html)
        self.assertIn("完整", html)
        self.assertIn("查看原图", html)
        self.assertIn("替换图片", html)
        self.assertIn("重生成", html)
        self.assertIn("基于当前图生成变体", html)
        self.assertIn("只重写提示词", html)
        self.assertIn("保留角色/风格锁定后再重写", html)
        self.assertIn("data-shot-operation", html)
        self.assertIn("submitShotOperation", html)
        self.assertIn("openOriginalImage", html)
        self.assertIn("organizeCanvasButton", html)
        self.assertIn("整理画布", html)
        self.assertIn("organizeCanvasLayout", html)
        self.assertIn("layoutPinsKey", html)
        self.assertIn("pinNodeLayout", html)
        self.assertIn("video-master-node-layout-pins-v2", html)
        self.assertIn('["source", "style", "character"]', html)
        self.assertIn("data-pin-node", html)
        self.assertIn("toggleNodePin", html)
        self.assertIn("固定节点", html)
        self.assertIn("avoidPinnedLayoutCollision", html)
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
        self.assertIn("manualEdgeControlKey", html)
        self.assertIn("saveManualEdgeControls", html)
        self.assertIn("saveManualEdge", html)
        self.assertIn("manualEdges", html)
        self.assertIn("connection-preview", html)
        self.assertIn("edge-path.manual", html)
        self.assertIn("edge-control-handle", html)
        self.assertIn("data-edge-control", html)
        self.assertIn("startEdgeControlDrag", html)
        self.assertIn("isAdjustableEdge", html)
        self.assertIn("deleteManualEdge", html)
        self.assertIn("deleteCanvasEdge", html)
        self.assertIn("deletedEdgesKey", html)
        self.assertIn("saveDeletedEdges", html)
        self.assertIn("data-edge-delete", html)
        self.assertIn("edge-delete-button", html)
        self.assertIn("edge-delete-hit", html)
        self.assertIn("edge-delete-icon", html)
        self.assertIn(".edge-delete-button:hover .edge-delete-icon", html)
        self.assertIn(".edge-delete-button {\n      opacity: 0.76;\n      pointer-events: auto;\n      cursor: pointer;\n      transition: opacity 140ms ease;\n    }", html)
        self.assertNotIn(".edge-delete-button:hover {\n      opacity: 1;\n      transform: scale(1.08);\n    }", html)
        self.assertIn("删除连线", html)
        self.assertIn("pointer-events: auto;\n      z-index: 0;", html)
        self.assertIn("function isEdgeDeleteTarget", html)
        self.assertIn("function stopEdgeDeletePointerDown", html)
        self.assertIn("[data-edge-delete], [data-edge-control]", html)
        self.assertIn('els.connectionLayer.addEventListener("pointerdown", stopEdgeDeletePointerDown);', html)
        self.assertIn(".node-layer {\n      position: absolute;\n      inset: 0;\n      z-index: 1;\n      pointer-events: none;", html)
        self.assertIn(".graph-node {\n      position: absolute;\n      pointer-events: auto;", html)
        self.assertIn("edgePathWithControl", html)
        self.assertIn("port-label", html)
        self.assertIn("连接首端", html)
        self.assertIn("连接尾端", html)
        self.assertIn("marker-end", html)
        self.assertNotIn("data-shot-add-after", html)
        self.assertIn("复制图片", html)
        self.assertIn("复制提示词", html)
        self.assertIn("Codex 登录", html)
        self.assertIn("直接生成分镜图", html)
        self.assertIn("generateStoryboardImage", html)
        self.assertIn("data-copy-image", html)
        self.assertIn("data-copy-prompt", html)
        self.assertIn("data-generate-storyboard-image", html)
        self.assertIn("copyShotImage", html)
        self.assertIn("copyShotPrompt", html)
        self.assertIn("ClipboardItem", html)
        self.assertIn("rewrite_prompt", html)
        self.assertIn("replace_image", html)
        self.assertIn("image_variant", html)
        self.assertIn("locked_rewrite", html)
        self.assertIn("regenerate_image", html)
        self.assertIn("syncCanvasButton", html)
        self.assertIn("同步修改", html)
        self.assertIn("collectCanvasSyncState", html)
        self.assertIn("syncCanvasToBackend", html)
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
        self.assertIn("toggleProjectPanelButton", html)
        self.assertIn("project-panel-icon", html)
        self.assertIn("toggleProjectPanel", html)
        self.assertIn("显示项目栏", html)
        self.assertIn("隐藏项目栏", html)
        self.assertIn("canvasModeSelect", html)
        self.assertNotIn('id="toggleFrameworkButton"', html)
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
            previous_auth_file = os.environ.get("VIDEO_MASTER_CODEX_AUTH_FILE")
            os.environ["VIDEO_MASTER_CODEX_AUTH_FILE"] = str(root / "codex_auth.json")
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

                auth = read_json(f"{base_url}/api/auth/codex/status")
                self.assertEqual(auth["provider"], "none")
                self.assertFalse(auth["codex"]["available"])

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
                with LOCAL_OPENER.open(hero_request, timeout=10) as response:
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
                with LOCAL_OPENER.open(
                    f"{base_url}/api/file?{urlencode({'project': str(project), 'path': frame_path})}",
                    timeout=10,
                ) as response:
                    self.assertEqual(response.read(), b"fakepng")

                request = Request(
                    f"{base_url}/api/file?{urlencode({'project': str(project), 'path': frame_path})}",
                    headers={"Range": "bytes=0-3"},
                )
                with LOCAL_OPENER.open(request, timeout=10) as response:
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

                operation = post_json(
                    f"{base_url}/api/shot-operation",
                    {
                        "project": str(project),
                        "shot_id": "S02",
                        "operation": "rewrite_prompt",
                        "note": "只重写当前分镜提示词",
                        "preserve_locks": True,
                        "shot": {"beat": "肌肤近景", "video_prompt": "old prompt"},
                    },
                )
                self.assertTrue(operation["ok"])
                self.assertEqual(operation["request"]["status"], "pending")
                self.assertEqual(operation["request"]["operation"], "rewrite_prompt")
                self.assertEqual(operation["request"]["shot_id"], "S02")
                self.assertTrue(operation["request"]["preserve_locks"])
                operation_file = project / "qa" / "metadata" / "codex_shot_operation_requests.json"
                self.assertTrue(operation_file.is_file())
                operation_requests = json.loads(operation_file.read_text(encoding="utf-8"))
                self.assertEqual(operation_requests[0]["request_id"], operation["request"]["request_id"])
                self.assertEqual(operation_requests[0]["shot"]["beat"], "肌肤近景")

                original_generator = module.generate_storyboard_image_for_project

                def fake_generator(project_path, shot_id, operation="regenerate_image", prompt=None):
                    frame = project_path / "最终交付" / "01_分镜图" / f"{shot_id}.png"
                    frame.parent.mkdir(parents=True, exist_ok=True)
                    frame.write_bytes(b"newpng")
                    return {
                        "job": {
                            "job_id": "image_test",
                            "status": "succeeded",
                            "shot_id": shot_id,
                            "operation": operation,
                        },
                        "asset": {
                            "path": f"最终交付/01_分镜图/{shot_id}.png",
                            "url": "",
                        },
                    }

                module.generate_storyboard_image_for_project = fake_generator
                try:
                    generated = post_json(
                        f"{base_url}/api/storyboard-image/generate",
                        {
                            "project": str(project),
                            "shot_id": "S02",
                            "operation": "regenerate_image",
                        },
                    )
                finally:
                    module.generate_storyboard_image_for_project = original_generator

                self.assertTrue(generated["ok"])
                self.assertEqual(generated["result"]["job"]["status"], "succeeded")
                self.assertEqual(generated["state"]["shots"][1]["frame"]["path"], "最终交付/01_分镜图/S02.png")
                self.assertEqual((project / "最终交付" / "01_分镜图" / "S02.png").read_bytes(), b"newpng")

                synced = post_json(
                    f"{base_url}/api/canvas-sync",
                    {
                        "project": str(project),
                        "note": "重构分镜流程",
                        "canvas_state": {
                            "manual_edges": [["shot_S01", "shot_S03", "manual"]],
                            "deleted_edges": ["shot_S02->shot_S03"],
                            "edge_controls": {"shot_S01->shot_S03": {"x": 720, "y": 240}},
                            "draft_idea": {"idea": "补一个产品微距镜头"},
                        },
                    },
                )
                self.assertTrue(synced["ok"])
                self.assertEqual(synced["request"]["status"], "pending")
                self.assertEqual(synced["request"]["note"], "重构分镜流程")
                self.assertIn("manual_edges", synced["request"]["canvas_state"])
                sync_file = project / "qa" / "metadata" / "codex_canvas_sync_requests.json"
                self.assertTrue(sync_file.is_file())
                sync_requests = json.loads(sync_file.read_text(encoding="utf-8"))
                self.assertEqual(sync_requests[0]["request_id"], synced["request"]["request_id"])
                self.assertEqual(sync_requests[0]["canvas_state"]["deleted_edges"], ["shot_S02->shot_S03"])

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
                if previous_auth_file is None:
                    os.environ.pop("VIDEO_MASTER_CODEX_AUTH_FILE", None)
                else:
                    os.environ["VIDEO_MASTER_CODEX_AUTH_FILE"] = previous_auth_file
                module.HERO_MEDIA_OVERRIDE = None
                server.shutdown()
                server.server_close()
                thread.join(timeout=10)


if __name__ == "__main__":
    unittest.main()
