# Integración FET ↔ Odoo — Progreso (lado Odoo, máquina 108)

> Estado a **2026-07-01** (código; las cifras de datos de la sección 4 son de
> 2026-06-30). Complementa `INTEGRACION_ODOO.md` (contrato de la API FET en la
> 104). Aquí se documenta TODO lo construido en Odoo para alimentar el futuro
> generador del `.fet`. Ver el **Historial de cambios** (sección 7) para el
> registro por sesiones.

Módulo: `addons19/openeducat_erp/openeducat_hernani` (Odoo 17, BD `kudeaketa`).

**Repositorio GitHub**: `github.com/hlhkudeaketa-odoo/HLH_openeducat`, rama por
defecto **`17.0`** (autenticación por token en `~/.git-credentials`). El repo
local trackea `hlh/17.0`; `git push` sube los cambios.

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

### #4 · DESDOBLE/HE banaketa  ✅  (antes "Saio simultaneoak")
Menú **DESDOBLE/HE banaketa** (renombrado 2026-07-01; era "Saio simultaneoak").
Modelo `op.fet.simultaneity`: un registro = una copia `DESDO_`/`HE_` y su
tratamiento en el `.fet`.

**Campos principales:**
- **`copy_id`** (Many2one, la copia `DESDO_`/`HE_`) — `unique`, un registro por
  copia. **`copy_code`** (related, col. "Desdoble modulua") muestra el código.
- **`copy_desdoble_orduak`** (related `copy_id.rpt_total`, col. "Desdoble
  orduak") = horas REDUCIDAS asignadas a la copia (p.ej. `DESDO_1MSS2_MUNTAIA`=3h,
  no las 7h de gela del origen); coincide con "Moduluak Kopiatu" de Perfilazioak.
- **`mota`** (computed **stored**, readonly): `eleanitza` si `copy_id.code`
  empieza por `HE_`, si no `desdoblea`. Garantiza que un `DESDO_` nunca sea
  eleanitza ni al revés; no editable a mano.
- **`subject_id`** (Many2one, origen, ancla interna) + **`jatorri_ids`**
  (Many2many `op_fet_simult_jatorri_rel`, col. "Jatorrizko modulua(k)"): los
  módulos reales del grupo con los que la copia comparte sesión. **Multi-origen**
  para desdoble (talde txikiak comparten aula); en `HE_` es fijo (1 origen).
  Widget `many2many_tags` con `context={'show_code':1}` → muestra el **código**.
- **`edozein_tekniko` / `edozein_amankomun`** (Boolean, solo desdoble): flexibilidad
  total con módulos del MISMO grupo, sin `jatorri_ids` concretos. **Transversal
  (amankomun) = código contiene ZIA/KOG/ING/FOL/EIE/EIP/IPE** (lista cerrada); el
  resto = técnico. tekniko=solo técnicos, amankomun=solo transversales,
  ambos=en cualquier sitio, ninguno=`jatorri_ids` concretos. Al activar cualquiera,
  `jatorri_ids` queda readonly/ignorado.
- **`modua`** (Selection `banatua` / `berean`, col. "Modu mota", editable):
  banatua = gela banatan, irakasle bana; berean = gela bakarrean varios profes.
