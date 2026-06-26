"""
主窗口模块
"""
import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QMessageBox, 
                               QFileDialog, QSplitter, QVBoxLayout)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
from pathlib import Path

from ui.document_canvas import ScrollableCanvas
from ui.toolbar import ToolBar
from ui.mode_panel import ModePanel
from ui.status_bar import StatusBar
from ui.selection_list import SelectionListWidget
from ui.composition_window import CompositionWindow
from ui.particle_background import ParticleBackground
from ui.glass_effect import GlassEffect
from core.document_loader import DocumentLoader
from config import persist
from core.pdf_renderer import PDFRenderer
from core.selection_exporter import SelectionExporter
from core.selection_merger import SelectionMerger
from core.selection_manager import SelectionManager
from core.page_navigator import PageNavigator
from config.settings import Settings


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.is_pdf = False
        self.pdf_renderer = None
        self.page_navigator = None
        self.scale_factor = 1.0
        self._doc_size = None
        self.render_timer = QTimer()
        self.render_timer.setSingleShot(True)
        self.render_timer.timeout.connect(self._execute_render)
        
        self.selection_manager = SelectionManager()
        self._cfg = persist.load()
        
        self._init_ui()
        self._connect_signals()
        self._apply_glass_effects()
    
    def _get_icon_path(self):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = Path(__file__).parent.parent
        return str(Path(base_path) / 'app_icon.ico')
    
    def _init_ui(self):
        self.setWindowTitle("切题辅助应用")
        self.setGeometry(100, 100, 1400, 800)
        self.setWindowIcon(QIcon(self._get_icon_path()))
        
        self.particle_background = ParticleBackground(self)
        self.particle_background.setGeometry(0, 0, 1400, 800)
        self.particle_background.lower()
        
        self.toolbar = ToolBar()
        self.addToolBar(self.toolbar)
        
        last_output = self._cfg.get('output_dir')
        self.mode_panel = ModePanel(
            last_output,
            self._cfg.get('export_prefix', ''),
            self._cfg.get('auto_increment_enabled', False),
        )
        self.selection_list = SelectionListWidget()
        self.scrollable_canvas = ScrollableCanvas()
        self.canvas = self.scrollable_canvas.get_canvas()
        
        left_splitter = QSplitter(Qt.Orientation.Vertical)
        left_splitter.addWidget(self.mode_panel)
        left_splitter.addWidget(self.selection_list)
        left_splitter.setStretchFactor(0, 1)
        left_splitter.setStretchFactor(1, 1)
        left_splitter.setMinimumWidth(328)
        left_splitter.setMaximumWidth(390)
        left_splitter.setSizes([430, 370])
        
        central_widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)
        layout.addWidget(left_splitter)
        layout.addWidget(self.scrollable_canvas, stretch=1)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        self.status_bar = StatusBar()
        self.setStatusBar(self.status_bar)
        
        self._apply_glass_effects()
    
    def _connect_signals(self):
        self.toolbar.open_action.triggered.connect(self._open_file)
        self.toolbar.prev_page_action.triggered.connect(self._prev_page)
        self.toolbar.next_page_action.triggered.connect(self._next_page)
        self.toolbar.zoom_in_action.triggered.connect(self._zoom_in)
        self.toolbar.zoom_out_action.triggered.connect(self._zoom_out)
        self.toolbar.fit_width_action.triggered.connect(self._fit_width)
        self.toolbar.fit_page_action.triggered.connect(self._fit_page)
        
        self.toolbar.zoom_changed.connect(self._on_zoom_input)
        self.toolbar.page_changed.connect(self._on_page_input)
        
        self.mode_panel.mode_changed.connect(self._on_mode_changed)
        self.mode_panel.start_selection.connect(self._on_start_selection)
        self.mode_panel.selection_tool_changed.connect(self._on_selection_tool_changed)
        self.mode_panel.confirm_cut.connect(self._on_confirm_cut)
        self.mode_panel.add_selection.connect(self._on_add_selection)
        self.mode_panel.open_composition.connect(self._on_open_composition)
        
        self.canvas.selection_changed.connect(self._on_selection_changed)
        
        self.selection_list.export_merged.connect(self._on_export_merged)
        self.selection_list.clear_all.connect(self._on_clear_all_selections)
    
    def _open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "打开文件",
            "",
            "支持的文件 (*.png *.jpg *.jpeg *.bmp *.pdf);;图片文件 (*.png *.jpg *.jpeg *.bmp);;PDF文件 (*.pdf)"
        )
        
        if file_path:
            try:
                self._load_file(file_path)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法打开文件：{str(e)}")
    
    def _load_file(self, file_path):
        self.current_file = Path(file_path)
        file_ext = self.current_file.suffix.lower()
        
        if file_ext == '.pdf':
            self.is_pdf = True
            if self.pdf_renderer:
                self.pdf_renderer.close()
            self.pdf_renderer = PDFRenderer(str(self.current_file))
            total_pages = self.pdf_renderer.get_page_count()
            self.page_navigator = PageNavigator(total_pages)
            self.page_navigator.page_changed.connect(self._on_page_changed)

            self._doc_size = self.pdf_renderer.get_page_size(0, Settings.PDF_ZOOM)

            image = self.pdf_renderer.render_page(0, Settings.PDF_ZOOM * self.scale_factor)
            self.canvas.set_image_without_scale(image)
            
            self.toolbar.enable_pdf_controls(True)
            self.toolbar.set_page_info(0, total_pages)
            self.status_bar.set_page_info(0, total_pages)
        else:
            self.is_pdf = False
            if self.pdf_renderer:
                self.pdf_renderer.close()
                self.pdf_renderer = None
            self.page_navigator = None

            self.canvas.load_file(str(self.current_file))
            self._doc_size = self.canvas._orig_size
            if self._doc_size:
                self.scale_factor = self.canvas.image.width() / self._doc_size[0]
                self.toolbar.set_zoom_info(self.scale_factor)
                self.status_bar.set_zoom_info(self.scale_factor)
            
            self.toolbar.enable_pdf_controls(False)
            self.toolbar.set_page_info(0, 0)
            self.status_bar.set_page_info(0, 0)
        
        doc_name = DocumentLoader.get_document_name(str(self.current_file))
        self.status_bar.set_file_info(doc_name)
        self.mode_panel.cancel_selection()
        self.canvas.set_selection_mode(False)
        self.canvas.clear_selection()
        self.selection_list.clear_selections()
    
    def _prev_page(self):
        if self.page_navigator:
            self.page_navigator.prev_page()
    
    def _next_page(self):
        if self.page_navigator:
            self.page_navigator.next_page()
    
    def _on_page_changed(self, page_num):
        if self.pdf_renderer:
            self._doc_size = self.pdf_renderer.get_page_size(page_num, Settings.PDF_ZOOM)
            zoom = Settings.PDF_ZOOM * self.scale_factor
            image = self.pdf_renderer.render_page(page_num, zoom)
            self.canvas.set_image_without_scale(image)
            self.toolbar.set_page_info(page_num, self.page_navigator.get_total_pages())
            self.status_bar.set_page_info(page_num, self.page_navigator.get_total_pages())
            self.mode_panel.cancel_selection()
            self.canvas.set_selection_mode(False)
            self.canvas.clear_selection()
    
    def _render_current_page(self):
        self.render_timer.start(100)
    
    def _execute_render(self):
        if self.pdf_renderer and self.page_navigator:
            page_num = self.page_navigator.get_current_page()
            
            zoom = 2.5 * self.scale_factor
            image = self.pdf_renderer.render_page(page_num, zoom)
            
            self.canvas.set_image_without_scale(image)
    
    def _zoom_in(self):
        self.scale_factor = min(self.scale_factor * 1.2, 3.0)
        
        if self.pdf_renderer:
            self._render_current_page()
        else:
            self.canvas.set_scale_factor(self.scale_factor)
        
        self.toolbar.set_zoom_info(self.scale_factor)
        self.status_bar.set_zoom_info(self.scale_factor)
    
    def _zoom_out(self):
        self.scale_factor = max(self.scale_factor / 1.2, 0.3)
        
        if self.pdf_renderer:
            self._render_current_page()
        else:
            self.canvas.set_scale_factor(self.scale_factor)
        
        self.toolbar.set_zoom_info(self.scale_factor)
        self.status_bar.set_zoom_info(self.scale_factor)
    
    def _fit_width(self):
        if self.canvas.image:
            canvas_width = self.scrollable_canvas.width() - 20
            self.scale_factor = canvas_width / self._doc_size[0]
            if self.pdf_renderer:
                self._render_current_page()
            else:
                self.canvas.set_scale_factor(self.scale_factor)
            self.toolbar.set_zoom_info(self.scale_factor)
            self.status_bar.set_zoom_info(self.scale_factor)
    
    def _fit_page(self):
        if self._doc_size:
            canvas_width = self.scrollable_canvas.width() - 20
            canvas_height = self.scrollable_canvas.height() - 20
            scale_x = canvas_width / self._doc_size[0]
            scale_y = canvas_height / self._doc_size[1]
            self.scale_factor = min(scale_x, scale_y)
            if self.pdf_renderer:
                self._render_current_page()
            else:
                self.canvas.set_scale_factor(self.scale_factor)
            self.toolbar.set_zoom_info(self.scale_factor)
            self.status_bar.set_zoom_info(self.scale_factor)
    
    def _on_zoom_input(self, zoom):
        self.scale_factor = zoom
        
        if self.pdf_renderer:
            self._render_current_page()
        else:
            self.canvas.set_scale_factor(self.scale_factor)
        
        self.toolbar.set_zoom_info(self.scale_factor)
        self.status_bar.set_zoom_info(self.scale_factor)
    
    def _on_page_input(self, page_num):
        if self.page_navigator and page_num >= 0:
            total_pages = self.page_navigator.get_total_pages()
            if page_num < total_pages:
                self.page_navigator.goto_page(page_num)
    
    def _on_mode_changed(self, mode):
        self.status_bar.set_mode_info(mode)
    
    def _on_start_selection(self):
        self.canvas.set_selection_tool(self.mode_panel.get_selection_tool())
        if self.mode_panel.start_selection_btn.isChecked():
            self.canvas.set_selection_mode(True)
        else:
            self.canvas.set_selection_mode(False)

    def _on_selection_tool_changed(self, tool):
        self.canvas.set_selection_tool(tool)
    
    def _on_selection_changed(self, has_selection):
        self.mode_panel.set_selection_active(has_selection)
        if has_selection:
            rect = self.canvas.get_selection_rect()
            self.status_bar.set_selection_info(rect, self.canvas.get_selection_shape_type())
        else:
            self.status_bar.set_selection_info(None)
    
    def _on_add_selection(self):
        if not self.canvas.image:
            QMessageBox.warning(self, "警告", "请先打开文件")
            return
        
        rect = self.canvas.get_selection_rect()
        if not rect:
            QMessageBox.warning(self, "警告", "请先选择区域")
            return
        
        question_num = self.mode_panel.get_question_num()
        if not question_num:
            QMessageBox.warning(self, "警告", "请输入题号")
            return
        
        if not self.mode_panel.get_output_dir():
            QMessageBox.warning(self, "警告", "请先选择输出文件夹")
            return
        
        try:
            page_num = self.page_navigator.get_current_page() if self.page_navigator else 0
            rect_orig = self.canvas.get_selection_rect_original() if self.canvas._orig_size else rect
            file_path = str(self.current_file) if self.canvas._orig_size else None
            shape_type, mask_points = self._current_selection_shape(original=bool(self.canvas._orig_size))
            preview = self.canvas.get_selection_preview("transparent")
            self.selection_manager.add_selection(
                page_num, rect_orig, self.canvas.image, file_path=file_path,
                shape_type=shape_type, mask_points=mask_points, preview=preview
            )
            self.selection_list.add_selection(self.selection_manager.get_selections()[-1])
            self.mode_panel.composition_btn.setEnabled(True)
            
            self.canvas.clear_selection()
            self.mode_panel.cancel_selection()
            self.canvas.set_selection_mode(False)
            
            QMessageBox.information(
                self,
                "成功",
                f"已添加选区（第{page_num + 1}页）"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加选区失败：{str(e)}")
    
    def _on_open_composition(self):
        selections = self.selection_list.get_selections()
        if not selections:
            QMessageBox.warning(self, "警告", "没有选区可用于编排")
            return
        doc_name = DocumentLoader.get_document_name(str(self.current_file)) if self.current_file else "未命名"
        mode = self.mode_panel.get_mode()
        question_num = self.mode_panel.get_question_num()
        out_dir = self.mode_panel.get_output_dir() or Path.cwd()
        dlg = CompositionWindow(
            selections, doc_name, mode, question_num, out_dir, self,
            custom_prefix=self.mode_panel.get_export_prefix(),
        )
        dlg.export_succeeded.connect(lambda path: self._on_composition_export_succeeded(dlg, path))
        dlg.exec()

    def _on_composition_export_succeeded(self, dialog, output_path):
        self._on_export_succeeded(output_path)
        dialog.set_question_num(self.mode_panel.get_question_num())

    def _on_export_merged(self):
        selections = self.selection_list.get_selections()
        if not selections:
            QMessageBox.warning(self, "警告", "没有选区需要导出")
            return
        
        question_num = self.mode_panel.get_question_num()
        if not question_num:
            QMessageBox.warning(self, "警告", "请输入题号")
            return
        
        if not self.mode_panel.get_output_dir():
            QMessageBox.warning(self, "警告", "请先选择输出文件夹")
            return
        
        try:
            doc_name = DocumentLoader.get_document_name(str(self.current_file))
            mode = self.mode_panel.get_mode()
            output_dir = self.mode_panel.get_output_dir()
            export_prefix = self.mode_panel.get_export_prefix()
            
            output_path = SelectionMerger.merge_selections(
                selections, output_dir, doc_name, mode, question_num,
                custom_prefix=export_prefix
            )
            
            QMessageBox.information(
                self,
                "成功",
                f"已成功合并导出到：\n{output_path}\n\n共{len(selections)}个选区"
            )
            self.selection_list.clear_selections()
            self.mode_panel.composition_btn.setEnabled(False)
            self._on_export_succeeded(output_path)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"合并导出失败：{str(e)}")
    
    def _on_clear_all_selections(self):
        reply = QMessageBox.question(
            self,
            "确认",
            "确定要清除所有选区吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.selection_list.clear_selections()
            self.mode_panel.composition_btn.setEnabled(False)
    
    def _on_confirm_cut(self):
        if not self.canvas.image:
            QMessageBox.warning(self, "警告", "请先打开文件")
            return
        
        rect = self.canvas.get_selection_rect_original() if self.canvas._orig_size else self.canvas.get_selection_rect()
        if not rect:
            QMessageBox.warning(self, "警告", "请先选择区域")
            return
        
        question_num = self.mode_panel.get_question_num()
        if not question_num:
            QMessageBox.warning(self, "警告", "请输入题号")
            return
        
        if not self.mode_panel.get_output_dir():
            QMessageBox.warning(self, "警告", "请先选择输出文件夹")
            return
        
        try:
            doc_name = DocumentLoader.get_document_name(str(self.current_file))
            mode = self.mode_panel.get_mode()
            output_dir = self.mode_panel.get_output_dir()
            export_prefix = self.mode_panel.get_export_prefix()
            shape_type, mask_points = self._current_selection_shape(original=bool(self.canvas._orig_size))
            outside_mode = self.mode_panel.get_selection_outside_mode()
            
            exporter = SelectionExporter(output_dir)
            src_path = str(self.current_file) if self.canvas._orig_size else self.canvas.image
            output_path = exporter.export_selection(
                src_path, rect, doc_name, mode, question_num,
                custom_prefix=export_prefix,
                shape_type=shape_type,
                mask_points=mask_points,
                outside_mode=outside_mode,
            )
            
            QMessageBox.information(
                self,
                "成功",
                f"已成功导出到：\n{output_path}"
            )
            
            self.canvas.clear_selection()
            self.mode_panel.cancel_selection()
            self.canvas.set_selection_mode(False)
            self._on_export_succeeded(output_path)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败：{str(e)}")

    def _on_export_succeeded(self, output_path=""):
        if not self.mode_panel.is_auto_increment_enabled():
            return
        old_value = self.mode_panel.get_question_num()
        new_value = self.mode_panel.increment_question_num()
        if old_value:
            self.status_bar.showMessage(f"题号已自动更新：{old_value} → {new_value}", 3500)
        else:
            self.status_bar.showMessage(f"题号已自动更新：{new_value}", 3500)

    def _current_selection_shape(self, original=False):
        shape_type = self.canvas.get_selection_shape_type()
        if shape_type != "free":
            return "rect", None
        if original and self.canvas._orig_size:
            return "free", self.canvas.get_selection_mask_points_original()
        return "free", self.canvas.get_selection_mask_points()
    
    def _apply_glass_effects(self):
        GlassEffect.apply_glass_effect(self.toolbar, 'toolbar')
        GlassEffect.apply_glass_effect(self.mode_panel, 'panel')
        GlassEffect.apply_glass_effect(self.selection_list, 'list')
        GlassEffect.apply_glass_effect(self.status_bar, 'statusbar')
        GlassEffect.apply_glass_effect(self.scrollable_canvas, 'canvas')
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'particle_background'):
            self.particle_background.setGeometry(0, 0, self.width(), self.height())
    
    def closeEvent(self, event):
        if self.pdf_renderer:
            self.pdf_renderer.close()
        event.accept()
