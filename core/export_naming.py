"""
导出文件命名工具。
"""
import re


_TRAILING_NUMBER_RE = re.compile(r"(\d+)$")


def build_export_stem(mode: str, question_num: str, custom_prefix: str = "") -> str:
    """Return the filename stem for an export image."""
    label = (custom_prefix or "").strip() or (mode or "").strip() or "导出"
    number = str(question_num or "").strip()
    return f"{label}_{number}" if number else label


def next_question_num(value: str) -> str:
    """Increment the trailing number; append 1 when no trailing number exists."""
    text = str(value or "").strip()
    if not text:
        return "1"

    match = _TRAILING_NUMBER_RE.search(text)
    if not match:
        return f"{text}1"

    digits = match.group(1)
    next_value = int(digits) + 1
    if len(str(next_value)) <= len(digits):
        replacement = f"{next_value:0{len(digits)}d}"
    else:
        replacement = str(next_value)
    return f"{text[:match.start(1)]}{replacement}"
