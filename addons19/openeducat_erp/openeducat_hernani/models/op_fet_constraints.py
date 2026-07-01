# -*- coding: utf-8 -*-
# Ordutegi murrizpenak — datos que FET necesita y NO salen de perfilazioak.
# Cada apartado del menú "Ordutegi murrizpenak" es uno de estos modelos.
from odoo import api, fields, models

# Días lectivos (Lun-Vie). La clave se mapea al <Day> del .fet en euskera/castellano
# en el generador; aquí etiquetamos en euskera para la UI.
FET_WEEKDAYS = [
    ('monday', 'Astelehena'),
    ('tuesday', 'Asteartea'),
    ('wednesday', 'Asteazkena'),
    ('thursday', 'Osteguna'),
    ('friday', 'Ostirala'),
]


class OpFetIrakasleKop(models.Model):
    """Opciones del desplegable "Irakasle kop." de un desdoble.

    Es un Many2one (no Selection) para poder FILTRAR las opciones por fila con
    un dominio (`value <= irakasle_max`): un Selection estático no permite
    recortar sus opciones por registro. Registros 2..8 sembrados en
    data/fet_irakasle_kop_data.xml.
    """
    _name = 'op.fet.irakasle.kop'
    _description = 'FET desdoble: irakasle kopurua (aukera)'
    _order = 'value'

    value = fields.Integer('Balioa', required=True, index=True)
    name = fields.Char('Izena', required=True)

    _sql_constraints = [
        ('uniq_value', 'unique(value)', 'Balio bakoitza behin bakarrik.'),
    ]


class OpFetTeacherUnavailability(models.Model):
    """Apartado #1: Irakasleen erabilgarritasuna.

    Una línea = una franja (día × Aste Saioa) en la que el profesor NO puede
    dar clase. FET: ConstraintTeacherNotAvailableTimes.
    """
    _name = 'op.fet.teacher.unavailability'
    _description = 'FET: Irakaslearen ez-erabilgarritasuna'
    _order = 'faculty_id, day, timing_id'

    faculty_id = fields.Many2one(
        'op.faculty', string='Irakaslea', required=True, index=True,
        ondelete='cascade')
    day = fields.Selection(
        FET_WEEKDAYS, string='Eguna', required=True, index=True)
    timing_id = fields.Many2one(
        'op.timing', string='Aste Saioa', required=True, ondelete='cascade')
    reason = fields.Char('Arrazoia')

    _sql_constraints = [
        ('uniq_teacher_slot',
         'unique(faculty_id, day, timing_id)',
         'Irakasle horrek franja hori behin bakarrik izan dezake.'),
    ]

    @api.depends('faculty_id', 'day', 'timing_id')
    def _compute_display_name(self):
        days = dict(FET_WEEKDAYS)
        for rec in self:
            rec.display_name = '%s · %s · %s' % (
                rec.faculty_id.name or '',
                days.get(rec.day, ''),
                rec.timing_id.name or '')

    # ------------------------------------------------------------------ #
    # RPC para el componente OWL "Irakasleen erabilgarritasuna"
    # (rejilla 5 días × N Aste Saioak + lista de profes por mintegi)
    # ------------------------------------------------------------------ #
    @api.model
    def get_mintegiak(self):
        cr = self.env.cr
        cr.execute("""
            SELECT DISTINCT d.id, d.name, d.code
            FROM op_department d
            JOIN op_department_op_faculty_rel rel ON rel.op_department_id = d.id
            JOIN op_faculty f ON f.id = rel.op_faculty_id AND f.active = true
            ORDER BY d.name
        """)
        return [{'id': r[0], 'name': r[1], 'code': r[2] or ''}
                for r in cr.fetchall()]

    @api.model
    def get_irakasleak(self, dept_id):
        """Mismos profes que el panel de Perfilazioak: funtzionarioak +
        impertsonalak (X1, X2...) del mintegi; impersonalak al final."""
        cr = self.env.cr
        cr.execute("""
            SELECT f.id, rp.name, f.kidergoa
            FROM op_faculty f
            JOIN res_partner rp ON rp.id = f.partner_id
            JOIN op_department_op_faculty_rel rel
                ON rel.op_faculty_id = f.id AND rel.op_department_id = %s
            WHERE f.active = true
              AND (f.kidergoa = 'funtzionarioa' OR f.kidergoa = 'impersonala')
            ORDER BY
                CASE WHEN f.kidergoa = 'impersonala' THEN 1 ELSE 0 END,
                f.last_name
        """, (dept_id,))
        return [{'id': r[0], 'name': r[1], 'kidergoa': r[2] or ''}
                for r in cr.fetchall()]

    @api.model
    def get_grid(self):
        """Ejes de la rejilla: días lectivos + Aste Saioak (op.timing)."""
        timings = self.env['op.timing'].search([], order='sequence')
        return {
            'days': [{'key': k, 'label': lbl} for k, lbl in FET_WEEKDAYS],
            'timings': [{'id': t.id, 'name': t.name} for t in timings],
        }

    @api.model
    def get_unavailability(self, faculty_id):
        """Franjas marcadas (NO disponible) del profesor: ['day|timing_id', ...]."""
        if not faculty_id:
            return []
        recs = self.search([('faculty_id', '=', faculty_id)])
        return ['%s|%s' % (r.day, r.timing_id.id) for r in recs]

    @api.model
    def toggle_slot(self, faculty_id, day, timing_id):
        """Marca/desmarca una franja. Devuelve True si queda NO disponible."""
        existing = self.search([
            ('faculty_id', '=', faculty_id),
            ('day', '=', day),
            ('timing_id', '=', timing_id),
        ], limit=1)
        if existing:
            existing.unlink()
            return False
        self.create({
            'faculty_id': faculty_id, 'day': day, 'timing_id': timing_id,
        })
        return True


