#!/usr/bin/env python3
"""Render publication-safe Markdown chapters into DOCX or PDF.

This is a THIN, SPEC-DRIVEN renderer. All presentation decisions (title page,
fonts, colors, sizes, table of contents, headers/footers, chapter order,
front/back matter) come from an LLM-authored document spec — not from
hardcoded policy here. The script only:

  1. resolves the spec (JSON) merged over minimal defaults,
  2. assembles the chapter Markdown the agent wrote,
  3. runs a mechanical publication-safety scan,
  4. renders bytes (DOCX via python-docx, PDF via reportlab).

Author the spec at docs/<mode>/_document.json (or pass --spec). Generate a
starter with --emit-spec, then edit it per report/scenario/language.
"""

from __future__ import annotations

import argparse
import copy
import html
import json
import re
from datetime import date
from pathlib import Path
from typing import Any, Iterable

MODES = ("survey", "report", "manuscript", "brief")

INTERNAL_PATTERNS = {
    "internal material ID": re.compile(
        r"(?<![\w-])\[?(?:P|W|G|S|E)-\d{1,6}\]?(?![\w-])", re.I
    ),
    "workflow name": re.compile(
        r"\bOMR\b|Oh-My-Research|Evidence-Deep|THINK mode|SYNTH mode", re.I
    ),
    "gate or QA name": re.compile(r"\bGate\s+[ABDL]\b|\bQA[12]\b", re.I),
    "private artifact path": re.compile(r"(?:docs/plans/|\.omr/|tree-state\.json)", re.I),
    "internal evidence label": re.compile(
        r"evidence\s+(?:grade|boundary)|boundary-tagged|"
        r"(?:grade|boundary)\s*:\s*(?:proven|suggests|inferred)",
        re.I,
    ),
}

# Minimal, neutral defaults. The LLM spec is expected to override anything that
# should vary by report, audience, or language. These are only a safety net.
DEFAULT_SPEC: dict[str, Any] = {
    "title": None,
    "subtitle": None,
    "author": "",
    "date": None,
    "page": {"size": "A4", "margin_mm": 22},
    "fonts": {
        "body": {"latin": "Calibri", "eastasia": "Microsoft YaHei", "size": 10.5},
        "heading": {"latin": "Calibri", "eastasia": "Microsoft YaHei"},
        "mono": {"latin": "Courier New", "size": 9},
        "pdf_latin": "Helvetica",
        "pdf_cjk": "STSong-Light",
    },
    "colors": {"heading": ["#1F4E79", "#2F5597", "#44546A"], "table_header_bg": "#D9EAF7"},
    "heading_sizes": [18, 14, 12],
    "line_spacing": 1.25,
    "cover": {"enabled": True, "elements": ["title", "subtitle", "author", "date"]},
    "toc": {"enabled": True, "title": None, "depth": 3},
    "header": {"enabled": True, "text": None},
    "footer": {"enabled": True, "page_numbers": True},
    "chapters": {"order": None, "include": None, "exclude": []},
    "drop_first_h1_matching_title": True,
}

LANG_STRINGS = {
    "en": {"toc": "Table of Contents", "subtitle": "Deep Research Report"},
    "zh-CN": {"toc": "目录", "subtitle": "深度研究报告"},
}


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def lang_string(spec: dict[str, Any], language: str, key: str) -> str:
    table = LANG_STRINGS.get(language, LANG_STRINGS["en"])
    return table.get(key, LANG_STRINGS["en"][key])


