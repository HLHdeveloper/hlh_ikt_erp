# -*- coding: utf-8 -*-
# Eguneratu SOILIK kolumna berriak (paste-an datozenak), kodearen arabera.
# Izenak, kodeak, kode_jima eta gainerako eremuak EZ dira ukitzen.
# Eremu bakoitza hutsik badator -> ez da idazten (lehengo balioa mantentzen da).
# Run: docker exec -i odoo19 odoo shell -d kudeaketa --no-http < update_new_cols.py

def num(v):
    v = (v or '').strip().replace(',', '.')
    return float(v) if v else None  # None -> ez idatzi

# (code, rpt_reala, rpt_zorretan, emandako_orduak, orduak_zorretan)  -- AST3 ING_A
# Paste-ko 1AST3_ING_A (kode_jima E201) = BDko 1AST3_ING_P_2
ROWS = [
    ('1AST3_ING_P_2', '3,0', '0,2', '99,0', ''),
]

FIELDS = ['rpt_reala', 'rpt_zorretan', 'emandako_orduak', 'orduak_zorretan']

Subject = env['op.subject']
updated, errors = [], []
for code, *cols in ROWS:
    subj = Subject.search([('code', '=', code)], limit=1)
    if not subj:
        errors.append(code)
        continue
    vals = {f: num(v) for f, v in zip(FIELDS, cols) if num(v) is not None}
    if vals:
        subj.write(vals)
    updated.append(code)

env.cr.commit()
print("=== KOLUMNA BERRIAK EGUNERATZE EMAITZA ===")
print("Eguneratuak (%d): %s" % (len(updated), ', '.join(updated)))
print("EZ aurkituak (%d): %s" % (len(errors), ', '.join(errors)))
