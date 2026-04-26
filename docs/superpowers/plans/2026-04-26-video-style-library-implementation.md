# Video Style Library Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a file-based, extensible video style template library to `video-master`, starting with the official `cinematic-flow-racing` template.

**Architecture:** Keep the style library inside the skill so it travels with the installable package. Add a small template loader that validates template package structure and exposes simple functions for validator and future workflow code. Update the skill instructions and project validator so selected templates become part of the production contract.

**Tech Stack:** Python standard library, existing `unittest` suite, Markdown/JSON template files, existing `validate_video_project.py` checker, Codex skill packaging rules.

---

## Scope Check

This plan implements the first file-based version of the style library. It does not build a UI, a cloud video-understanding integration, multi-template blending, or a fully automated "reference video to official template" generator. Those are later extensions. This version must be testable through local unit tests and the existing skill validator.

## File Structure

- Create `skills/video-master/style_templates/cinematic-flow-racing/`
  - First official style template package.
- Create `skills/video-master/style_templates/cinematic-flow-racing/template.md`
  - Human-readable director guide.
- Create `skills/video-master/style_templates/cinematic-flow-racing/template.json`
  - Machine-readable metadata, rules, tags, supported strengths, and required files.
- Create `skills/video-master/style_templates/cinematic-flow-racing/rhythm_rules.json`
  - Reusable rhythm phases, shot count guidance, fast-cut clusters, breath shots, and transition rules.
- Create `skills/video-master/style_templates/cinematic-flow-racing/prompt_rules.md`
  - Storyboard image and video prompt rules for this template.
- Create `skills/video-master/style_templates/cinematic-flow-racing/reference_notes.md`
  - Reference-derived observations, non-copying boundaries, and human curation notes.
- Create `skills/video-master/scripts/style_templates.py`
  - Loader and validator for template packages.
- Modify `skills/video-master/SKILL.md`
  - Add template intake mode, selected-template production lock fields, template strength rules, and template injection steps.
- Modify `skills/video-master/scripts/validate_video_project.py`
  - Validate `template_id`, `template_strength`, official/draft usage, rhythm-map traceability, and final prompt compliance when a template is selected.
- Modify `README.md`
  - Mention the first official style template after implementation.
- Create `tests/test_style_templates.py`
  - Unit tests for loader and template metadata.
- Modify `tests/test_validate_video_project.py`
  - Validator tests for selected templates in project packages.
- Modify `tests/test_reference_style_workflow.py`
  - Confirm skill instructions mention style templates and safe template application.

---

### Task 1: Add Style Template Loader

**Files:**
- Create: `skills/video-master/scripts/style_templates.py`
- Test: `tests/test_style_templates.py`

- [ ] **Step 1: Write failing loader tests**

Create `tests/test_style_templates.py`:

```python
import tempfile
import unittest
from pathlib import Path

import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "video-master" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from style_templates import TemplateError, load_template, list_templates


class StyleTemplateLoaderTest(unittest.TestCase):
    def test_loads_official_cinematic_flow_racing_template(self):
        template = load_template("cinematic-flow-racing")

        self.assertEqual(template["id"], "cinematic-flow-racing")
        self.assertEqual(template["status"], "official")
        self.assertIn("意识流", template["display_name"])
        self.assertIn("高压职业", template["tags"])
        self.assertIn("medium", template["strengths"])

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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the new tests and verify they fail**

Run:

```bash
python3 -m unittest tests/test_style_templates.py -v
```

Expected: FAIL or ERROR because `style_templates.py` and the template package do not exist yet.

- [ ] **Step 3: Implement the loader**

Create `skills/video-master/scripts/style_templates.py`:

```python
#!/usr/bin/env python3
"""Load and validate video-master style template packages."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE_ROOT = SKILL_DIR / "style_templates"

REQUIRED_PACKAGE_FILES = [
    "template.md",
    "template.json",
    "rhythm_rules.json",
    "prompt_rules.md",
    "reference_notes.md",
]

REQUIRED_TEMPLATE_FIELDS = [
    "id",
    "display_name",
    "status",
    "version",
    "updated_at",
    "tags",
    "best_for",
    "not_for",
    "supported_video_modes",
    "supported_aspect_ratios",
    "duration_range_seconds",
    "strengths",
    "visual_rules",
    "rhythm_rules",
    "camera_rules",
    "sound_rules",
    "storyboard_prompt_rules",
    "video_prompt_rules",
    "safety_boundaries",
    "required_files",
]

VALID_STATUSES = {"draft", "official"}
VALID_STRENGTHS = {"light", "medium", "high"}


class TemplateError(ValueError):
    """Raised when a style template package is missing or invalid."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TemplateError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise TemplateError(f"{path} must contain a JSON object")
    return data


