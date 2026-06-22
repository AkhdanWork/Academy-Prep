from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "assets" / "academy-prep-logo.png"
SIZE = 512


def interpolate(start, end, progress):
    return tuple(
        round(start[index] + (end[index] - start[index]) * progress)
        for index in range(3)
    )


def generate_logo():
    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    gradient = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    gradient_draw = ImageDraw.Draw(gradient)
    top = (255, 122, 114)
    bottom = (237, 62, 122)
    for y in range(SIZE):
        color = interpolate(top, bottom, y / (SIZE - 1))
        gradient_draw.line((0, y, SIZE, y), fill=(*color, 255))

    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle((32, 28, 480, 476), radius=132, fill=255)
    canvas.paste(gradient, (0, 0), mask)

    draw = ImageDraw.Draw(canvas)
    white = (255, 255, 255, 255)
    navy = (23, 32, 45, 255)
    gold = (255, 214, 107, 255)

    draw.line([(218, 164), (128, 256), (218, 348)], fill=white, width=42, joint="curve")
    draw.line([(294, 164), (384, 256), (294, 348)], fill=white, width=42, joint="curve")
    draw.line([(294, 122), (218, 390)], fill=navy, width=35)

    for x, y in ((218, 164), (128, 256), (218, 348), (294, 164), (384, 256), (294, 348)):
        draw.ellipse((x - 21, y - 21, x + 21, y + 21), fill=white)
    draw.ellipse((386 - 18, 116 - 18, 386 + 18, 116 + 18), fill=gold)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUTPUT_PATH, optimize=True)
    print(OUTPUT_PATH)


if __name__ == "__main__":
    generate_logo()
