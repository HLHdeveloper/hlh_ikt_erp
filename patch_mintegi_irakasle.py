#!/usr/bin/env python3
"""
Repopulates op_department_op_faculty_rel from MINTEGI_IRAKASLE (direct membership).

Previously the relation was built from IRAKASLEAK_TALDEAK (groups taught),
which incorrectly placed FOL/INGLÉS teachers into MEKANIKA and other departments.
MINTEGI_IRAKASLE is the authoritative source for department membership.
"""
import pymysql
import odoo

odoo.tools.config.parse_config(['--config=/etc/odoo/odoo.conf'])

with odoo.registry('kudeaketa').cursor() as cr:
    # email → faculty_id
    cr.execute("""
        SELECT rp.email, of2.id
        FROM op_faculty of2
        JOIN res_partner rp ON rp.id = of2.partner_id
        WHERE of2.active = true AND rp.email IS NOT NULL
    """)
    email_to_faculty = {row[0]: row[1] for row in cr.fetchall()}

    # code → dept_id  (code = mIZ minus 'MINTEGIA-' prefix)
    cr.execute("SELECT code, id FROM op_department")
    code_to_dept = {row[0]: row[1] for row in cr.fetchall()}

    conn = pymysql.connect(host='192.168.1.103', user='sail',
                           password='password', db='laravel')
    cur = conn.cursor()

    cur.execute("""
        SELECT i.emailLanekoa, m.mIZ
        FROM MINTEGI_IRAKASLE mi
        JOIN IRAKASLEAK i ON i.id = mi.irakaslea_id
        JOIN MINTEGIAK m ON m.mIZ = mi.mIZ
        WHERE i.suspenditua = 0
          AND i.emailLanekoa IS NOT NULL
    """)
    rows = cur.fetchall()
    conn.close()

    pairs = set()
    skipped = 0
    for email, miz in rows:
        code = miz.replace('MINTEGIA-', '')[:16]
        faculty_id = email_to_faculty.get(email)
        dept_id = code_to_dept.get(code)
        if faculty_id and dept_id:
            pairs.add((dept_id, faculty_id))
        else:
            skipped += 1
            if not faculty_id:
                print(f"  SKIP no faculty: {email}")
            if not dept_id:
                print(f"  SKIP no dept code: {code!r} (mIZ={miz})")

    # Clear existing relation and repopulate
    cr.execute("DELETE FROM op_department_op_faculty_rel")
    deleted = cr.rowcount

    if pairs:
        values = ','.join(cr.mogrify("(%s,%s)", (dept_id, fac_id)).decode()
                         for dept_id, fac_id in pairs)
        cr.execute(
            f"INSERT INTO op_department_op_faculty_rel "
            f"(op_department_id, op_faculty_id) VALUES {values}"
        )

    cr.commit()
    print(f"Cleared {deleted} old records")
    print(f"Inserted {len(pairs)} records from MINTEGI_IRAKASLE")
    print(f"Skipped {skipped} rows (no matching faculty or dept)")
