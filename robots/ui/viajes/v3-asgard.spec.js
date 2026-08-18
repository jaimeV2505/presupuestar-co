// ═══ VIAJE 3 — ASGARD (obra publica): el vigia de deducciones y el sello ═══
// Crear publico → escribir 9% en Ley 1106 → la alerta ambar aparece →
// [corregir a 5%] la arregla de un clic → avance por API SELLA → el banner
// del presupuesto oficial aparece y el anexo de APUs descarga.
import { test, expect } from '@playwright/test'
import { emailUnico, registrarPorAPI, crearProyecto, api, sesion } from './helpers.js'

test('asgard: vigia de deducciones + el sello del primer avance', async ({ page }) => {
  page.on('dialog', d => { throw new Error(`dialogo NATIVO: ${d.message()}`) })

  const email = emailUnico('asgard')
  const token = await registrarPorAPI(email)
  const p = await crearProyecto(token, {
    nombre: 'Parque municipal', sector: 'publico',
    entidad_nombre: 'Alcaldia Robot', contrato_numero: 'CTO-001-2026',
  })
  await api(token, 'PUT', `/proyectos/${p.id}`, { items: [{ id: 'it1', capitulo: 'OBRA',
    descripcion: 'Anden en concreto', unidad: 'm2', cantidad: 200, precio_unitario: 85000 }] })
  await sesion(page, token, { nombre: 'Contratista Estatal', email, plan: 'gratis' })

  // el Dashboard distingue el universo: badge 🏛️ AL INICIO de la tarjeta
  await page.goto('/')
  await expect(page.getByTestId('badge-sector').first()).toContainText('Pública')

  // ── EL VIGIA: Ley 1106 al 9% dispara la alerta; un clic la corrige ──
  await page.goto(`/editor/${p.id}`)
  await page.getByTestId('btn-herramientas').click()
  await page.getByText(/Contrato y deducciones|Condiciones del contrato/).first().click()
  const filaLey = page.locator('div').filter({ hasText: /1106/ }).last()
  const inputPct = filaLey.locator('input[type="number"]').first()
  await inputPct.fill('9')
  await expect(page.getByText(/Ley 1106.*es del 5%|la ley dice 5%|deberia ser 5/i).first())
    .toBeVisible({ timeout: 10_000 })
  await page.getByRole('button', { name: /corregir a 5/i }).click()
  await expect(inputPct).toHaveValue('5')
  await page.keyboard.press('Escape')

  // ── EL SELLO: primer avance por API → el banner del presupuesto oficial ──
  await api(token, 'POST', `/avances/proyectos/${p.id}/avances`, {
    titulo: 'Acta parcial 1', items: [{ id: 'it1', pct: 40 }] })
  await page.reload()
  await expect(page.getByText(/presupuesto oficial|sellado|SELLADO/i).first())
    .toBeVisible({ timeout: 10_000 })

  // el anexo de APUs descarga como PDF
  await page.getByTestId('btn-herramientas').click()
  const descarga = page.waitForEvent('download')
  await page.getByTestId('btn-export-apus').click()
  expect((await descarga).suggestedFilename()).toMatch(/\.pdf$/)
})
