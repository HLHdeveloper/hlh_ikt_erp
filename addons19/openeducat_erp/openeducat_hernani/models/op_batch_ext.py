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
