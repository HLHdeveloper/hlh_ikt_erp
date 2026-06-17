# Manual de usuario — SIS (Moduluak · Karguak · Perfilazioak)
### Guía para personas que empiezan, paso a paso

> Este manual explica, con palabras sencillas, cómo usar las tres pantallas
> principales del SIS: **Moduluak** (módulos), **Karguak** (cargos) y
> **Perfilazioak** (perfilación). No hace falta saber de informática: solo
> seguir los pasos.

---

## 0. Antes de empezar

- **Cómo entrar**: abre el navegador (Chrome, Firefox…) y entra en la dirección
  de Odoo del centro. Inicia sesión con tu usuario y contraseña.
- **El menú SIS**: arriba verás un menú con apartados. Los que cubre este
  manual son **Moduluak**, **Karguak** y **Perfilazioak**.
- **Guardar**: en las fichas, los cambios se guardan con el icono del **disquete**
  (arriba a la izquierda). En las listas editables, se guarda al salir de la fila
  (clic fuera o tecla *Enter*).
- **Si algo no se ve bien**: pulsa **Ctrl + Mayúsculas + R** para recargar la
  página del todo. Resuelve la mayoría de problemas visuales.

### Pequeño diccionario (euskera → castellano)
| Euskera | Castellano |
|---|---|
| Moduluak | Módulos / asignaturas |
| Karguak | Cargos |
| Irakaslea / Irakasleak | Profesor / profesores |
| Mintegia / Mintegiak | Departamento(s) |
| Taldea / Taldeak | Grupo(s) |
| Zikloa / Zikloak | Ciclo(s) formativo(s) |
| Orduak | Horas |
| Gela | Aula (horas de aula) |
| RPT | Horas de plantilla del módulo/cargo |
| Aste Banaketa | Reparto semanal de horas |
| PT / PES | Cuerpo del profesorado (Técnico / Secundaria) |
| PL1 / PL2 | Perfil lingüístico |
| Eleanitza | Multilingüe (copias HE_) |
| Desdoblea | Desdoble (copias DESDO_) |
| Esleitzeke | Pendiente de asignar |
| Guztira | Total |
| Laburpena | Resumen |

---

## 1. MODULUAK (módulos)

Es la lista de todos los módulos del centro. Cada fila es un módulo de un grupo.

### 1.1. Ver y buscar
- Usa el buscador de arriba para filtrar por **código** o **nombre**.
- Las columnas muestran: código del módulo, grupo (Talde Kodea), PT/PES, PL,
  horas (Orduak), curso, horas de aula (Gela), reparto semanal (Aste Banaketa) y
  las distintas columnas de RPT.

### 1.2. Editar directamente en la lista (solo "Aste Banaketa")
En la lista **solo se puede cambiar la columna "Aste Banaketa"** sin abrir la
ficha:
1. Haz clic en la celda **Aste Banaketa** del módulo.
2. Se abre un desplegable que **solo muestra los repartos que cuadran con las
   horas de aula (Gela)** de ese módulo. Por ejemplo, un módulo de 7 horas de
   aula solo ofrece repartos que suman 7 (7, 4/3, 2/2/2/1…).
3. Elige uno y haz clic fuera de la fila para guardar.

> Si cambias las horas de Gela de un módulo y el reparto ya no cuadra, el campo
> Aste Banaketa **se vacía solo** para que elijas uno nuevo válido.

### 1.3. Editar el resto de datos (en la ficha)
El resto de columnas **no** se editan en la lista. Para cambiarlas:
1. Pulsa el botón **"Fitxa"** (icono de lápiz, primera columna de la fila).
2. Se abre la **ficha del módulo** con todos los campos.
3. Cambia lo que necesites y pulsa el **disquete** para guardar.

---

## 2. KARGUAK (cargos)

Es la lista de cargos (tutorías, coordinaciones, responsables…). Cada cargo
tiene un total de horas (**RPT Total**) que luego se reparte entre profesores.

### 2.1. La ficha de un cargo
Al abrir un cargo verás:
- **Datos básicos**: código, nombre, email y **RPT Total (h/aste)**.
- Dos pestañas:
  - **Uneko Irakasleak** ("profesores actuales"): los profesores que tienen
    asignado ahora mismo ese cargo.
  - **Perfilazio Irakasleak**: el **reparto del cargo por departamento**.

### 2.2. Repartir las horas de un cargo por departamento
En la pestaña **Perfilazio Irakasleak**:
1. Pulsa **"Añadir línea"**.
2. En **Mintegia**, elige el departamento al que corresponde ese cargo.
3. En **PT/PES**, elige el cuerpo.
4. En **Orduak (h/aste)**, escribe las horas de ese cargo para ese departamento.
5. Repite si el cargo se reparte entre varios departamentos.

**RPT Total** se calcula solo: es la **suma** de las horas de todas las líneas.
- Si el cargo **no tiene ninguna línea** de reparto, el RPT Total se queda con el
  valor que escribas a mano.
