# -*- coding: utf-8 -*-
from odoo import api, models, fields
from odoo.osv.expression import AND


class OpSubjectExt(models.Model):
    _inherit = "op.subject"

    kode_jima = fields.Char('Kode Jima', size=256)
    batch_id = fields.Many2one('op.batch', 'Taldea')
    apoyo_taldea_id = fields.Many2one(
        'op.apoyo.taldea', 'Apoyo multzoa', ondelete='set null', index=True)
    faculty_id = fields.Many2one('op.faculty', 'Irakaslea', ondelete='set null', index=True)
    talde_kodea = fields.Char(related='batch_id.code', string='Talde Kodea', store=False)
    # Mintegi propio del módulo (vía taldea → zikloa → departamentua). Se usa
    # para el dominio de 'mintegiko_irakaslea' (excluir el departamento propio)
    # y como categoría MINTEGIA del searchpanel de la lista de Moduluak; por eso
    # es store=True + index (el searchpanel con enable_counters usa read_group,
    # que requiere un campo almacenado).
    own_department_id = fields.Many2one(
        'op.department', string='Moduluaren mintegia',
        related='batch_id.course_id.department_id', store=True, index=True)
    # Zikloa del módulo (vía taldea). store=True + index para usarlo como
    # categoría intermedia del searchpanel (Mintegia → Zikloa → Taldea).
    course_id = fields.Many2one(
        'op.course', string='Zikloa',
        related='batch_id.course_id', store=True, index=True)
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

    def action_open_form(self):
        """Abre la ficha (formulario) del módulo desde la lista. Necesario
        porque la lista es editable (solo 'Aste Banaketa') y en ese modo el
        clic en una fila no abre el formulario; el resto de campos se editan
        en la ficha vía este botón."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.display_name,
            'res_model': 'op.subject',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model
    def _hernani_fold_category_domain(self, kwargs):
        """Searchpanel en cascada real (Mintegia → Zikloa → Taldea).

        Por defecto Odoo calcula los valores VISIBLES de cada categoría del
        searchpanel solo a partir de `search_domain` (la barra de búsqueda) e
        ignora la selección de las OTRAS categorías: esa selección va a
        `category_domain`, que únicamente ajusta los contadores (dejando las
        no coincidentes a 0, pero mostrándolas). Por eso al elegir un mintegi
        seguían apareciendo TODOS los zikloak/taldeak.

        Plegamos `category_domain` dentro de `search_domain` para que el propio
        conjunto de valores mostrados quede restringido: así Zikloa solo
        muestra los del mintegi elegido y Taldea solo los del zikloa elegido.
        """
        cat = kwargs.get('category_domain')
        if cat:
            kwargs = dict(kwargs)
            kwargs['search_domain'] = AND([kwargs.get('search_domain') or [], cat])
            kwargs['category_domain'] = []
        return kwargs

    @api.model
    def search_panel_select_range(self, field_name, **kwargs):
        return super().search_panel_select_range(
            field_name, **self._hernani_fold_category_domain(kwargs))

    @api.model
    def search_panel_select_multi_range(self, field_name, **kwargs):
        return super().search_panel_select_multi_range(
            field_name, **self._hernani_fold_category_domain(kwargs))

    @api.onchange('gela_orduak')
    def _onchange_gela_orduak(self):
        # Aste banaketa va ligada a las horas de gela: si al cambiar gela la
        # banaketa elegida ya no cuadra (guztira != gela_orduak), se limpia
        # para que el desplegable vuelva a ofrecer solo las opciones válidas y
        # no quede un valor fuera de dominio (que dispararía el modal de campo
        # inválido al guardar inline en la lista).
        for rec in self:
            if rec.banaketa_id and rec.banaketa_id.guztira != rec.gela_orduak:
                rec.banaketa_id = False
