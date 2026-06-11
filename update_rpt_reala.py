# -*- coding: utf-8 -*-
# Eguneratu SOILIK rpt_reala kolumna, kodearen arabera lotuta.
# Izenak, kodeak eta gainerako eremuak EZ dira ukitzen.
# Run: docker exec -i odoo19 odoo shell -d kudeaketa --no-http < update_rpt_reala.py

def num(v):
    v = (v or '').strip().replace(',', '.')
    return float(v) if v else 0.0

# (code, rpt_reala)  -- EXP_FG (rpt_reala = LPZ/RPT, paste-ak ez dakar REALAK)
ROWS = [
    ('FG_TECNOL',   '2,5'),
    ('FG_OPTIM',    '3,2'),
    ('FG_SCANNER',  '1,9'),
    ('FG_MODEL',    '5,7'),
    ('FG_POSTPRO',  '2,5'),
    ('FG_MAK_KONP', '3,2'),
]

Subject = env['op.subject']
updated, errors = [], []
for code, rpt_reala in ROWS:
    subj = Subject.search([('code', '=', code)], limit=1)
    if not subj:
        errors.append(code)
        continue
    subj.write({'rpt_reala': num(rpt_reala)})  # SOILIK rpt_reala
    updated.append(code)

env.cr.commit()
print("=== rpt_reala EGUNERATZE EMAITZA ===")
print("Eguneratuak (%d): %s" % (len(updated), ', '.join(updated)))
print("EZ aurkituak (%d): %s" % (len(errors), ', '.join(errors)))