# --------------------------------------------------------------------------- #
# Chapter assembly
# --------------------------------------------------------------------------- #
def strip_frontmatter(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end >= 0:
            return text[end + 5 :]
    return text


def default_sort_key(path: Path) -> tuple[int, str]:
    """Abstract/overview (00-*) leads unless the spec sets an explicit order."""
    name = path.stem
    return (0, name) if name.startswith("00-") else (1, name)


def chapter_files(root: Path, spec: dict[str, Any]) -> list[Path]:
    chapters_dir = root / "chapters"
    search_root = chapters_dir if chapters_dir.is_dir() else root
    available = {
        p.name: p
        for p in search_root.glob("*.md")
        if not p.name.startswith("_") and not p.name.startswith(".")
    }
    order = (spec.get("chapters") or {}).get("order")
    include = (spec.get("chapters") or {}).get("include")
    exclude = set((spec.get("chapters") or {}).get("exclude") or [])

    if order:
        selected: list[Path] = []
        for name in order:
            fname = name if name.endswith(".md") else f"{name}.md"
            if fname in available and fname not in {e if e.endswith('.md') else f'{e}.md' for e in exclude}:
                selected.append(available[fname])
        return selected

    names = list(available)
    if include:
        include_set = {n if n.endswith(".md") else f"{n}.md" for n in include}
        names = [n for n in names if n in include_set]
    exclude_set = {n if n.endswith(".md") else f"{n}.md" for n in exclude}
    names = [n for n in names if n not in exclude_set]
    return sorted((available[n] for n in names), key=default_sort_key)


def assemble(root: Path, spec: dict[str, Any]) -> tuple[str, list[tuple[str, str]]]:
    files = chapter_files(root, spec)
    if not files:
        raise SystemExit(f"No Markdown chapters found in {root}")
    chapters = [(p.name, strip_frontmatter(p.read_text(encoding="utf-8")).strip()) for p in files]
    combined = "\n\n".join(text for _, text in chapters).strip() + "\n"
    return combined, chapters


def validate_publication(text: str) -> list[str]:
    findings: list[str] = []
    for label, pattern in INTERNAL_PATTERNS.items():
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            findings.append(f"{label} at line {line}: {match.group(0)!r}")
    return findings


def infer_title(text: str) -> str | None:
    match = re.search(r"^#\s+(.+)$", text, re.M)
    return clean_inline(match.group(1)) if match else None


def slugify(value: str) -> str:
    value = re.sub(r"[^\w\u3400-\u9fff]+", "-", value.strip().lower(), flags=re.UNICODE)
    return value.strip("-") or "research"


def clean_inline(text: str) -> str:
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*_`~]", "", text)
    return text.strip()


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_table_separator(line: str) -> bool:
    cells = split_table_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def markdown_blocks(text: str) -> Iterable[dict[str, object]]:
    lines = text.splitlines()
    i = 0
    paragraph: list[str] = []

    def flush() -> Iterable[dict[str, object]]:
        nonlocal paragraph
        if paragraph:
            yield {"type": "paragraph", "text": " ".join(x.strip() for x in paragraph)}
            paragraph = []

    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            yield from flush()
            i += 1
            continue
        if line.startswith("<!--"):
            yield from flush()
            while i < len(lines) and "-->" not in lines[i]:
                i += 1
            i += 1
            continue
        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            yield from flush()
            yield {"type": "heading", "level": len(heading.group(1)), "text": clean_inline(heading.group(2))}
            i += 1
            continue
        if i + 1 < len(lines) and "|" in line and is_table_separator(lines[i + 1]):
            yield from flush()
            rows = [split_table_row(line)]
            i += 2
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                rows.append(split_table_row(lines[i]))
                i += 1
            yield {"type": "table", "rows": rows}
            continue
        bullet = re.match(r"^\s*[-*+]\s+(.+)$", line)
        numbered = re.match(r"^\s*\d+[.)]\s+(.+)$", line)
        if bullet or numbered:
            yield from flush()
            yield {"type": "list", "ordered": bool(numbered), "text": (numbered or bullet).group(1)}
            i += 1
            continue
        if line.startswith(">"):
            yield from flush()
            yield {"type": "quote", "text": line.lstrip("> ").strip()}
            i += 1
            continue
        if line.startswith("```"):
            yield from flush()
            i += 1
            code: list[str] = []
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            yield {"type": "code", "text": "\n".join(code)}
            continue
        paragraph.append(line)
        i += 1
    yield from flush()


# --------------------------------------------------------------------------- #
# DOCX
# --------------------------------------------------------------------------- #
def _docx_inline(paragraph: object, text: str) -> None:
    token = re.compile(r"(\*\*[^*]+\*\*|(?<!\*)\*[^*]+\*(?!\*)|`[^`]+`|\[[^\]]+\]\([^)]+\))")
    position = 0
    for match in token.finditer(text):
        if match.start() > position:
            paragraph.add_run(text[position : match.start()])
        value = match.group(0)
        if value.startswith("**"):
            paragraph.add_run(value[2:-2]).bold = True
        elif value.startswith("*"):
            paragraph.add_run(value[1:-1]).italic = True
        elif value.startswith("`"):
            paragraph.add_run(value[1:-1]).font.name = "Courier New"
        else:
            link = re.match(r"\[([^\]]+)\]\(([^)]+)\)", value)
            run = paragraph.add_run(link.group(1) if link else value)
            if link:
                run.font.underline = True
        position = match.end()
    if position < len(text):
        paragraph.add_run(text[position:])


def _set_eastasia(run: object, font_name: str) -> None:
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    properties = run._element.get_or_add_rPr()
    fonts = properties.rFonts
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        properties.insert(0, fonts)
    fonts.set(qn("w:eastAsia"), font_name)


def _field(paragraph: object, instruction: str, placeholder: str = "") -> None:
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = instruction
    sep = OxmlElement("w:fldChar")
    sep.set(qn("w:fldCharType"), "separate")
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    nodes = [begin, instr, sep]
    if placeholder:
        text_node = OxmlElement("w:t")
        text_node.text = placeholder
        sep.append(text_node)
    nodes.append(end)
    run._r.extend(nodes)


def export_docx(chapters: list[tuple[str, str]], output: Path, spec: dict[str, Any], language: str) -> None:
    try:
        from docx import Document
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
        from docx.shared import Cm, Pt, RGBColor
    except ImportError as exc:
        raise SystemExit("DOCX export requires python-docx: pip install python-docx") from exc

    def rgb(hex_str: str) -> "RGBColor":
        return RGBColor.from_string(hex_str.lstrip("#"))

    title = spec["title"]
    document = Document()
    section = document.sections[0]
    if str(spec["page"].get("size", "A4")).upper() == "A4":
        section.page_height, section.page_width = Cm(29.7), Cm(21)
    else:  # Letter
        section.page_height, section.page_width = Cm(27.94), Cm(21.59)
    margin = Cm(spec["page"].get("margin_mm", 22) / 10)
    section.top_margin = section.bottom_margin = margin
    section.left_margin = section.right_margin = margin

    body_font = spec["fonts"]["body"]["latin"]
    body_ea = spec["fonts"]["body"].get("eastasia", body_font)
    heading_font = spec["fonts"]["heading"].get("latin", body_font)
    heading_ea = spec["fonts"]["heading"].get("eastasia", body_ea)

    normal = document.styles["Normal"]
    normal.font.name = body_font
    normal.font.size = Pt(spec["fonts"]["body"].get("size", 10.5))
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), body_ea)
    normal.paragraph_format.line_spacing = spec.get("line_spacing", 1.25)
    normal.paragraph_format.space_after = Pt(7)

    heading_colors = spec["colors"]["heading"]
    heading_sizes = spec["heading_sizes"]
    for level in range(1, 4):
        style = document.styles[f"Heading {level}"]
        style.font.name = heading_font
        style._element.rPr.rFonts.set(qn("w:eastAsia"), heading_ea)
        style.font.color.rgb = rgb(heading_colors[min(level - 1, len(heading_colors) - 1)])
        style.font.size = Pt(heading_sizes[min(level - 1, len(heading_sizes) - 1)])
        style.paragraph_format.space_before = Pt(14)
        style.paragraph_format.space_after = Pt(6)

    document.core_properties.title = title or ""
    document.core_properties.author = spec.get("author", "") or ""

    if spec["toc"].get("enabled", True):
        settings = document.settings.element
        if settings.find(qn("w:updateFields")) is None:
            update = OxmlElement("w:updateFields")
            update.set(qn("w:val"), "true")
            settings.append(update)

    # Cover (spec-driven element list)
    cover = spec.get("cover") or {}
    if cover.get("enabled", True):
        elements = cover.get("elements") or ["title"]
        date_str = spec.get("date") or date.today().isoformat()
        first = True
        for element in elements:
            para = document.add_paragraph()
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if first:
                para.paragraph_format.space_before = Pt(150)
                first = False
            if element == "title" and title:
                run = para.add_run(title)
                run.bold = True
                run.font.size = Pt(28)
                run.font.color.rgb = rgb(heading_colors[0])
                _set_eastasia(run, heading_ea)
            elif element == "subtitle":
                text = spec.get("subtitle") or lang_string(spec, language, "subtitle")
                para.add_run(text).italic = True
            elif element == "author" and spec.get("author"):
                para.paragraph_format.space_before = Pt(60)
                para.add_run(spec["author"])
            elif element == "date":
                para.add_run(date_str)
            else:
                para.add_run(str(element))
        document.add_page_break()

    # TOC
    if spec["toc"].get("enabled", True):
        toc_title = spec["toc"].get("title") or lang_string(spec, language, "toc")
        document.add_heading(toc_title, level=1)
        depth = spec["toc"].get("depth", 3)
        _field(document.add_paragraph(), f' TOC \\o "1-{depth}" \\h \\z \\u ', "Update field to build the table of contents.")
        document.add_page_break()

    drop_title = spec.get("drop_first_h1_matching_title", True)
    first_heading = True
    for block in markdown_blocks("\n\n".join(text for _, text in chapters)):
        kind = block["type"]
        if kind == "heading":
            level = min(int(block["level"]), 3)
            text = str(block["text"])
            if first_heading and drop_title and level == 1 and title and text == title:
                first_heading = False
                continue
            first_heading = False
            document.add_heading(text, level=level)
        elif kind == "paragraph":
            _docx_inline(document.add_paragraph(), str(block["text"]))
        elif kind == "list":
            style = "List Number" if block["ordered"] else "List Bullet"
            _docx_inline(document.add_paragraph(style=style), str(block["text"]))
        elif kind == "quote":
            _docx_inline(document.add_paragraph(style="Quote"), str(block["text"]))
        elif kind == "code":
            run = document.add_paragraph().add_run(str(block["text"]))
            run.font.name = spec["fonts"]["mono"]["latin"]
            run.font.size = Pt(spec["fonts"]["mono"].get("size", 9))
        elif kind == "table":
            rows = block["rows"]
            if not rows:
                continue
            columns = max(len(r) for r in rows)
            table = document.add_table(rows=len(rows), cols=columns)
            table.style = "Light Shading Accent 1"
            for r_index, row in enumerate(rows):
                for c_index, value in enumerate(row):
                    cell = table.cell(r_index, c_index)
                    cell.text = clean_inline(value)
                    for run in cell.paragraphs[0].runs:
                        run.bold = r_index == 0
                        _set_eastasia(run, body_ea)

    header_spec = spec.get("header") or {}
    footer_spec = spec.get("footer") or {}
    for section in document.sections:
        if header_spec.get("enabled", True):
            header_text = header_spec.get("text")
            header_text = title if header_text is None else header_text
            para = section.header.paragraphs[0]
            para.text = header_text or ""
            para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            if para.runs:
                para.runs[0].font.size = Pt(8)
        if footer_spec.get("enabled", True) and footer_spec.get("page_numbers", True):
            para = section.footer.paragraphs[0]
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            _field(para, " PAGE ")

    output.parent.mkdir(parents=True, exist_ok=True)
    document.save(output)


