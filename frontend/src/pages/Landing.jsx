// ═══════════════════════════════════════════════════════════════════════════
// LA VITRINA — el escaparate a la altura de la maquina. Cero dependencias:
// CSS puro + React. Cada efecto cuenta algo REAL del producto.
// ═══════════════════════════════════════════════════════════════════════════
import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'

const COP = (v) => '$' + Math.round(v || 0).toLocaleString('es-CO')

// ── EL TICKER: un numero que sube con alma (rAF + easing) ──
function Ticker({ hasta, dur = 1400, prefijo = '$', activo = true }) {
  const [n, setN] = useState(0)
  useEffect(() => {
    if (!activo) return
    let raf, t0
    const paso = (t) => {
      if (!t0) t0 = t
      const p = Math.min((t - t0) / dur, 1)
      setN(Math.round(hasta * (1 - Math.pow(1 - p, 3))))
      if (p < 1) raf = requestAnimationFrame(paso)
    }
    raf = requestAnimationFrame(paso)
    return () => cancelAnimationFrame(raf)
  }, [hasta, dur, activo])
  return <span className="tabular-nums">{prefijo}{n.toLocaleString('es-CO')}</span>
}

// ── EN-VISTA: dispara animaciones al entrar al viewport ──
function useEnVista(margen = '-80px') {
  const ref = useRef(null)
  const [visto, setVisto] = useState(false)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) setVisto(true) },
      { rootMargin: margen })
    io.observe(el)
    return () => io.disconnect()
  }, [margen])
  return [ref, visto]
}

// ── EL APU QUE SE CONSTRUYE SOLO (el hero) ──
const CHIPS = [
  { e: '🧱', t: 'Cemento gris', d: '0.35 bulto', v: 10474 },
  { e: '⏳', t: 'Arena lavada', d: '0.04 m³', v: 2600 },
  { e: '👷', t: 'Mano de obra', d: 'oficial + ayudante', v: 9000 },
  { e: '🔧', t: 'Herramienta', d: '5% s/ M.O.', v: 450 },
  { e: '🚚', t: 'Transporte', d: 'acarreo', v: 1500 },
]
function ApuVivo() {
  const [n, setN] = useState(0)
  useEffect(() => {
    const id = setInterval(() => setN(x => (x >= CHIPS.length ? 0 : x + 1)), 1100)
    return () => clearInterval(id)
  }, [])
  const total = CHIPS.slice(0, n).reduce((a, c) => a + c.v, 0)
  return (
    <div className="relative bg-navy-800/80 backdrop-blur border border-navy-600/60 rounded-2xl p-5 shadow-2xl shadow-navy-900/60 w-full max-w-md">
      <p className="text-[10px] font-bold tracking-widest text-navy-300 mb-3">APU · PAÑETE 1:4 MUROS — m²</p>
      <div className="space-y-2 min-h-[190px]">
        {CHIPS.map((c, i) => (
          <div key={c.t}
               className={`flex items-center gap-2.5 bg-navy-700/70 border border-navy-600/50 rounded-xl px-3 py-2 transition-all duration-500
                           ${i < n ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-6'}`}>
            <span className="text-lg">{c.e}</span>
            <span className="text-sm text-slate-200 font-medium flex-1">{c.t}
              <span className="text-slate-400 font-normal text-[11px] ml-1.5">{c.d}</span></span>
            <span className="text-sm font-bold text-slate-100 tabular-nums">{COP(c.v)}</span>
          </div>
        ))}
      </div>
      <div className="flex items-center justify-between mt-4 pt-3 border-t border-navy-600/60">
        <span className="text-[11px] font-bold text-navy-300">PRECIO UNITARIO</span>
        <span className="text-2xl font-black text-amber-400 drop-shadow-[0_0_12px_rgba(251,191,36,.35)]">
          <Ticker hasta={total || 24024} dur={700} />
        </span>
      </div>
    </div>
  )
}

