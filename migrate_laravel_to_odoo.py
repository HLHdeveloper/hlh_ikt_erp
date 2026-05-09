#!/usr/bin/env python3
"""
Migración de datos Laravel (MySQL) → Odoo OpenEducat (PostgreSQL)
Base de datos origen: laravel @ 192.168.1.103 (SOLO LECTURA)
Base de datos destino: kudeaketa @ postgres19

Mapeo:
  IKASTURTEA   → op_academic_year
  MINTEGIAK    → op_department
  ZIKLOAK      → op_course  (vinculado a departamento)
  TALDEAK      → op_batch   (vinculado a course)
  GELAK        → op_classroom
  IRAKASLEAK   → res_partner + op_faculty
  IKASLEAK     → res_partner + op_student
  MATRIKULA    → op_student_course
  IRAKASLEAK_TALDEAK → op_department_op_faculty_rel
"""

import json
import pymysql
import psycopg2
import psycopg2.extras
import sys
from datetime import date, datetime

# ── Conexiones ──────────────────────────────────────────────────────────────

MYSQL_CFG = dict(
    host='192.168.1.103', port=3306,
    user='sail', password='password',
    database='laravel',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor,
)

PG_CFG = dict(
    host='postgres19', port=5432,
    user='odoo', password='odoo123',
    dbname='kudeaketa',
)

ADMIN_UID  = 2   # ikt@hernanilanh.eus
COMPANY_ID = 1   # CIFP GIZARTE BERRIKUNTZA

# Año académico origen
IKASTURTEA = '25_26'
AY_NAME    = '2025-2026'
AY_START   = date(2025, 9, 1)
AY_END     = date(2026, 6, 30)

# ── Helpers ──────────────────────────────────────────────────────────────────

def now_ts():
    return datetime.now()

