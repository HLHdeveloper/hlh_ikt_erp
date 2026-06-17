# SIS — Manual resumen (usuarios medios/avanzados)
### Moduluak · Karguak · Perfilazioak — referencia rápida

> Referencia condensada de funcionalidades y particularidades. Para la guía
> paso a paso, ver `MANUAL_SIS_HASIBERRIENTZAT.md`.

---

## Moduluak (op.subject)

- **Lista editable solo en "Aste Banaketa"**; el resto de columnas es de solo
  lectura. Botón **"Fitxa"** (lápiz) en cada fila → abre el formulario para
  editar todo.
- **Aste Banaketa** filtra el desplegable por `guztira = gela_orduak` (un módulo
  de 7h de aula solo ofrece repartos de 7h). Al cambiar Gela, si el reparto deja
  de cuadrar se **vacía solo** (evita el aviso de campo inválido).
- Campos clave: `code`, `kode_jima`, `pt_pes`, `pl` (PL1/PL2/PL1_PL2), `orduak`,
  `gela_orduak`, `kurtsoa`, `banaketa_id`/`aste_banaketa`, `rpt_total`,
  `rpt_reala`, `rpt_zorretan`, `emandako_orduak`, `orduak_zorretan`.
- `talde_kodea` = `batch_id.code` (solo lectura). `mintegiko_irakaslea`: permite
  que un módulo lo imparta profesorado de **otro** departamento.

## Karguak (op.kargu)

- Pestañas en la ficha: **Uneko Irakasleak** (`faculty_ids`) y **Perfilazio
  Irakasleak** (`op.kargu.mintegi`: Mintegia + PT/PES + Orduak; único por
  mintegi+PT/PES).
- **RPT Total**: si hay reparto por mintegi → **suma** de las líneas (campo de
  solo lectura); si no hay reparto → valor **manual**. La sincronización es vía
  `create/write/unlink` (no es un campo computed; evita que el form pise el
  valor con 0).
- El RPT Total es el **tope** de horas repartibles a profesores en Perfilazioak.

## Perfilazioak (acción OWL)

Flujo: **Mintegia → Zikloa → Taldea**. Panel izquierdo (Irakasleak) + panel
derecho (Moduluak + Perfilazio Laburpena del profesor).

### Asignación
- **Módulo → profesor**: clic en la fila de la tabla **Moduluak**. Módulos
  especiales (otro depto.) y TUTO: desplegable en la fila.
- **Kargu → profesor**: sección Karguak del profesor. Guard de servidor:
  `orduak ≤ rpt_total − asignadas_a_otros` (no se supera el RPT Total).
- **Distintivo PT/PES**: automático (PT si algún módulo es PT), clic para forzar.

### Badges del profesor
- **Gela** = Σ `gela_orduak`. **RPT** = Σ `rpt_reala` módulos + horas de karguak.
  Estados: gris `<17`, verde `=17` (completa, comparación redondeada a 2 dec.),
  amarillo `>17` (overload).

### Eleanitza / Desdoblea
- Botones toggle excluyentes (verde / morado). Abren **MODULUAK KOPIATU**: clic
  crea/borra copia `HE_` / `DESDO_`. En desdoble, columna **Desdoble Orduak**
  (al deseleccionar vuelve al RPT del módulo). Filtrado por taldea seleccionada.

### Cuadros de resumen del mintegi (panel izquierdo)
- **Mintegiko taldeak**: `esleitzeke_mod` / `mod_kop` por grupo (verde si 0
  pendientes).
- **Eleanitza / Desdobleak**: filas eleanitza/desdoblea con *esleitzeke* y *ordu
  guztiak* (Σ `rpt_reala` de copias `HE_`/`DESDO_`, pendientes = sin `faculty_id`)
  + fila GUZTIRA.
- **Mintegiko karguak**: cargos del depto.; *ordu guztiak* = Σ líneas del depto.,
  *esleitzeke* = ordu guztiak − repartidas a profesores (`op.perfilazio.kargu`),
  clamp 0, fila GUZTIRA. Decremento en vivo al asignar.
- **Ordu ez lektiboak** (naranja) = Mintegiko karguak GUZTIRA + Eleanitza/
  Desdobleak GUZTIRA.
- **Plazen laburpena**: 2 cuadros PES/PT con **plazas** (17h=1; p.ej. 62h →
  `3 + 11h`) y total de horas. Backend `get_perfilazio_plazak_laburpena`
  (`lekt` = módulos normales, `ez_lekt` = `HE_`/`DESDO_` + karguak por distintivo).

### Otras funciones
- **Apoyo Educativo**: multzo con tope `guztira_orduak`; suma de RPT ≤ tope
  (**BETETA** al llegar).
- **LABURPENA IKUSI**: tarjetas de todos los profesores del depto.; roles;
  asignación de **ordezkoa** a plazas impersonales (1 plaza = 1 ordezkoa, anotación).

### Versiones y JSON (snapshots, op.perfilazio.bertsioa)
- **GORDE …**: guarda versión (módulo→profesor + horas de karguak + PT/PES).
- **BERTSIOAK**: panel con **Kargatu** (autoguarda antes de sobrescribir; conserva
  los últimos 5 autoguardados), **Deskargatu** (export JSON portable por
  email/código), **Ezabatu**, **Inportatu** (crea impersonales que falten; avisa
  de lo no resuelto).

---

## Orden recomendado para perfilar un mintegi
1. Karguak → Perfilazio Irakasleak (definir horas por mintegi).
2. Perfilazioak → elegir Mintegia.
3. Crear copias Eleanitza/Desdoblea (con sus horas).
4. Repartir módulos (Mintegiko taldeak en verde).
5. Repartir horas de cargos (Mintegiko karguak → esleitzeke a 0).
6. Ajustar PT/PES; revisar RPT (17h), Plazen laburpena, Ordu ez lektiboak.
7. LABURPENA IKUSI (+ ordezkoak impersonales).
8. GORDE versión / Deskargatu JSON.

---

## Notas técnicas útiles
- RPT en la perfilación = **`rpt_reala`** (no `rpt_total`), salvo Apoyo y MODULUAK
  KOPIATU.
- Tras cambios visuales: recargar con **Ctrl+Mayús+R**.
- Las versiones pesan ~0,4–1,5 KB; el export JSON es portable entre departamentos
  (empareja por email del profesor / código de módulo y cargo).

*Documento vivo: ampliar conforme evolucione el SIS.*
