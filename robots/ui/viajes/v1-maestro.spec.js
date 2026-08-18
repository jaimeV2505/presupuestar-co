// ═══ VIAJE 1 — EL MAESTRO (movil 390px): el corazon del producto ═══
// 🍳 recetario → ⭐ Mis APUs → agregar pañete → 🔬 editar precio → ⚡ aplicar
// → el TOTAL de la barra CAMBIA → 💸 descuento → exportar Excel de 3 hojas.
// Todo en la pantalla del celular donde vive el maestro real.
import { test, expect } from '@playwright/test'
import { emailUnico, registrarPorAPI, crearProyecto, sesion } from './helpers.js'

test('el maestro: del recetario al Excel, en el celular', async ({ page }) => {
  page.on('dialog', d => { throw new Error(`dialogo NATIVO: ${d.message()}`) })

  const email = emailUnico('maestro')
  const token = await registrarPorAPI(email)
  const p = await crearProyecto(token, { nombre: 'Casa del maestro' })
  await sesion(page, token, { nombre: 'Maestro', email, plan: 'gratis' })

  await page.goto(`/editor/${p.id}`)
  await expect(page.getByTestId('total-obra')).toBeVisible()

  // 1) abrir el buscador y cargar el RECETARIO (via el constructor 🧱)
  await page.getByTestId('abrir-buscador').click()
  // el boton del recetario vive dentro del constructor "Construir mi APU"
  await page.getByText('🧱 Construir mi APU').click()
  await page.getByTestId('btn-recetario').click()

  // 2) la app salta SOLA a ⭐ Mis APUs con las 16 recetas
  await expect(page.getByText('Pañete liso muros 1:4')).toBeVisible({ timeout: 15_000 })

  // 3) agregar el pañete al presupuesto
  await page.getByText('Pañete liso muros 1:4').click()
  await page.keyboard.press('Escape')   // cerrar el buscador

  // 4) el item esta en la tabla con su chip 🔬
  await expect(page.getByText('Pañete liso muros 1:4')).toBeVisible()
  const totalAntes = await page.getByTestId('total-obra').textContent()

  // 5) abrir el ANALISIS y subir el precio del cemento (SU ferreteria)
  await page.getByTestId('chip-analisis').click()
  const precioCemento = page.locator('input[type="number"]').filter({ hasNot: page.locator('[disabled]') }).nth(1)
  // fila del cemento: input de precio (el 2do numerico de la fila 1)
  const filaCemento = page.locator('tr, div').filter({ hasText: 'Cemento gris' }).first()
  await filaCemento.locator('input').nth(2).fill('42000')

  // 6) ⚡ APLICAR: recalcula en el servidor y el precio del item cambia
  await page.getByTestId('btn-aplicar-apu').click()
  await expect(page.getByTestId('total-obra')).not.toHaveText(totalAntes || '', { timeout: 15_000 })

  // 7) 💸 descuento del 5%: chip verde aparece
  await page.getByTestId('btn-descuento').click()
  await page.getByTestId('input-descuento').fill('5')
  await page.getByTestId('btn-aplicar-descuento').click()
  await expect(page.getByText(/-5\s?%|5% de descuento|💸/).first()).toBeVisible({ timeout: 10_000 })

  // 8) exportar el EXCEL del oficio: la descarga llega con nombre .xlsx
  await page.getByTestId('btn-herramientas').click()
  const descarga = page.waitForEvent('download')
  await page.getByText('Excel (.xlsx)').click()
  const archivo = await descarga
  expect(archivo.suggestedFilename()).toMatch(/\.xlsx$/)
})
