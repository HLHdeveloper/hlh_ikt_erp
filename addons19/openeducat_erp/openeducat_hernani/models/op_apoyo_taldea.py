# -*- coding: utf-8 -*-
from odoo import fields, models


class OpApoyoTaldea(models.Model):
    _name = 'op.apoyo.taldea'
    _description = 'Apoyo Educativo multzoa (modulu sorta talde batean)'
    _rec_name = 'kodea'

    batch_id = fields.Many2one(
        'op.batch', 'Taldea', required=True, ondelete='cascade', index=True)
    kodea = fields.Selection([
        ('I', 'APOYO_EDUCATIVO_I'),
        ('II', 'APOYO_EDUCATIVO_II'),
        ('III', 'APOYO_EDUCATIVO_III'),
    ], string='Apoyo multzoa', required=True)
    guztira_orduak = fields.Float('Horas totales', default=0.0)
    subject_ids = fields.One2many(
        'op.subject', 'apoyo_taldea_id', 'Moduluak')

    _sql_constraints = [
        ('unique_batch_kodea', 'unique(batch_id, kodea)',
         'Talde bakoitzak apoyo multzo bat izango du kode bakoitzeko.'),
    ]
