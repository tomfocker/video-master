# Midjourney 8.1：角色、分镜与场景锚点

## 目录

1. 提示词骨架与参数
2. 角色一致性
3. 历史写实与反奇幻
4. 场景、分镜、战争与宏大场景模板
5. 输出格式与检查

## 1. 提示词骨架与参数

按“镜头 → 主体与动作 → 外观/道具 → 环境层次 → 光线/材质 → 真实度 → 参数”写。一个提示词表达一个可见瞬间：

```text
[Framing and medium]. [One clear subject] doing [one clear action],
[locked appearance / wardrobe / prop], [time and location].
Foreground: [occluder or scale cue]. Middle ground: [main action]. Background: [threat or geography].
[Physical materials and state]. [Lighting, palette and atmosphere].
[Grounded cinematography and texture].
--ar <ratio> --v 8.1 --style raw --stylize <15-45>
```

- 人设图、人物细节、剧情帧：`--stylize 15-30`；宏大景别：`30-45`。
- `--style raw` 用于抑制默认的装饰化美术，不替代对服装、材质、动作和禁用元素的明确描述。
- 角色锚点常用 `--ar 2:3`，剧情帧常用 `--ar 16:9`，极宽建立镜头常用 `--ar 7:3`。
- 没有可靠的“负面提示词”流程；首先用正向具体描述修正。只有固定错误反复出现时，再使用极短 `--no`。

## 2. 角色一致性

### 先做角色锚点

```text
Cinematic character design sheet, three-quarter full-body portrait.
[CHARACTER_ID], [age range and social role], [face, hair, beard, body],
wearing [period-appropriate practical clothing and armor], carrying [plain prop],
standing in a neutral dim stone corridor, no battle action, no crowd.
Restrained historical realism, practical materials, natural proportions, muted earth-and-indigo palette,
soft overcast side light, fine film grain, no readable text, no symbols.
--ar 2:3 --v 8.1 --style raw --stylize 20
```

锁定并反复使用：角色 ID、年龄段、脸型与胡须、发型、体态、内外服色、甲胄/道具、可变化项和禁变项。先让用户批准锚点，再进入雨、火、战场或强情绪等戏剧环境。

### 使用批准参考图

```text
<SHOT PROMPT> --cref <approved-character-image-URL> --cw 80 --ar 16:9 --v 8.1 --style raw --stylize 25
```

`--cw 80` 是身份稳定的起点。脸与服装漂移时提高；构图被参考图限制时降低。只在用户提供或批准的角色图可作为参照时使用 `--cref`。

## 3. 历史写实与反奇幻

历史角色先写时代工艺和实用性，再写电影氛围。不要堆叠“银白甲、白披风、白发、羽饰、圣光、火焰风暴、神性英雄”等词，它们会把写实人物推向玄幻角色。

**晚东汉/三国通用写实锁：**

```text
late Eastern Han / Three Kingdoms historical realism, practical dark iron lamellar armor,
weathered hemp and silk garments, plain wood-shaft weapons, worn leather straps,
mud, rain, soot, no fantasy ornament, no glowing effects, no magical energy,
no white-silver ceremonial armor, no cape, no plume
```

**赵云写实锚点示例：**

```text
Cinematic character design sheet, three-quarter full-body portrait. Zhao Yun, a late-50s practical cavalry commander,
black hair greying only at the temples, short dark-grey beard, lean and battle-worn face,
wearing utilitarian dark iron lamellar armor over a faded indigo hemp tunic, worn leather straps,
holding a plain wooden-shaft spear. Standing in a neutral dim stone corridor, no battle action, no crowd.
Late Eastern Han historical realism, natural proportions, wet metal and coarse cloth texture, muted earth-and-indigo palette,
soft overcast side light, fine film grain, no fantasy ornament, no glowing effects, no cape, no plume, no readable text.
--ar 2:3 --v 8.1 --style raw --stylize 20
```

**修复顺序：**删去渲染器名、超高分辨率、物理公式和互相冲突的风格词；补回具体的甲胄、衣料、武器、发色；把角色锚点改回无雨无火的中性背景；最后才在分镜里加入戏剧光线。固定错误可补 `--no glowing armor, cape, plume`。

## 4. 场景、分镜、战争与宏大场景模板

