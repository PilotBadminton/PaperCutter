"""
选区导出器模块
"""
from pathlib import Path
from PySide6.QtGui import QImage
from core.document_loader import DocumentLoader
from core.compat import qimage_to_pil
from core.export_naming import build_export_stem
from core.selection_mask import apply_mask_to_crop


class SelectionExporter:
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)

    def export_selection(self, source, rect, doc_name, mode, question_num,
                         custom_prefix="", shape_type="rect",
                         mask_points=None, outside_mode="transparent"):
        """source: str（图片文件路径）或 QImage（PDF 无原始文件时）。"""
        doc_dir = self.output_dir / doc_name
        doc_dir.mkdir(parents=True, exist_ok=True)
        x, y, w, h = rect

        if isinstance(source, str):
            pil_img = DocumentLoader.pil_open_crop(source, (x, y, w, h))
        else:
            pil_img = qimage_to_pil(source).crop((x, y, x + w, y + h))

        if shape_type == "free" and mask_points:
            pil_img = apply_mask_to_crop(pil_img, mask_points, outside_mode)

        path = doc_dir / f"{build_export_stem(mode, question_num, custom_prefix)}.png"
        pil_img.save(path, "PNG")
        return str(path)
