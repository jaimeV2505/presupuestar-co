import React, { useState, useEffect, useRef } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Building2, Loader2 } from 'lucide-react'
import { authAPI, recuperarAPI } from '../services/api'

// ── Fuerza de contraseña: largo, mayúscula, minúscula, número, símbolo ──
function evaluarFuerza(pw) {
  const reglas = [
    { ok: pw.length >= 8, label: '8+ caracteres' },
    { ok: /[A-Z]/.test(pw), label: 'Una mayúscula' },
    { ok: /[a-z]/.test(pw), label: 'Una minúscula' },
    { ok: /[0-9]/.test(pw), label: 'Un número' },
    { ok: /[^A-Za-z0-9]/.test(pw), label: 'Un símbolo (opcional)' },
  ]
  const cumplidas = reglas.filter(r => r.ok).length
  const nivel = pw.length === 0 ? 0 : cumplidas <= 1 ? 1 : cumplidas === 2 ? 2 : cumplidas === 3 ? 3 : 4
  const estilos = [
    { texto: '', color: '' },
    { texto: 'Muy débil', color: 'bg-red-400', tcolor: 'text-red-500' },
    { texto: 'Débil', color: 'bg-orange-400', tcolor: 'text-orange-500' },
    { texto: 'Aceptable', color: 'bg-amber-400', tcolor: 'text-amber-600' },
    { texto: 'Fuerte', color: 'bg-emerald-500', tcolor: 'text-emerald-600' },
  ]
  return { reglas, nivel, ...estilos[nivel] }
}

function BarraFuerza({ password }) {
  const f = evaluarFuerza(password)
  if (!password) return null
  return (
    <div className="animate-fadeIn -mt-1">
      <div className="flex gap-1">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className={`h-1.5 flex-1 rounded-full transition-colors ${i <= f.nivel ? f.color : 'bg-slate-200'}`} />
        ))}
      </div>
      <div className="flex items-center justify-between mt-1.5">
        <span className={`text-[10px] font-semibold ${f.tcolor}`}>{f.texto}</span>
        <span className="text-[9px] text-slate-400">
          {f.reglas.filter(r => !r.ok && r.label !== 'Un símbolo (opcional)').map(r => r.label).join(' · ') || '✓ cumple lo básico'}
        </span>
      </div>
    </div>
  )
}

// ── Calculadorita animada — el momento de "abrimos la cuenta" ──
function CalculadoraAnimada() {
  return (
    <svg viewBox="0 0 64 64" className="w-9 h-9">
      <rect x="8" y="4" width="48" height="56" rx="6" fill="#1C3A5E" />
      <rect x="14" y="10" width="36" height="14" rx="3" fill="#EEF2F8" />
      <text x="44" y="20" textAnchor="end" fontSize="10" fontFamily="monospace" fill="#1C3A5E">
        <animate attributeName="x" values="44;44" dur="0.01s" />
        <set attributeName="opacity" to="1" />
        0
        <animate attributeName="opacity" values="0;1;1;0" dur="1.6s" repeatCount="indefinite" begin="0s" />
      </text>
      {[0, 1, 2, 3, 4, 5, 6, 7, 8].map(i => {
        const col = i % 3, row = Math.floor(i / 3)
        return (
          <rect key={i} x={14 + col * 13} y={30 + row * 10} width="10" height="7" rx="1.5" fill="#3D70A9">
            <animate attributeName="opacity" values="0.35;1;0.35" dur="1.2s" repeatCount="indefinite" begin={`${i * 0.12}s`} />
          </rect>
        )
      })}
    </svg>
  )
}

