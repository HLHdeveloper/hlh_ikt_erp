# -*- coding: utf-8 -*-
from odoo import fields, models


class OpPerfilazioBertsioa(models.Model):
    """Versión guardada (snapshot) de la perfilación de un departamento.
    Permite tener varias versiones por mintegi y poder cargar/volver a
    perfilaciones anteriores. El estado se guarda como JSON en `data`:
        {
          'modules': {subject_id: faculty_id | null, ...},   # módulos del mintegi
          'karguak': [{'faculty_id', 'kargu_id', 'orduak'}, ...],
          'pt_pes':  {faculty_id: 'PT'|'PES'|null, ...},      # override manual
        }
    """
    _name = 'op.perfilazio.bertsioa'
    _description = 'Perfilazio bertsioa (snapshot)'
    _order = 'create_date desc'

    name = fields.Char('Izena', required=True)
    department_id = fields.Many2one(
        'op.department', 'Mintegia', required=True, ondelete='cascade', index=True)
    oharra = fields.Char('Oharra')
    is_auto = fields.Boolean('Auto-gordea', default=False)
    data = fields.Json('Snapshot')
