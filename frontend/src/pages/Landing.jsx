import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { Link } from 'react-router-dom'
import { Building2, Search, MessageCircle, FileSignature, HardHat, Calculator,
         CheckCircle2, Zap, Shield, ChevronRight, Eye, Star, Camera,
         FileSpreadsheet, MapPin, Hash, ClipboardCheck } from 'lucide-react'

const CHECK = ({ children, bold }) => (
  <li className="flex items-start gap-2.5 text-sm text-slate-600">
    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
    <span className={bold ? 'font-bold text-slate-800' : ''}>{children}</span>
  </li>
)

const FUNCIONES = [
  [Search, 'Base APU 2026', '2.288 actividades de construcción con precios de referencia por capítulos. Precios ajustados a 13 ciudades colombianas.'],
  [Zap, 'Plantillas de presupuesto', 'Baño, cocina, casa 60m², cubierta, pintura, placa: actividades típicas pre-cargadas. Primera cotización en 3 minutos.'],
  [Calculator, 'Calculadora de cantidades', '¿3 columnas de 30×30 por 3 metros? Escribes dimensiones y la app convierte a m³ sola.'],
  [Shield, 'AIU + IVA como manda la ley', 'A, I y U configurables. IVA 19% solo sobre la utilidad (Art. 462-1 ET). Deja de regalar plata.'],
  [MessageCircle, 'Enlace WhatsApp con "visto"', 'Tu cliente abre todo en su celular sin instalar nada. Tú ves cuándo lo abrió y cuántas veces.'],
  [FileSignature, 'Contrato con doble firma', 'Contrato de Obra Civil de 8 cláusulas generado automático. El cliente firma con el dedo, tu firma ya está puesta. Ley 527/1999.'],
  [HardHat, 'Avances de obra en vivo', 'Marcas % por actividad → valor ejecutado ponderado. Tu cliente sigue su obra en tiempo real con fotos.'],
  [ClipboardCheck, 'Gastos y utilidad REAL', 'Registra cada gasto con foto del recibo. Utilidad proyectada vs real con semáforo: verde vas bien, rojo estás perdiendo.'],
  [FileSpreadsheet, 'Cuentas de cobro automáticas', 'Cada corte se liquida solo: ejecutado menos amortización del anticipo. PDF con tu firma y cuenta bancaria.'],
  [Eye, 'Estado de pagos del cliente', 'Tu cliente ve sus cuentas pendientes y pagadas junto a la evidencia del avance. Pagar se siente justo.'],
  [Hash, 'Caja neta siempre visible', 'Cobrado menos gastado, por proyecto y global. La cifra que decide si arrancas la próxima obra.'],
  [Star, 'Acta de entrega bilateral', 'El cliente confirma y firma el recibido. Acta PDF con las dos firmas cierra el ciclo legal.'],
  [Camera, 'Encuesta y reputación pública', 'Cada obra terminada suma estrellas a tu perfil público. Tus reseñas venden la siguiente obra.'],
  [MapPin, 'Mini-CRM de clientes', 'Cada cliente con su historial: obras, total contratado, pagado y calificación. Autocompletar al cotizar de nuevo.'],
  [CheckCircle2, 'Numeración y estados', 'COT-2026-0001, CC-2026-0001... Borrador → Visto → Aceptado → Terminado. Todo ordenado y trazable.'],
  [Building2, 'PDF y Excel con tu marca', 'Cotización, contrato, cuenta de cobro y acta: 4 documentos profesionales con tu logo y tus datos.'],
  [Zap, 'Notificaciones al instante', 'Te avisa cuando el cliente ve, firma, confirma la entrega o te califica. La campana 🔔 no descansa.'],
  [Shield, 'Cadena documental inmutable', 'Ítems bloqueados tras la firma, cuentas pagadas ineliminables, avances con cobro protegidos. Nadie borra la historia.'],
]


