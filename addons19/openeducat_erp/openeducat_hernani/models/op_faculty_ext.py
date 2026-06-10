import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError


# Módulos no técnicos: el token del código del módulo determina qué
# departamento (por `code`) imparte el módulo. El orden no importa porque
# los tokens no se solapan. Cada token se busca delimitado por `_` o por
# inicio/fin de cadena (p.ej. `2EMF1_KOG_2`, `1AST3_ING_P`, `1EMF1_IPE`).
SPECIAL_MODULU_DEPT = [
    ('EIP', 'LPO'),       # Ekintzailetza → LPO
    ('IPE', 'LPO'),       # Ekintzailetza → LPO
    ('KOG', 'INGELES'),   # Konpetentzia digitala/ingelesa → Ingelesa
    ('ING', 'INGELES'),   # Ingelesa (ING / ING_P) → Ingelesa
    ('ZIA', 'ORIENTA'),   # Zientzia aplikatuak/orientazioa → Orientazioa
]


def _modulu_special_dept_code(code):
    """Devuelve el `code` del departamento que imparte el módulo cuando es
    un módulo especial (no técnico), o None si lo imparte el propio mintegi."""
    if not code:
        return None
    up = code.upper()
    for token, dept_code in SPECIAL_MODULU_DEPT:
        if re.search(r'(^|_)' + token + r'(_|$)', up):
            return dept_code
    return None


# Módulos TUTO: además del profesor del mintegi, pueden asignarse a un
# profesor de Orientazioa, LPO o Ingelesa (se muestran 3 desplegables).
TUTO_DEPT_CODES = ('ORIENTA', 'LPO', 'INGELES')


