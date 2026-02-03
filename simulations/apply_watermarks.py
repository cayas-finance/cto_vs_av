import os

from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

# Configuration
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOGO_REL_PATH = "assets/logo_cayas/png/black/logo-cayas-HD-1920.png"


# Polices
FONT_PATH = "Outfit/static/Outfit-Regular.ttf"

TARGET_IMAGES = [
    "images/heatmap_tipping_point_3pct.png",
    "images/heatmap_tipping_point_5pct.png",
    "images/heatmap_tipping_point.png",
    "images/heatmap_siblings_5pct.png",
    "images/heatmap_accident.png",
    "images/heatmap_rente.png",
    "images/heatmap_rente_senior.png",
    "images/stochastic_dual_scenario.png",
    "images/complex_portfolio_results.png",
    "images/heatmap_low_fee_3pct.png",
    "images/heatmap_low_fee_5pct.png",
    "images/heatmap_low_fee_8pct.png",
]

SOURCE_TEXT = "Source: G. Flament, Comparatif CTO vs AV, Cayas.fr"

TEXT_COLOR = (50, 50, 50, 255)
LOGO_WIDTH_PCT = 0.18
PADDING_PCT = 0.02
FOOTER_HEIGHT_PCT = 0.05
HEADER_HEIGHT_PCT = 0.05
LOGO_OUTLINE_PX = 6
FORCE_REAPPLY = True
MIN_FONT_SIZE = 20
MAX_FONT_SIZE = 100


def get_font(is_italic, size):
    font_path = os.path.join(PROJECT_ROOT, FONT_PATH)
    try:
        return ImageFont.truetype(font_path, size)
    except Exception as e:
        print(f"Error loading font {font_path}: {e}")
        return ImageFont.load_default()


def apply_watermark():
    logo_path = os.path.join(PROJECT_ROOT, LOGO_REL_PATH)

    if not os.path.exists(logo_path):
        print(f"Error: Logo not found at {logo_path}")
        return

    print(f"Using logo: {logo_path}")

    for img_rel_path in TARGET_IMAGES:
        img_full_path = os.path.join(PROJECT_ROOT, img_rel_path)

        if not os.path.exists(img_full_path):
            print(f"Warning: Image not found: {img_full_path}")
            continue

        try:
            with Image.open(img_full_path) as base_image:
                if base_image.info.get("watermarked") == "1" and not FORCE_REAPPLY:
                    print(f"Skipping already watermarked: {img_rel_path}")
                    continue
                original_image = base_image.convert("RGBA")
                width, height = original_image.size

                # --- 1. Dimensions ---
                header_height = int(height * HEADER_HEIGHT_PCT)
                if header_height < 60:
                    header_height = 60

                footer_height = int(height * FOOTER_HEIGHT_PCT)
                if footer_height < 45:
                    footer_height = 45

                new_height = height + header_height + footer_height
                new_image = Image.new("RGBA", (width, new_height), (255, 255, 255, 255))

                # --- 2. Construction du layout ---
                new_image.paste(original_image, (0, header_height))

                # --- 3. Logo ---
                logo = Image.open(logo_path).convert("RGBA")

                target_logo_width = int(width * LOGO_WIDTH_PCT)
                logo_aspect_ratio = logo.height / logo.width
                target_logo_height = int(target_logo_width * logo_aspect_ratio)

                max_logo_height = int(header_height * 0.95)
                if target_logo_height > max_logo_height:
                    target_logo_height = max_logo_height
                    target_logo_width = int(target_logo_height / logo_aspect_ratio)

                logo_resized = logo.resize(
                    (target_logo_width, target_logo_height),
                    Image.Resampling.LANCZOS,
                )

                padding = int(width * PADDING_PCT)
                logo_box_width = target_logo_width + (LOGO_OUTLINE_PX * 2)
                logo_box_height = target_logo_height + (LOGO_OUTLINE_PX * 2)
                logo_x = width - logo_box_width - padding
                logo_margin = max(6, int(header_height * 0.08))
                logo_y = header_height - logo_box_height - logo_margin
                if logo_y < 0:
                    logo_y = 0

                logo_bg = Image.new("RGBA", (logo_box_width, logo_box_height), (255, 255, 255, 255))
                new_image.paste(logo_bg, (logo_x, logo_y))
                new_image.paste(
                    logo_resized,
                    (logo_x + LOGO_OUTLINE_PX, logo_y + LOGO_OUTLINE_PX),
                    logo_resized,
                )

                # --- 4. Texte ---
                draw = ImageDraw.Draw(new_image)

                font_size = int(height * 0.0275)
                if font_size < MIN_FONT_SIZE:
                    font_size = MIN_FONT_SIZE
                if font_size > MAX_FONT_SIZE:
                    font_size = MAX_FONT_SIZE

                font = get_font(False, font_size)
                bbox = draw.textbbox((0, 0), SOURCE_TEXT, font=font)
                text_width = bbox[2] - bbox[0]
                
                # Dessin centré
                current_x = (width - text_width) // 2
                footer_start_y = height + header_height
                # Centre en Y sur le premier segment (même baseline de police).
                bbox_sample = draw.textbbox((0, 0), "Ag", font=font)
                sample_h = bbox_sample[3] - bbox_sample[1]
                text_margin = max(4, int(footer_height * 0.15))
                text_y = footer_start_y + text_margin
                max_text_y = footer_start_y + footer_height - sample_h - 2
                if text_y > max_text_y:
                    text_y = max_text_y

                draw.text((current_x, text_y), SOURCE_TEXT, font=font, fill=TEXT_COLOR)

                png_info = PngImagePlugin.PngInfo()
                png_info.add_text("watermarked", "1")
                new_image.save(img_full_path, format="PNG", pnginfo=png_info)
                print(f"Processed: {img_rel_path}")

        except Exception as e:
            print(f"Failed to process {img_rel_path}: {e}")


if __name__ == "__main__":
    apply_watermark()
