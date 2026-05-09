from odoo import api, fields, models


class OpFaculty(models.Model):
    _inherit = 'op.faculty'

    kidergoa = fields.Char(string='Kidergoa')

    # Cargos (KARGUAK)
    kargu_ids = fields.Many2many(
        'op.kargu',
        'op_faculty_kargu_rel',
        'faculty_id', 'kargu_id',
        string='Cargos',
    )

    # Huelgas (IR_GREBAK)
    greba_ids = fields.Many2many(
        'op.greba',
        'op_faculty_greba_rel',
        'faculty_id', 'greba_id',
        string='Huelgas',
    )

    # Grupos donde imparte (IRAKASLEAK_TALDEAK)
    batch_ids = fields.Many2many(
        'op.batch',
        'op_faculty_batch_rel',
        'faculty_id', 'batch_id',
        string='Grupos donde imparte',
    )

    # Sustituciones como titular
    titular_ordezkapen_ids = fields.One2many(
        'op.ordezkapen', 'titular_id',
        string='Sustituciones (como titular)',
    )

    # Sustituciones como sustituto
    ordezko_ordezkapen_ids = fields.One2many(
        'op.ordezkapen', 'ordezko_id',
        string='Sustituciones (como sustituto)',
    )

    # ── Dashboard methods ────────────────────────────────────────────

    @api.model
    def get_dashboard_counts(self):
        cr = self.env.cr
        cr.execute("SELECT COUNT(*) FROM op_faculty WHERE active=true")
        total = cr.fetchone()[0]
        cr.execute("SELECT COUNT(*) FROM op_faculty WHERE active=true AND kidergoa='funtzionarioa'")
        funtzionarioak = cr.fetchone()[0]
        cr.execute("SELECT COUNT(*) FROM op_faculty WHERE active=true AND kidergoa='ordezkoa'")
        ordezkoak = cr.fetchone()[0]
        cr.execute("SELECT COUNT(*) FROM op_ordezkapen WHERE end_date IS NULL")
        bajan = cr.fetchone()[0]
        cr.execute("""
            SELECT COUNT(DISTINCT fk.faculty_id)
            FROM op_faculty_kargu_rel fk
            JOIN op_kargu k ON k.id = fk.kargu_id
            JOIN op_faculty f ON f.id = fk.faculty_id AND f.active = true
            WHERE k.code LIKE 'MB-%%' OR k.code LIKE 'TUTO_%%'
               OR k.code = 'DUAL_ARDURADUNAK'
        """)
        karguak = cr.fetchone()[0]
        return {'total': total, 'funtzionarioak': funtzionarioak,
                'ordezkoak': ordezkoak, 'bajan': bajan, 'karguak': karguak}

    @api.model
    def get_dept_breakdown(self, kidergoa=None):
        cr = self.env.cr
        if kidergoa:
            cr.execute("""
                SELECT od.id, od.name, COUNT(DISTINCT of2.id)
                FROM op_department od
                LEFT JOIN op_department_op_faculty_rel dfr ON dfr.op_department_id = od.id
                LEFT JOIN op_faculty of2 ON of2.id = dfr.op_faculty_id
                    AND of2.active=true AND of2.kidergoa=%s
                GROUP BY od.id, od.name
                HAVING COUNT(DISTINCT of2.id) > 0
                ORDER BY COUNT(DISTINCT of2.id) DESC
            """, [kidergoa])
        else:
            cr.execute("""
                SELECT od.id, od.name, COUNT(DISTINCT of2.id)
                FROM op_department od
                LEFT JOIN op_department_op_faculty_rel dfr ON dfr.op_department_id = od.id
                LEFT JOIN op_faculty of2 ON of2.id = dfr.op_faculty_id AND of2.active=true
                GROUP BY od.id, od.name
                HAVING COUNT(DISTINCT of2.id) > 0
                ORDER BY COUNT(DISTINCT of2.id) DESC
            """)
        return [{'id': r[0], 'name': r[1], 'count': r[2]} for r in cr.fetchall()]

    @api.model
    def get_bajan_depts(self):
        cr = self.env.cr
        cr.execute("""
            SELECT d.id, d.name, COUNT(DISTINCT o.titular_id)
            FROM op_department d
            JOIN op_department_op_faculty_rel rel ON rel.op_department_id = d.id
            JOIN op_ordezkapen o ON o.titular_id = rel.op_faculty_id
                AND o.end_date IS NULL
            GROUP BY d.id, d.name
            HAVING COUNT(DISTINCT o.titular_id) > 0
            ORDER BY d.name
        """)
        return [{'id': r[0], 'name': r[1], 'count': r[2]} for r in cr.fetchall()]

    @api.model
    def get_bajan_faculty_by_dept(self, dept_id):
        cr = self.env.cr
        cr.execute("""
            SELECT
                f.id,
                rp.name,
                (
                    SELECT rp2.name
                    FROM op_ordezkapen o2
                    JOIN op_faculty f2 ON f2.id = o2.ordezko_id
                    JOIN res_partner rp2 ON rp2.id = f2.partner_id
                    WHERE o2.titular_id = f.id AND o2.end_date IS NULL
                    ORDER BY o2.start_date DESC
                    LIMIT 1
                ) AS ordezko_name,
                (
                    SELECT COUNT(DISTINCT o3.ordezko_id)
                    FROM op_ordezkapen o3
                    WHERE o3.titular_id = f.id
                ) AS ordezko_count
            FROM op_faculty f
            JOIN res_partner rp ON rp.id = f.partner_id
            JOIN op_department_op_faculty_rel rel
                ON rel.op_faculty_id = f.id AND rel.op_department_id = %s
            WHERE f.active = true
              AND EXISTS (
                  SELECT 1 FROM op_ordezkapen o
                  WHERE o.titular_id = f.id AND o.end_date IS NULL
              )
            ORDER BY rp.name
        """, (dept_id,))
        return [
            {'id': r[0], 'name': r[1],
             'ordezko': r[2] or '—', 'ordezko_count': r[3]}
            for r in cr.fetchall()
        ]

    @api.model
    def get_bajan_history(self, titular_id):
        cr = self.env.cr
        cr.execute("""
            SELECT o.id, rp.name,
                   o.start_date::text,
                   o.end_date::text
            FROM op_ordezkapen o
            JOIN op_faculty f ON f.id = o.ordezko_id
            JOIN res_partner rp ON rp.id = f.partner_id
            WHERE o.titular_id = %s
            ORDER BY o.start_date
        """, (titular_id,))
        return [{'id': r[0], 'ordezko': r[1], 'start_date': r[2], 'end_date': r[3]}
                for r in cr.fetchall()]

    @api.model
    def get_kargu_depts(self):
        cr = self.env.cr
        cr.execute("""
            SELECT d.id, d.name, COUNT(DISTINCT f.id)
            FROM op_department d
            JOIN op_department_op_faculty_rel rel ON rel.op_department_id = d.id
            JOIN op_faculty f ON f.id = rel.op_faculty_id AND f.active = true
            JOIN op_faculty_kargu_rel fk ON fk.faculty_id = f.id
            JOIN op_kargu k ON k.id = fk.kargu_id
            WHERE k.code LIKE 'MB-%%' OR k.code LIKE 'TUTO_%%'
               OR k.code = 'DUAL_ARDURADUNAK'
            GROUP BY d.id, d.name
            ORDER BY d.name
        """)
        return [{'id': r[0], 'name': r[1], 'count': r[2]} for r in cr.fetchall()]

    @api.model
    def get_kargu_types_for_dept(self, dept_id):
        cr = self.env.cr
        result = []
        for code_pattern, label, ktype in [
            ('MB-%%',            'Mintegi buruak',  'mb'),
            ('TUTO_%%',          'Tutoreak',        'tuto'),
            ('DUAL_ARDURADUNAK', 'Dual Arduradunak','dual'),
        ]:
            cr.execute("""
                SELECT COUNT(DISTINCT f.id)
                FROM op_faculty f
                JOIN op_faculty_kargu_rel fk ON fk.faculty_id = f.id
                JOIN op_kargu k ON k.id = fk.kargu_id
                    AND k.code LIKE %s
                JOIN op_department_op_faculty_rel rel
                    ON rel.op_faculty_id = f.id AND rel.op_department_id = %s
                WHERE f.active = true
            """, (code_pattern, dept_id))
            count = cr.fetchone()[0]
            if count:
                result.append({'code': code_pattern, 'label': label,
                               'type': ktype, 'count': count})
        return result

    @api.model
    def get_faculty_for_dept_kargu(self, dept_id, code_pattern):
        cr = self.env.cr
        cr.execute("""
            SELECT f.id, rp.name,
                   STRING_AGG(k.code, ', ' ORDER BY k.code) AS kargoak
            FROM op_faculty f
            JOIN res_partner rp ON rp.id = f.partner_id
            JOIN op_faculty_kargu_rel fk ON fk.faculty_id = f.id
            JOIN op_kargu k ON k.id = fk.kargu_id AND k.code LIKE %s
            JOIN op_department_op_faculty_rel rel
                ON rel.op_faculty_id = f.id AND rel.op_department_id = %s
            WHERE f.active = true
            GROUP BY f.id, rp.name
            ORDER BY rp.name
        """, (code_pattern, dept_id))
        return [{'id': r[0], 'name': r[1], 'kargu': r[2]} for r in cr.fetchall()]

    @api.model
    def get_faculty_by_dept(self, dept_id, kidergoa=None):
        cr = self.env.cr
        if kidergoa:
            cr.execute("""
                SELECT DISTINCT of2.id, rp.name
                FROM op_faculty of2
                JOIN res_partner rp ON rp.id = of2.partner_id
                JOIN op_department_op_faculty_rel dfr ON dfr.op_faculty_id = of2.id
                WHERE dfr.op_department_id = %s AND of2.active=true AND of2.kidergoa=%s
                ORDER BY rp.name
            """, [dept_id, kidergoa])
        else:
            cr.execute("""
                SELECT DISTINCT of2.id, rp.name
                FROM op_faculty of2
                JOIN res_partner rp ON rp.id = of2.partner_id
                JOIN op_department_op_faculty_rel dfr ON dfr.op_faculty_id = of2.id
                WHERE dfr.op_department_id = %s AND of2.active=true
                ORDER BY rp.name
            """, [dept_id])
        return [{'id': r[0], 'name': r[1]} for r in cr.fetchall()]
