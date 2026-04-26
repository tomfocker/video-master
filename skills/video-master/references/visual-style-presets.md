# Visual Style Presets

Use these presets before writing storyboard image prompts. They are lightweight look cards: they lock medium, realism, art direction, palette, lighting, texture, and camera language. They do not replace full style templates in `style_templates/`; full templates also control rhythm, editing craft, sound policy, and director method.

## Workflow

1. During Production Lock, ask the user to choose one visual style preset, provide a custom visual style, or use reference assets to derive the style.
2. Record the choice in `brief/spec_lock.md` under `visual_style`.
3. If the user provides reference images or videos, apply the reference-style analysis as an override on top of the preset. Do not copy protected subjects, brands, exact scenes, or creator-specific style.
4. Before generating storyboard frames, copy the selected preset's `storyboard_prompt_rules` into `prompts/storyboard_image_prompts.md`.
5. Before writing final video prompts, copy the selected preset's `video_prompt_rules` into `prompts/video_prompts.md`.

## Preset Cards

| ID | User-facing card | Best for |
| --- | --- | --- |
| `imax_70mm_realism` | IMAX 70mm Cinematic Realism | premium brand films, travel, automotive, documentary realism |
| `photoreal_commercial` | Photoreal Commercial | products, ecommerce, beauty, food, consumer tech |
| `eastern_fantasy_3d` | Eastern Fantasy 3D | cultural stories, tourism, fantasy brand films |
| `hyperreal_3d_render` | Hyperreal 3D Render | tech objects, architecture, industrial design, product launches |
| `graphic_2d_editorial` | Graphic 2D Editorial | explainers, education, data stories, brand manifestos |
| `soft_storybook_2d` | Soft Storybook 2D | family-safe stories, public welfare, warm emotional shorts |
| `anime_cinematic_light` | Anime Cinematic Light | youth stories, music videos, romantic travel, campus films |
| `noir_gothic` | Noir Gothic | fashion, mystery, nightlife, dramatic teasers |
| `future_tech_clean` | Future Tech Clean | AI/software, consumer electronics, enterprise launches |

## Selection Rules

- Prefer one primary preset. If the user wants a blend, name one primary preset and record the blend as `visual_style_overrides`.
- Do not present protected artist or studio imitation as a preset. Use descriptive traits instead.
- Preset prompts may mention medium and cinematography language, but must not ask for a specific living artist's style, exact studio look, copyrighted character, brand mark, or source scene.
- Reference assets can refine palette, lighting, framing, and packaging behavior, but user-owned project content always wins over the preset.
- When no style is chosen, make a conservative recommendation from the brief and mark it as `assumed` in `visual_style_lock`.

## Spec Lock Fields

```markdown
## visual_style
- visual_style_lock: confirmed | assumed | reference-derived | custom
- visual_style_preset_id: imax_70mm_realism | photoreal_commercial | eastern_fantasy_3d | hyperreal_3d_render | graphic_2d_editorial | soft_storybook_2d | anime_cinematic_light | noir_gothic | future_tech_clean | custom
- visual_style_preset_name:
- medium:
- realism_level:
- art_direction:
- color_palette:
- lighting:
- texture:
- camera_language:
- storyboard_prompt_rules:
- video_prompt_rules:
- visual_style_overrides:
```

## Example Production Lock Wording

```markdown
Visual style recommendation: `photoreal_commercial`
Why: product-led short video needs clean product readability, premium lighting, and fast visual scanning.
Alternatives: `imax_70mm_realism` for a more cinematic brand-film feeling; `future_tech_clean` for a more technology-led launch.
Please confirm the visual style before storyboard image prompts are generated.
```
