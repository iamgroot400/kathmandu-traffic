#!/usr/bin/env python3
"""Build the complete Kathmandu Traffic Simulation manual as a single-column,
book-style PDF from the markdown source files in this directory.

A small, purpose-built markdown-to-reportlab converter - not a general markdown
library - since the source files here were all written by this project with a
known, consistent set of constructs (headers, bold/italic, bullet and numbered
lists, pipe tables, and ```latex fenced blocks for displayed equations).

    python docs/manual/build_manual_pdf.py
"""
from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                                 Table, TableStyle, ListFlowable, ListItem, KeepTogether)

HERE = Path(__file__).parent
OUT = HERE / "Kathmandu_Traffic_Simulation_Manual.pdf"

ORDER = [
    "00_preface.md",
    "00_toc.md",
    "01_part1_foundations.md",
    "02_part2_network.md",
    "03_part3_demand.md",
    "04_part4_calibration.md",
    "05_part5_routechoice.md",
    "06_part6_interventions.md",
    "07_part7_statistics.md",
    "08_part8_correction.md",
    "09_part9_validation.md",
    "10_part10_robustness.md",
    "11_part11_grounding.md",
    "12_part12_future.md",
    "13_part13_software.md",
    "14_part14_closing.md",
    "15_glossary.md",
    "16_appendix_a_assumptions.md",
    "17_appendix_b_decisions.md",
]

# ---------------------------------------------------------------- styles --

TITLE = ParagraphStyle("Title", fontName="Times-Bold", fontSize=26, leading=32,
                       alignment=1, spaceAfter=18)
SUBTITLE = ParagraphStyle("Subtitle", fontName="Times-Italic", fontSize=14, leading=18,
                          alignment=1, spaceAfter=10, textColor=colors.HexColor("#444444"))
PART = ParagraphStyle("Part", fontName="Times-Bold", fontSize=22, leading=27,
                      spaceBefore=0, spaceAfter=24, textColor=colors.HexColor("#1a1a1a"))
H2 = ParagraphStyle("H2", fontName="Times-Bold", fontSize=15, leading=19,
                    spaceBefore=18, spaceAfter=10)
H3 = ParagraphStyle("H3", fontName="Times-Bold", fontSize=12, leading=15,
                    spaceBefore=12, spaceAfter=6)
BODY = ParagraphStyle("Body", fontName="Times-Roman", fontSize=10.8, leading=16,
                      spaceAfter=9, alignment=4)
BULLET = ParagraphStyle("Bullet", parent=BODY, leftIndent=18, spaceAfter=4)
EQUATION = ParagraphStyle("Equation", fontName="Times-Italic", fontSize=11, leading=16,
                          alignment=1, spaceBefore=6, spaceAfter=10,
                          textColor=colors.HexColor("#1a1a3a"),
                          backColor=colors.HexColor("#f4f4f8"), borderPadding=8)
TOC_LINE = ParagraphStyle("TocLine", fontName="Times-Roman", fontSize=10.5, leading=15)
NUMBERED = ParagraphStyle("Numbered", parent=TOC_LINE, leftIndent=28, firstLineIndent=-28,
                          spaceAfter=4)
TOC_PART = ParagraphStyle("TocPart", fontName="Times-Bold", fontSize=11.5, leading=18,
                          spaceBefore=10)

# ---------------------------------------------------------------- inline markup --

