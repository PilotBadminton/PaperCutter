"""
自由编排合并导出引擎 — 全分辨率原图，按编排位置摆放
"""
from pathlib import Path
from PIL import Image as PILImage
from core.document_loader import DocumentLoader
from core.compat import qimage_to_pil
from core.export_naming import build_export_stem


class CompositionMerger:
    @staticmethod
    def export(items: list, output_dir: Path, doc_name: str,
               mode: str, question_num: str, background=None,
               padding: int = 0, custom_prefix: str = "") -> str:
        if not items:
            raise ValueError("没有选区需要导出")

        crops = []
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')

        for it in items:
            fp = it.get('file_path')
            r  = it.get('rect_orig')
            cx = it.get('comp_x', 0.0)
            cy = it.get('comp_y', 0.0)
            rotation = float(it.get('comp_rotation', 0.0) or 0.0)

            if not r or len(r) < 4:
                continue

            if it.get('_full_pil') is not None:
                pil = it.get('_full_pil').copy()
            elif fp:
                pil = DocumentLoader.pil_open_crop(fp, (r[0], r[1], r[2], r[3]))
            else:
                di = it.get('display_image')
                if di is None:
                    continue
                pil = qimage_to_pil(di)
                pil = pil.crop((r[0], r[1], r[0] + r[2], r[1] + r[3]))

            if pil.mode != 'RGBA':
                pil = pil.convert('RGBA')

            fw, fh = pil.size
            if abs(rotation) > 0.01:
                rotated = pil.rotate(-rotation, resample=PILImage.Resampling.BICUBIC, expand=True)
                rw, rh = rotated.size
                ix = int(round(float(cx) + fw / 2 - rw / 2))
                iy = int(round(float(cy) + fh / 2 - rh / 2))
                pil = rotated
                fw, fh = rw, rh
            else:
                ix, iy = int(round(cx)), int(round(cy))

            crops.append((pil, ix, iy, fw, fh))
            min_x = min(min_x, ix, ix + fw)
            min_y = min(min_y, iy, iy + fh)
            max_x = max(max_x, ix + fw)
            max_y = max(max_y, iy + fh)

        if not crops:
            raise ValueError("没有有效的选区可导出")

        padding = max(0, int(padding or 0))
        cw = max(1, int(max_x - min_x) + padding * 2)
        ch = max(1, int(max_y - min_y) + padding * 2)

        if background is None:
            bg = (0, 0, 0, 0)
        else:
            if len(background) == 3:
                bg = (*background, 255)
            else:
                bg = tuple(background)
        merged = PILImage.new("RGBA", (cw, ch), bg)

        for pil, ix, iy, fw, fh in crops:
            tx = int(ix - min_x) + padding
            ty = int(iy - min_y) + padding
            merged.paste(pil, (tx, ty), pil)

        doc_dir = output_dir / doc_name
        doc_dir.mkdir(parents=True, exist_ok=True)
        dest = doc_dir / f"{build_export_stem(mode, question_num, custom_prefix)}.png"
        merged.save(dest, "PNG")
        return str(dest)
