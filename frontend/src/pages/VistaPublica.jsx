import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { CheckCircle2, ChevronDown, ChevronUp, Phone, Building2 } from 'lucide-react'
import { shareAPI } from '../services/api'
import InfoTip from '../components/InfoTip'
import Lightbox from '../components/Lightbox'
import { comprimirImagen } from '../utils/imagen'

const COP = (v) => '$' + Math.round(v || 0).toLocaleString('es-CO')

function PadFirma({ onChange }) {
  const canvasRef = React.useRef(null)
  const dibujando = React.useRef(false)
  const [hayTrazo, setHayTrazo] = React.useState(false)

  const pos = (e) => {
    const c = canvasRef.current
    const r = c.getBoundingClientRect()
    const t = e.touches?.[0] || e
    return { x: (t.clientX - r.left) * (c.width / r.width), y: (t.clientY - r.top) * (c.height / r.height) }
  }
  const empezar = (e) => {
    e.preventDefault()
    dibujando.current = true
    const ctx = canvasRef.current.getContext('2d')
    const p = pos(e)
    ctx.beginPath(); ctx.moveTo(p.x, p.y)
  }
  const mover = (e) => {
    if (!dibujando.current) return
    e.preventDefault()
    const ctx = canvasRef.current.getContext('2d')
    ctx.lineWidth = 2.5; ctx.lineCap = 'round'; ctx.strokeStyle = '#1C3A5E'
    const p = pos(e)
    ctx.lineTo(p.x, p.y); ctx.stroke()
    if (!hayTrazo) setHayTrazo(true)
  }
  const terminar = () => {
    if (!dibujando.current) return
    dibujando.current = false
    onChange(canvasRef.current.toDataURL('image/png'))
  }
  const limpiar = () => {
    const c = canvasRef.current
    c.getContext('2d').clearRect(0, 0, c.width, c.height)
    setHayTrazo(false)
    onChange('')
  }

  return (
    <div>
      <canvas ref={canvasRef} width={560} height={180}
              className="w-full h-32 bg-white border-2 border-dashed border-slate-300 rounded-xl touch-none"
              onMouseDown={empezar} onMouseMove={mover} onMouseUp={terminar} onMouseLeave={terminar}
              onTouchStart={empezar} onTouchMove={mover} onTouchEnd={terminar} />
      <div className="flex justify-between items-center mt-1.5">
        <p className="text-[10px] text-slate-400">{hayTrazo ? 'Firma capturada ✓' : 'Firma aquí con tu dedo o mouse'}</p>
        <button type="button" onClick={limpiar} className="text-[10px] text-slate-400 underline">Limpiar</button>
      </div>
    </div>
  )
}

