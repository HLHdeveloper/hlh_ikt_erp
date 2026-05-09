from odoo import api, fields, models


class OpGreba(models.Model):
    """Huelgas de profesores (IR_GREBAK)"""
    _name = 'op.greba'
    _description = 'Huelga de Profesores'
    _order = 'date desc'

    code = fields.Char(
        string='Código', required=True,
        help='Código de la huelga (irGREBA)'
    )
    date = fields.Date(string='Fecha', required=True)
    reason = fields.Char(string='Motivo')
    faculty_ids = fields.Many2many(
        'op.faculty',
        'op_faculty_greba_rel',
        'greba_id', 'faculty_id',
        string='Profesores participantes',
    )
    faculty_count = fields.Integer(
        string='Nº Participantes',
        compute='_compute_faculty_count',
        store=True,
    )

    @api.depends('faculty_ids')
    def _compute_faculty_count(self):
        for rec in self:
            rec.faculty_count = len(rec.faculty_ids)

    _sql_constraints = [
        ('unique_greba_code', 'unique(code)', 'El código de huelga debe ser único.'),
    ]