const FASES = [
  {
    id: 'clientes', emoji: '👥', nombre: 'Clientes', titulo: 'Tu cartera de clientes, con memoria',
    desc: 'Cada cliente con su historial: cuánto te ha contratado, cuánto te ha pagado y cómo te calificó. La segunda obra se cotiza con su teléfono ya guardado.',
    mock: (
      <div className="space-y-2">
        {[
          ['MR', 'María Rodríguez', '3 obras · ⭐ 5', '$45.3M', 'pagado $38.1M'],
          ['KT', 'Karoll Tobio', '1 obra en ejecución', '$45.3M', 'pagado $22.6M'],
          ['RV', 'Ramiro Vergara', '1 terminada · ⭐ 5', '$11.3M', 'pagado $11.3M'],
        ].map(([ini, n, sub, tot, pag], i) => (
          <div key={i} className="flex items-center gap-2.5 bg-white rounded-xl p-2.5 border border-slate-100">
            <span className="w-8 h-8 bg-navy-50 rounded-lg flex items-center justify-center text-[10px] font-bold text-navy-600">{ini}</span>
            <div className="flex-1 min-w-0">
              <p className="text-[11px] font-bold text-slate-700">{n}</p>
              <p className="text-[9px] text-slate-400">{sub}</p>
            </div>
            <div className="text-right">
              <p className="text-[11px] font-black text-slate-700">{tot}</p>
              <p className="text-[8px] text-emerald-600">{pag}</p>
            </div>
          </div>
        ))}
      </div>
    ),
  },
  {
    id: 'cotiza', emoji: '📋', nombre: 'Cotiza', titulo: 'De la hoja en blanco a la cotización en 3 minutos',
    desc: 'Plantillas listas (baño, cocina, casa 60m²...) sobre la base APU 2026: 2.288 actividades con precios de tu ciudad. AIU e IVA sobre utilidad como manda el Art. 462-1.',
    mock: (
      <div>
        <div className="grid grid-cols-3 gap-1.5 mb-2.5">
          {[['🚿','Baño'],['🍳','Cocina'],['🏠','Casa 60m²'],['🎨','Pintura'],['🧱','Placa'],['🏭','Cubierta']].map(([e, n], i) => (
            <div key={i} className={`rounded-lg border-2 p-1.5 text-center ${i === 0 ? 'border-emerald-400 bg-emerald-50' : 'border-slate-100 bg-white'}`}>
              <span className="text-sm">{e}</span>
              <p className="text-[8px] font-bold text-slate-600">{n}</p>
            </div>
          ))}
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-2.5 space-y-1">
          {[['Enchape pared cerámica', '18 m²', '$1.2M'],['Sanitario + instalación', '1 un', '$485k'],['Punto hidráulico', '4 un', '$754k']].map(([d, c, v], i) => (
            <div key={i} className="flex justify-between text-[9px]">
              <span className="text-slate-500 truncate">{d}</span>
              <span className="text-slate-400 mx-2">{c}</span>
              <span className="font-bold text-slate-700">{v}</span>
            </div>
          ))}
          <div className="flex justify-between text-[10px] font-black text-navy-700 border-t border-slate-100 pt-1">
            <span>Total con AIU + IVA</span><span>$8.2M</span>
          </div>
        </div>
      </div>
    ),
  },
  {
    id: 'contrata', emoji: '📜', nombre: 'Contrata', titulo: 'Contrato de obra con las dos firmas',
    desc: 'Al aceptar, tu cliente firma con el dedo un Contrato de Ejecución de Obra Civil de 8 cláusulas generado automático. Tu firma manuscrita ya está en el documento. Ley 527 de 1999.',
    mock: (
      <div className="bg-white rounded-xl border border-slate-100 p-3">
        <p className="text-[9px] font-black text-slate-700 text-center mb-1">CONTRATO DE EJECUCIÓN DE OBRA CIVIL</p>
        <p className="text-[8px] text-slate-400 text-center mb-2">COT-2026-0037 · $8.245.000 · Anticipo 50% · 20 días</p>
        <div className="space-y-1 mb-3">
          {['PRIMERA — Objeto', 'CUARTA — Forma de pago', 'SEXTA — Garantías'].map((c, i) => (
            <p key={i} className="text-[8px] text-slate-400">§ {c}...</p>
          ))}
        </div>
        <div className="grid grid-cols-2 gap-2">
          {[['✍️', 'María López', 'EL CONTRATANTE'], ['✍️', 'Jaime V.', 'EL CONTRATISTA']].map(([f, n, r], i) => (
            <div key={i} className="border-t-2 border-slate-300 pt-1 text-center">
              <p className="text-base -mb-0.5" style={{fontFamily: 'cursive'}}>{f} {n.split(' ')[0]}</p>
              <p className="text-[7px] font-bold text-slate-600">{n}</p>
              <p className="text-[7px] text-slate-400">{r}</p>
            </div>
          ))}
        </div>
      </div>
    ),
  },
  {
    id: 'ejecuta', emoji: '🏗️', nombre: 'Ejecuta', titulo: 'Tu cliente sigue la obra en vivo — y tú, tu plata',
    desc: 'Publicas avances con % por actividad y fotos: el cliente ve el valor ejecutado en tiempo real desde su enlace. Y registras cada gasto con foto del recibo: utilidad proyectada vs REAL, con semáforo.',
    mock: (
      <div className="space-y-2">
        <div className="bg-white rounded-xl border border-slate-100 p-2.5">
          <div className="flex justify-between text-[9px] mb-1">
            <span className="font-bold text-slate-700">📱 Lo que ve tu cliente</span>
            <span className="font-black text-emerald-600">64%</span>
          </div>
          <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden mb-1">
            <div className="h-full bg-emerald-500 rounded-full" style={{width: '64%'}} />
          </div>
          <p className="text-[8px] text-slate-400">Valor ejecutado: <strong className="text-slate-600">$5.2M</strong> de $8.2M · 📸 6 fotos</p>
        </div>
        <div className="bg-emerald-50 rounded-xl border border-emerald-100 p-2.5">
          <p className="text-[9px] font-bold text-slate-700 mb-1">💸 Lo que ves tú (privado)</p>
          <div className="flex justify-between text-[9px]">
            <span className="text-slate-500">Utilidad proyectada: <strong>$660k</strong></span>
            <span className="text-emerald-700 font-black">Real: $612k 🟢</span>
          </div>
          <p className="text-[8px] text-slate-400 mt-0.5">Gastado $4.6M de $6.9M presupuestado · recibos 📷 archivados</p>
        </div>
      </div>
    ),
  },
  {
    id: 'cobra', emoji: '💵', nombre: 'Cobra', titulo: 'Cuentas de cobro que se liquidan solas',
    desc: 'Cada corte genera su cuenta de cobro: valor ejecutado menos amortización del anticipo, con tu firma y tu cuenta bancaria. El cliente la ve junto a la evidencia. Caja neta siempre visible.',
    mock: (
      <div className="bg-white rounded-xl border border-slate-100 p-3">
        <p className="text-[9px] font-black text-slate-700 mb-0.5">CUENTA DE COBRO N° CC-2026-0012</p>
        <p className="text-[8px] text-slate-400 mb-2">María López DEBE A Jaime V. — Corte 2 (34% → 64%)</p>
        <div className="space-y-0.5 text-[9px]">
          <div className="flex justify-between text-slate-500"><span>Valor ejecutado del corte</span><span>$2.460.000</span></div>
          <div className="flex justify-between text-slate-500"><span>(−) Amortización anticipo 50%</span><span>− $1.230.000</span></div>
          <div className="flex justify-between font-black text-emerald-700 border-t border-slate-100 pt-0.5"><span>NETO A PAGAR</span><span>$1.230.000</span></div>
        </div>
        <div className="flex gap-1.5 mt-2">
          <span className="text-[8px] font-bold bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full">✓ CC-0011 pagada</span>
          <span className="text-[8px] font-bold bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">⏳ CC-0012 enviada</span>
        </div>
      </div>
    ),
  },
  {
    id: 'crece', emoji: '⭐', nombre: 'Crece', titulo: 'Cada obra terminada te vende la siguiente',
    desc: 'Acta de entrega bilateral con las dos firmas, encuesta de satisfacción, y tu perfil público con reseñas reales. El badge ⭐ aparece en cada cotización nueva que envías.',
    mock: (
      <div className="space-y-2">
        <div className="bg-white rounded-xl border border-slate-100 p-2.5 text-center">
          <p className="text-[10px] font-black text-slate-700">Jaime V. — Contratista</p>
          <p className="text-lg font-black text-amber-500">⭐ 4.9</p>
          <p className="text-[8px] text-slate-400">12 obras terminadas · 9 reseñas públicas</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-2.5">
          <p className="text-[9px] text-slate-600 italic">"Cumplió el plazo y la obra quedó impecable. Lo recomiendo."</p>
          <p className="text-[8px] text-slate-400 mt-1">— María R. · ⭐⭐⭐⭐⭐ · Remodelación baño</p>
        </div>
      </div>
    ),
  },
]

