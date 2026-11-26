"""Re-creates the sample course covers and lesson videos in seed_assets/.

Only needed if you edit seed_data.py. Requires Pillow and ffmpeg:
    pip install pillow
    python tools/make_seed_assets.py
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from seed_data import COURSES  # noqa: E402

PALETTES = {
    "html-css": ((234, 88, 12), (190, 24, 93)),
    "javascript": ((180, 83, 9), (120, 53, 15)),
    "python": ((29, 78, 216), (15, 118, 110)),
    "sql": ((15, 118, 110), (6, 78, 59)),
    "ui-design": ((147, 51, 234), (219, 39, 119)),
    "cloud": ((2, 132, 199), (49, 46, 129)),
}
SYMBOLS = {"html-css": "</>", "javascript": "JS", "python": "Py", "sql": "SQL",
           "ui-design": "UX", "cloud": "API"}


def font(size, bold=True):
    names = (["DejaVuSans-Bold.ttf", "arialbd.ttf"] if bold else ["DejaVuSans.ttf", "arial.ttf"])
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def gradient(width, height, start, end):
    small = Image.new("RGB", (2, 2))
    middle = tuple((a + b) // 2 for a, b in zip(start, end))
    small.putdata([start, middle, middle, end])
    return small.resize((width, height), Image.Resampling.BILINEAR)


def wrap(draw, text, face, width):
    lines, line = [], ""
    for word in text.split():
        candidate = f"{line} {word}".strip()
        if draw.textlength(candidate, font=face) > width and line:
            lines.append(line)
            line = word
        else:
            line = candidate
    return lines + [line]


def cover(course):
    image = gradient(800, 450, *PALETTES[course["slug"]]).convert("RGBA")
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.ellipse((500, -120, 920, 300), fill=(255, 255, 255, 28))
    draw.ellipse((600, 220, 860, 480), fill=(255, 255, 255, 20))
    draw.text((52, 40), SYMBOLS[course["slug"]], font=font(120), fill=(255, 255, 255, 235))
    face = font(46)
    y = 240
    for line in wrap(draw, course["title"], face, 680):
        draw.text((52, y), line, font=face, fill="white")
        y += 58
    draw.text((52, 390), course["category"].upper(), font=font(22),
              fill=(255, 255, 255, 200))
    return Image.alpha_composite(image, layer).convert("RGB")


def slide(course, heading, body, footer):
    image = gradient(960, 540, (15, 23, 42), PALETTES[course["slug"]][1])
    draw = ImageDraw.Draw(image)
    draw.rectangle((60, 70, 140, 78), fill=PALETTES[course["slug"]][0])
    y = 105
    for line in wrap(draw, heading, font(44), 840):
        draw.text((60, y), line, font=font(44), fill="white")
        y += 56
    y += 34
    for text in body:
        for line in wrap(draw, text, font(30, False), 800):
            draw.text((90, y), line, font=font(30, False), fill=(226, 232, 240))
            y += 44
        draw.ellipse((62, y - 30, 72, y - 20), fill=(250, 204, 21))
        y += 18
    draw.text((60, 488), footer, font=font(18, False), fill=(148, 163, 184))
    return image


def video(course, item, target):
    slides = [(item["title"], ["In this lesson: " + course["title"]])]
    slides += [(item["title"], item["points"][: n + 1]) for n in range(len(item["points"]))]
    slides.append(("Recap", item["points"]))
    seconds = 6
    with tempfile.TemporaryDirectory() as folder:
        listing = []
        for index, (heading, body) in enumerate(slides):
            path = Path(folder) / f"{index}.png"
            slide(course, heading, body, f"LearnSphere sample lesson  |  {index + 1} of "
                                         f"{len(slides)}  |  no audio").save(path)
            listing += [f"file '{path.as_posix()}'", f"duration {seconds}"]
        listing.append(f"file '{path.as_posix()}'")
        (Path(folder) / "list.txt").write_text("\n".join(listing))
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i",
             str(Path(folder) / "list.txt"), "-vf", "fps=10,format=yuv420p",
             "-t", str(seconds * len(slides)), "-c:v", "libx264", "-preset", "veryslow",
             "-tune", "stillimage", "-crf", "30", "-g", "20", "-movflags", "+faststart",
             str(target)], check=True)
    return seconds * len(slides)


def main():
    assets = ROOT / "seed_assets"
    for course in COURSES:
        cover(course).save(assets / "thumbnails" / f"{course['slug']}.jpg", quality=86)
        for item in course["lessons"]:
            name = f"{course['slug']}-{item['slug']}.mp4"
            print(name, video(course, item, assets / "videos" / name), "seconds")


if __name__ == "__main__":
    main()
