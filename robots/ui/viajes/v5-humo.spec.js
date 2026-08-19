// ═══ VIAJE 5 — HUMO DE VITRINA: ¿la plataforma AMANECIO viva? ═══
import { test, expect } from '@playwright/test'
import { emailUnico, registrarPorAPI, crearProyecto, cerrarBienvenida, abrirHerramientas } from './helpers.js'

test('humo: login por UI, KPIs pintan, badges y modales viven', async ({ page }) => {
  page.on('dialog', d => { throw new Error(`dialogo NATIVO: ${d.type()} "${d.message()}"`) })

  const email = emailUnico('humo')
  const token = await registrarPorAPI(email)
  await crearProyecto(token, { nombre: 'Obra de humo' })

  // LA VITRINA: la landing recibe al visitante con su hero vivo
  await page.goto('/')
  await expect(page.getByTestId('landing-hero')).toBeVisible()
  await expect(page.getByText('Crear cuenta gratis').first()).toBeVisible()
  // el demo del cliente abre (la joya del embudo) y cierra por backdrop
  await page.getByTestId('btn-demo-enlace').click()
  await expect(page.getByTestId('demo-modal')).toBeVisible()
  await page.mouse.click(8, 8)
  await expect(page.getByTestId('demo-modal')).toHaveCount(0)

  // LOGIN COMO HUMANO (el unico viaje que lo hace por UI, a proposito)
  await page.goto('/login')
  await page.getByTestId('auth-email').fill(email)
  await page.getByTestId('auth-password').fill('clave-robot-123')
  await page.getByTestId('auth-submit').click()

  // el modal de bienvenida saluda al primer login: elegir oficio lo cierra
  await expect(page.getByTestId('kpi-0')).toBeVisible({ timeout: 15_000 })
  await cerrarBienvenida(page)

  await expect(page.getByTestId('kpi-3')).toContainText('%')
  // las tarjetas se ABREN: donde vive cada numero
  // 🎯 PARA HOY: el panel vive y habla con datos (o declara el 'al dia')
  await expect(page.getByTestId('para-hoy')).toBeVisible()
  await expect(page.getByTestId('para-hoy')).toContainText('PARA HOY')

  // la pestaña de ANALISIS: la grafica mensual respira
  await page.getByTestId('tab-analisis').click()
  await expect(page.getByTestId('vista-analisis')).toBeVisible()
  await expect(page.getByTestId('grafica-mensual')).toBeVisible()
  await page.getByTestId('tab-inicio').click()

  await page.getByTestId('kpi-0').click()
  await expect(page.getByTestId('kpi-detalle')).toBeVisible()
  await expect(page.getByTestId('kpi-detalle')).toContainText('Obra de humo')
  // 🎯 PARA HOY: el panel vive y habla con datos (o declara el 'al dia')
  await expect(page.getByTestId('para-hoy')).toBeVisible()
  await expect(page.getByTestId('para-hoy')).toContainText('PARA HOY')

  // la pestaña de ANALISIS: la grafica mensual respira
  await page.getByTestId('tab-analisis').click()
  await expect(page.getByTestId('vista-analisis')).toBeVisible()
  await expect(page.getByTestId('grafica-mensual')).toBeVisible()
  await page.getByTestId('tab-inicio').click()

  await page.getByTestId('kpi-0').click()
  await expect(page.getByTestId('badge-sector').first()).toContainText('Privada')
  await expect(page.getByText('Obra de humo')).toBeVisible()

  // el modal de crear abre y cierra sin romperse
  await page.getByTestId('btn-nuevo-presupuesto').click()
  await expect(page.getByTestId('input-nombre-proyecto')).toBeVisible()
  await page.mouse.click(8, 8)   // click al fondo cierra el modal (asi esta disenado)
  await expect(page.getByTestId('input-nombre-proyecto')).toHaveCount(0)

  // entrar al Editor: el buscador vive y las herramientas abren
  await page.getByText('Obra de humo').click()
  await expect(page.getByTestId('abrir-buscador')).toBeVisible()
  await abrirHerramientas(page)
  await expect(page.getByTestId('menu-disenos').first()).toBeVisible()
})
