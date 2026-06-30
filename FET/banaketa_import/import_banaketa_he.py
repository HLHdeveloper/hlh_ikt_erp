# -*- coding: utf-8 -*-
# Copia banaketa_id + teoria_praktika_id del modulo ORIGEN a su copia HE_ (eleanitza).
# Eleanitza = codocencia en la misma aula -> misma banaketa y T/P que el original.
# Empareja quitando el prefijo "HE_" del code. Idempotente. Solo escribe esos 2 campos.
#   docker exec -i odoo19 odoo shell -d kudeaketa --no-http < import_banaketa_he.py

APPLY = True  # aplicado 2026-06-30

he_subjects = env['op.subject'].search([('code', '=like', 'HE\\_%')])

ok, skip_done, blocked, notfound = [], [], [], []
for he in he_subjects:
    orig_code = he.code[3:]  # quita "HE_"
    orig = env['op.subject'].search([('code', '=', orig_code)], limit=1)
    if not orig:
        notfound.append((he.code, orig_code))
        continue
    if not orig.banaketa_id:
        blocked.append((he.code, orig_code))
        continue
    vals = {}
    if he.banaketa_id.id != orig.banaketa_id.id:
        vals['banaketa_id'] = orig.banaketa_id.id
    if orig.teoria_praktika_id and he.teoria_praktika_id.id != orig.teoria_praktika_id.id:
        vals['teoria_praktika_id'] = orig.teoria_praktika_id.id
    if not vals:
        skip_done.append(he.code)
        continue
    ban = orig.banaketa_id.name
    tp = orig.teoria_praktika_id.name or '-'
    ok.append((he.code, orig_code, ban, tp))
    if APPLY:
        he.write(vals)

print("=== A RELLENAR (%d) ===" % len(ok))
for c, o, b, tp in ok:
    print("  %-18s <- %-14s  banaketa=%-10s T/P=%s" % (c, o, b, tp))
print("=== YA HECHOS / sin cambios (%d) ===" % len(skip_done))
for c in skip_done:
    print("  %s" % c)
print("=== BLOQUEADOS (origen sin banaketa) (%d) ===" % len(blocked))
for c, o in blocked:
    print("  %-18s <- %s (origen SIN banaketa)" % (c, o))
print("=== ORIGEN NO ENCONTRADO (%d) ===" % len(notfound))
for c, o in notfound:
    print("  %-18s -> %s ???" % (c, o))

if APPLY:
    env.cr.commit()
    print(">>> APLICADO y commit.")
else:
    print(">>> DRY-RUN (APPLY=False). No se ha escrito nada.")
