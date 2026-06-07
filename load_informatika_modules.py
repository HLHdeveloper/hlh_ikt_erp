# -*- coding: utf-8 -*-
# Carga de valores de módulos de Informatika (1MSS2, 2MSS2, 1INF1, 2INF1)
# Ejecutar: docker exec -i odoo19 odoo shell -d kudeaketa < load_informatika_modules.py
S = env['op.subject']

# (id, batch_id, kurtsoa, kode_jima|None, pt_pes, orduak, rpt_total, gela_orduak)
updates = [
    # --- 1MSS2 (batch 216) ---
    (310, 216, '1º', '0221', 'PT',      231, 7,   7),
    (311, 216, '1º', '0222', 'PT',      165, 5,   5),
    (316, 216, '1º', '1664', 'PT_PES',   60, 2,   2),
    (313, 216, '1º', '0225', 'PES',     231, 7,   7),
    (314, 216, '1º', '0226', 'PES',      99, 3,   3),
    (315, 216, '1º', '0156', 'PES_ING',  60, 2,   1.8),
    (312, 216, '1º', '1709', 'PES_FOL', 120, 4,   3.6),
    # --- 2MSS2 (batch 228) ---
    (317, 228, '2º', '0224', 'PT',      168, 5.1, 5),
    (322, 228, '2º', '0223', 'PT',      231, 7,   7),
    (318, 228, '2º', '0227', 'PES',     189, 5.7, 6),
    (319, 228, '2º', '0227', 'PES',     105, 3.2, 3),
    (324, 228, '2º', '0224', 'PT_PES',   42, 2.0, 2),
    (323, 228, '2º', '1710', 'PES_FOL',  63, 1.9, 3),
    (325, 228, '2º', None,   'PT_PES',   50, 1.5, 1.5),  # PRO: kode_jima existente
    # --- 1INF1 (batch 213) ---
    (216, 213, '1º', '3016', 'PT',      231, 7.0, 7),
    (218, 213, '1º', '3030', 'PT',      165, 5.0, 5),
    (217, 213, '1º', '3029', 'PT',      231, 7.0, 7),
    (219, 213, '1º', '3011', 'PES',     165, 5.0, 5),
    (220, 213, '1º', '3009', 'PES',     165, 5.0, 5),
    (222, 213, '1º', 'E900', 'PT_PES',   33, 1.0, 1),
    # --- 2INF1 (batch 225) ---
    (223, 225, '2º', '3015', 'PT',      240, 8,   8),
    (224, 225, '2º', 'E650', 'PT',      120, 4.0, 4),
    (227, 225, '2º', 'E800', 'PT_PES',   53, 1.6, 1.6),
    (225, 225, '2º', '3012', 'PES',     168, 5.1, 5.1),
    (226, 225, '2º', '3019', 'PES',     144, 4.4, 4.4),
    (228, 225, '2º', 'E901', 'PT_PES',   25, 1.0, 0.8),
]

# (code, name, batch_id, kurtsoa, kode_jima, pt_pes, orduak, rpt_total, gela_orduak)
creates = [
    ('2MSS2_HAUTAZKOA_I',   'HAUTAZKOA_I',   228, '2º', '0223', 'PT_PES', 42, 2.0, 2),
    ('2MSS2_HAUTAZKOA_II',  'HAUTAZKOA_II',  228, '2º', '0223', 'PT_PES', 42, 2.0, 2),
    ('2MSS2_HAUTAZKOA_III', 'HAUTAZKOA_III', 228, '2º', '0223', 'PT_PES', 84, 2.5, 4),
]

n_upd = 0
for sid, bid, kur, kj, pt, orduak, rpt, gela in updates:
    rec = S.browse(sid)
    vals = {
        'batch_id': bid, 'kurtsoa': kur, 'pt_pes': pt,
        'orduak': orduak, 'rpt_total': rpt, 'gela_orduak': gela,
    }
    if kj is not None:
        vals['kode_jima'] = kj
    rec.write(vals)
    n_upd += 1

n_new = 0
for code, name, bid, kur, kj, pt, orduak, rpt, gela in creates:
    if S.search_count([('code', '=', code)]):
        continue
    S.create({
        'code': code, 'name': name, 'batch_id': bid, 'kurtsoa': kur,
        'kode_jima': kj, 'pt_pes': pt, 'orduak': orduak,
        'rpt_total': rpt, 'gela_orduak': gela,
    })
    n_new += 1

env.cr.commit()
print('UPDATED:', n_upd, 'CREATED:', n_new)
