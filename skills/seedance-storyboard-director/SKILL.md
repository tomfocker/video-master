---
name: seedance-storyboard-director
description: Create compact director-led storyboards and copy-ready Chinese Seedance 2.0 video prompts. Use for video briefs, shot lists, 15-second Seedance segments, scene-to-video prompts, product ads, micro-dramas, montages, one-take transitions, extensions, edits, motion posters, science explainers, fantasy action, or animation action.
---

# Seedance 分镜导演

把用户的创意简报转成可执行分镜与可直接粘贴的 Seedance 2.0 中文提示词。以一个清晰的导演模式组织每段，优先保证人物、产品、空间、风格和节奏连续，而不是堆砌视觉名词。

## 交付内容

根据用户需求，输出以下一项或多项：

- 导演方案：核心创意、受众情绪、时长、画幅、风格圣经、连续性锁定项。
- 分镜表：每镜的时长、画面动作、景别、运镜、声音、转场和参考图角色。
- Seedance 2.0 成片提示词：按镜头或 15 秒段落给出中文可复制块。

不要虚构产品功效、价格、医疗结论或版权授权。除非用户明确批准，文字、Logo、字幕、包装文案和标题一律交由后期；不要模仿在世创作者、受保护角色或真人肖像。

## 工作流

1. 提炼简报：确认目标、受众、总时长、画幅、目标模型、语言、风格、资产、可见文字政策和交付粒度。未提供时，做明确且可逆的合理假设。
2. 写一份风格圣经：固定场景/光线方向、角色或产品外观、材质、色彩、镜头语言、音频与文字政策。每个镜头重复必要的连续性锚点。
3. 选择一个主导演模式。读取 [references/director-patterns.md](references/director-patterns.md)，把其节奏语法改写为当前题材的具体动作；每段最多一个主模式。
4. 规划参考图链。需要重复空间时，先准备 `SEGxx_SCENE` 宽景锚点；再按开场、交接/转折、中段、收束准备 `A-D` 关键帧。单张图只表达一个关键状态，不要试图塞进整段剧情。若需要生成这些静帧，交给独立的 `midjourney-storyboard-prompts` 技能。
5. 写 Seedance 2.0 或 15 秒中文视频提示词时，读取 [references/seedance-2.md](references/seedance-2.md)，严格使用其模板。每个时间切片必须在同一句中交代画面动作、运镜、表演（如需要）、同期声和重点 SFX。
6. 在输出前执行 [references/qa.md](references/qa.md) 的检查；修复漂移、时长矛盾、无动机运镜与文字生成风险。

## 分镜写法

先给紧凑总表，再给每镜详情。每镜至少包含：`时长`、`叙事/卖点节拍`、`画面动作`、`景别与构图`、`运镜`、`光线/材质`、`人物/产品连续性`、`同期声与 SFX`、`转场/下一镜衔接`、`参考图`。

- 短镜头只放一个主动作；快动作后必须有可读停顿。
- 运镜必须服务于揭示、交接、情绪或空间关系：推进、甩镜、掠过遮挡、拉焦、匹配剪辑、环绕、升降或拉远。
- 多段视频的配乐留给后期。提示词要求自然现场声、环境声与可见材质声；只列重点 SFX，不要限制其他自然声音。
- 有口播时，用表情/口型/短表演提示，不粘贴长台词，更不要要求画内字幕。

## 与 Video Master 协作

既可以独立完成 Seedance 分镜任务，也可以作为 `$video-master` 的专项执行层。由 Video Master 调用时：

- 把其 `brief/spec_lock.md`、节奏图、角色/产品连续性锚点、参考图角色和音频政策视为上游契约。
- 返回分镜方案与 Seedance 提示词，不另建一套项目状态或改写上游锁定项。
- 让 Video Master 负责规范化落盘、跨阶段一致性、最终交付与项目级 QA。

## 资源路由

- 需要选择叙事与镜头节奏时：读取 `references/director-patterns.md`。
- 需要 Seedance 2.0、15 秒段、场景锚点、多图参考或可复制提示词时：读取 `references/seedance-2.md`。
- 完成前：读取 `references/qa.md`。