def log(msg):
    print(f"  → {msg}")

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("\nConectando a MySQL (SOLO LECTURA)...")
    my = pymysql.connect(**MYSQL_CFG)
    mc = my.cursor()

    print("Conectando a PostgreSQL (Odoo kudeaketa)...")
    pg = psycopg2.connect(**PG_CFG)
    pc = pg.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        migrate_academic_year(mc, pc)
        pg.commit()

        dept_map = migrate_departments(mc, pc)
        pg.commit()

        course_map = migrate_courses(mc, pc, dept_map)
        pg.commit()

        batch_map = migrate_batches(mc, pc, course_map)
        pg.commit()

        migrate_classrooms(mc, pc, course_map, batch_map)
        pg.commit()

        faculty_map = migrate_faculty(mc, pc, dept_map)
        pg.commit()

        student_map = migrate_students(mc, pc)
        pg.commit()

        migrate_enrollments(mc, pc, student_map, course_map, batch_map)
        pg.commit()

        migrate_faculty_batches(mc, pc, faculty_map, dept_map)
        pg.commit()

        kargu_map = migrate_karguak(mc, pc)
        pg.commit()

        greba_map = migrate_grebak(mc, pc)
        pg.commit()

        migrate_faculty_kargu(mc, pc, faculty_map, kargu_map)
        pg.commit()

        migrate_faculty_greba(mc, pc, faculty_map, greba_map)
        pg.commit()

        migrate_faculty_batch_direct(mc, pc, faculty_map, batch_map)
        pg.commit()

        migrate_ordezkapenak(mc, pc, faculty_map)
        pg.commit()

        print("\n" + "="*60)
        print("  MIGRACIÓN COMPLETADA CON ÉXITO")
        print("="*60)

    except Exception as e:
        pg.rollback()
        print(f"\n[ERROR] {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)
    finally:
        my.close()
        pg.close()


# ── 1. Año académico ─────────────────────────────────────────────────────────

def migrate_academic_year(mc, pc):
    section("1. Año académico (IKASTURTEA → op_academic_year)")

    pc.execute("SELECT id FROM op_academic_year WHERE name = %s", (AY_NAME,))
    row = pc.fetchone()
    if row:
        log(f"Ya existe: '{AY_NAME}' (id={row['id']})")
        return row['id']

    pc.execute("""
        INSERT INTO op_academic_year
            (company_id, create_uid, write_uid, name, term_structure,
             start_date, end_date, create_boolean, create_date, write_date)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
    """, (COMPANY_ID, ADMIN_UID, ADMIN_UID, AY_NAME, 'semester',
          AY_START, AY_END, False, now_ts(), now_ts()))
    ay_id = pc.fetchone()[0]
    log(f"Creado año académico '{AY_NAME}' (id={ay_id})")
    return ay_id


# ── 2. Departamentos (MINTEGIAK → op_department) ─────────────────────────────

def migrate_departments(mc, pc):
    section("2. Departamentos (MINTEGIAK → op_department)")

    mc.execute("SELECT mIZ, izena FROM MINTEGIAK")
    rows = mc.fetchall()

    dept_map = {}  # mIZ → op_department.id

    for r in rows:
        miz  = r['mIZ']
        name = r['izena']
        code = miz.replace('MINTEGIA-', '')[:16]

        pc.execute("SELECT id FROM op_department WHERE code = %s", (code,))
        existing = pc.fetchone()
        if existing:
            dept_map[miz] = existing['id']
            log(f"Ya existe departamento '{name}' (code={code})")
            continue

        pc.execute("""
            INSERT INTO op_department
                (create_uid, write_uid, name, code, create_date, write_date)
            VALUES (%s,%s,%s,%s,%s,%s)
            RETURNING id
        """, (ADMIN_UID, ADMIN_UID, name, code, now_ts(), now_ts()))
        dept_id = pc.fetchone()[0]
        dept_map[miz] = dept_id
        log(f"Departamento creado: '{name}' (code={code}, id={dept_id})")

    return dept_map


# ── 3. Cursos/Ciclos (ZIKLOAK → op_course) ───────────────────────────────────

def migrate_courses(mc, pc, dept_map):
    section("3. Ciclos formativos (ZIKLOAK → op_course)")

    mc.execute("SELECT zIZ, mIZ FROM ZIKLOAK")
    rows = mc.fetchall()

    course_map = {}  # zIZ → op_course.id

    for r in rows:
        ziz  = r['zIZ']
        miz  = r['mIZ']
        code = ziz[:16]
        dept_id = dept_map.get(miz)

        pc.execute("SELECT id, department_id FROM op_course WHERE code = %s", (code,))
        existing = pc.fetchone()
        if existing:
            course_map[ziz] = existing['id']
            if dept_id and not existing['department_id']:
                pc.execute("""
                    UPDATE op_course SET department_id = %s, write_date = %s WHERE id = %s
                """, (dept_id, now_ts(), existing['id']))
                log(f"Ciclo '{ziz}' actualizado: department_id={dept_id}")
            else:
                log(f"Ya existe ciclo '{ziz}'")
            continue

        pc.execute("""
            INSERT INTO op_course
                (department_id, create_uid, write_uid, name, code,
                 evaluation_type, active, create_date, write_date)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
        """, (dept_id, ADMIN_UID, ADMIN_UID, ziz, code,
              'marks', True, now_ts(), now_ts()))
        course_id = pc.fetchone()[0]
        course_map[ziz] = course_id
        log(f"Ciclo creado: '{ziz}' (dept={miz}, id={course_id})")

    return course_map


# ── 4. Grupos/Batches (TALDEAK → op_batch) ────────────────────────────────────

def migrate_batches(mc, pc, course_map):
    section("4. Grupos (TALDEAK → op_batch)")

    mc.execute("SELECT tIZ, zIZ FROM TALDEAK")
    rows = mc.fetchall()

    batch_map = {}  # tIZ → op_batch.id

    for r in rows:
        tiz  = r['tIZ']
        ziz  = r['zIZ']
        code = tiz[:16]
        course_id = course_map.get(ziz)

        if not course_id:
            log(f"AVISO: Ciclo '{ziz}' no encontrado para grupo '{tiz}', saltando.")
            continue

        pc.execute("SELECT id FROM op_batch WHERE code = %s", (code,))
        existing = pc.fetchone()
        if existing:
            batch_map[tiz] = existing['id']
            log(f"Ya existe grupo '{tiz}'")
            continue

        pc.execute("""
            INSERT INTO op_batch
                (course_id, create_uid, write_uid, code, name,
                 start_date, end_date, active, create_date, write_date)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
        """, (course_id, ADMIN_UID, ADMIN_UID, code, tiz,
              AY_START, AY_END, True, now_ts(), now_ts()))
        batch_id = pc.fetchone()[0]
        batch_map[tiz] = batch_id
        log(f"Grupo creado: '{tiz}' (ciclo={ziz}, id={batch_id})")

    return batch_map


# ── 5. Aulas (GELAK → op_classroom) ──────────────────────────────────────────

def migrate_classrooms(mc, pc, course_map, batch_map):
    section("5. Aulas (GELAK → op_classroom)")

    mc.execute("SELECT id, kodea, izena, kodeIzena FROM GELAK")
    rows = mc.fetchall()

    pc.execute("SELECT code, name FROM op_classroom")
    existing_classrooms = pc.fetchall()
    existing_codes  = {r[0] for r in existing_classrooms}
    existing_names  = {r[1] for r in existing_classrooms}

    # name_counter para desduplicar nombres truncados
    name_count = {}

    created = 0
    for r in rows:
        code = r['kodea'][:8]
        if code in existing_codes:
            continue

        base_name = r['izena'][:16]
        # Desduplicar nombre si ya existe
        name = base_name
        if name in existing_names or name in name_count:
            suffix = name_count.get(base_name, 1)
            name = base_name[:14] + f"-{suffix}"
            name_count[base_name] = suffix + 1
        else:
            name_count[base_name] = 1

        if name in existing_names:
            log(f"AVISO: Aula '{r['izena']}' (code={code}) nombre duplicado irresoluble, saltando.")
            continue

        pc.execute("""
            INSERT INTO op_classroom
                (create_uid, write_uid, name, code, active, create_date, write_date)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (ADMIN_UID, ADMIN_UID, name, code, True, now_ts(), now_ts()))
        existing_codes.add(code)
        existing_names.add(name)
        created += 1

    log(f"Aulas creadas: {created} (existían: {len(rows)-created})")


# ── 6. Profesores (IRAKASLEAK → res_partner + op_faculty) ────────────────────

def migrate_faculty(mc, pc, dept_map):
    section("6. Profesores (IRAKASLEAK → res_partner + op_faculty)")

    mc.execute("""
        SELECT id, irNAN, izena, abizena1, abizena2,
               emailLanekoa, emailPertsonala, telefonoa,
               helbidea, posta_kodea, herrialdea,
               suspenditua, hasieraData
        FROM IRAKASLEAK
    """)
    rows = mc.fetchall()

    # Mapa de dept para facultad: irakaslea_id → [mIZ list]
    mc.execute("""
        SELECT mi.irakaslea_id, mi.mIZ
        FROM MINTEGI_IRAKASLE mi
    """)
    faculty_depts = {}
    for fd in mc.fetchall():
        faculty_depts.setdefault(fd['irakaslea_id'], []).append(fd['mIZ'])

    faculty_map = {}  # irakaslea.id → op_faculty.id
    created = skipped = 0

    for r in rows:
        email = r['emailLanekoa']
        if not email:
            log(f"AVISO: Profesor id={r['id']} sin email, saltando.")
            skipped += 1
            continue

        name = f"{r['izena']} {r['abizena1']}"
        if r['abizena2']:
            name += f" {r['abizena2']}"

        # Verificar si ya existe partner con ese email
        pc.execute("SELECT id FROM res_partner WHERE email = %s LIMIT 1", (email,))
        partner_row = pc.fetchone()

        if partner_row:
            partner_id = partner_row['id']
        else:
            pc.execute("""
                INSERT INTO res_partner
                    (company_id, create_uid, write_uid, name, email, phone,
                     street, zip, active, is_company,
                     create_date, write_date)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING id
            """, (COMPANY_ID, ADMIN_UID, ADMIN_UID,
                  name, email, r['telefonoa'],
                  r['helbidea'], r['posta_kodea'],
                  not bool(r['suspenditua']), False,
                  now_ts(), now_ts()))
            partner_id = pc.fetchone()[0]

        # Verificar si ya existe op_faculty con ese partner
        pc.execute("SELECT id FROM op_faculty WHERE partner_id = %s LIMIT 1", (partner_id,))
        fac_row = pc.fetchone()

        if fac_row:
            faculty_map[r['id']] = fac_row['id']
            skipped += 1
            continue

        # Departamento principal (primer mintegi)
        miz_list = faculty_depts.get(r['id'], [])
        main_dept_id = dept_map.get(miz_list[0]) if miz_list else None

        # birth_date obligatorio en op_faculty → usamos placeholder si falta
        birth_date = r.get('hasieraData') or date(1980, 1, 1)

        fn = r['izena']
        first_name_json = json.dumps({"es": fn, "eu": fn})

        pc.execute("""
            INSERT INTO op_faculty
                (partner_id, main_department_id, create_uid, write_uid,
                 first_name, last_name, middle_name,
                 gender, birth_date, id_number,
                 active, create_date, write_date)
            VALUES (%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
        """, (partner_id, main_dept_id, ADMIN_UID, ADMIN_UID,
              first_name_json,
              r['abizena1'],
              r['abizena2'] or '',
              'male',        # género requerido; dato no disponible
              birth_date,
              r['irNAN'] or '',
              not bool(r['suspenditua']),
              now_ts(), now_ts()))
        fac_id = pc.fetchone()[0]
        faculty_map[r['id']] = fac_id

        # Asociar a todos sus departamentos
        for miz in miz_list:
            d_id = dept_map.get(miz)
            if d_id:
                pc.execute("""
                    INSERT INTO op_department_op_faculty_rel
                        (op_department_id, op_faculty_id)
                    VALUES (%s,%s)
                    ON CONFLICT DO NOTHING
                """, (d_id, fac_id))

        created += 1

    log(f"Profesores creados: {created} | ya existían/saltados: {skipped}")
    return faculty_map


# ── 7. Alumnos (IKASLEAK → res_partner + op_student) ─────────────────────────

def migrate_students(mc, pc):
    section("7. Alumnos (IKASLEAK → res_partner + op_student)")

    mc.execute("""
        SELECT id, ikDIE, ikNAN, izena, abizena1, abizena2,
               emailLanekoa, jaiotze_data, telefonoa,
               helbidea, posta_kodea, suspenditua, tIZ
        FROM IKASLEAK
    """)
    rows = mc.fetchall()

    student_map = {}  # ikasleak.id → op_student.id
    created = skipped = 0

    for r in rows:
        email = r['emailLanekoa']
        if not email:
            skipped += 1
            continue

        name = f"{r['izena']} {r['abizena1']}"
        if r['abizena2']:
            name += f" {r['abizena2']}"

        pc.execute("SELECT id FROM res_partner WHERE email = %s LIMIT 1", (email,))
        partner_row = pc.fetchone()

        if partner_row:
            partner_id = partner_row['id']
        else:
            pc.execute("""
                INSERT INTO res_partner
                    (company_id, create_uid, write_uid, name, email, phone,
                     street, zip, active, is_company,
                     create_date, write_date)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING id
            """, (COMPANY_ID, ADMIN_UID, ADMIN_UID,
                  name, email, r['telefonoa'],
                  r['helbidea'], r['posta_kodea'],
                  not bool(r['suspenditua']), False,
                  now_ts(), now_ts()))
            partner_id = pc.fetchone()[0]

        pc.execute("SELECT id FROM op_student WHERE partner_id = %s LIMIT 1", (partner_id,))
        stu_row = pc.fetchone()

        if stu_row:
            student_map[r['id']] = stu_row['id']
            skipped += 1
            continue

        # gr_no único: usamos ikDIE o generamos uno
        gr_no = r['ikDIE'] or f"IK{r['id']:06d}"
        # Verificar unicidad
        pc.execute("SELECT id FROM op_student WHERE gr_no = %s LIMIT 1", (gr_no,))
        if pc.fetchone():
            gr_no = f"IK{r['id']:06d}"

        fn = r['izena']
        ln = r['abizena1']
        first_name_json  = json.dumps({"es": fn, "eu": fn})
        last_name_json   = json.dumps({"es": ln, "eu": ln})
        middle_name_json = 'null'
        if r['abizena2']:
            mn = r['abizena2']
            middle_name_json = json.dumps({"es": mn, "eu": mn})

        pc.execute("""
            INSERT INTO op_student
                (partner_id, create_uid, write_uid,
                 first_name, last_name, middle_name,
                 gender, birth_date, id_number, gr_no,
                 active, create_date, write_date)
            VALUES (%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
        """, (partner_id, ADMIN_UID, ADMIN_UID,
              first_name_json, last_name_json, middle_name_json,
              'male',
              r['jaiotze_data'],
              r['ikNAN'] or '',
              gr_no,
              not bool(r['suspenditua']),
              now_ts(), now_ts()))
        stu_id = pc.fetchone()[0]
        student_map[r['id']] = stu_id
        created += 1

    log(f"Alumnos creados: {created} | ya existían/saltados: {skipped}")
    return student_map


# ── 8. Matrículas (MATRIKULA → op_student_course) ────────────────────────────

def migrate_enrollments(mc, pc, student_map, course_map, batch_map):
    section("8. Matrículas (MATRIKULA → op_student_course)")

    # Obtener id del año académico ya creado
    pc.execute("SELECT id FROM op_academic_year WHERE name = %s", (AY_NAME,))
    ay = pc.fetchone()
    ay_id = ay['id'] if ay else None

    mc.execute("""
        SELECT ikasle_id, tIZ, ikasturtea, matrikulaData, egoera
        FROM MATRIKULA
        WHERE ikasturtea = %s
    """, (IKASTURTEA,))
    rows = mc.fetchall()

    created = skipped = 0

    for r in rows:
        stu_id = student_map.get(r['ikasle_id'])
        tiz = r['tIZ']

        if not stu_id:
            skipped += 1
            continue

        # Buscar ciclo a partir del tIZ del grupo
        mc.execute("SELECT zIZ FROM TALDEAK WHERE tIZ = %s", (tiz,))
        taldea = mc.fetchone()
        if not taldea:
            skipped += 1
            continue

        course_id = course_map.get(taldea['zIZ'])
        batch_id  = batch_map.get(tiz)

        if not course_id:
            skipped += 1
            continue

        # Estado
        estado_map = {
            'matrikulatua': 'studying',
            'amaitua':      'alumni',
            'baja':         'cancelled',
        }
        state = estado_map.get(r['egoera'], 'studying')

        # Verificar unicidad
        pc.execute("""
            SELECT id FROM op_student_course
            WHERE student_id=%s AND course_id=%s AND batch_id IS NOT DISTINCT FROM %s
            LIMIT 1
        """, (stu_id, course_id, batch_id))
        if pc.fetchone():
            skipped += 1
            continue

        roll_no = f"{tiz}-{r['ikasle_id']:04d}"

        pc.execute("""
            INSERT INTO op_student_course
                (student_id, course_id, batch_id, academic_years_id,
                 roll_number, state, create_uid, write_uid, create_date, write_date)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (stu_id, course_id, batch_id, ay_id,
              roll_no, state, ADMIN_UID, ADMIN_UID, now_ts(), now_ts()))
        created += 1

    log(f"Matrículas creadas: {created} | saltadas: {skipped}")


# ── 9. Profesores ↔ Grupos (IRAKASLEAK_TALDEAK) ───────────────────────────────

def migrate_faculty_batches(mc, pc, faculty_map, dept_map):
    section("9. Asignación profesores-grupos (IRAKASLEAK_TALDEAK → op_department_op_faculty_rel)")

    # Aquí vinculamos profesores a departamentos via los grupos a los que pertenecen
    mc.execute("""
        SELECT it.irakaslea_id, t.zIZ
        FROM IRAKASLEAK_TALDEAK it
        JOIN TALDEAK t ON t.tIZ = it.tIZ
    """)
    rows = mc.fetchall()

    # Mapa zIZ → mIZ (departamento del ciclo)
    mc.execute("SELECT zIZ, mIZ FROM ZIKLOAK")
    ziz_to_miz = {r['zIZ']: r['mIZ'] for r in mc.fetchall()}

    added = skipped = 0
    for r in rows:
        fac_id = faculty_map.get(r['irakaslea_id'])
        miz    = ziz_to_miz.get(r['zIZ'])
        dept_id = dept_map.get(miz) if miz else None

        if not fac_id or not dept_id:
            skipped += 1
            continue

        pc.execute("""
            INSERT INTO op_department_op_faculty_rel (op_department_id, op_faculty_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """, (dept_id, fac_id))
        added += 1

    log(f"Vínculos profesor-departamento procesados: {added} | saltados: {skipped}")


# ── 10. Cargos (KARGUAK → op.kargu) ──────────────────────────────────────────

def migrate_karguak(mc, pc):
    section("10. Cargos (KARGUAK → op.kargu)")

    mc.execute("SELECT karguIZ, gsuite_email, izena FROM KARGUAK")
    rows = mc.fetchall()

    kargu_map = {}  # karguIZ → op.kargu.id
    created = skipped = 0

    for r in rows:
        code = r['karguIZ']
        pc.execute("SELECT id FROM op_kargu WHERE code = %s", (code,))
        existing = pc.fetchone()
        if existing:
            kargu_map[code] = existing['id']
            skipped += 1
            continue

        pc.execute("""
            INSERT INTO op_kargu (code, name, gsuite_email, create_uid, write_uid, create_date, write_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (code, r['izena'] or code, r['gsuite_email'],
              ADMIN_UID, ADMIN_UID, now_ts(), now_ts()))
        kargu_map[code] = pc.fetchone()[0]
        created += 1

    log(f"Cargos creados: {created} | ya existían: {skipped}")
    return kargu_map


# ── 11. Huelgas (IR_GREBAK → op.greba) ───────────────────────────────────────

def migrate_grebak(mc, pc):
    section("11. Huelgas (IR_GREBAK → op.greba)")

    mc.execute("SELECT irGREBA, grebaData, arrazoia FROM IR_GREBAK")
    rows = mc.fetchall()

    greba_map = {}  # irGREBA → op.greba.id
    created = skipped = 0

    for r in rows:
        code = r['irGREBA']
        pc.execute("SELECT id FROM op_greba WHERE code = %s", (code,))
        existing = pc.fetchone()
        if existing:
            greba_map[code] = existing['id']
            skipped += 1
            continue

        pc.execute("""
            INSERT INTO op_greba (code, date, reason, faculty_count, create_uid, write_uid, create_date, write_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (code, r['grebaData'], r['arrazoia'], 0,
              ADMIN_UID, ADMIN_UID, now_ts(), now_ts()))
        greba_map[code] = pc.fetchone()[0]
        created += 1

    log(f"Huelgas creadas: {created} | ya existían: {skipped}")
    return greba_map


# ── 12. Profesor ↔ Cargo (IRAKASLE_KARGU → op_faculty_kargu_rel) ─────────────

def migrate_faculty_kargu(mc, pc, faculty_map, kargu_map):
    section("12. Cargos de profesores (IRAKASLE_KARGU → op_faculty_kargu_rel)")

    mc.execute("SELECT irakaslea_id, karguIZ FROM IRAKASLE_KARGU")
    rows = mc.fetchall()

    added = skipped = 0
    for r in rows:
        fac_id   = faculty_map.get(r['irakaslea_id'])
        kargu_id = kargu_map.get(r['karguIZ'])
        if not fac_id or not kargu_id:
            skipped += 1
            continue
        pc.execute("""
            INSERT INTO op_faculty_kargu_rel (faculty_id, kargu_id)
            VALUES (%s, %s) ON CONFLICT DO NOTHING
        """, (fac_id, kargu_id))
        added += 1

    log(f"Vínculos profesor-cargo: {added} | saltados: {skipped}")


# ── 13. Profesor ↔ Huelga (IRAKASLEAK_GREBAK → op_faculty_greba_rel) ─────────

def migrate_faculty_greba(mc, pc, faculty_map, greba_map):
    section("13. Participación en huelgas (IRAKASLEAK_GREBAK → op_faculty_greba_rel)")

    mc.execute("SELECT irakaslea_id, irGREBA FROM IRAKASLEAK_GREBAK")
    rows = mc.fetchall()

    added = skipped = 0
    for r in rows:
        fac_id  = faculty_map.get(r['irakaslea_id'])
        greb_id = greba_map.get(r['irGREBA'])
        if not fac_id or not greb_id:
            skipped += 1
            continue
        pc.execute("""
            INSERT INTO op_faculty_greba_rel (faculty_id, greba_id)
            VALUES (%s, %s) ON CONFLICT DO NOTHING
        """, (fac_id, greb_id))
        added += 1

    log(f"Vínculos profesor-huelga: {added} | saltados: {skipped}")

    # Recalcular faculty_count en todas las huelgas
    pc.execute("""
        UPDATE op_greba g
        SET faculty_count = (
            SELECT COUNT(*) FROM op_faculty_greba_rel WHERE greba_id = g.id
        )
    """)
    log("faculty_count actualizado en op_greba")


# ── 14. Profesor ↔ Grupo directo (IRAKASLEAK_TALDEAK → op_faculty_batch_rel) ──

def migrate_faculty_batch_direct(mc, pc, faculty_map, batch_map):
    section("14. Grupos por profesor (IRAKASLEAK_TALDEAK → op_faculty_batch_rel)")

    mc.execute("SELECT irakaslea_id, tIZ FROM IRAKASLEAK_TALDEAK")
    rows = mc.fetchall()

    added = skipped = 0
    for r in rows:
        fac_id   = faculty_map.get(r['irakaslea_id'])
        batch_id = batch_map.get(r['tIZ'])
        if not fac_id or not batch_id:
            skipped += 1
            continue
        pc.execute("""
            INSERT INTO op_faculty_batch_rel (faculty_id, batch_id)
            VALUES (%s, %s) ON CONFLICT DO NOTHING
        """, (fac_id, batch_id))
        added += 1

    log(f"Vínculos profesor-grupo: {added} | saltados: {skipped}")


# ── 15. Sustituciones (ORDEZKAPENAK → op.ordezkapen) ─────────────────────────

def migrate_ordezkapenak(mc, pc, faculty_map):
    section("15. Sustituciones (ORDEZKAPENAK → op.ordezkapen)")

    # Registros de MySQL con datos erróneos (roles invertidos u otros errores confirmados)
    MYSQL_IDS_EXCLUIDOS = {10}  # id=10: FRANCO como titular y BUENO como sustituto (roles invertidos)

    mc.execute("""
        SELECT id, titular_id, ordezko_id, hasieraData, bukaeraData, oharrak
        FROM ORDEZKAPENAK
    """)
    rows = mc.fetchall()

    created = skipped = 0
    for r in rows:
        if r['id'] in MYSQL_IDS_EXCLUIDOS:
            skipped += 1
            continue
        titular_id = faculty_map.get(r['titular_id'])
        ordezko_id = faculty_map.get(r['ordezko_id'])
        if not titular_id or not ordezko_id:
            skipped += 1
            continue
        if titular_id == ordezko_id:
            skipped += 1
            continue

        pc.execute("""
            SELECT id, end_date FROM op_ordezkapen
            WHERE titular_id = %s AND start_date = %s
        """, (titular_id, r['hasieraData']))
        existing = pc.fetchone()
        if existing:
            if existing['end_date'] != r['bukaeraData']:
                pc.execute("""
                    UPDATE op_ordezkapen SET end_date = %s, write_date = %s
                    WHERE id = %s
                """, (r['bukaeraData'], now_ts(), existing['id']))
            skipped += 1
            continue

        pc.execute("""
            INSERT INTO op_ordezkapen
                (titular_id, ordezko_id, start_date, end_date, notes,
                 create_uid, write_uid, create_date, write_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (titular_id, ordezko_id,
              r['hasieraData'], r['bukaeraData'], r['oharrak'],
              ADMIN_UID, ADMIN_UID, now_ts(), now_ts()))
        created += 1

    log(f"Sustituciones creadas: {created} | saltadas: {skipped}")


if __name__ == '__main__':
    main()
