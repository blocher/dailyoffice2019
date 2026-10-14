"""Draw the podcast cover art: the app's gold Jerusalem cross on bound leather.

The leather follows the two editions of the Prayer Book: red for the
contemporary (ESV) feeds, green for the traditional-language (KJV) ones. A gold
border marks the section: none for the Daily Office, a rounded border for
Family Prayer, and a double border for the readings.

Writes ``podcasts/artwork/<slug>.jpg`` (3000 x 3000, the size Apple Podcasts
prefers) and ``<slug>-600.jpg`` for the landing page and ID3 tags. The art is
committed; re-run this only when the design or the catalog changes:

    python manage.py build_podcast_artwork
"""

from pathlib import Path

from django.core.management.base import BaseCommand
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from podcasts import catalog
from podcasts.builder import ARTWORK_DIR

# The app's own splash photo and Adobe Caslon Pro, the face of the 2019 BCP.
APP = Path(__file__).resolve().parents[4] / "app"
PHOTO = APP / "assets" / "splash.jpg"
FONTS = APP / "public" / "assets" / "fonts"
SIZE = 3000
MAX_BYTES = 500 * 1024  # directories reject covers over about 512 KB

# Leather colors by language: the photo's red for the 2019 Prayer Book, green
# for its traditional-language edition. (hue 0-1, saturation and value multipliers)
LEATHER_TONE = {catalog.CONTEMPORARY: None, catalog.TRADITIONAL: (0.38, 0.62, 0.62)}
# Gold borders by section, each rule as (inset, width, corner radius).
BORDERS = {
    "daily-office": [],
    "family": [(95, 24, 150)],
    "readings": [(80, 26, 0), (140, 10, 0)],
}
GOLD_LIGHT = (241, 226, 182)
GOLD_DARK = (196, 165, 98)


def font(name, size):
    return ImageFont.truetype(str(FONTS / f"ACaslonPro-{name}.woff"), size)


