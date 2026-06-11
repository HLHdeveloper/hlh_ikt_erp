# -*- coding: utf-8 -*-
# Import / update op.subject from pasted ciclo tables.
# Run: docker exec -i odoo19 odoo shell -d kudeaketa --no-http < import_moduluak.py

def num(v):
    v = (v or '').strip().replace(',', '.')
    return float(v) if v else 0.0

PT = {'PT': 'PT', 'PS': 'PES', 'PES': 'PES', 'PT_PES': 'PT_PES'}
PLMAP = {'PL1': 'PL1', 'PL2': 'PL2', 'PL1/PL2': 'PL1_PL2', 'PL1_PL2': 'PL1_PL2'}

# Kode berria -> BDko kode zaharra (berrizendatzeko)
ALIAS = {}

# Zutabeak (taularen ordena):
# (batch_code, code, kode_jima, pt_ps, pl, orduak, kurtsoa, gela, banaketa,
#  rpt, rpt_reala, rpt_zorretan, emandako_orduak, orduak_zorretan)
#  - pt_ps / pl hutsik  -> ez ukitu lehengo balioa
#  - rpt_reala / rpt_zorretan / emandako_orduak / orduak_zorretan hutsik
#    -> ez ukitu lehengo balioa (ziklo batzuetan ez daude zutabe horiek)
# AST3 desdoble kopiak (berriak). rpt_reala = LPZ/RPT (paste-ak ez dakar REALAK).
ROWS = [
    ('1AST3', 'DESDO_1AST3_LELA', '', '', 'PL2', '66,00',  '1º', '2', '', '2,0', '2,0', '', '', ''),
    ('1AST3', 'DESDO_1AST3_GPHM', '', '', 'PL2', '132,00', '1º', '4', '', '4,0', '4,0', '', '', ''),
    ('1AST3', 'DESDO_1AST3_ADLJ', '', '', 'PL2', '132,00', '1º', '4', '', '4,0', '4,0', '', '', ''),
    ('1AST3', 'DESDO_1AST3_GIGA', '', '', 'PL2', '132,00', '1º', '4', '', '4,0', '4,0', '', '', ''),
    ('1AST3', 'DESDO_1AST3_ASKT', '', '', 'PL2', '132,00', '1º', '4', '', '4,0', '4,0', '', '', ''),
]

DELETE_CODES = []

Subject = env['op.subject']
Batch = env['op.batch']
Banak = env['op.subject.banaketa']

batch_cache = {}
banak_cache = {}
created, updated, errors = [], [], []

for (bcode, code, kode_jima, ptps, pl, orduak, kurtsoa, gela, banak_name,
     rpt, rpt_reala, rpt_zorretan, emandako, zorretan) in ROWS:
    bcode = bcode.replace(' ', '')  # taldea kodean ez espaziorik
    code = code.replace(' ', '_')   # inolaz ere espazio gabe kodean
    while '__' in code:             # gidoi bikoitzak ez ('1ELE1 _IED' -> '1ELE1_IED')
        code = code.replace('__', '_')
    if bcode not in batch_cache:
        batch_cache[bcode] = Batch.search([('code', '=', bcode)], limit=1)
    batch = batch_cache[bcode]
    if not batch:
        errors.append("Taldea EZ aurkitua: %s (%s)" % (bcode, code))
        continue
    banak = False
    if banak_name:
        if banak_name not in banak_cache:
            banak_cache[banak_name] = Banak.search([('name', '=', banak_name)], limit=1)
        banak = banak_cache[banak_name]
        if not banak:
            errors.append("Aste banaketa EZ aurkitua: '%s' (%s)" % (banak_name, code))
            banak = False
    vals = {
        'batch_id': batch.id,
        'orduak': num(orduak),
        'kurtsoa': kurtsoa,
        'gela_orduak': num(gela),
        'rpt_total': num(rpt),
    }
    if banak_name and banak:  # aste banaketa hutsik -> ez ukitu lehengo balioa
        vals['banaketa_id'] = banak.id
    if ptps:  # pt_ps hutsik bada, ez ukitu lehengo balioa
        vals['pt_pes'] = PT.get(ptps, ptps)
    if pl:    # pl hutsik bada, ez ukitu lehengo balioa
        vals['pl'] = PLMAP.get(pl, pl)
    if kode_jima:  # kode_jima hutsik bada, ez ukitu lehengo balioa
        vals['kode_jima'] = kode_jima
    # Zutabe hauek ziklo batzuetan ez daude: hutsik bada, ez ukitu lehengo balioa
    if rpt_reala:
        vals['rpt_reala'] = num(rpt_reala)
    if rpt_zorretan:
        vals['rpt_zorretan'] = num(rpt_zorretan)
    if emandako:
        vals['emandako_orduak'] = num(emandako)
    if zorretan:
        vals['orduak_zorretan'] = num(zorretan)
    subj = Subject.search([('code', '=', code)], limit=1)
    if not subj and code in ALIAS:
        subj = Subject.search([('code', '=', ALIAS[code])], limit=1)
    if subj:
        old = subj.code
        vals['code'] = code  # romatik arabiarra berrizendatzeko (besteetan berdina)
        subj.write(vals)
        updated.append(code if old == code else '%s (<-%s)' % (code, old))
    else:
        vals['code'] = code
        vals['name'] = code
        Subject.create(vals)
        created.append(code)

deleted = []
for dcode in DELETE_CODES:
    old = Subject.search([('code', '=', dcode)], limit=1)
    if old:
        old.unlink()
        deleted.append(dcode)

env.cr.commit()
print("=== IMPORT EMAITZA ===")
print("Eguneratuak (%d): %s" % (len(updated), ', '.join(updated)))
print("Sortuak (%d): %s" % (len(created), ', '.join(created)))
print("Ezabatuak (%d): %s" % (len(deleted), ', '.join(deleted)))
print("Erroreak (%d): %s" % (len(errors), ' | '.join(errors)))
