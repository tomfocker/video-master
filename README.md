# video-master

`video-master` 是一个 Codex skill，用来把视频想法、广告需求、已有素材或参考片，整理成一套 AI 视频前期制作包：需求判断、视频类型确认、创意策略、剧本/文案/音频拆分、详细分镜、原生生图分镜图，以及可直接复制到视频大模型里的生成提示词。

这个项目参考了 `ppt-master` 的组织方式：核心能力放在 `skills/video-master/`，仓库层面的文档、示例和测试用于说明如何安装、使用、验证和继续演进。

## 项目结构

```text
video-master/
  skills/
    video-master/
      SKILL.md
      agents/openai.yaml
      scripts/
        make_storyboard_overview.py
        make_animatic.py
        render_title_packaging.py
        generate_voiceover_tts.py
        export_production_workbook.py
        validate_video_project.py
      style_templates/
        cinematic-flow-racing/
      references/
        audio-and-copy.md
        output-contract.md
        platform-and-model-profiles.md
        quality-check.md
        storyboard-and-video-prompts.md
        video-modes.md
  docs/
    roadmap.md
    superpowers/plans/
    superpowers/specs/
  examples/
    sample-request.md
  tests/
    test_validate_video_project.py
```

## 当前能力

- 判断用户输入是纯想法、半成品素材，还是已经锁定的品牌/文案资料。
- 在写剧本前确认视频类型，例如广告 TVC、产品宣传短视频、故事短片、动画、教程讲解、品牌片或电商转化短视频。
- 分开确认提示词语言、口播语言、字幕语言和字幕渲染策略，避免视频模型误生成内嵌字幕。
- 设计非均匀镜头节奏，不再默认平均分配时长；高速、运动、竞速类主题会加入快切组、冲击镜头和呼吸镜头。
- 提取并集中管理口播稿、TTS 行、字幕、整片音乐方向、逐镜头 SFX 音效和音频生成提示。
- 面向国内用户交付中文优先的最终提示词；英文口播项目也会在 `最终交付/03_口播与字幕/` 中保留 `英文字幕.srt` 和 `中文字幕.srt`。
- 需要分镜图时，使用 Codex 原生生图能力生成 storyboard frames。
- 支持把用户提供的参考图片或视频作为 `reference_style` 分析，提炼可迁移的色彩、光影、节奏、镜头语言和包装规则，但不复制原片人物、品牌、台词、水印或具体画面。
- 默认把字幕作为后期资产处理；最终视频提示词会明确要求视频模型不要生成或烧录字幕，除非用户明确允许。
- 把用户真正需要使用的结果集中放到 `最终交付/`。
- 生成分镜总览 HTML 和 PNG 总览图。
- 生成 MP4 分镜预览视频，包含片头/片尾卡、镜头信息、字幕和可选配音。默认 `draft` 预览为 12fps，并自动匹配项目画面比例；如果不需要预览，可使用 `--preview-profile off`。
- 在生成分镜图前锁定视觉风格预设，例如 `imax_70mm_realism`、`photoreal_commercial`、`eastern_fantasy_3d`、`anime_cinematic_light`、`future_tech_clean`，并把画风、调色、光线、质感和镜头语言写入每条分镜图提示词。
- 可选生成商业标题包装旁路资产，包括大标题、章节标题、人名条、关键数据/数字包装和 CTA/end card。默认交付透明 PNG；只有明确需要真实动画叠加时才生成 ProRes 4444 透明通道 MOV。MOV 模板支持 `brush_reveal`、`route_light_trail`、`odometer`、`marker_annotation` 等，并可把原生生图清理出的透明设计稿作为 `design_asset` 继续动画化。这个分支不会改写原有视频提示词。
- 外部画外音不会直接写进最终视频提示词；每个视频片段提示词会要求不要生成背景音乐，并保留逐镜头 SFX 音效说明。
- 支持基于 `tts_lines.json` 生成或打包 TTS 配音。
- 导出制作总表，方便查看镜头、口播和交付信息。
- 使用本地校验脚本检查项目结构、镜头时长、音频文件、提示词语言和最终交付文件。