def _modulu_is_tuto(code):
    return bool(code) and bool(re.search(r'(^|_)TUTO(_|$)', code.upper()))


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
        cr.execute(r"""
            SELECT c.id, c.name,
                EXISTS(SELECT 1 FROM op_subject s JOIN op_batch b ON b.id = s.batch_id
                       WHERE b.course_id = c.id AND s.active = true
                         AND s.code ~* '^HE_') AS has_he,
                EXISTS(SELECT 1 FROM op_subject s JOIN op_batch b ON b.id = s.batch_id
                       WHERE b.course_id = c.id AND s.active = true
                         AND s.code ~* '^DESDO_') AS has_desdo
            FROM op_course c
            WHERE c.department_id = %s AND c.active = true
            ORDER BY c.name
        """, (dept_id,))
        return [{'id': r[0], 'name': r[1], 'has_he': r[2], 'has_desdo': r[3]}
                for r in cr.fetchall()]

    @api.model
    def get_perfilazio_batches(self, course_id):
        cr = self.env.cr
        cr.execute("""
            SELECT id, name FROM op_batch WHERE course_id = %s AND active = true ORDER BY name
        """, (course_id,))
        return [{'id': r[0], 'name': r[1]} for r in cr.fetchall()]

    @api.model
    def get_perfilazio_ziklo_moduluak(self, course_id):
        """Todos los módulos de un ciclo (vía sus taldeak), excluyendo los ya
        generados como desdoble (DESDO_) o eleanitza (HE_). Cada módulo indica
        con has_he / has_desdo si su copia ya existe (selección del panel)."""
        cr = self.env.cr
        cr.execute(r"""
            SELECT
                s.id, s.code, s.name,
                s.pt_pes, s.orduak, s.kurtsoa, s.aste_banaketa,
                s.gela_orduak, s.rpt_total, s.orduak_zorretan,
                EXISTS(SELECT 1 FROM op_subject h
                       WHERE h.code = 'HE_' || s.code) AS has_he,
                EXISTS(SELECT 1 FROM op_subject d
                       WHERE d.code = 'DESDO_' || s.code) AS has_desdo
            FROM op_subject s
            JOIN op_batch b ON b.id = s.batch_id
            WHERE b.course_id = %s
              AND s.active = true
              AND s.code !~* '^(DESDO_|HE_)'
            ORDER BY s.code
        """, (course_id,))
        return [
            {
                'id': r[0], 'code': r[1] or '', 'name': r[2] or '',
                'pt_pes': r[3] or '', 'orduak': float(r[4] or 0),
                'kurtsoa': r[5] or '', 'aste_banaketa': r[6] or '',
                'gela_orduak': float(r[7] or 0),
                'rpt_total': float(r[8] or 0), 'orduak_zorretan': float(r[9] or 0),
                'has_he': r[10], 'has_desdo': r[11],
            }
            for r in cr.fetchall()
        ]

    def _copy_subject_with_prefix(self, src, prefix):
        """Crea la copia DESDO_/HE_ de un módulo (mismo ciclo/taldea/curso,
        sin profesor), saneando campos Selection con datos heredados inválidos.
        Devuelve el registro creado, o False si ya existía."""
        Subject = self.env['op.subject']
        new_code = prefix + (src.code or '')
        if Subject.with_context(active_test=False).search(
                [('code', '=', new_code)], limit=1):
            return False
        sel_fields = {
            'hizkuntza':    ({'euskaraz', 'gazteleraz', 'eleanitza'}, False),
            'pt_pes':       ({'PT', 'PES', 'PT_PES'}, False),
            'type':         ({'theory', 'practical', 'both', 'other'}, 'theory'),
            'subject_type': ({'compulsory', 'elective'}, 'compulsory'),
        }
        cr = self.env.cr
        cr.execute("SELECT hizkuntza, pt_pes, type, subject_type "
                   "FROM op_subject WHERE id = %s", (src.id,))
        row = dict(zip(('hizkuntza', 'pt_pes', 'type', 'subject_type'), cr.fetchone()))
        defaults = {
            'code': new_code,
            'name': (prefix + (src.name or ''))[:128],
            'faculty_id': False,
        }
        for field, (allowed, fallback) in sel_fields.items():
            if row[field] is not None and row[field] not in allowed:
                defaults[field] = fallback
        return src.copy(defaults)

    @api.model
    def toggle_perfilazio_kopia(self, subject_id, prefix):
        """Alterna la existencia de la copia DESDO_/HE_ de un módulo.
        - Si no existe: la crea (seleccionar).
        - Si existe: la elimina (deseleccionar). Al borrarla, si estaba
          asignada a un profesor desaparece de su perfilación y sus horas se
          recalculan automáticamente (las sumas son sobre módulos existentes).
        Devuelve {'exists': bool} con el estado final."""
        Subject = self.env['op.subject']
        src = Subject.browse(subject_id)
        if not src.exists() or not src.code:
            return {'exists': False}
        new_code = (prefix or '') + src.code
        existing = Subject.with_context(active_test=False).search(
            [('code', '=', new_code)], limit=1)
        if existing:
            existing.unlink()
            self.env.flush_all()
            return {'exists': False}
        self._copy_subject_with_prefix(src, prefix)
        self.env.flush_all()
        return {'exists': True}

    # ── Apoyo Educativo ──────────────────────────────────────────────
    APOYO_KODEAK = ('I', 'II', 'III')

    def _apoyo_payload(self, taldea):
        """Datos de un multzo de apoyo: tope de horas, suma RPT y módulos."""
        mods = []
        sum_rpt = 0.0
        for s in taldea.subject_ids.sorted('code'):
            sum_rpt += float(s.rpt_total or 0)
            mods.append({
                'id': s.id, 'code': s.code or '', 'pt_pes': s.pt_pes or '',
                'orduak': float(s.orduak or 0), 'kurtsoa': s.kurtsoa or '',
                'aste_banaketa': s.aste_banaketa or '',
                'gela_orduak': float(s.gela_orduak or 0),
                'rpt_total': float(s.rpt_total or 0),
                'orduak_zorretan': float(s.orduak_zorretan or 0),
            })
        return {
            'id': taldea.id,
            'guztira_orduak': float(taldea.guztira_orduak or 0),
            'sum_rpt': round(sum_rpt, 2),
            'modules': mods,
        }

    def _get_or_create_apoyo(self, batch_id, kodea):
        if kodea not in self.APOYO_KODEAK:
            raise UserError(_("Apoyo multzo baliogabea: %s", kodea))
        Apoyo = self.env['op.apoyo.taldea']
        taldea = Apoyo.search(
            [('batch_id', '=', batch_id), ('kodea', '=', kodea)], limit=1)
        if not taldea:
            taldea = Apoyo.create({'batch_id': batch_id, 'kodea': kodea})
        return taldea

    @api.model
    def get_banaketa_aukerak(self):
        cr = self.env.cr
        cr.execute("SELECT id, name FROM op_subject_banaketa ORDER BY guztira, name")
        return [{'id': r[0], 'name': r[1]} for r in cr.fetchall()]

    @api.model
    def get_apoyo_taldea(self, batch_id, kodea):
        taldea = self._get_or_create_apoyo(batch_id, kodea)
        return self._apoyo_payload(taldea)

    @api.model
    def set_apoyo_guztira(self, batch_id, kodea, orduak):
        taldea = self._get_or_create_apoyo(batch_id, kodea)
        taldea.guztira_orduak = float(orduak or 0)
        return self._apoyo_payload(taldea)

    @api.model
    def create_apoyo_modulu(self, batch_id, kodea, vals):
        taldea = self._get_or_create_apoyo(batch_id, kodea)
        vals = vals or {}
        code = (vals.get('code') or '').strip()
        if not code:
            raise UserError(_("Kodea beharrezkoa da."))
        new_rpt = float(vals.get('rpt_total') or 0)
        sum_rpt = sum(float(s.rpt_total or 0) for s in taldea.subject_ids)
        guztira = float(taldea.guztira_orduak or 0)
        if guztira > 0 and round(sum_rpt, 2) >= round(guztira, 2):
            raise UserError(_(
                "Multzoa beteta dago (%(batura)sh / %(guztira)sh). "
                "Ezin da modulu gehiago gehitu.",
                batura=round(sum_rpt, 2), guztira=guztira))
        if sum_rpt + new_rpt > guztira:
            raise UserError(_(
                "RPT batura (%(batura)sh) ezin du multzoaren guztira "
                "(%(guztira)sh) gainditu.",
                batura=round(sum_rpt + new_rpt, 2), guztira=guztira))
        pt_pes = vals.get('pt_pes') or False
        if pt_pes not in ('PT', 'PES', 'PT_PES'):
            pt_pes = False
        self.env['op.subject'].create({
            'name': code[:128],
            'code': code,
            'batch_id': batch_id,
            'apoyo_taldea_id': taldea.id,
            'pt_pes': pt_pes,
            'orduak': float(vals.get('orduak') or 0),
            'kurtsoa': (vals.get('kurtsoa') or '')[:10],
            'banaketa_id': int(vals['banaketa_id']) if vals.get('banaketa_id') else False,
            'gela_orduak': float(vals.get('gela_orduak') or 0),
            'rpt_total': new_rpt,
            'orduak_zorretan': float(vals.get('orduak_zorretan') or 0),
        })
        self.env.flush_all()
        return self._apoyo_payload(taldea)

    @api.model
    def delete_apoyo_modulu(self, subject_id):
        subject = self.env['op.subject'].browse(subject_id)
        taldea = subject.apoyo_taldea_id
        subject.unlink()
        self.env.flush_all()
        return self._apoyo_payload(taldea) if taldea.exists() else \
            {'id': False, 'guztira_orduak': 0.0, 'sum_rpt': 0.0, 'modules': []}

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
    def get_perfilazio_laburpena(self, dept_id):
        """Resumen de perfilación de TODOS los profesores del mintegi
        (funtzionarioak + impersonalak). Para cada profesor devuelve su
        nombre, los roles (Mintegiburua / Taldeko tutorea) y las filas de su
        perfilación (módulos + karguak) con columnas Kodea, Gela, RPT."""
        cr = self.env.cr
        cr.execute("""
            SELECT f.id, rp.name, f.kidergoa
            FROM op_faculty f
            JOIN res_partner rp ON rp.id = f.partner_id
            JOIN op_department_op_faculty_rel rel ON rel.op_faculty_id = f.id
            WHERE rel.op_department_id = %s AND f.active = true
              AND (f.kidergoa = 'funtzionarioa' OR f.kidergoa = 'impersonala')
            ORDER BY
                CASE WHEN f.kidergoa = 'impersonala' THEN 1 ELSE 0 END,
                f.last_name
        """, (dept_id,))
        faculties = cr.fetchall()

        result = []
        for fid, name, kidergoa in faculties:
            # Roles desde los karguak perfilados (op_perfilazio_kargu)
            cr.execute("""
                SELECT k.code
                FROM op_perfilazio_kargu pk
                JOIN op_kargu k ON k.id = pk.kargu_id
                WHERE pk.faculty_id = %s
                ORDER BY k.code
            """, (fid,))
            kargu_codes = [r[0] or '' for r in cr.fetchall()]
            roles = []
            for code in kargu_codes:
                up = code.upper()
                if up.startswith('MB-'):
                    roles.append('Mintegiburua')
                elif up.startswith('TUTO_'):
                    suffix = code[5:].strip()
                    roles.append('Taldeko tutorea' + (f' ({suffix})' if suffix else ''))

            # Filas: módulos (Kodea, Gela, RPT)
            cr.execute("""
                SELECT s.code, s.gela_orduak, s.rpt_total
                FROM op_subject s
                WHERE s.faculty_id = %s
                ORDER BY s.code
            """, (fid,))
            rows = [
                {'code': r[0] or '', 'gela': float(r[1] or 0),
                 'rpt': float(r[2] or 0), 'is_kargu': False}
                for r in cr.fetchall()
            ]
            # Filas: karguak (Kodea, sin Gela, RPT = orduak)
            cr.execute("""
                SELECT k.code, pk.orduak
                FROM op_perfilazio_kargu pk
                JOIN op_kargu k ON k.id = pk.kargu_id
                WHERE pk.faculty_id = %s
                ORDER BY k.code
            """, (fid,))
            for r in cr.fetchall():
                rows.append({'code': r[0] or '', 'gela': None,
                             'rpt': float(r[1] or 0), 'is_kargu': True})

            gela_total = round(sum(r['gela'] or 0 for r in rows), 2)
            rpt_total = round(sum(r['rpt'] or 0 for r in rows), 2)
            result.append({
                'id': fid, 'name': name, 'kidergoa': kidergoa or '',
                'roles': roles, 'rows': rows,
                'gela_total': gela_total, 'rpt_total': rpt_total,
                'overload': rpt_total > 17,
            })
        return result

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
                'special_dept': _modulu_special_dept_code(r[1]),
                'tuto': _modulu_is_tuto(r[1]),
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
                'special_dept': _modulu_special_dept_code(r[1]),
                'tuto': _modulu_is_tuto(r[1]),
            }
            for r in cr.fetchall()
        ]

    @api.model
    def get_special_modulu_irakasleak(self, dept_codes):
        """Para cada `code` de departamento, devuelve los profesores candidatos
        para impartir módulos especiales. Igual que el panel Perfilazioak: solo
        funtzionarioak e inpertsonalak (X1, X2…), no todos los activos.
        Devuelve un dict {dept_code: [{'id', 'name'}, ...]}."""
        cr = self.env.cr
        result = {}
        for dcode in set(dept_codes or []):
            cr.execute("""
                SELECT f.id, rp.name
                FROM op_faculty f
                JOIN res_partner rp ON rp.id = f.partner_id
                JOIN op_department d ON d.code = %s
                JOIN op_department_op_faculty_rel rel
                    ON rel.op_faculty_id = f.id AND rel.op_department_id = d.id
                WHERE f.active = true
                  AND (f.kidergoa = 'funtzionarioa' OR f.kidergoa = 'impersonala')
                ORDER BY
                    CASE WHEN f.kidergoa = 'impersonala' THEN 1 ELSE 0 END,
                    f.last_name
            """, (dcode,))
            result[dcode] = [{'id': r[0], 'name': r[1]} for r in cr.fetchall()]
        return result

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
