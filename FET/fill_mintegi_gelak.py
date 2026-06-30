# -*- coding: utf-8 -*-
# Rellena op.department.gela_ids con la union de aulas (gela_teoria_ids +
# tailerra_ids) de los modulos de cada mintegi. Idempotente.
#   docker exec -i odoo19 odoo shell -d kudeaketa --no-http < fill_mintegi_gelak.py
APPLY = True

Dept = env['op.department']
for d in Dept.search([]):
    subs = env['op.subject'].search([('own_department_id','=',d.id)])
    aulas = env['op.classroom']
    for s in subs:
        aulas |= s.gela_teoria_ids | s.tailerra_ids
    if aulas:
        print("  %-16s %d aulas: %s" % (d.name, len(aulas),
              ", ".join(sorted(aulas.mapped('code')))))
        if APPLY:
            d.gela_ids = [(6, 0, aulas.ids)]
if APPLY:
    env.cr.commit()
    print(">>> APLICADO.")
else:
    print(">>> DRY-RUN.")
