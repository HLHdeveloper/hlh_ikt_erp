# Integración FET ↔ Odoo — Progreso (lado Odoo, máquina 108)

> Estado a **2026-06-25**. Complementa `INTEGRACION_ODOO.md` (contrato de la API
> FET en la 104). Aquí se documenta TODO lo construido en Odoo para alimentar el
> futuro generador del `.fet`.

Módulo: `addons19/openeducat_erp/openeducat_hernani` (Odoo 17, BD `kudeaketa`).

---

## 1. Rejilla horaria — "Aste Saioak" (`op.timing`)

Modelo `op.timing` (módulo `openeducat_timetable`) poblado con la rejilla real
del centro: **Lunes–Viernes, 6 sesiones de 60 min, 8:00–14:30, recreo 11:00–11:30**.

| seq | name | inicio | dur |
|----|------|--------|-----|
| 1 | `1º 08:00-09:00` | 8:00 | 1h |
| 2 | `2º 09:00-10:00` | 9:00 | 1h |
| 3 | `3º 10:00-11:00` | 10:00 | 1h |
| 4 | `4º 11:30-12:30` | 11:30 | 1h |
| 5 | `5º 12:30-13:30` | 12:30 | 1h |
| 6 | `6º 13:30-14:30` | 13:30 | 1h |

- Los `name` son los **literales canónicos** que se reutilizarán en el
  `<Hours_List>` del `.fet` para mapear el `<Hour>` del resultado a `op.session`.
- Los **días** (Lun–Vie) van fijos en `op.session` (`week_days`), no en `op.timing`.
- Carga idempotente: `load_timings.py`
  (`docker exec -i odoo19 odoo shell -d kudeaketa --no-http < load_timings.py`).
- **Menú SIS**: `Aste Saioak` (HLH_KUDEAKETA, seq 56, entre *Gelak* 55 e
  *Irakasleak* 58). Definido en `views/op_sis_menu.xml`; hernani depende ahora de
  `openeducat_timetable`.

---

## 2. Tipo de aula — `gela_mota` (`op.classroom`)

Campo `gela_mota` (Selection **`gela`** / **`tailerra`**, def. `gela`) en
`models/op_classroom_ext.py`. Columna + filtros + group-by en
`views/op_classroom_views.xml`. Sirve para que en el `.fet` los módulos prácticos
prefieran talleres y los teóricos aulas normales (resuelto por `gela_mota` +
`op.subject.type`, sin asignación manual de aulas — decisión del usuario).

---

## 3. "Ordutegi murrizpenak" — restricciones que NO salen de Perfilazioak

Menú padre **Ordutegi murrizpenak** (HLH_KUDEAKETA, seq 57). Modelos en
`models/op_fet_constraints.py`, vistas en `views/op_fet_constraints_views.xml`,
permisos en `security/ir.model.access.csv`.

Constante de días `FET_WEEKDAYS` (monday…friday en euskera) en el propio módulo.

### #1 · Irakasleen erabilgarritasuna  ✅ (componente OWL)
- Modelo `op.fet.teacher.unavailability` (`faculty_id`, `day`, `timing_id`).
- UI: acción cliente `fet_teacher_unavail_action`
  (`static/src/components/fet_teacher_unavail.js` + `xml/fet_teacher_unavail.xml`).
  Selector **Mintegia** → lista de profes (solo **funtzionarioak + impertsonalak**,
  igual que Perfilazioak) → **rejilla 5 días × 6 Aste Saioak (30 huecos)**; clic
  marca el hueco como NO disponible.
- RPC: `get_mintegiak`, `get_irakasleak`, `get_grid`, `get_unavailability`,
  `toggle_slot`. CSS `.feu-*` en `hernani.css`.
- FET: `ConstraintTeacherNotAvailableTimes`.

### #2 · Gelen okupazioa  → SIN pantalla
Resuelto automáticamente por `gela_mota` + `op.subject.type` en la generación del
`.fet` (decisión del usuario: mínimo esfuerzo).

### #3 · Gelen erabilgarritasuna  ✅ (componente OWL)
- Modelo `op.fet.room.unavailability` (`classroom_id`, `day`, `timing_id`).
- UI: acción cliente `fet_room_unavail_action` (mismo patrón que #1; selector
  **Solairua** en vez de mintegi; lista de aulas docentes con columnas
  **Izena/Kodea** y badge **T** para talleres).
- FET: `ConstraintRoomNotAvailableTimes`.

### #4 · Saio simultaneoak  ✅
- Modelo `op.fet.simultaneity`: par **origen ↔ copia** (`DESDO_`/`HE_`), `mota`
  (desdoblea/eleanitza), `batch_id`, `department_id` (related, para filtrar),
  `enabled`, y dos modos editables por fila:
  - **`desdoble_mota`** (col. "Desdoble modua"): `gela_banatua` / `gela_bakarrean`.
  - **`eleanitza_mota`** (col. "Eleanitza modua"): `gela_banatua` / `gela_berean`.
