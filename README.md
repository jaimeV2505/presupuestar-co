# PresupuestarCO

Presupuestos de obra profesionales en minutos, para el contratista colombiano.
APU 2026 (2,288 actividades) · AIU con IVA sobre utilidad (Art. 462-1 ET) · Enlace WhatsApp con tracking.

## Arquitectura

- **Local (desarrollo):** Docker Compose — FastAPI + SQLite + React. Incluye TODO (también la IA de planos).
- **Producción:** TODO en Vercel — frontend estático + backend como función Python serverless + Vercel Postgres.

```
/api/index.py     <- entrada serverless (importa backend/app/main.py)
/backend          <- FastAPI completo
/frontend         <- React + Vite
/requirements.txt <- deps SLIM para Vercel (Fase 1, sin IA pesada)
/vercel.json      <- build frontend + funcion python + rewrites
```

## Desarrollo local (todo incluido)

```bash
cp .env.example .env   # ANTHROPIC_API_KEY para la IA de planos
docker compose up --build
# http://localhost:3000
```

## Deploy en Vercel (una sola vez, ~10 minutos)

1. **Subir a GitHub:**
   ```bash
   git remote add origin https://github.com/TU-USUARIO/presupuestar-co.git
   git branch -M main
   git push -u origin main
   ```

2. **Importar en Vercel:** [vercel.com](https://vercel.com) → Add New → Project → tu repo.
   - Root Directory: **la raíz del repo** (no cambiar)
   - Framework Preset: **Other** (el vercel.json ya define todo)
   - Deploy.

3. **Crear la base de datos:** en el proyecto de Vercel → pestaña **Storage** →
   Create Database → **Postgres** (Neon) → Connect. Vercel agrega `DATABASE_URL` sola.

4. **Variable de sesiones:** Settings → Environment Variables →
   `JWT_SECRET` = cualquier texto largo aleatorio (50+ caracteres).

5. **Redeploy** (Deployments → ⋯ → Redeploy) para que tome la BD y el secret.

Listo. Desde ahí, cada `git push` despliega automáticamente.

## Qué funciona dónde

| Feature | Local (Docker) | Vercel |
|---|---|---|
| Cotizador completo (Fase 1) | ✓ | ✓ |
| Auth, proyectos, AIU/IVA, PDF/Excel | ✓ | ✓ |
| Enlace WhatsApp + visto + aceptar/rechazar | ✓ | ✓ |
| Lectura de planos con IA (premium, Fase 3) | ✓ | — (requiere Tesseract y procesos largos; se activará en su fase con infra dedicada) |

## Flujo diario

```bash
git add -A && git commit -m "mejora" && git push   # Vercel despliega solo
```
