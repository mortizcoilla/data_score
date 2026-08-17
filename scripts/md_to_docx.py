"""
scripts/md_to_docx.py
=====================

Convierte el paper markdown a un .docx con formato academico:
- Tipografia Calibri 11, headings jerarquizados
- Tablas markdown como tablas docx
- Imagenes referenciadas con [figN_xxx.png] placeholder
- Blockquotes como captions
- Listas numeradas / bullets

Uso:
    python scripts/md_to_docx.py
"""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

PROJECT_ROOT = Path(r"C:\Workspace\Modelo_DataScore")
MD_PATH = PROJECT_ROOT / "docs" / "paper1_despliegue_datamining.md"
FIG_DIR = PROJECT_ROOT / "docs" / "figures"
OUT_PATH = PROJECT_ROOT / "docs" / "paper1_despliegue_datamining.docx"

# Colores de la paleta (mismo que en el dashboard)
COL_INK = RGBColor(0x08, 0x16, 0x30)
COL_TEAL = RGBColor(0x3B, 0x87, 0x8C)
COL_TEAL_DEEP = RGBColor(0x12, 0x53, 0x58)
COL_LOSS = RGBColor(0xA0, 0x45, 0x45)
COL_GREY = RGBColor(0xC2, 0xC3, 0xC5)


def set_cell_bg(cell, color_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), color_hex)
    tcPr.append(shd)


def add_horizontal_rule(doc):
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), 'C2C3C5')
    pBdr.append(bottom)
    pPr.append(pBdr)
    return p


def add_styled_heading(doc, text, level):
    h = doc.add_heading(level=level)
    run = h.add_run(text)
    run.font.name = "Calibri"
    if level == 0:
        run.font.size = Pt(20)
        run.font.bold = True
    elif level == 1:
        run.font.size = Pt(15)
        run.font.bold = True
    elif level == 2:
        run.font.size = Pt(12.5)
        run.font.bold = True
    else:
        run.font.size = Pt(11)
        run.font.bold = True
    run.font.color.rgb = COL_INK
    return h


def parse_inline(text):
    segments = []
    pattern = re.compile(r"(\*\*([^*]+)\*\*|\*([^*]+)\*|`([^`]+)`)")
    pos = 0
    for m in pattern.finditer(text):
        if m.start() > pos:
            segments.append((text[pos:m.start()], False, False, False))
        if m.group(2):
            segments.append((m.group(2), True, False, False))
        elif m.group(3):
            segments.append((m.group(3), False, True, False))
        elif m.group(4):
            segments.append((m.group(4), False, False, True))
        pos = m.end()
    if pos < len(text):
        segments.append((text[pos:], False, False, False))
    return segments


def add_inline_paragraph(doc, text, size=11, align=None, color=None, italic=False, bold=False):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    if not parse_inline(text):
        run = p.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(size)
        run.italic = italic
        run.bold = bold
        if color is not None:
            run.font.color.rgb = color
    else:
        for seg_text, seg_bold, seg_italic, seg_code in parse_inline(text):
            if not seg_text:
                continue
            run = p.add_run(seg_text)
            run.font.name = "Calibri"
            run.font.size = Pt(size)
            run.bold = seg_bold
            run.italic = seg_italic
            if color is not None:
                run.font.color.rgb = color
            if seg_code:
                run.font.name = "Consolas"
                run.font.size = Pt(size - 1)
    return p


def add_table_from_md(doc, md_lines):
    header = [c.strip() for c in md_lines[0].strip("|").split("|")]
    rows = []
    for line in md_lines[2:]:
        cells = [c.strip() for c in line.strip("|").split("|")]
        rows.append(cells)
    table = doc.add_table(rows=1 + len(rows), cols=len(header))
    table.style = "Light Grid Accent 1"
    for j, txt in enumerate(header):
        cell = table.rows[0].cells[j]
        cell.text = ""
        p = cell.paragraphs[0]
        run = p.add_run(txt)
        run.font.bold = True
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(0xFF, 0xFD, 0xFC)
        set_cell_bg(cell, "125358")
    for i, row in enumerate(rows):
        for j, txt in enumerate(row):
            if j >= len(table.rows[i + 1].cells):
                continue
            cell = table.rows[i + 1].cells[j]
            cell.text = ""
            p = cell.paragraphs[0]
            run = p.add_run(txt)
            run.font.size = Pt(9)
    return table


