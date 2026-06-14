# -*- coding: utf-8 -*-
from odoo import api, models, fields


class OpSubjectExt(models.Model):
    _inherit = "op.subject"

    kode_jima = fields.Char('Kode Jima', size=256)
    batch_id = fields.Many2one('op.batch', 'Taldea')
    apoyo_taldea_id = fields.Many2one(
        'op.apoyo.taldea', 'Apoyo multzoa', ondelete='set null', index=True)
    faculty_id = fields.Many2one('op.faculty', 'Irakaslea', ondelete='set null', index=True)
    talde_kodea = fields.Char(related='batch_id.code', string='Talde Kodea', store=False)
    # Mintegi propio del módulo (vía taldea → zikloa → departamentua). Solo para
    # el dominio del campo siguiente (excluir el departamento propio).
    own_department_id = fields.Many2one(
        'op.department', string='Moduluaren mintegia',
        related='batch_id.course_id.department_id', store=False)
    # Override manual: departamento (distinto del propio) cuyos profesores
    # pueden impartir este módulo en Perfilazioak. Ej: 2INF4_EEE (mintegi
    # INFORMATIKA) impartido por un profesor de ELEKTRIZITATEA.
    mintegiko_irakaslea = fields.Many2one(
        'op.department', string='Mintegiko irakaslea', ondelete='set null', index=True)
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
    pl = fields.Selection([
        ('PL1', 'PL1'),
        ('PL2', 'PL2'),
        ('PL1_PL2', 'PL1/PL2'),
    ], string='PL')
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
    rpt_reala = fields.Float('RPT Reala')
    rpt_zorretan = fields.Float('RPT Zorretan')
    emandako_orduak = fields.Float('Emandako Orduak')
    orduak_zorretan = fields.Float('Orduak Zorretan')
    zikloko_orduak_enpresan = fields.Float('Zikloko Orduak Enpresan')

    @api.depends('banaketa_id')
    def _compute_aste_banaketa(self):
        for rec in self:
            rec.aste_banaketa = rec.banaketa_id.name or False
