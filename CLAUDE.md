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
# Actualizar módulo personalizado y relanzar el servidor web
docker exec odoo19 odoo -u openeducat_hernani -d kudeaketa --stop-after-init
docker restart odoo19
# IMPORTANTE: usar siempre `docker restart`, nunca `docker start`.
# `docker start` es no-op si el contenedor ya corre y el proceso web
# queda con la caché de menús/vistas antigua.

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
[70] Txostenak        → Dashboard OWL (sis_dashboard_action)
[80] Konfigurazioa
```

El menú Txostenak abre directamente el **SIS Dashboard** (OWL component):
- **Sección Irakasleak**: 6 tarjetas (total, funtzionarioak, ordezkoak, bajan, karguak, gainontzeko karguak)
- **Sección Ikasleak**: 1 tarjeta con drill-down 3 niveles
- Drill-down irakasleak: tarjeta → mintegiak → irakasleak / kargu types → irakasleak → formulario
- Drill-down ikasleak: tarjeta → mintegiak → taldeak → ikasleak → formulario (editable)

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
| `IRAKASLEAK_TALDEAK` | `op_faculty_batch_rel` |
| `MINTEGI_IRAKASLE` | `op_department_op_faculty_rel` |

### patch_mintegi_irakasle.py

Repuebla `op_department_op_faculty_rel` desde `MINTEGI_IRAKASLE` (membresía directa de departamento).
**Ejecutar al inicio de cada curso**, después de `migrate_laravel_to_odoo.py`.

```bash
docker cp patch_mintegi_irakasle.py odoo19:/tmp/
docker exec odoo19 python3 /tmp/patch_mintegi_irakasle.py
```

- Borra todos los registros anteriores de `op_department_op_faculty_rel`
- Reinserta desde MySQL uniendo `MINTEGI_IRAKASLE` + `IRAKASLEAK` (suspenditua=0) + `MINTEGIAK`
- El join de departamento usa `code` (mIZ sin prefijo `MINTEGIA-`), no el nombre
- Nota: MySQL `MINTEGIA-LPO` (`izena='FOL'`) → Odoo departamento `code='LPO'`

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

Botón en la **vista lista** (columna), en la **cabecera del formulario** (`<header>`) y en el **SIS Dashboard** (historial de bajas).
- Solo visible cuando `end_date` está vacío (`invisible="end_date"` en vistas Odoo)
- Al pulsar llama a `action_bukatu()` que escribe `end_date = Date.today()`
- Desaparece automáticamente tras establecer la fecha

## SIS Dashboard (OWL — `sis_dashboard_action`)

6 tarjetas Irakasleak + 1 tarjeta Ikasleak. Métodos RPC:

| Tarjeta | Nivel 1 | Nivel 2 | Nivel 3 |
|---|---|---|---|
| Irakasleak / Funtzionarioak / Ordezkoak | `get_dept_breakdown(kidergoa)` | `get_faculty_by_dept(dept_id, kidergoa)` | → form |
| Bajan daudenak | `get_bajan_depts()` | `get_bajan_faculty_by_dept(dept_id)` — titular / ordezkoa actual / kop. total | `get_bajan_history(titular_id)` — con botón "Bukatu ordezkapena" inline |
| Karguak | `get_kargu_depts()` | `get_kargu_types_for_dept(dept_id)` — MB-%, TUTO_%, DUAL | `get_faculty_for_dept_kargu(dept_id, code_pattern)` — con columna Taldea para Tutoreak |
| Gainontzeko karguak | `get_gainontzeko_kargu_types()` — karguak NOT MB/TUTO/DUAL | `get_faculty_for_gainontzeko_kargu(kargu_id)` | → form |

**Métodos RPC en `op.student`:**

| Sección | Nivel 1 | Nivel 2 | Nivel 3 |
|---|---|---|---|
| Ikasleak | `get_ikasleak_dept_breakdown()` | `get_ikasleak_batch_breakdown(dept_id)` | `get_ikasleak_by_batch(batch_id)` → form editable |

**Nota:** El contador de la tarjeta Ikasleak muestra el total de alumnos activos (278); el drill-down muestra solo los 261 que tienen matrícula activa en un taldea con departamento asignado.

**Notas de implementación:**
- `get_bajan_faculty_by_dept`: `ordezko_count` cuenta todos los sustitutos históricos (`COUNT DISTINCT` sin filtro `end_date IS NULL`)
- `get_bajan_history`: devuelve `id` del `op.ordezkapen` para el botón Bukatu; `end_date=null` → botón; `end_date` con valor → fecha
- Kargu types: `MB-%%` = mintegi buruak, `TUTO_%%` = tutoreak, `DUAL_ARDURADUNAK` = dual; campo `type` ('mb'/'tuto'/'dual') para lógica de template
- Tutoreak muestra columna extra "Taldea" con `STRING_AGG(k.code)` del cargo
- Gainontzeko karguak: drill-down de 2 niveles (sin filtro de departamento), basado en `op.kargu.id`

## Vistas personalizadas (op_student_views.xml, op_faculty_views.xml)

- Botón "Create Student User" (`create_student_user`) **oculto** en el formulario de alumno — los alumnos no acceden a Odoo.
- Campos de nombre renombrados en **ambos** formularios (alumno e irakasle):
  - `last_name` → etiqueta **Abizena_1** (antes "Abizenak" / "Last Name")
  - `middle_name` → etiqueta **Abizena_2** (antes "Bigarren Izena" / "Middle Name")
  - Cambio solo de etiqueta en la vista; el nombre de columna en BD no varía.

## Alineación de columnas en vistas lista (tree)

En Odoo 17, los campos `Float`, `Integer` y `Monetary` se alinean a la derecha por defecto. Para forzar alineación a la izquierda:

### Celdas de datos
Añadir `class="text-start"` al `<field>` en el XML del `<tree>`. El list renderer añade esa clase al `<td>`, y Bootstrap aplica `text-align: left !important` directamente:
```xml
<field name="orduak" string="Orduak" class="text-start"/>
```

### Cabeceras de columna
Los headers numéricos usan **dos mecanismos** de alineación a la derecha:
1. `flex-row-reverse` en el `<div>` interior del `<th>` (posiciona el span a la derecha)
2. `text-align: right` en el `<span class="o_list_number_th">` (alinea el texto dentro del span)

Para corregir ambos mediante CSS, el selector debe usar la clase del `<tree>` que Odoo aplica al div del **controller** (no del renderer):
```css
.mi_clase.o_list_view .o_list_table thead th > div.flex-row-reverse {
    flex-direction: row !important;
}
.mi_clase.o_list_view .o_list_table thead .o_list_number_th {
    text-align: left !important;
}
```

### Cómo funciona el `class` en `<tree>`
`class="mi_clase"` en el elemento `<tree>` se aplica al div raíz del **ListController** (junto a `o_list_view` y `o_view_controller`), NO al div `.o_list_renderer`. Los selectores CSS deben partir de `.mi_clase` como ancestro.

### Limpiar caché de assets tras cambios CSS
```bash
docker exec postgres19 psql -U odoo -d kudeaketa -c "DELETE FROM ir_attachment WHERE name LIKE '%web.assets%';"
docker restart odoo19
# Después, hard-refresh en el navegador: Ctrl+Shift+R
```

## Perfilazioak (OWL — `perfilazioak_action`)

Acción cliente OWL (menú `Perfilazioak`, `ir.actions.client` tag `perfilazioak_action`). Permite perfilar (asignar módulos y cargos a profesores) por mintegi → zikloa → taldea. Componente en `static/src/components/perfilazioak.js`, plantilla en `static/src/xml/perfilazioak.xml`. Métodos RPC en `op.faculty` (`models/op_faculty_ext.py`).

### Paneles
- **Izquierda — Irakasleak**: lista de profesores del mintegi (funtzionarioak + impersonalak). Cada profesor muestra dos cuadros junto al nombre:
  - **Gela** (badge azul `bg-info`, `pfz-faculty-gela`) = `SUM(gela_orduak)` de sus módulos.
  - **RPT** (badge gris/amarillo, `pfz-faculty-hours`) = `SUM(rpt_total)` módulos + horas de karguak. Amarillo si `> 17` (overload).
  - Leyenda en la cabecera (`.pfz-legend`, `inline-flex` `nowrap`) distingue ambos cuadros.
  - Panel `.pfz-left` ensanchado a 420px (min 380px) para que quepan los dos apellidos + cuadros.
  - Debajo: sección **Karguak** del profesor seleccionado.
- **Derecha — Moduluak** (de la taldea seleccionada) + **Perfilazio Laburpena** (resumen del profesor).

### Tablas
- **Moduluak**: Kodea · PT/PES · Orduak · Kurtsoa · Aste Ban. · **Gela** · RPT · Zorretan · Irakaslea. Clic en fila asigna/desasigna el módulo al profesor seleccionado.
- **Perfilazio Laburpena**: columnas Taldea · Kurtsoa · Kodea · PT/PES · Orduak · **Gela** · RPT · Aste Ban. · Zorretan. Filas de módulos (rm) + filas de karguak (k, con "—" en columnas de módulo). Última fila **GUZTIRA** (etiqueta bajo PT/PES) con **totales** de Gela (`sumGela`), RPT (`sumRpt` = módulos + karguak) y Zorretan (`sumZorretan`).

### Reparto de horas de karguak (cap por `op.kargu.rpt_total`)
Cada kargu tiene un total de horas RPT (`op.kargu.rpt_total`). Las horas se reparten entre profesores y **la suma no puede superar el total del kargu**.
- `get_all_karguak(faculty_id)` → `remaining` = total − horas asignadas a **otros** profesores.
- `get_perfilazio_karguak(faculty_id)` → `max_orduak` por línea = total − asignadas a otros (máximo que ese profesor puede tener).
- `upsert_perfilazio_kargu` → **guard de servidor**: lanza `UserError` si `orduak > rpt_total − asignadas_otros`.
- UI: al añadir kargu, el desplegable muestra `(libre/total h libre)` y "Libre: Xh"; el campo de horas es un **selector limitado** a las horas libres (enteros 1…remaining). Si no quedan, muestra "Ez dago ordu librerik". Las líneas ya asignadas usan selector 1…`max_orduak` con su valor actual preseleccionado.
- **Nota**: un kargu con `rpt_total = 0` no permite asignar horas (remaining 0). Hay que definir su total RPT en `op.kargu` para poder repartirlo.

## Notas importantes

- La BD MySQL es **SOLO LECTURA**. Nunca modificar datos en ella.
- El campo clave de unicidad de profesores y alumnos en `res_partner` es el **email**.
- `suspenditua=1` en MySQL → `active=False` en Odoo.
- Los menús de Konfigurazioa del SIS se gestionan en `views/op_sis_menu.xml`.
- Al añadir campos o modelos al módulo hernani, actualizar también `security/ir.model.access.csv`.
- `openeducat_classroom` está en `depends` del módulo hernani (necesario para la referencia XML al action de Gelak).
- El campo `active` (Aktiboa) está **oculto** en todas las listas embebidas del módulo (faculty_ids, course_ids, etc.). El archivado sigue funcionando internamente.
- `op_department_op_faculty_rel` se gestiona con `patch_mintegi_irakasle.py` (fuente: `MINTEGI_IRAKASLE`). Los cambios manuales desde la UI del departamento se perderán al re-ejecutar el script.
- CSS personalizado en `static/src/css/hernani.css`: dashboard, columnas ajustadas al contenido (`table-layout: auto`), cabecera "Ezabatu Mintegitik" en lista de facultad.
- El campo `gela_orduak` (`fields.Integer`) se muestra como **"Gela"** en la vista lista y como **"Gela Orduak"** en el formulario. Es intencionado: en el listado de moduluak el espacio es limitado y el usuario pidió la etiqueta corta.
