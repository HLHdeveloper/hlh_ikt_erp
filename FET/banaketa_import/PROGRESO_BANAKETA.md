# Import de `banaketa_id` + `teoria_praktika_id` (op.subject) — progreso

> Estado a **2026-07-01** (base de datos/import: 2026-06-29/30). Para continuar.
> **Novedad 2026-07-01**: ya se puede introducir la banaketa/T-P de los `DESDO_`
> desde la propia pantalla Moduluak (ver sección **C-bis**). El import por script
> sigue igual para los módulos origen.
> Fuente: Excel del usuario "Planificación de módulos por ciclo", **una pestaña por
> mintegi**, tablas con columnas: Módulo · Horas de clase · Sesión 1–4 · Total
> sesiones · Horas de teoría · Horas de práctica · Comprobación · Aula teoria
> Opc.1-4 · Aula práctica.

## Qué se importa (y cómo se mapea)

Por cada fila de módulo del Excel:
- **`banaketa_id`** ← Sesión 1–4. Nombre Odoo = horas por sesión **ordenadas
  descendente** unidas por `/`. Ej. sesiones 2,2,1 → `2/2/1`; 3,2 → `3/2`.
- **`teoria_praktika_id`** ← Horas de teoría / práctica. Nombre = `<T>T/<P>P`.
  Ej. teoría 2, práctica 3 → `2T/3P`; teoría 6, práctica 0 → `6T/0P`.
- **Validación dura**: `suma(sesiones)` y `teoría+práctica` deben **igualar** el
  `gela_orduak` que ya hay en Odoo. La banaketa y la T/P se validan/escriben por
  **separado** (si una falla, se escribe la otra). Las opciones existen en
  `op.subject.banaketa` / `op.subject.teoria.praktika` (totales 1..15).
- **Solo escribe esos 2 campos.** Empareja por `code`. Idempotente.
- **Aula teoria/práctica**: NO se importan aún (futuro: modelar gelak por mintegi
  para el `.fet`; ver pendiente 6 del proyecto).

### Reglas de mapeo de códigos (alias vistos)
- Code Odoo = `<taldea>_<modulo>`; el nombre corto del Excel suele ser el sufijo.
- Alias por nombre/abreviatura: `DIGI`→`PSAD_2` (1SEA3), `EEEL`→`EEE`,
  `IMRTD`→`IMRT`, `BTIETKMM`→`TENBA`, `EETAK`→`ICTVE`, `IA`→`HAUT_1`,
  `PLC`→`HAUT_2`, `FUNDE`→`FE`, `ALMAC`→`ALMA`, `ING_A`→`ING_P_2`, `MOD_OPT_2`→
  `HAUT_2`, `TUTO1`→`TUTO_1`, `PSAD2`→`PSAD_2`.
- **Romano vs árabe** (empleabilidad LPO/FOL): Excel usa `_1/_2`, Odoo usa
  `_I/_II` **salvo** `1MSS2_EIP_1`, `2MSS2_EIP_2`, `1SEA3_EIP_1`, `2SEA3_EIP_2`
  (árabe en Odoo) y `1IEA2D`: Excel `EIP_1`→Odoo `IPE_I`.
- **Taldea**: Excel `OLHELE1`→Odoo `OLHELE3`.
- **EXP_FG**: batch `EXP_ FG` (con espacio); módulos con code literal `FG_*`
  (sin prefijo de taldea).
- Filas `*_PRO` (Proiektu intermodularra, gela 0) → se omiten.

## Mintegiak procesados (✅) — 224/257 módulos origen con banaketa

| Mintegi | Script | Módulos |
|---|---|---|
| ELEKTRIZITATEA | `import_banaketa_ele.py` | 62 |
| MEKANIKA | `import_banaketa_mek.py` | 59 |
| AST (+GHEG suelto) | `import_banaketa_ast.py` | 14 |
| ORIENTAZIO | `import_banaketa_ori.py` | 13 |
| INGELESA | `import_banaketa_ing.py` | 26 |
| LPO/FOL | `import_banaketa_lpo.py` | 23 |

Cómo se ejecuta cada uno (idempotente; `APPLY=True` ya aplicado):
```bash
docker exec -i odoo19 odoo shell -d kudeaketa --no-http < import_banaketa_XXX.py
```

