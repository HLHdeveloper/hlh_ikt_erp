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
    mota = fields.Selection(
        [('desdoblea', 'Desdoblea'), ('eleanitza', 'Eleanitza')],
        string='Mota', required=True, index=True)
    batch_id = fields.Many2one(
        'op.batch', string='Taldea', related='subject_id.batch_id',
        store=True, readonly=True)
    department_id = fields.Many2one(
        'op.department', string='Mintegia',
        related='subject_id.own_department_id', store=True, index=True,
        readonly=True)
    desdoble_mota = fields.Selection(
        [('gela_banatua', 'Gela banatua (2 gela / 2 irakasle)'),
         ('gela_bakarrean', 'Gela bakarrean (gela berean, 2 irakasle)')],
        string='Desdoble modua', default='gela_banatua',
        help='Desdoblerako soilik. Gela banatua: taldea bi geletan banatzen '
             'da, irakasle bana, aldi berean. Gela bakarrean: gela berean, '
             'bi irakasle.')
    eleanitza_mota = fields.Selection(
        [('gela_banatua', 'Aula banatua (2 gela / 2 irakasle)'),
         ('gela_berean', 'Gela berean (hizkuntza irakaslea sartzen da)')],
        string='Eleanitza modua', default='gela_banatua',
        help='Eleanitzarentzat soilik. Aula banatua: taldea bi geletan '
             'banatzen da, irakasle bana, aldi berean. Gela berean: '
             'hizkuntza irakaslea gela berean sartzen da, dena gela batean.')
    enabled = fields.Boolean('Gaituta', default=True, index=True)

    _sql_constraints = [
        ('uniq_copy', 'unique(copy_id)',
         'Kopia honek lerro bat baino ezin du izan.'),
    ]

    @api.model
    def generate_pairs(self):
        """Crea (idempotente) un par por cada DESDO_/HE_ con su origen.
        Solo AÑADE los que falten; conserva 'enabled'/'eleanitza_mota' ya
        editados. Empareja por código (origen = copia sin prefijo)."""
        Subject = self.env['op.subject']
        existing = set(self.search([]).mapped('copy_id').ids)
        subjects = Subject.search([('active', '=', True)])
        by_code = {s.code: s for s in subjects}
        created = 0
        for c in subjects:
            if c.id in existing:
                continue
            if c.code.startswith('DESDO_'):
                mota, origin_code = 'desdoblea', c.code[6:]
            elif c.code.startswith('HE_'):
                mota, origin_code = 'eleanitza', c.code[3:]
            else:
                continue
            origin = by_code.get(origin_code)
            if not origin:
                continue
            self.create({
                'subject_id': origin.id, 'copy_id': c.id, 'mota': mota,
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
