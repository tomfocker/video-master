# Prompt Rules

## 先写资产图谱

不要先写“一张完整的剪贴画视频画面”。每个段落先列出：

```text
BG：背景底板（材质、色彩、标题安全区、活动空间）
CHAR：角色/讲解者（姿态、轮廓、比例、可动范围）
PROP：关键道具/概念物（单一功能）
WINDOW：实拍或插画场景窗口（进入/退出时机）
FX：小型情绪或强调特效（仅一类）
TYPE_SAFE：后期文字、标签、图表安全区
```

优先逐个生成 `BG`、`CHAR`、`PROP`、`WINDOW`。只有需要决定组合关系时才生成少量总览图；总览图不能替代可单独抠像的资产。

## Storyboard Image Prompts

- 背景底板必须写明：`modular paper-cut collage packaging, clean reusable background plate, tactile material, blank title-safe area, no main character, no readable text`。
- 独立元素必须写明：`isolated cutout element, clear silhouette, consistent outline and soft shadow, neutral extraction background, no text`。
- 组合图必须写明：`layered 2.5D collage, independent elements with readable spacing, one focal point, limited accent palette, no readable text`。
- 为同一项目锁定边缘规则、阴影方向、纸张/材质、颜色数量、角色比例和镜头视角；实拍窗口保留真实质感。
- 不得生成准确文字、数字、Logo、新闻截图、文件内容或图表；这些内容后期制作。

## Video Prompts

每个视频提示词必须包含：

- 画面
- 动作
- 镜头
- 声音/口播
- 背景音乐
- SFX 音效
- 画面文字策略

声音/口播写法：

```text
声音/口播：外部画外音，后期添加；本片段不生成对白或口播台词。
```

背景音乐写法：

```text
背景音乐：不要生成背景音乐；整片音乐后期统一处理。
```

文字写法：

```text
画面文字策略：预留标题、标签和字幕安全区；不要生成字幕、caption、对白文字、可读数字、logo 或水印，精确文字由后期包装添加。
```

在动作中写明“哪个元素在什么层级、以何种动作进入或退出”，不要笼统写“有剪贴画动效”。每镜只强调一到两种与可见材质/对象匹配的 SFX。不要使用 `负面提示词` 字段。
