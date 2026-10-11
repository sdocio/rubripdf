#!/usr/bin/env python3
"""
Normalise the student names in a USC "Secretaría Virtual" list export.

The export (``Listaxe de alumnos.xls``) is HTML-disguised-as-.xls with a nested
wrapper table and names in ``APELIDOS, Nome`` order, with inconsistent casing and
stray whitespace. This tool cleans and Title-Cases the names so you can work from
a *normalised source*. It never touches anything but the name text.

Two outputs, both using the SAME name function (so names match across them):

  --identical PATH   a byte-structure-identical copy of the input (same nested
                     HTML), with the Nome column as the ONLY change. Import this
                     back into RubriPDF.
  --flat PATH        a clean table with just the 5 data columns (no wrapper
                     nesting). Format by extension: .csv, .xlsx or .xls.

With no output flags, both are written next to the input.

Normalisation rules (deliberately conservative — no guessing):
  * collapse whitespace, remove the stray space before commas;
  * Title Case, keeping name particles (de/la/da/e/…) lower-cased mid-name;
  * accents are NOT invented: an accent-less ALL-CAPS "ANON" becomes "Anon",
    never guessed as "Añón".
"""

import argparse
import csv
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

NAME_KEYWORDS = {'nome', 'nombre', 'name', 'nom', 'alumno', 'alumna', 'aluno'}

# Lower-cased mid-name particles (surname connectors / conjunctions). Only applied
# when NOT the first token of a segment, so a surname *starting* with one keeps
# its capital ("De la Rega" -> "De la Rega").
PARTICLES = {
    'de', 'do', 'da', 'dos', 'das', 'del', 'della', 'di', 'la', 'las', 'lo',
    'los', 'le', 'e', 'y', 'i', 'van', 'von', 'der', 'den', 'du',
}


# ── name normalisation ───────────────────────────────────────────────────────

def _cap_word(word):
    """Capitalise one word, capitalising each hyphen/apostrophe sub-part."""
    def cap(s):
        return s[:1].upper() + s[1:].lower() if s else s
    # keep the delimiters (- ' ’) between sub-parts
    return ''.join(p if p in "-'’" else cap(p)
                   for p in re.split(r"([-'’])", word))


def normalize_name(raw):
    """'GONDAR VEIGA, BRAIS' -> 'Gondar Veiga, Brais'; 'Seoane , I' -> 'Seoane, I'."""
    s = ' '.join(raw.split())              # collapse every whitespace run to one space
    s = re.sub(r'\s*,\s*', ', ', s)        # tidy comma spacing (kills "Seoane ,")
    s = s.strip().strip(',').strip()
    out_segments = []
    for segment in s.split(','):
        tokens = [t for t in segment.strip().split(' ') if t]
        rebuilt = []
        for i, tok in enumerate(tokens):
            low = tok.lower()
            rebuilt.append(low if (i > 0 and low in PARTICLES) else _cap_word(tok))
        out_segments.append(' '.join(rebuilt))
    return ', '.join(seg for seg in out_segments if seg)


# ── table reading (nested-HTML aware) ────────────────────────────────────────

def _load_soup(path):
    raw = Path(path).read_bytes()
    if raw.lstrip()[:1] != b'<':
        sys.exit(f"error: {path} is not the HTML-based USC .xls this tool expects.")
    for enc in ('utf-8-sig', 'utf-8', 'latin-1'):
        try:
            return BeautifulSoup(raw.decode(enc), 'html.parser')
        except UnicodeDecodeError:
            continue
    return BeautifulSoup(raw.decode('latin-1', errors='replace'), 'html.parser')


def _direct_cell_rows(soup):
    """Every <tr> as its list of DIRECT <td>/<th> cells (skips the wrapper row,
    whose single cell merely contains the nested table)."""
    rows = []
    for tr in soup.find_all('tr'):
        cells = tr.find_all(['td', 'th'], recursive=False)
        if cells:
            rows.append(cells)
    return rows


def _locate_table(rows):
    """Return (header_idx, name_col) for the real data table, or exit if not found."""
    for idx, cells in enumerate(rows):
        texts = [c.get_text(' ', strip=True) for c in cells]
        for col, txt in enumerate(texts):
            if txt.strip().lower() in NAME_KEYWORDS:
                return idx, col
    sys.exit("error: could not find a 'Nome' header column in the file.")


def _is_data_row(cells, width, name_col):
    if len(cells) != width:                       # footer / title / stray rows
        return False
    name = cells[name_col].get_text(' ', strip=True)
    if not name:
        return False
    if name.lower() in NAME_KEYWORDS:             # repeated header
        return False
    if re.match(r'(?i)^n[ºouú]m?\.?$', name):     # bare ordinal
        return False
    return True


