# Carga idempotente de la rejilla horaria del centro en op.timing
# CIFP Gizarte Berrikuntza: Lunes-Viernes, 6 sesiones de 60 min,
# 8:00-14:30 con recreo 11:00-11:30.
# Ejecutar:  docker exec -i odoo19 odoo shell -d kudeaketa --no-http < load_timings.py
#
# hour/minute/am_pm = hora de INICIO de la franja (formato 12h).
# name = etiqueta canonica que se reutilizara en el <Hours_List> del .fet.

ROWS = [
    # (sequence, name,            hour, minute, am_pm, duration)
    (1, u"1º 08:00-09:00",  "8",  "00", "am", 1.0),
    (2, u"2º 09:00-10:00",  "9",  "00", "am", 1.0),
    (3, u"3º 10:00-11:00", "10",  "00", "am", 1.0),
    (4, u"4º 11:30-12:30", "11",  "30", "am", 1.0),
    (5, u"5º 12:30-13:30", "12",  "30", "pm", 1.0),
    (6, u"6º 13:30-14:30",  "1",  "30", "pm", 1.0),
]

Timing = env["op.timing"]
for seq, name, hour, minute, am_pm, duration in ROWS:
    vals = {
        "name": name, "hour": hour, "minute": minute,
        "am_pm": am_pm, "duration": duration, "sequence": seq,
    }
    rec = Timing.search([("sequence", "=", seq)], limit=1)
    if rec:
        rec.write(vals)
        print(u"update seq %s -> %s" % (seq, name))
    else:
        Timing.create(vals)
        print(u"create seq %s -> %s" % (seq, name))

env.cr.commit()
print("op.timing total:", Timing.search_count([]))
