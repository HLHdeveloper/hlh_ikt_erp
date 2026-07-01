# CIFP Gizarte Berrikuntza LHII — Odoo OpenEducat

Gestión del centro educativo CIFP Gizarte Berrikuntza LHII (Hernani) con Odoo 17 + OpenEducat.

## Integración FET (generación de horarios) — EN CURSO

Integración con FET (servicio en la 104) para generar horarios. **Lado Odoo
documentado en detalle en [`FET/PROGRESO_ODOO.md`](FET/PROGRESO_ODOO.md)**; contrato
de la API FET en `FET/INTEGRACION_ODOO.md`. Resumen de lo construido:
- **Aste Saioak** (`op.timing`): rejilla Lun–Vie, 6 sesiones 8:00–14:30, recreo
  11:00–11:30 (menú SIS seq 56). Carga: `load_timings.py`.
- **`gela_mota`** (`op.classroom`): gela / tailerra / gela_tailerra.
- **Gela-esleipena (aulas ↔ mintegi ↔ módulo)** — EN CURSO (reemplaza el Excel):
  - `op.department.gela_ids` ↔ `op.classroom.department_ids` (M2M, tabla
    `op_department_op_classroom_rel`): gelak/tailerrak disponibles por mintegi.
    UI: pestaña "Gelak erabilgarriak" en ficha mintegi + columna/filtro Mintegia
    en lista Gelak.
  - `op.subject.gela_teoria_ids` (M2M `op_subject_gela_teoria_rel`, aulas
    gela/gela_tailerra) = opciones de aula teórica (FET elige una);
    `op.subject.tailerra_ids` (M2M `op_subject_tailerra_rel`, aulas
    tailerra/gela_tailerra) = taller(es) de prácticas. M2M para admitir 1 o varias.
  - Import del Excel HECHO 2026-06-30 (`FET/import_aulak.py`, 209 módulos;
    `FET/fill_mintegi_gelak.py` rellena `gela_ids`). Detalle y reglas de alias en
    `FET/AULAK_IMPORT.md`. Pendiente: `2IEA2A/2IEA2D_PROG` (módulo "PROG" sin casar)
    y `3OLHMEK3_EAE` (inexistente).
  - **Fase 3 HECHA**: pantalla OWL **Gela esleipena** (menú Ordutegi murrizpenak,
    `aula_esleipena_action`; `static/src/components/aula_esleipena.js` + xml; CSS
    `.pae-*`). **Filtros en cascada estilo Perfilazioak** (Mintegia → Zikloa →
    Taldea): reutiliza `op.faculty.get_perfilazio_mintegiak/_zikloak/_batches`; al
    elegir zikloa muestra los módulos de todos sus grupos (una card por taldea),
    al elegir taldea solo esa. Cada card = rejilla módulos × aulas del mintegi
    (bloque TEORIA + TAILERRA); clic asigna/quita. RPC aula en `op.subject`:
    `get_aula_columns(dept)`, `get_aula_moduluak(batch)`, `toggle_aula`,
    `set_aula_column` (clic en cabecera de aula → asigna/quita a TODOS los módulos
    de esa taldea). Cards **2 por línea** (`.pae-cards` flex), tabla a ancho 100%
    de la card. Colores **TEORIA turquesa / TAILERRA morado** (homogéneo con
    Perfilazioak). `get_aula_moduluak` devuelve **todos** los módulos del batch
    (incluidas copias HE_/DESDO_/ERREF), igual que `get_perfilazio_moduluak`.
- **Ordutegi murrizpenak** (menú SIS seq 57): restricciones FET en
  `models/op_fet_constraints.py` (`op.fet.*`): #1 Irakasleen erabilgarritasuna
  (OWL grid), #3 Gelen erabilgarritasuna (OWL grid), #4 **DESDOBLE/HE banaketa**
  (antes "Saio simultaneoak": desdoble/eleanitza auto con `jatorri_ids`
  multi-origen, modua banatua/berean, `irakasle_kop` por fila + agrupaciones
  manuales con aforo), **#4c Modulu Bateratuak** (`op.fet.bateratua`: unir módulos
  de distinto ziklo/mintegi en una misma aula, ej. 2INF4_EEE + 1ELE1_EEE),
  #5 Saio finkoak, #6 Murrizpen orokorrak (config única).
  #2 y #7 sin pantalla (automático/no aplica). Detalle en `FET/PROGRESO_ODOO.md`.
- **Datos FET (2026-07-01): COMPLETOS**. `banaketa_id` 0 sin, `faculty_id` 0 sin,
  aula (Gela Esleipena) 0 sin, 20 DESDO_ en `edozein_tekniko`, **30 aulas docentes**
  (`irakasgela=True`, las únicas que entran a FET) todas con `capacity`. Solo queda
  `teoria_praktika_id` en 20 DESDO_ (opcional, no bloquea). Detalle en
  `FET/banaketa_import/PROGRESO_BANAKETA.md`.
