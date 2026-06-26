from odoo import api, fields, models


class OpBatch(models.Model):
    _inherit = 'op.batch'

    # Nº de alumnos matriculados (state 'studying'). Para el cálculo de aforo
    # en los desdobles/agrupaciones FET.
    fet_student_count = fields.Integer(
        string='Ikasle kopurua', compute='_compute_fet_student_count')

    @api.depends('student_course_ids', 'student_course_ids.state')
    def _compute_fet_student_count(self):
        data = {}
        if self.ids:
            self.env.cr.execute("""
                SELECT batch_id, COUNT(*) FROM op_student_course
                WHERE batch_id IN %s AND state = 'studying'
                GROUP BY batch_id
            """, (tuple(self.ids),))
            data = dict(self.env.cr.fetchall())
        for rec in self:
            rec.fet_student_count = data.get(rec.id, 0)

    # Profesores que imparten en este grupo
    faculty_ids = fields.Many2many(
        'op.faculty',
        'op_faculty_batch_rel',
        'batch_id', 'faculty_id',
        string='Profesores',
    )

    # Alumnos matriculados en este grupo
    student_course_ids = fields.One2many(
        'op.student.course', 'batch_id',
        string='Alumnos matriculados',
    )

    # Tope total de horas de desdoble del grupo (Perfilazioak / Desdoblea).
    # La suma de las horas de desdoble de los módulos DESDO_ del grupo no puede
    # superar este valor. 0 = sin tope (comportamiento previo).
    desdoble_orduak = fields.Float(string='Desdoble orduak guztira')
