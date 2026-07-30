# AI Animation Motion Grammar

Apply this grammar by default to concept, science, tutorial, and knowledge animations rendered with HyperFrames.

## Required rules

1. Create a meaningful visual change at least once every 2 seconds. Count camera arrival/departure, focus transfer, mask or connector growth, hierarchy change, data change, or a purposeful foreground/background motion. Do not count imperceptible noise alone.
2. Link adjacent beats spatially or semantically. Carry a shared object, line, light direction, color field, camera path, or composition anchor across the boundary.
3. Prefer slow point-to-point camera movement. Keep the current subject sharp and progressively soften distant nodes to create depth of field.
4. Do not use flat full-frame horizontal or vertical translation as the complete transition. Combine position with depth, scale, focus, parallax, masking, or a shared element.
5. Do not pop elements between positions or states. Use continuous interpolation with finite deterministic timelines. Allow subtle floating only when it does not compete with reading.

## Default thresholds

- `max_static_interval_seconds`: 2.0
- Camera travel: 0.8–1.4 seconds for a normal transition; longer only for an intentional establishing move.
- Camera rotation: normally within ±2 degrees.
- Consecutive camera scale ratio: normally no greater than 2.2.
- Focus settling time before dense reading: at least 0.25 seconds.
- Ambient float amplitude: normally 4–12 px at 1920×1080.
- Ambient float period: normally 1.8–4.0 seconds, finite and smoothly eased.
- Background blur: normally 3–12 px; preserve enough silhouette to maintain spatial continuity.
- Avoid simultaneous dense-text entrance during the highest camera velocity.

## Motion event contract

Each original spatial composition must declare ordered seconds in `data-motion-events`. Include `0`, every meaningful change, and the composition end. The largest adjacent gap must not exceed `max_static_interval_seconds`.

Example:

```html
<main
  data-composition-id="main"
  data-duration="7"
  data-motion-events="0,0.4,1.15,2.48,3.82,5.08,6.62,7"
  data-transition-grammar="spatial-linked"
  data-depth-of-field="near-sharp-far-soft"
>
```

Record the same policy in `animation/ai_animation_plan.json` under `motion_standard`. The plan declaration is the production lock; the composition attributes and timeline are the executable evidence.

## Review checklist

- Scrub the timeline in 0.5-second steps and verify no interval feels visually abandoned.
- Inspect the midpoint and arrival frame of every camera move.
- Confirm the viewer can infer where the camera came from and where it is going.
- Confirm the focused subject is sharp and distant nodes are visibly but not excessively softened.
- Confirm no panel behaves like a flat PowerPoint slide entering from an edge.
- Confirm all floating, parallax, and blur are deterministic under seeking and stop at the declared duration.