- **Pendiente principal**: el módulo generador `openeducat_fet` (aún no existe):
  generador `.fet`, cliente HTTP a la 104 y parseo del resultado a `op.session`
  (hoy = 0). Ver plan y semánticas en `FET/PROGRESO_ODOO.md`.

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
| `op.kargu.mintegi` | — | Reparto de horas (RPT) de un kargu por mintegi + PT/PES |
| `op.greba` | `IRAKASLEAK_GREBAK` | Huelgas de profesores |
| `op.ordezkapen` | `ORDEZKAPENAK` | Sustituciones entre profesores |
| `op.report.batch.student` | — (SQL view) | Informe: ikasleak taldeka |
| `op.report.dept.faculty` | — (SQL view) | Informe: irakasleak mintegika |
| `op.report.dept.greba` | — (SQL view) | Informe: grebak mintegika |
| `op.report.dept.ordezkapen` | — (SQL view) | Informe: ordezkapenak mintegika |
| `op.report.faculty.greba` | — (SQL view) | Informe: irakasleak greba kopuruaren arabera |
| `op.apoyo.taldea` | — | Grupo de Apoyo Educativo (I/II/III) por taldea, con tope de horas (`guztira_orduak`) y `subject_ids` |

### Extensiones de modelos OpenEducat
| Modelo extendido | Campos añadidos |
|---|---|
| `op.faculty` | `kargu_ids`, `greba_ids`, `batch_ids`, `titular_ordezkapen_ids`, `ordezko_ordezkapen_ids` |
| `op.batch` | `faculty_ids`, `student_course_ids` |
| `op.department` | `course_ids`, `faculty_ids` |
| `op.subject` | `kode_jima`, `batch_id`, `apoyo_taldea_id`, `faculty_id`, `pt_pes`, `hizkuntza`, `pl` (PL1/PL2/PL1_PL2), `orduak`, `kurtsoa`, `gela_orduak`, `banaketa_id`, `aste_banaketa`, `rpt_total`, `rpt_reala`, `rpt_zorretan`, `emandako_orduak`, `orduak_zorretan`, `gela_teoria_ids`, `tailerra_ids` |
| `op.department` | `course_ids`, `faculty_ids`, `desdoble_orduak`, `errefortzu_orduak`, `errefortzu_mota`, `errefortzu_poltsan_orduak`, `gela_ids` |
| `op.classroom` | `irakasgela`, `gela_mota` (gela/tailerra/gela_tailerra), `solairua`, `department_ids` |

**Campo `pl`** (`op.subject`): Selection `PL1` / `PL2` / `PL1_PL2` (etiqueta "PL1/PL2" = cualquier perfil lingüístico válido).

### Menú SIS (orden actual)
```
[10] Mintegiak        → op.department
[20] Taldeak          → op.batch
[30] Moduluak         → op.subject
[40] Irakasleak       → op.faculty
[45] Karguak          → op.kargu  (menu_op_kargu, antes bajo Konfigurazioa)
[50] Perfilazioak     → action_perfilazioak (OWL)
[60] Ikasleak         → op.student
[70] Txostenak        → Dashboard OWL (sis_dashboard_action)
[80] Orokorra (General)
[90] Konfigurazioa
```
Orden y secuencias en `views/op_sis_menu.xml`; `menu_op_kargu` (nivel superior, name "Karguak") en `views/op_kargu_views.xml`. La traducción eu_ES del menú Karguak está en `i18n/eu_ES.po` (la acción sigue "Irakasleen Karguak").

El menú Txostenak abre directamente el **SIS Dashboard** (OWL component):
- **Sección Irakasleak**: 6 tarjetas (total, funtzionarioak, ordezkoak, bajan, karguak, gainontzeko karguak)
- **Sección Ikasleak**: 1 tarjeta con drill-down 3 niveles
- Drill-down irakasleak: tarjeta → mintegiak → irakasleak / kargu types → irakasleak → formulario
- Drill-down ikasleak: tarjeta → mintegiak → taldeak → ikasleak → formulario (editable)

## Ficha de Kargua (op.kargu) — reparto por mintegi

Form `view_op_kargu_form` (acción "Irakasleen Karguak", menú Karguak):
- Pestaña **"Uneko Irakasleak"** (antes "Irakasleak"): `faculty_ids`, profesores actuales del cargo.
- Pestaña **"Perfilazio Irakasleak"**: lista editable de `perfilazio_ids` (modelo **`op.kargu.mintegi`**), una línea por reparto: **Mintegia** (`department_id`) · **PT/PES** (`pt_pes`) · **Orduak (h/aste)** (`orduak`). Único por `(kargu_id, department_id, pt_pes)`.
- **`rpt_total`** = Float normal (NO computed) sincronizado por `_sync_rpt_total()`: si hay líneas → **suma** de sus horas; si **no hay líneas** → conserva el valor **manual**. En la vista es `readonly="perfilazio_ids"` (readonly cuando hay reparto). La sincronización se dispara desde `op.kargu.mintegi.create/write/unlink` (→ `kargu_id._sync_rpt_total()`) y desde `op.kargu.create/write`. **No usar computed editable** aquí: el form envía siempre el valor del campo (0.0) y Odoo lo trata como override manual, cancelando el recálculo (por eso `rpt_total` se quedaba a 0).
- Ejemplo: BERRIKUNTZA_TALDEA con `rpt_total=1` (manual, sin reparto) → al añadir línea Informatika/PT/1h, RPT Total = suma = 1h.