- **`irakasle_kop_id`** (Many2one a **`op.fet.irakasle.kop`**, col. "Irakasle
  kop.", solo desdoble): nº de profes/gelas del reparto. **Dominio POR FILA**
  `value <= irakasle_max` (por eso es Many2one, no Selection: un Selection no
  recorta opciones por registro). **`irakasle_max`** (Integer computed) =
  **`1 + nº módulos en jatorri_ids`** (el profe `DESDO_` + los orígenes); edozein
  → 8 (abierto); no-desdoble → 2. Rango: mín 2, máx `1+orígenes`.
- **`modua_azalpena`** (Char computed, col. **"Modua"**, readonly): expande el
  modo con el nº de profes → `Gela bakarra (X irakasle)` / `Gela banatuak (X gela
  / X irakasle)`; eleanitza fijo a 2 (titular + idiomas); edozein → "taldeko
  edozein". El valor se **recorta en silencio** a `irakasle_max`.
- **`enabled`** (Boolean, col. "Gaituta"), `batch_id`/`department_id` (related,
  para filtrar). **Leyenda en pantalla** (CSS `.fet-simult-list …::before`).

**Botones siempre visibles** en la lista (header `display="always"`, slot nativo
Odoo 17 `control-panel-always-buttons`; el cog "Ekintzak" solo sale al seleccionar
filas). ⚠️ El método de un botón de cabecera en `<tree>` **NO lleva `@api.model`**
(el arg extra de IDs da `TypeError`):
- **"Sortu automatikoki"** → `generate_pairs()` (idempotente): crea un par por
  cada `DESDO_`/`HE_` emparejando por código sin prefijo (DESDO_=6, HE_=3);
  pre-rellena `jatorri_ids=[origen]`; conserva `enabled`/`modua` ya editados.
- **"Desdoble/agrupazio berria"** → abre `op.fet.grouping` (ver #4b).

**Searchpanel** por **Mintegia** + **Mota** (filtros Desdobleak/Eleanitzak).

**Semántica FET (a implementar en el generador):**
- Las N `copy_desdoble_orduak` de un `DESDO_` son un **POOL de horas** que el profe
  de apoyo distribuye LIBREMENTE entre los módulos de `jatorri_ids` (mismo grupo).
  Ej: `DESDO_1MSS2_MUNTAIA`=3h con orígenes MUNTAIA/SEGUR/PBSE → 2h SEGUR+1h
  MUNTAIA, o 2h PBSE+1h SEGUR, etc. Cada hora coincide con UNA sesión de ALGUNO de
  los orígenes (NO es una sesión única que bloquee a todos a la vez). Mapeo
  probable: N sub-actividades de 1h, cada una `SameStartingTime` con una sesión de
  algún origen. Más orígenes = más combinaciones = horario más flexible.
- `modua`=**banatua** → `SameStartingTime` + aulas distintas (el profe `DESDO_`
  cuenta como una gela/irakasle más → máx = 1+orígenes); **berean** → misma aula,
  `irakasle_kop_id` profes dentro.
- `edozein_tekniko/amankomun/ambos` → el origen deja de ser fijo: la copia puede
  coincidir con cualquier módulo del grupo del tipo indicado (a mapear).

### #4b · Desdoble/Agrupación manual con aforo  ✅
- Modelos `op.fet.grouping` + `op.fet.grouping.line`.
- `mota` **bateratu** (varios grupos → misma aula) / **banatu** (grupo → varias
  aulas). `batch_ids` (≥1), `classroom_ids` (≥1).
- Cálculo en vivo: `student_total` (alumnos `studying` vía
  `op.batch.fet_student_count`) y `capacity_total` (suma de `capacity` de aulas).
  - bateratu → aviso si `student_total > capacity_total`.
  - banatu → líneas (taldea, gela, ikasleak); si una aula supera su aforo, **fila
    en rojo** + **banner "Aforoa gainditua!"**.
- ⚠️ **El aviso de aforo solo funciona donde haya `capacity`**: a 2026-06-29 hay
  **28 de 63 aulas** con aforo (faltan 35). Falta rellenar `capacity` en Gelak.

### #4c · Modulu Bateratuak  ✅  (2026-07-01)
Menú **Modulu Bateratuak** (seq 45). Modelo `op.fet.bateratua`: une módulos de
**distintos zikloak/mintegiak** que se imparten JUNTOS en la misma aula
(normalmente el mismo profe). Ej: `2INF4_EEE` + `1ELE1_EEE`.
- **`subject_ids`** (M2M, col. "Moduluak"): selección **TOTALMENTE ABIERTA** (sin
  dominio, cualquier `op.subject`); widget `many2many_tags` + `context={'show_code':1}`
  (muestra el código); `@api.constrains` exige **≥2** módulos.
- **`irakasle_ids`** (M2M editable, col. "Irakasleak"): profes que REALMENTE
  estarán en el aula. Dominio al pool `irakasle_erabilgarri_ids` (profes de los
  módulos); onchange auto-rellena con todos y el usuario **quita** los que no van
  para dejar **solo uno**. En FET solo esos se asignan; los quitados quedan libres.
- **`classroom_ids`** (M2M, col. "Gela erabilgarriak"): **opcional**. Dominio al
  pool `gela_esleipena_ids` (`gela_teoria_ids`+`tailerra_ids` de los módulos, de
  Gela Esleipena); onchange auto-rellena con todas; muestra el **código** de aula
  (`context={'show_code':1}`). **Placeholder "Defektuzko Gela Esleipena"**: si se
  deja vacío → FET usa las aulas de Gela esleipena de cada módulo.
- `name` (computed = códigos unidos por " + "), `enabled`.
- **Regla aulas (2026-07-01)**: solo aulas `irakasgela=True` (docentes) entran a
  FET; enforced en todos los selectores de aula (Gela Esleipena, department.gela_ids,
  #3, #4b grouping, `get_aula_columns`). 30 docentes (todas con aforo) + 36 no docentes.
- Lista editable (`class="hlh-styled"`, decoration-muted si no enabled).
- FET: `ConstraintActivitiesSameStartingTime` + **misma aula** (`SameRoom`) para
  todos los módulos de la línea → una sola clase física. Distinto de #4
  (copias DESDO_/HE_) y de #4b (agrupación de taldeak por aforo).

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

## 4. Datos pendientes (bloquean parte del `.fet`)  — recontado 2026-06-30

Base: **256 módulos** con `gela_orduak > 0` (los que generan actividad).

1. **`banaketa_id`** en `op.subject`: faltan **20** módulos = 2 sueltos
   (`2MLE2_MUME`, `2FMD3_HAUT_2`) + 18 copias `DESDO_`/`HE_` (las `DESDO_` >1h que
   el usuario indicará). También faltan **31** `teoria_praktika_id`. Scripts en
   `FET/banaketa_import/` (ver `PROGRESO_BANAKETA.md`).
2. **`faculty_id`**: faltan **11** módulos sin profe — `2FMD3_HAUT_2`,
   `2SEA3_HAUT_2` + copias `DESDO_`/`HE_`. **Sin profe FET no crea la actividad**;
   revisar si la copia hereda el profe del origen o lleva el de apoyo.
3. **Aula asignada**: faltan **6** módulos sin gela ni tailerra —
   `1IEA2A_IPE_I`, `2IEA2A_EIP_II`, `2SEA3_EIP_2`, `1SEA3_EIP_1`, `1IEA2D_IPE_I`,
   `2IEA2D_EIP_II` (módulos EIP/IPE de proyecto/empresa; **probablemente no
   necesitan aula** — confirmar; podrían quedar fuera del `.fet`).
4. **`capacity`** (aforo) en `op.classroom`: **28 de 66** (faltan **38**). Solo
   afecta al aviso de aforo de #4b, **no bloquea** el `.fet`.

> Prerequisitos ya OK (2026-06-30): `batch_id` en todos los módulos con horas;
> `op.faculty` activos = **165**; `op.batch` activos = **35**; `op.timing` = **6**
> franjas. **`op.session` = 0** (destino del volcado, aún vacío).

---

## 5. Próximos pasos (módulo `openeducat_fet` / generador)

> El módulo/generador `openeducat_fet` **aún no existe** (verificado 2026-06-29);
> todo lo construido vive dentro de `openeducat_hernani`.

1. Cerrar datos pendientes (sección 4): `banaketa_id` (20), `faculty_id` (11),
   decidir las 6 EIP/IPE sin aula y, opcional, `capacity` (38).
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
                                 #   irakasle.kop, grouping(+line), fixed.session,
                                 #   config)
models/op_classroom_ext.py       # gela_mota, irakasgela, solairua
models/op_batch_ext.py           # fet_student_count
models/op_subject_ext.py         # da_kopia/da_desdo, banaketa/T-P, show_code…
views/op_fet_constraints_views.xml
views/op_classroom_views.xml
views/op_sis_menu.xml            # menús SIS (Aste Saioak, Ordutegi murrizpenak)
data/fet_irakasle_kop_data.xml   # opciones 2..8 del desplegable Irakasle kop.
static/src/components/fet_teacher_unavail.js  + xml/fet_teacher_unavail.xml
static/src/components/fet_room_unavail.js     + xml/fet_room_unavail.xml
static/src/css/hernani.css       # .feu-* (rejillas), .fet-simult-list (leyenda)
security/ir.model.access.csv     # ACL de los op.fet.*
../../../load_timings.py         # carga rejilla op.timing
```

---

## 7. Historial de cambios

### 2026-07-01 — DESDOBLE/HE banaketa: flexibilización + GitHub
Sesión centrada en la lista de simultaneidades (`op.fet.simultaneity`) y en dejar
constancia/copia del trabajo. Cambios de código:
- **Menú renombrado** "Saio simultaneoak" → **"DESDOBLE/HE banaketa"** (menuitem
  + acción).
- **`mota`** pasó a **computed stored** desde `copy_id.code` (readonly).
- Fundidos `desdoble_mota`+`eleanitza_mota` en un solo **`modua`** (banatua/berean).
- Origen **Many2many `jatorri_ids`** (multi-origen para desdoble; `HE_` fijo) que
  muestra el **código** (override `op.subject._compute_display_name` con
  `@api.depends_context('show_code')`); nuevo flag `op.subject.da_kopia`.
- Dos toggles **`edozein_tekniko` / `edozein_amankomun`** (transversal =
  ZIA/KOG/ING/FOL/EIE/EIP/IPE) + **leyenda** en pantalla.
- Columna **Modua** dinámica (`modua_azalpena`): "Gela bakarra (X irakasle)" /
  "Gela banatuak (X gela / X irakasle)".
- Desplegable **Irakasle kop.** (`irakasle_kop_id` → nuevo modelo
  **`op.fet.irakasle.kop`**, seed 2..8) con **dominio por fila** `value <=
  irakasle_max` (= **1 + nº orígenes**), recorte en silencio del display.
- Permitido editar **teoría/práctica** en `DESDO_` (dominio `banaketa_orduak`) y
  banaketa **`edozein`** (malgua) para `DESDO_` (ver `PROGRESO_BANAKETA.md`).
- Eliminado el campo muerto `subject_code` (warning "same label").
- **Nuevo apartado #4c "Modulu Bateratuak"** (`op.fet.bateratua`): unir módulos de
  distintos zikloak/mintegiak en la misma aula (selección abierta, aulas opcionales
  → Gela esleipena por defecto). Ver sección #4c. Ampliado: `irakasle_ids` editable
  (quitar profes para dejar solo uno), `classroom_ids` auto-rellenado desde Gela
  Esleipena con código de aula (`show_code`) y placeholder "Defektuzko Gela Esleipena".
- **Regla `irakasgela`**: solo aulas docentes entran a FET; filtro añadido en
  `get_aula_columns` y en #4b grouping (los demás selectores ya lo tenían).
- **Cierre de datos FET** (todo completo): `banaketa_id` 0 sin (HE_1MLE2_EAEL
  copiado del origen; 9 DESDO_ a banaketa `edozein`), `faculty_id` 0 sin, aula 0 sin,
  20 DESDO_ en `edozein_tekniko`, 30 aulas docentes todas con `capacity`. Solo queda
  T/P de DESDO_ (opcional, no bloquea). `op.session` sigue a 0 (falta el generador).

**Infra / copia de seguridad:**
- Commit local `7971878` en rama `17.0`.
- **Push inicial a GitHub** `hlhkudeaketa-odoo/HLH_openeducat`: el clon era
  *shallow* (7 commits) → `git fetch --unshallow origin` (1371 commits) → push OK.
  Rama por defecto puesta a `17.0` y `main` (vacío) borrado.
- **Backups** en `openeducat-project/backups/`: `kudeaketa_*.sql.gz` (BD, pg_dump)
  + `filestore_kudeaketa_*.tar.gz` (adjuntos Odoo).

### ≤ 2026-06-30 — Base FET
Construcción de secciones 1–6: rejilla `op.timing`, `gela_mota`, Gela-esleipena
(OWL), Ordutegi murrizpenak (#1 #3 #4 #4b #5 #6), imports de banaketa y aulas.
Ver el resto del documento.
