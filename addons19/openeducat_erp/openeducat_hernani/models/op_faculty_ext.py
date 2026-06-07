from odoo import api, fields, models, _
from odoo.exceptions import UserError


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
        cr.execute("""
            SELECT COUNT(DISTINCT fk.faculty_id)
            FROM op_faculty_kargu_rel fk
            JOIN op_kargu k ON k.id = fk.kargu_id
            JOIN op_faculty f ON f.id = fk.faculty_id AND f.active = true
            WHERE k.code NOT LIKE 'MB-%%'
              AND k.code NOT LIKE 'TUTO_%%'
              AND k.code != 'DUAL_ARDURADUNAK'
        """)
        gainontzeko = cr.fetchone()[0]
        cr.execute("SELECT COUNT(*) FROM op_student WHERE active=true")
        ikasleak = cr.fetchone()[0]
        return {'total': total, 'funtzionarioak': funtzionarioak,
                'ordezkoak': ordezkoak, 'bajan': bajan,
                'karguak': karguak, 'gainontzeko': gainontzeko,
                'ikasleak': ikasleak}

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
    def get_gainontzeko_kargu_types(self):
        cr = self.env.cr
        cr.execute("""
            SELECT k.id, k.code, k.name, COUNT(DISTINCT fk.faculty_id)
            FROM op_kargu k
            JOIN op_faculty_kargu_rel fk ON fk.kargu_id = k.id
            JOIN op_faculty f ON f.id = fk.faculty_id AND f.active = true
            WHERE k.code NOT LIKE 'MB-%%'
              AND k.code NOT LIKE 'TUTO_%%'
              AND k.code != 'DUAL_ARDURADUNAK'
            GROUP BY k.id, k.code, k.name
            ORDER BY COUNT(DISTINCT fk.faculty_id) DESC, k.code
        """)
        return [{'id': r[0], 'code': r[1], 'name': r[2], 'count': r[3]}
                for r in cr.fetchall()]

    @api.model
    def get_faculty_for_gainontzeko_kargu(self, kargu_id):
        cr = self.env.cr
        cr.execute("""
            SELECT f.id, rp.name
            FROM op_faculty f
            JOIN res_partner rp ON rp.id = f.partner_id
            JOIN op_faculty_kargu_rel fk ON fk.faculty_id = f.id
            WHERE fk.kargu_id = %s AND f.active = true
            ORDER BY rp.name
        """, (kargu_id,))
        return [{'id': r[0], 'name': r[1]} for r in cr.fetchall()]

    # ── Perfilazioak methods ─────────────────────────────────────────

    @api.model
    def get_perfilazio_mintegiak(self):
        cr = self.env.cr
        cr.execute("""
            SELECT DISTINCT d.id, d.name, d.code
            FROM op_department d
            JOIN op_department_op_faculty_rel rel ON rel.op_department_id = d.id
            JOIN op_faculty f ON f.id = rel.op_faculty_id AND f.active = true
            ORDER BY d.name
        """)
        return [{'id': r[0], 'name': r[1], 'code': r[2] or ''} for r in cr.fetchall()]

    @api.model
    def get_perfilazio_zikloak(self, dept_id):
        cr = self.env.cr
        cr.execute("""
            SELECT id, name FROM op_course WHERE department_id = %s AND active = true ORDER BY name
        """, (dept_id,))
        return [{'id': r[0], 'name': r[1]} for r in cr.fetchall()]

    @api.model
    def get_perfilazio_batches(self, course_id):
        cr = self.env.cr
        cr.execute("""
            SELECT id, name FROM op_batch WHERE course_id = %s AND active = true ORDER BY name
        """, (course_id,))
        return [{'id': r[0], 'name': r[1]} for r in cr.fetchall()]

    @api.model
    def get_perfilazio_irakasleak(self, dept_id):
        cr = self.env.cr
        cr.execute("""
            SELECT
                f.id,
                rp.name,
                COALESCE(
                    (SELECT SUM(s.rpt_total) FROM op_subject s WHERE s.faculty_id = f.id), 0
                ) + COALESCE(
                    (SELECT SUM(pk.orduak) FROM op_perfilazio_kargu pk WHERE pk.faculty_id = f.id), 0
                ) AS orduak,
                f.kidergoa,
                COALESCE(
                    (SELECT SUM(s.gela_orduak) FROM op_subject s WHERE s.faculty_id = f.id), 0
                ) AS gela
            FROM op_faculty f
            JOIN res_partner rp ON rp.id = f.partner_id
            JOIN op_department_op_faculty_rel rel ON rel.op_faculty_id = f.id
            WHERE rel.op_department_id = %s AND f.active = true
              AND (f.kidergoa = 'funtzionarioa' OR f.kidergoa = 'impersonala')
            ORDER BY
                CASE WHEN f.kidergoa = 'impersonala' THEN 1 ELSE 0 END,
                f.last_name
        """, (dept_id,))
        return [
            {'id': r[0], 'name': r[1], 'orduak': float(r[2]),
             'overload': float(r[2]) > 17, 'kidergoa': r[3] or '',
             'gela': float(r[4])}
            for r in cr.fetchall()
        ]

    @api.model
    def create_perfilazio_impersonal(self, dept_id):
        dept = self.env['op.department'].browse(dept_id)
        code = (dept.code or dept.name or 'PROF').strip()
        prefix = code[:4].upper()
        pattern = prefix + '_X%'
        cr = self.env.cr
        cr.execute("""
            SELECT rp.name FROM op_faculty f
            JOIN res_partner rp ON rp.id = f.partner_id
            JOIN op_department_op_faculty_rel rel ON rel.op_faculty_id = f.id
            WHERE rel.op_department_id = %s AND f.kidergoa = 'impersonala'
              AND rp.name LIKE %s
        """, (dept_id, pattern))
        used = set()
        for (name,) in cr.fetchall():
            try:
                used.add(int(name.split('_X')[-1]))
            except (ValueError, IndexError):
                pass
        n = 1
        while n in used:
            n += 1
        new_name = f'{prefix}_X{n}'
        partner = self.env['res.partner'].create({'name': new_name})
        faculty = self.env['op.faculty'].create({
            'partner_id': partner.id,
            'first_name': prefix,
            'last_name': f'X{n}',
            'birth_date': '1970-01-01',
            'gender': 'male',
            'kidergoa': 'impersonala',
            'allowed_department_ids': [(6, 0, [dept_id])],
        })
        self.env.flush_all()
        return {'id': faculty.id, 'name': new_name, 'orduak': 0.0, 'overload': False, 'gela': 0.0}

    @api.model
    def clear_perfilazio_faculty(self, faculty_id):
        self.env['op.subject'].search([('faculty_id', '=', faculty_id)]).write({'faculty_id': False})
        self.env.flush_all()
        cr = self.env.cr
        cr.execute("""
            SELECT COALESCE((SELECT SUM(pk.orduak) FROM op_perfilazio_kargu pk WHERE pk.faculty_id = %s), 0)
        """, (faculty_id,))
        orduak = float(cr.fetchone()[0])
        return {'id': faculty_id, 'orduak': orduak, 'overload': orduak > 17, 'gela': 0.0}

    @api.model
    def get_perfilazio_resumen(self, faculty_id):
        cr = self.env.cr
        cr.execute("""
            SELECT s.code, s.name, s.rpt_total, b.name AS batch_name,
                   s.kurtsoa, s.pt_pes, s.orduak, s.gela_orduak,
                   s.aste_banaketa, s.orduak_zorretan
            FROM op_subject s
            LEFT JOIN op_batch b ON b.id = s.batch_id
            WHERE s.faculty_id = %s
            ORDER BY b.name, s.code
        """, (faculty_id,))
        return [
            {
                'code': r[0] or '', 'name': r[1] or '',
                'rpt_total': float(r[2] or 0), 'batch': r[3] or '',
                'kurtsoa': r[4] or '', 'pt_pes': r[5] or '',
                'orduak': float(r[6] or 0), 'gela_orduak': float(r[7] or 0),
                'aste_banaketa': r[8] or '', 'orduak_zorretan': float(r[9] or 0),
            }
            for r in cr.fetchall()
        ]

    @api.model
    def delete_perfilazio_impersonal(self, faculty_id):
        faculty = self.env['op.faculty'].browse(faculty_id)
        if not faculty.exists() or faculty.kidergoa != 'impersonala':
            return False
        self.env['op.subject'].search([('faculty_id', '=', faculty_id)]).write({'faculty_id': False})
        partner = faculty.partner_id
        faculty.unlink()
        if partner.exists():
            partner.unlink()
        return True

    @api.model
    def get_perfilazio_ingelesa_moduluak(self):
        """Todos los módulos de inglés (código con el token _ING),
        independientemente del taldea. Para el mintegi Ingelesa."""
        cr = self.env.cr
        cr.execute(r"""
            SELECT
                s.id, s.code, s.name,
                s.pt_pes, s.orduak, s.kurtsoa, s.aste_banaketa,
                s.gela_orduak, s.rpt_total, s.orduak_zorretan,
                s.faculty_id,
                rp.name AS faculty_name
            FROM op_subject s
            LEFT JOIN op_faculty f ON f.id = s.faculty_id
            LEFT JOIN res_partner rp ON rp.id = f.partner_id
            WHERE s.code ~* '_ING(_|$)'
            ORDER BY s.code
        """)
        return [
            {
                'id': r[0], 'code': r[1] or '', 'name': r[2] or '',
                'pt_pes': r[3] or '', 'orduak': float(r[4] or 0),
                'kurtsoa': r[5] or '', 'aste_banaketa': r[6] or '',
                'gela_orduak': float(r[7] or 0),
                'rpt_total': float(r[8] or 0), 'orduak_zorretan': float(r[9] or 0),
                'faculty_id': r[10], 'faculty_name': r[11],
            }
            for r in cr.fetchall()
        ]

    @api.model
    def get_perfilazio_moduluak(self, batch_id):
        cr = self.env.cr
        cr.execute("""
            SELECT
                s.id, s.code, s.name,
                s.pt_pes, s.orduak, s.kurtsoa, s.aste_banaketa,
                s.gela_orduak, s.rpt_total, s.orduak_zorretan,
                s.faculty_id,
                rp.name AS faculty_name
            FROM op_subject s
            LEFT JOIN op_faculty f ON f.id = s.faculty_id
            LEFT JOIN res_partner rp ON rp.id = f.partner_id
            WHERE s.batch_id = %s
            ORDER BY s.code
        """, (batch_id,))
        return [
            {
                'id': r[0], 'code': r[1] or '', 'name': r[2] or '',
                'pt_pes': r[3] or '', 'orduak': float(r[4] or 0),
                'kurtsoa': r[5] or '', 'aste_banaketa': r[6] or '',
                'gela_orduak': float(r[7] or 0),
                'rpt_total': float(r[8] or 0), 'orduak_zorretan': float(r[9] or 0),
                'faculty_id': r[10], 'faculty_name': r[11],
            }
            for r in cr.fetchall()
        ]

    @api.model
    def assign_perfilazio_modulu(self, subject_id, faculty_id):
        subject = self.env['op.subject'].browse(subject_id)
        old_faculty_id = subject.faculty_id.id if subject.faculty_id else None
        subject.write({'faculty_id': faculty_id or False})
        self.env.flush_all()
        affected_ids = list(filter(None, {old_faculty_id, faculty_id or None}))
        result = []
        cr = self.env.cr
        for fid in affected_ids:
            cr.execute("""
                SELECT
                    COALESCE((SELECT SUM(s.rpt_total) FROM op_subject s WHERE s.faculty_id = %s), 0)
                    + COALESCE((SELECT SUM(pk.orduak) FROM op_perfilazio_kargu pk WHERE pk.faculty_id = %s), 0),
                    COALESCE((SELECT SUM(s.gela_orduak) FROM op_subject s WHERE s.faculty_id = %s), 0)
            """, (fid, fid, fid))
            row = cr.fetchone()
            orduak = float(row[0])
            result.append({'id': fid, 'orduak': orduak, 'overload': orduak > 17,
                           'gela': float(row[1])})
        return result

    @api.model
    def get_perfilazio_karguak(self, faculty_id):
        cr = self.env.cr
        cr.execute("""
            SELECT pk.id, pk.kargu_id, k.code, k.name, k.rpt_total, pk.orduak,
                   COALESCE((
                       SELECT SUM(pk2.orduak) FROM op_perfilazio_kargu pk2
                       WHERE pk2.kargu_id = k.id AND pk2.faculty_id <> pk.faculty_id
                   ), 0) AS assigned_others
            FROM op_perfilazio_kargu pk
            JOIN op_kargu k ON k.id = pk.kargu_id
            WHERE pk.faculty_id = %s
            ORDER BY k.name
        """, (faculty_id,))
        return [
            {'id': r[0], 'kargu_id': r[1], 'code': r[2] or '', 'name': r[3] or '',
             'kargu_rpt': float(r[4] or 0), 'orduak': float(r[5]),
             'max_orduak': max(float(r[4] or 0) - float(r[6] or 0), 0.0)}
            for r in cr.fetchall()
        ]

    @api.model
    def get_all_karguak(self, faculty_id=None):
        cr = self.env.cr
        cr.execute("""
            SELECT k.id, k.code, k.name, k.rpt_total,
                   COALESCE(SUM(pk.orduak), 0) AS assigned,
                   COALESCE(SUM(pk.orduak) FILTER (WHERE pk.faculty_id <> %s), 0) AS assigned_others
            FROM op_kargu k
            LEFT JOIN op_perfilazio_kargu pk ON pk.kargu_id = k.id
            GROUP BY k.id, k.code, k.name, k.rpt_total
            ORDER BY k.name
        """, (faculty_id or 0,))
        return [
            {'id': r[0], 'code': r[1] or '', 'name': r[2] or '',
             'rpt_total': float(r[3] or 0), 'assigned': float(r[4]),
             'remaining': max(float(r[3] or 0) - float(r[5] or 0), 0.0)}
            for r in cr.fetchall()
        ]

    @api.model
    def upsert_perfilazio_kargu(self, faculty_id, kargu_id, orduak):
        orduak = float(orduak or 0)
        kargu = self.env['op.kargu'].browse(kargu_id)
        cr = self.env.cr
        cr.execute("""
            SELECT COALESCE(SUM(orduak), 0) FROM op_perfilazio_kargu
            WHERE kargu_id = %s AND faculty_id <> %s
        """, (kargu_id, faculty_id))
        assigned_others = float(cr.fetchone()[0])
        max_allowed = float(kargu.rpt_total or 0) - assigned_others
        if orduak > max_allowed:
            raise UserError(_(
                "'%(kargu)s' karguak %(libre)s ordu libre baino ez ditu "
                "(guztira: %(total)sh, beste irakasleek esleituta: %(besteak)sh).",
                kargu=kargu.code, libre=max_allowed,
                total=float(kargu.rpt_total or 0), besteak=assigned_others,
            ))
        existing = self.env['op.perfilazio.kargu'].search([
            ('faculty_id', '=', faculty_id), ('kargu_id', '=', kargu_id)
        ], limit=1)
        if existing:
            existing.orduak = orduak
        else:
            self.env['op.perfilazio.kargu'].create({
                'faculty_id': faculty_id, 'kargu_id': kargu_id, 'orduak': orduak,
            })
        cr.execute("""
            SELECT
                COALESCE((SELECT SUM(s.rpt_total) FROM op_subject s WHERE s.faculty_id = %s), 0)
                + COALESCE((SELECT SUM(pk.orduak) FROM op_perfilazio_kargu pk WHERE pk.faculty_id = %s), 0)
        """, (faculty_id, faculty_id))
        orduak_total = float(cr.fetchone()[0])
        return {'orduak': orduak_total, 'overload': orduak_total > 17}

    @api.model
    def delete_perfilazio_kargu(self, line_id):
        line = self.env['op.perfilazio.kargu'].browse(line_id)
        faculty_id = line.faculty_id.id
        line.unlink()
        cr = self.env.cr
        cr.execute("""
            SELECT
                COALESCE((SELECT SUM(s.rpt_total) FROM op_subject s WHERE s.faculty_id = %s), 0)
                + COALESCE((SELECT SUM(pk.orduak) FROM op_perfilazio_kargu pk WHERE pk.faculty_id = %s), 0)
        """, (faculty_id, faculty_id))
        orduak_total = float(cr.fetchone()[0])
        return {'orduak': orduak_total, 'overload': orduak_total > 17}

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
