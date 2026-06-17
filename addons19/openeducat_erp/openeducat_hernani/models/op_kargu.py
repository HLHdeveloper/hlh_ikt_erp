from odoo import api, fields, models


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
    rpt_total = fields.Float(
        string='RPT Total (h/aste)', default=0.0,
        help='Suma de las horas repartidas por mintegi en "Perfilazio '
             'Irakasleak". Si el kargu no tiene reparto por mintegi, se '
             'conserva el valor introducido manualmente.')
    faculty_ids = fields.Many2many(
        'op.faculty',
        'op_faculty_kargu_rel',
        'kargu_id', 'faculty_id',
        string='Profesores',
    )
    perfilazio_ids = fields.One2many(
        'op.kargu.mintegi', 'kargu_id', string='Perfilazio Irakasleak')

    _sql_constraints = [
        ('unique_kargu_code', 'unique(code)', 'El código de cargo debe ser único.'),
    ]

    def _sync_rpt_total(self):
        """Si el kargu tiene reparto por mintegi (perfilazio_ids), rpt_total =
        suma de esas horas. Si no hay reparto, se conserva el valor manual."""
        for rec in self:
            if rec.perfilazio_ids:
                total = sum(rec.perfilazio_ids.mapped('orduak'))
                if rec.rpt_total != total:
                    rec.rpt_total = total

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_rpt_total()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'perfilazio_ids' in vals:
            self._sync_rpt_total()
        return res