function CicloCompleto() {
  const [fase, setFase] = useState('cotiza')
  const activa = FASES.find(f => f.id === fase)
  return (
    <section className="bg-slate-50 py-16">
      <div className="max-w-5xl mx-auto px-4">
        <div className="text-center mb-8">
          <span className="text-[11px] font-black uppercase tracking-wider text-navy-500">No es un cotizador — es tu sistema de gestión</span>
          <h2 className="text-2xl sm:text-3xl font-black text-slate-800 mt-1.5">El ciclo completo de cada obra, conectado</h2>
          <p className="text-sm text-slate-500 mt-2 max-w-xl mx-auto">
            Del primer contacto al último peso cobrado. Cada documento hereda del anterior — nada se digita dos veces.
          </p>
        </div>

        <div className="flex justify-center gap-1.5 sm:gap-2 flex-wrap mb-6">
          {FASES.map(f => (
            <button key={f.id} onClick={() => setFase(f.id)}
                    className={`flex items-center gap-1.5 text-xs font-bold px-3 sm:px-4 py-2 rounded-full transition ${fase === f.id ? 'bg-navy-700 text-white shadow-lg' : 'bg-white text-slate-500 border border-slate-200 hover:border-navy-300'}`}>
              <span>{f.emoji}</span><span className="hidden sm:inline">{f.nombre}</span>
            </button>
          ))}
        </div>

        <div className="bg-white rounded-3xl border border-slate-200 shadow-xl overflow-hidden">
          <div className="grid md:grid-cols-2">
            <div className="p-6 sm:p-8 flex flex-col justify-center">
              <span className="text-3xl mb-3">{activa.emoji}</span>
              <h3 className="text-xl font-black text-slate-800 leading-snug">{activa.titulo}</h3>
              <p className="text-sm text-slate-500 mt-3 leading-relaxed">{activa.desc}</p>
              <Link to="/registro" className="inline-flex items-center gap-1.5 text-sm font-bold text-emerald-600 mt-5">
                Empezar gratis <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
            <div className="bg-slate-50 p-5 sm:p-6 flex items-center">
              <div className="w-full">{activa.mock}</div>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-center gap-1 mt-6 text-[10px] text-slate-400 flex-wrap">
          {FASES.map((f, i) => (
            <React.Fragment key={f.id}>
              <button onClick={() => setFase(f.id)} className={`font-bold ${fase === f.id ? 'text-navy-600' : ''}`}>{f.emoji} {f.nombre}</button>
              {i < FASES.length - 1 && <ChevronRight className="w-3 h-3" />}
            </React.Fragment>
          ))}
          <span className="ml-1">↻</span>
        </div>
      </div>
    </section>
  )
}

function DemoBuscador() {
  const [q, setQ] = useState('')
  const [resultados, setResultados] = useState([])
  const [buscando, setBuscando] = useState(false)
  const [buscado, setBuscado] = useState(false)
  const timer = useRef(null)

  useEffect(() => {
    if (!q.trim()) { setResultados([]); setBuscado(false); return }
    clearTimeout(timer.current)
    timer.current = setTimeout(async () => {
      setBuscando(true)
      try {
        const res = await axios.get('/api/precios/', { params: { q, limit: 5 } })
        setResultados(res.data.items || [])
        setBuscado(true)
      } catch { setResultados([]) }
      finally { setBuscando(false) }
    }, 350)
  }, [q])

  const COP = (v) => '$' + Math.round(v || 0).toLocaleString('es-CO')

  return (
    <section className="max-w-3xl mx-auto px-4 py-14">
      <div className="text-center mb-6">
        <span className="text-[11px] font-black uppercase tracking-wider text-emerald-600">Pruébalo ahora — sin cuenta</span>
        <h2 className="text-2xl sm:text-3xl font-black text-slate-800 mt-1.5">Busca en la base APU 2026 en vivo</h2>
        <p className="text-sm text-slate-500 mt-2">Escribe una actividad: pañete, placa, mampostería, pintura, cerámica...</p>
      </div>
      <div className="bg-white rounded-2xl border-2 border-navy-200 shadow-lg p-4 sm:p-5">
        <input
          className="w-full text-base sm:text-lg border-2 border-slate-200 rounded-xl px-4 py-3.5 outline-none focus:border-emerald-400 transition"
          placeholder='Ej: "pañete liso" o "concreto 3000"'
          value={q} onChange={e => setQ(e.target.value)} />
        <div className="flex flex-wrap gap-1.5 mt-3">
          {['pañete', 'placa', 'mampostería', 'excavación', 'pintura', 'cerámica'].map(s => (
            <button key={s} onClick={() => setQ(s)}
                    className="text-xs bg-slate-100 hover:bg-navy-50 text-slate-600 px-3 py-1.5 rounded-full transition">
              {s}
            </button>
          ))}
        </div>
        <div className="mt-4 min-h-[60px]">
          {buscando ? (
            <p className="text-center text-sm text-slate-400 py-4">Buscando en 2.288 actividades...</p>
          ) : resultados.length > 0 ? (
            <div className="divide-y divide-slate-50">
              {resultados.map((r, i) => (
                <div key={i} className="py-2.5 flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-sm text-slate-700 leading-snug">{r.descripcion}</p>
                    <p className="text-[10px] text-slate-400">{r.categoria}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-sm font-bold text-slate-800">{COP(r.precio)}</p>
                    <p className="text-[10px] text-slate-400">/{r.unidad}</p>
                  </div>
                </div>
              ))}
              <div className="pt-3 text-center">
                <a href="/registro" className="inline-flex items-center gap-1.5 text-sm font-bold text-emerald-600">
                  Crear cuenta gratis y usar estos precios <ChevronRight className="w-4 h-4" />
                </a>
              </div>
            </div>
          ) : buscado ? (
            <p className="text-center text-sm text-slate-400 py-4">Sin resultados — prueba otra palabra</p>
          ) : (
            <p className="text-center text-xs text-slate-300 py-4">Los resultados aparecen aquí con precios reales de la base</p>
          )}
        </div>
      </div>
    </section>
  )
}

