#!/usr/bin/env python3
# RubriPDF — generate fillable PDF evaluation sheets and extract grades.
# Copyright (C) 2026  Susana Sotelo Docio
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
RubriPDF
Generates fillable PDF evaluation sheets from marking criteria and student lists.
Usage: python app.py  (opens browser automatically at http://localhost:5000)
"""

import io
import os
import re
import csv
import sys
import threading
import webbrowser
from io import StringIO
from flask import Flask, render_template, request, jsonify, send_file

# Base directory for bundled resources: the PyInstaller extraction dir when
# frozen into an executable, else this file's directory (pip / source run).
BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))

# Directory holding the bundled TrueType fonts (full Unicode coverage)
FONT_DIR = os.path.join(BASE_DIR, 'fonts')


# Strings that appear in the generated PDF, keyed by language name
_LANG = {
    'galician':   {'toc': 'Índice de alumnos',    'eval': 'Avaliación',  'criterion': 'Criterio',  'points': 'Puntos', 'final': 'Nota final', 'obs': 'Observacións',  'obs_cont': 'Observacións (cont.)', 'np': 'Non presentado'},
    'portuguese': {'toc': 'Índice de alunos',     'eval': 'Avaliação',   'criterion': 'Critério',  'points': 'Pontos', 'final': 'Nota final', 'obs': 'Observações',   'obs_cont': 'Observações (cont.)',  'np': 'Não compareceu'},
    'spanish':    {'toc': 'Índice de alumnos',    'eval': 'Evaluación',  'criterion': 'Criterio',  'points': 'Puntos', 'final': 'Nota final', 'obs': 'Observaciones', 'obs_cont': 'Observaciones (cont.)', 'np': 'No presentado'},
    'english':    {'toc': 'Student index',        'eval': 'Assessment',  'criterion': 'Criterion', 'points': 'Points', 'final': 'Final mark', 'obs': 'Notes',         'obs_cont': 'Notes (cont.)',         'np': 'Absent'},
}


# ---------------------------------------------------------------------------
# PDF generator (fpdf2)
# ---------------------------------------------------------------------------

def generate_pdf_python(data):
    from fpdf import FPDF
    from fpdf.annotations import PDFAnnotation
    from fpdf.output import OutputProducer
    from fpdf.syntax import Name, PDFString

    t         = _LANG.get(data.get('language', 'english'), _LANG['english'])
    title     = data.get('title', '')
    subject   = data.get('subject', '')
    year      = data.get('year', '')
    students  = data.get('students', [])
    criteria  = data.get('criteria', [])
    try:
        obs_pages = int(data.get('obs_pages', 1))
    except (TypeError, ValueError):
        obs_pages = 1
    obs_pages = max(0, min(obs_pages, 20))   # clamp to a sane range
    obs_template = bool(data.get('obs_template', True))

    # Optional starter text for the first notes box: the rubric items with a
    # rule under each and blank space below, to guide per-item comments.
    obs_tpl = None
    if obs_template and criteria:
        _lines = []
        for i, crit in enumerate(criteria, 1):
            _lines.append(f"### {i}. {crit.get('description', '').strip()}")
            _lines += ['', '', '']
        obs_tpl = '\n'.join(_lines).rstrip('\n')

    try:
        hr, hg, hb = [int(x.strip()) for x in data.get('color', '210,235,230').split(',')]
    except Exception:
        hr, hg, hb = 210, 235, 230

    header_str = f"{subject} - {year}" if year else subject
    # Cover subtitle: the assessment title with the year (e.g. "Práctica 4 - 2025/26")
    cover_subtitle = ' - '.join(p for p in (title, year) if p)

    # ── AcroForm support ─────────────────────────────────────────────────────

    class FormOutputProducer(OutputProducer):
        """Injects the AcroForm dictionary into the PDF catalog."""
        def _finalize_catalog(self, catalog_obj, pages_root_obj, first_page_obj,
                               sig_annotation_obj, xmp_metadata_obj,
                               struct_tree_root_obj, outline_dict_obj):
            super()._finalize_catalog(
                catalog_obj, pages_root_obj, first_page_obj,
                sig_annotation_obj, xmp_metadata_obj,
                struct_tree_root_obj, outline_dict_obj,
            )
            widgets = []
            for page in self._iter_pages_in_order():
                if page.annots:
                    for ann in page.annots:
                        if isinstance(ann, PDFAnnotation) and str(ann.subtype) == 'Widget':
                            widgets.append(ann)
            if widgets:
                fields_str = " ".join(f"{ann.id} 0 R" for ann in widgets)
                catalog_obj.acro_form = (
                    f"<</Fields [{fields_str}]"
                    # Default resources: declare the fonts referenced by the
                    # field /DA strings (/Helv for text, /ZaDb for the checkbox
                    # tick) so viewers other than Acrobat render field content.
                    f" /DR <</Font <<"
                    f"/Helv <</Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding>>"
                    f" /ZaDb <</Type /Font /Subtype /Type1 /BaseFont /ZapfDingbats>>"
                    f">>>>"
                    f" /DA (/Helv 10 Tf 0 g)"
                    f" /NeedAppearances true>>"
                )

    class PDF(FPDF):
        def header(self):
            if getattr(self, '_show_header', False):
                self.set_font(FONT, '', 9)
                self.set_text_color(80, 80, 80)
                self.cell(0, 6, header_str, align='L', new_x='LMARGIN', new_y='NEXT')
                self.set_draw_color(180, 180, 180)
                self.set_line_width(0.2)
                self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
                self.set_draw_color(0)
                self.set_text_color(0)
                self.ln(5)

        def footer(self):
            self.set_y(-13)
            self.set_font(FONT, '', 9)
            self.set_text_color(120, 120, 120)
            self.cell(0, 6, str(self.page_no()), align='C')
            self.set_text_color(0)

        def _widget(self, x_mm, y_mm, w_mm, h_mm, field_name, field_type,
                    multiline=False, font_size=10, q=0, border_width=1,
                    value=None):
            """Add an AcroForm Widget annotation at the given mm coordinates.
            q: 0=left, 1=centre, 2=right (PDF /Q quadding).
            value: initial text value for a text field (editable by the user)."""
            k = self.k
            ann = PDFAnnotation(
                "Widget",
                x_mm * k,
                (self.h - y_mm) * k,   # PDF origin is bottom-left
                w_mm * k,
                h_mm * k,
                field_type=field_type,
                title=field_name,       # /T = field name in Widget context
                border_width=border_width,
            )
            if field_type == "Btn":
                ann.v   = Name("Off")
                ann.d_a = "(/ZaDb 10 Tf 0 g)"
            if field_type == "Tx":
                ann.d_a = f"(/Helv {font_size} Tf 0 g)"
                ann.q   = q
                if value:
                    ann.v = PDFString(value)
            if multiline and field_type == "Tx":
                ann.ff = 4096 | 8388608  # bit 13=Multiline, bit 24=DoNotScroll
            self.pages[self.page].add_annotation(ann)

        def output(self, name='', **kwargs):
            kwargs.setdefault('output_producer_class', FormOutputProducer)
            return super().output(name=name, **kwargs)

    pdf = PDF(orientation='P', unit='mm', format='A4')
    pdf.set_margins(25, 20, 25)
    pdf.set_auto_page_break(True, margin=20)
    pdf._show_header = False

    # Register the bundled DejaVu family (full Unicode) so that names with
    # characters outside latin-1 no longer crash PDF generation. Falls back to
    # the core Helvetica font if the bundled files are unavailable.
    try:
        pdf.add_font('DejaVu', '',  os.path.join(FONT_DIR, 'DejaVuSans.ttf'))
        pdf.add_font('DejaVu', 'B', os.path.join(FONT_DIR, 'DejaVuSans-Bold.ttf'))
        FONT = 'DejaVu'
    except Exception:
        FONT = 'Helvetica'

    ew = pdf.w - pdf.l_margin - pdf.r_margin  # effective width ≈ 160 mm

    # ── Cover page ──────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.ln(25)
    pdf.set_font(FONT, 'B', 22)
    pdf.multi_cell(0, 11, subject, align='C')       # Materia (prominent)
    pdf.ln(4)
    pdf.set_font(FONT, '', 14)
    pdf.multi_cell(0, 8, cover_subtitle, align='C')  # assessment title - year
    pdf.ln(12)

    pdf.set_font(FONT, 'B', 13)
    pdf.cell(0, 8, t['toc'], new_x='LMARGIN', new_y='NEXT')
    pdf.ln(2)

    # Pre-create one internal link per student for the TOC
    student_links = [pdf.add_link() for _ in students]

    pdf.set_font(FONT, '', 11)
    for s, lnk in zip(students, student_links):
        pdf.cell(6)
        pdf.set_text_color(0, 0, 180)
        pdf.cell(0, 7, f'-  {s}', link=lnk, new_x='LMARGIN', new_y='NEXT')
        pdf.set_text_color(0)

    # Hidden read-only fields (on the cover page) storing each criterion's
    # maximum points, so the grade extractor can flag any item scored above it.
    k = pdf.k
    for cidx, crit in enumerate(criteria):
        ann_max = PDFAnnotation(
            "Widget", 0, k, k, k,      # 1mm × 1mm at bottom-left corner
            field_type="Tx", title=f"cmax{cidx}", border_width=0,
        )
        ann_max.v  = PDFString(f"{float(crit.get('points', 0) or 0):g}")
        ann_max.ff = 1   # ReadOnly
        pdf.pages[pdf.page].add_annotation(ann_max)

    # ── Per-student sections ─────────────────────────────────────────────────
    pdf._show_header = True

    # Achievement levels (the analytic-rubric scale): (label, fraction-of-max).
    # Overridable via config['levels'] = [{'label':.., 'frac':..}, ...].
    _LVL = {
        'galician':   [('Insuficiente', 0.0), ('Escaso', 0.25), ('Suficiente', 0.5), ('Notable', 0.8), ('Excelente', 1.0)],
        'spanish':    [('Insuficiente', 0.0), ('Escaso', 0.25), ('Suficiente', 0.5), ('Notable', 0.8), ('Sobresaliente', 1.0)],
        'english':    [('Insufficient', 0.0), ('Poor', 0.25), ('Sufficient', 0.5), ('Good', 0.8), ('Excellent', 1.0)],
        'portuguese': [('Insuficiente', 0.0), ('Fraco', 0.25), ('Suficiente', 0.5), ('Bom', 0.8), ('Excelente', 1.0)],
    }
    if data.get('levels'):
        levels = [(l.get('label', ''), float(l.get('frac', 0) or 0)) for l in data['levels']]
    else:
        levels = _LVL.get(data.get('language', 'english'), _LVL['english'])
    n_lvl         = len(levels)
    derive_points = bool(data.get('derive_points', False))

    # Hidden read-only fields (on the cover): each level's fraction + the derive
    # flag, so the grade extractor can turn a ticked level into points.
    for lk, (_, frac) in enumerate(levels):
        af = PDFAnnotation("Widget", 0, k, k, k, field_type="Tx",
                           title=f"lvlfrac{lk}", border_width=0)
        af.v  = PDFString(f"{frac:g}")
        af.ff = 1
        pdf.pages[pdf.page].add_annotation(af)
    ad = PDFAnnotation("Widget", 0, k, k, k, field_type="Tx",
                       title="derivepts", border_width=0)
    ad.v  = PDFString("1" if derive_points else "0")
    ad.ff = 1
    pdf.pages[pdf.page].add_annotation(ad)

    # Table column widths: criterion | one column per level | points
    cw_points = 20
    cw_lvl    = 11
    cw_lvls   = cw_lvl * n_lvl
    cw_crit   = ew - cw_lvls - cw_points
    row_h     = 7

    for stu_idx, (student, lnk) in enumerate(zip(students, student_links), 1):
        pdf.add_page()
        pdf.set_link(lnk)   # anchor for TOC link

        # Hidden read-only field storing the student name (used for CSV extraction)
        k = pdf.k
        ann_name = PDFAnnotation(
            "Widget", 0, k, k, k,      # 1mm × 1mm at bottom-left corner
            field_type="Tx", title=f"name{stu_idx}", border_width=0,
        )
        ann_name.v  = PDFString(student)
        ann_name.ff = 1   # ReadOnly
        pdf.pages[pdf.page].add_annotation(ann_name)

        # Coloured name box — leave room below the page header
        pdf.ln(4)
        y0 = pdf.get_y()
        pdf.set_fill_color(hr, hg, hb)
        pdf.rect(pdf.l_margin, y0, ew, 13, style='F')
        pdf.set_xy(pdf.l_margin + 4, y0 + 2.5)
        # Shrink the font so a long name never overflows the coloured box
        name_w = ew - 8
        fs = 13
        pdf.set_font(FONT, 'B', fs)
        while fs > 8 and pdf.get_string_width(student) > name_w:
            fs -= 0.5
            pdf.set_font(FONT, 'B', fs)
        pdf.cell(name_w, 8, student)
        pdf.set_xy(pdf.l_margin, y0 + 16)

        # Section title
        pdf.set_font(FONT, 'B', 12)
        pdf.cell(0, 7, t['eval'], new_x='LMARGIN', new_y='NEXT')
        pdf.ln(1)

        # Level legend (numbers -> labels)
        pdf.set_font(FONT, '', 8)
        pdf.cell(0, 5, '     '.join(f"{i+1} = {lab}" for i, (lab, _) in enumerate(levels)),
                 new_x='LMARGIN', new_y='NEXT')
        pdf.ln(1)

        # Table header
        pdf.set_fill_color(220, 220, 220)
        pdf.set_font(FONT, 'B', 10)
        pdf.cell(cw_crit, row_h, t['criterion'], border=1, fill=True)
        for lk in range(n_lvl):
            pdf.cell(cw_lvl, row_h, str(lk + 1), border=1, fill=True, align='C')
        pdf.cell(cw_points, row_h, t['points'], border=1, fill=True, align='C',
                 new_x='LMARGIN', new_y='NEXT')

        # Criteria rows — with Widget overlays for OK and Points
        pdf.set_font(FONT, '', 10)
        for cidx, crit in enumerate(criteria):
            desc  = f"{crit.get('description', '')} ({crit.get('points', 0):g} pts)"
            xs    = pdf.l_margin
            ys    = pdf.get_y()
            pdf.multi_cell(cw_crit, row_h, desc, border=1)
            actual_h = pdf.get_y() - ys

            # Level columns: one checkbox per achievement level
            for lk in range(n_lvl):
                lxp = xs + cw_crit + lk * cw_lvl
                pdf.set_xy(lxp, ys)
                pdf.cell(cw_lvl, actual_h, '', border=1, align='C')
                cb = min(actual_h, cw_lvl) - 1.5
                pdf._widget(lxp + (cw_lvl - cb) / 2, ys + (actual_h - cb) / 2, cb, cb,
                            f"lvl{stu_idx}c{cidx}_{lk}", "Btn")

            # Points column: draw border; text Widget centred inside
            px = xs + cw_crit + cw_lvls
            pdf.set_xy(px, ys)
            pdf.cell(cw_points, actual_h, '', border=1, align='C',
                     new_x='LMARGIN', new_y='NEXT')
            pdf._widget(px, ys, cw_points, actual_h, f"pts{stu_idx}c{cidx}", "Tx", q=1)

        pdf.ln(6)

        # Nota final — label + text field Widget
        pdf.set_font(FONT, '', 11)
        y_row = pdf.get_y()
        lbl   = t['final'] + ': '
        pdf.cell(pdf.get_string_width(lbl), 7, lbl)
        fx = pdf.get_x() + 2   # 2mm gap between label and field
        pdf._widget(fx, y_row, 33, 7, f"final{stu_idx}", "Tx")

        # "Not presented" checkbox + label (when ticked, the CSV grade is "NP")
        np_x = fx + 33 + 12
        cb   = 5
        pdf.set_line_width(0.3)
        pdf.rect(np_x, y_row + 1, cb, cb)
        pdf.set_line_width(0.2)
        pdf._widget(np_x, y_row + 1, cb, cb, f"np{stu_idx}", "Btn", border_width=0)
        pdf.set_xy(np_x + cb + 2, y_row)
        pdf.cell(0, 7, t['np'])
        pdf.ln(12)

        # Observations heading + multiline Widget filling remaining page space
        pdf.set_font(FONT, 'B', 12)
        pdf.cell(0, 7, t['obs'], new_x='LMARGIN', new_y='NEXT')
        pdf.ln(1)

        obs_y = pdf.get_y()
        obs_h = pdf.h - pdf.b_margin - obs_y - 12  # leave ~12mm at bottom
        if obs_h > 5:
            pad = 2.5  # internal padding in mm
            pdf.set_line_width(0.3)
            pdf.rect(pdf.l_margin, obs_y, ew, obs_h)
            pdf.set_line_width(0.2)
            pdf._widget(pdf.l_margin + pad, obs_y + pad, ew - 2*pad, obs_h - 2*pad,
                        f"obs{stu_idx}p0", "Tx", multiline=True, border_width=0,
                        value=obs_tpl)

        # Extra observation pages
        for pidx in range(obs_pages):
            pdf.add_page()
            pdf.ln(4)
            pdf.set_font(FONT, 'B', 12)
            pdf.cell(0, 7, t['obs_cont'], new_x='LMARGIN', new_y='NEXT')
            pdf.ln(1)
            obs_y = pdf.get_y()
            obs_h = pdf.h - pdf.b_margin - obs_y - 12
            if obs_h > 5:
                pad = 2.5
                pdf.set_line_width(0.3)
                pdf.rect(pdf.l_margin, obs_y, ew, obs_h)
                pdf.set_line_width(0.2)
                pdf._widget(pdf.l_margin + pad, obs_y + pad, ew - 2*pad, obs_h - 2*pad,
                            f"obs{stu_idx}p{pidx+1}", "Tx", multiline=True,
                            border_width=0)

    return bytes(pdf.output())


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')


def _md_to_html(md):
    """Tiny Markdown subset -> HTML for the in-app help (no dependency). Supports
    # headings, paragraphs, - / * and 1. lists, **bold**, *italic* / _italic_,
    [text](url) links and ![alt](src) images. Content is authored by the maintainer."""
    import html as _html

    def inline(t):
        t = _html.escape(t)
        t = re.sub(r'!\[([^\]]*)\]\(([^)\s]+)\)',
                   r'<img src="\2" alt="\1" class="img-fluid my-2">', t)
        t = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', r'<a href="\2" target="_blank" rel="noopener">\1</a>', t)
        t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
        t = re.sub(r'__(.+?)__', r'<strong>\1</strong>', t)
        t = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<em>\1</em>', t)
        t = re.sub(r'(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])', r'<em>\1</em>', t)
        return t

    out, para = [], []

    def flush():
        if para:
            out.append('<p>' + ' '.join(para) + '</p>')
            para.clear()

    lines = md.replace('\r\n', '\n').split('\n')
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        h = re.match(r'(#{1,6})\s+(.*)', s)
        if h:
            flush()
            n = min(len(h.group(1)) + 3, 6)
            out.append(f'<h{n} class="fw-bold text-primary mt-3 mb-1">{inline(h.group(2))}</h{n}>')
            i += 1
        elif re.match(r'[-*]\s+', s):
            flush()
            items = []
            while i < len(lines) and re.match(r'[-*]\s+', lines[i].strip()):
                items.append('<li>' + inline(re.sub(r'^[-*]\s+', '', lines[i].strip())) + '</li>')
                i += 1
            out.append('<ul>' + ''.join(items) + '</ul>')
        elif re.match(r'\d+\.\s+', s):
            flush()
            items = []
            while i < len(lines) and re.match(r'\d+\.\s+', lines[i].strip()):
                items.append('<li>' + inline(re.sub(r'^\d+\.\s+', '', lines[i].strip())) + '</li>')
                i += 1
            out.append('<ol>' + ''.join(items) + '</ol>')
        elif s == '':
            flush()
            i += 1
        else:
            para.append(inline(s))
            i += 1
    flush()
    return '\n'.join(out)


@app.route('/help/<lang>')
def help_page(lang):
    """Serve the help manual (Markdown in help/<lang>.md) rendered to HTML."""
    if lang not in ('gl', 'es', 'en', 'pt'):
        lang = 'en'
    path = os.path.join(BASE_DIR, 'help', f'{lang}.md')
    if not os.path.exists(path):
        return '', 404
    with open(path, encoding='utf-8') as f:
        return _md_to_html(f.read())


@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    try:
        pdf_bytes = generate_pdf_python(data)
        return send_file(io.BytesIO(pdf_bytes), as_attachment=True,
                         download_name='evaluation.pdf', mimetype='application/pdf')
    except Exception as e:
        return jsonify({'error': f'PDF generation failed: {e}'}), 500


@app.route('/extract', methods=['POST'])
def extract():
    from pypdf import PdfReader

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    try:
        reader = PdfReader(request.files['file'])
        fields = reader.get_fields() or {}
    except Exception as e:
        return jsonify({'error': f'Could not read PDF: {e}'}), 400

    detailed = request.form.get('detailed') == '1'

    # Decimal separator + CSV delimiter follow the UI language: English uses "."
    # (comma-delimited); gl/es/pt use "," as decimal, so fields must be ";"-delimited.
    lang      = request.form.get('lang', '')
    decimal   = {'gl': ',', 'es': ',', 'pt': ','}.get(lang, '.')
    delimiter = ';' if decimal == ',' else ','

    def _val(field):
        v = field.value if hasattr(field, 'value') else ''
        return str(v).strip() if v not in (None, '') else ''

    def _num(s):
        """Parse a grade string, tolerating comma as decimal separator."""
        try:
            return float(str(s).replace(',', '.'))
        except (TypeError, ValueError):
            return None

    def _fmt_grade(s):
        """Render a grade with the locale decimal; non-numbers (NP, '') pass through."""
        n = _num(s)
        return f'{n:g}'.replace('.', decimal) if n is not None else s

    def _csv_safe(value):
        """Neutralise CSV/formula injection: a cell that a spreadsheet would
        treat as a formula (leading = + - @, or a control char) is prefixed
        with an apostrophe so it is shown as literal text."""
        s = '' if value is None else str(value)
        if s[:1] in ('=', '+', '-', '@', '\t', '\r'):
            return "'" + s
        return s

    # ── Gather all fields per student (pts/ok always read, for the checks) ────
    rows = {}   # idx -> {name, final, pts:{c:str}, ok:{c:str}, lvl:{c:int}}
    max_crit = 0

    def _new_row():
        return {'name': '', 'final': '', 'pts': {}, 'ok': {}, 'lvl': {}}

    for field_name, field in fields.items():
        m = re.match(r'^(name|final)(\d+)$', field_name)
        if m:
            ftype, idx = m.group(1), int(m.group(2))
            rows.setdefault(idx, _new_row())
            rows[idx][ftype] = _val(field)
            continue
        m = re.match(r'^(ok|pts)(\d+)c(\d+)$', field_name)
        if m:
            ftype, idx, cidx = m.group(1), int(m.group(2)), int(m.group(3))
            row = rows.setdefault(idx, _new_row())
            row[ftype][cidx] = _val(field)
            max_crit = max(max_crit, cidx + 1)
            continue
        m = re.match(r'^lvl(\d+)c(\d+)_(\d+)$', field_name)
        if m and _val(field) not in ('', 'Off', '/Off'):
            idx, cidx, lk = int(m.group(1)), int(m.group(2)), int(m.group(3))
            rows.setdefault(idx, _new_row())['lvl'][cidx] = lk
            max_crit = max(max_crit, cidx + 1)

    # Per-criterion maximum points (hidden fields on the cover page). Absent in
    # PDFs made by older versions, in which case the over-max check is skipped.
    max_pts = {}
    for field_name, field in fields.items():
        m = re.match(r'^cmax(\d+)$', field_name)
        if m:
            v = _num(_val(field))
            if v is not None:
                max_pts[int(m.group(1))] = v

    # Level fractions + derive-points flag (hidden fields). When deriving, a
    # ticked level sets that criterion's points to fraction × its maximum.
    level_fracs = {}
    derive = False
    for field_name, field in fields.items():
        m = re.match(r'^lvlfrac(\d+)$', field_name)
        if m:
            level_fracs[int(m.group(1))] = _num(_val(field))
        elif field_name == 'derivepts':
            derive = _val(field) == '1'
    if derive:
        for r in rows.values():
            for c, lk in r['lvl'].items():
                frac, mx = level_fracs.get(lk), max_pts.get(c)
                if frac is not None and mx is not None:
                    r['pts'][c] = f'{frac * mx:g}'

    # "Not presented" checkboxes: when ticked, the grade becomes "NP" and the
    # numeric quality checks are skipped for that student.
    np_set = set()
    for field_name, field in fields.items():
        m = re.match(r'^np(\d+)$', field_name)
        if m and _val(field) not in ('', 'Off', '/Off'):
            np_set.add(int(m.group(1)))

    if not rows:
        return jsonify({'error': 'no_fields'}), 400

    # ── Quality checks: build structured warnings; auto-fill blank finals ─────
    warnings = []
    for idx in sorted(rows):
        r    = rows[idx]
        name = r['name'] or f'#{idx}'

        # Not presented: grade is "NP". No grade box (per-criterion points or
        # final) may be filled — flag it if any is.
        if idx in np_set:
            if any(r['pts'].values()) or r['final']:
                warnings.append({'t': 'np_has_grades', 's': name})
            r['final'] = 'NP'
            continue

        blank, nan, values = [], [], {}
        for c in range(max_crit):
            raw = r['pts'].get(c, '')
            if raw == '':
                blank.append(c)
            elif _num(raw) is None:
                nan.append(c)
            else:
                values[c] = _num(raw)

        all_filled = max_crit > 0 and not blank and not nan
        sum_pts    = sum(values.values())
        final_raw  = r['final']
        final_num  = _num(final_raw) if final_raw else None

        if blank:
            warnings.append({'t': 'crit_empty', 's': name, 'c': blank})
        if nan:
            warnings.append({'t': 'crit_nan', 's': name, 'c': nan})

        # Any item scored above its own maximum
        for c, v in values.items():
            if c in max_pts and v > max_pts[c] + 0.01:
                warnings.append({'t': 'crit_over', 's': name, 'c': c,
                                 'v': v, 'max': max_pts[c]})

        if final_raw == '':
            if all_filled:
                r['final'] = f'{sum_pts:g}'          # auto-fill from the sum
                warnings.append({'t': 'final_autofill', 's': name, 'v': sum_pts})
            else:
                warnings.append({'t': 'final_empty', 's': name})
        elif final_num is None:
            warnings.append({'t': 'final_nan', 's': name, 'v': final_raw})
        elif all_filled and abs(final_num - sum_pts) > 0.01:
            warnings.append({'t': 'final_mismatch', 's': name,
                             'f': final_num, 'sum': sum_pts})

    # ── Build the CSV (finals may have been auto-filled above) ────────────────
    output = StringIO()
    writer = csv.writer(output, delimiter=delimiter)
    student_lbl, final_lbl, lvl_lbl, pts_lbl = {
        'gl': ('Alumno/a', 'Nota final', 'Nivel', 'ptos'),
        'es': ('Alumno/a', 'Nota final', 'Nivel', 'ptos'),
        'pt': ('Aluno/a',  'Nota final', 'Nível', 'ptos'),
    }.get(lang, ('Student', 'Final grade', 'Level', 'pts'))
    header = [student_lbl, final_lbl]
    if detailed:
        for c in range(max_crit):
            header += [f'C{c+1} {lvl_lbl}', f'C{c+1} {pts_lbl}']
    writer.writerow(header)
    for idx in sorted(rows):
        r = rows[idx]
        line = [r['name'], _fmt_grade(r['final'])]
        if detailed:
            for c in range(max_crit):
                lvl = r['lvl'].get(c)
                line += ['' if lvl is None else str(lvl + 1), _fmt_grade(r['pts'].get(c, ''))]
        writer.writerow([_csv_safe(cell) for cell in line])

    return jsonify({
        'csv':      output.getvalue(),
        'count':    len(rows),
        'warnings': warnings,
    })


@app.route('/parse-csv', methods=['POST'])
def parse_csv():
    """Plain list of student names: one name per line (a single-column CSV/txt).

    Each line is taken as a whole name, verbatim — never split on commas, since
    names legitimately contain them ("Apelidos, Nome"). No header is assumed: a
    first line is only dropped if it is literally a column label like "Nome", so
    the first real student is never swallowed (the old DictReader bug)."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    raw = request.files['file'].read()
    for enc in ('utf-8-sig', 'utf-8', 'latin-1'):
        try:
            content = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        return jsonify({'error': 'Cannot decode file encoding'}), 400

    def unwrap(v):                                   # drop a fully-quoted wrapper
        if len(v) >= 2 and v[0] == '"' and v[-1] == '"':
            return v[1:-1].replace('""', '"')
        return v

    name_labels = {'nome', 'nombre', 'name', 'nom', 'alumno', 'alumna', 'aluno'}
    values = [unwrap(ln.strip()) for ln in content.splitlines() if ln.strip()]
    if values and values[0].lower() in name_labels:  # skip a bare header label
        values = values[1:]

    students = []
    for v in values:
        if v.lower() in name_labels:                 # stray repeated header
            continue
        if re.match(r'(?i)^n[ºouú]m?\.?$', v):       # bare ordinal ("Nº", "Núm.")
            continue
        students.append(v)

    if not students:
        return jsonify({'error': 'No names found in the file'}), 400

    # Safety net: a real multi-column file (e.g. a Moodle CSV export) was probably
    # uploaded by mistake. We still import each line whole (never split a name),
    # but flag it. Only ; \t | count — commas can't, since names contain ", ".
    resp = {
        'students':        students,
        'columns':         [],
        'selected_column': None,
        'format':          'generic',
        'count':           len(students),
        'duplicates':      len(students) - len(set(students)),
    }
    for delim in (';', '\t', '|'):
        if sum(delim in s for s in students) >= max(2, int(0.8 * len(students))):
            resp['note'] = 'looks_multicolumn'
            break
    return jsonify(resp)


def _read_spreadsheet_rows(file):
    """
    Read a spreadsheet file (.xls, .xlsx, or HTML-disguised-as-xls) and return
    a list of rows, each row being a list of stripped strings.
    """
    raw = file.read()
    ext = file.filename.rsplit('.', 1)[-1].lower()

    # Detect HTML-disguised-as-xls (very common in Spanish university systems)
    if raw.lstrip()[:5].lower().startswith(b'<'):
        from bs4 import BeautifulSoup
        for enc in ('utf-8-sig', 'utf-8', 'latin-1'):
            try:
                html = raw.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            html = raw.decode('latin-1', errors='replace')
        soup = BeautifulSoup(html, 'html.parser')
        rows = []
        for tr in soup.find_all('tr'):
            cells = [td.get_text(separator=' ', strip=True) for td in tr.find_all(['td', 'th'])]
            if any(cells):
                rows.append(cells)
        return rows

    if ext == 'xls':
        import xlrd
        wb = xlrd.open_workbook(file_contents=raw)
        sh = wb.sheet_by_index(0)
        return [[str(sh.cell_value(r, c)).strip() for c in range(sh.ncols)]
                for r in range(sh.nrows)]

    # xlsx
    import openpyxl
    from io import BytesIO
    wb = openpyxl.load_workbook(BytesIO(raw), read_only=True, data_only=True)
    sh = wb.active
    return [[str(v).strip() if v is not None else '' for v in row]
            for row in sh.iter_rows(values_only=True)]


# Header labels that mark a *given name* vs a *surname* column, across the
# languages Moodle and USC export in (gl/es/en/pt). Used to recognise the
# split-name (Moodle) layout and reassemble it as "Apelidos, Nome".
GIVEN_NAME_KEYWORDS = {'nome', 'nombre', 'name', 'first name', 'nome próprio', 'primeiro nome'}
SURNAME_KEYWORDS    = {'apelidos', 'apelido', 'apellidos', 'apellido', 'surname',
                       'last name', 'sobrenome', 'sobrenomes'}


def _column_cells(rows, start, col):
    """Non-empty values of a column, from row index `start` onward."""
    return [row[col].strip() for row in rows[start:]
            if col < len(row) and row[col].strip()]


def _email_column(rows, start, width):
    """Index of the column holding email addresses, or None. Language-independent —
    a Moodle participants export always carries one, whatever the UI language."""
    best, best_frac = None, 0.0
    for c in range(width):
        vals = _column_cells(rows, start, c)
        if len(vals) < 2:
            continue
        frac = sum('@' in v and '.' in v.split('@')[-1] for v in vals) / len(vals)
        if frac >= 0.6 and frac > best_frac:
            best, best_frac = c, frac
    return best


def _looks_like_name_column(rows, start, col):
    """True if the column reads like names (text, not numbers/emails/codes)."""
    vals = _column_cells(rows, start, col)
    if not vals:
        return False
    def nameish(v):
        return '@' not in v and any(ch.isalpha() for ch in v) and not v.replace(' ', '').isdigit()
    return sum(nameish(v) for v in vals) / len(vals) >= 0.7


@app.route('/parse-xls', methods=['POST'])
def parse_xls():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    try:
        rows = _read_spreadsheet_rows(file)
    except Exception as e:
        return jsonify({'error': f'Could not read file: {e}'}), 400

    if not rows:
        return jsonify({'error': 'Empty file'}), 400

    width_all = max(len(r) for r in rows)

    # Find header row: the first row with a cell matching a known name label.
    # Robust against outer layout rows (logo, title, etc.).
    name_keywords = {'nome', 'nombre', 'name', 'nom', 'alumno', 'alumna', 'aluno'}
    header_idx = None
    for i, row in enumerate(rows):
        non_empty = [c for c in row if c.strip()]
        if len(non_empty) <= 15 and any(c.strip().lower() in name_keywords for c in row):
            header_idx = i
            break
    if header_idx is None:
        # Structural fallback: a flat export in a language whose labels we don't
        # know, recognised by its email column (Moodle always has one). Its header
        # is the first row.
        if _email_column(rows, 0, width_all) is not None:
            header_idx = 0
        else:
            return jsonify({'error': 'Could not find a name column in the file'}), 400

    headers = rows[header_idx]
    lower   = [h.strip().lower() for h in headers]
    width   = len(headers)

    # Moodle exports split the name across "Nome"/"Apelidos" (localised). Assemble
    # a "Apelidos, Nome" column — the same shape the USC single-column list uses —
    # so both sources look identical downstream.
    given_idx   = next((i for i, h in enumerate(lower) if h in GIVEN_NAME_KEYWORDS), None)
    surname_idx = next((i for i, h in enumerate(lower) if h in SURNAME_KEYWORDS), None)
    email_idx   = _email_column(rows, header_idx + 1, width)

    inferred = False
    if given_idx is not None and surname_idx is not None:
        fmt = 'moodle'                                # confident: labels recognised
    elif (email_idx is not None and email_idx >= 2
          and _looks_like_name_column(rows, header_idx + 1, email_idx - 2)
          and _looks_like_name_column(rows, header_idx + 1, email_idx - 1)):
        # Labels unrecognised, but the fixed Moodle order is [given, surname, email].
        # Use position, and flag it so the UI asks the user to double-check.
        given_idx, surname_idx = email_idx - 2, email_idx - 1
        fmt = 'moodle'
        inferred = True
    else:
        given_idx = surname_idx = None               # fall back to a single column

    combined_col = None
    if given_idx is not None and surname_idx is not None:
        combined_col = f'{headers[surname_idx]}, {headers[given_idx]}'
        while combined_col in headers:               # keep the synthetic key unique
            combined_col += ' '
        preferred = combined_col
    else:
        name_pref = ['nome', 'nombre', 'name', 'nom', 'alumno', 'alumna', 'aluno']
        preferred = next((h for h in headers if h.strip().lower() in name_pref), None) or \
                    (headers[0] if headers else None)
        fmt = 'usc' if 'documento' in lower else 'generic'

    # Data rows: after the header, drop empty rows, layout artefacts, repeated
    # headers and bare enumeration markers. Every decision is based on the NAME
    # value only, so real names (Noa, Nuria, Núria…) are never dropped.
    data_rows = []
    for row in rows[header_idx + 1:]:
        if not any(c.strip() for c in row):          # empty row
            continue
        if len(row) > len(headers) * 2:              # layout artefact
            continue
        rowdict = dict(zip(headers, row))
        if combined_col is not None:
            given   = row[given_idx].strip()   if given_idx   < len(row) else ''
            surname = row[surname_idx].strip() if surname_idx < len(row) else ''
            name = f'{surname}, {given}' if surname and given else (surname or given)
            rowdict[combined_col] = name
        else:
            name = (rowdict.get(preferred) or '').strip() if preferred else ''
        if not name:                                 # summary row, empty name
            continue
        if name.lower() in name_keywords:            # repeated header row
            continue
        if re.match(r'(?i)^n[ºouú]m?\.?$', name):    # bare ordinal ("Nº", "Núm.")
            continue
        data_rows.append(rowdict)

    students = [(r.get(preferred) or '').strip() for r in data_rows
                if (r.get(preferred) or '').strip()] if preferred else []

    columns = [h for h in headers if h]
    if combined_col is not None:
        columns = [combined_col] + columns

    # Serialise rows back to JSON for column re-selection
    resp = {
        'students':        students,
        'columns':         columns,
        'selected_column': preferred,
        'rows':            data_rows,
        'format':          fmt,
        'count':           len(students),
        'duplicates':      len(students) - len(set(students)),
    }
    if inferred:                       # name columns guessed by position, not label
        resp['note'] = 'inferred_columns'
    return jsonify(resp)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '5000'))       # override if 5000 is taken
    url  = f'http://localhost:{port}'

    def _open():
        import time; time.sleep(1.2)
        webbrowser.open(url)

    threading.Thread(target=_open, daemon=True).start()
    print(f"RubriPDF running at {url}  (Ctrl+C to quit)")
    from waitress import serve                        # production WSGI server
    serve(app, host='127.0.0.1', port=port)
