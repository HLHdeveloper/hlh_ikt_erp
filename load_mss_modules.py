# -*- coding: utf-8 -*-
# Carga ciclo MSS desde JIMA_INFOR.xlsx (datos en euskera, RPT redondeado 1 decimal)
# Ejecutar: docker exec -i odoo19 odoo shell -d kudeaketa < load_mss_modules.py
S = env['op.subject']

# (id, kode_jima|None, kurtsoa, pt_pes, name_eu, orduak, gela, rpt, enpresan)
rows = [
    (313, '0225', '1º', 'PES',    'Sare lokalak',                                   231, 7,   7.0, 21),
    (314, '0226', '1º', 'PES',    'Informatika-segurtasuna',                         99, 3,   3.0,  9),
    (318, '0227', '2º', 'PES',    'Sareko zerbitzuak',                              189, 6,   5.7, 63),
    (319, '0228', '2º', 'PES',    'Web aplikazioak',                                105, 3,   3.2, 42),  # kode_jima FIX 0227->0228
    (310, '0221', '1º', 'PT',     'Tresneria muntatzea eta mantentzea',             231, 7,   7.0, 21),
    (311, '0222', '1º', 'PT',     'Postu bakarreko sistema eragileak',              165, 5,   5.0, 15),
    (322, '0223', '2º', 'PT',     'Bulegotika-aplikazioak',                         231, 7,   7.0, 84),
    (317, '0224', '2º', 'PT',     'Sareko sistema eragileak',                       168, 5,   5.1, 63),
    (315, '0156', '1º', 'PES',    'Ingeles profesional',                             60, 2,   1.8,  0),
    (312, '1709', '1º', 'PES',    'Enplegagarritasunerako ibilbide pertsonala I',   120, 4,   3.6,  0),
    (323, '1710', '2º', 'PES',    'Enplegagarritasunerako ibilbide pertsonala II',   63, 3,   1.9,  0),
    (316, '1664', '1º', 'PT_PES', 'Produkzio-sektoreei aplikatutako digitalizazioa', 60, 2,   1.5,  0),
    (324, '1708', '2º', 'PT_PES', 'Produkzio-sistemari aplikatutako iraunkortasuna',  42, 2,   2.0,  0),  # kode_jima FIX 0224->1708, RPT se mantiene 2.0
    (325, None,   '2º', 'PT_PES', 'Proiektu intermodularra',                          50, 0,   1.5,  0),  # kode_jima existente (1713)
]

n = 0
for sid, kj, kur, pt, name, orduak, gela, rpt, enpresan in rows:
    rec = S.browse(sid)
    vals = {
        'name': name,
        'kurtsoa': kur,
        'pt_pes': pt,
        'orduak': float(orduak),
        'gela_orduak': float(gela),
        'rpt_total': float(rpt),
        'zikloko_orduak_enpresan': float(enpresan),
    }
    if kj is not None:
        vals['kode_jima'] = kj
    rec.write(vals)
    n += 1

env.cr.commit()
print('UPDATED:', n)
