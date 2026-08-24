# Asistencia por QR — guía de frontend (`gradebook-web`)

Cómo implementar la asistencia en el frontend. El **backend ya está** (`gradebook-api`):
esta guía describe el flujo, el orden de las llamadas y las piezas a construir en el web.

> Recordatorio de arquitectura (BFF): el navegador **no** le pega a la API directo. Todo pasa por
> `web/services/*.py`, que agrega `X-API-Key` + el `Authorization: Bearer <token>` de la sesión del
> docente. El JS solo llama a rutas del **propio** web (`/admin/...`), que proxean a la API. Ver
> `AGENTS.md` y `web/services/auth.py` como referencia.

---

## 1. Endpoints de la API (referencia)

Todos bajo `/gradebook_api`. Permisos: `asistencias.gestionar` (disparar/enviar/marcar/cerrar) y
`asistencias.leer` (listar/progreso). Un docente `super_admin`/`admin` los tiene.

| # | Método | Path | Para qué | Body / Query |
|---|--------|------|----------|--------------|
| 1 | POST | `/cursadas/{cursadaId}/clases` | Dispara la toma: crea la clase y genera un QR por alumno | `{ "fecha": "YYYY-MM-DD", "titulo": "opcional" }` |
| 2 | POST | `/clases/{claseId}/enviar-qrs` | Envía el **próximo lote** de QRs por email | query opcional `?limite=N` |
| 3 | GET | `/clases/{claseId}/envio` | Progreso del envío (para el polling) | — |
| 4 | POST | `/clases/{claseId}/marcar` | Marca **presente** | `{ "codigo": "ABCD2345" }` o `{ "codigo": "ABCD2345", "manual": true }` o `{ "padron": "116530" }` |
| 5 | GET | `/clases/{claseId}/asistencias` | Listado con estado por alumno | query `estado`, `q`, `_offset`, `_limit` |
| 6 | GET | `/cursadas/{cursadaId}/clases` | Clases con toma de asistencia de la cursada | `_offset`, `_limit` |
| 7 | POST | `/clases/{claseId}/cerrar` | Cierra la clase: pendientes → ausentes | — |

### Formas de respuesta

**(1) POST clases** → `201`
```json
{ "clase": { "id": 5, "cursada_id": 9, "fecha": "2026-09-01", "titulo": "Clase 1", "estado": "abierta", "created_at": "...", "updated_at": null },
  "total_estudiantes": 120, "generados": 120 }
```
Idempotente: si ya se disparó esa fecha, devuelve la misma clase y `generados: 0`.

**(2) POST enviar-qrs** y **(3) GET envio** → `200` (mismo shape)
```json
{ "clase_id": 5, "total": 120, "enviados": 45, "con_error": 1, "quedan": 74, "completo": false, "enviados_en_lote": 15 }
```
(`enviados_en_lote` solo viene en el POST.)

**(4) POST marcar** → `200`
```json
{ "clase_id": 5, "estudiante_id": 3, "padron": "116530", "nombre": "Ana", "apellido": "Perez", "estado": "presente", "metodo": "qr" }
```

**(5) GET asistencias** → `200` (paginado con `_links`) o `204` si no hay
```json
{ "asistencias": [ { "estudiante_id": 3, "padron": "116530", "nombre": "Ana", "apellido": "Perez",
    "email": "a@x", "codigo": "ABCD2345", "estado": "presente", "metodo": "qr", "marcado_at": "...", "enviado": true } ],
  "_links": { "_first": {"href": "..."}, "_next": {"href": "..."} } }
```

**(7) POST cerrar** → `200`
```json
{ "clase_id": 5, "estado": "cerrada", "marcados_ausentes": 74 }
```

### Errores relevantes
- `400 clase.fecha.fuera.de.cursada` — la fecha no cae en el período de la cursada.
- `400 asistencia.marcar.body.invalido` — mandaste `codigo` **y** `padron`, o ninguno.
- `404 cursada.not.found` / `404 clase.not.found` / `404 asistencia.not.found` (código/padrón que no existe en la clase).
- `409 clase.cerrada` — intentaste marcar en una clase cerrada.

---

## 2. Flujo 1 — Botón "Tomar asistencia"

Es un solo botón para el docente, pero por dentro son **2 fases** (generar y enviar), porque en
Vercel un request no puede quedarse minutos mandando mails.

```
[Docente] clic "Tomar asistencia" (elige fecha, opcional título)
   │
   ├─▶ (1) POST /cursadas/{cursadaVigenteId}/clases   → devuelve claseId + total
   │
   └─▶ bucle de envío (mostrar barra de progreso):
         repetir:
            (2) POST /clases/{claseId}/enviar-qrs      → { enviados, total, quedan, completo }
            actualizar barra con enviados/total
         hasta que  completo === true
```

Pseudo-código del orquestador (en el JS del web, llamando a rutas del **web** que proxean):
```js
async function tomarAsistencia(cursadaId, fecha, titulo) {
  const { clase, total } = await postJson(`/admin/asistencia/cursadas/${cursadaId}/clases`, { fecha, titulo });
  let estado;
  do {
    estado = await postJson(`/admin/asistencia/clases/${clase.id}/enviar-qrs`, {});
    pintarProgreso(estado.enviados, estado.total, estado.con_error);
  } while (!estado.completo);
  avisar(`Listo: ${estado.enviados}/${estado.total} enviados`);
}
```

