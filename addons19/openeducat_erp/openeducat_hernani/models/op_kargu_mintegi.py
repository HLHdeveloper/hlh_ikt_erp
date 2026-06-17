from odoo import api, fields, models


class OpKarguMintegi(models.Model):
    """Reparto de las horas (RPT) de un kargu entre mintegiak.

    Cada línea indica, para un kargu, cuántas horas se asignan a un mintegi y
    con qué perfil PT/PES. La pestaña "Perfilazio Irakasleak" de la ficha del
    kargu edita estas líneas; el RPT Total del kargu es la suma de sus horas.
    """
    _name = 'op.kargu.mintegi'
    _description = 'Karguaren orduak mintegika (perfilazioa)'
    _rec_name = 'department_id'
    _order = 'department_id'

    kargu_id = fields.Many2one(
        'op.kargu', 'Kargua', required=True, ondelete='cascade', index=True)
    department_id = fields.Many2one(
        'op.department', 'Mintegia', required=True, ondelete='cascade', index=True)
    pt_pes = fields.Selection([
        ('PT', 'PT'),
        ('PES', 'PES'),
        ('PT_PES', 'PT edo PES'),
    ], string='PT/PES')
    orduak = fields.Float('Orduak (h/aste)', default=0.0)

    _sql_constraints = [
        ('unique_kargu_dept_ptpes', 'unique(kargu_id, department_id, pt_pes)',
         'Mintegi eta PT/PES konbinazio bakoitzeko erregistro bakarra kargu honetan.'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.kargu_id._sync_rpt_total()
        return records

    def write(self, vals):
        karguak = self.kargu_id
        res = super().write(vals)
        (karguak | self.kargu_id)._sync_rpt_total()
        return res

    def unlink(self):
        karguak = self.kargu_id
        res = super().unlink()
        karguak._sync_rpt_total()
        return res
