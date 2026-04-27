import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "skills" / "video-master" / "scripts" / "validate_video_project.py"
REQUIRED_TEMPLATE_FILES = [
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


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def seconds_label(value) -> str:
    return f"{float(value):05.1f}".rstrip("0").rstrip(".")


def write_template_package(root: Path, template_id="draft-template", status="draft") -> Path:
    package = root / template_id
    package.mkdir(parents=True, exist_ok=True)
    for filename in REQUIRED_TEMPLATE_FILES:
        write(package / filename, "{}\n" if filename.endswith(".json") else "# Fixture\n")
    write(
        package / "template.json",
        json.dumps(
            {
                "id": template_id,
                "display_name": "Draft Fixture",
                "status": status,
                "version": "0.1.0",
                "updated_at": "2026-04-26",
                "tags": ["fixture"],
                "best_for": ["fixture"],
                "not_for": ["fixture"],
                "supported_video_modes": ["fast-paced-tvc"],
                "supported_aspect_ratios": ["9:16"],
                "duration_range_seconds": {"min": 1, "max": 120},
                "user_override_policy": ["User project ideas override template defaults."],
                "visual_rules": ["visual"],
                "rhythm_rules": ["rhythm"],
                "camera_rules": ["camera"],
                "sound_rules": ["sound"],
                "storyboard_prompt_rules": ["storyboard"],
                "video_prompt_rules": ["video"],
                "safety_boundaries": ["safety"],
                "required_files": REQUIRED_TEMPLATE_FILES,
            },
            ensure_ascii=False,
        ),
    )
    return package


def make_project(
    base: Path,
    *,
    durations,
    prompt_language="zh-CN",
    with_deliverables=True,
    with_audio=True,
    extra_spec_lines=None,
    shot_overrides=None,
    rhythm_map_content="# Rhythm Map\n",
    final_video_prompt_content=None,
) -> Path:
    project = base / "sample_project"
    for directory in [
        "brief",
        "strategy",
        "script",
        "storyboard/frames",
        "prompts",
        "audio",
        "最终交付/01_分镜图",
        "最终交付/02_提示词",
        "最终交付/03_口播与字幕",
        "最终交付/04_分镜总览",
        "最终交付/05_预览视频",
        "最终交付/06_制作总表",
        "qa/metadata",
    ]:
        (project / directory).mkdir(parents=True, exist_ok=True)

    write(project / "brief" / "creative_brief.md", "# Creative Brief\n")
    spec_lines = [
        "# Spec Lock",
        "",
        "## format",
        "- aspect_ratio: 9:16",
        "- target_duration_seconds: 30",
        "- target_platform: 小红书",
        f"- prompt_language: {prompt_language}",
        "- prompt_dialect: domestic-cn",
        "",
        "## production_mode",
        "- input_mode: idea-only",
        "- video_mode: fast-paced-tvc",
        "",
        "## audio",
        "- copy_language: zh-CN",
        "- voiceover_language: zh-CN",
        "- caption_language: zh-CN",
        "- localized_caption_languages: zh-CN",
        "- subtitle_rendering_policy: post-production-only",
        "- burned_subtitles_allowed: false",
    ]
    if extra_spec_lines:
        spec_lines.extend(extra_spec_lines)
    write(
        project / "brief" / "spec_lock.md",
        "\n".join(spec_lines),
    )
    write(project / "strategy" / "input_readiness.md", "# Input Readiness\n")
    write(project / "strategy" / "video_mode.md", "# Video Mode\n")
    write(project / "strategy" / "creative_strategy.md", "# Creative Strategy\n")
    write(project / "strategy" / "rhythm_map.md", rhythm_map_content)
    write(project / "script" / "script.md", "# Script\n")
    write(project / "storyboard" / "shot_list.md", "# Shot List\n")
    write(project / "storyboard" / "storyboard_manifest.md", "# Manifest\n")
    write(project / "prompts" / "storyboard_image_prompts.md", "# Image Prompts\n")
    write(
        project / "prompts" / "video_prompts.md",
        "# Video Prompts\n\n## S01\n- 画面提示词：清晨护肤广告\n- 运动提示词：镜头缓慢推进\n",
    )

    shots = []
    start = 0
    shot_overrides = shot_overrides or {}
    for index, duration in enumerate(durations, start=1):
        end = start + duration
        shot_id = f"S{index:02d}"
        shot = {
            "shot_id": shot_id,
            "start": f"00:{seconds_label(start)}",
            "end": f"00:{seconds_label(end)}",
            "duration_seconds": duration,
            "beat": "测试",
        }
        shot.update(shot_overrides.get(shot_id, {}))
        shots.append(shot)
        (project / "storyboard" / "frames" / f"{shot_id}.png").write_bytes(b"fakepng")
        start = end
    write(project / "storyboard" / "shot_list.json", json.dumps(shots, ensure_ascii=False))

    if with_audio:
        write(project / "audio" / "voiceover_script.md", "# Voiceover\n")
        write(project / "audio" / "tts_lines.json", json.dumps([{"id": "VO01", "text": "测试"}], ensure_ascii=False))
        write(project / "audio" / "captions.srt", "1\n00:00:00,000 --> 00:00:02,000\n测试\n")
        write(project / "audio" / "captions_zh.srt", "1\n00:00:00,000 --> 00:00:02,000\n测试\n")
        write(project / "audio" / "music_sfx_cue_sheet.md", "# Music SFX\n")
        write(project / "audio" / "audio_generation_prompt.md", "# Audio Prompt\n")

    if with_deliverables:
        write(project / "最终交付" / "00_使用说明.md", "# Handoff\n")
        write(project / "qa" / "metadata" / "storyboard_overview.html", "<!doctype html><title>Storyboard Overview</title>\n")
        (project / "最终交付" / "04_分镜总览" / "分镜总览图.png").write_bytes(b"fakepng")
        (project / "最终交付" / "06_制作总表" / "制作总表.xlsx").write_bytes(b"fakexlsx")
        (project / "最终交付" / "05_预览视频" / "分镜预览.mp4").write_bytes(b"fakemp4")
        write(
            project / "qa" / "metadata" / "preview_manifest.json",
            json.dumps(
                {
                    "title": "测试项目",
                    "preview_profile": "draft",
                    "output": "最终交付/05_预览视频/分镜预览.mp4",
                    "shot_count": len(durations),
                    "skipped": False,
                    "title_card": True,
                    "end_card": True,
                    "shot_overlays": True,
                    "burned_captions": True,
                    "ken_burns_motion": False,
                    "motion_style": "none",
                    "voiceover_audio": False,
                },
                ensure_ascii=False,
            ),
        )
        if final_video_prompt_content is None:
            final_video_prompt_content = (
                "# Copy Ready\n\n"
                "## S01\n"
                "目标模型：Seedance 2.0\n"
                "动态时间切片：\n"
                "(00-1.5s): 镜头缓慢推近，清晨光线掠过产品表面，主体动作自然连续。\n"
                "(1.5-3.0s): 镜头继续稳定推进，手部轻轻拿起产品，反射光保持平滑。\n"
                "稳定性要求：主体稳定、产品造型稳定、无闪烁、无重影。\n"
                "声音/口播：外部画外音，后期添加；本片段不生成对白或口播台词。\n"
                "背景音乐：不要生成背景音乐；整片音乐后期统一处理。\n"
                "SFX音效：清晨环境声、衣料摩擦声。\n"
                "画面文字策略：无；字幕使用SRT后期添加，模型生成画面不添加字幕。\n"
            )
        write(project / "最终交付" / "02_提示词" / "视频生成提示词.md", final_video_prompt_content)
        write(project / "最终交付" / "02_提示词" / "图片生成提示词.md", "# Copy Ready\n")
        write(project / "最终交付" / "03_口播与字幕" / "口播稿.md", "# Final VO\n")
        write(project / "最终交付" / "03_口播与字幕" / "中文字幕.srt", "1\n00:00:00,000 --> 00:00:02,000\n测试\n")
        for index in range(1, len(durations) + 1):
            (project / "最终交付" / "01_分镜图" / f"S{index:02d}.png").write_bytes(b"fakepng")

    return project


class ValidateVideoProjectTest(unittest.TestCase):
    def run_validator(self, project: Path, env=None):
        subprocess_env = os.environ.copy()
        subprocess_env.pop("VIDEO_MASTER_STYLE_TEMPLATE_ROOT", None)
        if env:
            subprocess_env.update(env)
        return subprocess.run(
            [sys.executable, str(VALIDATOR), str(project)],
            cwd=ROOT,
            env=subprocess_env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_rejects_even_timing_for_fast_paced_ad(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(Path(tmp), durations=[5, 5, 5, 5, 5, 5])
            result = self.run_validator(project)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("shot durations are too uniform", result.stdout + result.stderr)

    def test_accepts_v2_project_with_chinese_delivery_audio_and_chinese_prompts(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(Path(tmp), durations=[3, 4, 4, 6, 5, 3, 5])
            result = self.run_validator(project)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("OK", result.stdout)

    def test_rejects_high_motion_project_without_rapid_cut_cluster_or_impact_camera(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(
                Path(tmp),
                durations=[4, 5, 6, 7, 8],
                extra_spec_lines=["- pacing_style: 高速赛车，要求高速快切和车载冲击感"],
            )
            result = self.run_validator(project)
            self.assertNotEqual(result.returncode, 0)
            combined = result.stdout + result.stderr
            self.assertIn("high-motion pacing requires at least one rapid-cut cluster", combined)
            self.assertIn("high-motion pacing requires impact camera language", combined)

    def test_accepts_high_motion_project_with_rapid_cut_cluster_and_impact_camera(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(
                Path(tmp),
                durations=[6, 1, 1, 1.5, 4.5, 7, 4, 5],
                extra_spec_lines=["- pacing_style: 高速赛车，要求高速快切和车载冲击感"],
                shot_overrides={
                    "S02": {"movement": "高速快切，车载震动，轻微手持抖动"},
                    "S03": {"movement": "冲击式推近，头盔视角晃动"},
                    "S04": {"movement": "轮胎掠过，短促甩镜"},
                },
            )
            result = self.run_validator(project)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_deprecated_template_strength_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(
                Path(tmp),
                durations=[3, 4, 4, 6, 5, 3, 5],
                extra_spec_lines=[
                    "- style_route: use_style_template",
                    "- template_id: cinematic-flow-racing",
                    "- template_strength: medium",
                ],
                rhythm_map_content=(
                    "# Rhythm Map\n\n"
                    "- template_id: cinematic-flow-racing\n"
                    "- template_application: 套用完整模板方法，并按用户项目重写主体。\n"
                ),
            )
            result = self.run_validator(project)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("template_strength is no longer supported", result.stdout + result.stderr)

    def test_rejects_style_template_route_without_template_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(
                Path(tmp),
                durations=[3, 4, 4, 6, 5, 3, 5],
                extra_spec_lines=["- style_route: use_style_template"],
            )
            result = self.run_validator(project)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "template_id is required when style_route is use_style_template",
                result.stdout + result.stderr,
            )

    def test_rejects_unknown_template_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(
                Path(tmp),
                durations=[3, 4, 4, 6, 5, 3, 5],
                extra_spec_lines=[
                    "- style_route: use_style_template",
                    "- template_id: missing-template",
                ],
            )
            result = self.run_validator(project)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("template not found", result.stdout + result.stderr)

    def test_rejects_template_project_without_rhythm_trace(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(
                Path(tmp),
                durations=[6, 1, 1, 1.2, 5, 5, 5, 5.8],
                extra_spec_lines=[
                    "- style_route: use_style_template",
                    "- template_id: cinematic-flow-racing",
                ],
                shot_overrides={
                    "S02": {"movement": "车载震动，快切冲击"},
                    "S03": {"movement": "POV 晃动，硬切"},
                    "S04": {"movement": "甩镜，仪表红灯闪烁"},
                },
            )
            result = self.run_validator(project)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("rhythm_map must name selected template", result.stdout + result.stderr)

    def test_rejects_cinematic_flow_racing_prompt_with_only_abstract_style_term(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(
                Path(tmp),
                durations=[6, 1, 1, 1.2, 5, 5, 5, 5.8],
                extra_spec_lines=[
                    "- style_route: use_style_template",
                    "- template_id: cinematic-flow-racing",
                ],
                rhythm_map_content=(
                    "# Rhythm Map\n\n"
                    "- template_id: cinematic-flow-racing\n"
                    "- template_application: 套用完整心流结构，并按用户项目重写主体。\n"
                ),
                shot_overrides={
                    "S02": {"movement": "车载震动，快切冲击"},
                    "S03": {"movement": "POV 晃动，硬切"},
                    "S04": {"movement": "甩镜，仪表红灯闪烁"},
                },
                final_video_prompt_content=(
                    "# Copy Ready\n\n"
                    "## S01\n"
                    "画面：进入心流状态，情绪沉静。\n"
                    "声音/口播：外部画外音，后期添加；本片段不生成对白或口播台词。\n"
                    "背景音乐：不要生成背景音乐；整片音乐后期统一处理。\n"
                    "SFX音效：远处发动机低频、雨滴敲击、呼吸声。\n"
                    "画面文字策略：无；不要生成字幕、caption、对白文字或烧录文字，字幕使用 SRT 后期添加。\n"
                ),
            )
            result = self.run_validator(project)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "cinematic-flow-racing prompts must carry the template visual language",
                result.stdout + result.stderr,
            )

    def test_accepts_project_with_official_template_trace(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(
                Path(tmp),
                durations=[6, 1, 1, 1.2, 5, 5, 5, 5.8],
                extra_spec_lines=[
                    "- style_route: use_style_template",
                    "- template_id: cinematic-flow-racing",
                ],
                rhythm_map_content=(
                    "# Rhythm Map\n\n"
                    "- template_id: cinematic-flow-racing\n"
                    "- template_application: 套用完整模板方法：现实压迫、快切压力组、暴风眼和超现实心流结构；用户具体主题优先。\n"
                ),
                shot_overrides={
                    "S02": {"movement": "车载震动，快切冲击"},
                    "S03": {"movement": "POV 晃动，硬切"},
                    "S04": {"movement": "甩镜，仪表红灯闪烁"},
                },
                final_video_prompt_content=(
                    "# Copy Ready\n\n"
                    "## S01\n"
                    "目标模型：Seedance 2.0\n"
                    "画面：低饱和黑白高反差，湿润银色高光，人物处在巨大负空间中。\n"
                    "动态时间切片：\n"
                    "(00-1.5s): 镜头缓慢推近，湿润银色高光沿着人物轮廓移动，人物呼吸和眼神保持克制。\n"
                    "(1.5-3.0s): 手持压迫感轻微增强，背景负空间维持稳定，雨滴和反射光自然流动。\n"
                    "稳定性要求：主体稳定、人体结构正常、服装一致、无闪烁、无重影。\n"
                    "声音/口播：外部画外音，后期添加；本片段不生成对白或口播台词。\n"
                    "背景音乐：不要生成背景音乐；整片音乐后期统一处理。\n"
                    "SFX音效：远处发动机低频、雨滴敲击、呼吸声。\n"
                    "画面文字策略：无；不要生成字幕、caption、对白文字或烧录文字，字幕使用 SRT 后期添加。\n"
                ),
            )
            result = self.run_validator(project)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_draft_template_without_allow_draft_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template_root = root / "templates"
            write_template_package(template_root)
            project = make_project(
                root,
                durations=[3, 4, 4, 6, 5, 3, 5],
                extra_spec_lines=[
                    "- style_route: use_style_template",
                    "- template_id: draft-template",
                ],
                rhythm_map_content=(
                    "# Rhythm Map\n\n"
                    "- template_id: draft-template\n"
                ),
            )
            result = self.run_validator(
                project,
                env={"VIDEO_MASTER_STYLE_TEMPLATE_ROOT": str(template_root)},
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "draft template requires allow_draft_template: true: draft-template",
                result.stdout + result.stderr,
            )

    def test_accepts_draft_template_with_allow_draft_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template_root = root / "templates"
            write_template_package(template_root)
            project = make_project(
                root,
                durations=[3, 4, 4, 6, 5, 3, 5],
                extra_spec_lines=[
                    "- style_route: use_style_template",
                    "- template_id: draft-template",
                    "- allow_draft_template: true",
                ],
                rhythm_map_content=(
                    "# Rhythm Map\n\n"
                    "- template_id: draft-template\n"
                ),
            )
            result = self.run_validator(
                project,
                env={"VIDEO_MASTER_STYLE_TEMPLATE_ROOT": str(template_root)},
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_missing_audio_and_deliverables(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(
                Path(tmp),
                durations=[3, 4, 4, 6, 5, 3, 5],
                with_audio=False,
                with_deliverables=False,
            )
            result = self.run_validator(project)
            self.assertNotEqual(result.returncode, 0)
            combined = result.stdout + result.stderr
            self.assertIn("missing required file: audio/voiceover_script.md", combined)
            self.assertIn("missing required file: 最终交付/00_使用说明.md", combined)

    def test_rejects_missing_storyboard_overview(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(Path(tmp), durations=[3, 4, 4, 6, 5, 3, 5])
            (project / "最终交付" / "04_分镜总览" / "分镜总览图.png").unlink()
            result = self.run_validator(project)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing storyboard overview", result.stdout + result.stderr)

    def test_rejects_missing_preview_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(Path(tmp), durations=[3, 4, 4, 6, 5, 3, 5])
            (project / "qa" / "metadata" / "preview_manifest.json").unlink()
            result = self.run_validator(project)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing required file: qa/metadata/preview_manifest.json", result.stdout + result.stderr)

    def test_rejects_preview_manifest_without_packaging_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(Path(tmp), durations=[3, 4, 4, 6, 5, 3, 5])
            write(
                project / "qa" / "metadata" / "preview_manifest.json",
                json.dumps({"title": "测试项目", "shot_count": 7}, ensure_ascii=False),
            )
            result = self.run_validator(project)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("preview manifest missing field: shot_overlays", result.stdout + result.stderr)

    def test_accepts_explicitly_skipped_animatic_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(Path(tmp), durations=[3, 4, 4, 6, 5, 3, 5])
            (project / "最终交付" / "05_预览视频" / "分镜预览.mp4").unlink()
            write(
                project / "qa" / "metadata" / "preview_manifest.json",
                json.dumps(
                    {
                        "title": "测试项目",
                        "preview_profile": "off",
                        "shot_count": 7,
                        "skipped": True,
                        "output": False,
                        "motion_style": "none",
                    },
                    ensure_ascii=False,
                ),
            )
            result = self.run_validator(project)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_non_chinese_final_prompts_when_prompt_language_is_chinese(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(Path(tmp), durations=[3, 4, 4, 6, 5, 3, 5], prompt_language="zh-CN")
            write(
                project / "prompts" / "video_prompts.md",
                "# Video Prompts\n\n## S01\n- Visual prompt: premium beauty shot\n- Motion prompt: slow push in\n",
            )
            write(
                project / "最终交付" / "02_提示词" / "视频生成提示词.md",
                "# Copy Ready\n\n## S01\nVoiceover/audio: external voiceover.\nOn-screen text policy: none.\nNegative prompt: do not generate subtitles.\n",
            )
            result = self.run_validator(project)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Chinese prompt language requested", result.stdout + result.stderr)

    def test_rejects_negative_prompt_field_in_copy_ready_video_prompts(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(Path(tmp), durations=[3, 4, 4, 6, 5, 3, 5], prompt_language="zh-CN")
            write(
                project / "最终交付" / "02_提示词" / "视频生成提示词.md",
                "# Copy Ready\n\n"
                "## S01\n"
                "声音/口播：外部画外音，后期添加。\n"
                "背景音乐：不要生成背景音乐。\n"
                "SFX音效：雨声。\n"
                "画面文字策略：模型生成画面不添加字幕。\n"
                "负面提示词：不要水印。\n",
            )
            result = self.run_validator(project)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("final video prompts must not use negative prompt fields", result.stdout + result.stderr)

    def test_rejects_external_voiceover_prompt_that_repeats_transcript_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(Path(tmp), durations=[3, 4, 4, 6, 5, 3, 5], prompt_language="zh-CN")
            line = "The first time I held a steering wheel, I did not know what a finish line was."
            write(project / "audio" / "tts_lines.json", json.dumps([{"id": "VO01", "text": line}], ensure_ascii=False))
            write(
                project / "最终交付" / "02_提示词" / "视频生成提示词.md",
                "# Copy Ready\n\n"
                "## S01\n"
                f"声音/口播：外部画外音，后期添加：“{line}”\n"
                "背景音乐：不要生成背景音乐。\n"
                "SFX音效：方向盘皮革摩擦声。\n"
                "画面文字策略：模型生成画面不添加字幕。\n",
            )
            result = self.run_validator(project)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("external voiceover video prompts must not repeat transcript text", result.stdout + result.stderr)

    def test_rejects_copy_ready_video_prompt_blocks_without_no_music_or_sfx(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(Path(tmp), durations=[3, 4, 4, 6, 5, 3, 5], prompt_language="zh-CN")
            write(
                project / "最终交付" / "02_提示词" / "视频生成提示词.md",
                "# Copy Ready\n\n"
                "## S01\n"
                "声音/口播：外部画外音，后期添加。\n"
                "画面文字策略：模型生成画面不添加字幕。\n",
            )
            result = self.run_validator(project)
            self.assertNotEqual(result.returncode, 0)
            combined = result.stdout + result.stderr
            self.assertIn("missing no-background-music instruction", combined)
            self.assertIn("missing SFX sound design", combined)

    def test_default_seedance2_profile_requires_time_sliced_motion_prompts(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(Path(tmp), durations=[3, 4, 4, 6, 5, 3, 5], prompt_language="zh-CN")
            write(
                project / "最终交付" / "02_提示词" / "视频生成提示词.md",
                "# Copy Ready\n\n"
                "## S01\n"
                "声音/口播：外部画外音，后期添加。\n"
                "背景音乐：不要生成背景音乐；整片音乐后期统一处理。\n"
                "SFX音效：雨声。\n"
                "画面文字策略：模型生成画面不添加字幕。\n",
            )
            result = self.run_validator(project)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Seedance 2.0 prompts require time-coded motion slices", result.stdout + result.stderr)

    def test_explicit_non_seedance_model_can_use_model_agnostic_prompt_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(
                Path(tmp),
                durations=[3, 4, 4, 6, 5, 3, 5],
                prompt_language="zh-CN",
                extra_spec_lines=["- target_model: model-agnostic"],
            )
            result = self.run_validator(project)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_mixed_audio_subtitle_field_when_burned_subtitles_are_disabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(Path(tmp), durations=[3, 4, 4, 6, 5, 3, 5], prompt_language="zh-CN")
            write(
                project / "brief" / "spec_lock.md",
                "\n".join(
                    [
                        "# Spec Lock",
                        "",
                        "## format",
                        "- aspect_ratio: 9:16",
                        "- target_duration_seconds: 30",
                        "- prompt_language: zh-CN",
                        "",
                        "## production_mode",
                        "- video_mode: fast-paced-tvc",
                        "",
                        "## audio",
                        "- copy_language: zh-CN",
                        "- voiceover_language: zh-CN",
                        "- caption_language: zh-CN",
                        "- subtitle_rendering_policy: post-production-only",
                        "- burned_subtitles_allowed: false",
                    ]
                ),
            )
            write(
                project / "最终交付" / "02_提示词" / "视频生成提示词.md",
                "# Copy Ready\n\n## S01\n声音/字幕：VO“测试口播”\n",
            )
            result = self.run_validator(project)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("mixes voiceover and subtitle instructions", result.stdout + result.stderr)

    def test_rejects_missing_final_subtitle_deliverables(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(Path(tmp), durations=[3, 4, 4, 6, 5, 3, 5])
            (project / "最终交付" / "03_口播与字幕" / "中文字幕.srt").unlink()
            result = self.run_validator(project)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing final subtitle deliverable", result.stdout + result.stderr)

    def test_english_voiceover_requires_english_and_chinese_final_srt_when_localized_for_china(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(Path(tmp), durations=[3, 4, 4, 6, 5, 3, 5])
            write(
                project / "brief" / "spec_lock.md",
                "\n".join(
                    [
                        "# Spec Lock",
                        "",
                        "## format",
                        "- aspect_ratio: 9:16",
                        "- target_duration_seconds: 30",
                        "- prompt_language: zh-CN",
                        "",
                        "## production_mode",
                        "- video_mode: fast-paced-tvc",
                        "",
                        "## audio",
                        "- copy_language: en-US voiceover",
                        "- voiceover_language: en-US",
                        "- caption_language: en-US",
                        "- localized_caption_languages: zh-CN",
                        "- subtitle_rendering_policy: post-production-only",
                        "- burned_subtitles_allowed: false",
                    ]
                ),
            )
            write(project / "最终交付" / "03_口播与字幕" / "英文字幕.srt", "1\n00:00:00,000 --> 00:00:02,000\nTest\n")
            result = self.run_validator(project)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            (project / "最终交付" / "03_口播与字幕" / "英文字幕.srt").unlink()
            result = self.run_validator(project)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing English final subtitle file", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