def cross_free_leather(photo):
    """The splash photo with its cross covered by plain leather.

    Three feathered strips, all from leather the cross never touches: above
    it, beside it (turned on its side), and below it.
    """
    leather = photo.copy()
    width, height = photo.size
    left, right = int(width * 0.26), int(width * 0.74)
    top, bottom = int(height * 0.26), int(height * 0.75)
    strip = right - left
    above = photo.crop((left, 0, right, int(height * 0.28)))
    beside = photo.crop((0, top, int(width * 0.26), top + strip)).rotate(90, expand=True)
    below = photo.crop((left, int(height * 0.73), right, height))
    placements = [
        (above, top - 30),
        (beside, (top + bottom - beside.height) // 2),
        (below, bottom + 30 - below.height),
    ]
    for patch, y in placements:
        mask = Image.new("L", patch.size, 0)
        ImageDraw.Draw(mask).rectangle((24, 24, patch.width - 24, patch.height - 24), fill=255)
        leather.paste(patch, (left, y), mask.filter(ImageFilter.GaussianBlur(12)))
    return leather


def cross_patch(photo):
    """The cross with a margin of leather, feathered so it sits in any leather."""
    width, height = photo.size
    box = (int(width * 0.272), int(height * 0.28), int(width * 0.728), int(height * 0.735))
    patch = photo.crop(box)
    mask = Image.new("L", patch.size, 0)
    inset = int(patch.width * 0.05)
    ImageDraw.Draw(mask).rectangle((inset, inset, patch.width - inset, patch.height - inset), fill=255)
    return patch, mask.filter(ImageFilter.GaussianBlur(inset // 2))


def recolor(image, tone):
    """Re-dye the leather, leaving the low-saturation gold alone."""
    if tone is None:
        return image
    hue, saturation, value = tone
    h, s, v = image.convert("HSV").split()
    weight = s.point(lambda x: max(0, min(255, (x - 70) * 4)))
    dyed = Image.merge(
        "HSV",
        (
            Image.new("L", image.size, int(hue * 255)),
            s.point(lambda x: int(x * saturation)),
            v.point(lambda x: int(x * value)),
        ),
    )
    return Image.composite(dyed.convert("RGB"), image, weight)


def gold_text(canvas, text, typeface, center_x, top, tracking=0):
    """Gold-foil lettering, stamped slightly into the leather."""
    draw = ImageDraw.Draw(canvas)
    width = text_width(draw, text, typeface, tracking)
    x = center_x - width / 2
    mask = Image.new("L", canvas.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    for char in text:
        mask_draw.text((x, top), char, font=typeface, fill=255)
        x += draw.textlength(char, font=typeface) + tracking
    gold_foil(canvas, mask)
    bbox = mask.getbbox()
    return bbox[3] if bbox else top


def gold_border(canvas, rules):
    """Gold rules around the edge of the cover, like a binder's fillets."""
    mask = Image.new("L", canvas.size, 0)
    draw = ImageDraw.Draw(mask)
    for inset, width, radius in rules:
        box = (inset, inset, SIZE - inset, SIZE - inset)
        draw.rounded_rectangle(box, radius=radius, outline=255, width=width)
    if rules:
        gold_foil(canvas, mask)


def gold_foil(canvas, mask):
    """Stamp gold foil into the leather wherever the mask is drawn."""
    shadow = Image.new("RGB", canvas.size, (40, 8, 8))
    canvas.paste(
        shadow, (6, 8), ImageChops.multiply(mask, Image.new("L", canvas.size, 150)).filter(ImageFilter.GaussianBlur(5))
    )
    gradient = Image.linear_gradient("L").resize(canvas.size)
    gold = Image.composite(
        Image.new("RGB", canvas.size, GOLD_DARK), Image.new("RGB", canvas.size, GOLD_LIGHT), gradient
    )
    canvas.paste(gold, (0, 0), mask)


def text_width(draw, text, typeface, tracking=0):
    return sum(draw.textlength(char, font=typeface) for char in text) + tracking * max(len(text) - 1, 0)


def fit(text, name, size, max_width):
    draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    while size > 60 and text_width(draw, text, font(name, size)) > max_width:
        size -= 6
    return font(name, size)


def split_title(title):
    """Long titles break before 'in'/'at' so each line is a phrase."""
    for marker in (" in the ", " at the ", " at "):
        if marker in title and len(title) > 16:
            first, rest = title.split(marker, 1)
            return [first, marker.strip() + " " + rest]
    return [title]


def small_caps(text):
    return text.upper()


def draw_cover(feed, photo):
    title = feed.title.replace(" (Traditional Language)", "")
    lines = split_title(title)
    traditional = feed.style == catalog.TRADITIONAL
    # Longer titles get a smaller cross so everything stays above the bottom
    # fifth, which players cover with progress bars and labels.
    compact = len(lines) > 1 or traditional
    cross_width = 860 if len(lines) > 1 and traditional else 980 if compact else 1150

    background = cross_free_leather(photo).resize((SIZE, SIZE), Image.LANCZOS)
    patch, mask = cross_patch(photo)
    patch_size = (cross_width, int(patch.height * cross_width / patch.width))
    patch, mask = patch.resize(patch_size, Image.LANCZOS), mask.resize(patch_size, Image.LANCZOS)
    background.paste(patch, ((SIZE - patch_size[0]) // 2, 170), mask)
    # The photo is enlarged about threefold: soften its grain so the cover
    # compresses well; the lettering is drawn sharp afterwards.
    canvas = recolor(background, LEATHER_TONE[feed.style]).filter(ImageFilter.GaussianBlur(2.4))
    gold_border(canvas, BORDERS[feed.group])

    group = {"daily-office": "The Daily Office", "family": "The Daily Office", "readings": "The Lectionary"}[
        feed.group
    ]
    y = 170 + patch_size[1] + 20
    y = gold_text(canvas, small_caps(group), font("Regular", 100), SIZE // 2, y, tracking=22) + 60
    title_size = 300 if len(lines) == 1 else 236
    for line in lines:
        typeface = fit(line, "Semibold", title_size, 2550)
        y = gold_text(canvas, line, typeface, SIZE // 2, y) + 40
    if traditional:
        y = gold_text(canvas, "Traditional Language", font("Italic", 140), SIZE // 2, y + 10) + 30
    draw = ImageDraw.Draw(canvas)
    rule_y = y + 70
    draw.line((SIZE // 2 - 260, rule_y, SIZE // 2 + 260, rule_y), fill=GOLD_DARK, width=6)
    y = gold_text(
        canvas, small_caps("The Book of Common Prayer 2019"), font("Regular", 80), SIZE // 2, rule_y + 55, 14
    )
    gold_text(canvas, "dailyoffice2019.com", font("Italic", 90), SIZE // 2, max(2700, y + 90))
    return canvas


def save_jpeg(image, path, max_bytes=None):
    for quality in (90, 86, 82, 78, 74, 70, 66, 62, 58, 55, 52, 49, 46):
        image.save(path, "JPEG", quality=quality, optimize=True, progressive=True)
        if not max_bytes or path.stat().st_size <= max_bytes:
            return quality
    return quality


class Command(BaseCommand):
    help = "Draw the 3000px and 600px cover art for every podcast feed."

    def add_arguments(self, parser):
        parser.add_argument("--feed", action="append", help="Only these feed slugs.")

    def handle(self, *args, **options):
        photo = Image.open(PHOTO).convert("RGB")
        ARTWORK_DIR.mkdir(exist_ok=True)
        feeds = [catalog.get_feed(slug) for slug in options["feed"]] if options["feed"] else catalog.FEEDS
        for feed in feeds:
            cover = draw_cover(feed, photo)
            path = ARTWORK_DIR / f"{feed.slug}.jpg"
            quality = save_jpeg(cover, path, MAX_BYTES)
            save_jpeg(cover.resize((600, 600), Image.LANCZOS), ARTWORK_DIR / f"{feed.slug}-600.jpg")
            self.stdout.write(f"{path.name}: {path.stat().st_size // 1024} KB at quality {quality}")
