from odoo import fields, models


class OpKargu(models.Model):
    """Cargos de profesores (KARGUAK)"""
    _name = 'op.kargu'
    _description = 'Cargo de Profesor'
    _order = 'name'

    code = fields.Char(
        string='Código', required=True,
        help='Código interno del cargo (karguIZ)'
    )
    name = fields.Char(string='Nombre', required=True)
    gsuite_email = fields.Char(string='Email GSuite del cargo')
    rpt_total = fields.Float(string='RPT Total (h/aste)', default=0.0)
    faculty_ids = fields.Many2many(
        'op.faculty',
        'op_faculty_kargu_rel',
        'kargu_id', 'faculty_id',
        string='Profesores',
    )

    _sql_constraints = [
        ('unique_kargu_code', 'unique(code)', 'El código de cargo debe ser único.'),
    ]
