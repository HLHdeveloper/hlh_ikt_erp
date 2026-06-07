# -*- coding: utf-8 -*-
from odoo import api, models, fields


class OpSubjectExt(models.Model):
    _inherit = "op.subject"

    kode_jima = fields.Char('Kode Jima', size=256)
    batch_id = fields.Many2one('op.batch', 'Taldea')
    faculty_id = fields.Many2one('op.faculty', 'Irakaslea', ondelete='set null', index=True)
    talde_kodea = fields.Char(related='batch_id.code', string='Talde Kodea', store=False)
    pt_pes = fields.Selection([
        ('PT', 'PT'),
        ('PES', 'PES'),
        ('PT_PES', 'PT edo PES'),
    ], string='PT_PES')
    hizkuntza = fields.Selection([
        ('euskaraz', 'Euskaraz'),
        ('gazteleraz', 'Gazteleraz'),
        ('eleanitza', 'Eleanitza'),
    ], string='Hizkuntza')
    orduak = fields.Float('Orduak')
    kurtsoa = fields.Char('Kurtsoa', size=10)
    gela_orduak = fields.Float('Gela Orduak')
    banaketa_id = fields.Many2one(
        'op.subject.banaketa', string='Aste Banaketa',
        ondelete='set null',
        domain="[('guztira', '=', gela_orduak)]",
    )
    aste_banaketa = fields.Char(
        'Aste Banaketa', compute='_compute_aste_banaketa', store=True)
    rpt_total = fields.Float('RPT Total')
    orduak_zorretan = fields.Float('Orduak Zorretan')
    zikloko_orduak_enpresan = fields.Float('Zikloko Orduak Enpresan')

    @api.depends('banaketa_id')
    def _compute_aste_banaketa(self):
        for rec in self:
            rec.aste_banaketa = rec.banaketa_id.name or False
