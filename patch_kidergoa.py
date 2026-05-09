#!/usr/bin/env python3
"""Migra el campo kidergoa (funtzionarioa/ordezkoa) desde MySQL a op.faculty."""
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
    email_to_id = {row[0]: row[1] for row in cr.fetchall()}

    conn = pymysql.connect(host='192.168.1.103', user='sail',
                           password='password', db='laravel')
    cur = conn.cursor()
    cur.execute("SELECT emailLanekoa, kidergoa FROM IRAKASLEAK WHERE suspenditua=0 AND kidergoa IS NOT NULL")

    updated = 0
    for email, kidergoa in cur.fetchall():
        faculty_id = email_to_id.get(email)
        if faculty_id:
            cr.execute("UPDATE op_faculty SET kidergoa=%s WHERE id=%s", (kidergoa, faculty_id))
            updated += cr.rowcount

    cr.commit()
    print(f"Updated {updated} faculty with kidergoa")