## PENDIENTE para mañana

### A) Mintegiak que faltan por pegar (el usuario aún no los ha mandado)
**INFORMATIKA verificado 2026-06-30: NO está pendiente.** El ciclo `INF`
(`1INF4`/`2INF4`, 13 módulos) ya tiene banaketa+T/P completos y cuadrados en la
BD — entraron por otra vía (no hay `import_banaketa_inf.py`). `2INF4_PRO`
(gela 0, banaketa `JARRAIAN`, sin T/P) es el caso omitido normal. Ya estaba
contado dentro de los 224.

Quedan **4 módulos origen** sin banaketa que NO venían en las hojas recibidas:
- `1MLE2_EAEL` (8h) — MANTENUA
- `2MLE2_HAUT_2` (4h) — MANTENUA
- `2MLE2_MUME` (7h) — MANTENUA
- `2FMD3_HAUT_2` (4h) — MEKANIKA
(probablemente lleguen en pestañas pendientes; si no, pedir sus sesiones.)

### B) Datos sueltos a corregir/confirmar
- `1EMF1_OBF`: T/P del Excel = 6 (2+4) ≠ gela 5 → se escribió banaketa `3/1/1`,
  **T/P quedó vacío**. Falta reparto teoría/práctica correcto (que sume 5).
- `3OLHELE3` ×4 (`IMRTD`,`BTIETKMM`,`BEZ`,`PROIEK`): el grupo existe pero **vacío
  de módulos** en Odoo → el usuario dijo **NO crear** por ahora.
- `3OLHMEK3_EAE` (9h): no existe módulo `EAE` en ese grupo → sin resolver.
- `MUME` (3OLHMEK3, hoja ELE): venía en blanco → omitido.

### C) Copias HE_ y DESDO_ — reglas DISTINTAS (aclarado por el usuario 2026-06-30)

**HE_ (eleanitza = codocencia en la misma aula)**: misma franja y mismas horas
que el original → **copiar `banaketa_id` + `teoria_praktika_id` del origen**
(quitando el prefijo `HE_` del code). Verificado: los 13 HE_ tienen `gela_orduak`
idéntico al origen.
- HECHO 2026-06-30 con `import_banaketa_he.py` (APPLY=True). **12/13 OK**; falta
  solo `HE_1MLE2_EAEL` (origen `1MLE2_EAEL` = uno de los 4 sueltos sin banaketa).

**DESDO_ (desdoble = grupo partido)**: **NO se copia del origen.** El desdoble
tiene su **RPT propio menor** que el del original (el `gela_orduak` de la copia
sí coincide, pero NO es la referencia; manda el RPT). Ej: `1MSS2_SEGUR` RPT 3 →
`DESDO_1MSS2_SEGUR` RPT 1.
- **DESDO_ con RPT = 1h** → banaketa `1`, **flotante**: el profe de apoyo puede
  estar en cualquiera de las horas del grupo (no franja fija). Único pendiente
  así: `DESDO_1IEA2D_IEI` (RPT 1).
- **DESDO_ con RPT > 1h** → el **aste banaketa lo indicará el usuario LUEGO**
  (PENDIENTE, ver sección D). 17 módulos pendientes.

Quedan **19 copias sin banaketa** = 18 DESDO_ + 1 HE_ (`HE_1MLE2_EAEL`).

### C-bis) Herramientas nuevas (2026-07-01) para meter la banaketa de los DESDO_

Cambios de modelo/vista que **desbloquean** los DESDO_ >1h de la sección D sin
scripts (se hacen desde la lista **Moduluak**, columna editable *Aste Banaketa*):

- **DESDO_ referencia sus horas REDUCIDAS**, no `gela_orduak`. Nuevo campo
  `op.subject.banaketa_orduak` (= `rpt_total` de la copia). El dominio de
  `banaketa_id` **y** de `teoria_praktika_id` en los DESDO_ pasó a compararse
  contra **`banaketa_orduak`** (antes `gela_orduak`). Ej: `DESDO_1MSS2_MUNTAIA`
  tiene 3h reducidas → el desplegable ofrece reparto de 3h (`2/1`, `3`, …), no
  las 7h del origen.
