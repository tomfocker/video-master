# Seedance 2.0 Practical Playbook

Use this playbook when a project targets Seedance 2.0, Doubao video, or a Seedance-compatible Chinese web video workflow. It captures practical lessons from a multi-segment animated mascot short where reference images, dialogue, camera movement, and 15-second clip prompts had to stay coherent.

## Core Production Rules

- Treat each 15-second clip as a mini sequence, not as one static shot. A 15-second segment should have internal beats, motivated camera moves, and a clear start/middle/end.
- Do not force unrelated story material into the same 15-second prompt. If a new idea, location, product, or emotional beat is not tightly connected, move it to the next segment.
- Complex 15-second segments need multiple reference images. Use 3-5 frames for reveals, handoffs, transformations, multi-location windows, or end-card staging.
- For scene consistency, give each 15-second segment a `场景设定` and, when the scene/location/set matters, one wide scene-anchor reference image before action keyframes. Use the scene anchor to lock space, architecture, tabletop layout, room tone, environment density, light direction, and the visible placement of recurring characters/products when they belong to the scene.
- Each copy-ready prompt needs a detailed `画面风格说明`, not only a short style label. For style-heavy or realistic scenes, split it into `风格核心`, `视觉基调`, `色彩与影调`, `摄影机与镜头`, `材质与特效`, `动作质感`, and `风格边界`.
- Final video prompts should use an integrated timeline. Each time slice must combine image action, camera movement, character performance/dialogue mouth cue, natural synchronous sound, and SFX accents.
- Dialogue in the prompt is a performance and lip-sync cue. Do not ask the video model to render subtitles, dialogue text, captions, labels, signs, logos, maps, or readable packaging text.
- Keep per-clip background music off. Ask the model to generate natural synchronous sound / room tone when audio is relevant, then use shot-specific SFX as accents. Handle music in post-production so assembled clips do not fight each other.

## 15-Second Segment Design

For Seedance 2.0, write 15-second segments as time-coded continuity blocks:

```text
00-1s: opening hook + camera entry + first room tone/material sound
1-3s: motivated reveal or handoff + camera acceleration + first mouth cue/SFX accent
3-6s: product/material/object/environment detail + focus/camera change + natural sync sound
6-10s: performance, reaction, proof, or narrative payoff + camera settles into a readable hold
10-13s: transition preparation or emotional breath + environment response
13-15s: bridge into next segment, or clean hold for edit
```

The exact slice count and timing should follow the segment. Use whole-second ranges in final model-facing prompts. Do not use decimal/sub-second time codes unless writing a post-production edit note outside the copy-ready video prompt. Do not default to equal 3-second blocks unless the project deliberately uses a fixed beat grid. A calm segment can use fewer, longer slices; a dense transition segment can use short 1-second impact slices mixed with longer reaction or proof holds. Avoid generic slice language. Every slice must be derived from the actual beat, prop, character, material, sound, and transition.

## Scene Anchor And Style Detail

Before writing the time slices for a 15-second segment, lock:

- `场景设定`: the stable physical space, time, environmental state, set dressing, object layout, recurring visible character/product placement, and what should not change during the segment.
- `大场景参考图`: a wide/establishing scene anchor when the set, street, room, landscape, tabletop, stage, or product environment must remain consistent. Name it separately from action keyframes, for example `SEG01_SCENE`.
- `画面风格说明`: the detailed visual grammar, including style core, realism level, camera/lens base, color and shadow rules, texture/material rendering, atmosphere, and any model-facing consistency limits.

The scene anchor is not a busy storyboard frame. It should show the whole playable space clearly: background, floor/table/terrain, light direction, major props, recurring character/product starting zones when relevant, and title-safe or action-safe areas. Action keyframes such as `SEG01_A-SEG01_D` can then focus on close-ups, transitions, character reactions, product motion, or payoff states.

If a project uses one stable location across multiple segments, create one project-level scene anchor and repeat its path in each segment. If each segment changes location, create one scene anchor per segment. For abstract product ads, the scene anchor may be a clean tabletop, bathroom counter, studio plinth, poster layout, or product stage.

When the user wants a realistic live-action scene and needs to reduce AI-generated feel, include these model-facing realism anchors in `风格核心` or `视觉基调`: `超写实`, `极致逼真`, `Photorealism-真人实景拍摄`. Use them only for photoreal/live-action workflows. Do not add them to 2D illustration, anime, toy-like animation, deliberately stylized 3D, or graphic motion projects.

## Reference Image Coverage

Use multiple stills when a 15-second segment contains more than one important visual state:

- `A`: opening state or entry camera.
- `B`: first action handoff, reveal, or material close-up.
- `C`: transformation midpoint, character reaction, or key object state.
- `D`: payoff, transition exit, or next-segment bridge.
- `E`: optional extra frame for character introductions or especially complex openings.

Still image prompts should not try to show the whole 15 seconds at once. Each reference image should be a clean key frame with clear motion direction and a single purpose.

## Prompt Structure

Use this pattern for 15-second copy-ready prompts:

```markdown
## SEG01 - <段落名>（15s / 16:9 / Seedance 2.0 / 参考图：SEG01_SCENE + SEG01_A-SEG01_D）

场景设定：<stable scene, environment, time, layout, light direction, major props, recurring visible character/product identity and starting placement, what must not change>
画面风格说明：
风格核心：<core style and realism intent; for realistic scenes include 超写实、极致逼真、Photorealism-真人实景拍摄 when appropriate>
视觉基调：<cinema/camera base, aspect feeling, composition, motion texture>
色彩与影调：<palette, contrast, saturation, highlight/shadow behavior, grain/filter/light rules>
摄影机与镜头：<camera body/lens feel, focal length behavior, motion blur, handheld/stabilized style>
材质与特效：<material rendering, VFX/particle/CG boundaries, practical texture rules>
动作质感：<speed, weight, physical inertia, readable poses, stiffness/AI-feel controls>
风格边界：<what visual modes, medium drift, mood errors, or style misreadings to avoid; put text/logo/watermark execution limits under 生成要求>
画面与视觉连续性：<fixed characters, visible face/hair/body/wardrobe cues, product/food/material rules, scene anchor rules, no text policy>

动态时间切片：
(00-1s): <画面动作 + 运镜 + 角色对白口型/表情 + 同期声/环境声>
(1-3s): <画面动作 + 运镜 + 角色/产品互动 + 同期声 + SFX重点>
(3-6s): <材质/人物/产品/环境细节 + 机位变化 + 自然声音延续>
(6-10s): <情绪/卖点/叙事推进 + 运镜停顿或推进 + 表演反应 + 声音层次>
(10-13s): <转场准备/动作余韵/环境回应 + 同期声>
(13-15s): <桥接下一段或稳定收束 + SFX尾音>

生成要求：
稳定性：<identity, wardrobe, anatomy, face, material, no flicker>
音频：背景音乐不要生成；同期声请生成与画面动作自然同步的现场声、环境声、空间氛围声和可见材质互动声，不要只依据手动列出的音效；SFX只强调重点拟音/冲击音/转场音，不限制其他自然声音。
字幕与文字：不要生成字幕、caption、对白文字、烧录文字、随机logo、水印或未经授权IP标识；所有可读文字默认后期添加。
运动与画面：连续运动、真实物理惯性、清晰主体、稳定构图、自然表情或材质变化。
```

Do not split prompt content into separate `画面`, `运镜`, and `对白` sections for the same beat. Seedance performs better when the model sees what happens, how the camera moves, and who is speaking in the same time slice.
Do not repeat standalone `运镜与焦段` or `光线与风格` after the time slices; camera, lens, color, and lighting belong in `画面风格说明`.
The rule to avoid `Negative prompt` / `负面提示词` fields is for the workflow, not text to paste into the final prompt.

## Camera Language

Every 15-second segment should include motivated camera motion. Use movement to clarify story beats instead of adding motion as decoration:

- `quick push-in`: character introduction, object reveal, surprise reaction.
- `whip pan` / `snap pan`: handoff, throw/catch, sudden character entrance.
- `pass-by wipe`: leaves, wheat, steam, cloth, food, or props naturally hide a transition.
- `rack focus`: hand-to-object, object-to-face, texture/material reveal.
- `match cut`: food/process transformation, shape-to-shape transition.
- `controlled orbit`: object/process explanation or group table reveal.
- `crane reveal` / `slow pull-back`: ending, scale reveal, or emotional settling.
- `low-angle tracking`: running, travel, route, or entry energy.

Fast moves need a reason and should usually settle into a readable key frame. For cute animation, avoid shaky realism unless the segment explicitly needs impact or comedy.

## Camera Choreography Chain

This is a hard rule for Seedance 2.0 15-second prompts: do not write a segment that only says what appears in the picture. The segment must explain how the camera carries the beat. Think in camera/editing chains:

```text
entry texture or opening state -> acceleration or reveal move -> focus/hold for dialogue, food, material, or expression -> transition bridge
```

Write the chain inside the time slices, not as a disconnected `运镜` paragraph. The goal is to make Seedance understand not only "what happens", but how the director leads the viewer's eye.

Useful chain patterns:

- Character intro: steam macro opening -> quick push-in to mascot -> snap zoom or short hold for mouth cue -> whip tilt/down or pass-by wipe into the route.
- Food handoff: handheld orchard/table texture -> whip follow on the thrown object -> snap focus on the catch -> object wipe into the next environment.
- Food/material transformation: macro follow on grain/fruit/crystal -> match cut by shape or color -> rack focus from object to face -> controlled orbit or pull-back for the reveal.
- Pot/steam reveal: quick push-in to lid -> steam wipe -> rack focus to clean food detail -> vertical rise -> crane reveal into the next scene.
- Ending/title-safe staging: low-horizon pull-back -> slow arc to front -> characters hold or wave -> clean negative space for later title packaging.

Use fast pushes, whip pans, snap zooms, object wipes, match cuts, rack focus, orbit, and crane reveals where they support transitions or emotional lift. Pause or settle on dialogue, food texture, key expressions, and ending holds so the clip still feels directed rather than frantic.

## Style Lock And Drift Control

For recurring animated mascot shorts, repeat the style bible in every image and video prompt:

```text
高质感 3D 动画风，明亮卡通电影感，软萌角色，暖白蒸汽质感，图案化/手工模型感场景；不要真实摄影感，不要真实地点，不要纪实旅游素材感。
```

If the model drifts toward real scenes, strengthen the prompt with concrete replacements:

- Use `动画化布景`, `手工模型感`, `toy-like diorama`, `paper-cut set`, or `patterned stage`.
- Replace real scenery with symbolic bands, miniature sets, abstract silhouettes, or tabletop/stage layouts.
- Avoid real maps, administrative borders, place names, signs, route labels, skyline landmarks, logos, subtitles, and watermarks.
- If a generated frame is too realistic, regenerate it and mark the old candidate as superseded in the manifest instead of silently keeping both.

## Character And Dialogue Continuity

Fixed characters need compact but repeated identity anchors:

- Name and role.
- Hair/head feature.
- Signature outfit.
- Signature prop or food/material.
- Mouth cue only when speaking.

For mascot-led shorts, do not start with a group action if the audience has not met the characters. Introduce characters one by one first, then gather them into a team beat.

Dialogue and sound should be embedded inside the relevant time slice:

```text
(04-06s): 枣小甜从果篮旁跳入，镜头轻微 whip pan 后停到中近景；枣小甜做自我介绍口型，笑着挥手。同期声：果篮旁的轻微空间声与脚步软弹；SFX：果篮轻碰。
```

This keeps performance, camera, and visual action aligned for video generation and later dubbing.

## Food And Material Constraints

When a project uses regional foods or tactile materials, include stable positive constraints in both image and video prompts:

- Wheat must read as wheat, not rice.
- Winter jujubes should be small, round, glossy, and thin-skinned; not apples, cherries, or tomatoes.
- Cooked crab should show clean red shell and golden roe only; no gore, flowing roe, guts, or messy anatomy.
- Salt flats and salt crystals should be clean, white/blue, mirror-like, and not muddy.
- Steam should be warm and soft; avoid fantasy magic circles, cyber neon, and unreadable symbols.

## Segment Boundary Discipline

Each segment should end with either:

- a visual bridge into the next segment,
- a stable hold for editing,
- or a clean transition object such as steam, wheat, fruit, light, water, or a hand/object pass.

Do not mix unrelated places or products simply because there is still time left in the 15-second prompt. Continuity is usually stronger when a new concept starts in the next segment.

## Generation And File Discipline

After native image generation:

- Copy final selected images from the Codex generated image folder into both `storyboard/generated_frames/15s_segments/` and `最终交付/01_分镜图/15s_segments/`.
- Update `qa/metadata/image_generation_manifest.json`.
- Update `storyboard/segment_plan_15s.json` reference frame status and paths.
- Update `storyboard/generated_frames/15s_segments/generated_frames_manifest.json`.
- Run:

```bash
python3 skills/video-master/scripts/project_state.py <project_path> --write
python3 skills/video-master/scripts/validate_video_project.py <project_path>
```

Do not claim a frame is ready until the final project path exists and validation passes.

## Review Checklist

Before delivery, check:

- Each 15-second segment has internally motivated visual beats.
- Complex segments have enough reference images.
- Each time slice combines image, camera, dialogue mouth cue when applicable, natural synchronous sound, and SFX accents.
- Time slices are rhythm-driven, whole-second ranges and not mechanically equal unless a fixed beat grid is intentionally chosen.
- Dialogue is not visible text.
- No generated clip asks for background music.
- Style stays animation/model-like, not realistic footage.
- Recurring characters keep the same design.
- Food/material constraints are repeated where needed.
- Maps, signage, subtitles, logos, and readable labels are absent unless explicitly approved.
- Manifest and project state agree with actual files on disk.
