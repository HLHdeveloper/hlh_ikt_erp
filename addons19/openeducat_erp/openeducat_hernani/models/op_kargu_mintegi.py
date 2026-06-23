from odoo import api, fields, models
from odoo.tools import drop_view_if_exists


class OpKarguMintegi(models.Model):
    """Reparto de las horas (RPT) de un kargu entre mintegiak.

    Cada línea indica, para un kargu, cuántas horas se asignan a un mintegi y
    con qué perfil PT/PES. La pestaña "Perfilazio Irakasleak" de la ficha del
    kargu edita estas líneas; el RPT Total del kargu es la suma de sus horas.
    """
    _name = 'op.kargu.mintegi'
    _description = 'Karguaren orduak mintegika (perfilazioa)'
    _rec_name = 'department_id'
    _order = 'department_id'

    kargu_id = fields.Many2one(
        'op.kargu', 'Kargua', required=True, ondelete='cascade', index=True)
    department_id = fields.Many2one(
        'op.department', 'Mintegia', required=True, ondelete='cascade', index=True)
    pt_pes = fields.Selection([
        ('PT', 'PT'),
        ('PES', 'PES'),
        ('PT_PES', 'PT edo PES'),
    ], string='PT/PES')
    orduak = fields.Float('Orduak (h/aste)', default=0.0)
    kargu_code = fields.Char(
        related='kargu_id.code', string='Kodea', store=True, index=True)
    kargu_mota = fields.Selection(
        related='kargu_id.kargu_mota', string='Kargu mota', store=True, index=True)

    _sql_constraints = [
        ('unique_kargu_dept_ptpes', 'unique(kargu_id, department_id, pt_pes)',
         'Mintegi eta PT/PES konbinazio bakoitzeko erregistro bakarra kargu honetan.'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.kargu_id._sync_rpt_total()
        return records

    def write(self, vals):
        karguak = self.kargu_id
        res = super().write(vals)
        (karguak | self.kargu_id)._sync_rpt_total()
        return res

    def unlink(self):
        karguak = self.kargu_id
        res = super().unlink()
        karguak._sync_rpt_total()
        return res


class OpKarguMintegiAll(models.Model):
    """Vista de solo lectura para el menú Karguak.

    Une las líneas de reparto reales (op.kargu.mintegi) con una fila sintética
    por cada cargo SIN reparto, para que esos cargos (p.ej. LCAMP) también se
    vean cuando el searchpanel Mintegia está en "todos". Las filas sintéticas
    tienen department_id NULL y 0 horas, así no aparecen al filtrar por un
    mintegi concreto ni alteran el GUZTIRA por mintegi.
    """
    _name = 'op.kargu.mintegi.all'
    _description = 'Karguak mintegika (guztiak)'
    _auto = False
    _order = 'kargu_code'
    _rec_name = 'kargu_id'

    kargu_id = fields.Many2one('op.kargu', string='Kargua', readonly=True)
    kargu_code = fields.Char(string='Kodea', readonly=True)
    kargu_mota = fields.Selection([
        ('perfilazioa', 'Perfilazio Karguak'),
        ('drive', 'DRIVE Taldeak'),
    ], string='Kargu mota', readonly=True)
    department_id = fields.Many2one('op.department', string='Mintegia', readonly=True)
    pt_pes = fields.Selection([
        ('PT', 'PT'),
        ('PES', 'PES'),
        ('PT_PES', 'PT edo PES'),
    ], string='PT/PES', readonly=True)
    orduak = fields.Float(string='Orduak (h/aste)', readonly=True)

    def init(self):
        drop_view_if_exists(self.env.cr, 'op_kargu_mintegi_all')
        self.env.cr.execute("""
            CREATE VIEW op_kargu_mintegi_all AS
                SELECT
                    km.id AS id,
                    km.kargu_id AS kargu_id,
                    km.department_id AS department_id,
                    km.pt_pes AS pt_pes,
                    km.orduak AS orduak,
                    k.code AS kargu_code,
                    k.kargu_mota AS kargu_mota
                FROM op_kargu_mintegi km
                JOIN op_kargu k ON k.id = km.kargu_id
                UNION ALL
                SELECT
                    1000000000 + k.id AS id,
                    k.id AS kargu_id,
                    NULL::integer AS department_id,
                    NULL::varchar AS pt_pes,
                    0.0 AS orduak,
                    k.code AS kargu_code,
                    k.kargu_mota AS kargu_mota
                FROM op_kargu k
                WHERE NOT EXISTS (
                    SELECT 1 FROM op_kargu_mintegi km2 WHERE km2.kargu_id = k.id
                )
        """)
