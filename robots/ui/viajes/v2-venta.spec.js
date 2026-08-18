// ═══ VIAJE 2 — LA VENTA: disenos, el enlace y la firma del cliente ═══
import { test, expect } from '@playwright/test'
import { emailUnico, registrarPorAPI, crearProyecto, api, sesion, abrirHerramientas, PNG_1x1 } from './helpers.js'

test('la venta: diseno → enlace → cliente comenta y firma → candado', async ({ page, browser }) => {
  page.on('dialog', d => { throw new Error(`dialogo NATIVO: ${d.message()}`) })

  const email = emailUnico('venta')
  const token = await registrarPorAPI(email)
  const p = await crearProyecto(token, { nombre: 'Apto 501' })
  await api(token, 'PUT', `/proyectos/${p.id}`, { items: [{ id: 'it1', capitulo: 'ACABADOS',
    descripcion: 'Pintura general', unidad: 'm2', cantidad: 100, precio_unitario: 12000 }] })
  await sesion(page, token, { nombre: 'Vendedor', email, plan: 'gratis' })

  // ── EL DUENO: diseno con el dialogo DE LA PLATAFORMA ──
  await page.goto(`/editor/${p.id}`)
  await abrirHerramientas(page)
  await page.getByTestId('menu-disenos').first().click()
  const eleccion = page.waitForEvent('filechooser')
  await page.getByText('📤 Subir diseño').click()
  ;(await eleccion).setFiles({ name: 'render.png', mimeType: 'image/png', buffer: PNG_1x1 })
  await page.getByTestId('dialogo-input').fill('Render sala — opcion 1')
  await page.getByTestId('dialogo-ok').click()
  await expect(page.getByText('Render sala — opcion 1')).toBeVisible({ timeout: 10_000 })
  await page.keyboard.press('Escape')

  const share = await api(token, 'POST', `/share/proyectos/${p.id}/compartir`)
  const t = share.token || (share.url || '').split('/p/').pop()

  // ── EL CLIENTE (otro navegador): ve, comenta y FIRMA en el pad ──
  const ctx = await browser.newContext()
  const cliente = await ctx.newPage()
  cliente.on('dialog', d => { throw new Error(`dialogo NATIVO donde el cliente: ${d.message()}`) })
  await cliente.goto(`/p/${t}`)
  await expect(cliente.getByText('Apto 501').first()).toBeVisible()

  await cliente.getByTestId('btn-ver-disenos').click()
  await expect(cliente.getByText('Render sala — opcion 1')).toBeVisible()
  await cliente.getByTestId('input-comentar-diseno').fill('Me gusta, pero en gris')
  await cliente.getByTestId('btn-enviar-comentario').click()
  await expect(cliente.getByText('Me gusta, pero en gris')).toBeVisible()

  await cliente.getByTestId('btn-aceptar').click()
  await cliente.getByPlaceholder('Tu nombre completo *').fill('Dona Robot Cliente')
  const pad = cliente.locator('canvas').first()
  const caja = await pad.boundingBox()
  await cliente.mouse.move(caja.x + 20, caja.y + 30)
  await cliente.mouse.down()
  await cliente.mouse.move(caja.x + 120, caja.y + 60, { steps: 8 })
  await cliente.mouse.up()
  // aceptar terminos si hay checkbox de "lei el contrato"
  const check = cliente.locator('input[type="checkbox"]').first()
  if (await check.isVisible().catch(() => false)) await check.check()
  await cliente.getByTestId('btn-confirmar-firma').click()
  await expect(cliente.getByText(/firmad|aceptad/i).first()).toBeVisible({ timeout: 15_000 })
  await ctx.close()

  // ── DE VUELTA EL DUENO: notificacion 💬 y el SELLO UI (fila muerta, sin 💸) ──
  await page.goto(`/editor/${p.id}`)
  await expect(page.locator('input[type="number"][disabled]').first()).toBeAttached({ timeout: 15_000 })
  await expect(page.getByTestId('btn-descuento')).toHaveCount(0)
})