### Tipo de cargo (`kargu_mota`) y filtro por mintegi
- **`kargu_mota`** (`op.kargu`): Selection `perfilazioa` ('Perfilazio Karguak') / `drive` ('DRIVE Taldeak'), `required`, default `perfilazioa`. Distingue los dos tipos de cargo. Visible en tree, form y search (con filtros rápidos + group_by). **Regla de clasificación**: cargos **con** `gsuite_email` → `drive`; **sin** email → `perfilazioa` (asignado por SQL directo: 62 drive / 6 perfilazioa al implantarlo).
- **`department_ids`** (Mintegiak): Many2many **computed `store=True`** desde `perfilazio_ids.department_id` (`@api.depends('perfilazio_ids.department_id')`, tabla `op_kargu_department_rel`). Son los mintegis donde el cargo tiene reparto de horas en la pestaña "Perfilazio Irakasleak". Se usa en el form/relaciones; el searchpanel de la lista usa el modelo de líneas (ver abajo).

### Lista KARGUAK = vista SQL `op.kargu.mintegi.all` (líneas + cargos sin reparto)
La acción `act_open_op_kargu_view` (menú Karguak único, action 453) **muestra `op.kargu.mintegi.all`**, un modelo **`_auto=False` (vista SQL, solo lectura)** en `models/op_kargu_mintegi.py`. Motivo del diseño:
- El **GUZTIRA** de pie de columna en Odoo solo agrega campos **almacenados** (SQL `read_group`); las horas por mintegi viven en `op.kargu.mintegi.orduak`, así que la lista debe basarse en líneas (no en `op.kargu`) para que GUZTIRA = suma por mintegi.
- Pero cargos **sin reparto** (p.ej. `LCAMP`) no tienen línea y no aparecerían. La vista hace **UNION ALL**: (a) líneas reales `op.kargu.mintegi` + (b) una fila **sintética por cada cargo sin ninguna línea** (`id = 1000000000 + kargu.id`, `department_id NULL`, `orduak 0`). Así **Mintegia=ALL** (searchpanel sin selección) muestra **todos los cargos sin excepción**; al seleccionar un mintegi concreto las sintéticas (dept NULL) se excluyen y GUZTIRA no se altera.
- **Tree** `view_op_kargu_mintegi_tree` (`class="hlh-styled" js_class="kargu_mintegi_list"`): **Kargua** (`kargu_id`) · **Mintegia** (`department_id`) · **PT/PES** · **Orduak (h/aste)** (`orduak`, `sum="GUZTIRA"`, `text-start`); `kargu_mota` columna opcional oculta.
- **Searchpanel**: **Kargu mota** (categoría: Perfilazio Karguak / DRIVE Taldeak; sin selección = todos) + **Mintegia** (`department_id`, categoría; sin selección = todos). **No** hay group-by por defecto (no se pre-carga filtrada).
- **ACL del modelo SQL**: `op.kargu.mintegi.all` lleva **`create=1`** (read=1, write=0, create=1, unlink=0) y el tree `create="1" edit="0" delete="0"`. Esto es **solo para que el botón Berria/Nuevo se muestre** (Odoo lo oculta si el modelo no permite crear); el `js_class` redirige la creación a la ficha del cargo, así que **nunca** se crea en la vista SQL. Sin ese `create=1`, el botón Berria desaparece.
- **`js_class="kargu_mintegi_list"`** (`static/src/components/kargu_mintegi_list.js`, registrado en manifest): sobreescribe el `ListController`:
  - **`createRecord`** (botón **Berria**) → abre la **ficha del cargo nueva** (`act_open_op_kargu_new`, form `op.kargu`), donde se asigna a cualquier mintegi en la pestaña "Perfilazio Irakasleak". NO crea una línea.
  - **`openRecord`** (clic en fila) → abre la **ficha del cargo** (`op.kargu` form, `res_id = kargu_id`), no la fila read-only.
  - **`_afterFormClose()`** (en el `onClose` de ambos) → llama a **`this.env.searchModel._notify()`**, que refetchea las secciones del searchpanel (Kargu mota + Mintegia; tienen `enable_counters` → siempre se recargan) y dispara el `update` que recarga la lista. Así un **mintegi recién asignado aparece al instante** en el panel lateral sin F5. `_notify`→`_reset()` solo limpia cachés internos, **no** borra los filtros activos del usuario. Fallback a `model.root.load()` si `_notify` no existe. Motivo: el searchpanel de Odoo NO se autorrefresca al cambiar datos en la misma sesión.
- **Acción auxiliar** `act_open_op_kargu_new`: `op.kargu`, `view_mode="form"`, `view_op_kargu_form`, target current.
- **Campos related `store=True` en `op.kargu.mintegi`**: `kargu_code`, `kargu_mota` (para la pestaña del cargo / consistencia). La vista SQL expone `kargu_code` y `kargu_mota` desde `op_kargu`.
- El **form/tree/search de `op.kargu`** siguen existiendo (la ficha se abre vía JS), pero ya **no** son la vista de la acción 453. Ya **no** existe el menú "Kargu fitxak" (un solo apartado Karguak).
- **CSS** cabecera "Orduak (h/aste)" a la izquierda: `th[data-name="orduak"]` en `.hlh-styled`.

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
  - **RPT** (badge `pfz-faculty-hours`) = `SUM(rpt_reala)` módulos + horas de karguak. Estados: **gris** si `< 17`; **borde+texto verde negrita** (`.pfz-hours-complete`) si `= 17` (perfilación completa); **amarillo** si `> 17` (overload). El criterio de 17h es float-safe: el total se **redondea a 2 decimales** antes de comparar (helper JS `isComplete`, y `round(...,2)` en el servidor) para que sumas de decimales (`rpt_reala` 0,9+3,2…) no falseen el 17 exacto.
  - Leyenda en la cabecera (`.pfz-legend`, `inline-flex` `nowrap`) distingue ambos cuadros.
  - Panel `.pfz-left` ensanchado a 420px (min 380px) para que quepan los dos apellidos + cuadros.
  - Debajo: sección **Karguak** del profesor seleccionado.
