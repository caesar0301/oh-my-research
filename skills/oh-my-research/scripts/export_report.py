#!/usr/bin/env python3
"""Render publication-safe Markdown chapters as professional DOCX or PDF.

The exporter intentionally rejects private workflow terminology and internal
material IDs. Fix citations and prose in the source chapters before export.
"""

from __future__ import annotations

import argparse
import html
import re
from datetime import date
from pathlib import Path
from typing import Iterable

MODES = ("survey", "report", "manuscript", "brief")
LANGUAGES = ("en", "zh-CN")

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


def strip_frontmatter(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end >= 0:
            return text[end + 5 :]
    return text


def chapter_files(root: Path) -> list[Path]:
    return sorted(
        p
        for p in root.glob("*.md")
        if p.name not in {"_export.md", "_publication.md"} and not p.name.startswith(".")
    )


def concatenate(root: Path) -> tuple[str, list[tuple[str, str]]]:
    files = chapter_files(root)
    if not files:
        raise SystemExit(f"No Markdown chapters found in {root}")
    chapters: list[tuple[str, str]] = []
    for path in files:
        text = strip_frontmatter(path.read_text(encoding="utf-8")).strip()
        chapters.append((path.name, text))
    combined = "\n\n".join(text for _, text in chapters).strip() + "\n"
    return combined, chapters


def validate_publication(text: str) -> list[str]:
    findings: list[str] = []
    for label, pattern in INTERNAL_PATTERNS.items():
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            findings.append(f"{label} at line {line}: {match.group(0)!r}")
    return findings


def infer_title(text: str, mode: str, language: str) -> str:
    match = re.search(r"^#\s+(.+)$", text, re.M)
    if match:
        return clean_inline(match.group(1))
    if language == "zh-CN":
        return {"survey": "深度研究综述", "report": "深度研究报告", "manuscript": "研究论文", "brief": "研究简报"}[mode]
    return {
        "survey": "Deep Research Survey",
        "report": "Deep Research Report",
        "manuscript": "Research Manuscript",
        "brief": "Research Brief",
    }[mode]


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
    """Yield a compact block stream sufficient for report Markdown."""
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
            yield {
                "type": "heading",
                "level": len(heading.group(1)),
                "text": clean_inline(heading.group(2)),
            }
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
            yield {
                "type": "list",
                "ordered": bool(numbered),
                "text": (numbered or bullet).group(1),
            }
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


def add_docx_inline(paragraph: object, text: str) -> None:
    """Add basic Markdown emphasis and links to a python-docx paragraph."""
    token = re.compile(
        r"(\*\*[^*]+\*\*|(?<!\*)\*[^*]+\*(?!\*)|`[^`]+`|\[[^\]]+\]\([^)]+\))"
    )
    position = 0
    for match in token.finditer(text):
        if match.start() > position:
            paragraph.add_run(text[position : match.start()])
        value = match.group(0)
        if value.startswith("**"):
            run = paragraph.add_run(value[2:-2])
            run.bold = True
        elif value.startswith("*"):
            run = paragraph.add_run(value[1:-1])
            run.italic = True
        elif value.startswith("`"):
            run = paragraph.add_run(value[1:-1])
            run.font.name = "Courier New"
        else:
            link = re.match(r"\[([^\]]+)\]\(([^)]+)\)", value)
            run = paragraph.add_run(link.group(1) if link else value)
            if link:
                run.font.underline = True
        position = match.end()
    if position < len(text):
        paragraph.add_run(text[position:])


def set_east_asia_font(run: object, font_name: str) -> None:
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    properties = run._element.get_or_add_rPr()
    fonts = properties.rFonts
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        properties.insert(0, fonts)
    fonts.set(qn("w:eastAsia"), font_name)


def add_page_number(paragraph: object) -> None:
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    paragraph.alignment = 2
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = " PAGE "
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instruction, separate, end])


def add_toc(paragraph: object) -> None:
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = ' TOC \\o "1-3" \\h \\z \\u '
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    placeholder = OxmlElement("w:t")
    placeholder.text = "Update field to generate table of contents."
    separate.append(placeholder)
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instruction, separate, end])