def _as_list(value: Any, field: str) -> list:
    if not isinstance(value, list) or not value:
        raise TemplateError(f"{field} must be a non-empty list")
    return value


def _as_dict(value: Any, field: str) -> dict:
    if not isinstance(value, dict) or not value:
        raise TemplateError(f"{field} must be a non-empty object")
    return value


def validate_template_metadata(data: dict[str, Any], package_dir: Path) -> dict[str, Any]:
    missing = [field for field in REQUIRED_TEMPLATE_FIELDS if field not in data]
    if missing:
        raise TemplateError(f"missing required metadata: {', '.join(missing)}")

    template_id = str(data["id"]).strip()
    if not template_id:
        raise TemplateError("id must be non-empty")
    if template_id != package_dir.name:
        raise TemplateError(f"template id {template_id!r} must match folder name {package_dir.name!r}")

    status = str(data["status"]).strip()
    if status not in VALID_STATUSES:
        raise TemplateError(f"status must be one of: {', '.join(sorted(VALID_STATUSES))}")

    for field in [
        "tags",
        "best_for",
        "not_for",
        "supported_video_modes",
        "supported_aspect_ratios",
        "visual_rules",
        "rhythm_rules",
        "camera_rules",
        "sound_rules",
        "storyboard_prompt_rules",
        "video_prompt_rules",
        "safety_boundaries",
        "required_files",
    ]:
        _as_list(data[field], field)

    strengths = _as_dict(data["strengths"], "strengths")
    missing_strengths = sorted(VALID_STRENGTHS - set(strengths))
    if missing_strengths:
        raise TemplateError(f"strengths missing: {', '.join(missing_strengths)}")

    duration_range = data["duration_range_seconds"]
    if (
        not isinstance(duration_range, dict)
        or not isinstance(duration_range.get("min"), (int, float))
        or not isinstance(duration_range.get("max"), (int, float))
        or duration_range["min"] <= 0
        or duration_range["max"] < duration_range["min"]
    ):
        raise TemplateError("duration_range_seconds must include numeric min and max")

    required_files = [str(item) for item in data["required_files"]]
    for filename in REQUIRED_PACKAGE_FILES:
        if filename not in required_files:
            raise TemplateError(f"required_files must include {filename}")
        if not (package_dir / filename).is_file():
            raise TemplateError(f"missing template package file: {filename}")

    return data


def load_template(template_id: str, template_root: Path | None = None) -> dict[str, Any]:
    root = template_root or DEFAULT_TEMPLATE_ROOT
    package_dir = root / template_id
    if not package_dir.is_dir():
        raise TemplateError(f"template not found: {template_id}")

    data = _read_json(package_dir / "template.json")
    validated = validate_template_metadata(data, package_dir)
    validated = dict(validated)
    validated["package_dir"] = str(package_dir)
    return validated


def list_templates(template_root: Path | None = None) -> list[dict[str, Any]]:
    root = template_root or DEFAULT_TEMPLATE_ROOT
    if not root.is_dir():
        return []

    templates: list[dict[str, Any]] = []
    for package_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        template = load_template(package_dir.name, template_root=root)
        templates.append(
            {
                "id": template["id"],
                "display_name": template["display_name"],
                "status": template["status"],
                "version": template["version"],
                "tags": template["tags"],
            }
        )
    return templates
