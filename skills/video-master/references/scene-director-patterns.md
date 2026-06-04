# Scene Director Patterns

Use this reference after the main `video_mode` is selected when the brief fits a repeatable scene grammar such as product showcase, short drama, music beat montage, one-take transition, video extension, video edit, science visualization, fantasy action, or motion poster.

Scene director patterns are part of the director method library, but they are not full style templates. They define how a scene should be structured, staged, and paced. Combine them with:

- `style_templates/<template_id>/` for the full director archive when selected.
- `references/visual_style_presets.json` for the look card.
- `references/platform-and-model-profiles.md` for model-specific prompt syntax.

User-provided assets, `brief/spec_lock.md`, reference rights, subtitle policy, and the selected visual style always override a pattern.

## Shared Rules

- Select at most one primary scene pattern for a shot or segment. Secondary influences are allowed, but the final beat structure must stay readable.
- Convert the pattern into shot-specific beats or `动态时间切片`; do not paste a pattern as generic prompt text.
- Bind every referenced asset to a clear role before writing prompts: first frame, end frame, character, product, scene, motion, action, rhythm, synchronous sound/room tone, SFX accent, voice tone, or extension source.
- If the target workflow uses Seedance-style `@` handles, map roles explicitly, such as `@图片1 作为产品外观参考` or `@视频1 作为向后延长源视频`.
- Keep per-clip background music off unless the user explicitly wants one self-contained generated clip with model audio. For multi-clip projects, write model-facing no-BGM policy and keep music in post-production.
- Include natural synchronous sound / room tone when model audio is relevant, then add shot-specific SFX as accents. SFX cues should guide emphasis without forbidding other natural sounds.
- Treat captions, dialogue text, product claims, slogans, logos, UI labels, and title graphics as post-production unless `burned_subtitles_allowed` or exact generated on-screen text is explicitly approved.
- Avoid unlicensed celebrity likenesses, copyrighted characters, real brand marks, and recognizable creator-specific style imitation.

## Pattern Index

| Pattern | Use When | Core Director Grammar |
| ------- | -------- | --------------------- |
| `product_showcase` | Product ad, ecommerce proof, launch visual | Product continuity, material proof, category-appropriate reveal action |
| `live_commerce_spokesperson` | Host or model demonstrates a product | Hook, hand/product proof, mouth/performance cue, CTA hold |
| `short_drama_reversal` | Micro-drama, emotional conflict, punchline reversal | Conflict hook, prop evidence, close-up reaction, reversal |
| `fantasy_action` | Xianxia, fantasy combat, stylized power sequence | Stillness, acceleration, collision, particle bridge, hero pose |
| `science_visualization` | Medical, education, process explanation | System entry, cause/effect mechanism, before/after hold |
| `music_beat_montage` | MV, fashion switch, poster/card beat edit | Beat-mapped state changes and transition hits |
| `one_take_transition` | Continuous camera travel through multiple spaces | Start anchor, follow path, occluder transition, destination hold |
| `video_extension` | Extend an existing generated clip forward/backward | Boundary continuation, one new change, new boundary state |
| `video_edit` | Modify or replace part of an existing video | Preserve source timing/camera, change one target element |
| `motion_poster` | Dynamic poster, title-safe visual, graphic reveal | Fixed key visual, ordered reveals, clean title-safe hold |
| `animation_action` | Anime/stylized character action | Clear pose, anticipation, action arc, impact, readable hold |

## `product_showcase`

Use for products, packaging, food, apparel, devices, or objects that must remain identifiable.

Required locks:

- Product name or neutral descriptor, approved logo/text policy, exact color/material, shape, scale, and allowed claims.
- Product reference image role.
- Product category and showcase variant when the product has a strong category grammar.
- If exact text/logo is not approved, instruct no readable text and reserve packaging for post-production.

Rhythm pattern:

```text
entry material or hero silhouette -> macro texture/proof -> 360 turn, split, assembly, pour, wear, or use action -> clean hero hold/CTA-safe ending
```

Variant selection:

| Variant | Best For | Director Moves |
| ------- | -------- | -------------- |
| `soft_playful_assembly` | Toys, family products, playful accessories | Magnetic assembly, toy-scale tracking, color sorting, friendly motion, safe rounded detail |
| `tech_precision_exploded_view` | Shavers, electronics, tools, smart devices, automotive parts | 3D exploded view, floating layers, precision cutaway, scanning light, magnetic reassembly |
| `beauty_lifestyle_application` | Skincare, fragrance, cosmetics, personal care | Texture macro, hand application, skin-safe glow, bottle light sweep, clean vanity hero |
| `food_material_appetite` | Food, beverage, ingredients, kitchen products | Pour, slice, steam, crunch, condensation, ingredient cascade, appetite hero |
| `fashion_fit_switch` | Apparel, shoes, bags, accessories | Outfit beat switch, fabric motion, walk-in reveal, detail insert, full-look hold |
| `premium_static_hero` | Luxury goods, packaging, minimalist brand objects | Slow light sweep, restrained turntable, reflection control, negative space, quiet hold |

Selection rules:

- Use `tech_precision_exploded_view` only when the product benefits from showing internal engineering, parts, blades, circuits, sensors, motors, or precision construction.
- Use `soft_playful_assembly` for children's toys and family products; make decomposition feel playful and safe rather than industrial or clinical.
- Use `beauty_lifestyle_application` when the product proof is tactile use, glow, texture, fragrance mood, or bathroom/vanity ritual.
- Use `food_material_appetite` when taste, freshness, heat, cold, liquid, crunch, or ingredient transformation is the memory anchor.
- Use `fashion_fit_switch` when the product must be seen on-body or in a complete styling context.
- Use `premium_static_hero` when elegance, restraint, packaging shape, and negative space matter more than mechanical action.
- If no variant clearly fits, keep a simpler product hero sequence instead of forcing a 3D exploded view.

Prompt cues:

- Name material physics: condensation, powder, fabric stretch, liquid flow, glass reflection, metal glint, soft packaging flex.
- Keep one main product transformation per 4-6 seconds.
- Add natural product/tabletop/room sound first, then SFX accents such as click, cap twist, fabric sweep, pour, spin stop, magnetic snap, UI tap, or product impact.
- For `tech_precision_exploded_view`, show only legible product-relevant parts and reassemble before the hero hold.
- For `soft_playful_assembly`, use rounded pieces, gentle magnetic motion, bright color grouping, and child-safe tabletop staging.

Avoid:

- Unsupported ingredient, medical, price, or performance claims.
- Overloading one short clip with every product angle and every benefit.
- Using exploded-view mechanics for soft, lifestyle, food, fashion, or luxury products when they would feel unnatural.

## `live_commerce_spokesperson`

Use when a host, model, or character visibly handles a product and speaks or performs a sales beat.

Required locks:

- Character/host authority and likeness safety.
- Product handling action, allowed selling points, CTA wording, copy language, and subtitle policy.
- External VO or TTS stays in `audio/`; final prompts should use mouth/performance cues instead of pasting long VO lines.

Rhythm pattern:

```text
fast product hook -> hand/face/product proof -> close-up use detail -> reaction/benefit beat -> CTA-safe hold
```

Prompt cues:

- Describe mouth movement only for short visible speech cues.
- Alternate product close-up, hand action, side profile, and reaction rather than holding one talking-head frame.
- Keep product contact physically plausible: apply, open, spray, pour, press, compare, wipe, fold, or wear.

Avoid:

- Uploading or requesting restricted realistic human face references.
- Asking the video model to generate burned subtitles by default.

## `short_drama_reversal`

Use for micro-drama, short play, comedy setup, emotional conflict, or a reversal beat.

Required locks:

- Character IDs, wardrobe, relationship, location, emotional starting state, and turn/reveal object.
- Dialogue source in `script/` and `audio/`; final prompt uses short mouth cues and emotion cues.

Rhythm pattern:

```text
conflict hook -> evidence/prop or gesture escalation -> close-up reaction -> reversal line/performance cue -> freeze or exit beat
```

Prompt cues:

- Use close-ups for eyes, hands, contract/document/phone, door, cup, ring, or other reveal props.
- Write emotion transitions explicitly: calm to shock, anger to fear, confidence to collapse.
- SFX accents can include paper tear, phone buzz, footsteps, glass tap, rain, crowd gasp, or silence hit.

Avoid:

- Dense long dialogue in a short clip.
- Demanding lip sync and readable subtitles unless explicitly approved for model text.

## `fantasy_action`

Use for xianxia, martial arts, fantasy battle, magic transformation, mythic reveal, or stylized combat.

Required locks:

- Original character design, weapon/prop rules, energy color, costume, allowed violence level, and environment.
- No copyrighted characters or direct imitation of named IP unless the user provides rights and the request is allowed.

Rhythm pattern:

```text
stillness/charge -> acceleration or first strike -> interaction/collision -> particle/energy transition -> readable finishing pose
```

Prompt cues:

- Give weapons and effects stable colors, shapes, and trajectories.
- For high speed, alternate one fast move with one readable hold.
- Use transition logic such as flame ring to red feathers, ice shard to light streak, dust wipe, robe pass-by, or sword flare.
- SFX accents can include blade ring, cloth snap, stone crack, energy pulse, impact bass, breath, or wind.

Avoid:

- Too many characters, powers, locations, and transformations in one 4-6 second clip.
- Gore-heavy detail when a stylized impact is enough.

## `science_visualization`

Use for education, science, medical explainers, product mechanism, industrial process, or invisible-system visualization.

Required locks:

- Approved factual claims, audience level, visualization metaphor, and compliance boundaries.
- Whether the scene is realistic CGI, diagrammatic, translucent, macro, cross-section, or stylized.

Rhythm pattern:

```text
establish system -> camera enters mechanism -> visible cause/effect change -> before/after contrast -> stable explanatory hold
```

Prompt cues:

- Use clean labels only in post-production unless exact generated text is approved.
- Describe causal motion: particles enter, fluid thickens, component opens, heat spreads, material bonds, pressure changes.
- SFX accents can include subtle hum, pulse, liquid movement, mechanical click, UI beep, or low transition hit.