def export_docx(
    chapters: list[tuple[str, str]],
    output: Path,
    title: str,
    language: str,
    author: str,
) -> None:
    try:
        from docx import Document
        from docx.enum.section import WD_SECTION
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml.ns import qn
        from docx.shared import Cm, Pt, RGBColor
    except ImportError as exc:
        raise SystemExit("DOCX export requires python-docx: pip install python-docx") from exc

    document = Document()
    section = document.sections[0]
    section.page_height, section.page_width = Cm(29.7), Cm(21)
    section.top_margin = section.bottom_margin = Cm(2.2)
    section.left_margin = section.right_margin = Cm(2.4)
    section.header_distance, section.footer_distance = Cm(1), Cm(1)

    body_font = "Microsoft YaHei" if language == "zh-CN" else "Aptos"
    heading_font = "Microsoft YaHei" if language == "zh-CN" else "Aptos Display"
    styles = document.styles
    normal = styles["Normal"]
    normal.font.name, normal.font.size = body_font, Pt(10.5)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), body_font)
    normal.paragraph_format.space_after = Pt(7)
    normal.paragraph_format.line_spacing = 1.25
    for level in range(1, 4):
        style = styles[f"Heading {level}"]
        style.font.name = heading_font
        style._element.rPr.rFonts.set(qn("w:eastAsia"), heading_font)
        style.font.color.rgb = RGBColor(31, 78, 121)
        style.font.size = Pt({1: 18, 2: 14, 3: 12}[level])
        style.paragraph_format.space_before = Pt(14)
        style.paragraph_format.space_after = Pt(6)

    document.core_properties.title = title
    document.core_properties.author = author
    document.core_properties.subject = (
        "专业深度研究报告" if language == "zh-CN" else "Professional deep research report"
    )
    settings = document.settings.element
    update_fields = settings.find(qn("w:updateFields"))
    if update_fields is None:
        from docx.oxml import OxmlElement

        update_fields = OxmlElement("w:updateFields")
        settings.append(update_fields)
    update_fields.set(qn("w:val"), "true")

    cover = document.add_paragraph()
    cover.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cover.paragraph_format.space_before = Pt(150)
    run = cover.add_run(title)
    run.bold, run.font.size, run.font.color.rgb = True, Pt(28), RGBColor(31, 78, 121)
    set_east_asia_font(run, heading_font)
    subtitle = document.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.add_run("深度研究报告" if language == "zh-CN" else "Deep Research Report").italic = True
    meta = document.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta.paragraph_format.space_before = Pt(80)
    meta.add_run(f"{author}\n" if author else "")
    meta.add_run(date.today().isoformat())

    document.add_page_break()
    document.add_heading("目录" if language == "zh-CN" else "Table of Contents", level=1)
    add_toc(document.add_paragraph())
    document.add_page_break()

    first_heading = True
    for block in markdown_blocks("\n\n".join(text for _, text in chapters)):
        kind = block["type"]
        if kind == "heading":
            level = min(int(block["level"]), 3)
            text = str(block["text"])
            if first_heading and level == 1 and text == title:
                first_heading = False
                continue
            first_heading = False
            document.add_heading(text, level=level)
        elif kind == "paragraph":
            p = document.add_paragraph()
            add_docx_inline(p, str(block["text"]))
        elif kind == "list":
            style = "List Number" if block["ordered"] else "List Bullet"
            p = document.add_paragraph(style=style)
            add_docx_inline(p, str(block["text"]))
        elif kind == "quote":
            p = document.add_paragraph(style="Quote")
            add_docx_inline(p, str(block["text"]))
        elif kind == "code":
            p = document.add_paragraph()
            run = p.add_run(str(block["text"]))
            run.font.name, run.font.size = "Courier New", Pt(9)
        elif kind == "table":
            rows = block["rows"]
            if not rows:
                continue
            column_count = max(len(row) for row in rows)
            table = document.add_table(rows=len(rows), cols=column_count)
            table.style = "Light Shading Accent 1"
            table.autofit = True
            for r_index, row in enumerate(rows):
                for c_index, value in enumerate(row):
                    cell = table.cell(r_index, c_index)
                    cell.text = clean_inline(value)
                    for run in cell.paragraphs[0].runs:
                        run.bold = r_index == 0
                        set_east_asia_font(run, body_font)

    for section in document.sections:
        header = section.header.paragraphs[0]
        header.text = title
        header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        header.runs[0].font.size = Pt(8)
        add_page_number(section.footer.paragraphs[0])

    output.parent.mkdir(parents=True, exist_ok=True)
    document.save(output)