class OpFetRoomUnavailability(models.Model):
    """Apartado #3: Gelen erabilgarritasuna.

    Una línea = una franja (día × Aste Saioa) en la que el aula NO está
    disponible (ocupada por otro uso). FET: ConstraintRoomNotAvailableTimes.
    """
    _name = 'op.fet.room.unavailability'
    _description = 'FET: Gelaren ez-erabilgarritasuna'
    _order = 'classroom_id, day, timing_id'

    classroom_id = fields.Many2one(
        'op.classroom', string='Gela', required=True, index=True,
        ondelete='cascade')
    day = fields.Selection(
        FET_WEEKDAYS, string='Eguna', required=True, index=True)
    timing_id = fields.Many2one(
        'op.timing', string='Aste Saioa', required=True, ondelete='cascade')
    reason = fields.Char('Arrazoia')

    _sql_constraints = [
        ('uniq_room_slot',
         'unique(classroom_id, day, timing_id)',
         'Gela horrek franja hori behin bakarrik izan dezake.'),
    ]

    @api.depends('classroom_id', 'day', 'timing_id')
    def _compute_display_name(self):
        days = dict(FET_WEEKDAYS)
        for rec in self:
            rec.display_name = '%s · %s · %s' % (
                rec.classroom_id.name or '',
                days.get(rec.day, ''),
                rec.timing_id.name or '')

    # ------------------------------------------------------------------ #
    # RPC para el componente OWL "Gelen erabilgarritasuna"
    # (rejilla 5 días × N Aste Saioak + lista de gelas por solairua)
    # ------------------------------------------------------------------ #
    @api.model
    def get_solairuak(self):
        """Plantas que tienen aulas docentes, con su etiqueta."""
        labels = dict(
            self.env['op.classroom']._fields['solairua'].selection)
        cr = self.env.cr
        cr.execute("""
            SELECT DISTINCT solairua
            FROM op_classroom
            WHERE active = true AND irakasgela = true AND solairua IS NOT NULL
            ORDER BY solairua
        """)
        return [{'key': r[0], 'label': labels.get(r[0], r[0])}
                for r in cr.fetchall()]

    @api.model
    def get_gelak(self, solairua=None):
        """Aulas docentes, opcionalmente filtradas por planta."""
        domain = [('active', '=', True), ('irakasgela', '=', True)]
        if solairua:
            domain.append(('solairua', '=', solairua))
        rooms = self.env['op.classroom'].search(domain, order='code, name')
        return [{'id': r.id, 'name': r.name, 'code': r.code or '',
                 'gela_mota': r.gela_mota or ''} for r in rooms]

    @api.model
    def get_grid(self):
        """Ejes de la rejilla: días lectivos + Aste Saioak (op.timing)."""
        timings = self.env['op.timing'].search([], order='sequence')
        return {
            'days': [{'key': k, 'label': lbl} for k, lbl in FET_WEEKDAYS],
            'timings': [{'id': t.id, 'name': t.name} for t in timings],
        }

    @api.model
    def get_unavailability(self, classroom_id):
        """Franjas marcadas (NO disponible) del aula: ['day|timing_id', ...]."""
        if not classroom_id:
            return []
        recs = self.search([('classroom_id', '=', classroom_id)])
        return ['%s|%s' % (r.day, r.timing_id.id) for r in recs]

    @api.model
    def toggle_slot(self, classroom_id, day, timing_id):
        """Marca/desmarca una franja. Devuelve True si queda NO disponible."""
        existing = self.search([
            ('classroom_id', '=', classroom_id),
            ('day', '=', day),
            ('timing_id', '=', timing_id),
        ], limit=1)
        if existing:
            existing.unlink()
            return False
        self.create({
            'classroom_id': classroom_id, 'day': day, 'timing_id': timing_id,
        })
        return True


