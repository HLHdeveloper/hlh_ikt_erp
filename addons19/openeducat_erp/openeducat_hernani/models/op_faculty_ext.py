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
        return {'total': total, 'funtzionarioak': funtzionarioak,
                'ordezkoak': ordezkoak, 'bajan': bajan}

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
