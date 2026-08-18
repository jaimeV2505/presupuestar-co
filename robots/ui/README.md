# 🤖 Robot UI — Playwright

**SHIELD prueba que el sistema FUNCIONA; este robot prueba que el humano PUEDE USARLO.**

## Los 5 viajes
| Viaje | Pantalla | Que vigila |
|---|---|---|
| v1-maestro | 📱 390px | recetario → Mis APUs → 🔬 editar → ⚡ aplicar → total cambia → 💸 → Excel |
| v2-venta | 🖥️ + 2do navegador | diseño con diálogo PROPIO → cliente ve/comenta/FIRMA en el pad → notificación → candado |
| v3-asgard | 🖥️ | badge 🏛️, vigía de deducciones (9→[corregir a 5%]), el sello del 1er avance, anexo |
| v4-cierre | 🖥️ | banner 🔒, inputs muertos, duplicar con diálogo → copia viva |
| v5-humo | 🖥️ | login por UI, KPIs pintan, modales abren/cierran |

**Vigía transversal**: `page.on('dialog')` revienta si aparece CUALQUIER diálogo nativo de Chrome.

## Correr local (2 comandos)
```bash
cd frontend && npm run build     # una vez por cambio de frontend
cd robots/ui && npm install && npx playwright install chromium
npx playwright test              # levanta backend+preview SOLO y corre todo
npx playwright test --headed     # VER al robot moverse (demo del producto)
```
El mundo es efímero: sqlite en /tmp, nada toca Neon ni Vercel.

## El contrato de los data-testid
33 etiquetas sembradas (auth-*, kpi-*, btn-*, dialogo-*, total-obra, banner-terminado...).
**Cuando muevas un botón etiquetado, su testid viaja con él** — el robot te grita si lo olvidas.
