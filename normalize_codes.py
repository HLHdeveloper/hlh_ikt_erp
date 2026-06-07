# -*- coding: utf-8 -*-
# Normaliza op.subject.code: espacios -> '_', colapsa '__', recorta bordes.
# DRY-RUN si DRY=True (no escribe). Ejecutar:
#   docker exec -i odoo19 odoo shell -d kudeaketa < normalize_codes.py
import re
DRY = False

S = env['op.subject']

def norm(code):
    c = (code or '').strip()
    c = re.sub(r'\s+', '_', c)
    c = re.sub(r'_+', '_', c)
    return c.strip('_')

recs = S.search([('code', 'like', '% %')])
# mapa de codes existentes -> id (para detectar colisiones)
all_codes = {}
for r in S.search([]):
    all_codes.setdefault(r.code, r.id)

changes = []
collisions = []
for r in recs:
    new = norm(r.code)
    if new == r.code:
        continue
    owner = all_codes.get(new)
    if owner and owner != r.id:
        collisions.append((r.id, r.code, new, owner))
    else:
        changes.append((r.id, r.code, new))

print('=== CAMBIOS (%d) ===' % len(changes))
for cid, old, new in changes:
    print('  %-5d [%s] -> [%s]' % (cid, old, new))
print('=== COLISIONES (%d) ===' % len(collisions))
for cid, old, new, owner in collisions:
    print('  %-5d [%s] -> [%s] CHOCA con id %s' % (cid, old, new, owner))

if not DRY and not collisions:
    for cid, old, new in changes:
        S.browse(cid).write({'code': new})
    env.cr.commit()
    print('APLICADO:', len(changes))
elif not DRY and collisions:
    print('NO aplicado: hay colisiones, resuelvelas primero.')
