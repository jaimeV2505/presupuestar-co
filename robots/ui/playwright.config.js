// ═══════════════════════════════════════════════════════════════════════════
// EL MUNDO EFIMERO DEL ROBOT: `npx playwright test` levanta TODO solo —
// FastAPI con sqlite desechable + vite preview del build real — corre los
// viajes y el mundo se evapora. Nada toca Neon ni Vercel.
// ═══════════════════════════════════════════════════════════════════════════
import { defineConfig, devices } from '@playwright/test'
import { mkdtempSync } from 'fs'
import { tmpdir } from 'os'
import { join } from 'path'

const DB = join(mkdtempSync(join(tmpdir(), 'robot-ui-')), 'robot.db')

export default defineConfig({
  testDir: './viajes',
  timeout: 60_000,
  expect: { timeout: 10_000 },
  retries: process.env.CI ? 1 : 0,
  workers: 1,                       // los viajes comparten el mundo: en fila
  reporter: process.env.CI ? [['github'], ['html', { open: 'never' }]] : [['list']],
  use: {
    baseURL: 'http://127.0.0.1:4173',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
    locale: 'es-CO',
  },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
    { name: 'movil', use: { ...devices['Pixel 5'] }, testMatch: /v1-maestro/ },
  ],
  webServer: [
    {
      command: 'uvicorn app.main:app --host 127.0.0.1 --port 8000',
      cwd: '../../backend',
      url: 'http://127.0.0.1:8000/api/health',
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
      env: {
        DATABASE_URL: `sqlite:///${DB}`,
        JWT_SECRET: 'robot-ui-secreto-de-prueba-0123456789abcdef',
        ADMIN_EMAILS: 'robot@ui.test',
        WOMPI_EVENTS_SECRET: 'robot-ui-eventos',
      },
    },
    {
      command: 'npm run preview',
      cwd: '../../frontend',
      url: 'http://127.0.0.1:4173',
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
  ],
})
