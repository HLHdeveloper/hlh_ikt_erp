# -*- coding: utf-8 -*-
# Mintegi LPO/FOL (empleabilidad EIP/IPE/FOL + TUTO_3). Todo teoria=gela, praktika=0.
# Codes ya resueltos al code REAL de Odoo (Excel arabe _1/_2 -> Odoo romano _I/_II salvo MSS2/SEA3).
APPLY = True
ROWS = [
    ('1OLHMEK3_IPE',[2],2,0),
    ('3OLHMEK3_FOL',[2],2,0),
    ('3OLHMEK3_TUTO_3',[1],1,0),
    ('1OLHELE3_IPE',[2],2,0),
    ('1ELE1_IPE',[2],2,0),
    ('1EMF1_IPE',[2],2,0),
    ('1INF4_EIP',[2],2,0),
    ('1AST3_EIP_I',[2,2],4,0),        # Excel EIP_1
    ('2AST3_EIP_II',[2,1],3,0),       # Excel EIP_2
    ('1FMD3_EIP_I',[2,2],4,0),
    ('2FMD3_EIP_II',[2,1],3,0),
    ('1MEK2_EIP_I',[2,2],4,0),
    ('2MEK2_EIP_II',[2,1],3,0),
    ('1MLE2_EIP_I',[2,2],4,0),
    ('2MLE2_EIP_II',[2,1],3,0),
    ('1MSS2_EIP_1',[2,2],4,0),        # Odoo arabe
    ('2MSS2_EIP_2',[2,1],3,0),        # Odoo arabe
    ('1IEA2A_IPE_I',[2,2],4,0),       # Excel IPE_1
    ('2IEA2A_EIP_II',[2,1],3,0),
    ('1IEA2D_IPE_I',[2,2],4,0),       # Excel EIP_1 -> Odoo IPE_I
    ('2IEA2D_EIP_II',[2,1],3,0),
    ('1SEA3_EIP_1',[2,2],4,0),        # Odoo arabe
    ('2SEA3_EIP_2',[2,1],3,0),        # Odoo arabe
]
Subject = env['op.subject']; Ban = env['op.subject.banaketa']; TP = env['op.subject.teoria.praktika']
ok, partial, bad = [], [], []; n_ban=n_tp=0
for code, sess, teoria, praktika in ROWS:
    rec = Subject.search([('code','=',code)], limit=1)
    if not rec: bad.append('NOT_FOUND %s' % code); continue
    gela = int(round(rec.gela_orduak or 0)); s_sum = sum(sess)
    ban_name = '/'.join(str(x) for x in sorted(sess, reverse=True)); tp_name = '%dT/%dP' % (teoria, praktika)
    vals, notes = {}, []
    if s_sum != gela: notes.append('BAN ses=%d!=gela=%d' % (s_sum, gela))
    else:
        b = Ban.search([('name','=',ban_name),('guztira','=',gela)], limit=1)
        if b: vals['banaketa_id'] = b.id
        else: notes.append('BAN "%s" inexistente' % ban_name)
    if teoria+praktika != gela: notes.append('TP T+P=%d!=gela=%d' % (teoria+praktika, gela))
    else:
        t = TP.search([('name','=',tp_name),('guztira','=',gela)], limit=1)
        if t: vals['teoria_praktika_id'] = t.id
        else: notes.append('TP "%s" inexistente' % tp_name)
    if APPLY and vals: rec.write(vals)
    if 'banaketa_id' in vals: n_ban+=1
    if 'teoria_praktika_id' in vals: n_tp+=1
    tag = '%-16s ban=%-5s tp=%-6s gela %d' % (code, ban_name, tp_name, gela)
    (partial if notes else ok).append(('PARCIAL %s | %s' % (tag,'; '.join(notes))) if notes else ('OK %s' % tag))
print('OK=%d PARCIAL=%d NOT_FOUND=%d' % (len(ok), len(partial), len(bad)))
for l in partial+bad: print(l)
print('APPLY=%s | ban=%d | tp=%d' % (APPLY, n_ban, n_tp))
if APPLY: env.cr.commit(); print('>>> GUARDADO')
