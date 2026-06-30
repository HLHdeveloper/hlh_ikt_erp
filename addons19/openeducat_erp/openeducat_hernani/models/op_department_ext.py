from odoo import fields, models


class OpDepartment(models.Model):
    _inherit = 'op.department'

    # Ciclos formativos del departamento (inverso de op.course.department_id)
    course_ids = fields.One2many(
        'op.course', 'department_id',
        string='Ciclos formativos',
    )

    # Profesores del departamento — reutiliza la tabla de allowed_department_ids
    faculty_ids = fields.Many2many(
        'op.faculty',
        'op_department_op_faculty_rel',
        'op_department_id', 'op_faculty_id',
        string='Profesores',
    )

    # Tope (ordu erabilgarriak) de horas de desdoble / errefortzu del mintegi
    # (Desdoble_HE, tabla resumen). La suma del reparto por grupo
    # (op.batch.desdoble_orduak / errefortzu_orduak) no puede superar este valor.
    desdoble_orduak = fields.Float(string='Desdoble orduak guztira (mintegia)')
    errefortzu_orduak = fields.Float(string='Errefortzu orduak guztira (mintegia)')

    # Cómo se perfilan las horas de errefortzu del mintegi (Desdoble_HE):
    #  - 'poltsan' : sin módulos; se reparten a profesores como karguak
    #                (op.perfilazio.kargu), tal cual se hace actualmente.
    #  - 'taldean' : se crean módulos ERREF_ y se gestiona como desdobleak.
    #  - 'mix'     : una parte a POLTSAN (errefortzu_poltsan_orduak) y el resto
    #                a módulos (TALDEAN).
    errefortzu_mota = fields.Selection(
        [('poltsan', 'POLTSAN'), ('taldean', 'TALDEAN'), ('mix', 'MIX')],
        string='Errefortzu orduak', default='poltsan', required=True)

    # Solo en modo MIX: horas de errefortzu que van a POLTSAN (resto → módulos).
    errefortzu_poltsan_orduak = fields.Float(string='Errefortzu POLTSAN orduak (MIX)')

    # Gelak/tailerrak erabilgarriak mintegiarentzat (FET #3 oinarria). M2M
    # (ez esklusiboa): teoria gelak mintegien artean partekatu daitezke.
    # Moduluen aula-aukeren dominioa hemendik filtratzen da.
    gela_ids = fields.Many2many(
        'op.classroom',
        'op_department_op_classroom_rel',
        'department_id', 'classroom_id',
        string='Gelak erabilgarriak',
    )