def pdf_inline(text: str) -> str:
    value = html.escape(text)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", value)
    value = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", value)
    value = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"<a href='\2'>\1</a>", value)
    return value


def export_pdf(
    chapters: list[tuple[str, str]],
    output: Path,
    title: str,
    language: str,
    author: str,
) -> None:
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
        from reportlab.lib.pagesizes import A4
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

    font = "Helvetica"
    bold_font = "Helvetica-Bold"
    if language == "zh-CN":
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        font = bold_font = "STSong-Light"

    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "PublicationBody",
        parent=styles["BodyText"],
        fontName=font,
        fontSize=10.5,
        leading=16,
        alignment=TA_JUSTIFY,
        spaceAfter=7,
        wordWrap="CJK" if language == "zh-CN" else None,
    )
    headings = {
        1: ParagraphStyle(
            "PublicationH1",
            parent=styles["Heading1"],
            fontName=bold_font,
            fontSize=18,
            leading=23,
            textColor=colors.HexColor("#1F4E79"),
            spaceBefore=15,
            spaceAfter=8,
        ),
        2: ParagraphStyle(
            "PublicationH2",
            parent=styles["Heading2"],
            fontName=bold_font,
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#2F5597"),
            spaceBefore=12,
            spaceAfter=6,
        ),
        3: ParagraphStyle(
            "PublicationH3",
            parent=styles["Heading3"],
            fontName=bold_font,
            fontSize=11.5,
            leading=15,
            textColor=colors.HexColor("#44546A"),
            spaceBefore=10,
            spaceAfter=5,
        ),
    }

    class ReportDocTemplate(BaseDocTemplate):
        def afterFlowable(self, flowable: object) -> None:
            if isinstance(flowable, Paragraph):
                style_name = flowable.style.name
                if style_name.startswith("PublicationH"):
                    level = int(style_name[-1]) - 1
                    text = flowable.getPlainText()
                    key = f"heading-{self.seq.nextf('heading')}"
                    self.canv.bookmarkPage(key)
                    self.canv.addOutlineEntry(text, key, level=level, closed=False)
                    self.notify("TOCEntry", (level, text, self.page, key))

    def decorate_page(canvas: object, doc: object) -> None:
        canvas.saveState()
        canvas.setFont(font, 8)
        canvas.setFillColor(colors.HexColor("#666666"))
        canvas.drawString(20 * mm, 12 * mm, title[:80])
        canvas.drawRightString(A4[0] - 20 * mm, 12 * mm, str(doc.page))
        canvas.restoreState()

    output.parent.mkdir(parents=True, exist_ok=True)
    doc = ReportDocTemplate(
        str(output),
        pagesize=A4,
        title=title,
        author=author,
        subject="专业深度研究报告" if language == "zh-CN" else "Professional deep research report",
        leftMargin=22 * mm,
        rightMargin=22 * mm,
        topMargin=22 * mm,
        bottomMargin=22 * mm,
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    doc.addPageTemplates([PageTemplate(id="publication", frames=frame, onPage=decorate_page)])

    story: list[object] = []
    cover_style = ParagraphStyle(
        "Cover",
        parent=styles["Title"],
        fontName=bold_font,
        fontSize=28,
        leading=35,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1F4E79"),
    )
    center = ParagraphStyle(
        "Center", parent=body, alignment=TA_CENTER, fontName=font, fontSize=11
    )
    story.extend(
        [
            Spacer(1, 58 * mm),
            Paragraph(html.escape(title), cover_style),
            Spacer(1, 14 * mm),
            Paragraph("深度研究报告" if language == "zh-CN" else "Deep Research Report", center),
            Spacer(1, 42 * mm),
            Paragraph(html.escape(author), center) if author else Spacer(1, 1),
            Paragraph(date.today().isoformat(), center),
            PageBreak(),
            Paragraph("目录" if language == "zh-CN" else "Table of Contents", headings[1]),
        ]
    )
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(
            f"TOC{level}",
            fontName=font,
            fontSize=10 - level,
            leading=15,
            leftIndent=level * 12,
            firstLineIndent=0,
        )
        for level in range(3)
    ]
    story.extend([toc, PageBreak()])

    first_heading = True
    for block in markdown_blocks("\n\n".join(text for _, text in chapters)):
        kind = block["type"]
        if kind == "heading":
            level = min(int(block["level"]), 3)
            text = str(block["text"])
            if first_heading and level == 1 and text == title:
                first_heading = False
                continue
            first_heading = False
            story.append(Paragraph(html.escape(text), headings[level]))
        elif kind == "paragraph":
            story.append(Paragraph(pdf_inline(str(block["text"])), body))
        elif kind == "list":
            bullet = f"{'1.' if block['ordered'] else '•'} "
            list_style = ParagraphStyle(
                "PublicationList", parent=body, leftIndent=14, firstLineIndent=-10
            )
            story.append(Paragraph(bullet + pdf_inline(str(block["text"])), list_style))
        elif kind == "quote":
            quote_style = ParagraphStyle(
                "PublicationQuote",
                parent=body,
                leftIndent=14,
                rightIndent=14,
                textColor=colors.HexColor("#555555"),
            )
            story.append(Paragraph(pdf_inline(str(block["text"])), quote_style))
        elif kind == "code":
            code_style = ParagraphStyle(
                "PublicationCode",
                parent=body,
                fontName="Courier",
                fontSize=8.5,
                leading=11,
                backColor=colors.HexColor("#F3F3F3"),
                borderPadding=6,
            )
            story.append(Paragraph(html.escape(str(block["text"])).replace("\n", "<br/>"), code_style))
        elif kind == "table":
            rows = [[Paragraph(pdf_inline(cell), body) for cell in row] for row in block["rows"]]
            if rows:
                widths = [doc.width / max(len(rows[0]), 1)] * len(rows[0])
                table = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAF7")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1F1F1F")),
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
                story.append(table)
                story.append(Spacer(1, 6))

    doc.multiBuild(story)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a publication-safe deep research report")
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--mode", default="survey", choices=MODES)
    parser.add_argument("--format", default="docx", choices=["docx", "pdf"])
    parser.add_argument("--language", default="en", choices=LANGUAGES)
    parser.add_argument("--title", default=None)
    parser.add_argument("--author", default="")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    root = workspace / "docs" / args.mode
    if not root.is_dir():
        raise SystemExit(f"Missing docs/{args.mode}/")

    combined, chapters = concatenate(root)
    findings = validate_publication(combined)
    if findings:
        details = "\n".join(f"  - {finding}" for finding in findings[:30])
        raise SystemExit(
            "Publication-safety scan failed. Replace private references and workflow "
            f"terminology before export:\n{details}"
        )

    title = args.title or infer_title(combined, args.mode, args.language)
    if validate_publication(title):
        raise SystemExit("The report title contains private workflow terminology.")
    topic = slugify(title)
    output = args.output
    if output is None:
        output = root / "deliverables" / f"{topic}-{args.mode}-{args.language}.{args.format}"
    elif not output.is_absolute():
        output = workspace / output

    public_markdown = root / "_publication.md"
    public_markdown.write_text(combined, encoding="utf-8")
    if args.format == "docx":
        export_docx(chapters, output, title, args.language, args.author)
    else:
        export_pdf(chapters, output, title, args.language, args.author)
    print(output)


if __name__ == "__main__":
    main()
