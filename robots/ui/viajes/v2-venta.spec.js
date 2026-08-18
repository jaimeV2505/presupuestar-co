// ═══ VIAJE 2 — LA VENTA: disenos, el enlace y la firma del cliente ═══
// El dueno sube un diseno (con el DIALOGO PROPIO, jamas el de Chrome),
// comparte, y EN OTRO NAVEGADOR el cliente ve el diseno, comenta "en gris"
// y FIRMA en el pad. De vuelta: la notificacion 💬 llego y el candado cayo.
import { test, expect } from '@playwright/test'
import { emailUnico, registrarPorAPI, crearProyecto, api, sesion, PNG_1x1 } from './helpers.js'

test('la venta: diseno → enlace → cliente comenta y firma → candado', async ({ page, browser }) => {
  page.on('dialog', d => { throw new Error(`dialogo NATIVO: ${d.message()}`) })

  const email = emailUnico('venta')
  const token = await registrarPorAPI(email)
  const p = await crearProyecto(token, { nombre: 'Apto 501' })
  // items por API (la siembra no es lo probado)
  await api(token, 'PUT', `/proyectos/${p.id}`, { items: [{ id: 'it1', capitulo: 'ACABADOS',
    descripcion: 'Pintura general', unidad: 'm2', cantidad: 100, precio_unitario: 12000 }] })
  await sesion(page, token, { nombre: 'Vendedor', email, plan: 'gratis' })

  // ── EL DUENO: subir un diseno con el dialogo DE LA PLATAFORMA ──
  await page.goto(`/editor/${p.id}`)
  await page.getByTestId('btn-herramientas').click()
  await page.getByTestId('menu-disenos').click()
  const eleccion = page.waitForEvent('filechooser')
  await page.getByText('📤 Subir diseño').click()
  const chooser = await eleccion
  await chooser.setFiles({ name: 'render.png', mimeType: 'image/png', buffer: PNG_1x1 })
  // el titulo lo pide NUESTRO dialogo (si fuera prompt nativo, el vigia de arriba revienta)
  await page.getByTestId('dialogo-input').fill('Render sala — opcion 1')
  await page.getByTestId('dialogo-ok').click()
  await expect(page.getByText('Render sala — opcion 1')).toBeVisible({ timeout: 10_000 })
  await page.keyboard.press('Escape')

  // compartir por API (el link es lo probado, no el boton de compartir)
  const share = await api(token, 'POST', `/share/proyectos/${p.id}/compartir`)
  const rutaCliente = `/p/${share.token || share.share_token || share.url?.split('/p/')[1]}`

  // ── EL CLIENTE (otro navegador, sin sesion): ve, comenta y FIRMA ──
  const ctxCliente = await browser.newContext()
  const cliente = await ctxCliente.newPage()
  cliente.on('dialog', d => { throw new Error(`dialogo NATIVO donde el cliente: ${d.message()}`) })
  await cliente.goto(rutaCliente)
  await expect(cliente.getByText('Apto 501')).toBeVisible()

  // el diseno: la seccion existe (n_disenos>0), lo abre y COMENTA
  await cliente.getByTestId('btn-ver-disenos').click()
  await expect(cliente.getByText('Render sala — opcion 1')).toBeVisible()
  await cliente.getByTestId('input-comentar-diseno').fill('Me gusta, pero en gris')
  await cliente.getByTestId('btn-enviar-comentario').click()
  await expect(cliente.getByText('Me gusta, pero en gris')).toBeVisible()

  // FIRMA: abrir el flujo, escribir nombre/documento y dibujar en el pad
  await cliente.getByRole('button', { name: /Aceptar y firmar|Firmar/ }).first().click()
  await cliente.getByPlaceholder(/Nombre completo/i).fill('Dona Robot Cliente')
  await cliente.getByPlaceholder(/documento|cédula|Cedula/i).fill('51222333')
  const pad = cliente.locator('canvas').first()
  const caja = await pad.boundingBox()
  await cliente.mouse.move(caja.x + 20, caja.y + 30)
  await cliente.mouse.down()
  await cliente.mouse.move(caja.x + 120, caja.y + 60, { steps: 8 })
  await cliente.mouse.move(caja.x + 60, caja.y + 80, { steps: 8 })
  await cliente.mouse.up()
  await cliente.getByRole('button', { name: /Firmar y aceptar|Confirmar firma|Aceptar presupuesto/ }).first().click()
  await expect(cliente.getByText(/firmado|aceptad/i).first()).toBeVisible({ timeout: 15_000 })
  await ctxCliente.close()

  // ── DE VUELTA EL DUENO: notificacion 💬 y el candado visual del sello ──
  await page.goto('/')
  await expect(page.getByText(/comento un diseno|comentó un diseño/).first()).toBeVisible({ timeout: 15_000 })
  await page.goto(`/editor/${p.id}`)
  await expect(page.getByTestId('btn-descuento')).toHaveCount(0)   // 💸 se oculta al sellarse
})