// ── EL DOCK: las herramientas que se magnifican ──
const HERRAMIENTAS = [
  { e: '🔬', t: 'Análisis unitario', d: 'Edita el APU con TUS precios y ⚡ aplica' },
  { e: '🍳', t: 'Recetario', d: '16 recetas de arranque, listas para ajustar' },
  { e: '💸', t: 'Descuento', d: 'Negociación prorrateada, sin perder el precio de lista' },
  { e: '🎨', t: 'Diseños', d: 'Tu cliente ve los renders y comenta' },
  { e: '📊', t: 'Incidencia', d: 'Qué capítulo pesa en el total' },
  { e: '🧱', t: 'Explosión', d: 'Cuántos bultos comprar, con desperdicio' },
  { e: '💵', t: 'Actas', d: 'Anticipo, cortes, rete y deducciones a peso' },
]
function Dock() {
  const [cerca, setCerca] = useState(-1)
  return (
    <div className="flex items-end justify-center gap-1.5 sm:gap-2" onMouseLeave={() => setCerca(-1)}>
      {HERRAMIENTAS.map((h, i) => {
        const d = cerca < 0 ? 3 : Math.abs(i - cerca)
        const esc = d === 0 ? 1.45 : d === 1 ? 1.18 : 1
        return (
          <div key={h.t} className="relative flex flex-col items-center"
               onMouseEnter={() => setCerca(i)}>
            {cerca === i && (
              <div className="absolute bottom-full mb-3 w-48 bg-white rounded-xl shadow-2xl border border-slate-200 p-3 text-center animate-[aparecer_.2s_ease-out] z-10">
                <p className="text-xs font-bold text-slate-800">{h.t}</p>
                <p className="text-[10px] text-slate-500 mt-0.5 leading-snug">{h.d}</p>
                <div className="absolute top-full left-1/2 -translate-x-1/2 border-8 border-transparent border-t-white" />
              </div>
            )}
            <div style={{ transform: `scale(${esc}) translateY(${d === 0 ? -10 : d === 1 ? -4 : 0}px)` }}
                 className="w-11 h-11 sm:w-13 sm:h-13 bg-white/90 backdrop-blur border border-slate-200 rounded-2xl
                            flex items-center justify-center text-xl sm:text-2xl shadow-lg cursor-pointer
                            transition-transform duration-200 ease-out">
              {h.e}
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ── LA FIRMA QUE SE DIBUJA SOLA (SVG dash) ──
function FirmaViva({ activa }) {
  return (
    <svg viewBox="0 0 220 70" className="w-full h-16">
      <path d="M12 48 C 30 12, 48 60, 66 38 S 96 14, 112 40 C 122 55, 138 20, 158 34 C 172 44, 186 28, 208 36"
            fill="none" stroke="#1C3A5E" strokeWidth="2.5" strokeLinecap="round"
            style={{ strokeDasharray: 460, strokeDashoffset: activa ? 0 : 460,
                     transition: 'stroke-dashoffset 2.2s ease-in-out .3s' }} />
    </svg>
  )
}

// ── EL ACTA QUE SE LIQUIDA EN SCROLL (la plata a peso) ──
const LIQUIDACION = [
  { t: 'Corte de obra (30%)', v: 6227160, signo: '' },
  { t: 'Amortización del anticipo', v: -1868148, ley: '30% con tope' },
  { t: 'Retegarantía', v: -622716, ley: '10% del corte' },
  { t: 'Ley 1106/2006 — obra pública', v: -311358, ley: '5%' },
  { t: 'Estampilla pro-universidad', v: -249086, ley: '4%' },
  { t: 'Estampilla pro-cultura', v: -124543, ley: '2%' },
]
function ActaViva() {
  const [ref, visto] = useEnVista()
  return (
    <div ref={ref} className="bg-white rounded-2xl border border-slate-200 shadow-xl p-6 max-w-lg w-full">
      <p className="text-[10px] font-bold tracking-widest text-slate-400 mb-4">ACTA PARCIAL Nº 1 · CC-2026-0001</p>
      <div className="space-y-2.5">
        {LIQUIDACION.map((f, i) => (
          <div key={f.t}
               style={{ transitionDelay: `${i * 280}ms` }}
               className={`flex items-baseline justify-between transition-all duration-500
                           ${visto ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-3'}`}>
            <span className="text-sm text-slate-600">{f.t}
              {f.ley && <span className="text-[10px] text-slate-400 ml-1.5">({f.ley})</span>}</span>
            <span className={`text-sm font-bold tabular-nums ${f.v < 0 ? 'text-red-500' : 'text-slate-800'}`}>
              {f.v < 0 ? '−' : ''}{visto ? <Ticker hasta={Math.abs(f.v)} dur={900} activo={visto} /> : '$0'}
            </span>
          </div>
        ))}
      </div>
      <div style={{ transitionDelay: '1800ms' }}
           className={`flex items-center justify-between mt-4 pt-4 border-t-2 border-emerald-200 transition-all duration-700
                       ${visto ? 'opacity-100 scale-100' : 'opacity-0 scale-95'}`}>
        <span className="text-sm font-black text-slate-700">NETO A PAGAR</span>
        <span className="text-2xl font-black text-emerald-600 drop-shadow-[0_0_14px_rgba(16,185,129,.25)]">
          {visto ? <Ticker hasta={3051309} dur={1300} activo={visto} /> : '$0'}
        </span>
      </div>
      <p className="text-[10px] text-slate-400 mt-3 text-right">cada peso, verificado por robots en cada versión</p>
    </div>
  )
}

// ── LA TERMINAL DE LOS ROBOTS (typing) ──
const LINEAS = [
  '✓ 159 pasos de robots recorren la plataforma completa',
  '✓ 49 candados rechazan lo indebido (4xx a propósito)',
  '✓ deducciones de ley liquidadas a peso: $684.987 exactos',
  '✓ 11 candados estructurales vigilan cada versión',
  '✓ firma electrónica con evidencia — Ley 527 de 1999',
]
function Terminal() {
  const [ref, visto] = useEnVista()
  const [n, setN] = useState(0)
  useEffect(() => {
    if (!visto) return
    const id = setInterval(() => setN(x => Math.min(x + 1, LINEAS.length)), 650)
    return () => clearInterval(id)
  }, [visto])
  return (
    <div ref={ref} className="bg-navy-900 rounded-2xl border border-navy-700 shadow-2xl overflow-hidden max-w-lg w-full">
      <div className="flex items-center gap-1.5 px-4 py-2.5 bg-navy-800 border-b border-navy-700">
        <span className="w-2.5 h-2.5 rounded-full bg-red-400/80" />
        <span className="w-2.5 h-2.5 rounded-full bg-amber-400/80" />
        <span className="w-2.5 h-2.5 rounded-full bg-emerald-400/80" />
        <span className="text-[10px] text-navy-300 ml-2 font-mono">shield — cada push</span>
      </div>
      <div className="p-4 font-mono text-[12px] leading-relaxed min-h-[150px]">
        {LINEAS.slice(0, n).map(l => (
          <p key={l} className="text-emerald-400 animate-[aparecer_.3s_ease-out]">{l}</p>
        ))}
        {n < LINEAS.length && <span className="inline-block w-2 h-4 bg-emerald-400 animate-pulse" />}
      </div>
    </div>
  )
}

// ── EL MARQUEE de la base 2026 ──
const ACTIVIDADES = ['Pañete 1:4 muros', 'Mampostería e=12', 'Acero 60.000 PSI', 'Concreto 3000 PSI',
  'Estuco y pintura', 'Enchape cerámico', 'Cubierta teja UPVC', 'Instalación sanitaria', 'Red eléctrica',
  'Pisos en porcelanato', 'Cielo raso PVC', 'Impermeabilización']
function Marquee() {
  const doble = [...ACTIVIDADES, ...ACTIVIDADES]
  return (
    <div className="overflow-hidden py-3 border-y border-navy-700/50 bg-navy-800/40">
      <div className="flex gap-8 whitespace-nowrap animate-[marquesina_28s_linear_infinite] w-max">
        {doble.map((a, i) => (
          <span key={i} className="text-[12px] text-navy-300 font-medium">
            <span className="text-amber-500/80 mr-2">◆</span>{a}
          </span>
        ))}
      </div>
    </div>
  )
}

// ═══════════════════════════ LA PÁGINA ═══════════════════════════
export default function Landing() {
  const [refU, vistoU] = useEnVista()
  return (
    <div className="bg-navy-900 text-white overflow-x-hidden">
      <style>{`
        @keyframes aparecer { from { opacity: 0; transform: translateY(6px) } to { opacity: 1; transform: none } }
        @keyframes marquesina { from { transform: translateX(0) } to { transform: translateX(-50%) } }
        @keyframes rayo { 0% { transform: translateX(-120%) rotate(12deg) } 100% { transform: translateX(240%) rotate(12deg) } }
        @keyframes flotar { 0%,100% { transform: translateY(0) } 50% { transform: translateY(-8px) } }
        @keyframes brillo { 0% { background-position: -200% 0 } 100% { background-position: 200% 0 } }
        @keyframes palabra { from { opacity: 0; transform: translateY(14px) } to { opacity: 1; transform: none } }
        .grid-plano { background-image: linear-gradient(rgba(103,232,249,.05) 1px, transparent 1px),
                      linear-gradient(90deg, rgba(103,232,249,.05) 1px, transparent 1px); background-size: 44px 44px; }
        .cta-brillo { background: linear-gradient(110deg, #B45309 20%, #F59E0B 40%, #FDE68A 50%, #F59E0B 60%, #B45309 80%);
                      background-size: 200% 100%; animation: brillo 3.2s linear infinite; }
      `}</style>

      {/* NAV */}
      <nav className="fixed top-0 inset-x-0 z-40 backdrop-blur bg-navy-900/70 border-b border-navy-700/50">
        <div className="max-w-6xl mx-auto flex items-center justify-between px-5 py-3">
          <span className="font-black text-lg tracking-tight">Presupuestar<span className="text-amber-400">CO</span></span>
          <div className="flex items-center gap-3">
            <Link to="/login" className="text-sm text-navy-200 hover:text-white transition">Entrar</Link>
            <Link to="/registro" className="text-sm font-bold bg-white text-navy-800 rounded-xl px-4 py-2 hover:scale-105 transition">
              Crear cuenta gratis
            </Link>
          </div>
        </div>
      </nav>

      {/* HERO */}
      <header data-testid="landing-hero" className="relative grid-plano pt-28 pb-20 px-5">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-0 left-1/4 w-40 h-[140%] bg-gradient-to-b from-cyan-400/10 to-transparent blur-2xl animate-[rayo_9s_linear_infinite]" />
          <div className="absolute top-0 left-1/2 w-24 h-[140%] bg-gradient-to-b from-amber-400/10 to-transparent blur-2xl animate-[rayo_13s_linear_infinite]" style={{ animationDelay: '3s' }} />
        </div>
        <div className="relative max-w-6xl mx-auto grid lg:grid-cols-2 gap-12 items-center">
          <div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black leading-[1.05] tracking-tight">
              {'Presupuestos de obra que se defienden solos.'.split(' ').map((p, i) => (
                <span key={i} className="inline-block mr-[0.28em] opacity-0 animate-[palabra_.5s_ease-out_forwards]"
                      style={{ animationDelay: `${i * 90}ms` }}>{p}</span>
              ))}
            </h1>
            <p className="mt-5 text-navy-200 text-lg max-w-md opacity-0 animate-[palabra_.6s_ease-out_.9s_forwards]">
              APU con formato oficial, contratos que tu cliente firma desde el celular,
              y actas de obra pública liquidadas a peso. Hecho para Colombia.
            </p>
            <div className="mt-8 flex flex-wrap gap-3 opacity-0 animate-[palabra_.6s_ease-out_1.1s_forwards]">
              <Link to="/registro"
                    className="cta-brillo text-navy-900 font-black rounded-2xl px-7 py-3.5 text-sm shadow-xl shadow-amber-500/20 hover:scale-105 transition">
                Empieza gratis — 3 presupuestos al mes
              </Link>
              <Link to="/login" className="border border-navy-500 text-navy-100 rounded-2xl px-6 py-3.5 text-sm font-bold hover:bg-navy-800 transition">
                Ya tengo cuenta
              </Link>
            </div>
          </div>
          <div className="flex justify-center animate-[flotar_5s_ease-in-out_infinite]">
            <ApuVivo />
          </div>
        </div>
      </header>

      <Marquee />

      {/* EL DOCK */}
      <section className="py-20 px-5 text-center">
        <h2 className="text-2xl sm:text-3xl font-black">Las herramientas de la obra, en un solo lugar</h2>
        <p className="text-navy-300 mt-2 text-sm">Pasa el mouse — cada una hace el trabajo pesado.</p>
        <div className="mt-12 pb-6"><Dock /></div>
      </section>

      {/* LOS DOS UNIVERSOS */}
      <section ref={refU} className="py-20 px-5 bg-gradient-to-b from-navy-900 to-navy-800">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-black text-center">Dos universos, una sola matemática</h2>
          <div className="mt-12 grid md:grid-cols-2 gap-6">
            <div className="group bg-white rounded-3xl p-7 text-slate-800 hover:scale-[1.02] transition-transform duration-300 shadow-2xl">
              <p className="text-[10px] font-black tracking-widest text-navy-500">🏠 OBRA PRIVADA</p>
              <h3 className="text-xl font-black mt-2">Tu cliente firma desde el celular</h3>
              <p className="text-sm text-slate-500 mt-2">Envías el enlace. Ve el presupuesto, los diseños, comenta —
                y firma el contrato con validez de la Ley 527. Sin PDF por WhatsApp, sin "luego te digo".</p>
              <div className="mt-5 bg-slate-50 rounded-2xl border border-slate-200 p-4">
                <p className="text-[10px] text-slate-400 mb-1">Firma aquí con tu dedo o mouse</p>
                <FirmaViva activa={vistoU} />
                <p className="text-[11px] font-bold text-slate-600 text-right">María Fernanda López · C.C. ***2333</p>
              </div>
            </div>
            <div className="group bg-navy-700/60 border border-navy-600 rounded-3xl p-7 hover:scale-[1.02] transition-transform duration-300 shadow-2xl">
              <p className="text-[10px] font-black tracking-widest text-amber-400">🏛️ OBRA PÚBLICA — ASGARD</p>
              <h3 className="text-xl font-black mt-2">Nada viaja fuera. El primer avance sella.</h3>
              <p className="text-sm text-navy-200 mt-2">Presupuesto oficial inmutable, adicionales con aprobación interna,
                deducciones de ley vigiladas y balance oficial-vs-ejecutado que cuadra a peso.</p>
              <div className={`mt-5 flex items-center justify-center transition-all duration-700 ${vistoU ? 'opacity-100 scale-100' : 'opacity-0 scale-50'}`}>
                <div className="relative">
                  <div className="w-28 h-28 rounded-full border-4 border-amber-500/70 flex items-center justify-center rotate-[-12deg] shadow-[0_0_30px_rgba(245,158,11,.25)]">
                    <div className="text-center">
                      <p className="text-[9px] font-black text-amber-400 tracking-widest">PRESUPUESTO</p>
                      <p className="text-lg font-black text-amber-400">SELLADO</p>
                      <p className="text-[8px] text-amber-500/80">1er avance · inmutable</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* EL ACTA QUE SE LIQUIDA */}
      <section className="py-20 px-5 bg-navy-800">
        <div className="max-w-6xl mx-auto grid lg:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="text-2xl sm:text-3xl font-black">La plata de la obra, a peso</h2>
            <p className="text-navy-200 mt-3 text-sm leading-relaxed max-w-md">
              Anticipo que se amortiza con tope, retegarantía que se libera con el acta,
              deducciones de ley que el vigía corrige con un clic. El neto que ves es el neto que llega
              — y un robot lo verifica en cada versión de la plataforma.
            </p>
            <ul className="mt-5 space-y-2 text-sm text-navy-100">
              <li>💵 Acta de anticipo al flujo de caja</li>
              <li>📅 Cartera por edades con semáforo 🟢🟠🔴</li>
              <li>🏁 Margen ejecutado: contrato − costos reales</li>
            </ul>
          </div>
          <div className="flex justify-center"><ActaViva /></div>
        </div>
      </section>

      {/* LOS ROBOTS */}
      <section className="py-20 px-5">
        <div className="max-w-6xl mx-auto grid lg:grid-cols-2 gap-12 items-center">
          <div className="flex justify-center order-2 lg:order-1"><Terminal /></div>
          <div className="order-1 lg:order-2">
            <h2 className="text-2xl sm:text-3xl font-black">Vigilado por robots, no por promesas</h2>
            <p className="text-navy-200 mt-3 text-sm leading-relaxed max-w-md">
              Antes de cada versión, dos robots recorren la plataforma completa: registran, cotizan,
              firman, sellan, liquidan actas y exportan — 159 pasos con la matemática verificada a peso.
              Si un solo peso no cuadra, la versión no sale.
            </p>
            <div className="mt-6 grid grid-cols-3 gap-3 max-w-sm">
              {[['159', 'pasos de robot'], ['49', 'candados 4xx'], ['2.288', 'actividades APU']].map(([n, l]) => (
                <div key={l} className="bg-navy-800 border border-navy-700 rounded-2xl p-3 text-center">
                  <p className="text-xl font-black text-amber-400">{n}</p>
                  <p className="text-[10px] text-navy-300">{l}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA FINAL */}
      <section className="py-24 px-5 text-center bg-gradient-to-b from-navy-900 to-navy-800 grid-plano">
        <h2 className="text-3xl sm:text-4xl font-black">Tu próxima obra empieza aquí</h2>
        <p className="text-navy-300 mt-3 text-sm">Gratis: 3 presupuestos al mes con TODO el poder. Sin tarjeta.</p>
        <Link to="/registro"
              className="cta-brillo inline-block mt-8 text-navy-900 font-black rounded-2xl px-9 py-4 shadow-xl shadow-amber-500/20 hover:scale-105 transition">
          Crear mi cuenta gratis
        </Link>
      </section>

      <footer className="py-8 px-5 border-t border-navy-700/50 text-center text-[11px] text-navy-400">
        PresupuestarCO — presupuestos de obra profesionales, hechos en Colombia 🇨🇴 ·
        <Link to="/legal" className="underline ml-1 hover:text-navy-200">Términos y privacidad</Link>
      </footer>
    </div>
  )
}
