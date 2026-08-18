// ═══ VIAJE 3 — ASGARD: el vigia de deducciones y el sello UI del avance ═══
import { test, expect } from '@playwright/test'
import { emailUnico, registrarPorAPI, crearProyecto, api, sesion, abrirHerramientas } from './helpers.js'

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
  // por API el contrato nace sin deducciones: sembrar la Ley 1106 MAL (9%) para que el vigia la cace
  await api(token, 'PUT', `/proyectos/${p.id}`, { contrato: { plazo_dias: 45, anticipo_pct: 30,
    deducciones: [{ nombre: 'Contribución obra pública 5% (Ley 1106/2006)', pct: 9 }] } })
  await sesion(page, token, { nombre: 'Contratista Estatal', email, plan: 'gratis' })

  // el Dashboard distingue el universo: badge 🏛️ al inicio
  await page.goto('/')
  await expect(page.getByTestId('badge-sector').filter({ hasText: 'Pública' }).first()).toBeVisible()

  // ── EL VIGIA (seccion "Deducciones de ley" VISIBLE en el editor publico) ──
  await page.goto(`/editor/${p.id}`)
  // el vigia ya deberia estar gritando por el 9% sembrado
  const corregir = page.getByText(/corregir a 5%/).first()
  await corregir.scrollIntoViewIfNeeded()
  await corregir.click()
  const filaLey = page.locator('div').filter({ hasText: /1106/ }).last()
  await expect(filaLey.locator('input[type="number"]').first()).toHaveValue('5')

  // ── EL SELLO: primer avance por API → la fila queda MUERTA en la UI ──
  await api(token, 'POST', `/avances/proyectos/${p.id}/avances`, {
    titulo: 'Acta parcial 1', items: [{ id: 'it1', pct: 40 }] })
  await page.reload()
  await expect(page.locator('input[type="number"][disabled]').first()).toBeAttached({ timeout: 15_000 })
  await expect(page.getByTestId('btn-descuento')).toHaveCount(0)

  // el anexo de APUs descarga como PDF
  await abrirHerramientas(page)
  const descarga = page.waitForEvent('download')
  await page.getByTestId('btn-export-apus').first().click()
  expect((await descarga).suggestedFilename()).toMatch(/\.pdf$/)
})