- **Se permite editar `teoria_praktika_id` (T/P) en los DESDO_** (antes se
  excluían en `_compute_teoria_praktika_gabe`).
- **Nueva banaketa `edozein` (malgua)** para DESDO_: opción especial de
  **flexibilidad total** (FET coloca las horas donde mejor cuadre, sin franja
  fija). Campo `op.subject.banaketa.edozein` (Boolean) + registro especial
  `edozein` (`guztira=0, egun_kopurua=0`) que `_populate_options` añade. El
  dominio de `banaketa_id` la ofrece **solo** cuando el módulo es DESDO_:
  `['|', ('guztira','=',banaketa_orduak), '&', ('edozein','=',True),
  ('edozein','=',da_desdo)]`.
- Flags de apoyo en `op.subject`: **`da_desdo`** (code empieza por `DESDO_`) y
  **`da_kopia`** (DESDO_ o HE_), computed stored.

**Cómo meter cada DESDO_ >1h de la sección D**: en Moduluak, en la fila del
DESDO_, elegir en *Aste Banaketa* o bien un reparto fijo que sume su RPT
reducido (p.ej. RPT 2 → `1/1` o `2`), o bien **`edozein`** si el profe de apoyo
puede entrar en cualquier franja. Ya no hace falta script.

### D) PENDIENTE — datos que el usuario me pasará LUEGO (recordar)
1. **Banaketa de los 4 módulos sueltos** (sección A): `1MLE2_EAEL` (8h),
   `2MLE2_HAUT_2` (4h), `2MLE2_MUME` (7h), `2FMD3_HAUT_2` (4h). Al cerrar
   `1MLE2_EAEL` se podrá copiar también su `HE_1MLE2_EAEL`.
2. **Aste banaketa de los DESDO_ con RPT > 1h** (17 módulos). Listados con su RPT:
   `DESDO_1AST3_LELA`(2), `DESDO_1SEA3_IEDT`(2), `DESDO_2FMD3_PPMD`(2),
   `DESDO_1AST3_ADLJ`(4), `DESDO_1AST3_ASKT`(4), `DESDO_1AST3_GIGA`(4),
   `DESDO_1AST3_GPHM`(4), `DESDO_1IEA2A_TROTEC`(4), `DESDO_1IEA2D_TROTEC`(4),
   `DESDO_1SEA3_SIZE`(4), `DESDO_2FMD3_FAU`(4), `DESDO_1SEA3_TAIP`(5),
   `DESDO_1SEA3_IEKO`(6), `DESDO_1SEA3_IETP`(6), `DESDO_1ELE1_EEE`(7),
   `DESDO_1MLE2_AUPH`(7), `DESDO_1IEA2D_AUIND`(8).
   (El único DESDO_ de 1h, `DESDO_1IEA2D_IEI`, no necesita dato: banaketa `1`
   flotante; aplicar cuando se confirme.)

## Verificación rápida del avance
```bash
docker exec postgres19 psql -U odoo -d kudeaketa -t -c "
SELECT 'con banaketa', COUNT(*) FROM op_subject WHERE gela_orduak>0 AND banaketa_id IS NOT NULL
UNION ALL SELECT 'SIN (normal)', COUNT(*) FROM op_subject WHERE gela_orduak>0 AND banaketa_id IS NULL AND UPPER(code) NOT LIKE 'DESDO\_%' AND UPPER(code) NOT LIKE 'HE\_%' AND UPPER(code) NOT LIKE 'ERREF%'
UNION ALL SELECT 'con teoria_praktika', COUNT(*) FROM op_subject WHERE gela_orduak>0 AND teoria_praktika_id IS NOT NULL;"
```

## Flujo para procesar una nueva pestaña (recordatorio)
1. Parsear las tablas (cabecera `<TALDEA> — N h/semana`, filas de módulo, ignorar TOTAL).
2. Query a Odoo de esas taldeak (`code`, `gela_orduak`) para resolver alias/validar.
3. Montar `import_banaketa_<mintegi>.py` (copiar uno existente), `APPLY=False` dry-run.
4. Revisar OK / PARCIAL / NOT_FOUND; confirmar alias dudosos con el usuario.
5. `APPLY=True`, ejecutar, verificar avance.