- **Derecha — Moduluak** (de la taldea seleccionada) + **Perfilazio Laburpena** (resumen del profesor).

### Tablas
- **Moduluak**: Kodea · PT/PES · **PL** · Orduak · Kurtsoa · Aste Ban. · **Gela** · **RPT Guzt** (`rpt_total`) · **RPT Reala** (`rpt_reala`) · **RPT Zorretan** (`rpt_zorretan`) · Irakaslea. Clic en fila asigna/desasigna el módulo al profesor seleccionado. (Las tres columnas RPT muestran respectivamente `rpt_total`/`rpt_reala`/`rpt_zorretan`; ninguna usa `orduak_zorretan`.)
  - **Vista por grupos del zikloa**: si hay **mintegi + zikloa seleccionados pero NO taldea**, se muestran los módulos de **todos los grupos del zikloa**, una **card por taldea apilada** (ej. MSS → cards `1MSS2` y `2MSS2`). Al elegir una taldea concreta se muestra solo esa; al deseleccionarla, vuelven todas. Implementación (sin tocar la lógica de asignación): `_loadAllZikloModuluak()` carga en `state.moduluak` (lista plana usada por los handlers de clic, búsqueda por `id`) los módulos de todos los grupos etiquetados con `_batch_id`/`_batch_name`; getters `moduluakByBatch()` (agrupa) y `moduluakGroups()` (1 grupo para taldea/ingelesa, N para zikloa sin taldea y `!isKopiakActive()`); la card va envuelta en `t-foreach="moduluakGroups()"`. Se recarga en `onZikloaChange`, `onBatchChange` (al limpiar taldea) y `_reloadModuluak`.

**RPT = `rpt_reala` en toda la perfilación.** El RPT de los módulos usa `rpt_reala` en: la tabla Moduluak, la **Perfilazio Laburpena** (resumen por irakasle, incl. total GUZTIRA), la **Laburpena del mintegi** (`get_perfilazio_laburpena`) y los **totales/badge RPT del panel de irakasle** (`get_perfilazio_irakasleak` y los recálculos tras asignar módulo/kargu, overload `>17`). En el lado servidor las claves de dict siguen llamándose `rpt_total` pero transportan `rpt_reala`. **Excepciones que mantienen `rpt_total`**: Apoyo Educativo (tope del multzo) y la tabla MODULUAK KOPIATU. Las columnas **Zorretan** fuera de la tabla Moduluak siguen mostrando `orduak_zorretan`.
**Columna PL** (`op.subject.pl`, mostrada `PL1`/`PL2`/`PL1/PL2`) presente en 4 tablas, siempre entre PT/PES y Orduak: tabla **Moduluak** (RPC `get_perfilazio_moduluak` e `get_perfilazio_ingelesa_moduluak`), **Perfilazio Laburpena** resumen del profesor (RPC `get_perfilazio_resumen`; filas de kargu y GUZTIRA con `—`) y **MODULUAK KOPIATU** (RPC `get_perfilazio_ziklo_moduluak`; misma tabla para Eleanitza y Desdoblea). En el SQL el valor se formatea con `.replace('_', '/')`.

- **Perfilazio Laburpena**: columnas Kodea · PT/PES · **PL** · Orduak · **Gela** · RPT · Aste Ban. (7 columnas; Taldea y Kurtsoa **eliminadas** a petición del usuario; la columna **Zorretan se eliminó** del perfil del profesor — `orduak_zorretan` sigue existiendo como campo de módulo, solo no se muestra aquí). Filas de módulos (rm) + filas de karguak (k, con "—" en columnas de módulo). Última fila **GUZTIRA** (etiqueta bajo PT/PES) con **totales** de Gela (`sumGela`) y RPT (`sumRpt` = módulos `rpt_reala` + karguak). La columna RPT muestra `rpt_reala`.

