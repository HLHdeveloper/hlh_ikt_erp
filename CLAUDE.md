# CIFP Gizarte Berrikuntza LHII — Odoo OpenEducat

Gestión del centro educativo CIFP Gizarte Berrikuntza LHII (Hernani) con Odoo 17 + OpenEducat.

## Stack

- **Odoo 17.0** en Docker (`odoo19`), puerto 8069
- **PostgreSQL 15** en Docker (`postgres19`), base de datos `kudeaketa`
- **MySQL** externo en `192.168.1.103:3306`, base de datos `laravel` — SOLO LECTURA (origen de datos)

## Credenciales

| Servicio | Usuario | Contraseña | BD |
|---|---|---|---|
| Odoo (admin) | `ikt@hernanilanh.eus` | `odoo123` | kudeaketa |
| PostgreSQL | `odoo` | `odoo123` | kudeaketa |
| MySQL (origen) | `sail` | `password` | laravel |

## Comandos habituales

```bash
# Actualizar módulo personalizado
docker exec odoo19 odoo -u openeducat_hernani -d kudeaketa --stop-after-init

# Relanzar Odoo tras actualización
docker start odoo19

# Relanzar Odoo cuando se añade un directorio static/ nuevo al módulo
# (docker start es no-op si el contenedor ya corre; hay que hacer restart
# para que Odoo recompute el lazy_property `statics` y sirva los assets)
docker restart odoo19

# Ejecutar migración de datos (idempotente)
docker cp migrate_laravel_to_odoo.py odoo19:/tmp/
docker exec odoo19 python3 /tmp/migrate_laravel_to_odoo.py

# Importar traducciones Basque (si se modifica eu_ES.po)
docker exec odoo19 odoo -u openeducat_hernani -d kudeaketa --stop-after-init
# Para parchear campos de módulos base sin eu_ES (patch scripts en raíz del proyecto):
docker cp patch_eu_translations.py odoo19:/tmp/ && docker exec odoo19 python3 /tmp/patch_eu_translations.py
docker cp patch_menus.py odoo19:/tmp/         && docker exec odoo19 python3 /tmp/patch_menus.py

# Logs en tiempo real
docker compose logs -f odoo19

# Shell psql
docker exec -it postgres19 psql -U odoo -d kudeaketa
```

## Módulo personalizado: openeducat_hernani

Ruta: `addons19/openeducat_erp/openeducat_hernani/`

### Modelos propios
| Modelo | Tabla MySQL origen | Descripción |
|---|---|---|
| `op.kargu` | `KARGUAK` + `IRAKASLE_KARGU` | Cargos de profesores |
| `op.greba` | `IRAKASLEAK_GREBAK` | Huelgas de profesores |
| `op.ordezkapen` | `ORDEZKAPENAK` | Sustituciones entre profesores |
| `op.report.batch.student` | — (SQL view) | Informe: ikasleak taldeka |
| `op.report.dept.faculty` | — (SQL view) | Informe: irakasleak mintegika |
| `op.report.dept.greba` | — (SQL view) | Informe: grebak mintegika |
| `op.report.dept.ordezkapen` | — (SQL view) | Informe: ordezkapenak mintegika |
| `op.report.faculty.greba` | — (SQL view) | Informe: irakasleak greba kopuruaren arabera |

### Extensiones de modelos OpenEducat
| Modelo extendido | Campos añadidos |
|---|---|
| `op.faculty` | `kargu_ids`, `greba_ids`, `batch_ids`, `titular_ordezkapen_ids`, `ordezko_ordezkapen_ids` |
| `op.batch` | `faculty_ids`, `student_course_ids` |
| `op.department` | `course_ids`, `faculty_ids` |

### Menú SIS (orden actual)
```
[10] Mintegiak        → op.department
[20] Irakasleak       → op.faculty
[30] Taldeak          → op.batch
[40] Moduluak         → op.subject
[50] Ikasleak         → op.student
[60] General
[70] Reporting
      [10] Ikasleak taldeka                    → op.report.batch.student
      [20] Irakasleak mintegika                → op.report.dept.faculty
      [30] Grebak mintegika                    → op.report.dept.greba
      [35] Ordezkapenak mintegika              → op.report.dept.ordezkapen
      [40] Irakasleak greba kopuruaren arabera → op.report.faculty.greba
[80] Konfigurazioa
```

## Migración de datos (migrate_laravel_to_odoo.py)

Script idempotente (829 líneas). Mapeo principal:

| Tabla MySQL | Modelo Odoo |
|---|---|
| `IKASTURTEA` | `op_academic_year` |
| `MINTEGIAK` | `op_department` |
| `ZIKLOAK` | `op_course` |
| `TALDEAK` | `op_batch` |
| `GELAK` | `op_classroom` |
| `IRAKASLEAK` | `res_partner` + `op_faculty` |
| `IKASLEAK` | `res_partner` + `op_student` |
| `MATRIKULA` | `op_student_course` |
| `KARGUAK` | `op_kargu` |
| `IRAKASLEAK_GREBAK` | `op_greba` |
| `IRAKASLE_KARGU` | `op_faculty_kargu_rel` |
| `ORDEZKAPENAK` | `op_ordezkapen` |
| `IRAKASLEAK_TALDEAK` | `op_faculty_batch_rel` + `op_department_op_faculty_rel` |

