# -*- coding: utf-8 -*-
# Importa banaketa_id + teoria_praktika_id para el mintegi ELEKTRIZITATEA.
# Empareja por code (override explícito en los alias). DRY-RUN salvo APPLY=True.
APPLY = True

# (taldea_excel, short_excel, override_code|None, [sesiones], teoria, praktika)
ROWS = [
    # 1SEA3
    ('1SEA3','IEDT',None,[2],2,0),
    ('1SEA3','SIZE',None,[2,2,1],5,0),
    ('1SEA3','IEKO',None,[2,2,2],6,0),
    ('1SEA3','DIGI','1SEA3_PSAD_2',[2],2,0),
    ('1SEA3','TAIP',None,[3,2],2,3),
    ('1SEA3','IETP',None,[3,3],2,4),
    # 2SEA3
    ('2SEA3','IDAT',None,[3,3],2,4),
    ('2SEA3','SETG',None,[2,2],4,0),
    ('2SEA3','IDAK',None,[3,2],2,3),
    ('2SEA3','IEMMK',None,[2,1],3,0),
    ('2SEA3','PSAI',None,[2],2,0),
    ('2SEA3','HAUT1','2SEA3_HAUT_1',[2,2],2,2),
    ('2SEA3','HAUT2','2SEA3_HAUT_2',[2,2],2,2),
    # 1IEA2D
    ('1IEA2D','TROTEC',None,[2,2,2],6,0),
    ('1IEA2D','AUIND',None,[4,4],3,5),
    ('1IEA2D','IEI',None,[3,3,3],3,6),
    ('1IEA2D','PSAI',None,[1],1,0),
    # 1IEA2A
    ('1IEA2A','TROTEC',None,[2,2,2],6,0),
    ('1IEA2A','AUIND',None,[4,4],3,5),
    ('1IEA2A','IEI',None,[3,3,3],3,6),
    ('1IEA2A','PSAI',None,[1],1,0),
    # 2IEA2A
    ('2IEA2A','IDOM',None,[2,2],2,2),
    ('2IEA2A','ME',None,[2,2],2,2),
    ('2IEA2A','EETAK','2IEA2A_ICTVE',[3],1,2),     # CONFIRMAR alias
    ('2IEA2A','INSDIS',None,[3],3,0),
    ('2IEA2A','FV',None,[2],1,1),
    ('2IEA2A','TRONIC',None,[2,2],4,0),
    ('2IEA2A','PSAD',None,[3],3,0),
    ('2IEA2A','IA','2IEA2A_HAUT_1',[2,2],4,0),      # CONFIRMAR alias
    ('2IEA2A','PLC','2IEA2A_HAUT_2',[2,2],4,0),     # CONFIRMAR alias
    # 2IEA2D
    ('2IEA2D','IDOM',None,[2,2],2,2),
    ('2IEA2D','ME',None,[2,2],2,2),
    ('2IEA2D','EETAK','2IEA2D_ICTVE',[3],1,2),     # CONFIRMAR alias
    ('2IEA2D','INSDIS',None,[3],3,0),
    ('2IEA2D','FV',None,[2],1,1),
    ('2IEA2D','TRONIC',None,[2,2],4,0),
    ('2IEA2D','PSAD',None,[3],3,0),
    ('2IEA2D','IA','2IEA2D_HAUT_1',[2,2],4,0),      # CONFIRMAR alias
    ('2IEA2D','PLC','2IEA2D_HAUT_2',[2,2],4,0),     # CONFIRMAR alias
    # 1ELE1
    ('1ELE1','IED',None,[4,3],2,5),
    ('1ELE1','EEEL','1ELE1_EEE',[2,2,3],7,0),
    ('1ELE1','TELCOM',None,[2,3],2,3),
    ('1ELE1','TUTO','1ELE1_TUTO_1',[1],1,0),
    # 2ELE1
    ('2ELE1','IMRTD','2ELE1_IMRT',[3,3],2,4),
    ('2ELE1','BTIETKMM','2ELE1_TENBA',[3,4],2,5),
    ('2ELE1','BEZ',None,[2],2,0),
    ('2ELE1','TUTO','2ELE1_TUTO_2',[1],1,0),
    # 3OLHELE1 -> 3OLHELE3 (SIN modulos en Odoo: se reportaran NOT_FOUND)
    ('3OLHELE1','IMRTD',None,[3,3,1],3,4),
    ('3OLHELE1','BTIETKMM',None,[3,4,1],3,5),
    ('3OLHELE1','BEZ',None,[2,1],3,0),
    ('3OLHELE1','PROIEK',None,[3],3,0),
    # 2OLHELE1 -> 2OLHELE3
    ('2OLHELE1','IED2','2OLHELE3_IED_2',[3,2],2,3),
    ('2OLHELE1','TELCOM','2OLHELE3_TELCOM',[2,3],2,3),
    ('2OLHELE1','PROSOL_2','2OLHELE3_PROSOL_2',[2],0,2),
    ('2OLHELE1','DIGI_2','2OLHELE3_DIGI_2',[2],2,0),
    ('2OLHELE1','AUTO','2OLHELE3_AUTO',[4],1,3),
    # 1OLHELE1 -> 1OLHELE3
    ('1OLHELE1','EEE','1OLHELE3_EEE',[4,3],2,5),
    ('1OLHELE1','IED1','1OLHELE3_IED_1',[2],2,0),
    ('1OLHELE1','DIGI','1OLHELE3_DIGI_1',[2],2,0),
    ('1OLHELE1','ALMAC','1OLHELE3_ALMA',[2],1,1),
    ('1OLHELE1','FUNDE','1OLHELE3_FE',[2],2,0),     # CONFIRMAR alias
    ('1OLHELE1','PROSOL','1OLHELE3_PROSOL_1',[2],0,2),
    ('1OLHELE1','TUTO','1OLHELE3_TUTO_1',[1],1,0),
    # 2EMF1
    ('2EMF1','EEE',None,[3,3,2],0,8),
    # 2INF4
    ('2INF4','EEE',None,[3,3,2,2],0,10),
    # 3OLHMEK3
    ('3OLHMEK3','EEE',None,[3,3,3],0,9),
    ('3OLHMEK3','EAE',None,[3,3,3],0,9),            # sin modulo en Odoo -> NOT_FOUND
]

