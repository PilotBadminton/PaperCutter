# Paper Cutter Assistant

[中文](README.md)

Paper Cutter Assistant is a local desktop tool for cutting questions, answers, worksheets, handouts, and exam pages from images or PDF files. It lets you select regions, export them as PNG files with predictable naming rules, merge multiple selections, and arrange selections freely on an infinite composition canvas.

This project is released under the **AGPL-3.0-only** license. The application currently targets Windows desktop usage. End users are encouraged to download the self-contained EXE from GitHub Releases.

> GitHub repository: [github.com/pilot123tjcu/PaperCutter](https://github.com/pilot123tjcu/PaperCutter)

## Screenshots and Export Examples

**Open your material and start organizing.** Select the parts you need from images and PDFs, including questions, answers, and handouts.

![Main window with a PDF document open](展示样例/shot02.jpg)

**Arrange the pieces your way.** Bring selections into the composition workspace to adjust their positions, rotation, and layer order.

![Composition workspace with a title and table arranged together](展示样例/shot04.jpg)

<details>
<summary>More screenshots and export examples</summary>

**Choose the background and spacing.** Use transparency, white, a custom color, or the eyedropper, and adjust export padding.

![Composition workspace with eyedropper and padding controls](展示样例/shot06.jpg)

**Turn source material into a finished layout.** Export the same pieces as PNG files with different backgrounds for notes, handouts, or further layout work. Click an image to view the original.

| Transparent background | Custom-color background | White background with tighter padding |
| --- | --- | --- |
| [![Transparent PNG export](展示样例/题目_01.png)](展示样例/题目_01.png) | [![Custom-color PNG export](展示样例/题目_02.png)](展示样例/题目_02.png) | [![White-background PNG export](展示样例/题目_03.png)](展示样例/题目_03.png) |

**More views:** the main window, saved selections, and background color selection.

![Main window before opening a document](展示样例/shot01.jpg)

![Zoomed document with a selection added to the list](展示样例/shot03.jpg)

![Choosing a composition export background color](展示样例/shot05.jpg)

</details>

## Features

- Open JPG, JPEG, PNG, BMP, and PDF files.
- Create rectangular selections or freehand lasso selections.
- Export in question mode or answer mode.
- Use a custom export prefix.
- Automatically increment the question number after successful export.
- Export a single selection or merge multiple selections.
- Export freehand selections with transparent or white outside areas.
- Use the composition workspace for infinite-canvas layout, zooming, panning, drag previews, background settings, and padding settings.
- In the composition workspace, use alignment guides, gentle snapping, rotation, z-order controls, keyboard nudging, undo, and redo.
- All document and image processing is local. No user files are uploaded.

## Download

For normal use, download the release package from GitHub Releases:

- `切题辅助应用.exe`: self-contained Windows executable.

Run it directly after download. Windows may show a warning for unsigned personal applications. If you trust the source, choose to continue.

Detailed user instructions are available in:

- [使用说明.md](使用说明.md)
- [使用说明.txt](使用说明.txt)

## Basic Workflow

1. Click **Open** and choose an image or PDF file.
2. Choose **Cut Questions** or **Cut Answers**.
3. Set the output folder, question number, custom prefix, and auto-increment option.
4. Click **Start Selection**, then draw a rectangular or freehand lasso selection.
5. Click **Confirm Cut** to export directly, or **Add to Selection List** to keep it for later.
6. Use **Merge Export** or open the **Composition Workspace** for advanced layout.

## Composition Workspace

The composition workspace lets you place multiple cut-out selections on a larger canvas and export them as a single PNG. It is useful for handouts, mistake collections, answer collages, and custom layouts.

Key interactions:

- `Ctrl + Mouse Wheel`: zoom the view.
- `Space + Drag`: pan the canvas.
- `100%`: reset view zoom.
- `Fit Content`: bring all canvas items back into view.
- Alignment guides appear while moving objects.
- Hold `Alt` to temporarily disable snapping.
- Drag the rotation handle when a single object is selected.
- Move one layer up/down, bring to front, or send to back.
- Use arrow keys to nudge by 1px; use `Shift + Arrow` to nudge by 10px.
- Choose transparent, white, custom-color, or eyedropper-picked backgrounds.
- Use `Ctrl + Z` and `Ctrl + Y` for undo and redo.

## Run from Source

Recommended development environment:

- Windows 10 or newer.
- Python 3.10+.

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
python main.py
```

## Build the EXE

The project uses PyInstaller:

```bash
python -m PyInstaller --noconfirm paper_cutter.spec
```

The packaged executable will be generated at:

```text
dist/切题辅助应用.exe
```

## Project Structure

```text
config/              Configuration, persistence, and resource paths
core/                Rendering, selection management, export, merge, and mask logic
ui/                  PySide6 user interface components
main.py              Application entry point
paper_cutter.spec    PyInstaller build configuration
使用说明.md          Detailed end-user manual
```

## Privacy

The application does not upload user files. Images, PDFs, selections, and exports are processed locally. The application stores a small amount of local UI state, such as the last output folder, export prefix, and auto-increment setting.

## License

This project is licensed under the **GNU Affero General Public License v3.0 only**. See [LICENSE](LICENSE).

Dependencies follow their own licenses. In particular:

- PySide6 is part of Qt for Python and follows the LGPL/GPL/commercial licensing model.
- PyMuPDF follows the AGPL/commercial licensing model.

If you plan to use, distribute, or modify this project in commercial or closed-source contexts, please review the dependency license obligations first.
