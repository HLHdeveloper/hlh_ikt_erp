#!/usr/bin/env python3
"""
Create op.subject.registration records for all students in state='studying'.
Idempotent: skips if registration already exists for (student, course, batch).
"""
import odoo
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['--config=/etc/odoo/odoo.conf'])

with odoo.registry('kudeaketa').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})

    student_courses = env['op.student.course'].search([('state', '=', 'studying')])
    print(f"Found {len(student_courses)} student-course records in 'studying' state")

    created = 0
    skipped = 0
    errors = 0

    for sc in student_courses:
        if not sc.student_id or not sc.course_id or not sc.batch_id:
            skipped += 1
            continue

        existing = env['op.subject.registration'].search([
            ('student_id', '=', sc.student_id.id),
            ('course_id', '=', sc.course_id.id),
            ('batch_id', '=', sc.batch_id.id),
        ], limit=1)

        if existing:
            skipped += 1
            continue

        # Get compulsory subjects for this course
        compulsory_subjects = sc.course_id.subject_ids.filtered(
            lambda s: s.subject_type == 'compulsory'
        )

        try:
            reg = env['op.subject.registration'].create({
                'student_id': sc.student_id.id,
                'course_id': sc.course_id.id,
                'batch_id': sc.batch_id.id,
                'compulsory_subject_ids': [(6, 0, compulsory_subjects.ids)],
                'state': 'draft',
            })
            reg.action_submitted()
            reg.action_approve()
            created += 1
        except Exception as e:
            print(f"  ERROR student={sc.student_id.name} course={sc.course_id.name}: {e}")
            errors += 1

    cr.commit()
    print(f"\nDone: {created} created, {skipped} skipped, {errors} errors")