### Reparto de horas de karguak (cap por `op.kargu.rpt_total`)
Cada kargu tiene un total de horas RPT (`op.kargu.rpt_total`). Las horas se reparten entre profesores y **la suma no puede superar el total del kargu**.
- `get_all_karguak(faculty_id)` → `remaining` = total − horas asignadas a **otros** profesores.
- `get_perfilazio_karguak(faculty_id)` → `max_orduak` por línea = total − asignadas a otros (máximo que ese profesor puede tener).
- `upsert_perfilazio_kargu` → **guard de servidor**: lanza `UserError` si `orduak > rpt_total − asignadas_otros`. Tras el write/create hace `flush_model([...])` **antes** del SQL crudo que recalcula el total (si no, el `SUM(pk.orduak)` leía el valor antiguo y el overload `>17` se quedaba pegado al modificar una línea existente). El total devuelto se redondea a 2 decimales (mismo fix de overload en `delete_perfilazio_kargu`, `assign_perfilazio_modulu` y `get_perfilazio_irakasleak`).
- UI: al añadir kargu, el desplegable muestra `(libre/total h libre)` y "Libre: Xh". El tipo de entrada de horas depende del kargu (banderas que vienen del servidor en `get_all_karguak`/`get_perfilazio_karguak`):
  - **TUTO_* y MB-*** → **selector** de horas enteras (1…remaining; líneas existentes 1…`max_orduak`).
  - **`allow_zero`** (helper `_kargu_allows_zero`): los **TUTO de los grupos MLE, MSS, IEA, SEA, FMD, AST** pueden asignarse con **0h** (cotutor sin RPT); el selector incluye el `0` y se muestra aunque `remaining = 0`. El resto de TUTO_ y todos los MB requieren ≥1h.
  - **`allow_decimal`** (helper `_kargu_allows_decimal` = todo lo que **no** es TUTO/MB, p.ej. `ERALDI_TALDEA`, `DUAL_*`) → **campo numérico** `type=number step=0.1 min=0 max=remaining` (admite 1 decimal, p.ej. 2,8h). El campo `op.perfilazio.kargu.orduak` es `Float`.
- **Nota**: un kargu (no-`allow_zero`) con `rpt_total = 0` no permite asignar horas (remaining 0); hay que definir su total RPT en `op.kargu` para repartirlo.

### Eleanitza / Desdoblea (botones toggle)
En la cabecera, al seleccionar un ziklo aparecen dos **botones toggle** (antes desplegables BAI/EZ):
- **Eleanitza** (verde `btn-success` cuando activo) → copias con prefijo `HE_`.
- **Desdoblea** (morado `.pfz-btn-desdo`, `#6f42c1`, cuando activo) → copias con prefijo `DESDO_`.
- Son **mutuamente excluyentes**: activar uno desactiva el otro. Handlers JS `toggleEleanitza()` / `toggleDesdoblea()`.
- Al activar, se abre la tabla **MODULUAK KOPIATU**: clic en módulo crea/elimina su copia `HE_`/`DESDO_` (`toggle_perfilazio_kopia`). La selección (verde/morado) refleja qué copias ya existen.
- **Filtro por taldea**: `get_perfilazio_ziklo_moduluak(batch_id)` devuelve **solo los módulos de la taldea seleccionada** (códigos `<taldea>_XXX`, p.ej. `1IEA2A_*`), no de todo el ciclo. El JS pasa `selectedBatch.id`; al cambiar de taldea con un toggle activo, el panel se recarga (`onBatchChange`). Sin taldea seleccionada, el panel queda vacío.

### Apoyo Educativo (OLHMEK/OLHELE)
Botón "+ Apoyo Educativo" (kodea I/II/III según dígito inicial de la taldea). Tabla con tope editable `guztira_orduak`; la suma de RPT de los módulos del grupo no puede superarlo (al llegar al tope: **BETETA**, se oculta la fila de creación). Modelo `op.apoyo.taldea` (uno por `batch_id`+`kodea`), módulos vía `op.subject.apoyo_taldea_id`.

### Distintivo PT/PES por profesor
Badge **PT/PES** en cada profesor del panel Irakasleak (izquierda del cuadro Gela). Automático: **PT** si algún módulo del profesor tiene `pt_pes` PT (LIKE 'PT%'), si no **PES**. **Modificable a mano** (clic alterna PT↔PES, persiste en `op.faculty.perfilazio_pt_pes`; vacío = automático). RPC `toggle_perfilazio_pt_pes`. Colores: PT morado clarito (`.pfz-ptpes-pt`), PES gris (`.pfz-ptpes-pes`).

### Cuadro Mintegiko laburpena (bajo Irakasleak)
- Dos tablas en fila (`d-flex`, 50%/50%):
  - **Mintegiko taldeak**: tabla **Taldea · esleitzeke_mod · mod_kop** (sin asignar / total de módulos por taldea del mintegi). Fila en verde cuando `esleitzeke_mod = 0`. RPC `get_perfilazio_taldeak_laburpena`.
  - **Mintegiko karguak**: karguak con una línea en su pestaña "Perfilazio Irakasleak" (`op.kargu.mintegi`) para ese mintegi. Columnas **Kargua · esleitzeke orduak · ordu guztiak**: `ordu guztiak` = suma de líneas del kargu para ese dept; `esleitzeke` = `ordu guztiak − horas ya repartidas a profesores` (`op.perfilazio.kargu`), clamp a 0. Fila verde si `esleitzeke = 0`. Última fila **GUZTIRA** = suma de la columna `ordu guztiak` (helper JS `mintegiKarguakGuztira`). RPC `get_perfilazio_mintegi_karguak`. Estado JS `mintegiKarguak` (cargado en `_refreshTaldeakLaburpena`). **Decremento en vivo**: `saveKargu`/`onKarguHoursChange`/`removeKargu` llaman a `_refreshTaldeakLaburpena` para que `esleitzeke` baje al repartir horas. La caja izquierda (`.pfz-left`) se ensanchó a 720px (min 640) para las dos tablas; código de kargu en una línea (`white-space: nowrap`), karguak con `flex: 1.7` vs taldeak `flex: 1`.
  - **Tope de asignación = RPT Total**: `upsert_perfilazio_kargu` ya impide asignar a un profesor más de `rpt_total − asignadas_a_otros`; como `rpt_total` = suma de líneas mintegi, nunca se supera el RPT Total del kargu.
  - **Eleanitza / Desdobleak** (bajo Mintegiko taldeak; columna izquierda apilada en `flex-column`): filas `eleanitza` / `desdoblea`, columnas **esleitzeke orduak · ordu guztiak**. `ordu guztiak` = suma de `rpt_reala` de las copias `HE_` (eleanitza) / `DESDO_` (desdoble) de los zikloak del mintegi; `esleitzeke` = suma de `rpt_reala` de las que no tienen `faculty_id`. Verde si pending=0 y total>0. RPC `get_perfilazio_eleanitza_laburpena`, estado JS `eleanitzaLaburpena`.