function BotonWhatsApp() {
  const [numero, setNumero] = useState('')
  useEffect(() => {
    axios.get('/api/config').then(r => setNumero(r.data.whatsapp_soporte || '')).catch(() => {})
  }, [])
  if (!numero) return null
  const limpio = numero.replace(/\D/g, '')
  const url = `https://wa.me/${limpio.startsWith('57') ? limpio : '57' + limpio}?text=${encodeURIComponent('Hola! Tengo una pregunta sobre PresupuestarCO')}`
  return (
    <a href={url} target="_blank" rel="noreferrer"
       className="fixed bottom-5 right-5 z-50 flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-white rounded-full shadow-2xl pl-4 pr-5 py-3.5 transition hover:scale-105"
       aria-label="Escríbenos por WhatsApp">
      <MessageCircle className="w-5 h-5" />
      <span className="text-sm font-bold hidden sm:inline">¿Dudas? Escríbenos</span>
    </a>
  )
}

export default function Landing() {
  return (
    <div className="min-h-screen bg-white">
      {/* ── NAV ── */}
      <nav className="sticky top-0 z-50 bg-navy-800/95 backdrop-blur border-b border-white/10">
        <div className="max-w-6xl mx-auto px-4 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-white/10 rounded-lg flex items-center justify-center">
              <Building2 className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-white">PresupuestarCO</span>
          </div>
          <div className="flex items-center gap-3">
            <a href="#funciones" className="hidden sm:block text-sm text-blue-200 hover:text-white transition">Funciones</a>
            <a href="#precios" className="hidden sm:block text-sm text-blue-200 hover:text-white transition">Precios</a>
            <Link to="/login" className="text-sm text-blue-100 font-medium px-3 py-1.5">Entrar</Link>
            <Link to="/registro" className="text-sm bg-emerald-500 hover:bg-emerald-400 text-white font-semibold px-4 py-2 rounded-xl transition">
              Empezar gratis
            </Link>
          </div>
        </div>
      </nav>

      {/* ── HERO ── */}
      <header className="bg-gradient-to-br from-navy-900 via-navy-800 to-navy-600 text-white relative overflow-hidden">
        <div className="absolute inset-0 opacity-10" style={{backgroundImage: 'radial-gradient(circle at 20% 50%, white 1px, transparent 1px)', backgroundSize: '32px 32px'}}></div>
        <div className="max-w-6xl mx-auto px-4 pt-16 pb-20 relative">
          <div className="max-w-2xl">
            <span className="inline-flex items-center gap-1.5 text-xs font-semibold bg-emerald-500/20 text-emerald-300 px-3 py-1.5 rounded-full mb-5">
              <Zap className="w-3.5 h-3.5" /> Todas las funciones gratis — paga solo si cotizas en volumen
            </span>
            <h1 className="text-4xl sm:text-5xl font-black leading-tight tracking-tight">
              Deja de regalar tu trabajo: <span className="text-emerald-400">cotiza como empresa y cobra hasta el último peso</span>
            </h1>
            <p className="text-lg text-blue-200 mt-5 leading-relaxed">
              El sistema de gestión del contratista colombiano: presupuestos con la base APU 2026,
              contratos con firma digital, seguimiento de obra en vivo para tu cliente, control de
              gastos con utilidad real y cuentas de cobro que se liquidan solas.
            </p>
            <div className="flex flex-wrap gap-2 mt-5">
              {['📋 Presupuestos', '📜 Contratos', '🏗️ Avances en vivo', '💸 Gastos', '💵 Cuentas de cobro', '👥 Clientes', '⭐ Reputación'].map(c => (
                <span key={c} className="text-[11px] font-semibold bg-white/10 text-blue-100 px-2.5 py-1 rounded-full">{c}</span>
              ))}
            </div>
            <div className="flex flex-wrap gap-3 mt-8">
              <Link to="/registro" className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-white font-bold px-6 py-3.5 rounded-xl transition text-sm">
                Crear cuenta gratis <ChevronRight className="w-4 h-4" />
              </Link>
              <a href="/p/demo" target="_blank" rel="noreferrer"
                 className="flex items-center gap-2 border border-white/20 hover:bg-white/5 text-white font-medium px-6 py-3.5 rounded-xl transition text-sm">
                👀 Mira lo que verá tu cliente
              </a>
            </div>
            <p className="text-xs text-blue-300 mt-4">Sin tarjeta de crédito · 3 presupuestos gratis al mes · Listo en 2 minutos</p>

            {/* Mockup compacto solo mobile */}
            <div className="lg:hidden mt-8 bg-white rounded-2xl shadow-2xl p-4 max-w-sm">
              <div className="flex justify-between items-center mb-2">
                <div>
                  <p className="text-[10px] font-bold text-navy-500">COT-2026-0037</p>
                  <p className="text-xs font-semibold text-slate-700">Remodelación Casa López</p>
                </div>
                <span className="text-[9px] bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-bold">✓ Firmado</span>
              </div>
              <div className="flex justify-between bg-navy-800 text-white rounded-lg px-3 py-2">
                <span className="text-[10px] uppercase text-blue-200">Total</span>
                <span className="text-sm font-black">$276.675.000</span>
              </div>
              <div className="flex items-center gap-1.5 mt-2 text-[9px] text-slate-400">
                <MessageCircle className="w-3 h-3 text-emerald-500" /> Visto por el cliente · hace 5 min
              </div>
            </div>
          </div>

          <div className="hidden lg:block absolute right-4 top-16 w-80 bg-white rounded-2xl shadow-2xl p-4 rotate-2">
            <div className="flex justify-between items-center mb-3">
              <div>
                <p className="text-[10px] font-bold text-navy-500">COT-2026-0037</p>
                <p className="text-xs font-semibold text-slate-700">Remodelación Casa López</p>
              </div>
              <span className="text-[9px] bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-bold">✓ Firmado</span>
            </div>
            {[['Excavación zapatas 2×2×1.2', '$2.100.000'], ['Columnas 4000 PSI ×15', '$49.500.000'], ['Placa aligerada 360 m²', '$129.600.000']].map(([d, v], i) => (
              <div key={i} className="flex justify-between py-1.5 border-b border-slate-50 text-[10px]">
                <span className="text-slate-500">{d}</span>
                <span className="text-slate-700 font-medium">{v}</span>
              </div>
            ))}
            <div className="flex justify-between mt-3 bg-navy-800 text-white rounded-lg px-3 py-2">
              <span className="text-[10px] uppercase text-blue-200">Total</span>
              <span className="text-sm font-black">$276.675.000</span>
            </div>
            <div className="flex items-center gap-1.5 mt-2.5 text-[9px] text-slate-400">
              <MessageCircle className="w-3 h-3 text-emerald-500" /> Visto por el cliente · hace 5 min
            </div>
          </div>
        </div>
      </header>

      {/* ── CIFRAS ── */}
      <section className="bg-navy-800 border-t border-white/5 py-6">
        <div className="max-w-5xl mx-auto px-4 grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
          {[['2.288', 'actividades APU 2026'], ['13', 'ciudades con precios'], ['8', 'cláusulas de contrato'], ['100%', 'hecho en Colombia 🇨🇴']].map(([n, l], i) => (
            <div key={i}>
              <p className="text-2xl font-black text-emerald-400">{n}</p>
              <p className="text-[11px] text-blue-300 mt-0.5">{l}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── DEMO BUSCADOR EN VIVO ── */}
      <CicloCompleto />

      <DemoBuscador />

      {/* ── PROBLEMA ── */}
      <section className="max-w-4xl mx-auto px-4 py-16 text-center">
        <h2 className="text-2xl sm:text-3xl font-black text-slate-800">¿Te suena familiar?</h2>
        <div className="grid sm:grid-cols-3 gap-4 mt-8">
          {[
            ['😩', 'Excel hasta medianoche', 'Buscando precios viejos, cuadrando fórmulas que se dañan'],
            ['👻', 'Clientes que desaparecen', 'Envías el PDF por WhatsApp y nunca sabes si lo abrieron'],
            ['🤝', 'Acuerdos de palabra', '"Arrancamos y después firmamos" — y después nadie firma'],
          ].map(([e, t, d], i) => (
            <div key={i} className="bg-slate-50 rounded-2xl p-5">
              <span className="text-3xl">{e}</span>
              <p className="font-bold text-slate-700 mt-2 text-sm">{t}</p>
              <p className="text-xs text-slate-500 mt-1">{d}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── SHOWCASE: 3 funciones estrella ── */}
      <section className="bg-slate-50 py-16">
        <div className="max-w-5xl mx-auto px-4 space-y-14">

          {/* WhatsApp + visto */}
          <div className="grid md:grid-cols-2 gap-8 items-center">
            <div>
              <span className="text-[11px] font-black uppercase tracking-wider text-emerald-600">Cierra más negocios</span>
              <h3 className="text-2xl font-black text-slate-800 mt-1.5">Toda tu obra vive en la app — a tu cliente le llega con un solo link</h3>
              <p className="text-sm text-slate-500 mt-3 leading-relaxed">
                Nada de PDFs pesados que nadie abre. Compartes un enlace profesional con tu logo;
                tu cliente lo ve en su celular al instante y tú recibes el <strong>"visto"</strong> —
                para llamarlo en el momento exacto en que está pensando en tu oferta.
              </p>
              <ul className="space-y-2 mt-4">
                <CHECK>Notificación de cuándo y cuántas veces lo abrió</CHECK>
                <CHECK>Botones de aceptar o rechazar — respuestas claras, no silencio</CHECK>
                <CHECK>El cliente no instala nada ni crea cuenta</CHECK>
              </ul>
              <a href="/p/demo" target="_blank" rel="noreferrer"
                 className="inline-flex items-center gap-1.5 mt-4 text-sm font-bold text-emerald-600 border border-emerald-200 rounded-xl px-4 py-2.5 hover:bg-emerald-50 transition">
                Ver presupuesto de ejemplo <ChevronRight className="w-4 h-4" />
              </a>
            </div>
            <div className="bg-white rounded-2xl shadow-lg p-5 border border-slate-100">
              <div className="bg-navy-800 rounded-xl p-4 text-white">
                <p className="text-[9px] text-blue-300 uppercase">Presupuesto de obra · COT-2026-0012</p>
                <p className="text-sm font-bold mt-0.5">Cubierta metálica Local 3</p>
                <p className="text-2xl font-black mt-2">$18.450.000</p>
              </div>
              <div className="flex gap-2 mt-3">
                <div className="flex-1 text-center text-[10px] py-2.5 rounded-lg border border-slate-200 text-slate-500">Preguntar</div>
                <div className="flex-[2] text-center text-[10px] py-2.5 rounded-lg bg-emerald-500 text-white font-bold">✓ Aceptar presupuesto</div>
              </div>
              <div className="flex items-center gap-1.5 mt-3 text-[10px] text-violet-600 bg-violet-50 rounded-lg px-2.5 py-1.5 w-fit">
                <Eye className="w-3 h-3" /> Visto 3 veces · última hace 5 min
              </div>
            </div>
          </div>

          {/* Contrato */}
          <div className="grid md:grid-cols-2 gap-8 items-center">
            <div className="order-2 md:order-1 bg-white rounded-2xl shadow-lg p-5 border border-slate-100">
              <p className="text-[10px] font-black text-center text-slate-700">CONTRATO DE EJECUCIÓN DE OBRA CIVIL</p>
              <div className="mt-3 space-y-2">
                {['PRIMERA: OBJETO', 'SEGUNDA: TÉRMINO — 45 días hábiles', 'TERCERA: COSTO — $18.450.000', 'CUARTA: ANTICIPO 50% · SALDO 50%'].map((c, i) => (
                  <div key={i} className="text-[9px] text-slate-500 bg-slate-50 rounded-lg px-2.5 py-1.5">{c}</div>
                ))}
              </div>
              <div className="grid grid-cols-2 gap-2 mt-4 pt-3 border-t border-slate-100">
                <div className="text-center">
                  <p className="text-[9px] font-bold text-slate-600">CONTRATANTE</p>
                  <p className="text-[9px] text-emerald-600 mt-0.5">✓ Firmado · 10/08 14:32</p>
                </div>
                <div className="text-center">
                  <p className="text-[9px] font-bold text-slate-600">CONTRATISTA</p>
                  <p className="text-[9px] text-emerald-600 mt-0.5">✓ Emitido digitalmente</p>
                </div>
              </div>
            </div>
            <div className="order-1 md:order-2">
              <span className="text-[11px] font-black uppercase tracking-wider text-navy-500">Trabaja con respaldo</span>
              <h3 className="text-2xl font-black text-slate-800 mt-1.5">Se acabaron los acuerdos de palabra</h3>
              <p className="text-sm text-slate-500 mt-3 leading-relaxed">
                Cuando tu cliente acepta, no solo dice "sí": <strong>firma un Contrato de
                Ejecución de Obra Civil</strong> generado automáticamente con tus condiciones —
                plazo, anticipo, forma de pago, responsabilidades. Con nombre, cédula, fecha y hora registrados.
              </p>
              <ul className="space-y-2 mt-4">
                <CHECK>8 cláusulas generadas desde tu presupuesto</CHECK>
                <CHECK>Evidencia digital amparada en la Ley 527 de 1999</CHECK>
                <CHECK>PDF del contrato firmado para ambas partes</CHECK>
                <CHECK>El presupuesto se bloquea tras la firma — nadie cambia las reglas</CHECK>
              </ul>
            </div>
          </div>

          {/* Avances */}
          <div className="grid md:grid-cols-2 gap-8 items-center">
            <div>
              <span className="text-[11px] font-black uppercase tracking-wider text-amber-600">Cobra sin peleas</span>
              <h3 className="text-2xl font-black text-slate-800 mt-1.5">Avances de obra en plata, no en cuentos</h3>
              <p className="text-sm text-slate-500 mt-3 leading-relaxed">
                Marcas el % de avance <strong>por cada actividad del presupuesto</strong> y el sistema
                calcula el valor ejecutado ponderado. Tu cliente lo ve en tiempo real con fotos —
                cuando pidas el siguiente pago, los números ya están sobre la mesa.
              </p>
              <ul className="space-y-2 mt-4">
                <CHECK>Avance ponderado por el valor de cada actividad</CHECK>
                <CHECK>"$12.4M ejecutados de $36.4M" — claridad total</CHECK>
                <CHECK>Fotos por corte de obra</CHECK>
                <CHECK>Al terminar: encuesta de satisfacción y tu calificación ⭐</CHECK>
              </ul>
            </div>
            <div className="bg-white rounded-2xl shadow-lg p-5 border border-slate-100">
              <div className="flex justify-between items-center">
                <p className="text-xs font-bold text-slate-700">Avance de tu obra</p>
                <span className="text-sm font-black text-emerald-600">64%</span>
              </div>
              <div className="h-2.5 bg-slate-100 rounded-full mt-2 overflow-hidden">
                <div className="h-full bg-emerald-500 rounded-full" style={{width: '64%'}}></div>
              </div>
              <div className="flex justify-between text-[10px] bg-emerald-50 rounded-lg p-2.5 mt-3">
                <span className="text-emerald-700">Valor ejecutado</span>
                <span className="font-bold text-emerald-700">$11.8M de $18.4M</span>
              </div>
              <div className="mt-3 space-y-1.5">
                {[['Excavación y zapatas', 100], ['Columnas y pedestales', 80], ['Placa aligerada', 35]].map(([a, p], i) => (
                  <div key={i} className="flex items-center gap-2 text-[9px]">
                    <span className="flex-1 text-slate-500">{a}</span>
                    <div className="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full bg-emerald-400 rounded-full" style={{width: `${p}%`}}></div>
                    </div>
                    <span className="text-slate-400 w-7 text-right">{p}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── TODAS LAS FUNCIONES ── */}
      {/* ── LOS 4 DOCUMENTOS ── */}
      <section className="max-w-6xl mx-auto px-4 py-16">
        <div className="text-center mb-8">
          <span className="text-[11px] font-black uppercase tracking-wider text-navy-500">Papeles de empresa grande, esfuerzo de un tap</span>
          <h2 className="text-2xl sm:text-3xl font-black text-slate-800 mt-1.5">Los 4 documentos que profesionalizan tu negocio</h2>
          <p className="text-sm text-slate-500 mt-2">Cada uno hereda los datos del anterior. Con tu logo, tu firma y tus datos — cero digitación.</p>
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {[
            ['📋', 'Cotización', 'PDF y Excel con AIU, IVA y tu marca. Numeración COT automática.', 'Al cotizar'],
            ['📜', 'Contrato de obra', '8 cláusulas, doble firma manuscrita, anticipo y plazo. Ley 527/1999.', 'Al aceptar'],
            ['💵', 'Cuenta de cobro', 'Liquidación del corte menos anticipo. Con tu cuenta bancaria.', 'Cada corte'],
            ['🤝', 'Acta de entrega', 'El recibido firmado por ambos. Cierra el ciclo legal de la obra.', 'Al terminar'],
          ].map(([e, t, d, cuando], i) => (
            <div key={i} className="bg-white border-2 border-slate-100 hover:border-navy-200 rounded-2xl p-4 transition group">
              <div className="flex items-center justify-between mb-2">
                <span className="text-2xl">{e}</span>
                <span className="text-[9px] font-bold bg-navy-50 text-navy-500 px-2 py-1 rounded-full">{cuando}</span>
              </div>
              <p className="text-sm font-black text-slate-800">{t}</p>
              <p className="text-[11px] text-slate-400 mt-1.5 leading-relaxed">{d}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="funciones" className="max-w-6xl mx-auto px-4 py-16">
        <h2 className="text-2xl sm:text-3xl font-black text-slate-800 text-center">Todas las funciones, en ambos planes</h2>
        <p className="text-slate-500 text-center mt-2 text-sm">Sin funciones bloqueadas. Pruébalo todo gratis.</p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-10">
          {FUNCIONES.map(([Icon, t, d], i) => (
            <div key={i} className="bg-white rounded-2xl p-5 border border-slate-100 hover:border-navy-200 hover:shadow-md transition">
              <div className="w-10 h-10 bg-navy-50 rounded-xl flex items-center justify-center mb-3">
                <Icon className="w-5 h-5 text-navy-500" />
              </div>
              <p className="font-bold text-slate-700 text-sm">{t}</p>
              <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">{d}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── PARA QUIÉN ── */}
      <section className="bg-slate-50 py-14">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-2xl font-black text-slate-800">Hecho para el que construye</h2>
          <div className="grid sm:grid-cols-3 gap-4 mt-8">
            {[
              ['👷', 'Maestros de obra', 'Cotiza reformas y remodelaciones con precios serios, sin depender de nadie'],
              ['🏠', 'Remodeladores', 'Cocinas, baños, ampliaciones — presupuesto profesional en la primera visita'],
              ['🏗️', 'Contratistas', 'Casas, locales, cubiertas — con contrato firmado antes de mover un ladrillo'],
            ].map(([e, t, d], i) => (
              <div key={i} className="bg-white rounded-2xl p-5 border border-slate-100">
                <span className="text-3xl">{e}</span>
                <p className="font-bold text-slate-700 mt-2 text-sm">{t}</p>
                <p className="text-xs text-slate-500 mt-1.5">{d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CÓMO FUNCIONA ── */}
      <section id="como-funciona" className="max-w-5xl mx-auto px-4 py-16">
        <h2 className="text-2xl sm:text-3xl font-black text-slate-800 text-center">De cero a contrato firmado en 3 pasos</h2>
        <div className="grid sm:grid-cols-3 gap-6 mt-10">
          {[
            ['1', 'Arma el presupuesto', 'Busca actividades en la base APU, calcula cantidades por dimensiones y define tu AIU.'],
            ['2', 'Comparte por WhatsApp', 'Enlace profesional con tu logo. Ves cuándo lo abre y recibes su respuesta.'],
            ['3', 'El cliente firma', 'Contrato de obra civil con firma digital → PDF para ambos → a trabajar con respaldo.'],
          ].map(([n, t, d], i) => (
            <div key={i} className="text-center">
              <div className="w-12 h-12 bg-navy-800 text-white rounded-2xl flex items-center justify-center mx-auto font-black text-lg">{n}</div>
              <p className="font-bold text-slate-700 mt-4">{t}</p>
              <p className="text-sm text-slate-500 mt-2 leading-relaxed">{d}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── PRICING ── */}
      <section id="precios" className="bg-navy-900 py-16">
        <div className="max-w-4xl mx-auto px-4">
          <h2 className="text-2xl sm:text-3xl font-black text-white text-center">Un solo diferencial: el volumen</h2>
          <p className="text-blue-300 text-center mt-2 text-sm">
            Ambos planes tienen TODAS las funciones. Pro es para quien cotiza sin parar.
          </p>

          <div className="grid sm:grid-cols-2 gap-5 mt-10 max-w-3xl mx-auto">
            {/* BÁSICO */}
            <div className="bg-white rounded-2xl p-7 flex flex-col">
              <p className="font-bold text-slate-700">Básico</p>
              <div className="mt-3">
                <span className="text-4xl font-black text-slate-800">$0</span>
                <span className="text-sm text-slate-400"> /siempre</span>
              </div>
              <p className="text-xs text-slate-400 mt-1.5">Para probar todo y cotizar de vez en cuando</p>
              <ul className="space-y-2.5 mt-6 flex-1">
                <CHECK bold>3 presupuestos al mes</CHECK>
                <CHECK>Plantillas + base APU 2026 + AIU/IVA</CHECK>
                <CHECK>Contrato de obra con doble firma</CHECK>
                <CHECK>Avances en vivo para tu cliente</CHECK>
                <CHECK>Gastos + utilidad real con semáforo</CHECK>
                <CHECK>Cuentas de cobro y caja neta</CHECK>
                <CHECK>Mini-CRM + reputación pública</CHECK>
              </ul>
              <Link to="/registro" className="mt-7 text-center border-2 border-navy-600 text-navy-600 font-bold text-sm py-3 rounded-xl hover:bg-navy-50 transition">
                Empezar gratis
              </Link>
            </div>

            {/* PRO */}
            <div className="bg-white rounded-2xl p-7 flex flex-col relative ring-4 ring-emerald-400">
              <span className="absolute -top-3.5 left-1/2 -translate-x-1/2 bg-emerald-500 text-white text-[10px] font-black uppercase tracking-wider px-4 py-1.5 rounded-full">
                Para el que vive de esto
              </span>
              <p className="font-bold text-slate-700">Pro</p>
              <div className="mt-3 flex items-end gap-2">
                <span className="text-4xl font-black text-slate-800">$79.000</span>
                <span className="text-sm text-slate-400 pb-1.5">/mes</span>
              </div>
              <p className="text-xs text-slate-400 mt-1.5">Cotiza todo lo que tu negocio necesite</p>
              <ul className="space-y-2.5 mt-6 flex-1">
                <CHECK bold>Presupuestos ILIMITADOS</CHECK>
                <CHECK>Plantillas + base APU 2026 + AIU/IVA</CHECK>
                <CHECK>Contrato de obra con doble firma</CHECK>
                <CHECK>Avances en vivo para tu cliente</CHECK>
                <CHECK>Gastos + utilidad real con semáforo</CHECK>
                <CHECK>Cuentas de cobro y caja neta</CHECK>
                <CHECK bold>Soporte prioritario por WhatsApp</CHECK>
              </ul>
              <Link to="/registro" className="mt-7 text-center bg-emerald-500 hover:bg-emerald-400 text-white font-bold text-sm py-3 rounded-xl transition">
                Empezar con Pro
              </Link>
              <p className="text-[10px] text-slate-400 text-center mt-2">
                Una obra cerrada al año paga 3 años de Pro. La cuenta la haces tú.
              </p>
            </div>
          </div>
          <p className="text-center text-[11px] text-blue-400 mt-6">
            Precios en pesos colombianos · Cancela cuando quieras · Tus datos y proyectos siguen siendo tuyos
          </p>
        </div>
      </section>

      {/* ── FAQ ── */}
      <section className="max-w-3xl mx-auto px-4 py-16">
        <h2 className="text-2xl font-black text-slate-800 text-center mb-8">Preguntas frecuentes</h2>
        <div className="space-y-3">
          {[
            ['¿Qué diferencia hay entre Básico y Pro?', 'Solo una: el volumen. En Básico haces 3 presupuestos al mes con TODAS las funciones (contrato, avances, WhatsApp, todo). En Pro son ilimitados. Si cotizas más de 3 obras al mes, Pro se paga solo.'],
            ['¿Los precios de la base APU son confiables?', 'Son precios de referencia 2026 del mercado colombiano con factores por ciudad. Siempre puedes ajustar cualquier precio a tu realidad — tu ajuste queda guardado en el presupuesto.'],
            ['¿El contrato digital tiene validez?', 'Es un acuerdo privado con evidencia digital: nombre, documento, fecha y hora quedan registrados junto al texto íntegro. La Ley 527 de 1999 reconoce los mensajes de datos como medio de prueba en Colombia. Para obras con formalidades adicionales, consulta con tu abogado.'],
            ['¿Mi cliente necesita instalar algo?', 'Nada. Abre el enlace en su WhatsApp: ve el presupuesto, firma el contrato y sigue los avances desde el navegador de su celular.'],
            ['¿Cómo pago el plan Pro?', 'Por Nequi o transferencia Bancolombia desde la misma app. Reportas el pago y activamos tu Pro en menos de 24 horas.'],
            ['¿Cómo funcionan las cuentas de cobro?', 'Cada corte de avance se liquida automáticamente: valor ejecutado menos amortización del anticipo del contrato. Sale el PDF con tu firma y cuenta bancaria, listo para enviar por WhatsApp. Cuando te paguen, un tap y tu caja neta se actualiza.'],
            ['¿Mi cliente ve mis gastos y mi utilidad?', 'No. El cliente ve el avance de su obra, las fotos y sus cuentas de cobro. Tus gastos, tu utilidad real y tu caja neta son privados — solo tuyos.'],
            ['¿Sirve si soy maestro de obra y no empresa?', 'Está hecho para ti. La cuenta de cobro es el documento estándar del contratista persona natural en Colombia, y el contrato protege tu trabajo aunque no tengas empresa constituida.'],
            ['¿Qué pasa con mis datos si cancelo?', 'Son tuyos. Exportas todo a Excel y PDF, y tu cuenta Básica sigue activa con tus proyectos.'],
          ].map(([q, a], i) => (
            <details key={i} className="bg-slate-50 rounded-xl p-4 group">
              <summary className="font-semibold text-sm text-slate-700 cursor-pointer list-none flex justify-between items-center">
                {q} <ChevronRight className="w-4 h-4 text-slate-400 group-open:rotate-90 transition shrink-0 ml-2" />
              </summary>
              <p className="text-sm text-slate-500 mt-3 leading-relaxed">{a}</p>
            </details>
          ))}
        </div>
      </section>

      {/* ── CTA FINAL ── */}
      <section className="bg-gradient-to-br from-navy-800 to-navy-600 py-16 text-center px-4">
        <h2 className="text-2xl sm:text-3xl font-black text-white">De la cotización al último peso cobrado</h2>
        <p className="text-blue-200 mt-3">Presupuestos · Contratos · Avances · Gastos · Cuentas de cobro · Clientes · Reputación<br/>Todo gratis para empezar. Sin tarjeta. Listo en 2 minutos.</p>
        <Link to="/registro" className="inline-flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-white font-bold px-8 py-4 rounded-xl transition mt-7 text-sm">
          Crear mi cuenta gratis <ChevronRight className="w-4 h-4" />
        </Link>
      </section>

      {/* ── FOOTER ── */}
      <footer className="bg-navy-900 text-blue-300 text-xs py-8 px-4">
        <div className="max-w-6xl mx-auto flex flex-wrap justify-between gap-4">
          <div className="flex items-center gap-2">
            <Building2 className="w-4 h-4" />
            <span className="font-bold text-white">PresupuestarCO</span>
            <span>· Hecho en Colombia 🇨🇴</span>
          </div>
          <div className="flex gap-5">
            <a href="#funciones" className="hover:text-white transition">Funciones</a>
            <a href="#precios" className="hover:text-white transition">Precios</a>
            <Link to="/login" className="hover:text-white transition">Iniciar sesión</Link>
            <Link to="/registro" className="hover:text-white transition">Registrarse</Link>
          </div>
        </div>
      </footer>

      <BotonWhatsApp />
    </div>
  )
}
