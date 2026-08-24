// Helpers del Robot UI: SIEMBRA por API (rapida), INTERACCION por UI (lo probado)
const API = 'http://127.0.0.1:8000/api'

let _n = 0
export function emailUnico(prefijo = 'robot') {
  _n += 1
  return `${prefijo}-${Date.now()}-${_n}@ui.test`
}

export async function registrarPorAPI(email) {
  const r = await fetch(`${API}/auth/registro`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ acepta_terminos: true, nombre: 'Robot UI', email, password: 'clave-robot-123', ciudad: 'bogota' }),
  })
  if (!r.ok) throw new Error(`registro fallo: ${r.status} ${await r.text()}`)
  const d = await r.json()
  return d.token || d.access_token
}

export async function api(token, metodo, ruta, body) {
  const r = await fetch(`${API}${ruta}`, {
    method: metodo,
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!r.ok) throw new Error(`${metodo} ${ruta} -> ${r.status}: ${await r.text()}`)
  return r.json()
}

export async function crearProyecto(token, extra = {}) {
  return api(token, 'POST', '/proyectos', {
    nombre: extra.nombre || 'Obra del Robot', cliente_nombre: 'Cliente Robot',
    region: 'bogota', ...extra,
  })
}

// Entrar a la app COMO HUMANO: por localStorage (rapido) — el login por UI
// se prueba a fondo en v5-humo; los demas viajes no lo repiten.
export async function sesion(page, token, usuario) {
  await page.addInitScript(([t, u]) => {
    localStorage.setItem('token', t)
    localStorage.setItem('usuario', JSON.stringify(u))
  }, [token, usuario || { nombre: 'Robot UI', email: 'robot@ui.test', plan: 'gratis' }])
}

// Un PNG minusculo de 1x1 para subir como diseno
export const PNG_1x1 = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==',
  'base64')

// El panel Herramientas: en movil es un boton (visible); en desktop es sidebar fija.
// Y el panel se monta 2 veces (sidebar+modal) -> siempre .first() en sus entradas.
export async function abrirHerramientas(page) {
  const btn = page.getByTestId('btn-herramientas')
  if (await btn.isVisible().catch(() => false)) await btn.click()
}

// El modal de bienvenida (onboarding) intercepta clicks en el primer login:
// elegir un oficio lo cierra.
export async function cerrarBienvenida(page) {
  const b = page.getByTestId('bienvenida-maestro')
  if (await b.isVisible().catch(() => false)) await b.click()
}