- **Ordu ez lektiboak** + **Plazen laburpena** (en fila, `d-flex`):
  - **Ordu ez lektiboak** (recuadro ámbar `.pfz-ezlekt-box`, a la izquierda): horas no lectivas del mintegi = `Mintegiko karguak GUZTIRA` + `Eleanitza/Desdobleak GUZTIRA` (suma de *ordu guztiak* de karguak + eleanitza + desdoble). Helper JS `orduEzLektiboak()`. La tabla Eleanitza/Desdobleak tiene fila GUZTIRA (`eleanitzaGuztira('pending'|'total')`).
  - **Plazen laburpena**: **2 cuadros** (PES y PT). Cada uno muestra **plazas** `= <plazak> + <orduak sobrantes>h` (p.ej. 62h → `3 + 11h`; 75.2h → `4 + 7.2h`; helper `_plazaLabel`, total = lekt+ez_lekt) con subtítulo de horas totales. Datos del RPC `get_perfilazio_plazak_laburpena` (por faculty con `_perfilazio_pt_pes`: `lekt` = módulos normales `rpt_reala`, `ez_lekt` = módulos `HE_`/`DESDO_` + karguak); estado JS `plazakOrduak`, `plazakLaburpena()`. Se refresca también en `togglePtPes`. (`ez_lekt` se calcula pero ya no se muestra en cuadro aparte.)

### Campo `mintegiko_irakaslea` (op.subject)
Many2one a `op.department` (dominio excluye el mintegi propio vía `own_department_id`). Si está fijado, el módulo (que sigue en su taldea/mintegi) se ofrece en Perfilazioak con el **desplegable de profesores de ESE departamento** (override manual del mecanismo `special_dept`). Ej: `2INF4_EEE` (INFOR) impartido por un profesor de ELEKTRIZITATEA.

### Karguak: 0h y decimales
- `allow_zero` (`_kargu_allows_zero`): TUTO de grupos **MLE, MSS, IEA, SEA, FMD, AST** pueden asignarse con **0h** (cotutor). Resto de TUTO_ y todos los MB: ≥1h.
- `allow_decimal` (`_kargu_allows_decimal` = no TUTO/MB, p.ej. `ERALDI_TALDEA`, `DUAL_*`): horas con **campo numérico** `step=0.1` (un decimal). TUTO/MB usan selector de enteros. Banderas vienen de `get_all_karguak`/`get_perfilazio_karguak`.

### LABURPENA IKUSI — roles
Roles por profesor como `{label, type}`. **Mintegiburua** (kargu `MB-`) en turquesa; **Taldeko tutorea (taldea)** en **azul** (`.pfz-role-tuto`), detectado tanto de karguak `TUTO_` como de **módulos TUTO** asignados (código `(^|_)TUTO(_|$)`; taldea desde el `batch`). Roles deduplicados.

### LABURPENA IKUSI — asignar ordezkoa a impersonalak
Cada cuadro de profesor **impersonal** (INFO_X1, INFO_X2…) muestra un **desplegable de ordezkoak del mintegi** (`kidergoa='ordezkoa'`) para **anotar** qué ordezkoa cubrirá esa plaza X. **Solo es anotación**: la perfilación NO se mueve.
- Campo **`op.faculty.ordezko_esleitua_id`** (Many2one a `op.faculty`, `ondelete='set null'`).
- **Una plaza = un profesor**: un ordezkoa solo puede asignarse a UNA plaza impersonal. El desplegable de cada `X` **solo muestra ordezkoak no asignados a otra plaza** (más el propio, para verse seleccionado). `set_perfilazio_ordezko_esleitua` **rechaza** (`False`) si el ordezkoa ya está en otra plaza.
- RPC: `get_perfilazio_ordezkoak(dept_id)` (lista de ordezkoak del mintegi), `set_perfilazio_ordezko_esleitua(faculty_id, ordezko_id)` (solo acepta impersonalak; `ordezko_id` falsy = limpiar; guard de unicidad). `get_perfilazio_laburpena` devuelve `ordezko_esleitua_id` (con `flush_model` previo a la lectura SQL).
- Frontend: `state.laburpenaOrdezkoak` (cargado en `openLaburpena`), `availableOrdezkoak(lf)` (filtra los ya tomados), `onLaburpenaOrdezkoChange` (revierte y avisa si el backend rechaza); `<select>` en el cuadro impersonal; CSS `.pfz-laburpena-ordezko` / `.pfz-ordezko-select`.

