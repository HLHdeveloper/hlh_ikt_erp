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
    banaketa_orduak = fields.Float(
        'Banaketa orduak', compute='_compute_banaketa_orduak', store=True,
        help='Aste banaketaren oinarri diren orduak: DESDO_/ERREF_ '
             'moduluetan RPT Total; gainerakoetan Gela Orduak.')
    banaketa_id = fields.Many2one(
        'op.subject.banaketa', string='Aste Banaketa',
        ondelete='set null',
        domain="[('guztira', '=', banaketa_orduak)]",
    )
    aste_banaketa = fields.Char(
        'Aste Banaketa', compute='_compute_aste_banaketa', store=True)
    teoria_praktika_gabe = fields.Boolean(
        'Teoria/Praktika gabe', compute='_compute_teoria_praktika_gabe',
        store=True,
        help='DESDO_/ERREF_/ERRF_ moduluek edo JARRAIAN banaketa dutenek ez '
             'dute teoria/praktika ordu banaketarik aukeratzen.')
    teoria_praktika_id = fields.Many2one(
        'op.subject.teoria.praktika', string='Teoria/Praktika Orduak',
        ondelete='set null',
        domain="[('guztira', '=', gela_orduak)]",
        help='Gela orduen banaketa Teoria (gela) / Praktika (tailer) artean. '
             'Aukerak gela orduen kopurua berdintzen dute (ad. 7h → 5T/2P).')
    # Aula-esleipena (.fet sorkuntzarako; lehen Excel-en zegoena). Aukera anitz:
    # FET-ek bat hautatzen du sortzean. Dominioa gela_mota-ren arabera; mintegiaren
    # gela erabilgarrien araberako filtroa bistan/pantaila dedikatuan aplikatzen da.
    gela_teoria_ids = fields.Many2many(
        'op.classroom',
        'op_subject_gela_teoria_rel',
        'subject_id', 'classroom_id',
        string='Teoria gelak (aukerak)',
        domain="[('gela_mota', 'in', ['gela', 'gela_tailerra']), ('irakasgela', '=', True)]",
        help='Modulu honen teoria-orduentzako gela hautagaiak. FET-ek bat aukeratzen du.')
    tailerra_ids = fields.Many2many(
        'op.classroom',
        'op_subject_tailerra_rel',
        'subject_id', 'classroom_id',
        string='Tailerrak (aukerak)',
        domain="[('gela_mota', 'in', ['tailerra', 'gela_tailerra']), ('irakasgela', '=', True)]",
        help='Modulu honen praktika-orduentzako tailer hautagaiak.')

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

    @api.depends('code', 'banaketa_id', 'banaketa_id.name')
    def _compute_teoria_praktika_gabe(self):
        # DESDO_/ERREF_/ERRF_ y los módulos con banaketa JARRAIAN no eligen
        # teoria/praktika: se desactiva (vacío y readonly) la columna.
        for rec in self:
            code = (rec.code or '').upper()
            ban = (rec.banaketa_id.name or '').upper()
            gabe = (code.startswith('DESDO_') or code.startswith('ERREF')
                    or code.startswith('ERRF') or ban == 'JARRAIAN')
            rec.teoria_praktika_gabe = gabe
            if gabe and rec.teoria_praktika_id:
                rec.teoria_praktika_id = False

    @api.depends('code', 'gela_orduak', 'rpt_total')
    def _compute_banaketa_orduak(self):
        # DESDO_ y ERREF_ reparten sus horas RPT (no tienen gela propia); el
        # resto de módulos reparten las horas de gela.
        for rec in self:
            code = (rec.code or '').upper()
            if code.startswith('DESDO_') or code.startswith('ERREF_'):
                rec.banaketa_orduak = rec.rpt_total
            else:
                rec.banaketa_orduak = rec.gela_orduak

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

    # Jerarquía del searchpanel en cascada: Mintegia → Zikloa → Taldea.
    _HERNANI_SEARCHPANEL_ORDER = ['own_department_id', 'course_id', 'batch_id']

    @api.model
    def _hernani_fold_category_domain(self, field_name, kwargs):
        """Searchpanel en cascada real (Mintegia → Zikloa → Taldea).

        Por defecto Odoo calcula los valores VISIBLES de cada categoría del
        searchpanel solo a partir de `search_domain` (la barra de búsqueda) e
        ignora la selección de las OTRAS categorías: esa selección va a
        `category_domain`, que únicamente ajusta los contadores (dejando las
        no coincidentes a 0, pero mostrándolas). Por eso al elegir un mintegi
        seguían apareciendo TODOS los zikloak/taldeak.

        Plegamos `category_domain` dentro de `search_domain`, PERO solo las
        condiciones de las categorías ANTERIORES en la jerarquía (los
        "ancestros" de `field_name`). Así la cascada restringe SOLO hacia
        abajo: Zikloa se filtra por el Mintegi elegido y Taldea por el Zikloa
        elegido, mientras que cada categoría nunca se restringe por sí misma
        ni por sus descendientes. Esto es clave para que la categoría superior
        (Mintegia) muestre SIEMPRE todos sus valores: al pulsar "Todos" en
        Mintegia (o al cambiar de mintegi) la lista se refresca y se puede
        seleccionar otro, en vez de quedar atrapada por una selección de
        Zikloa/Taldea previa.
        """
        cat = kwargs.get('category_domain')
        if not cat:
            return kwargs
        order = self._HERNANI_SEARCHPANEL_ORDER
        if field_name in order:
            ancestors = set(order[:order.index(field_name)])
        else:
            # Campo fuera de la jerarquía: comportamiento anterior (plegar todo).
            ancestors = None
        kept = []
        for leaf in cat:
            if (ancestors is None
                    or (isinstance(leaf, (list, tuple)) and len(leaf) == 3
                        and leaf[0] in ancestors)):
                kept.append(leaf)
        kwargs = dict(kwargs)
        kwargs['search_domain'] = AND([kwargs.get('search_domain') or [], kept])
        kwargs['category_domain'] = []
        return kwargs

    @api.model
    def search_panel_select_range(self, field_name, **kwargs):
        return super().search_panel_select_range(
            field_name, **self._hernani_fold_category_domain(field_name, kwargs))

    @api.model
    def search_panel_select_multi_range(self, field_name, **kwargs):
        return super().search_panel_select_multi_range(
            field_name, **self._hernani_fold_category_domain(field_name, kwargs))

    # ------------------------------------------------------------------
    # Gela esleipena (pantalla OWL Fase 3): asignar aulas a módulos por mintegi
    # ------------------------------------------------------------------
    @api.model
    def get_aula_columns(self, dept_id):
        """Aulas disponibles del mintegi separadas en columnas teoría/taller."""
        dept = self.env['op.department'].browse(dept_id)
        gelak = dept.gela_ids.filtered(
            lambda c: c.gela_mota in ('gela', 'gela_tailerra'))
        tailerrak = dept.gela_ids.filtered(
            lambda c: c.gela_mota in ('tailerra', 'gela_tailerra'))

        def adict(recs):
            return [{'id': c.id, 'code': c.code, 'name': c.name or ''}
                    for c in recs.sorted('code')]
        return {'gelak': adict(gelak), 'tailerrak': adict(tailerrak)}

    @api.model
    def get_aula_moduluak(self, batch_id):
        """Módulos de una taldea con su asignación de aulas. Mismos módulos que
        Perfilazioak: TODOS los del batch (incluidas copias HE_/DESDO_/ERREF)."""
        mods = self.search([('batch_id', '=', batch_id)])
        out = []
        for m in mods.sorted('code'):
            out.append({
                'id': m.id, 'code': m.code,
                'gela_orduak': m.gela_orduak,
                'tp': m.teoria_praktika_id.name or '',
                'teoria_ids': m.gela_teoria_ids.ids,
                'tailerra_ids': m.tailerra_ids.ids,
            })
        return out

    @api.model
    def set_aula_column(self, subject_ids, classroom_id, kind, value):
        """Asigna (value=True) o quita (value=False) un aula en TODOS los módulos
        dados (un click en la cabecera del aula → toda la taldea)."""
        field = 'gela_teoria_ids' if kind == 'teoria' else 'tailerra_ids'
        cmd = (4, classroom_id) if value else (3, classroom_id)
        self.browse(subject_ids).write({field: [cmd]})
        return value

    @api.model
    def toggle_aula(self, subject_id, classroom_id, kind):
        """Alterna un aula (kind='teoria'|'tailerra') en un módulo. Devuelve
        True si quedó asignada, False si se quitó."""
        m = self.browse(subject_id)
        field = 'gela_teoria_ids' if kind == 'teoria' else 'tailerra_ids'
        if classroom_id in m[field].ids:
            m[field] = [(3, classroom_id)]
            return False
        m[field] = [(4, classroom_id)]
        return True

    @api.onchange('gela_orduak', 'rpt_total')
    def _onchange_gela_orduak(self):
        # Aste banaketa va ligada a las horas de referencia (banaketa_orduak =
        # RPT Total en DESDO_/ERREF_, gela_orduak en el resto): si al cambiar
        # esas horas la banaketa elegida ya no cuadra, se limpia para que el
        # desplegable vuelva a ofrecer solo las opciones válidas y no quede un
        # valor fuera de dominio (que dispararía el modal de campo inválido al
        # guardar inline en la lista).
        for rec in self:
            if (rec.banaketa_id
                    and rec.banaketa_id.guztira != rec.banaketa_orduak):
                rec.banaketa_id = False
            if (rec.teoria_praktika_id
                    and rec.teoria_praktika_id.guztira != rec.gela_orduak):
                rec.teoria_praktika_id = False