def add_figure(doc, fig_filename, caption=None, width_inches=6.0):
    fig_path = FIG_DIR / fig_filename
    if not fig_path.exists():
        p = doc.add_paragraph()
        run = p.add_run(f"[Figura no encontrada: {fig_filename}]")
        run.italic = True
        run.font.color.rgb = COL_GREY
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(str(fig_path), width=Inches(width_inches))
    if caption:
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        crun = cap.add_run(caption)
        crun.font.size = Pt(9)
        crun.italic = True
        crun.font.color.rgb = COL_TEAL_DEEP


def add_code_block(doc, code_text):
    """Add a monospaced code block."""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.5)
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), 'EBEBED')
    pPr.append(shd)
    for i, line in enumerate(code_text.split("\n")):
        if i > 0:
            p.add_run().add_break()
        run = p.add_run(line)
        run.font.name = "Consolas"
        run.font.size = Pt(9)


def main():
    md = MD_PATH.read_text(encoding="utf-8")
    lines = md.split("\n")

    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(2.0)
        section.bottom_margin = Cm(2.0)
        section.left_margin = Cm(2.0)
        section.right_margin = Cm(2.0)

    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    style.paragraph_format.space_after = Pt(6)
    style.paragraph_format.line_spacing = 1.3

    header = doc.sections[0].header
    hp = header.paragraphs[0]
    hp.text = "Ortiz C. - Despliegue de modelo de propension a hurto de energia - Working paper"
    for run in hp.runs:
        run.font.size = Pt(8)
        run.font.color.rgb = COL_GREY
        run.italic = True

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped.startswith("### "):
            add_styled_heading(doc, stripped[4:], level=3)
            i += 1
            continue
        if stripped.startswith("## "):
            add_styled_heading(doc, stripped[3:], level=2)
            i += 1
            continue
        if stripped.startswith("# "):
            add_styled_heading(doc, stripped[2:], level=1)
            i += 1
            continue

        if stripped == "---":
            add_horizontal_rule(doc)
            i += 1
            continue

        # Code block (``` ... ```)
        if stripped.startswith("```"):
            code_lines = []
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("```"):
                code_lines.append(lines[j])
                j += 1
            add_code_block(doc, "\n".join(code_lines))
            i = j + 1
            continue

        # Tablas markdown
        if stripped.startswith("|") and i + 1 < len(lines) and lines[i + 1].strip().startswith("|"):
            table_lines = [line]
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith("|"):
                table_lines.append(lines[j])
                j += 1
            add_table_from_md(doc, table_lines)
            i = j
            continue

        # Blockquote
        if stripped.startswith("> "):
            add_inline_paragraph(doc, stripped[2:], size=10, color=COL_TEAL_DEEP, italic=True)
            i += 1
            continue

        # Imagen
        m_img = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", stripped)
        if m_img:
            path = m_img.group(2)
            fname = path.split("/")[-1]
            caption = None
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line.startswith("**Figura") or next_line.startswith("**Tabla"):
                    caption = next_line.strip("* ")
            add_figure(doc, fname, caption=caption, width_inches=6.0)
            i += 1
            if caption:
                i += 1
            continue

        # Listas numeradas
        if re.match(r"^\d+\.\s", stripped):
            txt = re.sub(r"^\d+\.\s", "", stripped)
            doc.add_paragraph(txt, style="List Number")
            i += 1
            continue

        # Bullets
        if stripped.startswith("- "):
            txt = stripped[2:]
            doc.add_paragraph(txt, style="List Bullet")
            i += 1
            continue

        # Parrafo normal
        add_inline_paragraph(doc, stripped, size=11)
        i += 1

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT_PATH)
    print(f"OK: {OUT_PATH}")
    print(f"  Tamano: {OUT_PATH.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
