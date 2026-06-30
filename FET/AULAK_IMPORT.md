# Import de aulas (gela_teoria_ids + tailerra_ids) — estado

> Estado **2026-06-30**. Fuente: `FET/Copia de Ordutegiak sortzeko.xlsx`
> (1 pestaña por mintegi; las 4 últimas son resúmenes y se ignoran).

## Qué se importó

Por cada módulo: **`gela_teoria_ids`** (aulas teóricas, varias opciones; FET elige
una) y **`tailerra_ids`** (taller(es) de prácticas). Columnas Excel:
`Aula teoria - Opcion 1..4` (K-N) + `Aula práctica` (O). Celdas con `?` → se omiten.

Scripts (idempotentes, odoo shell):
- `import_aulak.py` — parsea el xlsx y escribe los 2 M2M. **APLICADO** (209 módulos).
- `fill_mintegi_gelak.py` — rellena `op.department.gela_ids` con la unión de aulas
  de los módulos de cada mintegi. **APLICADO**.

```bash
docker cp "Copia de Ordutegiak sortzeko.xlsx" odoo19:/tmp/ordutegiak.xlsx
docker exec -i odoo19 odoo shell -d kudeaketa --no-http < import_aulak.py
docker exec -i odoo19 odoo shell -d kudeaketa --no-http < fill_mintegi_gelak.py
```

## Reglas de mapeo

**Aulas (token Excel → op.classroom.code)**: el Excel a veces omite guiones
(`2R01→2-R01`, `3L01→3-L01`). Overrides por nombre/variante: `EXTRA→2-L09`,
`INFOR2→4-L02`, `INFOR3→4-L03`, `1-L02C→1-L02`, `1-L02B→1-L02-B`, `1-R01D→1-R01-D`,
`3-L03/A→3-L03-A`. Combos `2R01 / 2R02 / EXTRA` (con espacios) → varias aulas.

**Aulas creadas** (no existían): `1-L04`, `1-P01`, `1-P02` (mota `gela`, básicas;
renombrar/capacidad pendiente).

**Polivalentes → `gela_tailerra`**: aulas usadas en rol contrario a su `gela_mota`
se reclasificaron: `1-L02-B`, `2-L07`, `2-R02`, `3-L02` (así pasan el dominio de
ambos campos: teoria gela/gela_tailerra, taller tailerra/gela_tailerra).

**Pestaña KOG**: duplica los módulos de ELEK con códigos pelados; **KOG manda
sobre ELEK** (decisión usuario) → se procesa al final y sobrescribe. Verificado:
KOG no borra ninguna aula que ELEK tuviera (0 casos).

**Alias de código de módulo** (mismos del banaketa): taldea `OLHELE1→OLHELE3`;
`TUTO/TUTO1→TUTO_<año>`; `FG_*` literal (sin prefijo); `ID→IDOM`; `EAE→EAEL`
(1MLE2); SEA `DIGI→PSAD_2`; OLHELE `DIGI/PROSOL/IED→*_<año>`, `PROIEK→PRO`,
`IMRTD/BEZ` literales; `EETAK→ICTVE`, `IMRTD→IMRT` (no OLHELE), `BTIETKMM→TENBA`,
`EEEL→EEE`, `IA→HAUT_1`, `PLC→HAUT_2`, `EIP_1/2→EIP_I/II` (árabe en MSS/SEA;
1IEA2D `EIP_1→IPE_I`); anotaciones `" (EEE)"` se eliminan.

**Columnas detectadas dinámicamente** (rev. 2026-06-30): la posición de las
columnas de aula NO es fija — **MEK e INF tienen "Aula teoria - Opcion 5"** (col
15), así que "Aula práctica" cae en col 16 (en el resto, col 15). `import_aulak.py`
detecta las columnas leyendo la fila de cabecera de cada bloque (`Aula teoria...`
/ `Aula práctica`). La pestaña FOL no tiene columnas de Sesión pero las aulas
siguen en K-O. Verificado en las 8 pestañas.

**Copias HE_ (codocencia)**: NO vienen en el Excel; heredan las aulas (teoría +
taller) de su módulo origen (mismo aula, 2 profes). Aplicado por separado tras el
import (12 copias).

**Ajustes manuales 2026-06-30**: `1EMF1_OBF` T/P → `1T/4P` (antes vacío);
aulas `1-P01`/`1-P02` renombradas a `PREFABRIKATUA_1`/`PREFABRIKATUA_2` (code
intacto); `2MLE2_HAUT_2` y `2MLE2_MUMA` → teoría `1-L02` + `1-L02-B`.

**Módulos con práctica sin taller** (grupo C, confirmado por usuario): la práctica
se da en su propia aula de teoría (FMD→DISEINUA, FG→ADITIBA, OLHELE→2-R01/2-R02…).
No necesitan taller aparte.

**Variantes de aula MANTENUA** (rev. 2026-06-30): el Excel usa `1-L02A/B/C` y
formas sin guion `1L02A/B/C`. Mapeo: `*C→1-L02` (MANTENUA C), `*B→1-L02-B`,
`*A→1-L02-A`. Sin esto se perdían (LOMT/EAEL/MUME quedaban sin aula).

**Correcciones manuales en `import_aulak.py`** (reproducibles, se aplican al final):
- `FORCE`: `1ELE1_EEE`→`3-L01` (dato de ELEK, no el de KOG `2-L09`);
  `2MLE2_HAUT_2`→`1-L02`+`1-L02-B` (no está en Excel); `1INF4_MUNTAIA/SAREAK/
  KONF/TUTO_1`→`4-L01`; `2INF4_SISTEMAK/TUTO_2`→`2-L09`+`2-L07` (bloque INF del
  Excel vacío). `2MLE2_MUMA` se rige por el Excel (taller `1-L02-A`).
- `SKIP_PREFIX = ('3OLHELE3_',)`: grupo NO impartido en 26-27 → sin aulas.
- Copias `HE_` (codocencia) **y `DESDO_`** (desdoble; por ahora misma aula que el
  origen con 2 profes — a futuro: selector de opción) heredan aulas del origen en
  el APPLY. `2INF4_PRO`/`2MLE2_PRO` (gela 0) sin aula a propósito.

**Estado**: 217 módulos + 39 copias HE_/DESDO_ con aula. Revisados los 6 mintegiak
(ANIMAZIOA, MEKANIKA, ELEKTRIZITATEA, INFORMATIKA, MANTENUA, + transversales).

## PENDIENTE

- `3OLHMEK3_EAE`: el módulo no existe en Odoo (ya conocido del banaketa).
- (Resuelto 2026-06-30) `PROG`→`HAUT_2`: las optativas IEA vienen con su nombre
  real en el Excel — `IA`→`HAUT_1`, `PROG`→`HAUT_2` (confirmado por horas: 4h).
  **REGLA**: el módulo optativo se mantiene SIEMPRE como `HAUT_1`/`HAUT_2` en Odoo
  (su nombre real cambia cada curso); el Excel trae el nombre real y se mapea al
  HAUT_x vía alias. No renombrar; solo añadir el nombre nuevo al alias cada curso.
- (Inocuo) 5 filas de ELEK con taldea mal escrito `3OLHELE1_*` → KOG las cubre
  bien como `2OLHELE3_*`.

## Siguiente

Fase 3: pantalla dedicada OWL (rejilla módulos × aulas por mintegi) para
gestionar esto en la app en adelante (sin Excel).
