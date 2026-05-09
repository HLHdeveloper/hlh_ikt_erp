# CIFP Gizarte Berrikuntza LHII — Odoo OpenEducat

Gestión del centro educativo CIFP Gizarte Berrikuntza LHII (Hernani) mediante Odoo 17 + OpenEducat.

---

## Índice

1. [Arquitectura del sistema](#arquitectura-del-sistema)
2. [Infraestructura Docker](#infraestructura-docker)
3. [Módulos OpenEducat instalados](#módulos-openeducat-instalados)
4. [Base de datos de origen (Laravel/MySQL)](#base-de-datos-de-origen-laravelmysql)
5. [Migración de datos](#migración-de-datos)
6. [Mapeo de entidades](#mapeo-de-entidades)
7. [Estructura del proyecto](#estructura-del-proyecto)
8. [Operaciones habituales](#operaciones-habituales)

---

## Arquitectura del sistema

```
┌──────────────────────────────────────────────────────┐
│                   HOST: 192.168.1.x                  │
│                                                      │
│  ┌─────────────────────┐   ┌──────────────────────┐  │
│  │   odoo19            │   │   postgres19          │  │
│  │   Odoo 17.0         │──▶│   PostgreSQL 15       │  │
│  │   :8069             │   │   :5432               │  │
│  │   + OpenEducat ERP  │   │   DB: kudeaketa       │  │
│  └─────────────────────┘   └──────────────────────┘  │
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │   MySQL (externo)   192.168.1.103:3306           │ │
│  │   DB: laravel  —  SOLO LECTURA (origen)          │ │
│  └─────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

---

## Infraestructura Docker

| Contenedor   | Imagen          | Puerto | Rol                        |
|--------------|-----------------|--------|----------------------------|
| `odoo19`     | `odoo:17.0`     | 8069   | Aplicación Odoo + OpenEducat |
| `postgres19` | `postgres:15`   | 5432   | Base de datos Odoo          |

### Credenciales

| Servicio       | Usuario | Contraseña  | Base de datos |
|----------------|---------|-------------|---------------|
| PostgreSQL      | `odoo`  | `odoo123`   | `kudeaketa`   |
| Odoo (admin)   | `ikt@hernanilanh.eus` | `admin123` | — |
| MySQL (origen) | `sail`  | `password`  | `laravel`     |

### Volúmenes

| Volumen local        | Montaje en contenedor         | Contenido                  |
|----------------------|-------------------------------|----------------------------|
| `./addons19/`        | `/mnt/extra-addons`           | Módulos OpenEducat         |
| `./config19/`        | `/etc/odoo`                   | Configuración `odoo.conf`  |
| `./odoo-data19/`     | `/var/lib/odoo`               | Ficheros adjuntos y sesiones |
| `./postgres-data19/` | `/var/lib/postgresql/data`    | Datos PostgreSQL           |

### Comandos Docker básicos

```bash
# Levantar el stack
docker compose up -d

# Ver logs en tiempo real
docker compose logs -f odoo19

# Parar sin eliminar datos
docker compose stop

# Reiniciar Odoo
docker restart odoo19

# Shell en Odoo
docker exec -it odoo19 bash

# Shell psql
docker exec -it postgres19 psql -U odoo -d kudeaketa
```

---

## Módulos OpenEducat instalados

| Módulo                    | Función                                    |
|---------------------------|--------------------------------------------|
| `openeducat_core`         | Estudiantes, profesores, cursos, grupos    |
| `openeducat_admission`    | Gestión de admisiones                      |
| `openeducat_attendance`   | Control de asistencia                      |
| `openeducat_assignment`   | Tareas y trabajos                          |
| `openeducat_exam`         | Exámenes y calificaciones                  |
| `openeducat_classroom`    | Gestión de aulas                           |
| `openeducat_timetable`    | Horarios                                   |
| `openeducat_fees`         | Gestión de tasas                           |
| `openeducat_library`      | Biblioteca                                 |
| `openeducat_facility`     | Instalaciones                              |
| `openeducat_activity`     | Actividades extracurriculares              |
| `openeducat_parent`       | Portal de padres/tutores                   |
| `web_openeducat`          | Tema web OpenEducat                        |

**Ruta de addons:** `/home/erp/openeducat-project/addons19/openeducat_erp/`

---

## Base de datos de origen (Laravel/MySQL)

**Conexión:** `192.168.1.103:3306` — base de datos `laravel`
**Política:** SOLO LECTURA. Nunca modificar ni eliminar datos de esta BD.

### Tablas y su significado (en euskera)

| Tabla MySQL           | Significado               | Registros aprox. |
|-----------------------|---------------------------|-----------------|
| `IKASTURTEA`          | Año académico             | 1               |
| `ZIKLOAK`             | Ciclos formativos         | 13              |
| `MINTEGIAK`           | Departamentos/Seminarios  | 8               |
| `TALDEAK`             | Grupos de alumnos         | 30              |
| `MODULUAK`            | Módulos/Asignaturas       | —               |
| `IRAKASLEAK`          | Profesores                | 359 (113 activos)|
| `IKASLEAK`            | Alumnos                   | 641 (278 activos)|
| `GURASOAK`            | Padres/Tutores            | —               |
| `GURASO_IKASLE`       | Relación padre-alumno     | —               |
| `MATRIKULA`           | Matrículas                | 262             |
| `GELAK`               | Aulas/Espacios            | 63              |
| `IRAKASLEAK_TALDEAK`  | Asignación profesor-grupo | —               |
| `IRAKASLEAK_GREBAK`   | Huelgas de profesores     | —               |
| `IRAKASLE_KARGU`      | Cargos de profesores      | —               |
| `KARGUAK`             | Catálogo de cargos        | —               |
| `MINTEGI_IRAKASLE`    | Profesor-Departamento     | —               |
| `ARMAIRUAK`           | Armarios/Taquillas        | —               |
| `ORDENAGAILUAK`       | Equipos informáticos      | —               |
| `ESLEIPENA_HISTORIA`  | Historial de asignaciones | —               |
| `KOKAPENA_HISTORIA`   | Historial de ubicaciones  | —               |
| `ORDEZKAPENAK`        | Sustituciones de profesores| —              |

### Claves de dominio

| Campo MySQL | Significado          |
|-------------|----------------------|
| `tIZ`       | Código de grupo      |
| `zIZ`       | Código de ciclo      |
| `mIZ`       | Código de departamento |
| `ikDIE`     | ID externo alumno    |
| `ikNAN`     | DNI alumno           |
| `irNAN`     | DNI profesor         |
| `suspenditua` | Desactivado (1=sí) |

---

## Migración de datos

**Script:** `migrate_laravel_to_odoo.py`

El script lee la BD Laravel (MySQL) y replica los datos en Odoo (PostgreSQL).
Es **idempotente**: puede ejecutarse varias veces sin duplicar datos.

### Ejecutar migración

```bash
# Copiar script al contenedor y ejecutar
docker cp migrate_laravel_to_odoo.py odoo19:/tmp/
docker exec odoo19 python3 /tmp/migrate_laravel_to_odoo.py
```

### Dependencias Python (ya instaladas en el contenedor)

```bash
pip install pymysql psycopg2-binary
```

### Orden de migración (respeta dependencias FK)

```
1. op_academic_year     ← IKASTURTEA
2. op_department        ← MINTEGIAK
3. op_course            ← ZIKLOAK          (→ department)
4. op_batch             ← TALDEAK          (→ course)
5. op_classroom         ← GELAK
6. res_partner +
   op_faculty           ← IRAKASLEAK       (→ department)
7. res_partner +
   op_student           ← IKASLEAK
8. op_student_course    ← MATRIKULA        (→ student, course, batch, academic_year)
9. op_department_
   op_faculty_rel       ← IRAKASLEAK_TALDEAK
```

---

## Mapeo de entidades

| Entidad Laravel          | Entidad Odoo                     | Notas                                      |
|--------------------------|----------------------------------|--------------------------------------------|
| `IKASTURTEA.ikasturtea`  | `op_academic_year.name`          | `25_26` → `2025-2026`                      |
| `MINTEGIAK.mIZ`          | `op_department.code`             | Se elimina prefijo `MINTEGIA-`             |
| `MINTEGIAK.izena`        | `op_department.name`             |                                            |
| `ZIKLOAK.zIZ`            | `op_course.code` + `.name`       | Vinculado al departamento via `mIZ`        |
| `TALDEAK.tIZ`            | `op_batch.code` + `.name`        | Vinculado al ciclo via `zIZ`               |
| `GELAK.kodea`            | `op_classroom.code`              | Truncado a 8 chars                         |
| `GELAK.izena`            | `op_classroom.name`              | Truncado a 16 chars                        |
| `IRAKASLEAK.emailLanekoa`| `res_partner.email`              | Clave de unicidad del partner              |
| `IRAKASLEAK.*`           | `op_faculty.*`                   | `suspenditua=1` → `active=False`           |
| `IKASLEAK.ikDIE`         | `op_student.gr_no`               | Si vacío, se genera `IK{id:06d}`           |
| `IKASLEAK.emailLanekoa`  | `res_partner.email`              | Clave de unicidad del partner              |
| `IKASLEAK.*`             | `op_student.*`                   | `suspenditua=1` → `active=False`           |
| `MATRIKULA.*`            | `op_student_course.*`            | Estado: `matrikulatua`→`studying`          |

### Estados de matrícula

| `MATRIKULA.egoera` | `op_student_course.state` |
|--------------------|---------------------------|
| `matrikulatua`     | `studying`                |
| `amaitua`          | `alumni`                  |
| `baja`             | `cancelled`               |

---

## Estructura del proyecto

```
openeducat-project/
├── docker-compose.yml              # Stack Docker (Odoo + PostgreSQL)
├── docker-compose15.yml            # Stack alternativo (versión 15)
├── migrate_laravel_to_odoo.py      # Script de migración MySQL → PostgreSQL
├── README.md                       # Este fichero
├── addons19/
│   └── openeducat_erp/             # Módulos OpenEducat
│       ├── openeducat_core/
│       ├── openeducat_admission/
│       ├── openeducat_attendance/
│       ├── openeducat_assignment/
│       ├── openeducat_classroom/
│       ├── openeducat_exam/
│       ├── openeducat_facility/
│       ├── openeducat_fees/
│       ├── openeducat_library/
│       ├── openeducat_parent/
│       ├── openeducat_timetable/
│       ├── openeducat_activity/
│       ├── openeducat_erp/
│       └── web_openeducat/
├── config19/
│   └── odoo.conf                   # Configuración Odoo
├── odoo-data19/                    # Datos de sesión y adjuntos
└── postgres-data19/                # Datos PostgreSQL
```

---

## Operaciones habituales

### Actualizar módulo OpenEducat

```bash
docker exec odoo19 odoo -u openeducat_core -d kudeaketa --stop-after-init
```

### Backup de la BD

```bash
docker exec postgres19 pg_dump -U odoo kudeaketa > backup_$(date +%Y%m%d).sql
```

### Restaurar backup

```bash
docker exec -i postgres19 psql -U odoo -d kudeaketa < backup_YYYYMMDD.sql
```

### Consultar datos migrados en PostgreSQL

```bash
# Resumen de alumnos activos por grupo
docker exec postgres19 psql -U odoo -d kudeaketa -c "
SELECT b.code AS grupo, COUNT(sc.id) AS alumnos
FROM op_student_course sc
JOIN op_batch b ON b.id = sc.batch_id
GROUP BY b.code ORDER BY b.code;
"

# Profesores por departamento
docker exec postgres19 psql -U odoo -d kudeaketa -c "
SELECT d.name AS departamento, COUNT(r.op_faculty_id) AS profesores
FROM op_department_op_faculty_rel r
JOIN op_department d ON d.id = r.op_department_id
GROUP BY d.name ORDER BY d.name;
"
```

### Re-ejecutar migración (tras cambios en Laravel)

```bash
docker cp migrate_laravel_to_odoo.py odoo19:/tmp/
docker exec odoo19 python3 /tmp/migrate_laravel_to_odoo.py
```
