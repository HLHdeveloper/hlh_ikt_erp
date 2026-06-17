from odoo import fields, models


class OpBatch(models.Model):
    _inherit = 'op.batch'

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
