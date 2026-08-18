// ═══ VIAJE 1 — EL MAESTRO (movil 390px): el corazon del producto ═══
import { test, expect } from '@playwright/test'
import { emailUnico, registrarPorAPI, crearProyecto, sesion, abrirHerramientas } from './helpers.js'

test('el maestro: del recetario al Excel, en el celular', async ({ page }) => {
  page.on('dialog', d => { throw new Error(`dialogo NATIVO: ${d.message()}`) })

  const email = emailUnico('maestro')
  const token = await registrarPorAPI(email)
  const p = await crearProyecto(token, { nombre: 'Casa del maestro' })
  await sesion(page, token, { nombre: 'Maestro', email, plan: 'gratis' })

  await page.goto(`/editor/${p.id}`)
  const totalObra = page.getByTestId('total-obra')
  await expect(totalObra).toBeAttached()   // en movil vive oculto; el TEXTO igual respira

  // 1) buscador → constructor → RECETARIO
  await page.getByTestId('abrir-buscador').click()
  await page.getByText('⭐ Mis APUs').click()          // el constructor vive en MI pestana
  await page.getByTestId('btn-abrir-constructor').click()
  await page.getByTestId('btn-recetario').click()

  // 2) la app salta SOLA a ⭐ Mis APUs con las 16 recetas
  await expect(page.getByText('Pañete 1:4 muros interiores').first()).toBeVisible({ timeout: 20_000 })

  // 3) agregar el pañete y cerrar el buscador
  await page.getByText('Pañete 1:4 muros interiores').first().click()
  await page.mouse.click(8, 8)   // el buscador cierra por backdrop (como sus hermanos)
  await expect(page.getByTestId('abrir-buscador')).toBeVisible()   // modal cerrado de verdad
  await expect(page.getByText('Pañete 1:4 muros interiores').first()).toBeVisible()
  const totalAntes = await totalObra.textContent()

  // 4) abrir el ANALISIS 🔬 y subir el precio del cemento a SU precio
  await page.getByTestId('chip-analisis').first().click()
  const filaCemento = page.locator('div, tr').filter({ hasText: 'Cemento gris' }).last()
  await filaCemento.locator('input[type="number"]').nth(1).fill('42000')

  // 5) ⚡ APLICAR: recalculo en servidor -> el total del proyecto CAMBIA
  await page.getByTestId('btn-aplicar-apu').click()
  await expect(totalObra).not.toHaveText(totalAntes || '', { timeout: 20_000 })

  // 6) 💸 descuento 5%
  await page.getByTestId('btn-descuento').click()
  await page.getByTestId('input-descuento').fill('5')
  await page.getByTestId('btn-aplicar-descuento').click()

  // 7) exportar el EXCEL del oficio (3 hojas): la descarga llega
  await abrirHerramientas(page)
  const descarga = page.waitForEvent('download')
  await page.getByTestId('btn-export-excel').first().click()
  expect((await descarga).suggestedFilename()).toMatch(/\.xlsx$/)
})