### 场景锚点

```text
Cinematic epic establishing shot, [time], [SEGMENT LOCATION].
A complete, believable action space: [foreground terrain], [middle-ground route / structure / people start area],
[background scale cue]. [Recurring props and their fixed positions].
[Weather and physical traces]. [Key color-temperature contrast and light direction].
Grounded historical realism, tactile [stone / wet metal / silk / mud / smoke] textures,
central 16:9 action-safe composition, no readable text, no logo, no watermark.
--ar 7:3 --v 8.1 --style raw --stylize 35
```

明确出入口、人物起始区、道具位置、主光方向与前中后景。后续分镜沿用它们，不得让城门、战船或火光方向漂移。

### 剧情分镜帧

```text
Cinematic [wide / medium / close] film still, [time], [specific place].
[CHARACTER_ID] [one decisive action], [locked wardrobe / prop / physical state].
Foreground: [occluder or reaction]. Middle ground: [main action]. Background: [scale or threat].
[Camera angle and composition]. [Motivated practical light].
Grounded historical political thriller, wet stone, iron, silk and smoke textures, restrained color palette,
high-contrast warm firelight against cold storm-blue night, fine film grain,
no readable text, no logo, no watermark.
--ar 16:9 --v 8.1 --style raw --stylize 25
```

### 两军交战

```text
Cinematic wide battlefield frame, [time], [specific battlefield].
Two late Eastern Han armies collide at one narrow point: shield line braced in the muddy foreground,
spearmen pushing from the middle ground, loose horses and torn banners in the smoky distance.
No individual superhero pose; formations strain, stumble and regroup under real weight and fear.
Rain darkens practical iron lamellar armor, mud splashes on worn cloth, scattered torchlight and distant fires
cast warm orange highlights against a cold blue-black storm night. Low ground-level camera, readable layered depth,
historical realism, tactile rain, mud, smoke and metal, fine film grain, no fantasy effects, no readable text.
--ar 16:9 --v 8.1 --style raw --stylize 35
```

用“局部碰撞 + 队列深度”表达规模，而不是让每个士兵都摆英雄姿势。用远处军阵、火线、战船、城墙或连续旗线补规模。

### 宫廷惊悚

```text
Cinematic medium shot, night, inside [palace / fortress hall].
[CHARACTER_ID] enters or confronts [other character / object] at the threshold, one hand on [prop],
rainwater and soot visible on practical clothing. Blurred guards hold tension in the foreground;
a long shadowed corridor recedes behind the subject.
Cold rain light spills through the door while a single warm brazier defines wet metal, stone and silk textures.
Grounded historical political thriller, restrained performance, chiaroscuro, fine film grain,
no fantasy ornament, no readable text, no logo, no watermark.
--ar 16:9 --v 8.1 --style raw --stylize 22
```

### 宏大建立镜头

```text
Cinematic epic ultra-wide establishing shot, [time], [location].
[Main geographic feature] dominates the frame; [foreground human scale cue] leads toward [middle-ground crisis],
while [distant force / city / fleet / weather front] fills the horizon.
[One clear event] changes the landscape: [fireline / flood / army movement / collapsing bridge].
Natural large-scale physics, layered smoke and rain, wet reflective surfaces, tiny believable human silhouettes,
warm disaster light against a cold night sky, grounded historical epic, restrained palette, fine film grain,
central action-safe composition, no readable text, no logo, no watermark.
--ar 7:3 --v 8.1 --style raw --stylize 40
```

只保留一个地理主语和一个灾难事件；以前景断旗、船头、城墙或少量人物建立尺度。

## 5. 输出格式与检查

```markdown
### F03｜<镜头名>

用途：<角色锚点 / 场景锚点 / 分镜关键帧>
画幅：<2:3 / 16:9 / 7:3>
连续性：<角色 ID、地点锚点、不可变化项；如有，附 cref 用法>

```text
<English MJ prompt>
```
```

交付前确认：主体、动作、空间和镜头意图各只有一个主焦点；角色锚点与后续衣着/道具一致；战场具有真实重量与比例；历史场景没有魔法化符号；图中没有要求可读文字；最终帧可被清晰标注为 Seedance 的首帧、过程锚点或尾帧。