```

- [ ] **Step 4: Run the loader tests again**

Run:

```bash
python3 -m unittest tests/test_style_templates.py -v
```

Expected: still FAIL because `cinematic-flow-racing` has not been created yet.

- [ ] **Step 5: Commit the loader and tests**

Only commit after Task 2 passes with the real template package.

---

### Task 2: Add The First Official Template Package

**Files:**
- Create: `skills/video-master/style_templates/cinematic-flow-racing/template.md`
- Create: `skills/video-master/style_templates/cinematic-flow-racing/template.json`
- Create: `skills/video-master/style_templates/cinematic-flow-racing/rhythm_rules.json`
- Create: `skills/video-master/style_templates/cinematic-flow-racing/prompt_rules.md`
- Create: `skills/video-master/style_templates/cinematic-flow-racing/reference_notes.md`
- Test: `tests/test_style_templates.py`

- [ ] **Step 1: Create `template.json`**

Create `skills/video-master/style_templates/cinematic-flow-racing/template.json`:

```json
{
  "id": "cinematic-flow-racing",
  "display_name": "意识流赛车压迫感短片",
  "status": "official",
  "version": "1.0.0",
  "updated_at": "2026-04-26",
  "tags": ["意识流", "赛车", "高压职业", "心流", "黑白", "压迫感", "极限运动", "电影感"],
  "best_for": ["赛车手独白", "极限运动员", "拳击手", "外科医生", "钢琴家", "交易员", "创业者", "高压职业心流短片"],
  "not_for": ["明亮美妆广告", "轻松电商种草", "亲子儿童内容", "喜剧短片", "直接信息讲解类视频"],
  "supported_video_modes": ["narrative-short", "brand-film", "fast-paced-tvc"],
  "supported_aspect_ratios": ["16:9", "9:16", "1:1"],
  "duration_range_seconds": {
    "min": 30,
    "max": 120
  },
  "strengths": {
    "light": {
      "label": "轻度参考",
      "behavior": "只继承低饱和高反差、冷峻压迫气质、局部红色信号点和局部极近特写。"
    },
    "medium": {
      "label": "中度套用",
      "behavior": "继承现实压迫到心流释放的节奏弧线、快切压力组、呼吸镜头、外部画外音和逐镜头 SFX。"
    },
    "high": {
      "label": "高度风格锁定",
      "behavior": "强继承现实压迫、临界爆发、风暴眼、超现实升华的四段结构，但重写全部主体、场景、台词和具体画面。"
    }
  },
  "visual_rules": [
    "近黑白低饱和画面，高反差暗部，湿润银色高光。",
    "红色或橙色只作为信号灯、仪表、火花、尾灯等稀少强调色。",
    "用极近机械细节、眼神、手部动作和材质纹理制造压迫。",
    "用巨大负空间和小主体建立孤独、危险和心流感。",
    "人物面部常被头盔、反光、阴影、雨水、烟雾或玻璃遮挡。"
  ],
  "rhythm_rules": [
    "前半段使用短镜头和触觉插入制造焦虑。",
    "中段设置至少一组 0.6-1.2 秒快切压力组。",
    "后段出现明显节奏转折，进入更安静、更超现实的心流段。",
    "长镜头必须承担情绪呼吸或宇宙化意象，不作为平均填充。"
  ],
  "camera_rules": [
    "优先使用 extreme close-up、POV、macro insert、long negative-space wide shot。",
    "高速段允许车载震动、冲击式推近、甩镜和轻微手持不稳定。",
    "心流段减少晃动，使用漂浮感、远景、慢速推进或稳定横移。"
  ],
  "sound_rules": [
    "默认外部画外音，台词留在 audio 和 SRT 文件中。",
    "视频模型片段不要生成背景音乐，整片音乐由后期统一处理。",
    "每个镜头必须有具体 SFX 音效设计。",
    "字幕默认后期添加，视频模型画面不要生成字幕或内嵌文字。"
  ],
  "storyboard_prompt_rules": [
    "图片提示词必须包含低饱和、高反差、湿润高光、黑白工业质感。",
    "高压段必须包含触觉细节或主观视角。",
    "心流段必须包含负空间、超现实尺度或安静悬浮感。",
    "不得要求复制参考片的具体人物、品牌、水印、台词或构图。"
  ],
  "video_prompt_rules": [
    "每个镜头必须写明画面、动作、镜头、声音/口播、背景音乐、SFX 音效和画面文字策略。",
    "外部画外音只写后期添加，不粘贴完整口播台词。",
    "背景音乐字段必须说明不要生成背景音乐。",
    "不得使用负面提示词字段。"
  ],
  "safety_boundaries": [
    "不复制参考片人物、真实车队标识、赞助商品牌、字幕、水印或原始台词。",
    "不使用真实 F1 车手或真实品牌身份，除非用户提供授权。",
    "只迁移色彩、节奏、镜头语言、声音策略和抽象意象结构。"
  ],
  "required_files": [
    "template.md",
    "template.json",
    "rhythm_rules.json",
    "prompt_rules.md",
    "reference_notes.md"
  ]
}
```

- [ ] **Step 2: Create `rhythm_rules.json`**

Create `skills/video-master/style_templates/cinematic-flow-racing/rhythm_rules.json`:

```json
{
  "template_id": "cinematic-flow-racing",
  "default_arc": [
    {
      "phase": "现实压迫",
      "position": "0-35%",
      "shot_duration_guidance": "0.8-4s",
      "camera_energy": ["macro insert", "POV", "vehicle vibration", "impact push-in"]
    },
    {
      "phase": "临界爆发",
      "position": "35-55%",
      "shot_duration_guidance": "0.6-1.2s rapid-cut cluster",
      "camera_energy": ["whip pan", "hard cut", "gauge insert", "light flash"]
    },
    {
      "phase": "暴风眼",
      "position": "55-75%",
      "shot_duration_guidance": "3-7s",
      "camera_energy": ["stable", "floating", "slow push"]
    },
    {
      "phase": "超现实心流",
      "position": "75-100%",
      "shot_duration_guidance": "3-8s",
      "camera_energy": ["wide negative space", "slow drift", "locked-off calm"]
    }
  ],
  "minimum_requirements": {
    "rapid_cut_clusters": 1,
    "rapid_cut_cluster_min_shots": 3,
    "rapid_cut_max_duration_seconds": 1.2,
    "breath_shots": 2,
    "late_flow_state_turn": true
  },
  "transition_rules": [
    "Use hard cuts in pressure clusters.",
    "Use silence, visual expansion, or slowed motion at the flow-state turn.",
    "Avoid decorative transitions that reduce the pressure."
  ]
}
```

- [ ] **Step 3: Create `template.md`**

Create `skills/video-master/style_templates/cinematic-flow-racing/template.md`:

```markdown
# 意识流赛车压迫感短片