- Ejemplo: el cargo **BERRIKUNTZA_TALDEA** tiene 1h. Añades una línea
  *Informatika / PES / 1h* y el RPT Total queda en 1h.

> Importante: estas horas son el **máximo** que se podrá repartir luego entre
> profesores en Perfilazioak. Nunca se podrá asignar a profesores más horas que
> el RPT Total del cargo.

---

## 3. PERFILAZIOAK (perfilación)

Es la pantalla donde se reparte el trabajo del curso: qué módulos y cargos da
cada profesor, departamento por departamento.

### 3.1. Cómo está organizada la pantalla
- **Arriba**: selectores de **Mintegia** (departamento), **Zikloa** (ciclo) y
  **Taldea** (grupo). Al elegir un ciclo aparecen los botones **Eleanitza** y
  **Desdoblea**. También están los botones **LABURPENA IKUSI**, **GORDE … 
  PERFILAZIOAK** y **BERTSIOAK**.
- **Panel izquierdo — Irakasleak**: la lista de profesores del departamento.
  Cada profesor muestra:
  - un distintivo **PT/PES** (se puede cambiar haciendo clic en él);
  - un cuadro azul **Gela** (horas de aula sumadas);
  - un cuadro **RPT** con las horas totales. Está en **gris** si va por debajo de
    17, en **verde** cuando llega justo a 17 (perfilación completa) y en
    **amarillo** si pasa de 17 (sobrecarga).
  - Debajo, al seleccionar un profesor, aparece su sección de **Karguak** y su
    **Perfilazio Laburpena**.
- **Panel derecho — Moduluak**: los módulos del grupo elegido. Se asignan
  haciendo **clic** en la fila.
- **Cuadros de resumen del departamento** (debajo del panel izquierdo): ver 3.6.

### 3.2. Asignar un módulo a un profesor
1. Elige **Mintegia → Zikloa → Taldea** arriba.
2. En el panel izquierdo, haz **clic en un profesor** para seleccionarlo (queda
   resaltado).
3. En el panel derecho (Moduluak), haz **clic en un módulo** para asignárselo.
   El módulo se marca como asignado y el cuadro **RPT** del profesor sube.
4. Para **quitar** un módulo, vuelve a hacer clic en él.

> Algunos módulos especiales (de otro departamento) no se asignan con clic, sino
> con un **desplegable** que aparece en su fila.

### 3.3. Asignar horas de un cargo a un profesor
1. Selecciona el profesor (panel izquierdo).
2. En su sección **Karguak**, elige un cargo del desplegable e indica las horas.
3. El sistema **no deja pasar del total del cargo** (RPT Total): si lo intentas,
   avisa con un mensaje. Las horas que quedan libres se ven como *"X/Y h libre"*.

### 3.4. Distintivo PT / PES
- Cada profesor tiene un distintivo **PT** o **PES** que se calcula solo según
  sus módulos.
- Si necesitas cambiarlo a mano, **haz clic en el distintivo** (alterna PT↔PES).

### 3.5. Eleanitza y Desdoblea (copias de módulos)
Algunos módulos se imparten en versión **multilingüe** (Eleanitza) o **desdoblados**
(Desdoblea). Para ello se crean *copias* del módulo:
1. Selecciona el ciclo y el grupo.
2. Pulsa el botón **Eleanitza** (verde) o **Desdoblea** (morado). Son
   excluyentes: activar uno apaga el otro.
3. Se abre la tabla **MODULUAK KOPIATU**. Haz **clic en un módulo** para crear su
   copia (`HE_` para eleanitza, `DESDO_` para desdoble). Vuelve a hacer clic para
   quitarla.
4. En **Desdoblea**, además puedes escribir cuántas horas van al desdoble en la
   columna **Desdoble Orduak**. Al quitar la copia, ese valor vuelve al RPT del
   módulo.

Las copias se reparten luego a profesores **igual que un módulo normal** (clic).

### 3.6. Los cuadros de resumen del departamento
Debajo del panel de profesores verás:
- **Mintegiko taldeak**: por cada grupo, cuántos módulos quedan **sin asignar**
  (esleitzeke_mod) y el total. La fila se pone **verde** cuando está todo
  asignado.
- **Eleanitza / Desdobleak**: horas de las copias creadas. *ordu guztiak* = total
  de horas; *esleitzeke orduak* = horas que aún no tienen profesor. Fila GUZTIRA
  con la suma.
- **Mintegiko karguak**: los cargos de ese departamento. *ordu guztiak* = horas
  del cargo; *esleitzeke orduak* = horas del cargo que faltan por repartir a
  profesores (bajan según vas asignando). Fila GUZTIRA con la suma.
- **Ordu ez lektiboak** (recuadro naranja): total de horas no lectivas del
  departamento = GUZTIRA de Mintegiko karguak + GUZTIRA de Eleanitza/Desdobleak.