# --------------------------------------------------------------------------- #
# PDF
# --------------------------------------------------------------------------- #
def _pdf_inline(text: str) -> str:
    value = html.escape(text)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", value)
    value = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", value)
    value = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"<a href='\2'>\1</a>", value)
    return value


def export_pdf(chapters: list[tuple[str, str]], output: Path, spec: dict[str, Any], language: str) -> None:
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
        from reportlab.lib.pagesizes import A4, LETTER
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        from reportlab.platypus import (
            BaseDocTemplate,
            Frame,
            PageBreak,
            PageTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
        )
        from reportlab.platypus.tableofcontents import TableOfContents
    except ImportError as exc:
        raise SystemExit("PDF export requires reportlab: pip install reportlab") from exc

    title = spec["title"]
    page_size = A4 if str(spec["page"].get("size", "A4")).upper() == "A4" else LETTER
    margin = spec["page"].get("margin_mm", 22) * mm

    standard_bold = {
        "Helvetica": "Helvetica-Bold",
        "Times-Roman": "Times-Bold",
        "Courier": "Courier-Bold",
    }
    font = spec["fonts"].get("pdf_latin", "Helvetica")
    bold_font = standard_bold.get(font, font)
    if language == "zh-CN":
        cjk = spec["fonts"].get("pdf_cjk", "STSong-Light")
        pdfmetrics.registerFont(UnicodeCIDFont(cjk))
        font = bold_font = cjk

    heading_colors = spec["colors"]["heading"]
    heading_sizes = spec["heading_sizes"]
    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName=font,
        fontSize=spec["fonts"]["body"].get("size", 10.5),
        leading=spec["fonts"]["body"].get("size", 10.5) * 1.5,
        alignment=TA_JUSTIFY,
        spaceAfter=7,
        wordWrap="CJK" if language == "zh-CN" else None,
    )
    headings = {
        level: ParagraphStyle(
            f"H{level}",
            parent=styles[f"Heading{level}"],
            fontName=bold_font,
            fontSize=heading_sizes[min(level - 1, len(heading_sizes) - 1)],
            leading=heading_sizes[min(level - 1, len(heading_sizes) - 1)] * 1.3,
            textColor=colors.HexColor(heading_colors[min(level - 1, len(heading_colors) - 1)]),
            spaceBefore=13,
            spaceAfter=6,
        )
        for level in (1, 2, 3)
    }

    class ReportDoc(BaseDocTemplate):
        def afterFlowable(self, flowable: object) -> None:
            if isinstance(flowable, Paragraph) and flowable.style.name in ("H1", "H2", "H3"):
                level = int(flowable.style.name[1]) - 1
                key = f"h-{self.seq.nextf('h')}"
                self.canv.bookmarkPage(key)
                self.canv.addOutlineEntry(flowable.getPlainText(), key, level=level, closed=False)
                self.notify("TOCEntry", (level, flowable.getPlainText(), self.page, key))

    header_spec = spec.get("header") or {}
    footer_spec = spec.get("footer") or {}
    header_text = header_spec.get("text")
    header_text = title if header_text is None else header_text

    def decorate(canvas: object, doc: object) -> None:
        canvas.saveState()
        canvas.setFont(font, 8)
        canvas.setFillColor(colors.HexColor("#666666"))
        if header_spec.get("enabled", True) and header_text:
            canvas.drawString(margin, page_size[1] - margin + 6 * mm, str(header_text)[:90])
        if footer_spec.get("enabled", True) and footer_spec.get("page_numbers", True):
            canvas.drawRightString(page_size[0] - margin, margin - 8 * mm, str(doc.page))
        canvas.restoreState()

    output.parent.mkdir(parents=True, exist_ok=True)
    doc = ReportDoc(
        str(output),
        pagesize=page_size,
        title=title or "",
        author=spec.get("author", "") or "",
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin,
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    doc.addPageTemplates([PageTemplate(id="pub", frames=frame, onPage=decorate)])

    story: list[object] = []
    cover = spec.get("cover") or {}
    if cover.get("enabled", True):
        cover_style = ParagraphStyle("Cover", parent=styles["Title"], fontName=bold_font, fontSize=28, leading=35, alignment=TA_CENTER, textColor=colors.HexColor(heading_colors[0]))
        center = ParagraphStyle("Center", parent=body, alignment=TA_CENTER, fontName=font, fontSize=11)
        date_str = spec.get("date") or date.today().isoformat()
        story.append(Spacer(1, 58 * mm))
        for element in cover.get("elements") or ["title"]:
            if element == "title" and title:
                story.append(Paragraph(html.escape(title), cover_style))
                story.append(Spacer(1, 12 * mm))
            elif element == "subtitle":
                story.append(Paragraph(html.escape(spec.get("subtitle") or lang_string(spec, language, "subtitle")), center))
                story.append(Spacer(1, 30 * mm))
            elif element == "author" and spec.get("author"):
                story.append(Paragraph(html.escape(spec["author"]), center))
            elif element == "date":
                story.append(Paragraph(date_str, center))
        story.append(PageBreak())

    if spec["toc"].get("enabled", True):
        toc_title = spec["toc"].get("title") or lang_string(spec, language, "toc")
        story.append(Paragraph(html.escape(toc_title), headings[1]))
        toc = TableOfContents()
        depth = spec["toc"].get("depth", 3)
        toc.levelStyles = [
            ParagraphStyle(f"TOC{level}", fontName=font, fontSize=max(11 - level, 8), leading=15, leftIndent=level * 12)
            for level in range(depth)
        ]
        story.extend([toc, PageBreak()])

    drop_title = spec.get("drop_first_h1_matching_title", True)
    first_heading = True
    for block in markdown_blocks("\n\n".join(text for _, text in chapters)):
        kind = block["type"]
        if kind == "heading":
            level = min(int(block["level"]), 3)
            text = str(block["text"])
            if first_heading and drop_title and level == 1 and title and text == title:
                first_heading = False
                continue
            first_heading = False
            story.append(Paragraph(html.escape(text), headings[level]))
        elif kind == "paragraph":
            story.append(Paragraph(_pdf_inline(str(block["text"])), body))
        elif kind == "list":
            bullet = "1. " if block["ordered"] else "• "
            story.append(Paragraph(bullet + _pdf_inline(str(block["text"])), ParagraphStyle("List", parent=body, leftIndent=14, firstLineIndent=-10)))
        elif kind == "quote":
            story.append(Paragraph(_pdf_inline(str(block["text"])), ParagraphStyle("Quote", parent=body, leftIndent=14, rightIndent=14, textColor=colors.HexColor("#555555"))))
        elif kind == "code":
            code_html = html.escape(str(block["text"])).replace("\n", "<br/>")
            story.append(Paragraph(code_html, ParagraphStyle("Code", parent=body, fontName="Courier", fontSize=8.5, leading=11, backColor=colors.HexColor("#F3F3F3"), borderPadding=6)))
        elif kind == "table":
            rows = [[Paragraph(_pdf_inline(cell), body) for cell in row] for row in block["rows"]]
            if not rows:
                continue
            widths = [doc.width / max(len(rows[0]), 1)] * len(rows[0])
            table = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(spec["colors"].get("table_header_bg", "#D9EAF7"))),
                        ("FONTNAME", (0, 0), (-1, 0), bold_font),
                        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#A6A6A6")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            story.extend([table, Spacer(1, 6)])

    doc.multiBuild(story)


