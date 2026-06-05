from odoo import api, models


class OpStudent(models.Model):
    _inherit = 'op.student'

    @api.model
    def get_ikasleak_dept_breakdown(self):
        cr = self.env.cr
        cr.execute("""
            SELECT d.id, d.name, COUNT(DISTINCT sc.student_id)
            FROM op_department d
            JOIN op_course c ON c.department_id = d.id
            JOIN op_batch b ON b.course_id = c.id AND b.active = true
            JOIN op_student_course sc ON sc.batch_id = b.id
            JOIN op_student s ON s.id = sc.student_id AND s.active = true
            GROUP BY d.id, d.name
            HAVING COUNT(DISTINCT sc.student_id) > 0
            ORDER BY d.name
        """)
        return [{'id': r[0], 'name': r[1], 'count': r[2]} for r in cr.fetchall()]

    @api.model
    def get_ikasleak_batch_breakdown(self, dept_id):
        cr = self.env.cr
        cr.execute("""
            SELECT b.id, b.name, COUNT(DISTINCT sc.student_id)
            FROM op_batch b
            JOIN op_course c ON c.id = b.course_id AND c.department_id = %s
            JOIN op_student_course sc ON sc.batch_id = b.id
            JOIN op_student s ON s.id = sc.student_id AND s.active = true
            WHERE b.active = true
            GROUP BY b.id, b.name
            HAVING COUNT(DISTINCT sc.student_id) > 0
            ORDER BY b.name
        """, (dept_id,))
        return [{'id': r[0], 'name': r[1], 'count': r[2]} for r in cr.fetchall()]

    @api.model
    def get_ikasleak_by_batch(self, batch_id):
        cr = self.env.cr
        cr.execute("""
            SELECT s.id, rp.name
            FROM op_student s
            JOIN res_partner rp ON rp.id = s.partner_id
            JOIN op_student_course sc ON sc.student_id = s.id AND sc.batch_id = %s
            WHERE s.active = true
            ORDER BY rp.name
        """, (batch_id,))
        return [{'id': r[0], 'name': r[1]} for r in cr.fetchall()]
