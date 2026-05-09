from odoo import fields, models


class OpDepartment(models.Model):
    _inherit = 'op.department'

    # Ciclos formativos del departamento (inverso de op.course.department_id)
    course_ids = fields.One2many(
        'op.course', 'department_id',
        string='Ciclos formativos',
    )

    # Profesores del departamento — reutiliza la tabla de allowed_department_ids
    faculty_ids = fields.Many2many(
        'op.faculty',
        'op_department_op_faculty_rel',
        'op_department_id', 'op_faculty_id',
        string='Profesores',
    )