def latex_to_text(expr: str) -> str:
    """Rough, good-enough LaTeX -> readable-text conversion for this manual's
    own small, known set of equations. Not a general LaTeX engine."""
    s = expr.strip().strip("$")
    s = re.sub(r"\\text\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"(\1)/(\2)", s)
    s = re.sub(r"\\sqrt\{([^{}]*)\}", r"sqrt(\1)", s)
    s = re.sub(r"\\bar\{([^{}]*)\}", r"\1-bar", s)
    s = re.sub(r"\\big\((.*?)\\big\)", r"(\1)", s)
    s = re.sub(r"\\big\)", ")", s)
    s = re.sub(r"\\big\(", "(", s)
    s = s.replace("\\partial", "d")
    s = s.replace("\\cdot", "\u00b7")
    s = s.replace("\\pm", "\u00b1")
    s = s.replace("\\approx", "\u2248")
    s = s.replace("\\sum", "\u03a3")
    s = s.replace("\\Delta", "\u0394")
    s = s.replace("\\beta", "\u03b2")
    s = s.replace("\\le", "\u2264")
    s = s.replace("\\ge", "\u2265")
    s = s.replace("\\%", "%")
    s = s.replace("\\,", " ")
    s = re.sub(r"_\{([^{}]*)\}", r"<sub>\1</sub>", s)
    s = re.sub(r"\^\{([^{}]*)\}", r"<super>\1</super>", s)
    s = re.sub(r"_([A-Za-z0-9])", r"<sub>\1</sub>", s)
    s = re.sub(r"\^([A-Za-z0-9])", r"<super>\1</super>", s)
    s = re.sub(r"\\[a-zA-Z]+", "", s)  # drop any remaining unhandled macros
    s = re.sub(r"\s+", " ", s).strip()
    return s


def inline_markup(text: str) -> str:
    """**bold**, *italic*, inline $math$ -> reportlab mini-markup."""
    text = re.sub(r"\$([^$]+)\$", lambda m: f"<i>{latex_to_text(m.group(1))}</i>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"`([^`]+)`", r"<font face='Courier'>\1</font>", text)
    return text


# ---------------------------------------------------------------- block parser --

def parse_table(lines: list[str]) -> Table:
    rows = []
    for line in lines:
        if re.match(r"^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append([Paragraph(inline_markup(c), TOC_LINE) for c in cells])
    ncols = max(len(r) for r in rows)
    for r in rows:
        while len(r) < ncols:
            r.append(Paragraph("", TOC_LINE))
    t = Table(rows, repeatRows=1)
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8.7),
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e5e5")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#aaaaaa")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def parse_markdown(text: str, is_toc: bool) -> list:
    flow = []
    lines = text.splitlines()
    i, n = 0, len(lines)
    bullet_items: list = []
    numbered_items: list = []

    def flush_bullets():
        nonlocal bullet_items
        if bullet_items:
            flow.append(ListFlowable([ListItem(Paragraph(inline_markup(b), BULLET))
                                      for b in bullet_items],
                                     bulletType="bullet", leftIndent=18, bulletFontSize=11,
                                     bulletOffsetY=-1))
            bullet_items = []

    def flush_numbered():
        # Each item keeps the exact number it had in the source (a number + text
        # pair, rendered as a hanging-indent paragraph), rather than an
        # auto-incrementing ListFlowable counter - which silently restarts at 1
        # every time a heading or blank line interrupts and re-flushes the list,
        # even though the source's own numbers (e.g. a TOC spanning many parts)
        # were never meant to restart.
        nonlocal numbered_items
        for num, text in numbered_items:
            flow.append(Paragraph(f"{num}.&nbsp;&nbsp;&nbsp;{inline_markup(text)}", NUMBERED))
        numbered_items = []

    while i < n:
        line = lines[i].rstrip()

        if not line.strip():
            flush_bullets(); flush_numbered()
            i += 1
            continue

        if re.match(r"^-{3,}$", line.strip()):
            flush_bullets(); flush_numbered()
            flow.append(Spacer(1, 10))
            i += 1
            continue

        if line.startswith("```latex") or line.startswith("```"):
            flush_bullets(); flush_numbered()
            j = i + 1
            eq_lines = []
            while j < n and not lines[j].startswith("```"):
                eq_lines.append(lines[j])
                j += 1
            rendered = " ".join(latex_to_text(l) for l in eq_lines if l.strip())
            flow.append(Paragraph(rendered, EQUATION))
            i = j + 1
            continue

        if line.startswith("# "):
            flush_bullets(); flush_numbered()
            flow.append(Paragraph(inline_markup(line[2:]), PART if not is_toc else H2))
            i += 1
            continue
        if line.startswith("## "):
            flush_bullets(); flush_numbered()
            flow.append(Paragraph(inline_markup(line[3:]), H2))
            i += 1
            continue
        if line.startswith("### "):
            flush_bullets(); flush_numbered()
            flow.append(Paragraph(inline_markup(line[4:]), H3))
            i += 1
            continue

        if line.lstrip().startswith("| "):
            flush_bullets(); flush_numbered()
            table_lines = []
            while i < n and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            flow.append(parse_table(table_lines))
            flow.append(Spacer(1, 8))
            continue

        if re.match(r"^\s*-\s+", line):
            flush_numbered()
            item = re.sub(r"^\s*-\s+", "", line)
            i += 1
            while i < n and lines[i].strip() and not re.match(r"^\s*-\s+", lines[i]) \
                    and not re.match(r"^\s*\d+\.\s+", lines[i]) \
                    and not lines[i].startswith(("#", "```", "| ")):
                item += " " + lines[i].strip()
                i += 1
            bullet_items.append(item)
            continue

        m = re.match(r"^\s*(\d+)\.\s+(.*)$", line)
        if m:
            flush_bullets()
            num, item = m.group(1), m.group(2)
            i += 1
            while i < n and lines[i].strip() and not re.match(r"^\s*-\s+", lines[i]) \
                    and not re.match(r"^\s*\d+\.\s+", lines[i]) \
                    and not lines[i].startswith(("#", "```", "| ")):
                item += " " + lines[i].strip()
                i += 1
            numbered_items.append((num, item))
            continue

        if is_toc and not line.startswith("**") and line.strip() and not line.startswith("#"):
            flush_bullets(); flush_numbered()
            flow.append(Paragraph(inline_markup(line), TOC_LINE))
            i += 1
            continue
        if is_toc and line.startswith("**") and line.endswith("**"):
            flush_bullets(); flush_numbered()
            flow.append(Paragraph(inline_markup(line), TOC_PART))
            i += 1
            continue

        # plain paragraph - gather continuation lines
        flush_bullets(); flush_numbered()
        para_lines = [line]
        i += 1
        while i < n and lines[i].strip() and not lines[i].startswith(("#", "```", "- ", "| ")) \
                and not re.match(r"^\s*\d+\.\s+", lines[i]):
            para_lines.append(lines[i].rstrip())
            i += 1
        flow.append(Paragraph(inline_markup(" ".join(para_lines)), BODY))

    flush_bullets(); flush_numbered()
    return flow


