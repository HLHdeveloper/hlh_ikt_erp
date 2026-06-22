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


def _fmt_h(v):
    """Formatea horas con decimal de coma (estilo eu/es): 7→'7', 3.2→'3,2'."""
    v = round(float(v or 0), 2)
    if v == int(v):
        return str(int(v))
    return ("%.2f" % v).rstrip('0').rstrip('.').replace('.', ',')


def _jardunaldi_mota(total):
    """Tipo de jornada según el TOTAL de horas RPT de la plaza:
    osoa(17)→'C', 2/3(12), 1/2(9), 1/3(6). Se usa el bracket más cercano."""
    t = float(total or 0)
    if t <= 0:
        return ''
    if t >= 14.5:
        return 'C'
    if t >= 10.5:
        return '2/3'
    if t >= 7.5:
        return '1/2'
    return '1/3'


# Código TALDEA (especialidad/cuerpo) por distintivo PT/PES de la plaza.
PLAZA_TALDEA_KODEA = {'PES': '0237', 'PT': '1555'}


# Karguak TUTO de estos grupos pueden perfilarse con 0 horas (tutor sin RPT,
# p.ej. cotutoreak). El resto de TUTO_ y todos los MB requieren ≥1h.
# 'FG_ESP' (TUTO_FG_ESP) es un cargo de tutor sin RPT (0h) sin grupo propio.
ZERO_HOUR_TUTO_GROUPS = ('MLE', 'MSS', 'IEA', 'SEA', 'FMD', 'AST', 'FG_ESP')


def _kargu_allows_zero(code):
    up = (code or '').upper()
    if not up.startswith('TUTO_'):
        return False
    return any(grp in up for grp in ZERO_HOUR_TUTO_GROUPS)


def _kargu_allows_decimal(code):
    """Permite horas con un decimal (paso 0,1). Aplica a todos los karguak
    salvo TUTO_* y MB-*, que se reparten en horas enteras."""
    up = (code or '').upper()
    if _modulu_is_tuto(code) or up.startswith('MB-') or up.startswith('MB_') or up == 'MB':
        return False
    return True


