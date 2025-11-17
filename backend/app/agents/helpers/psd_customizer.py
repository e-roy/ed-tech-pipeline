"""
PSD Customizer Agent

Downloads template images and overlays custom text for educational content.
Uses PIL (Pillow) to add text overlays on template PNGs.
"""
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class PSDCustomizer:
    """
    Customizes educational templates with text overlays.

    Note: For MVP, works with PNG templates rather than full PSDs.
    Overlays text using PIL instead of editing PSD layers.
    """

    def customize_template(
        self,
        template_url: str,
        customizations: Dict[str, Any]
    ) -> bytes:
        """
        Download template and add custom text overlays.

        Args:
            template_url: URL to template image (PNG)
            customizations: {
                "title": "Main Title",
                "labels": ["Label 1", "Label 2"],
                "subtitle": "Optional subtitle"
            }

        Returns:
            Customized image as bytes
        """
        try:
            logger.info(f"Customizing template from {template_url}")

            # Download template
            response = requests.get(template_url, timeout=10)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))

            # Convert to RGB if needed (some PNGs are RGBA)
            if img.mode != 'RGB':
                # Create white background
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    rgb_img.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                else:
                    rgb_img.paste(img)
                img = rgb_img

            # Create drawing context
            draw = ImageDraw.Draw(img)

            # Load fonts (fallback to default if custom fonts not available)
            try:
                font_title = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                    72
                )
                font_subtitle = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    48
                )
                font_label = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    40
                )
            except Exception as e:
                logger.warning(f"Failed to load custom fonts: {e}, using default")
                font_title = ImageFont.load_default()
                font_subtitle = ImageFont.load_default()
                font_label = ImageFont.load_default()

            # Add title if provided
            if 'title' in customizations and customizations['title']:
                title = customizations['title']
                self._draw_centered_text(
                    draw, img.width, 80, title,
                    font_title, fill='white', outline='black'
                )

            # Add subtitle if provided
            if 'subtitle' in customizations and customizations['subtitle']:
                subtitle = customizations['subtitle']
                self._draw_centered_text(
                    draw, img.width, 180, subtitle,
                    font_subtitle, fill='white', outline='black'
                )

            # Add labels if provided
            if 'labels' in customizations and customizations['labels']:
                labels = customizations['labels']
                y_offset = 280
                for label in labels[:5]:  # Max 5 labels
                    self._draw_text_with_outline(
                        draw, 100, y_offset, label,
                        font_label, fill='white', outline='black'
                    )
                    y_offset += 70

            # Convert to bytes
            buffer = BytesIO()
            img.save(buffer, format='PNG', quality=95)
            image_bytes = buffer.getvalue()

            logger.info(
                f"Template customized successfully ({len(image_bytes)} bytes)"
            )

            return image_bytes

        except Exception as e:
            logger.error(f"Template customization failed: {e}")
            raise

    def _draw_centered_text(
        self,
        draw: ImageDraw.Draw,
        image_width: int,
        y: int,
        text: str,
        font: ImageFont.FreeTypeFont,
        fill: str = 'white',
        outline: str = 'black'
    ):
        """Draw text centered horizontally."""
        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]

        # Calculate center position
        x = (image_width - text_width) // 2

        # Draw with outline for visibility
        self._draw_text_with_outline(draw, x, y, text, font, fill, outline)

    def _draw_text_with_outline(
        self,
        draw: ImageDraw.Draw,
        x: int,
        y: int,
        text: str,
        font: ImageFont.FreeTypeFont,
        fill: str = 'white',
        outline: str = 'black'
    ):
        """Draw text with outline for better visibility."""
        # Draw outline (black border)
        outline_width = 3
        for offset_x in range(-outline_width, outline_width + 1):
            for offset_y in range(-outline_width, outline_width + 1):
                if offset_x != 0 or offset_y != 0:
                    draw.text(
                        (x + offset_x, y + offset_y),
                        text,
                        font=font,
                        fill=outline
                    )

        # Draw main text
        draw.text((x, y), text, font=font, fill=fill)
