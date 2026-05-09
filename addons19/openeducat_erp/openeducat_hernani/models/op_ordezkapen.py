from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class OpOrdezkapen(models.Model):
    """Sustituciones entre profesores (ORDEZKAPENAK)"""
    _name = 'op.ordezkapen'
    _description = 'Sustitución de Profesor'
    _order = 'start_date desc'

    titular_id = fields.Many2one(
        'op.faculty', string='Profesor titular',
        required=True, ondelete='cascade',
        index=True,
    )
    ordezko_id = fields.Many2one(
        'op.faculty', string='Profesor sustituto',
        required=True, ondelete='cascade',
        index=True,
    )
    start_date = fields.Date(string='Fecha inicio', required=True)
    end_date = fields.Date(string='Fecha fin')
    notes = fields.Text(string='Observaciones')

    @api.constrains('titular_id', 'ordezko_id')
    def _check_different_faculty(self):
        for rec in self:
            if rec.titular_id == rec.ordezko_id:
                raise ValidationError(
                    _('El profesor titular y el sustituto deben ser personas distintas.')
                )

    def action_bukatu(self):
        self.end_date = fields.Date.today()

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.end_date and rec.start_date > rec.end_date:
                raise ValidationError(
                    _('La fecha de fin no puede ser anterior a la fecha de inicio.')
                )