# --------------------------------------------------------------------------- #
# Spec resolution + CLI
# --------------------------------------------------------------------------- #
def resolve_spec(root: Path, args: argparse.Namespace, combined: str) -> dict[str, Any]:
    spec = copy.deepcopy(DEFAULT_SPEC)
    spec_path = args.spec or (root / "_document.json")
    if spec_path and Path(spec_path).exists():
        loaded = json.loads(Path(spec_path).read_text(encoding="utf-8"))
        spec = deep_merge(spec, loaded)
    # CLI overrides win over the file so quick runs still work
    if args.title:
        spec["title"] = args.title
    if args.author:
        spec["author"] = args.author
    if spec.get("title") is None:
        spec["title"] = infer_title(combined)
    return spec


def emit_spec(root: Path, language: str, mode: str) -> Path:
    spec = copy.deepcopy(DEFAULT_SPEC)
    spec["title"] = None
    spec["_comment"] = (
        "LLM-authored document spec. Edit any field to control presentation. "
        "Delete fields to fall back to defaults. chapters.order lists chapter "
        "filenames (without .md) in publication order; omit to auto-order."
    )
    out = root / "_document.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Spec-driven publication-safe report renderer")
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--mode", default="survey", choices=MODES)
    parser.add_argument("--format", default="docx", choices=["docx", "pdf"])
    parser.add_argument("--language", default="en")
    parser.add_argument("--spec", type=Path, default=None, help="Path to document spec JSON")
    parser.add_argument("--emit-spec", action="store_true", help="Write a starter _document.json and exit")
    parser.add_argument("--title", default=None, help="Override spec title")
    parser.add_argument("--author", default="", help="Override spec author")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    root = workspace / "docs" / args.mode
    if args.emit_spec:
        print(emit_spec(root, args.language, args.mode))
        return
    if not root.is_dir():
        raise SystemExit(f"Missing docs/{args.mode}/")

    combined, chapters = assemble(root, {"chapters": {}})
    findings = validate_publication(combined)
    if findings:
        details = "\n".join(f"  - {f}" for f in findings[:30])
        raise SystemExit(
            "Publication-safety scan failed. Replace private references and workflow "
            f"terminology before export:\n{details}"
        )

    spec = resolve_spec(root, args, combined)
    # Re-assemble honoring spec chapter order/include/exclude
    combined, chapters = assemble(root, spec)
    if spec.get("title") and validate_publication(spec["title"]):
        raise SystemExit("The report title contains private workflow terminology.")

    output = args.output
    if output is None:
        topic = slugify(spec.get("title") or args.mode)
        output = root / "deliverables" / f"{topic}-{args.mode}-{args.language}.{args.format}"
    elif not output.is_absolute():
        output = workspace / output

    if args.format == "docx":
        export_docx(chapters, output, spec, args.language)
    else:
        export_pdf(chapters, output, spec, args.language)
    print(output)


if __name__ == "__main__":
    main()