### Versiones de perfilación (snapshots por mintegi)
Modelo **`op.perfilazio.bertsioa`** (`name`, `department_id`, `is_auto`, `data` JSON). Botones junto a LABURPENA IKUSI: **GORDE \<MINTEGI\> PERFILAZIOAK** (guarda con nombre) y **BERTSIOAK** (panel de versiones: cada una con `N mod · M kargu`, **Kargatu**, **Deskargatu**, **Ezabatu**, e **Inportatu**).
- Snapshot = **módulo→profesor** (módulos del mintegi) + **horas de karguak** + **PT/PES** de sus profesores. Tamaño ~0,4–1,5 KB/versión.
- **Kargatu** autoguarda el estado actual antes de sobrescribir (`is_auto`); se conservan los **últimos 5 autoguardados** (`PERFILAZIO_AUTO_KEEP`).
- **Export/Import portable** por códigos: `subject.code`, **email** del profesor o `name:<izena>` para impersonalak, `kargu.code`. Al **importar**, se **crean automáticamente los impersonalak** (`name:…`) que falten en el mintegi destino; lo demás no resuelto solo se avisa (`missing`).
- RPC: `save/get/load/delete/export/import_perfilazio_bertsioa`. Acceso en `ir.model.access.csv`.

## Importación masiva de módulos (`import_moduluak.py`)

Script reutilizable (odoo shell) para crear/actualizar `op.subject` desde tablas de zikloak pegadas por el usuario. Se ejecuta:
```bash
docker exec -i odoo19 odoo shell -d kudeaketa --no-http < import_moduluak.py
```
- Empareja por `code` (o por `kode_jima`/alias en casos de renombrado); update si existe, create si no.
- Normaliza códigos: espacios→`_`, colapsa `__`→`_` (regla: **sin espacios en `code`**).
- `PT/PS` → `pt_pes` (`PT`/`PES`/`PT_PES`); `PL1/PL2` → `pl`. Columnas vacías de `pt_pes`/`pl` **no** sobrescriben el valor existente.
- `aste banaketa` se busca en `op.subject.banaketa` por nombre; `Orduak Horas`→`orduak`, `Gela/Aula`→`gela_orduak`, `LPZ/RPT Guz/Tot`→`rpt_total`, `RPT REALAK`→`rpt_reala`, `RPT ZORRETAN`→`rpt_zorretan`, `EMANDAKO ORDUAK`→`emandako_orduak`, `Orduak Zorrean`→`orduak_zorretan`.
- Columnas que faltan en algunos ciclos (`RPT ZORRETAN`, `EMANDAKO ORDUAK`, `ORDUAK ZORREAN`, `kode_jima`, `pt_pes`, `pl`): si vienen vacías **no** sobrescriben el valor existente.
- Tuple de `ROWS`: `(batch_code, code, kode_jima, pt_ps, pl, orduak, kurtsoa, gela, banaketa, rpt, rpt_reala, rpt_zorretan, emandako_orduak, orduak_zorretan)`.
- Convención: módulos optativos "Hautazko modulua" → code `<taldea>_HAUTAZKOA` con `kode_jima` vacío.
- Copias eleanitza/desdoble: filas `HE_<code>` / `DESDO_<code>` se asignan a la taldea del **módulo de origen**.
- `DELETE_CODES = [...]`: códigos a eliminar tras importar (p.ej. el placeholder `<taldea>_HAUTAZKOA` al crear `_HAUT_1`/`_HAUT_2`).
- `aste banaketa` vacío **no** borra `banaketa_id` existente (guard añadido).

### Scripts de actualización puntual (solo columnas nuevas)
Cuando el paste solo aporta datos para campos **nuevos** del proyecto, NO usar el `import_moduluak.py` general (reescribe code/name/orduak/etc.). Usar scripts enfocados que **solo** escriben las columnas indicadas y emparejan por `code` (no crean ni renombran):
- **`update_rpt_reala.py`** — `ROWS = [(code, rpt_reala), ...]`. Solo `rpt_reala`.
- **`update_new_cols.py`** — `ROWS = [(code, rpt_reala, rpt_zorretan, emandako_orduak, orduak_zorretan), ...]`. Cada campo vacío no se escribe.
```bash
docker exec -i odoo19 odoo shell -d kudeaketa --no-http < update_new_cols.py
```

### Reglas al importar tablas de zikloak (acordadas con el usuario)
- **Solo escribir las columnas NUEVAS del paste** (`rpt_reala`, `rpt_zorretan`, `emandako_orduak`; y `orduak_zorretan` si trae valor). **No** tocar `code`, `name`, `kode_jima` ni campos previos (`orduak`, `gela_orduak`, `rpt_total`, `pl`, `pt_pes`, `kurtsoa`).
- **Emparejar por `code`** verificando contra BD antes de escribir. El prefijo/código del paste a veces es erróneo: el **taldea correcto se deduce del Kurtsoa** (1º→`1XXX`, 2º→`2XXX`) y el código real puede llevar romano (`EIP_I`/`EIP_II`) o sufijos (`ING_P_2`); mapear al código existente, **sin renombrar**. Si un código no existe → reportar, **no crear** (salvo que el usuario lo pida).
- **Optativas HAUT**: filas `kode_jima='HAUT'` (o modulo "Módulo optativo") → crear `<taldea>_HAUT_1`/`_HAUT_2` y eliminar el placeholder `<taldea>_HAUTAZKOA` (patrón "Reemplazar", confirmado por el usuario). Verificar antes que el placeholder esté huérfano (sin faculty/matrículas/relaciones).
- **Copias `HE_`/`DESDO_` inexistentes**: si el paste las referencia y no están, preguntar; al crearlas con datos del paste sin `RPT REALAK`, usar `rpt_reala = LPZ/RPT`.

