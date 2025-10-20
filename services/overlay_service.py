import os
from PIL import Image, ImageEnhance
from utils.logger import get_logger

logger = get_logger(__name__)

class OverlayService:
    def __init__(self, overlay_base_path: str, output_dir: str):
        """
        overlay_base_path = directory where overlay images (PNG logos, badges) are stored
        output_dir = directory where processed posters should be saved
        """
        self.overlay_base_path = overlay_base_path
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def apply_overlay(self, poster_path: str, overlay_filename: str,
                      position: str = "bottom-right", opacity: float = 1.0, scale: float = 0.15) -> str | None:
        """
        Apply an overlay PNG on top of a poster image.
        - overlay_filename: file name of the PNG inside overlay_base_path
        - position: 'bottom-right', 'bottom-left', 'top-right', 'top-left', 'center'
        - opacity: 0.0 (invisible) to 1.0 (fully opaque)
        - scale: percentage of poster width to use for overlay width (e.g. 0.15 = 15%)
        
        Returns: output file path or None if failed
        """
        try:
            # Load images
            poster = Image.open(poster_path).convert("RGBA")
            overlay_path = os.path.join(self.overlay_base_path, overlay_filename)

            if not os.path.exists(overlay_path):
                raise FileNotFoundError(f"Overlay not found: {overlay_path}")

            overlay = Image.open(overlay_path).convert("RGBA")

            # Scale overlay relative to poster size
            target_width = int(poster.width * scale)
            ratio = target_width / overlay.width
            new_size = (target_width, int(overlay.height * ratio))
            overlay = overlay.resize(new_size, Image.LANCZOS)

            # Apply opacity if needed
            if opacity < 1.0:
                alpha = overlay.split()[3]
                alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
                overlay.putalpha(alpha)

            # Determine position
            margin = 40  # You can make this configurable
            if position == "bottom-right":
                x = poster.width - overlay.width - margin
                y = poster.height - overlay.height - margin
            elif position == "bottom-left":
                x = margin
                y = poster.height - overlay.height - margin
            elif position == "top-right":
                x = poster.width - overlay.width - margin
                y = margin
            elif position == "top-left":
                x = margin
                y = margin
            elif position == "center":
                x = (poster.width - overlay.width) // 2
                y = (poster.height - overlay.height) // 2
            else:
                x = y = 0

            # Apply overlay
            poster.paste(overlay, (x, y), overlay)

            # Save output
            filename = os.path.basename(poster_path)
            output_file = os.path.join(self.output_dir, filename)
            poster.save(output_file, "PNG")

            logger.info(f"Overlay applied and saved → {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"Failed to apply overlay: {e}")
            return None