class OpFetFixedSession(models.Model):
    """Apartado #5: Saio finkoak.

    Una actividad (módulo de una taldea) que debe ir a una hora fija
    (día × Aste Saioa). FET: ConstraintActivityPreferredStartingTime.
    """
    _name = 'op.fet.fixed.session'
    _description = 'FET: Saio finkoa'
    _order = 'subject_id, day, timing_id'

    subject_id = fields.Many2one(
        'op.subject', string='Modulua', required=True, index=True,
        ondelete='cascade')
    batch_id = fields.Many2one(
        'op.batch', string='Taldea', related='subject_id.batch_id',
        store=True, readonly=True)
    day = fields.Selection(
        FET_WEEKDAYS, string='Eguna', required=True, index=True)
    timing_id = fields.Many2one(
        'op.timing', string='Aste Saioa', required=True, ondelete='cascade')
    note = fields.Char('Oharra')

    _sql_constraints = [
        ('uniq_fixed_slot',
         'unique(subject_id, day, timing_id)',
         'Modulu horrek franja hori behin bakarrik izan dezake.'),
    ]


class OpFetConfig(models.Model):
    """Apartado #6: Murrizpen orokorrak.

    Reglas globales de un solo registro que se aplican a todo el .fet.
    """
    _name = 'op.fet.config'
    _description = 'FET: Murrizpen orokorrak'

    name = fields.Char('Izena', default='Ordutegi murrizpen orokorrak',
                       readonly=True)
    students_no_gaps = fields.Boolean(
        'Ikasleak hutsunerik gabe', default=True,
        help='Taldeen ordutegia trinkoa: ikasleentzat tarte hutsik gabe.')
    teacher_max_gaps_day = fields.Integer(
        'Irakaslearen gehienezko hutsuneak (egunean)', default=2)
    teacher_max_hours_day = fields.Integer(
        'Gehienezko orduak egunean (irakasleko)', default=6)
    max_hours_continuously = fields.Integer(
        'Gehienezko ordu jarraituak', default=4)
    same_subject_once_per_day = fields.Boolean(
        'Modulu bera ez egunean bitan', default=True,
        help='Modulu beraren bi saio ezin dira egun berean egon.')

    @api.model
    def get_singleton(self):
        """Devuelve (creando si hace falta) el único registro de config."""
        rec = self.search([], limit=1)
        if not rec:
            rec = self.create({})
        return rec


