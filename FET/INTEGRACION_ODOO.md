# Traspaso: integración OpenEduCat (Odoo, máquina 108) <-> FET (máquina 104)

Documento para retomar el trabajo del **módulo de Odoo** desde una sesión de
Claude en la **máquina 108**. La parte de FET (máquina 104) ya está terminada.

## Estado actual (lo que YA funciona)

- **Máquina 104** (Ubuntu): servicio FET en Docker, terminado y validado.
  - Imagen base `fet-cl:7.8.7` (FET compilado sobre Ubuntu 22.04 + Qt5).
  - Servicio `fet-api:7.8.7` (FastAPI) corriendo vía `docker compose`, con
    `restart: unless-stopped` y Docker habilitado en el boot -> arranca solo.
  - Puerto 8000 abierto en el cortafuegos hacia la 108.
  - Proyecto en la 104: `/home/fet/fet-integration/` (Dockerfile, Dockerfile.api,
    docker-compose.yml, api/main.py, scripts/test_fet_api.py, examples/ejemplo.fet).
- **Conexión 108 -> 104 validada**: el script `test_fet_api.py` ejecutado desde
  la 108 envió un `.fet`, esperó y recibió el horario (116 actividades). OK.

## Contrato de la API FET (lo que el módulo Odoo debe consumir)

Base: `http://192.168.1.104:8000`

1. `POST /timetable`
   - multipart/form-data: `file` = archivo .fet, `timelimitseconds` = entero (opcional, def. 300)
   - respuesta `202`: `{"job_id": "<hex>", "status": "pending"}`
2. `GET /timetable/{job_id}`
   - respuesta: `{"job_id", "status", "message"}` con status = pending|running|done|error
3. `GET /timetable/{job_id}/result`
   - cuando status=done: devuelve el XML `application/xml` (raíz `<Activities_Timetable>`)
   - si no está listo: `409`
4. `GET /health` -> `{"status": "ok"}`

Cliente de referencia ya probado: `scripts/test_fet_api.py` (usa `requests`).

## Formato del resultado (activities_timetable.xml)

```xml
<Activities_Timetable>
  <Activity>
    <Id>1</Id>           <!-- coincide con el Id de la actividad enviada en el .fet -->
    <Day>Jueves</Day>
    <Hour>6º 11:10-11:50</Hour>
    <Room>1º A</Room>
  </Activity>
  ...
</Activities_Timetable>
```

El `<Id>` es la clave: hay que enviar cada actividad en el `.fet` con un Id
conocido para luego mapear el resultado de vuelta a la sesión de Odoo correcta.

## Entorno Odoo (máquina 108)

- Odoo **17.0** en Docker (imagen `odoo:17.0`, contenedor `odoo19`, puerto 8069).
  OJO: las carpetas se llaman con sufijo "19" (addons19, config19...) pero la
  versión REAL es Odoo 17.
- PostgreSQL 15 (contenedor `postgres19`, BD `postgres`, user `odoo`).
- Addons del host `~/openeducat-project/addons19` -> `/mnt/extra-addons` en el contenedor.
- Config en `~/openeducat-project/config19` -> `/etc/odoo`.

### Módulos OpenEduCat instalados (en addons19/openeducat_erp/)
openeducat_core, openeducat_classroom, openeducat_timetable, openeducat_activity,
openeducat_admission, openeducat_assignment, openeducat_attendance, openeducat_exam,
openeducat_facility, openeducat_fees, openeducat_library, openeducat_parent,
web_openeducat, y **openeducat_hernani** (módulo personalizado -> revisar).

### Modelos clave a inspeccionar (campos exactos) para generar el .fet
- `op.faculty`  -> profesores (FET: Teachers)
- `op.subject`  -> asignaturas (FET: Subjects)
- `op.batch` / `op.course` -> grupos/clases (FET: Years/Groups/Students)
- `op.classroom` -> aulas (FET: Rooms)
- `op.timing`   -> franjas horarias (FET: Hours)  [openeducat_timetable]
- `op.session`  -> sesiones del horario (FET: Activities; aquí se VUELCA el resultado)

## Plan del módulo Odoo a construir (`openeducat_fet`)

1. **Leer datos** de OpenEduCat (faculty, subject, batch, classroom, timing).
2. **Generar el .fet** (XML FET v5.41): días, horas, profesores, asignaturas,
   estudiantes/grupos, aulas, actividades (cada una con un Id estable) y las
   restricciones básicas (disponibilidad, etc.).
3. **Llamar a la API FET** (los 3 pasos de arriba) con un cliente HTTP en Python.
4. **Parsear** activities_timetable.xml y **crear/actualizar `op.session`**
   mapeando por `<Id>` -> actividad -> sesión, asignando día, hora y aula.
5. **UI**: un botón/acción en Odoo "Generar horario con FET" + vista de estado.

### Primeros pasos sugeridos en la 108
- Inspeccionar los modelos reales:
  `docker exec -it odoo19 odoo shell -d <BD>` y mirar fields, o leer el código en
  `addons19/openeducat_erp/openeducat_core/models/` y `.../openeducat_timetable/models/`.
- Revisar `openeducat_hernani` por si ya añade campos/relaciones útiles.
- Confirmar el nombre de la base de datos (para `op.session` etc.).

## Pendientes menores en la 104 (no bloquean Odoo)
- Persistencia de los "tickets" (ahora en memoria; si se reinicia el contenedor
  se pierde la lista de jobs en curso, no los archivos). Para producción: Redis/DB.
