# -*- coding: utf-8 -*-
# Mintegi INGELESA (ING/KOG/HG). Todo teoria=gela, praktika=0.
APPLY = True
ROWS = [
    ('1OLHMEK3_TUTO_1',[1],1,0),
    ('1OLHMEK3_KOG_1',[2,1],3,0),
    ('1OLHMEK3_KOG_0',[2,1],3,0),
    ('2OLHMEK3_KOG_2',[2,2,1],5,0),
    ('2OLHMEK3_HG_2',[2],2,0),
    ('3OLHMEK3_HG_3',[2],2,0),
    ('1OLHELE3_KOG_1',[2,1],3,0),
    ('1OLHELE3_KOG_0',[2,1],3,0),
    ('2OLHELE3_TUTO_2',[1],1,0),
    ('2OLHELE3_KOG_2',[2,2,1],5,0),
    ('2OLHELE3_HG_2',[2],2,0),
    ('1ELE1_KOG_1',[2,2],4,0),
    ('2ELE1_KOG_2',[2,2,2,2],8,0),
    ('1EMF1_KOG_1',[2,2],4,0),
    ('2EMF1_KOG_2',[2,2,2,2],8,0),
    ('1INF4_KOG_1',[2,2],4,0),
    ('2INF4_KOG_2',[2,2,2,2],8,0),
    ('1AST3_ING_P_2',[2,1],3,0),
    ('1AST3_ING_P',[2],2,0),
    ('1FMD3_ING_P',[2],2,0),
    ('1MEK2_ING_P',[2],2,0),
    ('1MLE2_ING_P',[2],2,0),
    ('1MSS2_ING_P',[2],2,0),
    ('1IEA2A_ING_P',[2],2,0),
    ('1IEA2D_ING_P',[2],2,0),
    ('2SEA3_ING_P',[2,1],3,0),
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
    tag = '%-16s ban=%-8s tp=%-7s gela %d' % (code, ban_name, tp_name, gela)
    (partial if notes else ok).append(('PARCIAL %s | %s' % (tag,'; '.join(notes))) if notes else ('OK %s' % tag))
print('\n=== OK (%d) ===' % len(ok))
for l in ok: print(l)
print('\n=== PARCIAL (%d) ===' % len(partial))
for l in partial: print(l)
print('\n=== NOT_FOUND (%d) ===' % len(bad))
for l in bad: print(l)
print('\nAPPLY=%s | filas=%d | ban=%d | tp=%d' % (APPLY, len(ROWS), n_ban, n_tp))
if APPLY: env.cr.commit(); print('>>> GUARDADO')
