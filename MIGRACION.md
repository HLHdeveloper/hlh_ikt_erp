# Guía de migración — CIFP Gizarte Berrikuntza LHII (Odoo + OpenEducat)

Qué tener en cuenta al migrar **Odoo**, **OpenEducat** y la **base de datos**. Aterrizada en esta instalación concreta.

> Documento de referencia. Antes de cualquier migración real, releer y validar contra las notas de versión oficiales de Odoo y OpenEducat del destino.

## Estado actual (punto de partida)

| Componente | Versión real |
|---|---|
| Odoo | **17.0** (`image: odoo:17.0`, build `17.0-20260209`) |
| PostgreSQL | **15** |
| OpenEducat (`core`, `parent`, `classroom`) | **17.0.1.0** |
| Módulo propio | `openeducat_hernani` `17.0.1.0` |

> **Aviso de naming**: aunque todo se llama "19" (carpeta `addons19`, contenedor `odoo19`, `config19`…), realmente es **Odoo 17.0**. Una migración mayor es **17 → 18 → 19**, una versión cada vez (Odoo no permite saltos).

---

## 1. OpenEducat base NO está en el repositorio ⚠️ (riesgo principal)

En `.gitignore` están excluidos `openeducat_core`, `openeducat_parent`, `openeducat_classroom` y el resto de módulos OpenEducat. **Solo `openeducat_hernani` está versionado en git.**

Consecuencias:
- Al clonar el repo en otra máquina **falta toda la base de OpenEducat**; `openeducat_hernani` no instala (depende de `openeducat_core`, `openeducat_parent`, `openeducat_classroom`).
- Para migrar se necesita la versión de OpenEducat **del Odoo destino** (OpenEducat 18.0 para Odoo 18, etc.). No basta con la copia 17.0 local.

**Acción recomendada (ahora):** anotar de dónde y qué versión/commit exacto de OpenEducat se usa, o "vendorizarlo" (guardarlo aparte versionado). Sin esto la instalación no es reproducible.

---

## 2. Módulo `openeducat_hernani` al subir de versión de Odoo

Checklist al pasar a Odoo 18/19:

- **`version` del manifest**: `17.0.1.0` → `18.0.1.0` (y dependencias acordes).
- **Vistas `<tree>` → `<list>`**: en Odoo 18 la etiqueta de lista pasa a `<list>` (`<tree>` queda como alias obsoleto). Hay muchas: `op_subject_views.xml` (reemplaza el `<tree>` entero), vistas heredadas, etc. Revisar todas.
- **OWL (`perfilazioak.js`, `sis_dashboard.js`)**: la API de OWL, `registry`, hooks y servicios (`useService("orm")`) puede cambiar entre versiones. Probar y adaptar.
- **CSS frágil**: la alineación de columnas depende de clases internas del list renderer (`o_list_number_th`, `flex-row-reverse`, `o_list_table`). Odoo las cambia entre versiones → revisar `static/src/css/hernani.css` tras migrar.
- `attrs`/`states` ya están en formato 17 (`invisible="..."`, `column_invisible`); eso no requiere cambios.

---

## 3. Punto más frágil: SQL crudo contra tablas de OpenEducat ⚠️

Métodos RPC (`models/op_faculty_ext.py`) y modelos informe (`models/op_report.py`, que son **vistas SQL** con `_auto = False`) usan **SQL directo** sobre tablas como:

`op_subject`, `op_perfilazio_kargu`, `op_faculty`, `op_department_op_faculty_rel`, `op_kargu`, `res_partner`…

Si OpenEducat renombra una tabla, una columna o el nombre de una relación m2m (p.ej. `op_department_op_faculty_rel`), **estas consultas se rompen, a veces en silencio** (no al instalar, sino al usar la pantalla).

Lo mismo aplica a los scripts raíz, todos con nombres de tabla/columna a re-verificar contra la nueva versión:
- `migrate_laravel_to_odoo.py`
- `patch_menus.py`
- `patch_mintegi_irakasle.py`
- `patch_eu_translations.py`
- `enroll_students.py`
- `load_informatika_modules.py`, `load_mss_modules.py`, `normalize_codes.py`

---

## 4. Base de datos

### Datos que viven SOLO en la BD (no se regeneran desde el código)
- **Perfilazioak**: `op_perfilazio_kargu` (horas de cargos repartidas), `op_subject.faculty_id` (asignación módulo→profesor), y valores de `op_kargu.rpt_total`, `op_subject.gela_orduak/rpt_total/orduak/...`.
- Todos los datos migrados (profesores, alumnos, grupos, matrículas…).
- Traducciones JSON parcheadas en `ir_model_fields`, `ir_ui_menu`, `ir_act_window` (re-ejecutables con los scripts `patch_*`).
- Cualquier edición hecha a mano en la UI.

