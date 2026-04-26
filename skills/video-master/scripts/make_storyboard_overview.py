#!/usr/bin/env python3
"""Create a storyboard overview for a video-master project.

The guaranteed output is an HTML contact sheet that only needs the generated
frame image files. If Pillow is installed, the script also writes a PNG contact
sheet, but HTML generation never depends on third-party packages.
"""

from __future__ import annotations

import argparse
import html
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from delivery_paths import FINAL_STORYBOARD_DIR, OVERVIEW_HTML, OVERVIEW_PNG, storyboard_frame_dir


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def list_frames(project: Path) -> list[Path]:
    frame_dir = storyboard_frame_dir(project)
    if not frame_dir.is_dir():
        raise FileNotFoundError(f"missing final storyboard directory: {frame_dir}")
    frames = sorted(path for path in frame_dir.iterdir() if path.suffix.lower() in IMAGE_EXTENSIONS)
    if not frames:
        raise FileNotFoundError(f"no storyboard frames found in: {frame_dir}")
    return frames


def rel(path: Path, base: Path) -> str:
    return path.relative_to(base).as_posix()


def write_html(project: Path, frames: list[Path]) -> Path:
    out = project / OVERVIEW_HTML
    out.parent.mkdir(parents=True, exist_ok=True)
    cards = []
    for frame in frames:
        shot_id = frame.stem
        src = html.escape(rel(frame, project))
        cards.append(
            f"""
      <figure class="card">
        <img src="{src}" alt="{html.escape(shot_id)} storyboard frame">
        <figcaption>{html.escape(shot_id)}</figcaption>
      </figure>"""
        )
    out.write_text(
        f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Storyboard Overview</title>
  <style>
    body {{
      margin: 0;
      padding: 32px;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
      background: #f7f3f0;
      color: #222;
    }}
    h1 {{ margin: 0 0 24px; font-size: 28px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 18px;
      align-items: start;
    }}
    .card {{
      margin: 0;
      padding: 10px;
      background: #fff;
      border: 1px solid #e6ded8;
      border-radius: 8px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }}
    img {{
      width: 100%;
      height: auto;
      display: block;
      border-radius: 4px;
      background: #eee;
    }}
    figcaption {{
      margin-top: 8px;
      font-size: 13px;
      color: #555;
      text-align: center;
    }}
  </style>
</head>
<body>
  <h1>Storyboard Overview</h1>
  <section class="grid">
{''.join(cards)}
  </section>
</body>
</html>
""",
        encoding="utf-8",
    )
    return out


def write_png_if_possible(project: Path, frames: list[Path]) -> Path | None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return None

    thumbs = []
    thumb_width = 260
    label_height = 34
    padding = 18
    columns = min(4, max(1, len(frames)))
    for frame in frames:
        with Image.open(frame) as image:
            image = image.convert("RGB")
            ratio = thumb_width / image.width
            thumb_height = int(image.height * ratio)
            image = image.resize((thumb_width, thumb_height))
            thumbs.append((frame.stem, image))
    max_height = max(image.height for _, image in thumbs)
    rows = (len(thumbs) + columns - 1) // columns
    canvas_width = columns * thumb_width + (columns + 1) * padding
    canvas_height = rows * (max_height + label_height) + (rows + 1) * padding
    canvas = Image.new("RGB", (canvas_width, canvas_height), "#f7f3f0")
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("Arial.ttf", 18)
    except Exception:
        font = ImageFont.load_default()
    for index, (shot_id, image) in enumerate(thumbs):
        row, col = divmod(index, columns)
        x = padding + col * (thumb_width + padding)
        y = padding + row * (max_height + label_height + padding)
        canvas.paste(image, (x, y))
        draw.text((x, y + image.height + 8), shot_id, fill="#333333", font=font)
    out = project / OVERVIEW_PNG
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create storyboard overview deliverables.")
    parser.add_argument("project", type=Path, help="Path to a video-master project directory")
    parser.add_argument("--copy-from-storyboard", action="store_true", help="Copy frames from storyboard/frames into 最终交付/01_分镜图 first")
    args = parser.parse_args(argv)

    project = args.project.resolve()
    if args.copy_from_storyboard:
        source = project / "storyboard" / "frames"
        target = project / FINAL_STORYBOARD_DIR
        target.mkdir(parents=True, exist_ok=True)
        for frame in sorted(source.glob("*")):
            if frame.suffix.lower() in IMAGE_EXTENSIONS:
                shutil.copy2(frame, target / frame.name)

    frames = list_frames(project)
    html_path = write_html(project, frames)
    png_path = write_png_if_possible(project, frames)
    print(f"HTML: {html_path}")
    if png_path:
        print(f"PNG: {png_path}")
    else:
        print("PNG: skipped (Pillow not installed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
