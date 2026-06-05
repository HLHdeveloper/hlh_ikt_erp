# -*- coding: utf-8 -*-
from odoo import models, fields


class OpSubjectExt(models.Model):
    _inherit = "op.subject"

    kode_jima = fields.Char('Kode Jima', size=256)
    batch_id = fields.Many2one('op.batch', 'Taldea')
    talde_kodea = fields.Char(related='batch_id.code', string='Talde Kodea', store=False)
    pt_pes = fields.Char('PT_PES', size=10)
    hizkuntza = fields.Char('Hizkuntza', size=50)
    orduak = fields.Float('Orduak')
    kurtsoa = fields.Char('Kurtsoa', size=10)
    gela_orduak = fields.Integer('Gela Orduak')
    aste_banaketa = fields.Char('Aste Banaketa', size=50)
    rpt_total = fields.Float('RPT Total')
    orduak_zorretan = fields.Float('Orduak Zorretan')
