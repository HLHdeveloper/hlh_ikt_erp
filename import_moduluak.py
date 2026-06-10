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

# (batch_code, code, pt_ps, pl, orduak, kurtsoa, gela, banaketa, rpt, zorretan)
# pt_ps hutsik -> ez ukitu lehengo balioa
ROWS = [
    ('1OLHMEK3', '1OLHMEK3_OBF',    'PT',  '', '165,00', '1º', '5', '3/2', '5,0', ''),
    ('1OLHMEK3', '1OLHMEK3_SCM',    'PT',  '', '132,00', '1º', '4', '3/1', '4,0', ''),
    ('1OLHMEK3', '1OLHMEK3_IPE',    'PES', '', '66,00',  '1º', '2', '1/1', '2,0', ''),
    ('1OLHMEK3', '1OLHMEK3_ZIA 1',  'PT',  '', '132,00', '1º', '4', '2/2', '4,0', ''),
    ('1OLHMEK3', '1OLHMEK3_KOG 1',  'PT',  '', '132,00', '1º', '3', '2/1', '4,0', ''),
    ('1OLHMEK3', '1OLHMEK3_TUTO 1', 'PT',  '', '33,00',  '1º', '1', '1',   '1,0', ''),
    ('2OLHMEK3', '2OLHMEK3_CAPV',   'PT',  '', '132,00', '2º', '4', '3/1', '4,0', ''),
    ('2OLHMEK3', '2OLHMEK3_OBCL',   'PT',  '', '198,00', '2º', '6', '3/3', '6,0', ''),
    ('2OLHMEK3', '2OLHMEK3_KOG_2',  'PT',  '', '168,00', '2º', '5', '',    '5,1', ''),
    ('2OLHMEK3', '2OLHMEK3 ZIA 2',  'PT',  '', '126,00', '2º', '4', '2/2', '3,8', ''),
    ('2OLHMEK3', '2OLHMEK3_TUTO 2', 'PT',  '', '33,00',  '2º', '1', '1',   '1,0', ''),
    ('3OLHMEK3', '3OLHMEK3_EEE',    'PT',  '', '192,00', '3º', '9', '',    '5,8', ''),
    ('3OLHMEK3', '3OLHMEK3_OBMH',   'PT',  '', '168,00', '3º', '8', '',    '5,1', ''),
    ('3OLHMEK3', '3OLHMEK3_FOL',    'PT',  '', '53,00',  '3º', '2', '',    '1,6', ''),
    ('3OLHMEK3', '3OLHMEK3_TUTO 3', '',    '', '25,00',  '3º', '1', '',    '0,2', ''),
]

Subject = env['op.subject']
Batch = env['op.batch']
Banak = env['op.subject.banaketa']

batch_cache = {}
banak_cache = {}
created, updated, errors = [], [], []

for bcode, code, ptps, pl, orduak, kurtsoa, gela, banak_name, rpt, zorretan in ROWS:
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
        'banaketa_id': banak.id if banak else False,
        'rpt_total': num(rpt),
        'orduak_zorretan': num(zorretan),
    }
    if ptps:  # pt_ps hutsik bada, ez ukitu lehengo balioa
        vals['pt_pes'] = PT.get(ptps, ptps)
    if pl:    # pl hutsik bada, ez ukitu lehengo balioa
        vals['pl'] = PLMAP.get(pl, pl)
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

env.cr.commit()
print("=== IMPORT EMAITZA ===")
print("Eguneratuak (%d): %s" % (len(updated), ', '.join(updated)))
print("Sortuak (%d): %s" % (len(created), ', '.join(created)))
print("Erroreak (%d): %s" % (len(errors), ' | '.join(errors)))