export default function VistaPublica() {
  const { token } = useParams()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [abiertos, setAbiertos] = useState({})
  const [aceptando, setAceptando] = useState(false)
  const [aceptado, setAceptado] = useState(false)
  const [rechazado, setRechazado] = useState(false)
  const [showFirma, setShowFirma] = useState(false)
  const [firma, setFirma] = useState({ nombre: '', documento: '', firma_imagen: '' })
  const [modoFirma, setModoFirma] = useState('dibujar')  // dibujar | subir | escribir
  const [firmaInfo, setFirmaInfo] = useState(null)
  const [otrosiFirmando, setOtrosiFirmando] = useState(null)  // otrosi en proceso de aprobacion
  const [otResuelto, setOtResuelto] = useState({})            // {id: 'aprobado'|'rechazado'} local
  const [comentando, setComentando] = useState({})            // {avanceId: texto}
  const [interLocal, setInterLocal] = useState({})            // {avanceId: {reacciones, comentarios}} optimista
  const [galeria, setGaleria] = useState(null)                // {fotos, inicial}
  const [verHistoria, setVerHistoria] = useState(false)
  const [disenos, setDisenos] = useState(null)                // null = no cargados aun (lazy)
  const [comDiseno, setComDiseno] = useState({})              // did -> {nombre, texto}
  const [hintGuardar, setHintGuardar] = useState(() => !localStorage.getItem('obra_guardada_hint'))

  const AvisoFirma = () => (
    <p className="text-[9px] text-slate-400 leading-relaxed mt-2 text-center">
      🔒 Firma electrónica con validez legal (Ley 527 de 1999). Al firmar autorizas el tratamiento de tus
      datos (nombre, documento, firma y datos del dispositivo) para la gestión documental de esta obra.{' '}
      <a href="/legal" target="_blank" rel="noreferrer" className="underline text-slate-500">Términos y política de datos</a>
    </p>
  )

  const Cejilla = ({ children }) => (
    <p className="text-[10px] uppercase tracking-[0.2em] font-bold text-slate-400 mb-2 mt-6 px-1">{children}</p>
  )

  const interactuar = async (avanceId, tipo, valor) => {
    try {
      const r = await shareAPI.interactuar(token, avanceId, {
        tipo, valor, nombre: firmaInfo?.nombre || data?.firma?.nombre || 'Cliente'
      })
      setInterLocal(m => ({ ...m, [avanceId]: { reacciones: r.reacciones, comentarios: r.comentarios } }))
      if (tipo === 'comentario') {
        setComentando(c => ({ ...c, [avanceId]: '' }))
        toast.success('Tu contratista fue notificado 💬')
      }
    } catch (e) { toast.error(e.message) }
  }
  const [contrato, setContrato] = useState(null)
  const [leido, setLeido] = useState(false)
  const [avances, setAvances] = useState(null)
  const [encuesta, setEncuesta] = useState({ estrellas: 0, recomendaria: true, comentario: '' })
  const [encuestaEnviada, setEncuestaEnviada] = useState(false)
  const [enviandoEncuesta, setEnviandoEncuesta] = useState(false)
  const [showEntrega, setShowEntrega] = useState(false)
  const [showPendientes, setShowPendientes] = useState(false)
  const [pendientesTxt, setPendientesTxt] = useState('')
  const [entregaConfirmada, setEntregaConfirmada] = useState(false)

  useEffect(() => {
    shareAPI.verPublico(token)
      .then(d => {
        setData(d)
        setAceptado(d.estado === 'aceptado' || d.estado === 'entrega_solicitada')
        setRechazado(d.estado === 'rechazado')
        if (d.firma) setFirmaInfo(d.firma)
        if (d.estado === 'aceptado' || d.estado === 'entrega_solicitada') {
          shareAPI && import('../services/api').then(m => m.avancesAPI.publicos(token).then(setAvances).catch(() => {}))
        }
        // Abrir el primer capitulo por defecto
        const caps = Object.keys(d.capitulos || {})
        if (caps.length) setAbiertos({ [caps[0]]: true })
      })
      .catch(e => setError(e.message))
  }, [token])

  const rechazar = async () => {
    if (!confirm('¿Deseas rechazar este presupuesto? El contratista será notificado.')) return
    try {
      await shareAPI.rechazar(token)
      setRechazado(true)
    } catch (e) { alert(e.message) }
  }

  const aceptar = () => {
    setShowFirma(true)
    setLeido(false)
    if (!contrato) shareAPI.contrato(token).then(setContrato).catch(() => {})
  }

  const confirmarFirma = async () => {
    if (firma.nombre.trim().length < 5) { alert('Escribe tu nombre completo'); return }
    setAceptando(true)
    try {
      const res = await shareAPI.aceptar(token, firma)
      setAceptado(true)
      setShowFirma(false)
      setFirmaInfo({ nombre: res.firmado_por, fecha: new Date(res.fecha).toLocaleString('es-CO') })
    } catch (e) { alert(e.message) }
    finally { setAceptando(false) }
  }

  if (error) return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6 text-center">
      <div>
        <p className="text-slate-600 font-medium">{error}</p>
        <p className="text-sm text-slate-400 mt-2">Verifica el enlace o pide uno nuevo al contratista.</p>
      </div>
    </div>
  )

  if (!data) return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center text-slate-400">
      Cargando presupuesto...
    </div>
  )

  // ── PROYECTO TERMINADO: acceso cerrado + encuesta ────────────────────────
  if (data.terminado) {
    const yaRespondida = data.encuesta_respondida || encuestaEnviada
    const enviarEncuesta = async () => {
      if (encuesta.estrellas < 1) { alert('Selecciona una calificación de 1 a 5 estrellas'); return }
      setEnviandoEncuesta(true)
      try {
        await shareAPI.encuesta(token, encuesta)
        setEncuestaEnviada(true)
      } catch (e) { alert(e.message) }
      finally { setEnviandoEncuesta(false) }
    }
    return (
      <div className="min-h-screen bg-slate-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-lg w-full max-w-md p-6 text-center">
          {data.contratista.logo_b64 ? (
            <img src={data.contratista.logo_b64} alt="" className="w-14 h-14 rounded-xl object-contain mx-auto mb-3 border border-slate-100 p-1" />
          ) : (
            <div className="w-14 h-14 bg-emerald-100 rounded-2xl flex items-center justify-center mx-auto mb-3">
              <CheckCircle2 className="w-7 h-7 text-emerald-600" />
            </div>
          )}
          <h1 className="font-bold text-slate-800 text-lg">¡Obra culminada! 🎉</h1>
          <p className="text-sm text-slate-500 mt-1">
            El proyecto <strong>{data.proyecto}</strong> ({data.numero}) fue entregado por{' '}
            <strong>{data.contratista.empresa || data.contratista.nombre}</strong>.
          </p>
          <p className="text-[11px] text-slate-400 mt-2">
            Este enlace ya no muestra el detalle del presupuesto.
          </p>
          <a href={`/api/share/publico/${token}/acta.pdf`} target="_blank" rel="noreferrer"
             className="inline-block mt-3 text-[11px] font-medium text-navy-600 border border-navy-200 rounded-lg px-3 py-1.5">
            📄 Descargar Acta de Entrega (PDF)
          </a>

          {yaRespondida ? (
            <div className="mt-5 bg-emerald-50 rounded-xl p-4">
              <p className="text-sm font-medium text-emerald-700">¡Gracias por tu calificación!</p>
              <p className="text-[11px] text-emerald-600 mt-1">Tu opinión ayuda al contratista a mejorar.</p>
            </div>
          ) : (
            <div className="mt-5 text-left space-y-3">
              <p className="text-sm font-semibold text-slate-700 text-center">¿Cómo fue tu experiencia?</p>
              <div className="flex justify-center gap-2">
                {[1,2,3,4,5].map(n => (
                  <button key={n} onClick={() => setEncuesta(e => ({ ...e, estrellas: n }))}
                          className={`text-3xl transition ${n <= encuesta.estrellas ? '' : 'grayscale opacity-40'}`}>
                    ⭐
                  </button>
                ))}
              </div>
              <label className="flex items-center justify-center gap-2 text-xs text-slate-600">
                <input type="checkbox" checked={encuesta.recomendaria}
                       onChange={e => setEncuesta(x => ({ ...x, recomendaria: e.target.checked }))} />
                Recomendaría a este contratista
              </label>
              <textarea className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-xs outline-none focus:border-emerald-400 min-h-[70px]"
                        placeholder="Cuéntanos cómo fue el trabajo (opcional)"
                        value={encuesta.comentario}
                        onChange={e => setEncuesta(x => ({ ...x, comentario: e.target.value }))} />
              <button onClick={enviarEncuesta} disabled={enviandoEncuesta}
                      className="w-full py-3 rounded-xl bg-emerald-500 text-white text-sm font-bold disabled:opacity-50">
                {enviandoEncuesta ? 'Enviando...' : 'Enviar calificación'}
              </button>
            </div>
          )}
          <p className="text-[9px] text-slate-300 mt-4">Hecho con PresupuestarCO</p>
        </div>
      </div>
    )
  }

  const t = data.totales
  const c = data.contratista

  return (
    <div className="min-h-screen bg-slate-50 pb-32">
      {data.demo && (
        <div className="bg-amber-400 text-amber-900 text-center text-xs font-bold py-2 px-4">
          🧪 Presupuesto de DEMOSTRACIÓN — así lo verá tu cliente ·{' '}
          <a href="/registro" className="underline">Crea el tuyo gratis</a>
        </div>
      )}
      {/* Header del contratista — papel de plano */}
      <div className="relative bg-navy-900 text-white px-5 pt-8 pb-14 overflow-hidden">
        <div className="absolute inset-0 opacity-[0.07] pointer-events-none"
             style={{ backgroundImage: 'linear-gradient(rgba(255,255,255,.6) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.6) 1px, transparent 1px)', backgroundSize: '28px 28px' }} />
        <div className="absolute -top-20 -right-20 w-64 h-64 rounded-full bg-emerald-400/10 blur-3xl pointer-events-none" />
        <div className="relative max-w-lg mx-auto">
          <div className="flex items-center gap-3 mb-7">
            {c.logo_b64 ? (
              <img src={c.logo_b64} alt="" className="w-12 h-12 rounded-2xl object-contain bg-white p-1 ring-2 ring-white/20" />
            ) : (
              <div className="w-12 h-12 bg-white/10 rounded-2xl flex items-center justify-center ring-2 ring-white/10">
                <Building2 className="w-6 h-6" />
              </div>
            )}
            <div>
              <p className="font-semibold">{c.empresa || c.nombre}</p>
              {c.empresa && <p className="text-xs text-blue-200">{c.nombre}</p>}
              {c.reputacion && c.reputacion.promedio > 0 && (
                <a href={c.reputacion.slug ? `/c/${c.reputacion.slug}` : '#'}
                   className="inline-flex items-center gap-1 text-[10px] bg-amber-400/20 text-amber-300 px-2 py-0.5 rounded-full mt-1">
                  ⭐ {c.reputacion.promedio} · {c.reputacion.obras} obra{c.reputacion.obras !== 1 ? 's' : ''} terminada{c.reputacion.obras !== 1 ? 's' : ''}
                </a>
              )}
            </div>
          </div>
          <p className="text-emerald-300/80 text-[10px] uppercase tracking-[0.2em] font-bold mb-1.5">
            {data.sector === 'publico' ? 'Panel de seguimiento · Interventoría' : 'Presupuesto de obra'} {data.numero && <span className="text-white/60 tracking-normal">· {data.numero}</span>}
          </p>
          <h1 className="text-[26px] font-bold leading-tight tracking-tight">{data.proyecto}</h1>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 mt-2 text-xs text-blue-200/80">
            {data.sector === 'publico' && data.entidad_nombre && <span><strong className="text-white/90 font-semibold">{data.entidad_nombre}</strong></span>}
            {data.sector === 'publico' && data.contrato_numero && <span className="text-blue-300/70">· Contrato {data.contrato_numero}</span>}
            {data.sector !== 'publico' && data.cliente && <span>Para <strong className="text-white/90 font-semibold">{data.cliente}</strong></span>}
            {data.direccion && <span className="text-blue-300/70">· {data.direccion}</span>}
            <span className="text-blue-300/70">· {data.fecha}</span>
          </div>
        </div>
      </div>

      {/* Total destacado */}
      <div className="relative z-10 max-w-lg mx-auto px-4 -mt-8">
        <div className="bg-white rounded-2xl shadow-xl shadow-navy-900/10 ring-1 ring-slate-100 p-5 text-center">
          <p className="text-[10px] text-slate-400 uppercase tracking-[0.2em] font-bold">Valor total de tu obra</p>
          <p className="text-[34px] font-black text-navy-800 mt-1 tracking-tight tabular-nums">{COP(t.total)}</p>
          {aceptado && (
            <div className="mt-2">
              <span className="inline-flex items-center gap-1.5 text-sm text-emerald-700 bg-emerald-50 px-3 py-1 rounded-full font-medium">
                <CheckCircle2 className="w-4 h-4" /> Presupuesto aceptado
              </span>
              {firmaInfo && (
                <p className="text-[11px] text-slate-400 mt-1.5">
                  Firmado por <strong className="text-slate-500">{firmaInfo.nombre}</strong> · {firmaInfo.fecha}
                </p>
              )}
              <a href={`/api/share/publico/${token}/contrato.pdf`} target="_blank" rel="noreferrer"
                 className="inline-block mt-2 text-[11px] font-medium text-navy-600 border border-navy-200 rounded-lg px-3 py-1.5">
                📄 Descargar contrato firmado (PDF)
              </a>
            </div>
          )}
          {rechazado && !aceptado && (
            <span className="inline-flex items-center gap-1.5 mt-2 text-sm text-red-600 bg-red-50 px-3 py-1 rounded-full font-medium">
              Presupuesto rechazado
            </span>
          )}
        </div>
      </div>

      {/* ENTREGA SOLICITADA: el contratista reporta obra terminada */}
      {data.estado === 'entrega_solicitada' && !entregaConfirmada && (
        <div className="max-w-lg mx-auto px-4 mt-4">
          <div className="bg-amber-50 border-2 border-amber-300 rounded-2xl p-4 text-center">
            <p className="text-2xl">🏗️➡️🏁</p>
            <h3 className="font-bold text-amber-800 mt-1">El contratista reporta la obra terminada</h3>
            <p className="text-xs text-amber-700 mt-1.5">
              Revisa tu obra. Si todo está bien, confirma el recibido a satisfacción —
              se generará el Acta de Entrega firmada por ambos.
            </p>
            <div className="flex gap-2 mt-4">
              <button onClick={() => setShowPendientes(true)}
                      className="flex-1 py-2.5 rounded-xl border border-amber-300 text-amber-700 text-xs font-medium">
                Hay pendientes
              </button>
              <button onClick={() => { setShowEntrega(true); setModoFirma('dibujar'); setFirma(f => ({ ...f, firma_imagen: '' })) }}
                      className="flex-[2] py-2.5 rounded-xl bg-emerald-500 text-white text-xs font-bold">
                ✓ Confirmar recibido a satisfacción
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Capitulos */}
      <div className="max-w-lg mx-auto px-4 space-y-2">
        {/* ── 🎨 Diseños: el cliente VE su obra antes de que exista ── */}
        {!data.demo && data.n_disenos > 0 && (
          <>
          <Cejilla>Diseños de tu proyecto</Cejilla>
          <div className="bg-white rounded-2xl border border-slate-100 p-4 mb-2">
            {disenos === null ? (
              <button onClick={() => shareAPI.disenos(token).then(r => setDisenos(r.disenos || [])).catch(() => setDisenos([]))}
                      className="w-full py-2.5 rounded-xl border border-slate-200 text-sm font-semibold text-navy-600 hover:bg-slate-50">
                🎨 Ver los diseños del proyecto
              </button>
            ) : disenos.length === 0 ? (
              <p className="text-xs text-slate-400 text-center py-2">Aún no hay diseños cargados para este proyecto.</p>
            ) : (
              <div className="grid grid-cols-2 gap-3">
                {disenos.map(d => (
                  <div key={d.id} className="border border-slate-100 rounded-xl overflow-hidden">
                    <img src={d.imagen_b64} alt={d.titulo} className="w-full h-32 object-cover cursor-zoom-in"
                         onClick={() => setGaleria({ fotos: disenos.map(x => x.imagen_b64), inicial: disenos.indexOf(d) })} />
                    <div className="p-2">
                      <p className="text-[11px] font-semibold text-slate-700 truncate">{d.titulo || 'Diseño'}</p>
                      {(d.comentarios || []).map((cm, k) => (
                        <p key={k} className={`text-[10px] mt-1 rounded-lg px-2 py-1 ${cm.autor === 'cliente' ? 'bg-blue-50 text-blue-700' : 'bg-slate-50 text-slate-600'}`}>
                          <strong>{cm.nombre}:</strong> {cm.texto}
                        </p>
                      ))}
                      <div className="mt-1.5 space-y-1">
                        <input value={comDiseno[d.id]?.texto || ''} placeholder='Comenta este diseño ("me gusta, pero en gris")'
                               onChange={e => setComDiseno(prev => ({ ...prev, [d.id]: { ...prev[d.id], texto: e.target.value } }))}
                               className="w-full text-[10px] border border-slate-200 rounded-lg px-2 py-1.5" />
                        <div className="flex gap-1">
                          <input value={comDiseno[d.id]?.nombre || firma.nombre || ''} placeholder="Tu nombre"
                                 onChange={e => setComDiseno(prev => ({ ...prev, [d.id]: { ...prev[d.id], nombre: e.target.value } }))}
                                 className="flex-1 text-[10px] border border-slate-200 rounded-lg px-2 py-1.5" />
                          <button onClick={() => {
                                    const c2 = comDiseno[d.id] || {}
                                    const texto = (c2.texto || '').trim()
                                    if (!texto) return
                                    shareAPI.comentarDiseno(token, d.id, { nombre: c2.nombre || firma.nombre || '', texto })
                                      .then(r => {
                                        setDisenos(prev => prev.map(x => x.id === d.id ? { ...x, comentarios: r.comentarios } : x))
                                        setComDiseno(prev => ({ ...prev, [d.id]: { ...prev[d.id], texto: '' } }))
                                      }).catch(() => {})
                                  }}
                                  className="text-[10px] font-bold bg-navy-600 text-white rounded-lg px-3">💬 Enviar</button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          </>
        )}

        <Cejilla>Tu presupuesto, capítulo por capítulo</Cejilla>
        {Object.entries(data.capitulos || {}).map(([cap, info]) => (
          <div key={cap} className="bg-white rounded-2xl overflow-hidden ring-1 ring-slate-100">
            <button onClick={() => setAbiertos(a => ({ ...a, [cap]: !a[cap] }))}
                    className="w-full flex items-center justify-between p-4">
              <div className="text-left">
                <p className="text-sm font-semibold text-slate-700">{cap.charAt(0) + cap.slice(1).toLowerCase()}</p>
                <p className="text-xs text-slate-400">{info.items.length} ítem{info.items.length !== 1 ? 's' : ''}</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-slate-800 tabular-nums">{COP(info.subtotal)}</span>
                <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${abiertos[cap] ? 'rotate-180' : ''}`} />
              </div>
            </button>
            {abiertos[cap] && (
              <div className="border-t border-slate-100 divide-y divide-slate-50">
                {info.items.map((it, i) => (
                  <div key={i} className="px-4 py-2.5 flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="text-xs text-slate-600 leading-snug">{it.descripcion}</p>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        {it.cantidad} {it.unidad} × {COP(it.precio_unitario)}
                      </p>
                    </div>
                    <span className="text-xs font-medium text-slate-700 shrink-0">{COP(it.precio_total)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Resumen financiero */}
      <div className="max-w-lg mx-auto px-4">
        <Cejilla>Así se compone el valor</Cejilla>
        <div className="bg-white rounded-2xl ring-1 ring-slate-100 p-4 space-y-2 text-sm">
          <div className="flex justify-between text-slate-600">
            <span>Costo directo</span><span>{COP(t.subtotal_directo)}</span>
          </div>
          {t.aiu_total > 0 && (
            <>
              <div className="flex justify-between text-slate-500 text-xs">
                <span>Administración ({t.admin_pct}%)<InfoTip texto="Los costos de gestionar tu obra: coordinación, transporte, herramienta. Junto con Imprevistos y Utilidad forman el AIU, el estándar de la construcción en Colombia." /></span><span>{COP(t.admin_valor)}</span>
              </div>
              <div className="flex justify-between text-slate-500 text-xs">
                <span>Imprevistos ({t.imprevistos_pct}%)</span><span>{COP(t.imprevistos_valor)}</span>
              </div>
              <div className="flex justify-between text-slate-500 text-xs">
                <span>Utilidad ({t.utilidad_pct}%)<InfoTip texto="La ganancia del contratista por dirigir tu obra — es transparente y está pactada desde el inicio, no escondida en los precios." /></span><span>{COP(t.utilidad_valor)}</span>
              </div>
            </>
          )}
          <div className="flex justify-between text-slate-600">
            <span>IVA<InfoTip texto="En contratos de construcción con AIU, la ley (Art. 462-1) calcula el IVA solo sobre la utilidad — por eso puede verse menor de lo que esperabas." /></span><span>{COP(t.iva)}</span>
          </div>
          <div className="flex justify-between font-bold text-slate-800 pt-2 border-t border-slate-100">
            <span>Total</span><span>{COP(t.total)}</span>
          </div>
          <p className="text-[10px] text-slate-400 pt-1">{t.regimen_iva}</p>
        </div>

        {data.notas && (
          <div className="bg-white rounded-xl p-4 mt-2 text-xs text-slate-500 whitespace-pre-wrap">
            {data.notas}
          </div>
        )}

        {c.condiciones && (
          <div className="bg-white rounded-xl p-4 mt-2">
            <p className="text-xs font-semibold text-slate-600 mb-2">Condiciones</p>
            <p className="text-[11px] text-slate-400 whitespace-pre-wrap leading-relaxed">{c.condiciones}</p>
          </div>
        )}

        {/* ═══ HERO: TU OBRA, en primera persona ═══ */}
        {aceptado && avances && <Cejilla>Tu obra en vivo</Cejilla>}
        {aceptado && avances && (
          (() => {
            const pct = avances.porcentaje_actual || 0
            const totalObra = (data.totales?.total || 0) +
              (data.otrosies || []).filter(o => (otResuelto[o.id] || o.estado) === 'aprobado')
                                   .reduce((s, o) => s + (o.total || 0), 0)
            const pagado = avances.pagado_total || 0
            return (
              <div className="bg-gradient-to-br from-navy-700 to-navy-900 rounded-2xl p-5 text-white shadow-xl shadow-navy-900/20 ring-1 ring-white/10">
                <p className="text-[11px] uppercase tracking-wide text-white/60 font-bold">Tu obra</p>
                <p className="text-2xl font-bold mt-0.5">
                  {pct >= 100 ? '¡Terminada! 🎉' : `Va en ${Math.round(pct)}% 🏗️`}
                </p>
                <div className="h-2.5 bg-white/15 rounded-full overflow-hidden mt-2">
                  <div className="h-full bg-emerald-400 transition-all" style={{ width: `${Math.min(100, pct)}%` }} />
                </div>
                <div className="flex justify-between mt-3 text-[11px]">
                  <span className="text-white/70">
                    Pagado en cortes: <strong className="text-white">{COP(pagado)}</strong>
                  </span>
                  <span className="text-white/70">
                    Valor de tu obra: <strong className="text-white">{COP(totalObra)}</strong>
                  </span>
                </div>
              </div>
            )
          })()
        )}

        {/* ➕ ADICIONALES (otrosies) — el cliente aprueba con nueva firma */}
        {aceptado && data.otrosies?.length > 0 && (
          <div className="mt-4 space-y-2">
            <p className="text-sm font-semibold text-slate-700 px-1">➕ Adicionales de obra</p>
            {data.otrosies.map(o => {
              const estado = otResuelto[o.id] || o.estado
              return (
              <div key={o.id} className={`bg-white rounded-xl p-4 border-2 ${estado === 'propuesto' ? 'border-amber-300' : estado === 'aprobado' ? 'border-emerald-200' : 'border-slate-100 opacity-60'}`}>
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-sm font-bold text-slate-700">Otrosí N.{o.numero} · {COP(o.total)}</p>
                    {o.motivo && <p className="text-[11px] text-slate-400">{o.motivo}</p>}
                  </div>
                  {estado === 'aprobado' && (
                    <span className="text-[9px] font-bold bg-emerald-100 text-emerald-700 px-2 py-1 rounded-full shrink-0">✍️ Aprobado</span>
                  )}
                  {estado === 'rechazado' && (
                    <span className="text-[9px] font-bold bg-slate-100 text-slate-500 px-2 py-1 rounded-full shrink-0">No aprobado</span>
                  )}
                </div>
                <div className="mt-2 space-y-1">
                  {o.items.map((it, i) => (
                    <div key={i} className="flex justify-between text-[11px] text-slate-500">
                      <span className="truncate mr-2">{it.descripcion}</span>
                      <span className="shrink-0">{parseFloat(it.cantidad) || 0} {it.unidad} × {COP(it.precio_unitario)}</span>
                    </div>
                  ))}
                </div>
                {estado === 'propuesto' && (
                  <div className="flex gap-2 mt-3">
                    <button onClick={() => { setOtrosiFirmando(o); setFirma({ nombre: firmaInfo?.nombre || '', documento: '', firma_imagen: '' }) }}
                            className="flex-1 py-2.5 rounded-xl bg-emerald-500 text-white text-xs font-bold">
                      ✍️ Aprobar y firmar
                    </button>
                    <button onClick={async () => {
                              try {
                                await shareAPI.otrosiRechazar(token, o.id, '')
                                setOtResuelto(m => ({ ...m, [o.id]: 'rechazado' }))
                                toast('El contratista fue notificado')
                              } catch (e) { toast.error(e.message) }
                            }}
                            className="py-2.5 px-4 rounded-xl border border-slate-300 text-slate-500 text-xs font-medium">
                      No por ahora
                    </button>
                  </div>
                )}
                {estado === 'aprobado' && (
                  <a href={`/api/share/publico/${token}/otrosi/${o.id}.pdf`} target="_blank" rel="noreferrer"
                     className="inline-block mt-2 text-[11px] font-bold text-navy-600 border border-navy-200 rounded-lg px-2.5 py-1.5">
                    📄 Descargar Otrosí firmado (PDF)
                  </a>
                )}
              </div>
            )})}
            {(() => {
              const aprobadosTotal = data.otrosies.filter(o => (otResuelto[o.id] || o.estado) === 'aprobado')
                                       .reduce((s, o) => s + (o.total || 0), 0)
              return aprobadosTotal > 0 && data.totales && (
                <p className="text-[11px] text-slate-500 text-center bg-white rounded-xl py-2.5">
                  Valor actualizado del contrato: <strong className="text-slate-700">{COP((data.totales.total || 0) + aprobadosTotal)}</strong>
                  <span className="text-slate-400"> (original {COP(data.totales.total)} + adicionales {COP(aprobadosTotal)})</span>
                </p>
              )
            })()}
          </div>
        )}

        {/* Avances de obra (visible tras aceptar) */}
        {aceptado && avances && avances.avances?.length > 0 && (
          <div className="mt-4">
            {/* Resumen: % ponderado + valor ejecutado */}
            <div className="bg-white rounded-xl p-4 mb-2">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-semibold text-slate-700">Avance de tu obra</p>
                <span className="text-sm font-bold text-emerald-600">{avances.porcentaje_actual}%</span>
              </div>
              <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden mb-3">
                <div className="h-full bg-emerald-500 rounded-full transition-all"
                     style={{ width: `${avances.porcentaje_actual}%` }} />
              </div>
              <div className="flex justify-between text-xs bg-emerald-50 rounded-lg p-2.5">
                <span className="text-emerald-700">Valor ejecutado</span>
                <span className="font-bold text-emerald-700">
                  {COP(avances.valor_ejecutado_actual)} <span className="font-normal text-emerald-500">de {COP(avances.valor_total_directo)}</span>
                </span>
              </div>
              <p className="text-[9px] text-slate-300 mt-1.5">Avance ponderado por el valor de cada actividad del presupuesto (costo directo)</p>
            </div>

            {/* ESTADO DE PAGOS */}
            {avances.cuentas?.length > 0 && (
              <div className="bg-white rounded-2xl ring-1 ring-slate-100 p-4 mb-2">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-semibold text-slate-700">💵 Tus pagos, claros</p>
                  {avances.pendiente_total > 0 && (
                    <span className="text-[10px] font-bold bg-amber-100 text-amber-700 px-2 py-1 rounded-full">
                      Pendiente: {COP(avances.pendiente_total)}
                    </span>
                  )}
                </div>
                {avances.pagado_total > 0 && (
                  <p className="text-[11px] text-slate-400 mb-2">
                    Has pagado <strong className="text-emerald-600">{COP(avances.pagado_total)}</strong> de esta obra
                  </p>
                )}
                <div className="space-y-1.5">
                  {avances.cuentas.map((c, i) => (
                    <div key={i} className={`flex items-center justify-between gap-2 rounded-lg px-3 py-2 ${c.estado === 'pagada' ? 'bg-emerald-50' : 'bg-amber-50'}`}>
                      <div className="min-w-0">
                        <p className="text-xs font-medium text-slate-700">{c.numero} · {COP(c.neto)}</p>
                        <p className="text-[9px] text-slate-400">
                          {c.tipo === 'retegarantia' && '🔓 Retegarantía · '}
                          {c.estado === 'pagada' ? `✓ Pagada el ${c.fecha_pago}` : `Emitida el ${c.fecha}`}
                        </p>
                        {c.retencion > 0 && (
                          <p className="text-[9px] text-violet-500">
                            🔒 Retegarantía retenida: {COP(c.retencion)}
                            <InfoTip texto="Un porcentaje que se retiene de cada pago como garantía. Se paga al contratista cuando TÚ recibas la obra a satisfacción — es tu protección." />
                          </p>
                        )}
                        {c.estado !== 'pagada' && c.abonado > 0 && (
                          <p className="text-[9px] text-emerald-600">Abonado {COP(c.abonado)} · saldo {COP(c.neto - c.abonado)}</p>
                        )}
                      </div>
                      <div className="flex items-center gap-1.5 shrink-0">
                        {c.estado === 'enviada' && (
                          <span className="text-[9px] font-bold text-amber-700">⏳ Por pagar</span>
                        )}
                        {c.id > 0 && (
                          <a href={`/api/cuentas/publico/${token}/${c.id}.pdf`} target="_blank" rel="noreferrer"
                             className="text-[10px] font-medium text-navy-600 border border-navy-200 rounded-lg px-2 py-1">
                            📄 Ver
                          </a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
                <p className="text-[9px] text-slate-300 mt-2">
                  Cada cuenta corresponde a un corte de avance que puedes verificar abajo
                </p>
              </div>
            )}

            {/* Cortes de avance */}
            <div className="space-y-2">
              {avances.avances.map(a => (
                <div key={a.id} className="bg-white rounded-2xl ring-1 ring-slate-100 p-4">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="text-sm font-medium text-slate-700">{a.titulo}</p>
                      <p className="text-[10px] text-slate-400">{a.fecha}</p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="text-sm font-bold text-emerald-600">{a.porcentaje}%</p>
                      <p className="text-[10px] text-emerald-500">{COP(a.valor_ejecutado)}</p>
                    </div>
                  </div>
                  {a.descripcion && <p className="text-xs text-slate-500 mt-1.5 whitespace-pre-wrap">{a.descripcion}</p>}

                  {/* Detalle por actividad (solo las que tienen avance) */}
                  {a.items?.filter(it => it.pct > 0).length > 0 && (
                    <div className="mt-2.5 border-t border-slate-50 pt-2 space-y-1">
                      {a.items.filter(it => it.pct > 0).map((it, i) => (
                        <div key={i} className="flex items-center gap-2 text-[10px]">
                          <span className="flex-1 text-slate-500 truncate">{it.descripcion}</span>
                          <div className="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden shrink-0">
                            <div className="h-full bg-emerald-400 rounded-full" style={{ width: `${it.pct}%` }} />
                          </div>
                          <span className="text-slate-400 w-8 text-right shrink-0">{it.pct}%</span>
                          <span className="text-emerald-600 w-16 text-right shrink-0">{COP(it.valor_ejec)}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {a.fotos?.length > 0 && (
                    <div className="grid grid-cols-3 gap-1.5 mt-2">
                      {a.fotos.map((f, i) => (
                        <img key={i} src={f} alt="" onClick={() => setGaleria({ fotos: a.fotos, inicial: i })}
                             className="rounded-lg object-cover aspect-square w-full cursor-pointer active:scale-95 transition" />
                      ))}
                    </div>
                  )}

                  {/* ═══ PARTICIPACION: reacciones + comentarios ═══ */}
                  {!data.demo && (() => {
                    const inter = interLocal[a.id] || { reacciones: a.reacciones || {}, comentarios: a.comentarios || [] }
                    return (
                      <div className="mt-3 border-t border-slate-50 pt-2.5">
                        <div className="flex items-center gap-1.5">
                          {['👍', '❤️', '👏'].map(e => (
                            <button key={e} onClick={() => interactuar(a.id, 'reaccion', e)}
                                    className="flex items-center gap-1 text-sm bg-slate-50 hover:bg-emerald-50 border border-slate-100 rounded-full px-2.5 py-1 transition active:scale-95">
                              {e}{(inter.reacciones[e] || 0) > 0 && <span className="text-[10px] font-bold text-slate-500">{inter.reacciones[e]}</span>}
                            </button>
                          ))}
                        </div>
                        {inter.comentarios.length > 0 && (
                          <div className="mt-2 space-y-1.5">
                            {inter.comentarios.map((cm, i) => (
                              <div key={i} className={`rounded-lg px-2.5 py-1.5 text-[11px] ${cm.autor === 'contratista' ? 'bg-navy-600 text-white ml-5' : 'bg-slate-50 text-slate-600'}`}>
                                <span className={`font-bold ${cm.autor === 'contratista' ? 'text-white/80' : 'text-slate-500'}`}>
                                  {cm.autor === 'contratista' ? `👷 ${cm.nombre}` : cm.nombre}
                                </span>
                                <span className={cm.autor === 'contratista' ? 'text-white/50' : 'text-slate-300'}> · {cm.fecha}</span>
                                <p className="whitespace-pre-wrap">{cm.texto}</p>
                              </div>
                            ))}
                          </div>
                        )}
                        <div className="flex gap-1.5 mt-2">
                          <input className="flex-1 text-[11px] border border-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-emerald-300"
                                 placeholder="Escribe un comentario o pregunta..." maxLength={300}
                                 value={comentando[a.id] || ''}
                                 onChange={e => setComentando(c => ({ ...c, [a.id]: e.target.value }))}
                                 onKeyDown={e => { if (e.key === 'Enter' && (comentando[a.id] || '').trim()) interactuar(a.id, 'comentario', comentando[a.id].trim()) }} />
                          <button onClick={() => { const t = (comentando[a.id] || '').trim(); if (t) interactuar(a.id, 'comentario', t) }}
                                  className="text-[11px] font-bold text-white bg-navy-600 rounded-lg px-3 active:scale-95">
                            Enviar
                          </button>
                        </div>
                      </div>
                    )
                  })()}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ═══ 📂 MIS DOCUMENTOS: el expediente completo del cliente ═══ */}
        {aceptado && !data.demo && <Cejilla>Tus documentos</Cejilla>}
        {aceptado && !data.demo && (
          <div className="bg-white rounded-2xl ring-1 ring-slate-100 p-4">
            <p className="text-sm font-semibold text-slate-700 mb-2">📂 Todo tu expediente en un lugar</p>
            <div className="space-y-1.5">
              <a href={`/api/share/publico/${token}/contrato.pdf`} target="_blank" rel="noreferrer"
                 className="flex items-center justify-between text-xs text-slate-600 border border-slate-100 rounded-lg px-3 py-2.5 hover:border-navy-300">
                <span>📜 Contrato firmado</span><span className="text-navy-600 font-bold">PDF →</span>
              </a>
              {(data.otrosies || []).filter(o => (otResuelto[o.id] || o.estado) === 'aprobado').map(o => (
                <a key={o.id} href={`/api/share/publico/${token}/otrosi/${o.id}.pdf`} target="_blank" rel="noreferrer"
                   className="flex items-center justify-between text-xs text-slate-600 border border-slate-100 rounded-lg px-3 py-2.5 hover:border-navy-300">
                  <span>➕ Otrosí N.{o.numero} firmado</span><span className="text-navy-600 font-bold">PDF →</span>
                </a>
              ))}
              {(avances?.cuentas || []).map(c => (
                <a key={c.id} href={`/api/cuentas/publico/${token}/${c.id}.pdf`} target="_blank" rel="noreferrer"
                   className="flex items-center justify-between text-xs text-slate-600 border border-slate-100 rounded-lg px-3 py-2.5 hover:border-navy-300">
                  <span>💵 {c.numero}{c.estado === 'pagada' ? ' · pagada ✓' : ''}</span><span className="text-navy-600 font-bold">PDF →</span>
                </a>
              ))}
              {data.terminado && (
                <a href={`/api/share/publico/${token}/acta.pdf`} target="_blank" rel="noreferrer"
                   className="flex items-center justify-between text-xs text-slate-600 border border-emerald-200 bg-emerald-50/40 rounded-lg px-3 py-2.5">
                  <span>🏁 Acta de Entrega firmada</span><span className="text-emerald-600 font-bold">PDF →</span>
                </a>
              )}
            </div>
          </div>
        )}

        {/* ═══ 📖 LA HISTORIA DE TU OBRA (timeline) ═══ */}
        {aceptado && !data.demo && avances && (
          <div className="bg-white rounded-2xl ring-1 ring-slate-100 p-4 mt-3">
            <button onClick={() => setVerHistoria(v => !v)} className="w-full flex items-center justify-between">
              <p className="text-sm font-semibold text-slate-700">📖 La historia de tu obra</p>
              <span className="text-slate-400 text-xs">{verHistoria ? '▲' : '▼'}</span>
            </button>
            {verHistoria && (() => {
              const eventos = []
              if (firmaInfo) eventos.push({ f: firmaInfo.fecha, icono: '📝', txt: `Firmaste el contrato` })
              ;(avances.avances || []).slice().reverse().forEach(a =>
                eventos.push({ f: a.fecha, icono: '🏗️', txt: `${a.titulo} — obra al ${a.porcentaje}%` }))
              ;(avances.cuentas || []).filter(c => c.estado === 'pagada').forEach(c =>
                eventos.push({ f: c.fecha_pago, icono: '💵', txt: `Pagaste ${c.numero}` }))
              ;(data.otrosies || []).filter(o => o.estado === 'aprobado' && o.resuelto).forEach(o =>
                eventos.push({ f: o.resuelto, icono: '➕', txt: `Aprobaste el Otrosí N.${o.numero}` }))
              if (data.terminado) eventos.push({ f: '', icono: '🏁', txt: '¡Obra entregada a satisfacción!' })
              return (
                <div className="mt-3 space-y-0">
                  {eventos.map((e, i) => (
                    <div key={i} className="flex gap-3">
                      <div className="flex flex-col items-center">
                        <span className="text-base">{e.icono}</span>
                        {i < eventos.length - 1 && <span className="w-px flex-1 bg-slate-100 my-0.5" />}
                      </div>
                      <div className="pb-3">
                        <p className="text-xs text-slate-600">{e.txt}</p>
                        {e.f && <p className="text-[9px] text-slate-300">{e.f}</p>}
                      </div>
                    </div>
                  ))}
                </div>
              )
            })()}
          </div>
        )}

        {/* 💡 Guardar mi obra */}
        {aceptado && !data.demo && hintGuardar && (
          <div className="flex items-center justify-between gap-2 bg-blue-50 border border-blue-100 rounded-xl px-3 py-2.5 mt-3">
            <p className="text-[11px] text-blue-700">
              💡 <strong>Guarda tu obra:</strong> añade esta página a tu pantalla de inicio desde el menú del navegador, o
              <button onClick={() => { navigator.clipboard.writeText(window.location.href); toast.success('Enlace copiado 📋') }}
                      className="font-bold underline ml-1">copia el enlace</button>
            </p>
            <button onClick={() => { localStorage.setItem('obra_guardada_hint', '1'); setHintGuardar(false) }}
                    className="text-blue-300 text-xs shrink-0">✕</button>
          </div>
        )}

        {data.demo && (
          <a href="/registro"
             className="block text-center bg-emerald-500 hover:bg-emerald-400 text-white font-bold text-sm rounded-xl py-3.5 mt-4 transition">
            ¿Quieres enviar presupuestos así? Crea tu cuenta gratis →
          </a>
        )}

        <p className="text-center text-[10px] text-slate-400 mt-4">
          Hecho con PresupuestarCO
        </p>
      </div>

      {/* Modal CONFIRMAR ENTREGA */}
      {showEntrega && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => setShowEntrega(false)}>
          <div className="bg-white rounded-2xl w-full max-w-md p-6 space-y-4" onClick={e => e.stopPropagation()}>
            <div className="text-center">
              <h3 className="font-semibold text-slate-800">Acta de Entrega</h3>
              <p className="text-[11px] text-slate-400 mt-1">
                Confirmas que recibes la obra "{data.proyecto}" a satisfacción.
                Esto habilita el pago final según el contrato.
              </p>
            </div>
            <PadFirma onChange={img => setFirma(f => ({ ...f, firma_imagen: img }))} />
            <input className="w-full border border-slate-200 rounded-xl px-3.5 py-2.5 text-sm outline-none focus:border-emerald-400"
                   placeholder="Tu nombre completo *"
                   value={firma.nombre} onChange={e => setFirma(f => ({ ...f, nombre: e.target.value }))} />
            <input className="w-full border border-slate-200 rounded-xl px-3.5 py-2.5 text-sm outline-none focus:border-emerald-400"
                   placeholder="Cédula (opcional)"
                   value={firma.documento} onChange={e => setFirma(f => ({ ...f, documento: e.target.value }))} />
            <AvisoFirma />
            <div className="flex gap-2 mt-2">
              <button onClick={() => setShowEntrega(false)}
                      className="flex-1 py-2.5 rounded-xl border border-slate-200 text-slate-600 text-sm">Cancelar</button>
              <button onClick={async () => {
                        if (firma.nombre.trim().length < 5) { alert('Escribe tu nombre completo'); return }
                        try {
                          await shareAPI.confirmarEntrega(token, firma)
                          setEntregaConfirmada(true)
                          setShowEntrega(false)
                          window.location.reload()
                        } catch (e) { alert(e.message) }
                      }}
                      className="flex-[2] py-2.5 rounded-xl bg-emerald-500 text-white text-sm font-bold">
                Firmar acta de entrega
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal PENDIENTES */}
      {showPendientes && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => setShowPendientes(false)}>
          <div className="bg-white rounded-2xl w-full max-w-md p-6 space-y-3" onClick={e => e.stopPropagation()}>
            <h3 className="font-semibold text-slate-800">¿Qué falta por terminar?</h3>
            <textarea className="w-full border border-slate-200 rounded-xl px-3.5 py-2.5 text-sm outline-none focus:border-amber-400 min-h-[100px]"
                      placeholder="Describe los pendientes que encontraste..."
                      value={pendientesTxt} onChange={e => setPendientesTxt(e.target.value)} autoFocus />
            <div className="flex gap-2">
              <button onClick={() => setShowPendientes(false)}
                      className="flex-1 py-2.5 rounded-xl border border-slate-200 text-slate-600 text-sm">Cancelar</button>
              <button onClick={async () => {
                        if (pendientesTxt.trim().length < 5) { alert('Describe los pendientes'); return }
                        try {
                          await shareAPI.reportarPendientes(token, pendientesTxt)
                          setShowPendientes(false)
                          alert('Reportado. El contratista continuará la obra.')
                          window.location.reload()
                        } catch (e) { alert(e.message) }
                      }}
                      className="flex-[2] py-2.5 rounded-xl bg-amber-500 text-white text-sm font-bold">
                Enviar al contratista
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de firma / mutual agreement */}
      {showFirma && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-start justify-center p-4 pt-[4vh]" onClick={() => setShowFirma(false)}>
          <div className="bg-white rounded-2xl w-full max-w-md p-6 space-y-4 max-h-[92vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-12 h-12 bg-emerald-100 rounded-2xl mb-2">
                <CheckCircle2 className="w-6 h-6 text-emerald-600" />
              </div>
              <h3 className="font-semibold text-slate-800">Contrato de Ejecución de Obra Civil</h3>
              <p className="text-[10px] text-slate-400">Revisa y firma digitalmente</p>
            </div>

            {/* CONTRATO COMPLETO scrolleable */}
            {contrato ? (
              <div className="border border-slate-200 rounded-xl max-h-64 overflow-y-auto p-3 bg-slate-50">
                <p className="text-xs font-bold text-slate-700 text-center mb-2">
                  {contrato.titulo} — {contrato.numero}
                </p>
                <p className="text-[10px] text-slate-500 leading-relaxed mb-2">{contrato.encabezado}</p>
                {contrato.clausulas.map((cl, i) => (
                  <div key={i} className="mb-2">
                    <p className="text-[10px] font-bold text-slate-600">{cl.titulo}.</p>
                    <p className="text-[10px] text-slate-500 leading-relaxed">{cl.texto}</p>
                    {cl.incluye_tabla && (
                      <div className="mt-1 border border-slate-200 rounded-lg overflow-hidden bg-white">
                        {contrato.tabla.map(r => (
                          <div key={r.item} className="flex justify-between gap-2 px-2 py-1 border-b border-slate-50 text-[9px]">
                            <span className="text-slate-500 truncate">{r.item}. {r.descripcion}</span>
                            <span className="text-slate-600 whitespace-nowrap shrink-0">
                              {r.cantidad} {r.unidad} · {COP(r.subtotal)}
                            </span>
                          </div>
                        ))}
                        <div className="flex justify-between px-2 py-1.5 bg-blue-50 text-[10px] font-bold text-slate-700">
                          <span>TOTAL A PAGAR</span><span>{COP(contrato.total)}</span>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center text-xs text-slate-400 py-6">Cargando contrato...</div>
            )}

            <label className="flex items-start gap-2 text-[11px] text-slate-600 cursor-pointer">
              <input type="checkbox" className="mt-0.5" checked={leido} onChange={e => setLeido(e.target.checked)} />
              <span>He leído el contrato completo y acepto sus cláusulas</span>
            </label>

            {/* Modo de firma */}
            <div className="space-y-3">
              <div className="flex gap-1 bg-slate-100 rounded-xl p-1">
                {[['dibujar', '✍️ Dibujar'], ['subir', '📷 Subir'], ['escribir', '⌨️ Escribir']].map(([m, l]) => (
                  <button key={m} type="button" onClick={() => { setModoFirma(m); setFirma(f => ({ ...f, firma_imagen: '' })) }}
                          className={`flex-1 text-[11px] font-medium py-2 rounded-lg transition ${modoFirma === m ? 'bg-white text-navy-600 shadow-sm' : 'text-slate-500'}`}>
                    {l}
                  </button>
                ))}
              </div>

              {modoFirma === 'dibujar' && (
                <PadFirma onChange={img => setFirma(f => ({ ...f, firma_imagen: img }))} />
              )}
              {modoFirma === 'subir' && (
                <div>
                  {firma.firma_imagen ? (
                    <div className="relative w-fit">
                      <img src={firma.firma_imagen} alt="firma" className="h-20 border border-slate-200 rounded-xl bg-white p-1" />
                      <button onClick={() => setFirma(f => ({ ...f, firma_imagen: '' }))}
                              className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-5 h-5 text-xs">×</button>
                    </div>
                  ) : (
                    <label className="flex items-center justify-center gap-2 border-2 border-dashed border-slate-300 rounded-xl py-6 text-xs text-slate-400 cursor-pointer hover:border-emerald-300">
                      📷 Toca para subir foto de tu firma (máx 400KB)
                      <input type="file" accept="image/*" className="hidden"
                             onChange={e => {
                               const file = e.target.files?.[0]
                               if (!file) return
                               if (file.size > 400 * 1024) { alert('Máximo 400KB'); return }
                               comprimirImagen(file, 800, 0.8).then(img => setFirma(f => ({ ...f, firma_imagen: img }))).catch(() => toast.error('Imagen no valida'))
                             }} />
                    </label>
                  )}
                </div>
              )}

              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Tu nombre completo *</label>
                <input className="w-full border border-slate-200 rounded-xl px-3.5 py-2.5 text-sm outline-none focus:border-emerald-400"
                       placeholder="Ej: María Fernanda López García"
                       value={firma.nombre}
                       onChange={e => setFirma(f => ({ ...f, nombre: e.target.value }))} autoFocus />
              </div>
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Cédula / NIT (opcional)</label>
                <input className="w-full border border-slate-200 rounded-xl px-3.5 py-2.5 text-sm outline-none focus:border-emerald-400"
                       placeholder="1.234.567.890"
                       value={firma.documento}
                       onChange={e => setFirma(f => ({ ...f, documento: e.target.value }))} />
              </div>
            </div>

            <div className="flex gap-2 pt-1">
              <button onClick={() => setShowFirma(false)}
                      className="flex-1 py-2.5 rounded-xl border border-slate-200 text-slate-600 text-sm font-medium">
                Cancelar
              </button>
              <AvisoFirma />
              <button onClick={confirmarFirma} disabled={aceptando || !leido}
                      className="flex-[2] py-2.5 rounded-xl bg-emerald-500 text-white text-sm font-bold disabled:opacity-40">
                {aceptando ? 'Firmando...' : 'Firmar contrato'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Barra de accion fija */}
      {!aceptado && !rechazado && (
        <div className="fixed bottom-0 left-0 right-0 bg-white/90 backdrop-blur-md border-t border-slate-200/80 p-4 shadow-[0_-8px_30px_-12px_rgba(15,42,74,0.15)]">
          <div className="max-w-lg mx-auto space-y-2">
          <div className="flex gap-2">
            {c.telefono && (
              <a href={`https://wa.me/57${c.telefono.replace(/\D/g, '')}`}
                 className="flex items-center justify-center gap-2 flex-1 py-3 rounded-xl border border-slate-200 text-sm font-medium text-slate-600">
                <Phone className="w-4 h-4" /> Preguntar
              </a>
            )}
            <button onClick={aceptar} disabled={aceptando}
                    className="flex items-center justify-center gap-2 flex-[2] py-3.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 active:scale-[0.99] text-white text-sm font-bold shadow-lg shadow-emerald-500/30 transition disabled:opacity-50">
              <CheckCircle2 className="w-4 h-4" />
              {aceptando ? 'Confirmando...' : 'Aceptar presupuesto'}
            </button>
          </div>
          <button onClick={rechazar} className="w-full text-center text-[11px] text-slate-400 py-1">
            No me interesa este presupuesto
          </button>
          </div>
        </div>
      )}
      {/* Pie legal: la plataforma es herramienta neutral */}
      <div className="max-w-lg mx-auto px-4 mt-8 pb-4 text-center">
        <p className="text-[9px] text-slate-300 leading-relaxed">
          Enlace seguro provisto por <strong className="text-slate-400">PresupuestarCO</strong> — plataforma
          neutral de gestión documental. El contrato es entre el contratista y su cliente.{' '}
          <a href="/legal" target="_blank" rel="noreferrer" className="underline">Términos y datos</a>
        </p>
      </div>

      {/* Galeria a pantalla completa */}
      {galeria && <Lightbox fotos={galeria.fotos} inicial={galeria.inicial} onCerrar={() => setGaleria(null)} />}

      {/* Modal: firma del OTROSI */}
      {otrosiFirmando && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4"
             onClick={() => setOtrosiFirmando(null)}>
          <div className="bg-white w-full sm:max-w-md sm:rounded-2xl rounded-t-2xl p-5" onClick={e => e.stopPropagation()}>
            <h3 className="font-bold text-slate-800 mb-1">✍️ Aprobar Otrosí N.{otrosiFirmando.numero}</h3>
            <p className="text-[11px] text-slate-400 mb-3">
              Adicional por <strong>{COP(otrosiFirmando.total)}</strong> — se suma al contrato que ya firmaste.
              Tu firma genera el Otrosí en PDF con validez legal (Ley 527 de 1999).
            </p>
            <input className="input mb-2" placeholder="Tu nombre completo *" value={firma.nombre}
                   onChange={e => setFirma(f => ({ ...f, nombre: e.target.value }))} />
            <input className="input mb-2" placeholder="Cédula (opcional)" value={firma.documento}
                   onChange={e => setFirma(f => ({ ...f, documento: e.target.value }))} />
            <p className="text-[10px] text-slate-400 mb-1">Firma aquí con tu dedo:</p>
            <PadFirma onChange={img => setFirma(f => ({ ...f, firma_imagen: img }))} />
            <AvisoFirma />
            <button onClick={async () => {
                      if (!firma.nombre.trim()) { toast.error('Tu nombre es requerido'); return }
                      try {
                        await shareAPI.otrosiAprobar(token, otrosiFirmando.id, firma)
                        setOtResuelto(m => ({ ...m, [otrosiFirmando.id]: 'aprobado' }))
                        setOtrosiFirmando(null)
                        toast.success('¡Adicional aprobado y firmado! 🎉', { duration: 5000 })
                      } catch (e) { toast.error(e.message) }
                    }}
                    className="w-full mt-3 py-3 rounded-xl bg-emerald-500 text-white font-bold text-sm">
              Aprobar adicional por {COP(otrosiFirmando.total)}
            </button>
            <button onClick={() => setOtrosiFirmando(null)}
                    className="w-full mt-2 py-2 text-xs text-slate-400">Cancelar</button>
          </div>
        </div>
      )}
    </div>
  )
}
