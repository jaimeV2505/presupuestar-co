// ═══ VIAJE 4 — EL CIERRE: terminado es solo lectura, duplicar renace ═══
import { test, expect } from '@playwright/test'
import { emailUnico, registrarPorAPI, crearProyecto, api, sesion } from './helpers.js'

test('el cierre: banner de solo lectura + duplicar con dialogo propio', async ({ page }) => {
  page.on('dialog', d => { throw new Error(`dialogo NATIVO: ${d.message()}`) })

  const email = emailUnico('cierre')
  const token = await registrarPorAPI(email)
  const p = await crearProyecto(token, {
    nombre: 'Obra cerrada', sector: 'publico',
    entidad_nombre: 'Alcaldia Robot', contrato_numero: 'CTO-002-2026',
  })
  await api(token, 'PUT', `/proyectos/${p.id}`, { items: [{ id: 'it1', capitulo: 'OBRA',
    descripcion: 'Pintura fachada', unidad: 'm2', cantidad: 50, precio_unitario: 20000 }] })
  await api(token, 'POST', `/avances/proyectos/${p.id}/avances`,
    { titulo: 'Unico avance', items: [{ id: 'it1', pct: 100 }] })
  await api(token, 'POST', `/proyectos/${p.id}/terminar`)
  await sesion(page, token, { nombre: 'Contratista', email, plan: 'gratis' })

  // ── SOLO LECTURA VISUAL: banner + la fila del presupuesto MUERTA ──
  await page.goto(`/editor/${p.id}`)
  await expect(page.getByTestId('banner-terminado')).toBeVisible()
  // el hallazgo del estreno, ahora vigilado: cantidad y precio deshabilitados
  const filaViva = await page.locator('input[type="number"]:not([disabled]):visible').count()
  expect(filaViva, 'en terminado los number del presupuesto deben estar muertos').toBe(0)
  await expect(page.getByTestId('btn-descuento')).toHaveCount(0)

  // ── DUPLICAR: el dialogo PROPIO pide el nombre y la copia nace editable ──
  await page.getByTestId('btn-duplicar-terminado').click()
  await expect(page.getByTestId('dialogo-input')).toHaveValue(/copia/)
  await page.getByTestId('dialogo-input').fill('Obra renacida')
  await page.getByTestId('dialogo-ok').click()
  await page.waitForURL(/\/editor\/\d+/, { timeout: 15_000 })
  await expect(page.getByTestId('banner-terminado')).toHaveCount(0)
  await expect(page.getByText('Obra renacida').first()).toBeVisible()
})