class OpFetSimultaneity(models.Model):
    """Apartado #4: Saio simultaneoak (desdoble / eleanitza).

    Cada línea empareja un módulo origen con su copia (DESDO_/HE_) cuyas
    actividades deben ir a la MISMA hora. Mapeo al .fet:
      - desdoblea/gela_banatua  -> SameStartingTime + aulas distintas (subgrupos).
      - desdoblea/gela_bakarrean -> SameStartingTime + MISMA aula (2 irakasle).
      - eleanitza/gela_banatua  -> igual que desdoble banatua (2 aulas, 2 irak.).
      - eleanitza/gela_berean   -> SameStartingTime + MISMA aula (co-docencia:
                                   el profe de idiomas entra al aula).
    """
    _name = 'op.fet.simultaneity'
    _description = 'FET: Saio simultaneoak'
    _order = 'batch_id, subject_id'

    subject_id = fields.Many2one(
        'op.subject', string='Jatorrizko modulua', required=True,
        index=True, ondelete='cascade')
    copy_id = fields.Many2one(
        'op.subject', string='Kopia (DESDO_/HE_)', required=True,
        index=True, ondelete='cascade')
    copy_code = fields.Char(
        string='Desdoble modulua', related='copy_id.code', readonly=True)
    copy_desdoble_orduak = fields.Float(
        string='Desdoble orduak', related='copy_id.rpt_total', readonly=True,
        help='Kopiari (DESDO_) esleitutako orduak (RPT), ez jatorrizko gela '
             'orduak. Perfilazioetako "Moduluak Kopiatu" taulakoak.')
    # Jatorrizko modulua(k): DESDO_ malguetan, taldeko modulu bat baino
    # gehiago hauta daitezke (talde txikiak gela berean saioa partekatzeko).
    # HE_ moduluetan bakarra eta finkoa (jatorri kodearena). `edozein` markatuz
    # gero, desdoblea librea da (jatorririk gabe).
    jatorri_ids = fields.Many2many(
        'op.subject', 'op_fet_simult_jatorri_rel', 'simult_id', 'subject_id',
        string='Jatorrizko modulua(k)',
        domain="[('gela_orduak', '>', 0), ('da_kopia', '=', False)]",
        help='Desdoblea zein modulurekin bat datorren (SameStartingTime). '
             'Bat baino gehiago: talde txikiak gela berean partekatzen dutenean.')
    # Malgutasuna talde-moduluekin bat egiteko (jatorri zehatzik gabe).
    # Modulu ZEHARKAKOAK (transversales) = kodean ZIA/KOG/ING/FOL/EIE/EIP/IPE
    # dutenak; gainerakoak TEKNIKOAK.
    #   tekniko   → taldeko modulu TEKNIKOEKIN soilik bat egin dezake.
    #   amankomun → taldeko modulu ZEHARKAKOEKIN soilik.
    #   biak      → edonon (edozein talde-modulurekin).
    #   bat ere ez → jatorri_ids zehatzak erabiltzen dira.
    edozein_tekniko = fields.Boolean(
        'Edozein tekniko', default=False,
        help='Desdoblea taldeko modulu teknikoetako edozeinekin bat egin '
             'dezake (ez zeharkakoak).')
    edozein_amankomun = fields.Boolean(
        'Edozein amankomun', default=False,
        help='Desdoblea taldeko modulu zeharkakoetako edozeinekin bat egin '
             'dezake (kodean ZIA/KOG/ING/FOL/EIE/EIP/IPE). Biak: edonon.')
    mota = fields.Selection(
        [('desdoblea', 'Desdoblea'), ('eleanitza', 'Eleanitza')],
        string='Mota', compute='_compute_mota', store=True, index=True,
        help='Kopiaren kodetik ondorioztatzen da: HE_ → eleanitza; '
             'DESDO_ → desdoblea. Ezin da eskuz aldatu.')
    batch_id = fields.Many2one(
        'op.batch', string='Taldea', related='subject_id.batch_id',
        store=True, readonly=True)
    department_id = fields.Many2one(
        'op.department', string='Mintegia',
        related='subject_id.own_department_id', store=True, index=True,
        readonly=True)
    # Modu bakarra desdoble/eleanitza-rentzat (lehen bi eremu ziren:
    # desdoble_mota + eleanitza_mota). 'banatua' = 2 gela; 'berean' = gela
    # bakarra, 2 irakasle (desdoblean bigarren irakaslea; eleanitzan hizkuntza
    # irakaslea sartzen da).
    modua = fields.Selection(
        [('banatua', 'Banatua'),
         ('berean', 'Berean')],
        string='Modu mota', default='banatua', required=True,
        help='Gela banatuak: taldea gela banatan banatzen da, irakasle bana, '
             'aldi berean. Gela bakarra: gela bakarrean irakasle bat baino '
             'gehiago (desdoblean laguntzailea; eleanitzan hizkuntza irakaslea).')
    # Desdoble baten irakasle/gela kopurua aukeratzeko (banatua zein berean).
    # Gutxienez 2 (DESDO_ irakaslea + jatorri 1) eta gehienez DESDO_ + jatorri
    # kopurua. berean → gela bakarra, X irakasle; banatua → X gela / X irakasle.
    # Adib. DESDO_1MSS2_MUNTAIA + 3 jatorri = 4 profe: 2..4 bitartean hautatu.
    # Many2one (ez Selection) DOMINIOAK lerroz lerro moztu ahal izateko: aukerak
    # `value <= irakasle_max` bakarrik erakusten dira (desplegable-a bera mugatuta).
    irakasle_max = fields.Integer(
        string='Gehienezko irakasle', compute='_compute_irakasle_max',
        help='Desdoble honek onar dezakeen gehienezko irakasle kopurua: '
             'DESDO_ + jatorri kopurua (edozein → irekita).')
    irakasle_kop_id = fields.Many2one(
        'op.fet.irakasle.kop', string='Irakasle kop.',
        domain="[('value', '>=', 2), ('value', '<=', irakasle_max)]",
        default=lambda self: self.env['op.fet.irakasle.kop'].search(
            [('value', '=', 2)], limit=1),
        help='Desdoblean parte hartuko duten irakasle kopurua: DESDO_ '
             'irakaslea + jatorrizko moduluetako irakasleak. Gutxienez 2, '
             'gehienez DESDO_ + jatorri kopurua.')
    # Columna Modua (dinámica): expande el modu_mota. banatua → "Gela banatuak
    # (N gela / N irakasle)" con N = nº jatorri. berean → "Gela bakarra (X
    # irakasle)" con X = irakasle_kop (desdoble) o 2 (eleanitza). edozein →
    # "taldeko edozein".
    modua_azalpena = fields.Char(
        string='Modua', compute='_compute_modua_azalpena')
    enabled = fields.Boolean('Gaituta', default=True, index=True)

    _sql_constraints = [
        ('uniq_copy', 'unique(copy_id)',
         'Kopia honek lerro bat baino ezin du izan.'),
    ]

    @api.depends('copy_id', 'copy_id.code')
    def _compute_mota(self):
        # HE_ → eleanitza; DESDO_ (o cualquier otro) → desdoblea. Garantiza
        # que un DESDO_ nunca sea eleanitza y un HE_ nunca desdoblea.
        for rec in self:
            code = (rec.copy_id.code or '').upper()
            rec.mota = 'eleanitza' if code.startswith('HE_') else 'desdoblea'

    @api.depends('jatorri_ids', 'edozein_tekniko', 'edozein_amankomun', 'mota')
    def _compute_irakasle_max(self):
        # Máximo = 1 (DESDO_) + nº módulos en jatorri_ids. edozein → abierto (8).
        for rec in self:
            if rec.mota != 'desdoblea':
                rec.irakasle_max = 2
            elif rec.edozein_tekniko or rec.edozein_amankomun:
                rec.irakasle_max = 8
            else:
                rec.irakasle_max = max(len(rec.jatorri_ids) + 1, 2)

    @api.depends('modua', 'jatorri_ids', 'edozein_tekniko', 'edozein_amankomun',
                 'irakasle_kop_id', 'irakasle_max', 'mota')
    def _compute_modua_azalpena(self):
        # X = irakasle_kop_id hautatua, [2, irakasle_max]-era moztuta.
        for rec in self:
            edozein = rec.edozein_tekniko or rec.edozein_amankomun
            if rec.modua == 'berean':
                # Gela bakarra: eleanitza = 2 finko (titular + hizkuntza);
                # desdoblea = irakasle_kop hautatua.
                if rec.mota == 'eleanitza':
                    rec.modua_azalpena = 'Gela bakarra (2 irakasle)'
                else:
                    n = max(min(rec.irakasle_kop_id.value or 2, rec.irakasle_max), 2)
                    rec.modua_azalpena = 'Gela bakarra (%d irakasle)' % n
            else:  # banatua
                if edozein:
                    rec.modua_azalpena = 'Gela banatuak (taldeko edozein gela / irakasle)'
                elif rec.mota == 'eleanitza':
                    rec.modua_azalpena = 'Gela banatuak (2 gela / 2 irakasle)'
                else:
                    # desdoble: irakasle_kop, DESDO_ + jatorri kop.-era moztuta.
                    n = max(min(rec.irakasle_kop_id.value or 2, rec.irakasle_max), 2)
                    rec.modua_azalpena = 'Gela banatuak (%d gela / %d irakasle)' % (n, n)

    def generate_pairs(self):
        """Crea (idempotente) un par por cada DESDO_/HE_ con su origen.
        Solo AÑADE los que falten; conserva 'enabled'/'modua' ya editados.
        Empareja por código (origen = copia sin prefijo). 'mota' se computa
        de la copia (no se fija aquí)."""
        Subject = self.env['op.subject']
        existing = set(self.search([]).mapped('copy_id').ids)
        subjects = Subject.search([('active', '=', True)])
        by_code = {s.code: s for s in subjects}
        created = 0
        for c in subjects:
            if c.id in existing:
                continue
            if c.code.startswith('DESDO_'):
                origin_code = c.code[6:]
            elif c.code.startswith('HE_'):
                origin_code = c.code[3:]
            else:
                continue
            origin = by_code.get(origin_code)
            if not origin:
                continue
            self.create({
                'subject_id': origin.id, 'copy_id': c.id,
                'jatorri_ids': [(6, 0, [origin.id])],
            })
            created += 1
        return {
            'type': 'ir.actions.act_window',
            'name': 'Saio simultaneoak',
            'res_model': 'op.fet.simultaneity',
            'view_mode': 'tree',
            'target': 'current',
        }