Subject = env['op.subject']
Ban = env['op.subject.banaketa']
TP = env['op.subject.teoria.praktika']

ok, warn, bad = [], [], []
for taldea, short, override, sess, teoria, praktika in ROWS:
    code = override or '%s_%s' % (taldea, short)
    rec = Subject.search([('code','=',code)], limit=1)
    label = '%s/%s -> %s' % (taldea, short, code)
    if not rec:
        bad.append('NOT_FOUND   %s' % label)
        continue
    gela = int(round(rec.gela_orduak or 0))
    s_sum = sum(sess)
    tp_sum = teoria + praktika
    ban_name = '/'.join(str(x) for x in sorted(sess, reverse=True))
    tp_name = '%dT/%dP' % (teoria, praktika)
    problems = []
    if s_sum != gela:
        problems.append('sesiones=%d != gela=%d' % (s_sum, gela))
    if tp_sum != gela:
        problems.append('teoria+prak=%d != gela=%d' % (tp_sum, gela))
    ban = Ban.search([('name','=',ban_name),('guztira','=',gela)], limit=1)
    tp = TP.search([('name','=',tp_name),('guztira','=',gela)], limit=1)
    if not ban:
        problems.append('banaketa "%s" inexistente' % ban_name)
    if not tp:
        problems.append('tp "%s" inexistente' % tp_name)
    if rec.code in (override,) and override:
        pass
    if problems:
        bad.append('MISMATCH    %s | %s' % (label, '; '.join(problems)))
        continue
    flag = '  <-- ALIAS' if override else ''
    line = 'OK  %-22s ban=%-8s tp=%-7s (gela %d)%s' % (code, ban_name, tp_name, gela, flag)
    if override:
        warn.append(line)
    else:
        ok.append(line)
    if APPLY:
        rec.write({'banaketa_id': ban.id, 'teoria_praktika_id': tp.id})

print('\n===== OK por code exacto (%d) =====' % len(ok))
for l in ok: print(l)
print('\n===== OK pero por ALIAS - revisar (%d) =====' % len(warn))
for l in warn: print(l)
print('\n===== PROBLEMAS - NO escritos (%d) =====' % len(bad))
for l in bad: print(l)
print('\nAPPLY =', APPLY, '| total filas:', len(ROWS))
if APPLY:
    env.cr.commit()
    print('>>> CAMBIOS GUARDADOS')
