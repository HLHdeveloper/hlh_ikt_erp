# -*- coding: utf-8 -*-
# Mintegi MEKANIKA. Empareja por code literal. Valida banaketa y teoria/praktika
# por separado (escribe lo que valide). DRY-RUN salvo APPLY=True.
APPLY = True

# (code_odoo, [sesiones], teoria, praktika)   PRO (gela 0) omitidos.
ROWS = [
    # 1OLHMEK3
    ('1OLHMEK3_SCM',[3,1],1,3),
    ('1OLHMEK3_SOLA',[2],0,2),
    ('1OLHMEK3_PROSOL_1',[2],0,2),
    ('1OLHMEK3_OBF',[3,2],1,4),
    ('1OLHMEK3_MARRAZ_1',[2],2,0),
    ('1OLHMEK3_DIGI_1',[2],2,0),
    ('1OLHMEK3_TUTO_1',[1],1,0),       # Excel TUTO1
    # 2OLHMEK3
    ('2OLHMEK3_PROSOL_2',[2],0,2),
    ('2OLHMEK3_OBCL',[3,3],1,5),
    ('2OLHMEK3_CAPV',[3,1],1,3),
    ('2OLHMEK3_TIG',[2],0,2),
    ('2OLHMEK3_MARRAZ_2',[2],2,0),
    ('2OLHMEK3_DIGI_2',[2],2,0),
    # 1EMF1
    ('1EMF1_SCM',[3,1],1,3),
    ('1EMF1_OBF',[3,1,1],2,4),         # T/P=6 != gela 5 -> banaketa si, T/P no
    ('1EMF1_OBCL',[3,2,1],2,4),
    ('1EMF1_CAPV',[3,1],4,0),
    ('1EMF1_TUTO_1',[1],1,0),
    # 2EMF1
    ('2EMF1_OBMH',[4,3],0,7),
    ('2EMF1_TUTO_2',[1],1,0),
    # 3OLHMEK3
    ('3OLHMEK3_OBMH',[3,3,2],0,8),
    ('3OLHMEK3_MARRAZ_3',[2],2,0),
    ('3OLHMEK3_DIGI_3',[2],2,0),
    ('3OLHMEK3_KBP',[2],0,2),
    # 1MEK2
    ('1MEK2_TXBF',[4,4,3],0,11),
    ('1MEK2_MEPR',[3,2],5,0),
    ('1MEK2_METR',[2,2],4,0),
    ('1MEK2_INTG',[2,2],4,0),
    # 2MEK2
    ('2MEK2_ZKME',[3,3,2],2,6),
    ('2MEK2_HAUT_1',[2,2],2,2),
    ('2MEK2_HAUT_2',[2,2],2,2),
    ('2MEK2_SIAU',[2,2],4,0),
    ('2MEK2_PSAD',[2,1],3,0),
    ('2MEK2_PSAI',[2],2,0),
    ('2MEK2_UKPF',[3,3],2,4),
    # 1MLE2
    ('1MLE2_AUPH',[3,2,2],2,5),
    ('1MLE2_FATE',[3,4],3,4),
    ('1MLE2_PSAD',[2],2,0),
    # 2MLE2
    ('2MLE2_LAML',[3,2],2,3),
    ('2MLE2_LOMT',[3],3,0),
    ('2MLE2_HAUT_1',[2,2],2,2),
    ('2MLE2_MUMA',[3,3],2,4),
    ('2MLE2_PSAI',[2],2,0),
    # 1FMD3
    ('1FMD3_PMDI',[4,3,2],3,6),
    ('1FMD3_FMIG',[3,3],2,4),
    ('1FMD3_FMTE',[3,3],4,2),
    ('1FMD3_PSAD_2',[2],2,0),          # Excel PSAD2
    ('1FMD3_PSAI',[1],1,0),
    # 2FMD3
    ('2FMD3_TPED',[3,3,2],2,6),
    ('2FMD3_HAUT_1',[2,2],2,2),
    ('2FMD3_PPMD',[3,2],3,2),
    ('2FMD3_GMED',[2,2],2,2),
    ('2FMD3_FAU',[2,2,2],2,4),
    # EXP_FG (codes literales sin prefijo de taldea)
    ('FG_TECNOL',[4],4,0),
    ('FG_OPTIM',[3,2],2,3),
    ('FG_SCANNER',[3],0,3),
    ('FG_MODEL',[4,3,2],3,6),
    ('FG_POSTPRO',[2,2],0,4),
    ('FG_MAK_KONP',[3,2],2,3),
]

Subject = env['op.subject']
Ban = env['op.subject.banaketa']
TP = env['op.subject.teoria.praktika']

ok, partial, bad = [], [], []
n_ban, n_tp = 0, 0
for code, sess, teoria, praktika in ROWS:
    rec = Subject.search([('code','=',code)], limit=1)
    if not rec:
        bad.append('NOT_FOUND   %s' % code)
        continue
    gela = int(round(rec.gela_orduak or 0))
    s_sum = sum(sess)
    ban_name = '/'.join(str(x) for x in sorted(sess, reverse=True))
    tp_name = '%dT/%dP' % (teoria, praktika)
    vals, notes = {}, []
    # banaketa
    if s_sum != gela:
        notes.append('BAN: sesiones=%d != gela=%d' % (s_sum, gela))
    else:
        ban = Ban.search([('name','=',ban_name),('guztira','=',gela)], limit=1)
        if ban:
            vals['banaketa_id'] = ban.id
        else:
            notes.append('BAN: "%s" inexistente' % ban_name)
    # teoria/praktika
    if (teoria + praktika) != gela:
        notes.append('TP: T+P=%d != gela=%d' % (teoria + praktika, gela))
    else:
        tp = TP.search([('name','=',tp_name),('guztira','=',gela)], limit=1)
        if tp:
            vals['teoria_praktika_id'] = tp.id
        else:
            notes.append('TP: "%s" inexistente' % tp_name)
    if APPLY and vals:
        rec.write(vals)
    if 'banaketa_id' in vals: n_ban += 1
    if 'teoria_praktika_id' in vals: n_tp += 1
    tag = '%-20s ban=%-7s tp=%-7s gela %d' % (code, ban_name, tp_name, gela)
    if notes:
        partial.append('PARCIAL %s | %s' % (tag, '; '.join(notes)))
    else:
        ok.append('OK      %s' % tag)

print('\n===== OK completos (%d) =====' % len(ok))
for l in ok: print(l)
print('\n===== PARCIALES / avisos (%d) =====' % len(partial))
for l in partial: print(l)
print('\n===== NO ENCONTRADOS (%d) =====' % len(bad))
for l in bad: print(l)
print('\nAPPLY=%s | filas=%d | banaketa a escribir=%d | tp a escribir=%d' % (APPLY, len(ROWS), n_ban, n_tp))
if APPLY:
    env.cr.commit(); print('>>> GUARDADO')