class OpFetGrouping(models.Model):
    """Definición manual de un desdoble (banatu) o agrupación (bateratu).

    - bateratu: varios grupos comparten una misma aula -> el aforo total de
      las aulas debe alojar a TODOS los alumnos juntos.
    - banatu: un grupo (o varios) se reparten en varias aulas -> por cada
      línea se indica cuántos alumnos van a cada aula; si una aula supera su
      aforo, se avisa.
    """
    _name = 'op.fet.grouping'
    _description = 'FET: Desdoblea / Agrupazioa'
    _order = 'id desc'

    name = fields.Char('Izena', compute='_compute_name', store=True)
    mota = fields.Selection(
        [('bateratu', 'Bateratu (taldeak gela berean)'),
         ('banatu', 'Banatu (taldea geletan zatitu)')],
        string='Mota', required=True, default='banatu', index=True)
    batch_ids = fields.Many2many(
        'op.batch', 'op_fet_grouping_batch_rel', 'grouping_id', 'batch_id',
        string='Taldeak', required=True)
    classroom_ids = fields.Many2many(
        'op.classroom', 'op_fet_grouping_room_rel', 'grouping_id',
        'classroom_id', string='Gelak', required=True)
    department_id = fields.Many2one(
        'op.department', string='Mintegia',
        compute='_compute_department', store=True, index=True)
    enabled = fields.Boolean('Gaituta', default=True, index=True)

    line_ids = fields.One2many(
        'op.fet.grouping.line', 'grouping_id', string='Banaketa')

    student_total = fields.Integer(
        'Ikasleak guztira', compute='_compute_totals')
    capacity_total = fields.Integer(
        'Aforoa guztira', compute='_compute_totals')
    overflow = fields.Boolean('Aforoa gainditua', compute='_compute_overflow')
    overflow_msg = fields.Char(compute='_compute_overflow')

    @api.depends('batch_ids', 'classroom_ids', 'mota')
    def _compute_name(self):
        for rec in self:
            label = dict(rec._fields['mota'].selection).get(rec.mota, '')
            taldeak = ', '.join(rec.batch_ids.mapped('code')) or '—'
            rec.name = '%s: %s' % (label.split(' ')[0], taldeak)

    @api.depends('batch_ids')
    def _compute_department(self):
        for rec in self:
            depts = rec.batch_ids.mapped('course_id.department_id')
            rec.department_id = depts[:1].id if depts else False

    @api.depends('batch_ids.fet_student_count', 'classroom_ids.capacity')
    def _compute_totals(self):
        for rec in self:
            rec.student_total = sum(rec.batch_ids.mapped('fet_student_count'))
            rec.capacity_total = sum(rec.classroom_ids.mapped('capacity'))

    @api.depends('mota', 'student_total', 'capacity_total',
                 'line_ids.students', 'line_ids.classroom_id',
                 'classroom_ids.capacity')
    def _compute_overflow(self):
        for rec in self:
            over, msgs = False, []
            if rec.mota == 'bateratu':
                if rec.capacity_total and rec.student_total > rec.capacity_total:
                    over = True
                    msgs.append('Guztira %s ikasle / %s aforo' % (
                        rec.student_total, rec.capacity_total))
            else:  # banatu
                per_room = {}
                for ln in rec.line_ids:
                    if ln.classroom_id:
                        per_room.setdefault(ln.classroom_id, 0)
                        per_room[ln.classroom_id] += ln.students
                for room, n in per_room.items():
                    if room.capacity and n > room.capacity:
                        over = True
                        msgs.append('%s: %s/%s' % (room.name, n, room.capacity))
            rec.overflow = over
            rec.overflow_msg = ('Aforoa gainditua! ' + ' · '.join(msgs)
                                if over else '')


class OpFetGroupingLine(models.Model):
    """Línea de reparto (banatu): X alumnos de un grupo en un aula."""
    _name = 'op.fet.grouping.line'
    _description = 'FET: Banaketa-lerroa'

    grouping_id = fields.Many2one(
        'op.fet.grouping', required=True, ondelete='cascade')
    batch_id = fields.Many2one('op.batch', string='Taldea', required=True)
    classroom_id = fields.Many2one(
        'op.classroom', string='Gela', required=True)
    students = fields.Integer('Ikasleak', default=0)
    capacity = fields.Integer(
        'Aforoa', related='classroom_id.capacity', readonly=True)
    over_capacity = fields.Boolean(compute='_compute_over')

    @api.depends('students', 'capacity', 'grouping_id.line_ids.students',
                 'grouping_id.line_ids.classroom_id')
    def _compute_over(self):
        for ln in self:
            total_room = sum(
                o.students for o in ln.grouping_id.line_ids
                if o.classroom_id == ln.classroom_id)
            ln.over_capacity = bool(ln.capacity) and total_room > ln.capacity