Avoid:

- Unsupported medical claims or fear-based exaggeration.
- Text-heavy diagrams generated inside the video frame.

## `music_beat_montage`

Use for MV, fashion outfit switch, travel montage, card/poster reveal, or visual changes synchronized to a rhythm reference.

Required locks:

- Whether an audio/video reference is a rhythm reference only, or whether the user explicitly wants model-generated audio for one self-contained clip.
- Ordered reference image roles, beat count, transition language, and style consistency.

Rhythm pattern:

```text
beat 1 hero state -> beat 2 cut/switch -> beat 3 camera or outfit change -> beat 4 payoff hold
```

Prompt cues:

- Map each reference image to a beat or state.
- Use simple transition types: hard cut, flash cut, match pose, whip pan, object wipe, freeze-pop, or light sweep.
- SFX accents can include whoosh, flash pop, cloth snap, step hit, camera shutter, or impact tick.

Avoid:

- Vague `follow the music` wording without beat/state mapping.
- Letting the video model create unrelated per-clip music when the project will be edited across multiple clips.

## `one_take_transition`

Use for continuous tracking, travel through multiple spaces, first-person movement, showroom tour, food/process travel, or one-shot story reveal.

Required locks:

- Start frame, end frame, ordered reference scenes, no-cut rule, transition occluders, and final hold.
- If multiple references are used, assign each to a space, object, or destination.

Rhythm pattern:

```text
first frame anchor -> follow subject/object -> occluder or pass-by transition -> next space reveal -> end-frame hold
```

Prompt cues:

- Use occluders that make physical sense: wall edge, cloth, door, steam, vehicle pass, hand, product, shadow, light flare.
- Keep the camera path explainable and continuous.
- SFX accents can include footsteps, room tone change, door slide, cloth pass, breath, vehicle pass, or soft transition whoosh.

Avoid:

- Saying `one take` while also requesting hard cuts.
- Jumping between unrelated places without an occluder or camera path.

## `video_extension`

Use when an existing clip should continue forward or be extended backward.

Required locks:

- Source video role, exact ending or beginning state, extension direction, new duration, and continuity constraints.
- If extending forward, the first beat must start from the previous end frame. If extending backward, the last beat must arrive at the existing beginning.

Rhythm pattern:

```text
source state continuation -> one new action/change -> detail or reaction -> next ending state for another extension or edit
```

Prompt cues:

- For Seedance-style extension workflows, write `将 @视频1 向后延长 <seconds>` or `将 @视频1 向前延长 <seconds>` and keep the selected generation length equal to the new material duration.
- Record the segment handoff in the storyboard plan when building a multi-segment film.

Avoid:

- Retelling the whole previous clip instead of continuing from its boundary state.

## `video_edit`

Use when the user wants to preserve most of an uploaded video while changing a specific element, role, mood, action, prop, or story outcome.

Required locks:

- Source video role, preserved elements, changed elements, target replacement asset, allowed degree of rewrite, and rights/safety boundaries.

Rhythm pattern:

```text
preserve source camera/action -> introduce changed element -> keep timing and spatial relation -> revised payoff
```

Prompt cues:

- Say what must stay unchanged: camera path, background, lighting, action timing, body motion, or prop trajectory.
- Say what changes in one clear clause: replace subject, change costume/hair color, add object, change reaction, alter ending.
- SFX should preserve source-style sound unless the change needs a new sound cue.

Avoid:

- Asking for protected character replacement, real-person deception, or brand spoofing without rights.

## `motion_poster`

Use for poster-to-video, title-safe visual loops, product key visual motion, event graphics, or fixed-camera element reveals.

Required locks:

- Poster/grid/source image role, element order, camera policy, text policy, and final safe area.
- Exact text should be rendered in post-production or title packaging unless generated text is explicitly approved.

Rhythm pattern:

```text
fixed key visual -> ordered element reveal -> subtle depth/light/material motion -> clean title-safe hold
```

Prompt cues:

- Use fixed camera or very restrained parallax when the poster layout must remain legible.
- Animate shapes, product light, fabric, particles, paper layers, glow sweeps, or framed image panels.
- SFX accents can include soft pop, paper slide, light sweep, camera shutter, UI tick, or logo-safe hit.

Avoid:

- Asking the video model to accurately typeset dense copy.

## `animation_action`

Use for anime, stylized 2D/3D characters, mascot action, or animation tests.

Required locks:

- Character bible, style preset, animation medium, body proportions, costume, expression range, and action phases.

Rhythm pattern:

```text
clear pose -> anticipation -> action arc -> impact/reaction -> held readable pose
```

Prompt cues:

- Anchor silhouette, face, hair, costume, and prop before motion.
- Keep action phases simple and readable; one major motion per short slice.
- For style consistency, repeat the visual style bible in image and video prompts.
- SFX accents can include footstep bounce, cloth swish, impact pop, magic pulse, or environment response.

Avoid:

- Mixing exact copyrighted characters or franchises into the final prompt.
- Letting style words fight each other, such as photoreal documentary plus flat anime plus clay render in the same clip.