export default function Login({ modo = 'login' }) {
  const nav = useNavigate()
  const [form, setForm] = useState({ email: '', password: '', nombre: '', empresa: '', telefono: '' , acepta_terminos: false })
  const [loading, setLoading] = useState(false)
  const esRegistro = modo === 'registro'
  const [olvide, setOlvide] = useState(false)
  const [enviado, setEnviado] = useState(false)
  const googleBtnRef = useRef(null)
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID

  const entrarConGoogle = async (respuesta) => {
    try {
      const { token, usuario } = await authAPI.google(respuesta.credential)
      localStorage.setItem('token', token)
      localStorage.setItem('usuario', JSON.stringify(usuario))
      toast.success(`¡Bienvenido, ${usuario.nombre}!`)
      nav('/dashboard')
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'No se pudo entrar con Google — intenta de nuevo')
    }
  }

  useEffect(() => {
    if (!clientId || olvide) return
    const iniciar = () => {
      if (!window.google || !googleBtnRef.current) return
      window.google.accounts.id.initialize({ client_id: clientId, callback: entrarConGoogle })
      googleBtnRef.current.innerHTML = ''
      window.google.accounts.id.renderButton(googleBtnRef.current, {
        theme: 'outline', size: 'large', width: 360,
        text: esRegistro ? 'signup_with' : 'signin_with',
      })
    }
    if (window.google?.accounts?.id) { iniciar(); return }
    const script = document.createElement('script')
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.onload = iniciar
    document.body.appendChild(script)
  }, [olvide, esRegistro])

  const submit = async (e) => {
    e.preventDefault()
    if (olvide) {
      if (!form.email) { toast.error('Escribe tu correo'); return }
      setLoading(true)
      try {
        await recuperarAPI.olvide(form.email)
        setEnviado(true)
      } catch { setEnviado(true) }
      finally { setLoading(false) }
      return
    }
    if (!form.email || !form.password) { toast.error('Email y contraseña requeridos'); return }
    if (esRegistro && !form.nombre) { toast.error('Tu nombre es requerido'); return }
    if (esRegistro && !form.acepta_terminos) { toast.error('Debes aceptar los términos y la política de datos'); return }
    setLoading(true)
    try {
      const res = esRegistro
        ? await authAPI.registro(form)
        : await authAPI.login({ email: form.email, password: form.password })
      localStorage.setItem('token', res.token)
      localStorage.setItem('usuario', JSON.stringify(res.usuario))
      toast.success(esRegistro ? '¡Bienvenido a PresupuestarCO!' : `Hola, ${res.usuario.nombre}`)
      nav('/')
    } catch (err) {
      toast.error(err.message)
    } finally {
      setLoading(false)
    }
  }

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-navy-800 to-navy-600 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <Link to="/" className="inline-flex items-center gap-1.5 text-blue-200 hover:text-white text-xs font-medium mb-4 transition">
          ← Volver al inicio
        </Link>
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-white/10 rounded-2xl mb-3">
            <Building2 className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">PresupuestarCO</h1>
          <p className="text-blue-200 text-sm mt-1">Presupuestos de obra, listos en minutos ⚡</p>
        </div>

        <form key={`${esRegistro}-${olvide}`} onSubmit={submit}
              className="bg-white rounded-2xl shadow-2xl p-6 space-y-4 animate-slideIn">
          <h2 className="font-semibold text-slate-800">
            {esRegistro ? 'Crea tu cuenta gratis' : olvide ? 'Recupera tu contraseña' : 'Inicia sesión'}
          </h2>

          {esRegistro && (
            <>
              <input className="input" placeholder="Tu nombre *" value={form.nombre} onChange={set('nombre')} />
              <input className="input" placeholder="Empresa (opcional)" value={form.empresa} onChange={set('empresa')} />
              <input className="input" placeholder="WhatsApp (ej: 300 123 4567)" value={form.telefono} onChange={set('telefono')} />
            </>
          )}

          <input data-testid="auth-email" className="input" type="email" placeholder="Email *" value={form.email} onChange={set('email')} autoComplete="email" />
          {!olvide && <input data-testid="auth-password" className="input" type="password" placeholder={esRegistro ? 'Contraseña (mínimo 8 caracteres) *' : 'Contraseña *'}
                 value={form.password} onChange={set('password')} autoComplete={esRegistro ? 'new-password' : 'current-password'} />}
          {esRegistro && !olvide && <BarraFuerza password={form.password} />}

          {esRegistro && (
            <label className="flex items-start gap-2 text-[11px] text-slate-500 cursor-pointer">
              <input type="checkbox" data-testid="check-terminos" className="mt-0.5" checked={!!form.acepta_terminos}
                     onChange={e => setForm(f => ({ ...f, acepta_terminos: e.target.checked }))} />
              <span>Acepto los <a href="/legal" target="_blank" rel="noreferrer" className="underline text-navy-600">términos y la política de tratamiento de datos</a> (Ley 1581 de 2012)</span>
            </label>
          )}
          <button data-testid="auth-submit" disabled={loading}
                  className="w-full bg-navy-600 hover:bg-navy-700 text-white font-semibold rounded-xl py-3 transition disabled:opacity-50 flex items-center justify-center gap-2">
            {loading && (esRegistro ? <CalculadoraAnimada /> : <Loader2 className="w-4 h-4 animate-spin" />)}
            {loading ? (esRegistro ? 'Armando tu cuenta...' : 'Un momento...') : olvide ? 'Enviarme el enlace' : esRegistro ? 'Crear cuenta gratis' : 'Entrar'}
          </button>

          {!olvide && clientId && (
            <>
              <div className="flex items-center gap-2 text-[10px] text-slate-400">
                <span className="flex-1 h-px bg-slate-200" /> o <span className="flex-1 h-px bg-slate-200" />
              </div>
              <div ref={googleBtnRef} className="flex justify-center" />
            </>
          )}

          {olvide && enviado && (
            <p className="text-center text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-xl p-3 animate-fadeIn">
              ✓ Listo — si ese correo tiene una cuenta con nosotros, ya te llegó el enlace.<br />
              Revisá también spam o promociones. Es válido por 30 minutos.
            </p>
          )}
          {!esRegistro && (
            <p className="text-center text-xs">
              <button type="button"
                      onClick={() => { setOlvide(v => !v); setEnviado(false) }}
                      className="text-slate-400 hover:text-navy-600 underline">
                {olvide ? '← Volver a iniciar sesión' : '¿Olvidaste tu contraseña?'}
              </button>
            </p>
          )}
          {esRegistro && (
            <p className="text-center text-[10px] text-slate-400">
              Al crear tu cuenta aceptas los{' '}
              <Link to="/legal" className="underline text-slate-500">Términos y la Política de datos</Link>
              {' '}(Ley 1581 de 2012)
            </p>
          )}

          <p className="text-center text-sm text-slate-500">
            {esRegistro ? (
              <>¿Ya tienes cuenta? <Link to="/login" className="text-navy-600 font-medium">Inicia sesión</Link></>
            ) : (
              <>¿Primera vez? <Link to="/registro" className="text-navy-600 font-medium">Crea tu cuenta gratis</Link></>
            )}
          </p>
          {esRegistro && (
            <p className="text-xs text-slate-400 text-center">
              Gratis durante la fase de lanzamiento. Sin tarjeta de crédito.
            </p>
          )}
        </form>
      </div>
    </div>
  )
}
