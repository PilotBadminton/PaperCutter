"""
选区合并导出器模块
"""
from pathlib import Path
from PIL import Image as PILImage
from core.compat import qimage_to_pil
from core.document_loader import DocumentLoader
from core.export_naming import build_export_stem
from core.selection_mask import apply_mask_to_crop


class SelectionMerger:
    @staticmethod
    def merge_selections(selections: list, output_dir: Path,
                         doc_name: str, mode: str, question_num: str,
                         spacing: int = 10, custom_prefix: str = "") -> str:
        if not selections:
            raise ValueError("没有选区需要合并")

        total_height = 0
        max_width = 0

        for sel in selections:
            x, y, w, h = sel.rect
            total_height += h + spacing
            max_width = max(max_width, w)

        total_height -= spacing
        merged = PILImage.new("RGB", (max_width, total_height), "white")
        current_y = 0

        for sel in selections:
            x, y, w, h = sel.rect
            if sel.file_path:
                pil_img = DocumentLoader.pil_open_crop(sel.file_path, (x, y, w, h))
            else:
                pil_img = qimage_to_pil(sel.image).crop((x, y, x + w, y + h))
            if getattr(sel, 'shape_type', 'rect') == "free" and getattr(sel, 'mask_points', None):
                pil_img = apply_mask_to_crop(pil_img, sel.mask_points, "transparent")
            if pil_img.mode == "RGBA":
                merged.paste(pil_img.convert("RGB"), (0, current_y), pil_img.getchannel("A"))
            else:
                merged.paste(pil_img, (0, current_y))
            current_y += h + spacing

        doc_dir = output_dir / doc_name
        doc_dir.mkdir(parents=True, exist_ok=True)
        dest = doc_dir / f"{build_export_stem(mode, question_num, custom_prefix)}.png"
        merged.save(dest, "PNG")
        return str(dest)
