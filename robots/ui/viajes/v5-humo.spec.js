// ═══ VIAJE 5 — HUMO DE VITRINA: ¿la plataforma AMANECIO viva? ═══
// El mas barato y el mas frecuente: login real por UI, el Dashboard pinta
// sus KPIs, y los organos principales abren y cierran sin JS roto.
import { test, expect } from '@playwright/test'
import { emailUnico, registrarPorAPI, crearProyecto, api, sesion } from './helpers.js'

test('humo: login por UI, KPIs pintan, badges y modales viven', async ({ page }) => {
  // Vigia anti-dialogos-nativos: si Chrome muestra un prompt/confirm, FALLO
  page.on('dialog', d => { throw new Error(`dialogo NATIVO del navegador: ${d.type()} "${d.message()}"`) })

  const email = emailUnico('humo')
  const token = await registrarPorAPI(email)
  await crearProyecto(token, { nombre: 'Obra de humo' })

  // LOGIN COMO HUMANO (unico viaje que lo hace por UI, a proposito)
  await page.goto('/login')
  await page.getByTestId('auth-email').fill(email)
  await page.getByTestId('auth-password').fill('clave-robot-123')
  await page.getByTestId('auth-submit').click()

  // el Dashboard pinta sus 4 KPIs y la tarjeta con su badge de universo
  await expect(page.getByTestId('kpi-0')).toBeVisible()
  await expect(page.getByTestId('kpi-3')).toContainText('%')          // tasa con denominador
  await expect(page.getByTestId('badge-sector').first()).toContainText('Privada')
  await expect(page.getByText('Obra de humo')).toBeVisible()

  // el modal de crear abre y cierra sin romperse
  await page.getByTestId('btn-nuevo-presupuesto').click()
  await expect(page.getByTestId('input-nombre-proyecto')).toBeVisible()
  await page.keyboard.press('Escape')

  // entrar al Editor: la barra de totales vive
  await page.getByText('Obra de humo').click()
  await expect(page.getByTestId('total-obra')).toBeVisible()
  await expect(page.getByTestId('abrir-buscador')).toBeVisible()

  // herramientas abre (el panel de la obra)
  await page.getByTestId('btn-herramientas').click()
  await expect(page.getByTestId('menu-disenos')).toBeVisible()
  await page.keyboard.press('Escape')
})