## Grados C (zikloak C_INF / C_MEK)

Ciclos de **grado C** (`kurtsoa = C`) creados **solo en Odoo** (no existen en MySQL `ZIKLOAK`; conviven con la migración pero no se regeneran al re-ejecutar `migrate_laravel_to_odoo.py`). Jerarquía mintegia → ziklo → taldea → moduluak:

- Zikloak (`op.course`): **C_INF** (mintegi INFORMATIKA), **C_MEK** (mintegi MEKANIKA). `name = code`, `evaluation_type = normal`.
- Taldeak (`op.batch`): C_INF → `IFC_C_002_3B`, `IFC_C_003_4B`; C_MEK → `FME_C_001_3B`, `FME_C_002_4B`, `FME_C_005_5B`. Fechas curso 2025-09-01 → 2026-06-30.
- Moduluak (`op.subject`): `code = <FAM><NB>_<modulo>` donde `<FAM>` = familia (`INF`=IFC, `MEK`=FME) y `<NB>` = nivel del taldea (`3B`/`4B`/`5B`). Ej: `INF3B_C_IPE`, `MEK4B_C_ZKME`. **El prefijo familia+nivel es obligatorio** (IFC y FME comparten niveles y módulos como `C_IPE`, y `op.subject.code` es `varchar(256)`, no 16). `name` = el código de módulo del paste (`C_IPE`).
- Mapeo del paste: `PT/PS`→`pt_pes` (PS→`PES`); `Orduak`→`orduak`; `kurtsoa`=`C`; `aste banaketa`→banaketa **JARRAIAN** (bloque continuo, `op.subject.banaketa` con `guztira=0,egun_kopurua=0`); `LPZ/RPT Guz/Tot`→`rpt_total`; `RPT REALAK`→`rpt_reala`. Obligatorios `type='theory'`, `subject_type='compulsory'`. Cada módulo se vincula a su `batch_id` **y** al ziklo vía `op_course_op_subject_rel` (no existe campo `course_ids` en op.subject).

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
- La **lista de Moduluak** (`view_op_subject_tree_hernani`) es **editable solo en la columna "Aste Banaketa"** (`editable="bottom"` + todas las demás columnas con `readonly="1"`; "Aste Banaketa" = Many2one `banaketa_id`, no el calculado `aste_banaketa`). El resto de campos se editan en la **ficha**: botón **"Fitxa"** (icono lápiz, primera columna) que llama a `op.subject.action_open_form` y abre el formulario (`target='current'`). Motivo: en una lista editable el clic en fila entra en edición inline y NO abre el formulario; el botón da ese acceso. Odoo no permite "una columna inline + otra abre ficha" en la misma lista (la editabilidad es de toda la lista).
- **Aste Banaketa ligada a Gela**: `banaketa_id` (lista y formulario) usa `domain="[('guztira','=',gela_orduak)]"` → el desplegable solo ofrece distribuciones cuyo total semanal = `gela_orduak` (ej. módulo de 7h gela → opciones de 7h). `guztira` es Integer; `gela_orduak` Float (comparan bien).
- Para evitar el **modal de "campo inválido"** al editar inline: `@api.onchange('gela_orduak')` en `op.subject` (`_onchange_gela_orduak`) **limpia `banaketa_id`** si su `guztira` deja de cuadrar con el nuevo `gela_orduak` (así no queda un Many2one fuera de dominio). Un valor de banaketa fuera de dominio (ej. histórico `1FMD3_PSAD_2`: gela=2 con banaketa `2/2/2/2`=8h, ya saneado) disparaba el modal al guardar cualquier columna de esa fila.
- **Searchpanel de Moduluak en cascada (Mintegia → Zikloa → Taldea)**: el `<searchpanel>` de `view_op_subject_search_hernani` apila 3 categorías: `own_department_id` (Mintegia), `course_id` (Zikloa), `batch_id` (Taldea). Los tres son campos **stored + index** en `op.subject` (`own_department_id`/`course_id` son related de `batch_id.course_id...`). Para que **al elegir un mintegi solo aparezcan SUS zikloak/taldeak** (no todas a 0) hubo que **override** `search_panel_select_range`/`search_panel_select_multi_range` en `op.subject` (`_hernani_fold_category_domain`): por defecto Odoo calcula los valores visibles de cada categoría solo con `search_domain` (la barra), y la selección de OTRAS categorías va a `category_domain`, que **solo ajusta contadores** (deja las no coincidentes a 0 pero las muestra). El override **pliega `category_domain` dentro de `search_domain`** para que el propio conjunto de valores quede restringido. Sin esto, las categorías hermanas del searchpanel NO se filtran entre sí (limitación nativa de Odoo).
