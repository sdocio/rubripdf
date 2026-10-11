"""Tests for tools/normalize_names.py — the USC student-list name normaliser.

These use invented data. The utility must never lose a student, must change only
the name text, and both output formats must carry byte-identical normalised names.
"""

import csv
import io
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import app  # noqa: E402
from tools import normalize_names as nn  # noqa: E402


# ── unit: the normalisation rule ─────────────────────────────────────────────

# NOTE: all names below are invented — never copy data from real exports.
@pytest.mark.parametrize('raw, expected', [
    ('GONDAR VEIGA, BRAIS',      'Gondar Veiga, Brais'),      # ALL-CAPS -> Title
    ('Seoane , Icía',            'Seoane, Icía'),             # stray space before comma
    ('De la Rega Vilar, Sabela', 'De la Rega Vilar, Sabela'),  # leading + mid particle
    ('Torres da Ponte, Uxía',    'Torres da Ponte, Uxía'),    # mid particle 'da'
    ('MÉNDEZ AÑÓN, IAGO',        'Méndez Añón, Iago'),         # keep existing accents
    ('Rega  Ferro,  Noela',      'Rega Ferro, Noela'),        # collapse double spaces
    ('ferreiro souto, uxío',     'Ferreiro Souto, Uxío'),     # lowercase -> Title
    ('PORTA E RIOS, XOEL',       'Porta e Rios, Xoel'),       # conjunction stays low
])
def test_normalize_name(raw, expected):
    assert nn.normalize_name(raw) == expected


def test_normalize_does_not_invent_accents():
    # ALL-CAPS lost its accent in the source; we must NOT guess it back.
    assert nn.normalize_name('RUBAL ANON, XOEL') == 'Rubal Anon, Xoel'


# ── fixture: a synthetic USC export (nested wrapper table, title, footer) ─────
# All names are invented.

USC_NAMES = [
    'SEOANE , ICÍA',                 # ALL-CAPS + stray space before comma
    'De la Rega Vilar, SABELA',      # particles + mixed case
    'MÉNDEZ AÑÓN, IAGO',             # accents and ñ
    'nogareda mar, noa',             # lowercase, surname starting with "No"
]
EXPECTED = ['Seoane, Icía', 'De la Rega Vilar, Sabela',
            'Méndez Añón, Iago', 'Nogareda Mar, Noa']


def _usc_xls_bytes(names):
    body = ''.join(
        f'<tr><td>{i:08d}X</td><td>{n}</td><td>FB</td><td></td>'
        f'<td>Módulo de Formación Básica</td></tr>'
        for i, n in enumerate(names, 1)
    )
    inner = ('<tr><td>Listaxe de alumnos e alumnas</td></tr>'
             '<tr><td>Documento</td><td>Nome</td><td>Carácter</td>'
             '<td>Modo</td><td>Módulo</td></tr>'
             + body +
             f'<tr><td>Nº de alumnos/as : {len(names)}</td></tr>')
    return ('<html><head><meta http-equiv="Content-Type" '
            'content="text/html; charset=utf-8"></head><body><table><tr><td>'
            f'<table>{inner}</table></td></tr></table></body></html>').encode('utf-8')


@pytest.fixture
def sample(tmp_path):
    p = tmp_path / 'Listaxe de alumnos.xls'
    p.write_bytes(_usc_xls_bytes(USC_NAMES))
    return p


# ── integration: identical output re-imports cleanly into RubriPDF ───────────

def test_identical_output_roundtrips_through_rubripdf(sample, tmp_path):
    out = tmp_path / 'norm.xls'
    nn.main([str(sample), '--identical', str(out)])

    client = app.app.test_client()
    d = client.post('/parse-xls',
                    data={'file': (io.BytesIO(out.read_bytes()), 'norm.xls')}).get_json()
    assert d['selected_column'] == 'Nome'
    assert d['columns'] == ['Documento', 'Nome', 'Carácter', 'Modo', 'Módulo']
    assert d['students'] == EXPECTED          # none lost, all normalised


def test_identical_output_changes_only_names(sample, tmp_path):
    out = tmp_path / 'norm.xls'
    nn.main([str(sample), '--identical', str(out)])
    text = out.read_text(encoding='utf-8')
    # non-name data is untouched...
    assert 'Módulo de Formación Básica' in text
    assert '00000001X' in text
    assert 'Nº de alumnos/as : 4' in text
    # ...and the messy originals are gone, replaced by clean forms.
    assert 'SEOANE , ICÍA' not in text
    assert 'Seoane, Icía' in text


# ── integration: flat output has 5 columns and the SAME normalised names ─────

def test_flat_csv_output(sample, tmp_path):
    out = tmp_path / 'plano.csv'
    nn.main([str(sample), '--flat', str(out)])

    with open(out, encoding='utf-8-sig', newline='') as f:
        rows = list(csv.reader(f))
    assert rows[0] == ['Documento', 'Nome', 'Carácter', 'Modo', 'Módulo']
    assert [r[1] for r in rows[1:]] == EXPECTED          # names match the identical output
    assert len(rows) == 1 + len(USC_NAMES)               # header + every student, no footer


def test_flat_xlsx_output(sample, tmp_path):
    out = tmp_path / 'plano.xlsx'
    nn.main([str(sample), '--flat', str(out)])

    import openpyxl
    ws = openpyxl.load_workbook(out).active
    rows = [['' if c is None else str(c) for c in row] for row in ws.iter_rows(values_only=True)]
    assert rows[0] == ['Documento', 'Nome', 'Carácter', 'Modo', 'Módulo']
    assert [r[1] for r in rows[1:]] == EXPECTED
    assert len(rows) == 1 + len(USC_NAMES)               # header + every student, no footer


def test_flat_xls_output_reimports_into_rubripdf(sample, tmp_path):
    # the flat .xls is a plain single-table HTML sheet — RubriPDF must read it back
    out = tmp_path / 'plano.xls'
    nn.main([str(sample), '--flat', str(out)])

    client = app.app.test_client()
    d = client.post('/parse-xls',
                    data={'file': (io.BytesIO(out.read_bytes()), 'plano.xls')}).get_json()
    assert d['selected_column'] == 'Nome'
    assert d['students'] == EXPECTED


def test_flat_unsupported_extension_errors(sample, tmp_path):
    with pytest.raises(SystemExit):
        nn.main([str(sample), '--flat', str(tmp_path / 'plano.json')])


def test_default_writes_both_next_to_input(sample):
    nn.main([str(sample)])
    folder = sample.parent
    assert (folder / 'Listaxe de alumnos-normalizado.xls').exists()
    assert (folder / 'Listaxe de alumnos-plano.csv').exists()