## 定位

这是一个高压职业心流短片模板。它用赛车语境总结出一种可迁移的导演方法：先用身体压力、机械细节和快速剪辑压缩观众呼吸，再在后段切入更安静、更抽象的心流状态。

## 核心情绪

恐惧、过载、临界点、突然安静、进入心流。

## 适用题材

- 赛车手、极限运动员、拳击手、外科医生、钢琴家、交易员、创业者。
- 任何需要表现“高压环境下进入绝对专注”的人物短片。

## 不适合题材

- 明亮轻松的电商种草。
- 美妆晨光质感广告。
- 儿童亲子、喜剧、直接教程讲解。

## 视觉方法

- 近黑白低饱和，高反差暗部，湿润银色高光。
- 红色或橙色只用于信号点。
- 极近特写和巨大负空间交替出现。
- 人物情绪不靠直白表演，而靠眼神、手、呼吸、机械纹理和环境压力外化。

## 节奏方法

- 前半段：紧、短、硬，制造身体压力。
- 中段：至少一组 3 个以上的 0.6-1.2 秒快切镜头。
- 后段：出现明显的“暴风眼”式转折，画面变安静、尺度变大。
- 结尾：进入超现实心流，不用解释性字幕收尾。

## 声音方法

- 默认外部画外音。
- 视频模型不要逐片段生成背景音乐。
- 每个镜头必须设计 SFX。
- 字幕用 SRT 后期添加，不让视频模型烧录字幕。

## 不可复制

不得复制参考片人物、真实车队、赞助商品牌、水印、字幕、原始台词、具体画面或创作者身份。
```

- [ ] **Step 4: Create `prompt_rules.md`**

Create `skills/video-master/style_templates/cinematic-flow-racing/prompt_rules.md`:

```markdown
# Prompt Rules

## Storyboard Image Prompts

