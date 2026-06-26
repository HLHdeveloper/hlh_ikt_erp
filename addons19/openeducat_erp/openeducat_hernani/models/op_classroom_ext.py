from odoo import api, fields, models


class OpClassroomExt(models.Model):
    _inherit = 'op.classroom'

    irakasgela = fields.Boolean(
        'Irakasgela (docente)', default=True, index=True,
        help='Markatuta: ikasgela/tailer docentea (ordutegietan erabilgarria). '
             'Desmarkatuta: bestelako espazioa (biltegia, komuna, bulegoa, '
             'aldagela...).')

    gela_mota = fields.Selection(
        [('gela', 'Gela'),
         ('tailerra', 'Tailerra')],
        string='Gela mota', default='gela', index=True,
        help='Gela mota FET ordutegirako: gela arrunta (modulu teorikoak) '
             'edo tailerra (modulu praktikoak).')

    solairua = fields.Selection(
        [('0', '0. SOLAIRUA'),
         ('1', '1. SOLAIRUA'),
         ('2', '2. SOLAIRUA'),
         ('3', '3. SOLAIRUA'),
         ('4', '4. SOLAIRUA')],
        string='Solairua', compute='_compute_solairua', store=True, index=True,
        help='Gelaren kodearen arabera automatikoki kalkulatzen den solairua.')

    @api.depends('code')
    def _compute_solairua(self):
        for rec in self:
            code = (rec.code or '').strip().upper()
            if code.startswith('01') or code.startswith('B'):
                rec.solairua = '0'
            elif code.startswith('1-'):
                rec.solairua = '1'
            elif code.startswith('2-'):
                rec.solairua = '2'
            elif code.startswith('3-'):
                rec.solairua = '3'
            elif code.startswith('4-'):
                rec.solairua = '4'
            else:
                rec.solairua = False