## Datos migrados (estado actual)

| Entidad | Total | Activos |
|---|---|---|
| Año académico | 1 (2025-2026) | — |
| Departamentos | 8 | — |
| Ciclos | 13 | — |
| Grupos | 32 | 30 |
| Aulas | 63 | — |
| Profesores | 359 | 113 |
| Alumnos | 641 | 278 |
| Matrículas | 267 | — |
| Matrículas (`op.subject.registration`) | 271 | approved |
| Cargos | 66 | — |
| Huelgas | 1 | — |
| Sustituciones | 23 | — |

## Terminología (euskera → español)

| Euskera | Español |
|---|---|
| Ikasturtea | Año académico |
| Mintegiak | Departamentos |
| Irakasleak | Profesores |
| Taldeak | Grupos |
| Moduluak | Asignaturas/Módulos |
| Ikasleak | Alumnos |
| Karguak | Cargos |
| Grebak | Huelgas |
| Ordezkapenak | Sustituciones |
| Zikloak | Ciclos formativos |
| Gelak | Aulas |
| Gurasoak | Padres/Tutores |
| suspenditua=1 | Inactivo/Dado de baja |

## Traducciones al euskera (eu_ES)

El idioma `eu_ES` está activo y configurado como idioma del usuario admin.

### Arquitectura de traducciones en Odoo 17
En Odoo 17 **no existe tabla `ir_translation`**. Las traducciones se almacenan como JSON directamente en cada registro:
- Nombres de campo: `ir_model_fields.field_description` → `{"en_US": "Email", "eu_ES": "Helbide elektronikoa"}`
- Menús: `ir_ui_menu.name` → `{"en_US": "Settings", "eu_ES": "Ezarpenak"}`
- Acciones: `ir_act_window.name` → `{"en_US": "Class Rooms", "eu_ES": "Gelak"}`

### Fichero de traducciones del módulo
`addons19/openeducat_erp/openeducat_hernani/i18n/eu_ES.po`
- Generado con `python3 make_eu_po.py` (usa el POT exportado como base con los comentarios de módulo requeridos)
- **El .po debe contener los comentarios `#. module:` y `#:` de ocurrencia** o `TranslationFileReader` lanza `AttributeError: 'NoneType'.groups()`
- Se carga automáticamente al hacer `-u openeducat_hernani`

### Scripts de parcheo de traducciones base
Los módulos base de Odoo (`base`, `mail`, etc.) no tienen eu_ES. Se parchean directamente en BD:
- `patch_eu_translations.py` — traduce `ir_model_fields` (campos: Email, Phone, Active, Street…)
- `patch_menus.py` — traduce `ir_ui_menu` y `ir_act_window` (todos los menús incluido el menú de 9 cuadritos)

Tras ejecutar los scripts, hacer `docker restart odoo19` para limpiar caché.

### Exportar template de traducciones
```bash
docker exec odoo19 odoo --i18n-export=/tmp/openeducat_eu.pot \
  --modules=openeducat_core,openeducat_classroom,openeducat_parent,openeducat_hernani \
  -d kudeaketa -l eu_ES --stop-after-init
docker cp odoo19:/tmp/openeducat_eu.pot ./openeducat_eu.pot
python3 make_eu_po.py   # rellena msgstr y genera i18n/eu_ES.po
```

## Matrícula de módulos (op.subject.registration)

271 registros `op.subject.registration` en estado `approved` creados con `enroll_students.py`.
Flujo: student_course (studying) → subject_registration (draft→submitted→approved) → subject_ids en op_student_course_op_subject_rel.
Los sujetos compulsory vienen de `op_course_op_subject_rel` (todos son `subject_type='compulsory'`).

## Informes (Reporting)

Los informes usan modelos con `_auto = False` respaldados por vistas SQL de PostgreSQL.
Vistas creadas en `models/op_report.py`, vistas XML en `views/op_report_views.xml`.
Todos son de solo lectura (`perm_read=1`, resto=0 en `security/ir.model.access.csv`).

Cada informe tiene vistas **tree + graph (bar) + pivot** salvo `op.report.faculty.greba` (tree + graph).
Los informes de grebas y ordezkapenak mostrarán datos reales cuando se registren participaciones en `op.greba` y sustituciones en `op.ordezkapen`.

## Botón "Bukatu ordezkapena" (op.ordezkapen)

Botón en la **vista lista** (columna) y en la **cabecera del formulario** (`<header>`).
- Solo visible cuando `end_date` está vacío (`invisible="end_date"`)
- Al pulsar llama a `action_bukatu()` que escribe `end_date = Date.today()`
- Desaparece automáticamente tras establecer la fecha

## Notas importantes

- La BD MySQL es **SOLO LECTURA**. Nunca modificar datos en ella.
- El campo clave de unicidad de profesores y alumnos en `res_partner` es el **email**.
- `suspenditua=1` en MySQL → `active=False` en Odoo.
- Los menús de Konfigurazioa del SIS se gestionan en `views/op_sis_menu.xml`.
- Al añadir campos o modelos al módulo hernani, actualizar también `security/ir.model.access.csv`.
- `openeducat_classroom` está en `depends` del módulo hernani (necesario para la referencia XML al action de Gelak).