## 风格库方向

项目正在设计可扩展的视频风格库。未来用户可以选择：

- 完全原创：按新主题重新设计风格、剧本、分镜和提示词。
- 使用正式模板：调用已经维护好的导演风格模板。模板不再拆分强度档位；用户明确提出的想法、素材、文案、品牌和镜头优先于模板默认规则。
- 基于参考片创建模板：先由 AI 分析风格档案、节奏规则、分镜策略和提示词规则，再由用户补充设计思路、剪辑技巧和创作意图，确认后入库。

当前内置的第一枚正式模板：

- `cinematic-flow-racing`：意识流赛车压迫感短片。适合赛车手、极限运动员、拳击手、外科医生、钢琴家、交易员等高压职业心流主题。模板包包含导演笔记、剪辑技巧、镜头母题库和 60 秒示范分镜。

相关设计文档见：

```text
docs/superpowers/specs/2026-04-26-video-style-library-design.md
```

## 安装到 Codex

本地 Codex skill 的安装位置通常是：

```text
~/.codex/skills/video-master
```

修改仓库里的 skill 后，可以用下面的命令同步到 Codex：

```bash
rsync -a --delete skills/video-master/ ~/.codex/skills/video-master/
```

## 推荐依赖

`video-master` 作为 skill 可以不安装额外依赖运行，但仓库内的本地辅助工具需要 Python 依赖来获得更好的效果：

```bash
python3 -m pip install -r requirements.txt
```

推荐依赖当前用于：

- `Pillow`：生成分镜总览图和处理图片。
- `openpyxl`：导出制作总表。
- `imageio[ffmpeg]` 和 `numpy`：生成 MP4 分镜预览视频。
- `edge-tts`：可选 TTS 配音生成。
- `pydantic`：更稳的 JSON 结构校验。
- `pysubs2`：字幕文件校验。

## 验证项目

校验 skill 和测试：

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/video-master
python3 -m unittest discover -s tests
python3 -m unittest tests/test_validate_video_project.py -v
python3 -m unittest tests/test_storyboard_overview.py -v
python3 -m unittest tests/test_export_production_workbook.py -v
python3 -m unittest tests/test_make_animatic.py -v
python3 -m unittest tests/test_generate_voiceover_tts.py -v
```

针对生成后的视频项目：

```bash
python3 skills/video-master/scripts/make_storyboard_overview.py video_projects/<project>
python3 skills/video-master/scripts/export_production_workbook.py video_projects/<project>
python3 skills/video-master/scripts/generate_voiceover_tts.py video_projects/<project>
python3 skills/video-master/scripts/make_animatic.py video_projects/<project>
python3 skills/video-master/scripts/render_title_packaging.py video_projects/<project>
python3 skills/video-master/scripts/validate_video_project.py video_projects/<project>
```

分镜预览视频模式：

```bash
python3 skills/video-master/scripts/make_animatic.py video_projects/<project> --preview-profile draft
python3 skills/video-master/scripts/make_animatic.py video_projects/<project> --preview-profile smooth
python3 skills/video-master/scripts/make_animatic.py video_projects/<project> --preview-profile off
```

预览视频运动方式：

```bash
python3 skills/video-master/scripts/make_animatic.py video_projects/<project> --motion-style center-zoom
python3 skills/video-master/scripts/make_animatic.py video_projects/<project> --motion-style pan-zoom
python3 skills/video-master/scripts/make_animatic.py video_projects/<project> --motion-style none
```

## 示例调用

```text
Use $video-master 帮我做一个 30 秒小红书美妆新品广告。
我目前只有产品想法，没有品牌素材。
视频模式倾向快节奏广告 TVC，目标模型是可灵，最终提示词请用中文。
需要剧本、配音文案、字幕、详细分镜、关键分镜图和可直接复制的视频提示词。
```