def normalise_in_place(soup):
    """Title-Case the Nome cell of every data row, in place. Returns the count."""
    rows = _direct_cell_rows(soup)
    header_idx, name_col = _locate_table(rows)
    width = len(rows[header_idx])
    count = 0
    for cells in rows[header_idx + 1:]:
        if not _is_data_row(cells, width, name_col):
            continue
        cell = cells[name_col]
        original = cell.get_text(' ', strip=True)
        cell.clear()
        cell.append(normalize_name(original) or original)
        count += 1
    return count


def extract_flat_rows(soup, normalise=True):
    """Return (headers, data_rows) with the 5 columns; names normalised unless asked not to."""
    rows = _direct_cell_rows(soup)
    header_idx, name_col = _locate_table(rows)
    header_cells = rows[header_idx]
    width = len(header_cells)
    headers = [c.get_text(' ', strip=True) for c in header_cells]
    data = []
    for cells in rows[header_idx + 1:]:
        if not _is_data_row(cells, width, name_col):
            continue
        values = [c.get_text(' ', strip=True) for c in cells]
        if normalise:
            values[name_col] = normalize_name(values[name_col])
        data.append(values)
    return headers, data


# ── writers ──────────────────────────────────────────────────────────────────

def write_flat(path, headers, rows):
    path = Path(path)
    ext = path.suffix.lower()
    if ext == '.csv':
        with open(path, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f)
            w.writerow(headers)
            w.writerows(rows)
    elif ext == '.xlsx':
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(headers)
        for r in rows:
            ws.append(r)
        wb.save(path)
    elif ext == '.xls':
        # A plain single-table HTML .xls (no nesting): RubriPDF reads this fine.
        def esc(s):
            return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
        head = ''.join(f'<th>{esc(h)}</th>' for h in headers)
        body = ''.join('<tr>' + ''.join(f'<td>{esc(v)}</td>' for v in r) + '</tr>'
                       for r in rows)
        html = ('<html><head><meta http-equiv="Content-Type" '
                'content="text/html; charset=utf-8"></head><body><table>'
                f'<tr>{head}</tr>{body}</table></body></html>')
        Path(path).write_bytes(html.encode('utf-8'))
    else:
        sys.exit(f"error: unsupported --flat extension '{ext}' (use .csv, .xlsx or .xls).")


# ── CLI ──────────────────────────────────────────────────────────────────────

def main(argv=None):
    ap = argparse.ArgumentParser(description="Normalise names in a USC student-list .xls.")
    ap.add_argument('input', help="the USC 'Listaxe de alumnos.xls' export")
    ap.add_argument('--identical', metavar='PATH',
                    help="write a structure-identical .xls with only names changed")
    ap.add_argument('--flat', metavar='PATH',
                    help="write a clean 5-column table (.csv, .xlsx or .xls)")
    ap.add_argument('--dry-run', action='store_true',
                    help="just print before -> after, write nothing")
    args = ap.parse_args(argv)

    src = Path(args.input)
    if not src.exists():
        sys.exit(f"error: {src} not found.")

    # A single parse drives both outputs, so names are guaranteed identical.
    _, flat_rows = extract_flat_rows(_load_soup(src))
    soup = _load_soup(src)                          # fresh tree to edit in place
    count = normalise_in_place(soup)

    if args.dry_run:
        headers, raw_rows = extract_flat_rows(_load_soup(src), normalise=False)
        name_col = headers.index(next(h for h in headers if h.lower() in NAME_KEYWORDS))
        changed = 0
        print(f"{count} students — before -> after (only changes shown):")
        for orig_row, norm_row in zip(raw_rows, flat_rows):
            orig, norm = orig_row[name_col], norm_row[name_col]
            if orig != norm:
                changed += 1
                print(f"  {orig!r:42} -> {norm!r}")
        print(f"({changed} of {count} names changed)")
        return

    identical = args.identical
    flat = args.flat
    if not identical and not flat:                 # default: write both next to input
        identical = str(src.with_name(src.stem + '-normalizado' + src.suffix))
        flat = str(src.with_name(src.stem + '-plano.csv'))

    if identical:
        Path(identical).write_bytes(str(soup).encode('utf-8'))
        print(f"wrote {identical}  ({count} students, structure identical)")
    if flat:
        headers, _ = extract_flat_rows(_load_soup(src))
        write_flat(flat, headers, flat_rows)
        print(f"wrote {flat}  ({count} students, flat 5-column)")


if __name__ == '__main__':
    main()