def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Times-Roman", 9)
    canvas.drawCentredString(A4[0] / 2, 0.5 * inch, str(doc.page))
    canvas.restoreState()


def main() -> None:
    doc = SimpleDocTemplate(str(OUT), pagesize=A4, topMargin=1.0 * inch,
                            bottomMargin=1.0 * inch, leftMargin=1.1 * inch,
                            rightMargin=1.1 * inch,
                            title="The Kathmandu Traffic Simulation: A Complete Manual")
    story = []

    story.append(Spacer(1, 2.2 * inch))
    story.append(Paragraph("The Kathmandu Traffic Simulation", TITLE))
    story.append(Paragraph("A Complete Manual: Theory, Methodology, and Every Design Decision", SUBTITLE))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("From the physics of traffic flow to the last line of evidence - "
                            "written so that every feature, every assumption, and every "
                            "rejected alternative is explained in full.", SUBTITLE))
    story.append(PageBreak())

    for fname in ORDER:
        path = HERE / fname
        text = path.read_text(encoding="utf-8")
        is_toc = fname == "00_toc.md"
        story.extend(parse_markdown(text, is_toc=is_toc))
        story.append(PageBreak())

    # drop the trailing page break
    if story and isinstance(story[-1], PageBreak):
        story.pop()

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
