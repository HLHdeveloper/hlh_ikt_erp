from odoo import fields, models


class OpPerfilazioKargu(models.Model):
    _name = 'op.perfilazio.kargu'
    _description = 'Kargu orduak perfilaziotan'
    _rec_name = 'kargu_id'

    faculty_id = fields.Many2one(
        'op.faculty', 'Irakaslea', required=True, ondelete='cascade', index=True)
    kargu_id = fields.Many2one(
        'op.kargu', 'Kargua', required=True, ondelete='cascade')
    orduak = fields.Float('Orduak (h/aste)', default=0.0)

    _sql_constraints = [
        ('unique_faculty_kargu', 'unique(faculty_id, kargu_id)',
         'Irakasle bakoitzak kargu bakoitzarentzat erregistro bakarra izango du.'),
    ]
