# PresupuestarCO — Contexto para Claude

Subí este archivo al inicio de cada chat nuevo, antes de pedir cualquier cambio.
Reemplaza al chat anterior — no hace falta que Claude "recuerde" nada de antes.

## Qué es

SaaS de presupuestos de obra para contratistas colombianos. Fundador y único
desarrollador: Jaime. En fase de lanzamiento (pre-usuarios pagando).

## Stack real

- **Backend**: FastAPI + Python, en `backend/`
- **Frontend**: React + Vite, en `frontend/`
- **Base de datos**: Postgres en Neon
- **Hosting**: Vercel, un solo proyecto sirviendo frontend (estático) + backend
  (función serverless Python vía `api/index.py`)
- **Repo**: `jaimeV2505/presupuestar-co` en GitHub, rama `main`

## Cómo trabajamos (importante)

Jaime usa Claude en el navegador (chat normal), **no Claude Code**. Eso significa:
- Claude no puede leer el repo real directamente ni pushear nada.
- El flujo es: Claude edita una copia local, entrega el archivo completo,
  Jaime lo descarga, lo copia a su proyecto real, verifica (build/tests),
  y recién ahí hace `git add / commit / push` él mismo.
- Para que Claude pueda trabajar con el código real en un chat nuevo, Jaime
  sube un ZIP fresco del repo (sin `.git/`, `node_modules/`, `.venv/`).
- Cuando Claude entrega un archivo para reemplazar, Jaime debe borrar
  cualquier descarga vieja con el mismo nombre antes de descargar el nuevo
  (el navegador a veces reusa una versión vieja cacheada).

## Trampas ya encontradas — no perder horas de nuevo en esto

1. **Hay DOS `requirements.txt`**: uno en la raíz del repo y otro en
   `backend/`. Vercel usa el de la **raíz** (porque `api/index.py` vive ahí).
   Si agregás una dependencia nueva, actualizá los dos para que no se
   desincronicen, pero el que realmente importa para el deploy es el de la raíz.
2. **Vercel a veces sirve caché vieja de CDN** aunque el deploy nuevo ya
   esté "Ready". Si un cambio no se ve pese a pushear y esperar, antes de
   seguir debuggeando: Vercel → CDN → Caches → Purge cache → "All content" →
   capa "CDN, ISR, and Image Cache".
3. **Verificar `git status` / `git diff` antes de asumir que algo se
   commiteó**. Varias veces un archivo quedó listo en la copia de trabajo
   pero nunca llegó a git porque faltó el `git add`/`commit`/`push`.
4. Para forzar un redeploy sin cambios de código reales: `git commit
   --allow-empty -m "..."` + `git push`.
5. Verificar siempre con `grep`/`cat` que el archivo que Jaime copió
   localmente tiene el cambio esperado ANTES de pedirle que corra el build
   — ahorra una ronda completa si la descarga falló o fue la vieja.

## Estado actual del negocio (plan/acceso)

- Plan gratis: **5 presupuestos de por vida** (no mensual — se cambió de
  3/mes a esto en la fase de lanzamiento).
- Pago automático (Wompi + manual) **desactivado por ahora**, a propósito.
  Quien llega al límite pide más acceso por el sistema de tickets de
  soporte ya existente; Jaime decide caso por caso.
- Cuentas Pro ya otorgadas quedan como están, sin cambios.

## Tests que existen — correr siempre antes de dar algo por cerrado

```bash
cd backend
source ../.venv/bin/activate
python3 -m compileall -q app && echo "✓ compile OK"
python3 tests/smoke_financiero.py 2>&1 | tail -6
python3 tests/candado_authz.py 2>&1 | tail -3
```

- `smoke_financiero.py`: valida cálculos core (deducciones de ley, AIU,
  redondeo, explosión de insumos, etc.) — no se puede romper esto nunca.
- `candado_authz.py`: verifica que todo endpoint nuevo tenga auth o esté
  deliberadamente en la lista blanca (login, registro, etc.) — si un
  endpoint nuevo falla acá, agregarlo a `LISTA_BLANCA` en
  `backend/tests/candado_authz.py` solo si de verdad debe ser público.

Para frontend:
```bash
cd frontend
npm run build 2>&1 | tail -10
```
Confirmar que el hash del archivo (`index-XXXXXXXX.js`) cambió respecto
al build anterior — si es idéntico, algo no se copió bien.

## Patrones de diseño ya establecidos

- Mobile: fila de botones/íconos que puede crecer → agrupar lo secundario
  en un menú "⋯" desplegable (visible solo mobile, `sm:hidden`), ejemplo
  ya hecho en `Dashboard.jsx` y `Editor.jsx`.
- Un menú desplegable (`absolute`) nunca debe quedar dentro de un
  contenedor con `overflow-x-auto`/`overflow-hidden` — lo recorta.
- Grids de CSS necesitan `min-w-0` explícito en sus hijos para poder
  achicarse en mobile; sin esto, el contenido empuja el ancho más allá
  de la pantalla sin importar cuántos `overflow-x-auto` se agreguen adentro.
- Animaciones con Tailwind: si se usa `animate-[nombre_duracion_easing]`
  (sintaxis de corchetes), Tailwind **no** genera el bloque `@keyframes`
  solo — hay que además registrar `theme.extend.animation` con el mismo
  nombre para que el `@keyframes` se incluya de verdad en el CSS compilado.

## Pendiente conocido (no es que esté roto, está pausado a propósito)

- Wompi en modo producción: cuenta de comercio real pendiente de activar
  (actualmente desactivado del todo, ver arriba).
- 32 departamentos / regiones: pausado, las ciudades actuales alcanzan
  para lanzar.
- Compartir APUs entre usuarios: diseño pendiente.
- Lectura de planos con IA (Claude Vision): código completo y listo,
  inactivo porque no hay `ANTHROPIC_API_KEY` configurada en Vercel.