- Include: high-contrast near-monochrome, crushed blacks, wet silver highlights, rare red signal accent.
- Use tactile image anchors: visor reflection, gloved hand, gauge needle, tire spray, metal texture, breath fog, rain, smoke, carbon fiber.
- Use scale contrast: extreme close-up against vast negative-space wide shots.
- For flow-state shots, use calm surreal expansion instead of literal explanation.
- Do not ask for reference-frame copying, real team marks, watermarks, burned subtitles, or real driver likenesses.

## Video Prompts

Each final video prompt block must include these fields:

- 画面
- 动作
- 镜头
- 声音/口播
- 背景音乐
- SFX音效
- 画面文字策略

For external voiceover, write:

```text
声音/口播：外部画外音，后期添加；本片段不生成对白或口播台词。
```

For music, write:

```text
背景音乐：不要生成背景音乐；整片音乐后期统一处理。
```

For text, write:

```text
画面文字策略：无；不要生成字幕、caption、对白文字或烧录文字，字幕使用 SRT 后期添加。
```

Do not include a `负面提示词` or `Negative prompt` field.
```

- [ ] **Step 5: Create `reference_notes.md`**

Create `skills/video-master/style_templates/cinematic-flow-racing/reference_notes.md`:

```markdown
# Reference Notes

## 来源角色

该模板来自对意识流赛车压迫感短片的风格分析。参考素材只作为 `reference_style` 使用。

## 可迁移内容

- 低饱和黑白高反差。
- 湿润银色高光和少量红色信号点。
- 极近触觉细节和巨大负空间的交替。
- 前半段压迫、后半段心流的节奏转折。
- 外部画外音、逐镜头 SFX、字幕后期添加。

## 不可迁移内容

- 原片人物、台词、字幕、水印、品牌、具体镜头、真实赛车组织或车队身份。
- 原片创作者身份或受保护的个人风格标签。

## 人工策展判断

这个模板的核心不是“拍赛车”，而是“用视听压力表现高压职业进入心流”。因此它可以迁移到外科医生、拳击手、钢琴家、交易员等主题。
```

- [ ] **Step 6: Run loader tests**

Run:

```bash
python3 -m unittest tests/test_style_templates.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit loader and first template**

Run:

```bash
git add skills/video-master/scripts/style_templates.py \
  skills/video-master/style_templates/cinematic-flow-racing \
  tests/test_style_templates.py
git commit -m "feat: add video style template library"
```

---

### Task 3: Update Skill Workflow Instructions

**Files:**
- Modify: `skills/video-master/SKILL.md`
- Modify: `skills/video-master/references/output-contract.md`
- Modify: `skills/video-master/references/storyboard-and-video-prompts.md`
- Test: `tests/test_reference_style_workflow.py`

- [ ] **Step 1: Extend workflow instruction tests**

Modify `tests/test_reference_style_workflow.py` by adding this test method:

```python
    def test_skill_documents_style_template_modes_and_strengths(self):
        skill = (ROOT / "skills" / "video-master" / "SKILL.md").read_text(encoding="utf-8")
        output_contract = (
            ROOT / "skills" / "video-master" / "references" / "output-contract.md"
        ).read_text(encoding="utf-8")
        prompt_reference = (
            ROOT / "skills" / "video-master" / "references" / "storyboard-and-video-prompts.md"
        ).read_text(encoding="utf-8")

        self.assertIn("style_templates", skill)
        self.assertIn("template_id", skill)
        self.assertIn("template_strength", skill)
        self.assertIn("light", skill)
        self.assertIn("medium", skill)
        self.assertIn("high", skill)
        self.assertIn("template_id", output_contract)
        self.assertIn("template_strength", output_contract)
        self.assertIn("style template", prompt_reference)
```

- [ ] **Step 2: Run workflow instruction tests and verify they fail**

Run:

```bash
python3 -m unittest tests/test_reference_style_workflow.py -v
```

Expected: FAIL because template workflow instructions have not been added yet.

- [ ] **Step 3: Update `SKILL.md` global rules**

Modify `skills/video-master/SKILL.md` under `## Global Rules` and add:

```markdown
- When a user wants a reusable style approach, offer three project style modes: `original`, `use_style_template`, or `create_style_template_from_reference`.
- Official style templates live in `style_templates/<template_id>/` and are applied only through `template_id` plus `template_strength`.
- Supported `template_strength` values are `light`, `medium`, and `high`. Default to `medium` when the user selects a template but does not express a strength preference.
- Do not use a draft style template for a final project unless the user explicitly opts in with `allow_draft_template: true`.
- A style template transfers creative rules such as rhythm, palette, camera language, sound policy, and prompt structure; it never authorizes copying reference subjects, exact shots, dialogue, branding, subtitles, watermarks, or creator identity.
```

- [ ] **Step 4: Update `SKILL.md` input and production lock steps**

Modify Step 1 to include:

```markdown
Before video-mode confirmation, classify the style route:

- `original`: create a new style from the project brief.
- `use_style_template`: use an official template from `style_templates/`.
- `create_style_template_from_reference`: analyze reference assets and produce a draft template package for user confirmation.

If using a template, capture `template_id`, `template_strength`, and whether draft templates are allowed.
```

Modify the Production Lock numbered list to include these fields:

```markdown
13. Style route: `original`, `use_style_template`, or `create_style_template_from_reference`
14. Style template fields when applicable: `template_id`, `template_strength`, and `allow_draft_template`
15. Template application summary: what is inherited, what is adapted, and what must not be copied
```

- [ ] **Step 5: Update `SKILL.md` rhythm, script, storyboard, and prompt steps**

Add the following lines to the relevant steps:

```markdown
If `template_id` is present, read `style_templates/<template_id>/template.md`, `rhythm_rules.json`, and `prompt_rules.md` before writing the rhythm map.
```

```markdown
When a style template is selected, `strategy/rhythm_map.md` must name the template, state the selected strength, and explain how the template rhythm is adapted to the current subject and duration.
```

```markdown
When a style template is selected, storyboard image prompts and video prompts must carry the template's safe prompt rules according to `template_strength`.
```

- [ ] **Step 6: Update `output-contract.md`**

Add required optional fields to the `brief/spec_lock.md` contract:

```markdown
## style_route
- style_route: original | use_style_template | create_style_template_from_reference
- template_id: cinematic-flow-racing
- template_strength: light | medium | high
- allow_draft_template: false
- template_application_summary: 中度套用节奏结构、镜头语言、声音策略和提示词规则；不复制参考片人物、台词、品牌、水印或具体画面。
```

- [ ] **Step 7: Update `storyboard-and-video-prompts.md`**

Add this section:

```markdown
## Style Template Application

When `brief/spec_lock.md` contains `template_id`, prompt writing must read `style_templates/<template_id>/prompt_rules.md`.

- `light`: inherit mood, palette, lighting, and broad atmosphere only.
- `medium`: inherit mood, rhythm strategy, camera language, sound policy, and prompt fields while redesigning the subject.
- `high`: inherit the template's narrative rhythm and camera grammar strongly, while still rewriting all subject matter and never copying exact reference content.

Final video prompts must remain subject-specific and must not mention copying the reference video.
```

- [ ] **Step 8: Run workflow instruction tests**

Run:

```bash
python3 -m unittest tests/test_reference_style_workflow.py -v
```

Expected: PASS.

- [ ] **Step 9: Commit skill workflow updates**

Run:

```bash
git add skills/video-master/SKILL.md \
  skills/video-master/references/output-contract.md \
  skills/video-master/references/storyboard-and-video-prompts.md \
  tests/test_reference_style_workflow.py
git commit -m "docs: add style template workflow"
```

---

### Task 4: Add Template Validation To Project Checker

**Files:**
- Modify: `skills/video-master/scripts/validate_video_project.py`
- Modify: `tests/test_validate_video_project.py`

- [ ] **Step 1: Add failing validator tests**

Modify `tests/test_validate_video_project.py`.

Extend `make_project` to allow custom rhythm map and final video prompt content:

```python
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
```

Replace the existing rhythm map write with:

```python
    write(project / "strategy" / "rhythm_map.md", rhythm_map_content)
```

Before writing the final video prompt, add:

```python
        if final_video_prompt_content is None:
            final_video_prompt_content = (
                "# Copy Ready\n\n"
                "## S01\n"
                "声音/口播：外部画外音，后期添加；本片段不生成对白或口播台词。\n"
                "背景音乐：不要生成背景音乐；整片音乐后期统一处理。\n"
                "SFX音效：清晨环境声、衣料摩擦声。\n"
                "画面文字策略：无；字幕使用SRT后期添加，模型生成画面不添加字幕。\n"
            )
```