### Reanudar tras una caída de conexión
El progreso **vive en el backend**, no en el navegador. Si se corta la conexión o el docente
recarga:
1. Al volver, llamar **(3) GET `/clases/{claseId}/envio`** para pintar la barra donde estaba.
2. Seguir llamando **(2)** hasta `completo === true`.

No hay estado que guardar en el cliente: reintentar la misma llamada continúa por los que faltan
(idempotente). Puede haber algún email duplicado en el peor caso (preferimos eso a que a alguien no
le llegue). Los que fallan repetidamente aparecen en `con_error` (mostrarlos y ofrecer reintentar
llamando de nuevo a **(2)**; se saltean solos tras el máximo de intentos).

> La `cursadaVigenteId` sale del endpoint de cursos que ya consume el panel
> (`GET /cursadas?codigo=TB022`, la que tiene `vigente: true`).

---

## 3. Flujo 2 — Escanear / marcar (docente en la clase)

Vista "Escanear asistencia" para una clase. Necesita **JS con cámara** (única parte 100% cliente).

```
[Docente] abre "Escanear" de la clase
   │
   ├─▶ cámara + librería QR lee el código del QR del alumno
   │      └─▶ (4) POST /clases/{claseId}/marcar  { codigo }            (metodo = qr)
   │
   └─▶ fallback (si no hay QR):
          - tipear el código corto:  (4) POST .../marcar { codigo, manual: true }   (metodo = manual)
          - o por padrón:            (4) POST .../marcar { padron }                 (metodo = padron)
   │
   └─▶ mostrar "✔ Presente: Apellido, Nombre (padrón)" y seguir con el siguiente (sin recargar)
```

Detalles:
- **Librería de escaneo sugerida**: [`html5-qrcode`](https://github.com/mebjas/html5-qrcode) (cámara +
  decodificación en un componente). Requiere **HTTPS** para acceder a la cámara (Vercel ya es HTTPS;
  en local `localhost` está permitido).
- El QR **codifica el código corto** (ej. `ABCD2345`). Al leerlo, mandalo tal cual en `codigo`.
- Manejo de respuestas: `200` → presente; `409 clase.cerrada` → avisar y no reintentar; `404
  asistencia.not.found` → "código/padrón inválido para esta clase".
- Marcar dos veces al mismo alumno es inofensivo (queda `presente` igual).

---

## 4. Flujo 3 — Ver estado y cerrar

- Tabla con **(5) GET `/clases/{claseId}/asistencias`** (paginada; filtros `estado` y `q`). Mostrar
  `presente` / `ausente` / `pendiente` por alumno, y si el QR fue `enviado`.
- Botón **"Cerrar toma"** → **(7) POST `/clases/{claseId}/cerrar`** (los `pendiente` pasan a
  `ausente`). Después de cerrar, marcar da `409`.
- Listado de clases previas de la cursada con **(6) GET `/cursadas/{cursadaId}/clases`**.

---

## 5. Piezas a construir en `gradebook-web`

1. **`web/services/asistencias.py`** — llamadas HTTP a la API (con `api_headers()` + `Bearer`, como
   los otros services). Una función por endpoint: `crear_clase`, `enviar_qrs`, `estado_envio`,
   `marcar`, `listar_asistencias`, `listar_clases`, `cerrar`. Los reads degradan a `[]`/error
   manejable; en 401/403 devolver `{'unauthorized': True}` (patrón `respuestas_api.py`).
2. **`web/routes/admin/asistencias.py`** — blueprint fino con las rutas del web que el JS llama
   (`/admin/asistencia/...`), que proxean a los services. Registrarlo en el `__init__.py` de admin.
3. **Templates** (`templates/admin/`):
   - `asistencia.html` — panel de la clase: botón "Tomar asistencia", barra de progreso, tabla de
     estado, botón "Cerrar".
   - `asistencia_escanear.html` — vista de cámara + input de fallback.
4. **`static/js/`** — el orquestador del botón (fase generar + bucle de envío + polling), el scanner
   (html5-qrcode + `fetch` a `/admin/asistencia/.../marcar`), y el fetch parcial del listado (misma
   idea de las otras pantallas, sin recargar).
5. **Tests** — services (con `requests` mockeado) y rutas (`app.test_client()`), + mocks JSON en
   `tests/resources/json/asistencias/`.

---

## 6. Checklist de orden (resumen)

1. `GET /cursadas?codigo=TB022` → tomar la cursada `vigente` → `cursadaId`.
2. Botón **Tomar asistencia**: `POST /cursadas/{cursadaId}/clases` → `claseId`.
3. Bucle: `POST /clases/{claseId}/enviar-qrs` hasta `completo` (con `GET /clases/{claseId}/envio`
   para reanudar).
4. En la clase: `POST /clases/{claseId}/marcar` por QR / código / padrón.
5. Estado: `GET /clases/{claseId}/asistencias`; cerrar: `POST /clases/{claseId}/cerrar`.