- **Plazen laburpena**: dos cuadros (PES y PT) que muestran las **plazas**
  (17 horas = 1 plaza). Por ejemplo, *PES = 3 + 11h* significa 3 plazas completas
  y 11 horas sueltas.

### 3.7. Apoyo Educativo
En ciclos con apoyo (OLHMEK/OLHELE), el botón **"+ Apoyo Educativo"** abre una
tabla con un tope de horas editable. Vas creando módulos de apoyo y la suma de
sus horas no puede pasar del tope (al llegar, muestra **BETETA** = completo).

### 3.8. LABURPENA IKUSI (ver el resumen del departamento)
El botón **LABURPENA IKUSI** muestra, de un vistazo, la perfilación de **todos**
los profesores del departamento en tarjetas. Ahí también puedes:
- Ver los roles de cada profesor (mintegiburua, tutor…).
- En las plazas "impersonales" (INFO_X1, INFO_X2…), elegir con un desplegable
  qué **ordezkoa** (sustituto) cubrirá esa plaza. Es solo una anotación.

---

## 4. PASOS PARA PERFILAR UN DEPARTAMENTO (de principio a fin)

Sigue este orden para perfilar un departamento completo:

1. **Preparar los cargos (una vez).** En **Karguak**, abre cada cargo del
   departamento y, en la pestaña **Perfilazio Irakasleak**, añade la línea
   *Mintegia + PT/PES + horas*. Así el cargo queda con su RPT Total correcto.
   *(Sin este paso, en Perfilazioak no habrá horas de cargo que repartir.)*

2. **Entrar en Perfilazioak y elegir el departamento** (Mintegia) arriba.

3. **Crear las copias Eleanitza/Desdoblea que toquen.** Para cada grupo que las
   necesite: elige el ciclo y el grupo, activa **Eleanitza** o **Desdoblea**, y
   marca los módulos en **MODULUAK KOPIATU** (en desdoble, fija las horas).

4. **Repartir los módulos.** Grupo a grupo (Taldea): selecciona un profesor y
   ve haciendo clic en sus módulos. Repite con cada profesor hasta que la tabla
   **Mintegiko taldeak** quede en **verde** (todos los módulos asignados).

5. **Repartir las horas de los cargos.** Selecciona cada profesor y, en su
   sección **Karguak**, asígnale las horas de sus cargos. Vigila que la tabla
   **Mintegiko karguak** vaya bajando su *esleitzeke* hasta 0.

6. **Ajustar el distintivo PT/PES** de los profesores si hiciera falta (clic en
   el distintivo).

7. **Revisar el equilibrio.** Mira el cuadro **RPT** de cada profesor: el objetivo
   normal es **17h** (verde). Comprueba **Plazen laburpena** y **Ordu ez
   lektiboak**.

8. **Ver el resumen** con **LABURPENA IKUSI** y, en las plazas impersonales,
   anotar el ordezkoa que las cubrirá.

9. **Guardar la configuración** (siguiente apartado).

---

## 5. GUARDAR CONFIGURACIONES Y DESCARGAR JSON

La perfilación de un departamento se puede **guardar como versión** para no
perderla y poder volver atrás.

### 5.1. Guardar una versión
- Pulsa **"GORDE <DEPARTAMENTO> PERFILAZIOAK"**, ponle un nombre y acepta.
- Se guarda una "foto" del reparto: qué módulo tiene cada profesor, las horas de
  cargos y el distintivo PT/PES.

### 5.2. Gestionar versiones (BERTSIOAK)
Pulsa **"BERTSIOAK"** para abrir el panel de versiones. Cada versión muestra
cuántos módulos y cargos tiene, y ofrece:
- **Kargatu** (cargar): vuelve a esa versión. Antes de sobrescribir, el sistema
  **guarda solo** el estado actual (autoguardado), por si quieres recuperarlo.
- **Deskargatu** (descargar): baja la versión como **archivo JSON** a tu
  ordenador. Sirve para tener una copia o pasarla a otro departamento.
- **Ezabatu** (borrar): elimina la versión.
- **Inportatu** (importar): sube un archivo JSON guardado antes.

### 5.3. Qué es el archivo JSON
Es un archivo de texto pequeño con la perfilación guardada. Al **importarlo**, el
sistema reconoce a los profesores por su **email** (y crea automáticamente las
plazas impersonales que falten). Lo que no consiga emparejar, te lo avisa.

---

## 6. Consejos rápidos

- Trabaja **departamento a departamento** y **grupo a grupo**; es más fácil no
  perderse.
- El **color del cuadro RPT** es tu mejor guía: gris (falta), verde (17 justo),
  amarillo (pasado).
- Guarda una **versión** cada vez que termines algo importante; recuperar es
  fácil.
- Si la pantalla se ve rara, **Ctrl + Mayúsculas + R**.

---

*Este manual se irá ampliando y mejorando. Si echas en falta algo o algún paso no
queda claro, anótalo para añadirlo en la próxima versión.*