> La BD es la **fuente de verdad** del trabajo de perfilación. `op.subject.banaketa` ya está como dato XML reproducible. Los `op.report.*` son vistas SQL (no guardan datos).

### Estrategia de migración de la BD

- **Upgrade menor** (parches dentro de 17.0): seguro con
  ```bash
  docker exec odoo19 odoo -u openeducat_hernani -d kudeaketa --stop-after-init
  docker restart odoo19
  ```
- **Upgrade mayor** (17→18→19): Odoo **no** lo hace solo con módulos custom + terceros. El servicio oficial de upgrade y OpenUpgrade **no cubren OpenEducat**. En la práctica suele ser **más limpio**:
  1. Instalar Odoo destino + OpenEducat destino + `openeducat_hernani` adaptado, en BD nueva.
  2. **Re-importar** datos: `migrate_laravel_to_odoo.py` desde el MySQL origen (sigue siendo solo-lectura) + re-ejecutar `patch_*.py` y `enroll_students.py`.
  3. Lo que no esté en MySQL (perfilazioak hechas a mano en Odoo) exportarlo/reimportarlo aparte.

### Backups imprescindibles ANTES de tocar nada

```bash
# 1) Volcado de la BD (formato custom comprimido)
docker exec postgres19 pg_dump -U odoo -d kudeaketa -F c -f /tmp/kudeaketa.dump
docker cp postgres19:/tmp/kudeaketa.dump ./BD_backup/

# 2) Filestore (adjuntos binarios; los assets OWL y traducciones van en la BD)
tar czf BD_backup/filestore_$(date +%F).tgz -C odoo-data19 filestore
```

> `BD_backup/`, `postgres-data19/` y `odoo-data19/` están **gitignored**: no se suben a GitHub. Protegerlos por separado (copia externa).

---

## Resumen de acciones recomendadas (ahora, no en la migración)

1. **Registrar versión/fuente exacta de OpenEducat** (o vendorizarla) — mayor riesgo de reproducibilidad.
2. Hacer un **backup completo** (`pg_dump` + filestore) antes de cualquier upgrade.
3. Tener presente que el **SQL crudo** y las **vistas `<tree>`/CSS** son lo que más romperá un salto de versión.

---

## Inventario técnico de `openeducat_hernani` (para la migración)

### Modelos propios (tablas en BD)
| Modelo | Tabla | Notas |
|---|---|---|
| `op.kargu` | `op_kargu` | Cargos; campo `rpt_total` (cap de horas) |
| `op.perfilazio.kargu` | `op_perfilazio_kargu` | Reparto horas cargo↔profesor |
| `op.greba` | `op_greba` | Huelgas |
| `op.ordezkapen` | `op_ordezkapen` | Sustituciones |
| `op.subject.banaketa` | `op_subject_banaketa` | Datos en `data/op_subject_banaketa_data.xml` |
| `op.report.*` (5) | — | Vistas SQL `_auto=False` (`op_report.py`) |

### Extensiones (columnas añadidas a tablas OpenEducat)
| Modelo extendido | Ejemplos de campos añadidos |
|---|---|
| `op.subject` | `gela_orduak`, `kode_jima`, `batch_id`, `faculty_id`, `pt_pes`, `hizkuntza`, `kurtsoa`, `orduak`, `rpt_total`, `orduak_zorretan`, `banaketa_id`, `aste_banaketa` (compute) |
| `op.faculty` | `kidergoa`, `kargu_ids`, `greba_ids`, `batch_ids`, relaciones de ordezkapen |
| `op.student` | extensiones de vista/etiquetas |
| `op.batch` | `faculty_ids`, `student_course_ids` |
| `op.department` | `course_ids`, `faculty_ids` |

### Frontend OWL (assets en manifest)
- `static/src/components/sis_dashboard.js` + `static/src/xml/sis_dashboard.xml` (acción `sis_dashboard_action`)
- `static/src/components/perfilazioak.js` + `static/src/xml/perfilazioak.xml` (acción `perfilazioak_action`)
- `static/src/css/hernani.css`

### Dependencias del manifest
`openeducat_core`, `openeducat_parent`, `openeducat_classroom` — los tres deben existir en la versión destino.
