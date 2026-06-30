# -*- coding: utf-8 -*-
# Mintegi AST (1AST3, 2AST3). Todo teoria=gela, praktika=0. GHEG excluido (ambiguo).
APPLY = True

# (code_odoo, [sesiones], teoria, praktika)
ROWS = [
    # 1AST3
    ('1AST3_GIGA',[2,2],4,0),
    ('1AST3_GPHM',[2,2],4,0),
    ('1AST3_LELA',[2],2,0),
    ('1AST3_ASKT',[2,2],4,0),
    ('1AST3_ADLJ',[2,2],4,0),
    ('1AST3_PSAI',[1],1,0),
    ('1AST3_PSAD_2',[2],2,0),
    # 2AST3
    ('2AST3_TADI',[2,2],4,0),
    ('2AST3_HAUT_1',[2,2],4,0),
    ('2AST3_GAIN',[2,2],4,0),
    ('2AST3_HAUT_2',[2,2],4,0),     # Excel MOD_OPT_2
    ('2AST3_KAKU',[2,2,2],6,0),
    ('2AST3_ANTU',[3,2],5,0),
    # 2AST3_GHEG -> ambiguo, pendiente
]

Subject = env['op.subject']
Ban = env['op.subject.banaketa']
TP = env['op.subject.teoria.praktika']

ok, partial, bad = [], [], []
n_ban, n_tp = 0, 0
for code, sess, teoria, praktika in ROWS:
    rec = Subject.search([('code','=',code)], limit=1)
    if not rec:
        bad.append('NOT_FOUND   %s' % code); continue
    gela = int(round(rec.gela_orduak or 0))
    s_sum = sum(sess)
    ban_name = '/'.join(str(x) for x in sorted(sess, reverse=True))
    tp_name = '%dT/%dP' % (teoria, praktika)
    vals, notes = {}, []
    if s_sum != gela:
        notes.append('BAN: ses=%d != gela=%d' % (s_sum, gela))
    else:
        ban = Ban.search([('name','=',ban_name),('guztira','=',gela)], limit=1)
        if ban: vals['banaketa_id'] = ban.id
        else: notes.append('BAN "%s" inexistente' % ban_name)
    if (teoria + praktika) != gela:
        notes.append('TP: T+P=%d != gela=%d' % (teoria+praktika, gela))
    else:
        tp = TP.search([('name','=',tp_name),('guztira','=',gela)], limit=1)
        if tp: vals['teoria_praktika_id'] = tp.id
        else: notes.append('TP "%s" inexistente' % tp_name)
    if APPLY and vals: rec.write(vals)
    if 'banaketa_id' in vals: n_ban += 1
    if 'teoria_praktika_id' in vals: n_tp += 1
    tag = '%-16s ban=%-6s tp=%-6s gela %d' % (code, ban_name, tp_name, gela)
    (partial if notes else ok).append(('PARCIAL %s | %s' % (tag, '; '.join(notes))) if notes else ('OK %s' % tag))

print('\n=== OK (%d) ===' % len(ok))
for l in ok: print(l)
print('\n=== PARCIAL (%d) ===' % len(partial))
for l in partial: print(l)
print('\n=== NOT_FOUND (%d) ===' % len(bad))
for l in bad: print(l)
print('\nAPPLY=%s | filas=%d | ban=%d | tp=%d' % (APPLY, len(ROWS), n_ban, n_tp))
if APPLY: env.cr.commit(); print('>>> GUARDADO')
