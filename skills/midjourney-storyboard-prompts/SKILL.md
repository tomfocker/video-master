---
name: midjourney-storyboard-prompts
description: Create reusable Midjourney 8.1 prompts for character design anchors, scene anchors, cinematic storyboard frames, battles, palace thrillers, and epic establishing shots. Use for MJ prompts, character consistency, --cref workflows, prompt repair, historical-realism locks, storyboard keyframes, reference images, or converting a script beat into a single still image.
---

# MJ 分镜提示词导演

将剧本、角色设定或单个镜头转成可直接复制的 Midjourney 8.1 英文提示词。优先建立可复用的角色与场景锚点，再生成单一叙事瞬间的分镜帧；不把整段视频情节硬塞进一张图。

除非用户明确批准，不要求生成可读文字、字幕、Logo、水印、地图或包装文案。不要直接模仿具体创作者或电影的独特风格；将需求转译为可观察的摄影、光线、材质、构图和节奏语言。

## 工作流

1. 提取视觉锁：时代与地域、真实度、主光方向、色温、材质、镜头语言、画幅、可见文字政策，以及角色/场景不可变化项。
2. 固定重复角色时，先生成中性背景的人设锚点；固定空间时，先生成 `SEGxx_SCENE` 宽景锚点。
3. 将每个分镜限制为一个决定性瞬间：只选一个主体、一个动作和一个镜头意图。
4. 需要同一人物连续出现时，复用已批准锚点，以 `--cref <URL> --cw <value>` 维持身份；不要每一帧重新发明人物。
5. 输出时先写用途、画幅、连续性约束，再给英文 MJ 提示词。需要进入视频时，另说明这张图在 Seedance 中充当首帧、过程锚点或尾帧。
6. 完成前读取 [references/midjourney-storyboards.md](references/midjourney-storyboards.md)，检查风格漂移、历史/现实边界、镜头可读性和奇幻化风险。

## 输出纪律

- 角色、人设、单帧剧情优先 2:3 或 16:9；极宽建立镜头使用 7:3，但将人物与核心动作置于中央 16:9 安全区。
- 先写能被画面验证的物体、动作和材质，后写情绪；少用无实物支撑的 “epic”“powerful”“cinematic”。
- 同一图不同时要求冲入、拔剑、爆炸、对峙、换装和反转；动作越多，肢体与叙事越不稳定。
- 历史题材先锁服饰工艺、武器和实用性；如发生玄幻化，先净化角色锚点，再降低风格化，而不是继续堆加风格词。
- 使用 `--style raw` 降低默认装饰。人物/分镜通常从 `--stylize 15-30` 起试，宏大建立镜头可试 `30-45`。

## 与 Video Master 协作

既可以独立生成 Midjourney 提示词，也可以作为 `$video-master` 的分镜静帧专项执行层。由 Video Master 调用时：

- 接收已锁定的画幅、视觉预设、角色/产品连续性、场景布局、参考资产角色和文字政策。
- 返回角色锚点、场景锚点或单帧提示词，并标明它们在视频流程中的 `SCENE`、`A-D`、首帧或尾帧角色。
- 不另建项目契约；由 Video Master 将获选提示词和图片写入 manifest、完成连续性检查并交付。

## 资源路由

- 角色、人设、`--cref`、历史写实与反奇幻：读取 `references/midjourney-storyboards.md` 的“角色锚点”“历史写实”部分。
- 场景、宫廷惊悚、战争或宏大镜头：读取同文件的对应模板。
- 需要与 Seedance 视频提示词衔接时：把获选 MJ 图定位为 `SCENE`、`A-D` 关键帧或首/尾帧，再交给 `seedance-storyboard-director`。