- **Botones siempre visibles** en la lista (header `display="always"`, slot
  nativo Odoo 17 `control-panel-always-buttons`; el cog "Ekintzak" solo sale al
  seleccionar filas):
  - **"Sortu automatikoki"** → `generate_pairs()` (idempotente): crea un par por
    cada `DESDO_`/`HE_` emparejando por código sin prefijo (DESDO_=6, HE_=3).
    Genera **27 desdoble + 15 eleanitza = 42 pares**.
  - **"Desdoble/agrupazio berria"** → abre `op.fet.grouping` (ver #4b).
- **Searchpanel** por **Mintegia** + **Mota**.
- FET: `ConstraintActivitiesSameStartingTime` (+ misma aula cuando el modo es
  `gela_bakarrean`/`gela_berean`).

### #4b · Desdoble/Agrupación manual con aforo  ✅
- Modelos `op.fet.grouping` + `op.fet.grouping.line`.
- `mota` **bateratu** (varios grupos → misma aula) / **banatu** (grupo → varias
  aulas). `batch_ids` (≥1), `classroom_ids` (≥1).
- Cálculo en vivo: `student_total` (alumnos `studying` vía
  `op.batch.fet_student_count`) y `capacity_total` (suma de `capacity` de aulas).
  - bateratu → aviso si `student_total > capacity_total`.
  - banatu → líneas (taldea, gela, ikasleak); si una aula supera su aforo, **fila
    en rojo** + **banner "Aforoa gainditua!"**.
- ⚠️ **El aviso de aforo solo funciona donde haya `capacity`**: ahora mismo solo
  **4 de 63 aulas** tienen aforo. Falta rellenar `capacity` en Gelak.

### #5 · Saio finkoak  ✅
- Modelo `op.fet.fixed.session` (`subject_id`, `batch_id` related, `day`,
  `timing_id`). Actividad a hora fija (tutoría, etc.).
- FET: `ConstraintActivityPreferredStartingTime`.

### #6 · Murrizpen orokorrak  ✅
- Modelo `op.fet.config` (**registro único**, xml_id `fet_config_singleton`):
  `students_no_gaps` (def. True), `teacher_max_gaps_day` (2),
  `teacher_max_hours_day` (6), `max_hours_continuously` (4),
  `same_subject_once_per_day` (True).
- FET: `Students/TeachersGaps`, `MaxHoursContinuously`, etc.

### #7 · Karguen tratamendua  → SIN pantalla
Los karguak NO entran al `.fet` (solo informativos para plazas/perfilación).

---

## 4. Datos pendientes (bloquean parte del `.fet`)

1. **`banaketa_id`** en `op.subject`: solo **27 de 259** módulos con gela>0 tienen
   distribución semanal. Determina nº de sesiones/semana y duración de cada una
   (`Duration` de cada actividad FET). → Asignación masiva pendiente.
2. **`capacity`** (aforo) en `op.classroom`: solo **4 de 63**. Necesario para el
   aviso de aforo de #4b.

---

## 5. Próximos pasos (módulo `openeducat_fet` / generador)

1. Rellenar `banaketa_id` (232 módulos) y `capacity` (59 aulas).
2. **Generador del `.fet`** (FET v5.41):
   - Days (Lun–Vie) + Hours (`op.timing.name`).
   - Teachers (`op.faculty`), Subjects (`op.subject`), Students/Years/Groups
     (`op.batch` + subgrupos de desdoble), Rooms (`op.classroom`).
   - Activities: por módulo (faculty_id + gela_orduak + banaketa), con **Id estable**.
   - Restricciones desde *Ordutegi murrizpenak* (#1, #3, #4, #4b, #5, #6).
3. **Cliente HTTP** a la API de la 104 (`POST /timetable`, polling, `GET .../result`).
4. **Parseo** de `activities_timetable.xml` → `op.session` (mapeo por `<Id>`).

---

## 6. Archivos clave (módulo hernani)

```
models/op_fet_constraints.py     # op.fet.* (teacher/room unavail, simultaneity,
                                 #   grouping(+line), fixed.session, config)
models/op_classroom_ext.py       # gela_mota, irakasgela, solairua
models/op_batch_ext.py           # fet_student_count
views/op_fet_constraints_views.xml
views/op_classroom_views.xml
views/op_sis_menu.xml            # menús SIS (Aste Saioak, Ordutegi murrizpenak)
static/src/components/fet_teacher_unavail.js  + xml/fet_teacher_unavail.xml
static/src/components/fet_room_unavail.js     + xml/fet_room_unavail.xml
static/src/css/hernani.css       # .feu-* (rejillas)
security/ir.model.access.csv     # ACL de los op.fet.*
../../../load_timings.py         # carga rejilla op.timing
```