Replace the existing final video prompt write with:

```python
        write(project / "最终交付" / "02_提示词" / "视频生成提示词.md", final_video_prompt_content)
```

Add these tests:

```python
    def test_rejects_template_id_without_template_strength(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(
                Path(tmp),
                durations=[3, 4, 4, 6, 5, 3, 5],
                extra_spec_lines=["- style_route: use_style_template", "- template_id: cinematic-flow-racing"],
            )
            result = self.run_validator(project)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("template_strength is required when template_id is set", result.stdout + result.stderr)

    def test_rejects_unknown_template_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(
                Path(tmp),
                durations=[3, 4, 4, 6, 5, 3, 5],
                extra_spec_lines=[
                    "- style_route: use_style_template",
                    "- template_id: missing-template",
                    "- template_strength: medium",
                ],
            )
            result = self.run_validator(project)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("template not found", result.stdout + result.stderr)

    def test_rejects_template_project_without_rhythm_trace(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(
                Path(tmp),
                durations=[6, 1, 1, 1.2, 5, 5, 5, 5],
                extra_spec_lines=[
                    "- style_route: use_style_template",
                    "- template_id: cinematic-flow-racing",
                    "- template_strength: medium",
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

    def test_accepts_project_with_official_template_trace(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(
                Path(tmp),
                durations=[6, 1, 1, 1.2, 5, 5, 5, 5],
                extra_spec_lines=[
                    "- style_route: use_style_template",
                    "- template_id: cinematic-flow-racing",
                    "- template_strength: medium",
                ],
                rhythm_map_content=(
                    "# Rhythm Map\n\n"
                    "- template_id: cinematic-flow-racing\n"
                    "- template_strength: medium\n"
                    "- template_application: 中度套用现实压迫、快切压力组、暴风眼和超现实心流结构。\n"
                ),
                shot_overrides={
                    "S02": {"movement": "车载震动，快切冲击"},
                    "S03": {"movement": "POV 晃动，硬切"},
                    "S04": {"movement": "甩镜，仪表红灯闪烁"},
                },
                final_video_prompt_content=(
                    "# Copy Ready\n\n"
                    "## S01\n"
                    "画面：低饱和黑白高反差，湿润银色高光，人物处在巨大负空间中。\n"
                    "声音/口播：外部画外音，后期添加；本片段不生成对白或口播台词。\n"
                    "背景音乐：不要生成背景音乐；整片音乐后期统一处理。\n"
                    "SFX音效：远处发动机低频、雨滴敲击、呼吸声。\n"
                    "画面文字策略：无；不要生成字幕、caption、对白文字或烧录文字，字幕使用 SRT 后期添加。\n"
                ),
            )
            result = self.run_validator(project)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
```

- [ ] **Step 2: Run validator tests and verify they fail**

Run:

```bash
python3 -m unittest tests/test_validate_video_project.py -v
```

Expected: FAIL because validator does not validate template fields yet.

- [ ] **Step 3: Import template loader into validator**

Modify `skills/video-master/scripts/validate_video_project.py` near the existing imports:

```python
from style_templates import TemplateError, load_template
```

Add constants:

```python
VALID_TEMPLATE_STRENGTHS = {"light", "medium", "high"}
STYLE_TEMPLATE_TERMS = [
    "低饱和",
    "高反差",
    "黑白",
    "银色高光",
    "负空间",
    "心流",
    "压迫",
]
```

- [ ] **Step 4: Add template validation function**

Add this function to `validate_video_project.py`:

```python
def validate_style_template(project: Path, spec: dict[str, str], errors: list[str]) -> None:
    template_id = spec.get("template_id", "").strip()
    if not template_id:
        return

    template_strength = spec.get("template_strength", "").strip()
    if not template_strength:
        errors.append("template_strength is required when template_id is set")
        return
    if template_strength not in VALID_TEMPLATE_STRENGTHS:
        errors.append("template_strength must be one of: high, light, medium")
        return

    try:
        template = load_template(template_id)
    except TemplateError as exc:
        errors.append(str(exc))
        return

    allow_draft = spec.get("allow_draft_template", "false").strip().lower() == "true"
    if template["status"] == "draft" and not allow_draft:
        errors.append(f"draft template requires allow_draft_template: true: {template_id}")

    rhythm_map = project / "strategy" / "rhythm_map.md"
    rhythm_text = read_text(rhythm_map) if rhythm_map.is_file() else ""
    if template_id not in rhythm_text:
        errors.append("rhythm_map must name selected template")
    if template_strength not in rhythm_text:
        errors.append("rhythm_map must name selected template_strength")

    final_prompt = video_prompt_path(project)
    prompt_text = read_text(final_prompt) if final_prompt.is_file() else ""
    if template_id == "cinematic-flow-racing":
        if not any(term in prompt_text for term in STYLE_TEMPLATE_TERMS):
            errors.append("cinematic-flow-racing prompts must carry the template visual language")
```

- [ ] **Step 5: Call template validation from `main`**

Find the section in `validate_video_project.py` where other validators are called after `spec = parse_spec_lock(...)`.

Add:

```python
    validate_style_template(project, spec, errors)
```

- [ ] **Step 6: Run validator tests**

Run:

```bash
python3 -m unittest tests/test_validate_video_project.py -v
```

Expected: PASS.

- [ ] **Step 7: Run all tests**

Run:

```bash
python3 -m unittest discover -s tests
```

Expected: PASS.

- [ ] **Step 8: Commit validator updates**

Run:

```bash
git add skills/video-master/scripts/validate_video_project.py tests/test_validate_video_project.py
git commit -m "feat: validate style template usage"
```

---

### Task 5: Update README And Installable Skill Copy

**Files:**
- Modify: `README.md`
- Copy to: `/Users/andy/.codex/skills/video-master/`

- [ ] **Step 1: Update README style-library section**

Modify `README.md` under `## 风格库方向` and add:

```markdown
当前内置的第一枚正式模板：

- `cinematic-flow-racing`：意识流赛车压迫感短片。适合赛车手、极限运动员、拳击手、外科医生、钢琴家、交易员等高压职业心流主题。
```

- [ ] **Step 2: Sync skill into Codex install path**

Run:

```bash
rsync -a --delete skills/video-master/ ~/.codex/skills/video-master/
```

Expected: no output.

- [ ] **Step 3: Validate installed skill**

Run:

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py ~/.codex/skills/video-master
```

Expected:

```text
Skill is valid!
```

- [ ] **Step 4: Commit README and installed-skill source changes**

Run:

```bash
git add README.md
git commit -m "docs: document first style template"
```

---

### Task 6: Final Verification And Push

**Files:**
- Verify all modified files.
- No new source file should remain untracked.

- [ ] **Step 1: Run formatting and whitespace check**

Run:

```bash
git diff --check
```

Expected: no output.

- [ ] **Step 2: Run full tests**

Run:

```bash
python3 -m unittest discover -s tests
```

Expected:

```text
OK
```

- [ ] **Step 3: Validate repository skill**

Run:

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/video-master
```

Expected:

```text
Skill is valid!
```

- [ ] **Step 4: Validate installed skill**

Run:

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py ~/.codex/skills/video-master
```

Expected:

```text
Skill is valid!
```

- [ ] **Step 5: Check Git status**

Run:

```bash
git status --short
```

Expected: no uncommitted files.

- [ ] **Step 6: Push to GitHub**

Run:

```bash
git push
```

Expected: `main -> main` pushed to `https://github.com/tomfocker/video-master.git`.

---

## Self-Review

- Spec coverage: The plan implements the file-based template library, draft/official status validation, three strength levels, first `cinematic-flow-racing` template, skill workflow integration, validator checks, tests, README update, and installed-skill sync.
- Deferred scope: UI, template search, cloud video-reading providers, multi-template blending, and fully automated reference-to-template generation remain out of first implementation scope.
- Placeholder scan: The plan intentionally avoids unresolved placeholders and names exact files, commands, expected results, and code snippets for each implementation step.
- Type consistency: `template_id`, `template_strength`, `allow_draft_template`, and `style_route` are used consistently across `template.json`, `SKILL.md`, `spec_lock.md`, tests, and validator checks.