class OpFaculty(models.Model):
    _inherit = 'op.faculty'

    kidergoa = fields.Char(string='Kidergoa')

    # Distintivo PT/PES de la perfilación. Vacío = automático (PT si algún
    # módulo del profesor tiene PT, si no PES). Con valor ('PT'/'PES') =
    # override manual fijado desde el badge de Perfilazioak.
    perfilazio_pt_pes = fields.Char(string='Perfilazio PT/PES')

    # Ordezkoa asignado a una perfilación impersonal (INFO_X1, INFO_X2…).
    # Solo es una anotación de planificación: la perfilación NO se mueve,
    # solo se deja constancia de qué ordezkoa cubrirá esa plaza X.
    ordezko_esleitua_id = fields.Many2one(
        'op.faculty', string='Ordezko esleitua',
        ondelete='set null', index=True,
        help='Perfilazio impertsonal hau estaliko duen mintegiko ordezkoa.')

    # Tabla de plazas (PLAZAK IKUSI): columnas editables por plaza impersonal.
    # El resto de columnas se derivan de la perfilación.
    plaza_bakantea = fields.Char(string='Bakantea')
    plaza_oharrak = fields.Text(string='Oharrak (plaza)')
    # Override manual (vacío = valor automático derivado de la perfilación).
    plaza_hizkuntza_perfila = fields.Char(string='Hizkuntza perfila (plaza)')
    plaza_jarduna = fields.Char(string='Jarduna (plaza)')

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
    def get_perfilazio_ziklo_moduluak(self, batch_id):
        """Módulos de la TALDEA seleccionada (solo sus '<taldea>_XXX'),
        excluyendo los ya generados como desdoble (DESDO_) o eleanitza (HE_).
        Cada módulo indica con has_he / has_desdo si su copia ya existe."""
        cr = self.env.cr
        cr.execute(r"""
            SELECT
                s.id, s.code, s.name,
                s.pt_pes, s.orduak, s.kurtsoa, s.aste_banaketa,
                s.gela_orduak, s.rpt_total, s.orduak_zorretan,
                EXISTS(SELECT 1 FROM op_subject h
                       WHERE h.code = 'HE_' || s.code) AS has_he,
                EXISTS(SELECT 1 FROM op_subject d
                       WHERE d.code = 'DESDO_' || s.code) AS has_desdo,
                (SELECT d.rpt_total FROM op_subject d
                 WHERE d.code = 'DESDO_' || s.code LIMIT 1) AS desdo_orduak,
                s.pl
            FROM op_subject s
            WHERE s.batch_id = %s
              AND s.active = true
              AND s.code !~* '^(DESDO_|HE_)'
            ORDER BY s.code
        """, (batch_id,))
        return [
            {
                'id': r[0], 'code': r[1] or '', 'name': r[2] or '',
                'pt_pes': r[3] or '', 'orduak': float(r[4] or 0),
                'kurtsoa': r[5] or '', 'aste_banaketa': r[6] or '',
                'gela_orduak': float(r[7] or 0),
                'rpt_total': float(r[8] or 0), 'orduak_zorretan': float(r[9] or 0),
                'has_he': r[10], 'has_desdo': r[11],
                # Horas de desdoble: las de la copia DESDO_ existente, o por
                # defecto el RPT total del módulo origen (comportamiento previo).
                'desdo_orduak': float(r[12]) if r[12] is not None else float(r[8] or 0),
                'pl': (r[13] or '').replace('_', '/'),
            }
            for r in cr.fetchall()
        ]

    def _copy_subject_with_prefix(self, src, prefix, overrides=None):
        """Crea la copia DESDO_/HE_ de un módulo (mismo ciclo/taldea/curso,
        sin profesor), saneando campos Selection con datos heredados inválidos.
        `overrides` permite fijar campos adicionales en la copia (p.ej. las horas
        de desdoble). Devuelve el registro creado, o False si ya existía."""
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
        if overrides:
            defaults.update(overrides)
        return src.copy(defaults)

    def _desdo_used_orduak(self, batch_id, exclude_code=None):
        """Suma de horas de desdoble (rpt_total de las copias DESDO_ activas)
        de una taldea, opcionalmente excluyendo una copia por su code."""
        cr = self.env.cr
        cr.execute("""
            SELECT COALESCE(SUM(rpt_total), 0)
            FROM op_subject
            WHERE batch_id = %s AND active = true
              AND code ~* '^DESDO_' AND code <> %s
        """, (batch_id, exclude_code or ''))
        return float(cr.fetchone()[0] or 0)

    def _clamp_desdo_orduak(self, src, desdo_orduak):
        """Acota las horas de desdoble: al RPT total del módulo origen y al tope
        de horas de desdoble del grupo (batch.desdoble_orduak; 0 = sin tope).
        La suma de desdoble del grupo no puede superar ese tope."""
        try:
            v = float(desdo_orduak)
        except (TypeError, ValueError):
            return None
        if v < 0:
            v = 0.0
        cap = float(src.rpt_total or 0)
        if v > cap:
            v = cap
        total = float(src.batch_id.desdoble_orduak or 0)
        if total > 0:
            used_others = self._desdo_used_orduak(
                src.batch_id.id, exclude_code='DESDO_' + (src.code or ''))
            group_cap = max(total - used_others, 0.0)
            if v > group_cap:
                v = group_cap
        return round(v, 2)

    @api.model
    def get_perfilazio_desdoble_info(self, batch_id):
        """Tope de horas de desdoble del grupo y horas ya consumidas (suma de
        rpt_total de las copias DESDO_ de la taldea)."""
        batch = self.env['op.batch'].browse(batch_id)
        total = float(batch.desdoble_orduak or 0) if batch.exists() else 0.0
        used = self._desdo_used_orduak(batch_id)
        return {'total': round(total, 2), 'used': round(used, 2),
                'remaining': round(max(total - used, 0.0), 2)}

    @api.model
    def set_perfilazio_desdoble_total(self, batch_id, orduak):
        """Fija el tope total de horas de desdoble del grupo (batch.desdoble_orduak)."""
        batch = self.env['op.batch'].browse(batch_id)
        if not batch.exists():
            return False
        try:
            v = max(float(orduak), 0.0)
        except (TypeError, ValueError):
            v = 0.0
        batch.write({'desdoble_orduak': round(v, 2)})
        self.env.flush_all()
        return self.get_perfilazio_desdoble_info(batch_id)

    @api.model
    def toggle_perfilazio_kopia(self, subject_id, prefix, desdo_orduak=None):
        """Alterna la existencia de la copia DESDO_/HE_ de un módulo.
        - Si no existe: la crea (seleccionar). Para DESDO_, si se indica
          `desdo_orduak`, la copia se crea con ese RPT (total y reala) en vez
          de heredar el RPT completo del módulo origen.
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
        overrides = None
        applied = None
        if prefix == 'DESDO_' and desdo_orduak is not None:
            v = self._clamp_desdo_orduak(src, desdo_orduak)
            if v is not None:
                overrides = {'rpt_total': v, 'rpt_reala': v}
                applied = v
        self._copy_subject_with_prefix(src, prefix, overrides=overrides)
        self.env.flush_all()
        return {'exists': True, 'orduak': applied}

    @api.model
    def set_perfilazio_desdoble_orduak(self, subject_id, desdo_orduak):
        """Actualiza las horas (RPT) de la copia DESDO_ ya existente de un
        módulo origen. Las acota a [0, rpt_total del origen] y fija tanto
        rpt_total como rpt_reala (RPT = rpt_reala en la perfilación). Si la
        copia está asignada a un profesor, sus horas se recalcularán al
        recargar. Devuelve {'orduak': horas_aplicadas} o False si no existe."""
        Subject = self.env['op.subject']
        src = Subject.browse(subject_id)
        if not src.exists() or not src.code:
            return False
        copy = Subject.with_context(active_test=False).search(
            [('code', '=', 'DESDO_' + src.code)], limit=1)
        if not copy:
            return False
        v = self._clamp_desdo_orduak(src, desdo_orduak)
        if v is None:
            return False
        copy.write({'rpt_total': v, 'rpt_reala': v})
        self.env.flush_all()
        return {'orduak': v}

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
                    (SELECT SUM(s.rpt_reala) FROM op_subject s WHERE s.faculty_id = f.id), 0
                ) + COALESCE(
                    (SELECT SUM(pk.orduak) FROM op_perfilazio_kargu pk WHERE pk.faculty_id = f.id), 0
                ) AS orduak,
                f.kidergoa,
                COALESCE(
                    (SELECT SUM(s.gela_orduak) FROM op_subject s WHERE s.faculty_id = f.id), 0
                ) AS gela,
                COALESCE(
                    NULLIF(UPPER(f.perfilazio_pt_pes), ''),
                    CASE WHEN EXISTS (
                        SELECT 1 FROM op_subject s3
                        WHERE s3.faculty_id = f.id AND UPPER(s3.pt_pes) LIKE 'PT%%'
                    ) THEN 'PT' ELSE 'PES' END
                ) AS pt_pes
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
            {'id': r[0], 'name': r[1], 'orduak': round(float(r[2]), 2),
             'overload': round(float(r[2]), 2) > 17, 'kidergoa': r[3] or '',
             'gela': float(r[4]), 'pt_pes': r[5] or 'PES'}
            for r in cr.fetchall()
        ]

    def _perfilazio_pt_pes(self, faculty_id):
        """Distintivo PT/PES efectivo: override manual si existe, si no PT
        cuando algún módulo del profesor tiene PT (pt_pes LIKE 'PT%'), si no PES."""
        fac = self.browse(faculty_id)
        override = (fac.perfilazio_pt_pes or '').strip().upper()
        if override in ('PT', 'PES'):
            return override
        self.env.cr.execute("""
            SELECT 1 FROM op_subject
            WHERE faculty_id = %s AND UPPER(COALESCE(pt_pes, '')) LIKE 'PT%%' LIMIT 1
        """, (faculty_id,))
        return 'PT' if self.env.cr.fetchone() else 'PES'

    @api.model
    def toggle_perfilazio_pt_pes(self, faculty_id):
        """Alterna manualmente el distintivo PT↔PES y lo persiste."""
        current = self._perfilazio_pt_pes(faculty_id)
        new = 'PES' if current == 'PT' else 'PT'
        self.browse(faculty_id).perfilazio_pt_pes = new
        return new

    @api.model
    def get_perfilazio_taldeak_laburpena(self, dept_id):
        """Por cada taldea del mintegi: módulos sin asignar / total."""
        self.env.cr.execute("""
            SELECT b.code,
                   COUNT(s.id) AS total,
                   COUNT(s.id) FILTER (WHERE s.faculty_id IS NULL) AS pending
            FROM op_batch b
            JOIN op_course c ON c.id = b.course_id
            LEFT JOIN op_subject s ON s.batch_id = b.id
            WHERE c.department_id = %s
            GROUP BY b.code
            HAVING COUNT(s.id) > 0
            ORDER BY b.code
        """, (dept_id,))
        return [{'code': r[0], 'total': int(r[1]), 'pending': int(r[2])}
                for r in self.env.cr.fetchall()]

    @api.model
    def get_perfilazio_mintegi_karguak(self, dept_id):
        """Karguak con una línea en 'Perfilazio Irakasleak' (op.kargu.mintegi)
        para este mintegi. Por cada kargu: 'total' = horas asignadas a este
        mintegi (suma de sus líneas del dept); 'pending' (esleitzeke) = horas
        aún sin repartir a profesores (total − horas en op.perfilazio.kargu)."""
        self.env.cr.execute("""
            SELECT k.code, k.name,
                   COALESCE(SUM(km.orduak), 0) AS total_mintegi,
                   COALESCE((SELECT SUM(pk.orduak)
                             FROM op_perfilazio_kargu pk
                             JOIN op_department_op_faculty_rel dfr
                                  ON dfr.op_faculty_id = pk.faculty_id
                             WHERE pk.kargu_id = k.id
                               AND dfr.op_department_id = %s), 0) AS esleituak
            FROM op_kargu_mintegi km
            JOIN op_kargu k ON k.id = km.kargu_id
            WHERE km.department_id = %s
            GROUP BY k.id, k.code, k.name
            ORDER BY k.code
        """, (dept_id, dept_id))
        rows = []
        for r in self.env.cr.fetchall():
            total = round(float(r[2] or 0), 2)
            esleituak = float(r[3] or 0)
            rows.append({
                'code': r[0] or r[1] or '',
                'total': total,
                # 'esleitzeke' = horas aún sin repartir a profesores; nunca
                # negativo (un kargu sobre-asignado muestra 0 por asignar).
                'pending': round(max(total - esleituak, 0.0), 2),
            })
        return rows

    @api.model
    def get_perfilazio_eleanitza_laburpena(self, dept_id):
        """Horas de los módulos copia ELEANITZA (code 'HE_…') y DESDOBLE
        ('DESDO_…') del mintegi (taldea→zikloa→dept). 'total' (ordu guztiak) =
        suma de rpt_reala de esas copias; 'pending' (esleitzeke) = suma de
        rpt_reala de las que aún no tienen profesor asignado."""
        self.env.cr.execute(r"""
            SELECT
                CASE WHEN s.code ~* '^HE_' THEN 'eleanitza' ELSE 'desdoblea' END AS mota,
                COALESCE(SUM(s.rpt_reala), 0) AS total,
                COALESCE(SUM(s.rpt_reala) FILTER (WHERE s.faculty_id IS NULL), 0) AS pending
            FROM op_subject s
            JOIN op_batch b ON b.id = s.batch_id
            JOIN op_course c ON c.id = b.course_id
            WHERE c.department_id = %s
              AND s.active = true
              AND (s.code ~* '^HE_' OR s.code ~* '^DESDO_')
            GROUP BY mota
        """, (dept_id,))
        res = {'eleanitza': {'total': 0.0, 'pending': 0.0},
               'desdoblea': {'total': 0.0, 'pending': 0.0}}
        for r in self.env.cr.fetchall():
            res[r[0]] = {'total': round(float(r[1]), 2),
                         'pending': round(float(r[2]), 2)}
        return res

    @api.model
    def get_perfilazio_plazak_laburpena(self, dept_id):
        """Por distintivo PT/PES de los profesores del mintegi, desglosa sus
        horas en lektiboak (módulos normales) y ez lektiboak (módulos copia
        HE_/DESDO_ + karguak). lekt+ez_lekt = total que se convierte a plazas."""
        fac_ids = self._perfilazio_dept_faculty_ids(dept_id)
        res = {'PT': {'lekt': 0.0, 'ez_lekt': 0.0},
               'PES': {'lekt': 0.0, 'ez_lekt': 0.0}}
        if not fac_ids:
            return res
        cr = self.env.cr
        cr.execute(r"""
            SELECT faculty_id,
                   COALESCE(SUM(rpt_reala) FILTER (WHERE code !~* '^(HE_|DESDO_)'), 0),
                   COALESCE(SUM(rpt_reala) FILTER (WHERE code ~* '^(HE_|DESDO_)'), 0)
            FROM op_subject WHERE faculty_id = ANY(%s) GROUP BY faculty_id
        """, (fac_ids,))
        mod = {r[0]: (float(r[1]), float(r[2])) for r in cr.fetchall()}
        cr.execute("""
            SELECT faculty_id, COALESCE(SUM(orduak), 0)
            FROM op_perfilazio_kargu WHERE faculty_id = ANY(%s) GROUP BY faculty_id
        """, (fac_ids,))
        karg = {r[0]: float(r[1]) for r in cr.fetchall()}
        for fid in fac_ids:
            lekt, ez_mod = mod.get(fid, (0.0, 0.0))
            cat = 'PT' if self._perfilazio_pt_pes(fid) == 'PT' else 'PES'
            res[cat]['lekt'] += lekt
            res[cat]['ez_lekt'] += ez_mod + karg.get(fid, 0.0)
        for c in res:
            res[c]['lekt'] = round(res[c]['lekt'], 2)
            res[c]['ez_lekt'] = round(res[c]['ez_lekt'], 2)
        return res

    # ── Versiones de perfilación por mintegi (snapshots) ─────────────
    def _perfilazio_dept_faculty_ids(self, dept_id):
        """Profesores del mintegi (mismos que el panel Perfilazioak)."""
        self.env.cr.execute("""
            SELECT f.id FROM op_faculty f
            JOIN op_department_op_faculty_rel rel ON rel.op_faculty_id = f.id
            WHERE rel.op_department_id = %s AND f.active = true
              AND (f.kidergoa = 'funtzionarioa' OR f.kidergoa = 'impersonala')
        """, (dept_id,))
        return [r[0] for r in self.env.cr.fetchall()]

    def _perfilazio_dept_subject_ids(self, dept_id):
        """Módulos de los zikloak del mintegi (taldea → zikloa → departamentua)."""
        self.env.cr.execute("""
            SELECT s.id FROM op_subject s
            JOIN op_batch b ON b.id = s.batch_id
            JOIN op_course c ON c.id = b.course_id
            WHERE c.department_id = %s
        """, (dept_id,))
        return [r[0] for r in self.env.cr.fetchall()]

    def _perfilazio_snapshot(self, dept_id):
        """Captura el estado de perfilación del mintegi: módulo→profesor,
        horas de karguak y distintivo PT/PES (override) de sus profesores."""
        fac_ids = self._perfilazio_dept_faculty_ids(dept_id)
        sub_ids = self._perfilazio_dept_subject_ids(dept_id)
        modules = {
            str(s.id): (s.faculty_id.id or None)
            for s in self.env['op.subject'].browse(sub_ids)
        }
        karguak = [
            {'faculty_id': pk.faculty_id.id, 'kargu_id': pk.kargu_id.id,
             'orduak': pk.orduak}
            for pk in self.env['op.perfilazio.kargu'].search(
                [('faculty_id', 'in', fac_ids)])
        ]
        pt_pes = {
            str(f.id): (f.perfilazio_pt_pes or None)
            for f in self.browse(fac_ids)
        }
        return {'modules': modules, 'karguak': karguak, 'pt_pes': pt_pes}

    # Nº máximo de autoguardados que se conservan por mintegi (los más
    # antiguos se purgan). Las versiones manuales no tienen límite.
    PERFILAZIO_AUTO_KEEP = 5

    @api.model
    def save_perfilazio_bertsioa(self, dept_id, name, is_auto=False):
        Bertsioa = self.env['op.perfilazio.bertsioa']
        v = Bertsioa.create({
            'name': name or _('Bertsioa'),
            'department_id': dept_id,
            'is_auto': is_auto,
            'data': self._perfilazio_snapshot(dept_id),
        })
        if is_auto:
            autos = Bertsioa.search(
                [('department_id', '=', dept_id), ('is_auto', '=', True)],
                order='create_date desc')
            if len(autos) > self.PERFILAZIO_AUTO_KEEP:
                autos[self.PERFILAZIO_AUTO_KEEP:].unlink()
        return {'id': v.id, 'name': v.name, 'is_auto': v.is_auto,
                'create_date': fields.Datetime.to_string(v.create_date)}

    @api.model
    def get_perfilazio_bertsioak(self, dept_id):
        vs = self.env['op.perfilazio.bertsioa'].search(
            [('department_id', '=', dept_id)])
        result = []
        for v in vs:
            data = v.data or {}
            n_mod = sum(1 for fid in (data.get('modules') or {}).values() if fid)
            n_kargu = len(data.get('karguak') or [])
            result.append({
                'id': v.id, 'name': v.name, 'is_auto': v.is_auto,
                'oharra': v.oharra or '',
                'create_date': fields.Datetime.to_string(v.create_date),
                'n_mod': n_mod, 'n_kargu': n_kargu,
            })
        return result

    def _apply_perfilazio_snapshot(self, dept_id, data):
        skipped = {'modules': 0, 'karguak': 0, 'faculty': 0}
        Subject = self.env['op.subject']
        for sid, fid in (data.get('modules') or {}).items():
            s = Subject.browse(int(sid))
            if not s.exists():
                skipped['modules'] += 1
                continue
            s.faculty_id = fid or False
        # karguak: borrar los de los profesores del mintegi y recrear
        fac_ids = self._perfilazio_dept_faculty_ids(dept_id)
        PK = self.env['op.perfilazio.kargu']
        PK.search([('faculty_id', 'in', fac_ids)]).unlink()
        for k in (data.get('karguak') or []):
            f = self.browse(k.get('faculty_id'))
            kg = self.env['op.kargu'].browse(k.get('kargu_id'))
            if not f.exists() or not kg.exists():
                skipped['karguak'] += 1
                continue
            PK.create({'faculty_id': f.id, 'kargu_id': kg.id,
                       'orduak': k.get('orduak') or 0})
        for fid, val in (data.get('pt_pes') or {}).items():
            f = self.browse(int(fid))
            if not f.exists():
                skipped['faculty'] += 1
                continue
            f.perfilazio_pt_pes = val or False
        self.env.flush_all()
        return skipped

    @api.model
    def load_perfilazio_bertsioa(self, version_id):
        v = self.env['op.perfilazio.bertsioa'].browse(version_id)
        if not v.exists():
            raise UserError(_('Bertsioa ez da existitzen.'))
        dept_id = v.department_id.id
        # 1) Autoguardar el estado actual antes de sobrescribir
        self.save_perfilazio_bertsioa(
            dept_id,
            _('Auto - %s') % fields.Datetime.to_string(fields.Datetime.now()),
            is_auto=True)
        # 2) Aplicar el snapshot
        skipped = self._apply_perfilazio_snapshot(dept_id, v.data or {})
        return {'ok': True, 'skipped': skipped}

    @api.model
    def delete_perfilazio_bertsioa(self, version_id):
        self.env['op.perfilazio.bertsioa'].browse(version_id).unlink()
        return True

    # ── Export / Import portable (indexado por códigos, no por IDs) ───
    # Clave portable de un profesor: email si lo tiene; si no (impersonalak
    # tipo INFO_X1, sin email), 'name:<izena>'. Así sobrevive entre BDs/años.
    def _faculty_portable_key(self, faculty):
        if not faculty or not faculty.exists():
            return None
        email = faculty.partner_id.email
        if email:
            return email
        name = faculty.partner_id.name or ''
        return ('name:' + name) if name else None

    def _faculty_by_portable_key(self, key):
        if not key:
            return None
        if key.startswith('name:'):
            f = self.search([('partner_id.name', '=', key[5:])], limit=1)
        else:
            f = self.search([('partner_id.email', '=', key)], limit=1)
        return f.id if f else None

    def _perfilazio_portable_from_data(self, data):
        """Convierte un snapshot por IDs a formato portable: subject.code,
        clave de profesor (email o name:) y kargu.code (estables entre BDs)."""
        Subject = self.env['op.subject']
        modules = {}
        for sid, fid in (data.get('modules') or {}).items():
            s = Subject.browse(int(sid))
            if not s.exists() or not s.code:
                continue
            modules[s.code] = self._faculty_portable_key(self.browse(fid)) if fid else None
        karguak = []
        for k in (data.get('karguak') or []):
            key = self._faculty_portable_key(self.browse(k.get('faculty_id')))
            kg = self.env['op.kargu'].browse(k.get('kargu_id'))
            if not key or not kg.exists() or not kg.code:
                continue
            karguak.append({'faculty': key, 'kargu': kg.code,
                            'orduak': k.get('orduak') or 0})
        pt_pes = {}
        for fid, val in (data.get('pt_pes') or {}).items():
            key = self._faculty_portable_key(self.browse(int(fid)))
            if key:
                pt_pes[key] = val or None
        return {'modules': modules, 'karguak': karguak, 'pt_pes': pt_pes}

    def _perfilazio_data_from_portable(self, portable):
        """Resuelve el formato portable (códigos) a un snapshot por IDs de la
        BD actual. Devuelve (data, missing) con los elementos no resueltos."""
        missing = {'modules': 0, 'karguak': 0, 'faculty': 0}
        Subject = self.env['op.subject']
        modules = {}
        for code, key in (portable.get('modules') or {}).items():
            s = Subject.search([('code', '=', code)], limit=1)
            if not s:
                missing['modules'] += 1
                continue
            fid = self._faculty_by_portable_key(key) if key else None
            if key and not fid:
                missing['faculty'] += 1
            modules[str(s.id)] = fid
        karguak = []
        for k in (portable.get('karguak') or []):
            fid = self._faculty_by_portable_key(k.get('faculty'))
            kg = self.env['op.kargu'].search([('code', '=', k.get('kargu'))], limit=1)
            if not fid or not kg:
                missing['karguak'] += 1
                continue
            karguak.append({'faculty_id': fid, 'kargu_id': kg.id,
                            'orduak': k.get('orduak') or 0})
        pt_pes = {}
        for key, val in (portable.get('pt_pes') or {}).items():
            fid = self._faculty_by_portable_key(key)
            if not fid:
                missing['faculty'] += 1
                continue
            pt_pes[str(fid)] = val or None
        return {'modules': modules, 'karguak': karguak, 'pt_pes': pt_pes}, missing

    @api.model
    def export_perfilazio_bertsioa(self, version_id):
        v = self.env['op.perfilazio.bertsioa'].browse(version_id)
        if not v.exists():
            raise UserError(_('Bertsioa ez da existitzen.'))
        portable = self._perfilazio_portable_from_data(v.data or {})
        portable.update({
            'format': 'perfilazio_bertsioa', 'fmt_version': 1,
            'department': v.department_id.code or '',
            'department_name': v.department_id.name or '',
            'name': v.name,
        })
        return portable

    def _create_impersonal_named(self, dept_id, name):
        """Crea un profesor impersonal con un nombre concreto (p.ej. INFO_X3)
        en el mintegi indicado, igual que create_perfilazio_impersonal."""
        if '_X' in name:
            prefix, num = name.rsplit('_X', 1)
            last = 'X' + num
        else:
            prefix, last = name, name
        partner = self.env['res.partner'].create({'name': name})
        return self.env['op.faculty'].create({
            'partner_id': partner.id,
            'first_name': prefix or name,
            'last_name': last,
            'birth_date': '1970-01-01',
            'gender': 'male',
            'kidergoa': 'impersonala',
            'allowed_department_ids': [(6, 0, [dept_id])],
        })

    def _ensure_portable_impersonals(self, portable, dept_id):
        """Crea los impersonalak (claves 'name:…') del fichero que no existan,
        para que sus módulos/karguak se puedan restaurar. Devuelve cuántos creó."""
        keys = set()
        for v in (portable.get('modules') or {}).values():
            if v:
                keys.add(v)
        for k in (portable.get('karguak') or []):
            if k.get('faculty'):
                keys.add(k['faculty'])
        keys.update((portable.get('pt_pes') or {}).keys())
        created = 0
        for key in keys:
            if not key or not key.startswith('name:'):
                continue
            if self._faculty_by_portable_key(key):
                continue
            self._create_impersonal_named(dept_id, key[5:])
            created += 1
        if created:
            self.env.flush_all()
        return created

    @api.model
    def import_perfilazio_bertsioa(self, dept_id, portable, name=None):
        if not isinstance(portable, dict) or portable.get('format') != 'perfilazio_bertsioa':
            raise UserError(_('Fitxategi baliogabea: ez da perfilazio-bertsio bat.'))
        dept = self.env['op.department'].search(
            [('code', '=', portable.get('department'))], limit=1)
        target_dept = dept.id if dept else dept_id
        # Crear los impersonalak que falten antes de resolver (así no se pierden)
        created = self._ensure_portable_impersonals(portable, target_dept)
        data, missing = self._perfilazio_data_from_portable(portable)
        v = self.env['op.perfilazio.bertsioa'].create({
            'name': name or portable.get('name') or _('Inportatua'),
            'department_id': target_dept,
            'is_auto': False,
            'oharra': _('Inportatua fitxategitik'),
            'data': data,
        })
        return {'id': v.id, 'name': v.name,
                'department': (dept.code if dept else ''),
                'missing': missing, 'created_impersonal': created}

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
            SELECT s.code, s.name, s.rpt_reala, b.name AS batch_name,
                   s.kurtsoa, s.pt_pes, s.orduak, s.gela_orduak,
                   s.aste_banaketa, s.orduak_zorretan, s.pl
            FROM op_subject s
            LEFT JOIN op_batch b ON b.id = s.batch_id
            WHERE s.faculty_id = %s
            ORDER BY b.name, s.code
        """, (faculty_id,))
        return [
            {
                'code': r[0] or '', 'name': r[1] or '',
                # 'rpt_total' gakoak rpt_reala balioa darama (Laburpenak RPT reala erakusten du)
                'rpt_total': float(r[2] or 0), 'batch': r[3] or '',
                'kurtsoa': r[4] or '', 'pt_pes': r[5] or '',
                'orduak': float(r[6] or 0),
                # Módulos desdoble (DESDO_): la columna Gela = RPT (rpt_reala),
                # no las horas de gela del módulo completo (p.ej. DESDO_ de 2h
                # RPT muestra Gela 2h, no las 5h del módulo original).
                'gela_orduak': (float(r[2] or 0)
                                if (r[0] or '').upper().startswith('DESDO_')
                                else float(r[7] or 0)),
                'aste_banaketa': r[8] or '', 'orduak_zorretan': float(r[9] or 0),
                'pl': (r[10] or '').replace('_', '/'),
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
        # Asegurar que las escrituras ORM pendientes (p.ej. ordezko_esleitua_id)
        # están en BD antes de leer con SQL crudo.
        self.env['op.faculty'].flush_model(['ordezko_esleitua_id'])
        cr.execute("""
            SELECT f.id, rp.name, f.kidergoa, f.ordezko_esleitua_id
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
        for fid, name, kidergoa, ordezko_eid in faculties:
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
            seen_roles = set()

            def add_role(label, rtype):
                key = (rtype, label)
                if key not in seen_roles:
                    seen_roles.add(key)
                    roles.append({'label': label, 'type': rtype})

            for code in kargu_codes:
                up = code.upper()
                if up.startswith('MB-'):
                    add_role('Mintegiburua', 'mb')
                elif up.startswith('TUTO_'):
                    suffix = code[5:].strip()
                    add_role('Taldeko tutorea' + (f' ({suffix})' if suffix else ''), 'tuto')

            # Filas: módulos (Kodea, Gela, RPT = rpt_reala). Los módulos TUTO
            # (p.ej. 1INF4_TUTO_1) también dan rol "Taldeko tutorea (taldea)".
            cr.execute("""
                SELECT s.code, s.gela_orduak, s.rpt_reala, b.code
                FROM op_subject s
                LEFT JOIN op_batch b ON b.id = s.batch_id
                WHERE s.faculty_id = %s
                ORDER BY s.code
            """, (fid,))
            rows = []
            for r in cr.fetchall():
                code = r[0] or ''
                # Módulos desdoble (DESDO_): Gela = RPT (rpt_reala), no el
                # gela_orduak del módulo completo (mismo criterio que el
                # resumen del profesor, get_perfilazio_resumen).
                gela = (float(r[2] or 0) if code.upper().startswith('DESDO_')
                        else float(r[1] or 0))
                rows.append({'code': code, 'gela': gela,
                             'rpt': float(r[2] or 0), 'is_kargu': False})
                if _modulu_is_tuto(code):
                    taldea = r[3] or code.split('_TUTO')[0]
                    add_role('Taldeko tutorea' + (f' ({taldea})' if taldea else ''), 'tuto')
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
                'ordezko_esleitua_id': ordezko_eid or False,
            })
        return result

    @api.model
    def get_perfilazio_plazak(self, dept_id):
        """Tabla de plazas (impersonalak/vacantes) del mintegi para la vista
        'PLAZAK IKUSI'. Casi todo se deriva de la perfilación; solo BAKANTEA y
        OHARRAK son editables y se guardan en op.faculty.

        Columnas: IZENA (<PT/PES>-VAC_n) · PT/PES · TALDEA (código por cuerpo) ·
        JARDUNALDI_MOTA (según total horas) · HIZKUNTZA_PERFILA (PL de módulos) ·
        PLAZAREN INFORMAZIOA (módulos+karguak con horas, TOTAL y tutor) ·
        JARDUNA (M/A según GOIZEZ/ARRATSALDEZ) · BAKANTEA · OHARRAK."""
        cr = self.env.cr
        self.env['op.faculty'].flush_model(
            ['perfilazio_pt_pes', 'plaza_bakantea', 'plaza_oharrak',
             'plaza_hizkuntza_perfila', 'plaza_jarduna'])
        cr.execute("""
            SELECT f.id, rp.name, f.plaza_bakantea, f.plaza_oharrak,
                   f.plaza_hizkuntza_perfila, f.plaza_jarduna
            FROM op_faculty f
            JOIN res_partner rp ON rp.id = f.partner_id
            JOIN op_department_op_faculty_rel rel ON rel.op_faculty_id = f.id
            WHERE rel.op_department_id = %s AND f.active = true
              AND f.kidergoa = 'impersonala'
            ORDER BY f.last_name, f.id
        """, (dept_id,))
        plazas = cr.fetchall()

        result = []
        for fid, name, bakantea, oharrak, hizk_ovr, jarduna_ovr in plazas:
            pt_pes = self._perfilazio_pt_pes(fid)

            # Módulos asignados: nombre + rpt_reala + pl + taldea (para tutor) +
            # código de ziklo y kurtsoa (para detectar grado C = ARRATSALDEZ)
            cr.execute("""
                SELECT s.name, s.code, COALESCE(s.rpt_reala, 0),
                       UPPER(COALESCE(s.pl, '')), b.code,
                       UPPER(COALESCE(c.code, '')), UPPER(COALESCE(s.kurtsoa, ''))
                FROM op_subject s
                LEFT JOIN op_batch b ON b.id = s.batch_id
                LEFT JOIN op_course c ON c.id = b.course_id
                WHERE s.faculty_id = %s
                ORDER BY s.code
            """, (fid,))
            mods = cr.fetchall()
            # Karguak asignados: código + horas
            cr.execute("""
                SELECT k.code, COALESCE(pk.orduak, 0)
                FROM op_perfilazio_kargu pk
                JOIN op_kargu k ON k.id = pk.kargu_id
                WHERE pk.faculty_id = %s
                ORDER BY k.code
            """, (fid,))
            karg = cr.fetchall()

            parts = []
            total = 0.0
            has_pl1 = False
            has_pl2 = False
            tutor_taldea = ''
            has_goiz = False
            has_arrats = False
            for mname, mcode, rpt, pl, bcode, ccode, kurtsoa in mods:
                # Mostrar el código del módulo (lleva el grupo, p.ej. 2MSS2_ZERBI)
                # en vez del nombre descriptivo.
                label = mcode or mname or ''
                parts.append("%s %sh" % (label, _fmt_h(rpt)))
                total += float(rpt or 0)
                if 'PL2' in pl:
                    has_pl2 = True
                if 'PL1' in pl:
                    has_pl1 = True
                if _modulu_is_tuto(mcode or '') and not tutor_taldea:
                    tutor_taldea = bcode or (mcode or '').split('_TUTO')[0]
                # Grado C (ziklo C_INF/C_MEK o kurtsoa 'C') = ARRATSALDEZ (tarde)
                if ccode.startswith('C_') or kurtsoa == 'C':
                    has_arrats = True
                else:
                    has_goiz = True
            for kcode, korduak in karg:
                parts.append("%s %sh" % (kcode or '', _fmt_h(korduak)))
                total += float(korduak or 0)
                if (kcode or '').upper().startswith('TUTO_') and not tutor_taldea:
                    tutor_taldea = (kcode or '')[5:].strip()

            # JARDUNA: GOIZEZ (mañana) / ARRATSALDEZ (tarde, grado C) / ambos.
            if has_goiz and has_arrats:
                jarduna = 'GOIZ eta ARRATSALDEZ'
            elif has_arrats:
                jarduna = 'ARRATSALDEZ'
            else:
                jarduna = 'GOIZEZ'

            total = round(total, 2)
            info = jarduna + ": " + (", ".join(parts) if parts else "—")
            info += ". TOTAL %sh" % _fmt_h(total)
            if tutor_taldea:
                info += " (%s Tutorea)" % tutor_taldea

            # IZENA = nombre real de la plaza impersonal (p.ej. INFO_X1).
            izena = name or ''

            # HIZKUNTZA_PERFILA (dos opciones): PL2 si hay módulos PL2/PL1_PL2,
            # si no PL1; vacío si ningún módulo tiene perfil.
            if has_pl2:
                hizkuntza = 'PL2'
            elif has_pl1:
                hizkuntza = 'PL1'
            else:
                hizkuntza = ''
            # Override manual (HIZKUNTZA_PERFILA / JARDUNA): si hay valor guardado,
            # gana al automático. El prefijo de PLAZAREN INFORMAZIOA mantiene el
            # turno calculado de los módulos.
            hizkuntza = (hizk_ovr or '').strip() or hizkuntza
            jarduna = (jarduna_ovr or '').strip() or jarduna

            result.append({
                'id': fid,
                'real_name': name or '',
                'izena': izena,
                'pt_pes': pt_pes,
                'taldea': PLAZA_TALDEA_KODEA.get(pt_pes, ''),
                'jardunaldi_mota': _jardunaldi_mota(total),
                'hizkuntza_perfila': hizkuntza,
                'plazaren_informazioa': info,
                'jarduna': jarduna,
                'bakantea': bakantea or '',
                'oharrak': oharrak or '',
            })
        return result

    @api.model
    def set_perfilazio_plaza(self, faculty_id, field, value):
        """Guarda una columna editable de la tabla de plazas
        (BAKANTEA / OHARRAK / HIZKUNTZA_PERFILA / JARDUNA)."""
        fmap = {'bakantea': 'plaza_bakantea', 'oharrak': 'plaza_oharrak',
                'hizkuntza_perfila': 'plaza_hizkuntza_perfila',
                'jarduna': 'plaza_jarduna'}
        if field not in fmap:
            return False
        self.browse(faculty_id).write({fmap[field]: value or False})
        return True

    @api.model
    def get_perfilazio_ordezkoak(self, dept_id):
        """Lista de ordezkoak (kidergoa='ordezkoa') del mintegi indicado,
        para el desplegable de asignación de plazas impersonales en
        LABURPENA_IKUSI."""
        cr = self.env.cr
        cr.execute("""
            SELECT f.id, rp.name
            FROM op_faculty f
            JOIN res_partner rp ON rp.id = f.partner_id
            JOIN op_department_op_faculty_rel rel ON rel.op_faculty_id = f.id
            WHERE rel.op_department_id = %s AND f.active = true
              AND f.kidergoa = 'ordezkoa'
            ORDER BY f.last_name, rp.name
        """, (dept_id,))
        return [{'id': r[0], 'name': r[1] or ''} for r in cr.fetchall()]

    @api.model
    def set_perfilazio_ordezko_esleitua(self, faculty_id, ordezko_id):
        """Anota qué ordezkoa cubrirá una perfilación impersonal. No mueve la
        perfilación; solo guarda la referencia. ordezko_id falsy = limpiar.
        Una plaza = un profesor: rechaza si el ordezkoa ya está asignado a
        otra plaza impersonal (devuelve False)."""
        faculty = self.env['op.faculty'].browse(faculty_id)
        if not faculty.exists() or faculty.kidergoa != 'impersonala':
            return False
        oid = int(ordezko_id) if ordezko_id else False
        if oid:
            clash = self.env['op.faculty'].search_count([
                ('ordezko_esleitua_id', '=', oid),
                ('id', '!=', faculty.id),
            ])
            if clash:
                return False
        faculty.ordezko_esleitua_id = oid
        return True

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
                rp.name AS faculty_name,
                s.rpt_reala, s.rpt_zorretan, s.emandako_orduak,
                s.pl
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
                'rpt_reala': float(r[12] or 0), 'rpt_zorretan': float(r[13] or 0),
                'emandako_orduak': float(r[14] or 0),
                'special_dept': _modulu_special_dept_code(r[1]),
                'tuto': _modulu_is_tuto(r[1]),
                'pl': (r[15] or '').replace('_', '/'),
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
                rp.name AS faculty_name,
                s.rpt_reala, s.rpt_zorretan, s.emandako_orduak,
                md.code AS mintegiko_irakaslea_code,
                s.pl
            FROM op_subject s
            LEFT JOIN op_faculty f ON f.id = s.faculty_id
            LEFT JOIN res_partner rp ON rp.id = f.partner_id
            LEFT JOIN op_department md ON md.id = s.mintegiko_irakaslea
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
                'rpt_reala': float(r[12] or 0), 'rpt_zorretan': float(r[13] or 0),
                'emandako_orduak': float(r[14] or 0),
                # Override manual (mintegiko_irakaslea) tiene prioridad sobre el
                # departamento derivado del código del módulo.
                'special_dept': r[15] or _modulu_special_dept_code(r[1]),
                'tuto': _modulu_is_tuto(r[1]),
                'pl': (r[16] or '').replace('_', '/'),
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
                    COALESCE((SELECT SUM(s.rpt_reala) FROM op_subject s WHERE s.faculty_id = %s), 0)
                    + COALESCE((SELECT SUM(pk.orduak) FROM op_perfilazio_kargu pk WHERE pk.faculty_id = %s), 0),
                    COALESCE((SELECT SUM(s.gela_orduak) FROM op_subject s WHERE s.faculty_id = %s), 0)
            """, (fid, fid, fid))
            row = cr.fetchone()
            orduak = round(float(row[0]), 2)
            result.append({'id': fid, 'orduak': orduak, 'overload': orduak > 17,
                           'gela': float(row[1]),
                           'pt_pes': self._perfilazio_pt_pes(fid)})
        return result

    @api.model
    def get_perfilazio_karguak(self, faculty_id, dept_id=None):
        cr = self.env.cr
        if dept_id:
            # Si el kargu tiene reparto por mintegi (op.kargu.mintegi), 'kargu_rpt'
            # y 'max_orduak' se calculan sobre la asignación de ESTE mintegi y las
            # horas de otros solo entre profesores del mismo mintegi. Si NO tiene
            # líneas (p.ej. TUTO_/MB- asociados por código), se usa el rpt_total
            # global y las horas de todos los demás profesores.
            cr.execute("""
                SELECT pk.id, pk.kargu_id, k.code, k.name,
                       CASE WHEN EXISTS (SELECT 1 FROM op_kargu_mintegi km
                                         WHERE km.kargu_id = k.id)
                            THEN COALESCE((SELECT SUM(km.orduak)
                                           FROM op_kargu_mintegi km
                                           WHERE km.kargu_id = k.id
                                             AND km.department_id = %(dept)s), 0)
                            ELSE COALESCE(k.rpt_total, 0)
                       END AS kargu_total,
                       pk.orduak,
                       CASE WHEN EXISTS (SELECT 1 FROM op_kargu_mintegi km
                                         WHERE km.kargu_id = k.id)
                            THEN COALESCE((
                                     SELECT SUM(pk2.orduak)
                                     FROM op_perfilazio_kargu pk2
                                     JOIN op_department_op_faculty_rel dfr
                                          ON dfr.op_faculty_id = pk2.faculty_id
                                     WHERE pk2.kargu_id = k.id
                                       AND dfr.op_department_id = %(dept)s
                                       AND pk2.faculty_id <> pk.faculty_id), 0)
                            ELSE COALESCE((
                                     SELECT SUM(pk2.orduak)
                                     FROM op_perfilazio_kargu pk2
                                     WHERE pk2.kargu_id = k.id
                                       AND pk2.faculty_id <> pk.faculty_id), 0)
                       END AS assigned_others
                FROM op_perfilazio_kargu pk
                JOIN op_kargu k ON k.id = pk.kargu_id
                WHERE pk.faculty_id = %(fac)s
                ORDER BY k.name
            """, {'dept': dept_id, 'fac': faculty_id})
        else:
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
             'max_orduak': max(float(r[4] or 0) - float(r[6] or 0), 0.0),
             'allow_zero': _kargu_allows_zero(r[2]),
             'allow_decimal': _kargu_allows_decimal(r[2])}
            for r in cr.fetchall()
        ]

    @api.model
    def get_all_karguak(self, faculty_id=None, dept_id=None):
        cr = self.env.cr
        if dept_id:
            # Karguak ofrecidos en la perfilación de ESTE mintegi, de dos fuentes:
            #  (1) Karguak con línea en 'Perfilazio Irakasleak' (op.kargu.mintegi)
            #      para este mintegi (orduak>0): total y libres = asignación del
            #      mintegi (suma de sus líneas); 'others' = horas repartidas a
            #      OTROS profesores DEL MISMO mintegi.
            #  (2) Karguak TUTO_/MB- asociados a este mintegi POR CÓDIGO aunque no
            #      tengan línea: TUTO_<taldea> (la taldea pertenece al ciclo del
            #      mintegi) y MB-<dept> (sufijo = código de mintegi o, si el código
            #      está mal escrito, vía el mintegi de quien lo ostenta). Total y
            #      libres = rpt_total global del kargu (estos karguak son de un
            #      único mintegi). Se excluyen los que ya tengan línea de ESTE
            #      mintegi para no duplicar con (1).
            cr.execute(r"""
                SELECT id, code, name, total, others FROM (
                    SELECT k.id, k.code, k.name,
                           COALESCE(SUM(km.orduak), 0) AS total,
                           COALESCE((
                               SELECT SUM(pk.orduak)
                               FROM op_perfilazio_kargu pk
                               JOIN op_department_op_faculty_rel dfr
                                    ON dfr.op_faculty_id = pk.faculty_id
                               WHERE pk.kargu_id = k.id
                                 AND dfr.op_department_id = %(dept)s
                                 AND pk.faculty_id <> %(fac)s
                           ), 0) AS others
                    FROM op_kargu_mintegi km
                    JOIN op_kargu k ON k.id = km.kargu_id
                    WHERE km.department_id = %(dept)s
                    GROUP BY k.id, k.code, k.name
                    HAVING COALESCE(SUM(km.orduak), 0) > 0

                    UNION ALL

                    SELECT k.id, k.code, k.name,
                           COALESCE(k.rpt_total, 0) AS total,
                           COALESCE((
                               SELECT SUM(pk.orduak) FROM op_perfilazio_kargu pk
                               WHERE pk.kargu_id = k.id AND pk.faculty_id <> %(fac)s
                           ), 0) AS others
                    FROM op_kargu k
                    WHERE NOT EXISTS (
                              SELECT 1 FROM op_kargu_mintegi km2
                              WHERE km2.kargu_id = k.id AND km2.department_id = %(dept)s)
                      AND (
                          (k.code LIKE 'TUTO\_%%' AND (
                              EXISTS (
                                  SELECT 1 FROM op_batch b
                                  JOIN op_course c ON c.id = b.course_id
                                  WHERE b.code = substring(k.code FROM 6)
                                    AND c.department_id = %(dept)s)
                              -- Si el código no corresponde a ninguna taldea
                              -- (p.ej. TUTO_FG_ESP), se asocia al mintegi de
                              -- quien ostenta el cargo.
                              OR (NOT EXISTS (
                                      SELECT 1 FROM op_batch b
                                      WHERE b.code = substring(k.code FROM 6))
                                  AND EXISTS (
                                      SELECT 1 FROM op_faculty_kargu_rel fk
                                      JOIN op_department_op_faculty_rel r
                                           ON r.op_faculty_id = fk.faculty_id
                                      WHERE fk.kargu_id = k.id
                                        AND r.op_department_id = %(dept)s))))
                          OR
                          (k.code LIKE 'MB-%%' AND (
                              EXISTS (SELECT 1 FROM op_department d
                                      WHERE d.id = %(dept)s
                                        AND d.code = substring(k.code FROM 4))
                              OR EXISTS (
                                  SELECT 1 FROM op_faculty_kargu_rel fk
                                  JOIN op_department_op_faculty_rel r
                                       ON r.op_faculty_id = fk.faculty_id
                                  WHERE fk.kargu_id = k.id
                                    AND r.op_department_id = %(dept)s)))
                      )
                ) q
                ORDER BY name
            """, {'dept': dept_id, 'fac': faculty_id or 0})
            return [
                {'id': r[0], 'code': r[1] or '', 'name': r[2] or '',
                 'rpt_total': round(float(r[3] or 0), 2),
                 'assigned': round(float(r[4] or 0), 2),
                 'remaining': round(max(float(r[3] or 0) - float(r[4] or 0), 0.0), 2),
                 'allow_zero': _kargu_allows_zero(r[1]),
                 'allow_decimal': _kargu_allows_decimal(r[1])}
                for r in cr.fetchall()
            ]
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
             'remaining': max(float(r[3] or 0) - float(r[5] or 0), 0.0),
             'allow_zero': _kargu_allows_zero(r[1]),
             'allow_decimal': _kargu_allows_decimal(r[1])}
            for r in cr.fetchall()
        ]

    @api.model
    def upsert_perfilazio_kargu(self, faculty_id, kargu_id, orduak, dept_id=None):
        orduak = float(orduak or 0)
        kargu = self.env['op.kargu'].browse(kargu_id)
        cr = self.env.cr
        if dept_id and kargu.perfilazio_ids:
            # Kargu con reparto por mintegi: tope = horas asignadas a este mintegi
            # (líneas op.kargu.mintegi del dept) − horas ya repartidas a OTROS
            # profesores del mismo mintegi.
            cr.execute("""
                SELECT COALESCE(SUM(km.orduak), 0) FROM op_kargu_mintegi km
                WHERE km.kargu_id = %s AND km.department_id = %s
            """, (kargu_id, dept_id))
            kargu_total = float(cr.fetchone()[0])
            cr.execute("""
                SELECT COALESCE(SUM(pk.orduak), 0)
                FROM op_perfilazio_kargu pk
                JOIN op_department_op_faculty_rel dfr
                     ON dfr.op_faculty_id = pk.faculty_id
                WHERE pk.kargu_id = %s AND dfr.op_department_id = %s
                  AND pk.faculty_id <> %s
            """, (kargu_id, dept_id, faculty_id))
            assigned_others = float(cr.fetchone()[0])
        else:
            cr.execute("""
                SELECT COALESCE(SUM(orduak), 0) FROM op_perfilazio_kargu
                WHERE kargu_id = %s AND faculty_id <> %s
            """, (kargu_id, faculty_id))
            assigned_others = float(cr.fetchone()[0])
            kargu_total = float(kargu.rpt_total or 0)
        max_allowed = kargu_total - assigned_others
        if orduak > max_allowed:
            raise UserError(_(
                "'%(kargu)s' karguak %(libre)s ordu libre baino ez ditu "
                "(guztira: %(total)sh, beste irakasleek esleituta: %(besteak)sh).",
                kargu=kargu.code, libre=round(max_allowed, 2),
                total=round(kargu_total, 2), besteak=round(assigned_others, 2),
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
        # Volcar el write/create pendiente a BD antes del SQL crudo, si no
        # el SUM(pk.orduak) leería el valor antiguo y el overload (>17) sería erróneo.
        self.env['op.perfilazio.kargu'].flush_model(['orduak', 'faculty_id', 'kargu_id'])
        cr.execute("""
            SELECT
                COALESCE((SELECT SUM(s.rpt_reala) FROM op_subject s WHERE s.faculty_id = %s), 0)
                + COALESCE((SELECT SUM(pk.orduak) FROM op_perfilazio_kargu pk WHERE pk.faculty_id = %s), 0)
        """, (faculty_id, faculty_id))
        orduak_total = round(float(cr.fetchone()[0]), 2)
        return {'orduak': orduak_total, 'overload': orduak_total > 17}

    @api.model
    def delete_perfilazio_kargu(self, line_id):
        line = self.env['op.perfilazio.kargu'].browse(line_id)
        faculty_id = line.faculty_id.id
        line.unlink()
        cr = self.env.cr
        cr.execute("""
            SELECT
                COALESCE((SELECT SUM(s.rpt_reala) FROM op_subject s WHERE s.faculty_id = %s), 0)
                + COALESCE((SELECT SUM(pk.orduak) FROM op_perfilazio_kargu pk WHERE pk.faculty_id = %s), 0)
        """, (faculty_id, faculty_id))
        orduak_total = round(float(cr.fetchone()[0]), 2)
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
