from odoo import fields, models
from odoo.tools import drop_view_if_exists


class OpReportBatchStudent(models.Model):
    _name = 'op.report.batch.student'
    _description = 'Ikasleak taldeka'
    _auto = False
    _order = 'batch_name'
    _rec_name = 'batch_name'

    batch_id = fields.Many2one('op.batch', string='Taldea', readonly=True)
    batch_name = fields.Char(string='Taldea', readonly=True)
    student_count = fields.Integer(string='Ikasle kop.', readonly=True)

    def init(self):
        drop_view_if_exists(self.env.cr, 'op_report_batch_student')
        self.env.cr.execute("""
            CREATE VIEW op_report_batch_student AS
            SELECT
                ob.id AS id,
                ob.id AS batch_id,
                ob.name AS batch_name,
                COUNT(osc.id) AS student_count
            FROM op_batch ob
            LEFT JOIN op_student_course osc
                ON osc.batch_id = ob.id AND osc.state = 'studying'
            WHERE ob.active = true
            GROUP BY ob.id, ob.name
        """)


class OpReportDeptFaculty(models.Model):
    _name = 'op.report.dept.faculty'
    _description = 'Irakasleak mintegika'
    _auto = False
    _order = 'faculty_count DESC'
    _rec_name = 'department_name'

    department_id = fields.Many2one('op.department', string='Mintegia', readonly=True)
    department_name = fields.Char(string='Mintegia', readonly=True)
    faculty_count = fields.Integer(string='Irakasle kop.', readonly=True)

    def init(self):
        drop_view_if_exists(self.env.cr, 'op_report_dept_faculty')
        self.env.cr.execute("""
            CREATE VIEW op_report_dept_faculty AS
            SELECT
                od.id AS id,
                od.id AS department_id,
                od.name AS department_name,
                COUNT(DISTINCT dfr.op_faculty_id) AS faculty_count
            FROM op_department od
            LEFT JOIN op_department_op_faculty_rel dfr
                ON dfr.op_department_id = od.id
            LEFT JOIN op_faculty of2
                ON of2.id = dfr.op_faculty_id AND of2.active = true
            GROUP BY od.id, od.name
        """)


class OpReportDeptGreba(models.Model):
    _name = 'op.report.dept.greba'
    _description = 'Grebak mintegika'
    _auto = False
    _order = 'greba_count DESC'
    _rec_name = 'department_name'

    department_id = fields.Many2one('op.department', string='Mintegia', readonly=True)
    department_name = fields.Char(string='Mintegia', readonly=True)
    greba_count = fields.Integer(string='Greba parte-hartzeak', readonly=True)

    def init(self):
        drop_view_if_exists(self.env.cr, 'op_report_dept_greba')
        self.env.cr.execute("""
            CREATE VIEW op_report_dept_greba AS
            SELECT
                od.id AS id,
                od.id AS department_id,
                od.name AS department_name,
                COUNT(fgr.greba_id) AS greba_count
            FROM op_department od
            LEFT JOIN op_department_op_faculty_rel dfr
                ON dfr.op_department_id = od.id
            LEFT JOIN op_faculty_greba_rel fgr
                ON fgr.faculty_id = dfr.op_faculty_id
            GROUP BY od.id, od.name
        """)


class OpReportDeptOrdezkapen(models.Model):
    _name = 'op.report.dept.ordezkapen'
    _description = 'Ordezkapenak mintegika'
    _auto = False
    _order = 'ordezkapen_count DESC'
    _rec_name = 'department_name'

    department_id = fields.Many2one('op.department', string='Mintegia', readonly=True)
    department_name = fields.Char(string='Mintegia', readonly=True)
    ordezkapen_count = fields.Integer(string='Ordezkapen kop.', readonly=True)

    def init(self):
        drop_view_if_exists(self.env.cr, 'op_report_dept_ordezkapen')
        self.env.cr.execute("""
            CREATE VIEW op_report_dept_ordezkapen AS
            SELECT
                od.id AS id,
                od.id AS department_id,
                od.name AS department_name,
                COUNT(oo.id) AS ordezkapen_count
            FROM op_department od
            LEFT JOIN op_department_op_faculty_rel dfr
                ON dfr.op_department_id = od.id
            LEFT JOIN op_ordezkapen oo
                ON oo.titular_id = dfr.op_faculty_id
            GROUP BY od.id, od.name
        """)


class OpReportFacultyGreba(models.Model):
    _name = 'op.report.faculty.greba'
    _description = 'Irakasleak greba parte-hartzeak'
    _auto = False
    _order = 'greba_count DESC'
    _rec_name = 'faculty_name'

    faculty_id = fields.Many2one('op.faculty', string='Irakaslea', readonly=True)
    faculty_name = fields.Char(string='Irakaslea', readonly=True)
    department_id = fields.Many2one('op.department', string='Mintegia', readonly=True)
    department_name = fields.Char(string='Mintegia', readonly=True)
    greba_count = fields.Integer(string='Greba kop.', readonly=True)

    def init(self):
        drop_view_if_exists(self.env.cr, 'op_report_faculty_greba')
        self.env.cr.execute("""
            CREATE VIEW op_report_faculty_greba AS
            SELECT
                of2.id AS id,
                of2.id AS faculty_id,
                rp.name AS faculty_name,
                of2.main_department_id AS department_id,
                od.name AS department_name,
                COUNT(fgr.greba_id) AS greba_count
            FROM op_faculty of2
            JOIN res_partner rp ON rp.id = of2.partner_id
            LEFT JOIN op_faculty_greba_rel fgr ON fgr.faculty_id = of2.id
            LEFT JOIN op_department od ON od.id = of2.main_department_id
            WHERE of2.active = true
            GROUP BY of2.id, rp.name, of2.main_department_id, od.name
        """)
