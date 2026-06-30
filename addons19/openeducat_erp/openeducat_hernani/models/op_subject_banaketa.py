# -*- coding: utf-8 -*-
from odoo import api, fields, models


def _partitions(n, k, mx):
    """Particiones de n en <=k partes, cada parte <= mx, en orden descendente."""
    if n == 0:
        yield []
        return
    if k == 0:
        return
    for first in range(min(n, mx), 0, -1):
        for rest in _partitions(n - first, k - 1, first):
            yield [first] + rest


class OpSubjectBanaketa(models.Model):
    _name = 'op.subject.banaketa'
    _description = 'Aste banaketa aukerak (eguneko orduak)'
    _rec_name = 'name'
    _order = 'guztira, name'

    name = fields.Char('Banaketa', required=True, index=True)
    guztira = fields.Integer('Guztira (h/aste)', required=True, index=True)
    egun_kopurua = fields.Integer('Egun kopurua')

    _sql_constraints = [
        ('unique_name', 'unique(name)', 'Banaketa errepikatua.'),
    ]

    @api.model
    def _populate_options(self, max_total=15, max_days=5):
        """Genera idempotentemente todas las particiones (<= max_days días)
        para totales de 1 a max_total. Llamado desde data XML <function>."""
        existing = set(self.with_context(active_test=False).search([]).mapped('name'))
        vals = []
        for total in range(1, max_total + 1):
            for parts in _partitions(total, max_days, total):
                name = '/'.join(str(p) for p in parts)
                if name in existing:
                    continue
                vals.append({
                    'name': name,
                    'guztira': total,
                    'egun_kopurua': len(parts),
                })
        if vals:
            self.create(vals)
        return True


class OpSubjectTeoriaPraktika(models.Model):
    """Aukera-taula: gela orduak Teoria (gela) / Praktika (tailer) artean
    banatzeko konbinazioak. Aste banaketa bezala, desplegable batean
    eskaintzen dira `guztira` orduak berdintzen dituztenak."""
    _name = 'op.subject.teoria.praktika'
    _description = 'Teoria/Praktika ordu banaketa aukerak'
    _rec_name = 'name'
    _order = 'guztira, teoria desc'

    name = fields.Char('Teoria/Praktika', required=True, index=True)
    guztira = fields.Integer('Guztira (h)', required=True, index=True)
    teoria = fields.Integer('Teoria orduak (gela)')
    praktika = fields.Integer('Praktika orduak (tailer)')

    _sql_constraints = [
        ('unique_name', 'unique(name)', 'Konbinazioa errepikatua.'),
    ]

    @api.model
    def _populate_options(self, max_total=15):
        """Genera idempotentemente todas las combinaciones T/P (T+P=total)
        para totales de 1 a max_total. Ej. total 7 → 7T/0P, 6T/1P … 0T/7P."""
        existing = set(self.with_context(active_test=False).search([]).mapped('name'))
        vals = []
        for total in range(1, max_total + 1):
            for teoria in range(total, -1, -1):
                praktika = total - teoria
                name = '%dT/%dP' % (teoria, praktika)
                if name in existing:
                    continue
                vals.append({
                    'name': name,
                    'guztira': total,
                    'teoria': teoria,
                    'praktika': praktika,
                })
        if vals:
            self.create(vals)
        return True
