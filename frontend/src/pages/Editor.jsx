import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { ArrowLeft, Search, Plus, Trash2, Share2, FileSpreadsheet, FileText,
         Eye, CheckCircle2, X, MessageCircle, Copy as CopyIcon, Pencil, Calculator, Camera, Upload, HardHat } from 'lucide-react'
import { proyectosAPI, preciosAPI, shareAPI, exportarAPI, avancesAPI, gastosAPI, cuentasAPI } from '../services/api'

const COP = (v) => '$' + Math.round(v || 0).toLocaleString('es-CO')

export default function Editor() {
  const { id } = useParams()
  const nav = useNavigate()
  const [p, setP] = useState(null)
  const [items, setItems] = useState([])
  const [aiu, setAiu] = useState({ admin: 15, imprevistos: 5, utilidad: 8, aplicar: true, iva_sobre_utilidad: true })
  const [contrato, setContrato] = useState({ plazo_dias: 45, anticipo_pct: 50, fecha_inicio: '', lugar: '' })
  const [totales, setTotales] = useState(null)
  const [guardando, setGuardando] = useState(false)

  // Buscador
  const [q, setQ] = useState('')
  const [categoria, setCategoria] = useState('')
  const [resultados, setResultados] = useState([])
  const [categorias, setCategorias] = useState([])
  const [buscando, setBuscando] = useState(false)
  const [showBuscador, setShowBuscador] = useState(false)

  // Calculadora de cantidades + Preview
  const [calcAbierta, setCalcAbierta] = useState(null)  // idx del item con calc abierta
  const [showPreview, setShowPreview] = useState(false)

  // Avances de obra (cuando el presupuesto esta aceptado)
  const [showAvances, setShowAvances] = useState(false)
  const [avances, setAvances] = useState([])
  const [nuevoAvance, setNuevoAvance] = useState({ titulo: '', descripcion: '', fotos: [] })
  const [avanceItems, setAvanceItems] = useState({})  // {itemId: pct}
  const [valorTotalDirecto, setValorTotalDirecto] = useState(0)
  const [subiendoAvance, setSubiendoAvance] = useState(false)
  const [calificacion, setCalificacion] = useState(null)
  const [showGastos, setShowGastos] = useState(false)
  const [gastosData, setGastosData] = useState(null)
  const [nuevoGasto, setNuevoGasto] = useState({ categoria: 'materiales', descripcion: '', valor: '', foto: '' })
  const [showCobros, setShowCobros] = useState(false)
  const [cobrosData, setCobrosData] = useState(null)
  const [liquidacion, setLiquidacion] = useState(null)  // preview antes de crear

  // Share
  const [showShare, setShowShare] = useState(false)
  const [shareData, setShareData] = useState(null)
  const [eventos, setEventos] = useState(null)

  const timerGuardar = useRef(null)
  const timerBuscar = useRef(null)

  // ── Cargar proyecto ──────────────────────────────────────────────────
  useEffect(() => {
    proyectosAPI.obtener(id).then(data => {
      setP(data)
      setItems(data.items || [])
      setAiu(data.aiu || aiu)
      if (data.contrato && Object.keys(data.contrato).length) setContrato(c => ({ ...c, ...data.contrato }))
      setTotales(data.totales)
      if (data.share_token) shareAPI.eventos(id).then(setEventos).catch(() => {})
      if (data.estado === 'terminado') shareAPI.verEncuesta(id).then(setCalificacion).catch(() => {})
    }).catch(e => { toast.error(e.message); nav('/') })
  }, [id])

  // ── Calculo local instantaneo (mismo algoritmo que el backend) ────────
  const calcularLocal = useCallback((itemsAct, aiuAct) => {
    let sub = 0
    itemsAct.forEach(it => { sub += (parseFloat(it.cantidad) || 0) * (parseFloat(it.precio_unitario) || 0) })
    sub = Math.round(sub)
    const a = aiuAct.aplicar ? Math.round(sub * (aiuAct.admin || 0) / 100) : 0
    const i = aiuAct.aplicar ? Math.round(sub * (aiuAct.imprevistos || 0) / 100) : 0
    const u = aiuAct.aplicar ? Math.round(sub * (aiuAct.utilidad || 0) / 100) : 0
    const base = sub + a + i + u
    const iva = aiuAct.aplicar
      ? (aiuAct.iva_sobre_utilidad ? Math.round(u * 0.19) : Math.round(base * 0.19))
      : 0
    return {
      subtotal_directo: sub, admin_valor: a, imprevistos_valor: i, utilidad_valor: u,
      aiu_total: a + i + u, base_con_aiu: base, iva, total: base + iva, num_items: itemsAct.length,
      regimen_iva: aiuAct.iva_sobre_utilidad ? 'IVA 19% solo sobre utilidad (Art. 462-1 ET)' : 'IVA 19% sobre base + AIU',
    }
  }, [])

  // ── Autoguardado con debounce ─────────────────────────────────────────
  const guardar = useCallback((itemsAct, aiuAct) => {
    setTotales(calcularLocal(itemsAct, aiuAct))
    clearTimeout(timerGuardar.current)
    timerGuardar.current = setTimeout(async () => {
      setGuardando(true)
      try {
        const data = await proyectosAPI.actualizar(id, { items: itemsAct, aiu: aiuAct })
        setTotales(data.totales) // el backend es la fuente de verdad
      } catch (e) { toast.error('Error guardando: ' + e.message) }
      finally { setGuardando(false) }
    }, 800)
  }, [id, calcularLocal])

  const setItemsYGuardar = (fn) => {
    setItems(prev => {
      const next = typeof fn === 'function' ? fn(prev) : fn
      guardar(next, aiu)
      return next
    })
  }

  const timerContrato = useRef(null)
  const setContratoYGuardar = (nuevo) => {
    setContrato(nuevo)
    clearTimeout(timerContrato.current)
    timerContrato.current = setTimeout(() => {
      proyectosAPI.actualizar(id, { contrato: nuevo }).catch(e => toast.error(e.message))
    }, 800)
  }

  const avisarCliente = (mensaje) => {
    const link = `${window.location.origin}/p/${p.share_token}`
    const tel = (p.cliente_telefono || '').replace(/\D/g, '')
    const base = tel ? `https://wa.me/${tel.startsWith('57') ? tel : '57' + tel}` : 'https://wa.me/'
    window.open(`${base}?text=${encodeURIComponent(mensaje + '\n\n' + link)}`, '_blank')
  }

  const setAiuYGuardar = (nuevo) => {
    setAiu(nuevo)
    guardar(items, nuevo)
  }

  // ── Buscador de actividades ───────────────────────────────────────────
  useEffect(() => {
    if (!showBuscador) return
    clearTimeout(timerBuscar.current)
    timerBuscar.current = setTimeout(async () => {
      setBuscando(true)
      try {
        const res = await preciosAPI.buscar({ q: q || undefined, categoria: categoria || undefined, region: p?.region || 'bogota', limit: 40 })
        setResultados(res.items || [])
        if (!categorias.length && res.categorias) setCategorias(res.categorias)
      } catch (e) { /* silencioso */ }
      finally { setBuscando(false) }
    }, 300)
  }, [q, categoria, showBuscador, p?.region])

  const agregarItem = (apu) => {
    const nuevo = {
      id: `${apu.codigo}-${Date.now()}`,
      codigo: apu.codigo,
      capitulo: apu.categoria,
      descripcion: apu.descripcion,
      unidad: apu.unidad,
      cantidad: 1,
      precio_unitario: apu.precio,
      precio_editado: false,
    }
    setItemsYGuardar(prev => [...prev, nuevo])
    toast.success('Agregado', { duration: 1200 })
  }

  // Detectar que formula aplica segun la unidad del item
  const tipoCalc = (unidad) => {
    const u = (unidad || '').toLowerCase().replace('³','3').replace('²','2')
    if (u.includes('m3') || u.includes('dm3')) return 'volumen'
    if (u.includes('m2')) return 'area'
    if (u === 'm' || u === 'ml') return 'lineal'
    return null
  }

  // Actualizar calculadora: recalcula y auto-rellena la cantidad
  const actualizarCalc = (idx, campo, valor) => {
    setItemsYGuardar(prev => prev.map((it, i) => {
      if (i !== idx) return it
      const calc = { ...(it.calc || {}), [campo]: valor }
      const n = parseFloat(calc.n) || 1
      const largo = parseFloat(calc.largo) || 0
      const ancho = parseFloat(calc.ancho) || 0
      const alto = parseFloat(calc.alto) || 0
      const tipo = tipoCalc(it.unidad)
      let cantidad = it.cantidad
      if (tipo === 'volumen' && largo > 0 && ancho > 0 && alto > 0) {
        cantidad = Math.round(n * largo * ancho * alto * 1000) / 1000
      } else if (tipo === 'area' && largo > 0 && ancho > 0) {
        cantidad = Math.round(n * largo * ancho * 1000) / 1000
      } else if (tipo === 'lineal' && largo > 0) {
        cantidad = Math.round(n * largo * 100) / 100
      }
      return { ...it, calc, cantidad }
    }))
  }

  const actualizarItem = (idx, campo, valor) => {
    setItemsYGuardar(prev => prev.map((it, i) => {
      if (i !== idx) return it
      const next = { ...it, [campo]: valor }
      if (campo === 'precio_unitario') next.precio_editado = true
      return next
    }))
  }

  const eliminarItem = (idx) => {
    setItemsYGuardar(prev => prev.filter((_, i) => i !== idx))
  }

  // ── Compartir por WhatsApp ────────────────────────────────────────────
  const compartir = async () => {
    if (!items.length) { toast.error('Agrega ítems antes de compartir'); return }
    try {
      const data = await shareAPI.compartir(id)
      setShareData(data)
      setShowShare(true)
      shareAPI.eventos(id).then(setEventos).catch(() => {})
    } catch (e) { toast.error(e.message) }
  }

  const urlPublica = shareData ? `${window.location.origin}${shareData.ruta_publica}` : ''
  const abrirWhatsApp = () => {
    const texto = encodeURIComponent(`${shareData.mensaje_whatsapp} ${urlPublica}`)
    const base = shareData.telefono_cliente ? shareData.whatsapp_url_base : 'https://wa.me/'
    window.open(`${base}?text=${texto}`, '_blank')
  }

  const copiarLink = () => {
    navigator.clipboard.writeText(urlPublica)
    toast.success('Enlace copiado')
  }

  // ── Exportar ──────────────────────────────────────────────────────────
  const exportar = async (tipo) => {
    try {
      toast.loading('Generando ' + tipo.toUpperCase() + '...', { id: 'exp' })
      const payload = { proyecto_id: parseInt(id) }
      const res = tipo === 'excel' ? await exportarAPI.excel(payload) : await exportarAPI.pdf(payload)
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url
      a.download = `${p.nombre.replace(/[^a-z0-9]/gi, '_')}.${tipo === 'excel' ? 'xlsx' : 'pdf'}`
      a.click()
      URL.revokeObjectURL(url)
      toast.success('Descargado', { id: 'exp' })
    } catch (e) { toast.error('Error exportando: ' + e.message, { id: 'exp' }) }
  }

  if (!p) return <div className="min-h-screen bg-slate-50 flex items-center justify-center text-slate-400">Cargando...</div>

  // Agrupar items por capitulo
  const grupos = {}
  items.forEach((it, idx) => {
    const cap = it.capitulo || 'OTROS'
    if (!grupos[cap]) grupos[cap] = []
    grupos[cap].push({ ...it, _idx: idx })
  })

  return (
    <div className="min-h-screen bg-slate-50 pb-32">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <button onClick={() => nav('/')} className="p-2 hover:bg-slate-100 rounded-lg shrink-0">
              <ArrowLeft className="w-4 h-4 text-slate-600" />
            </button>
            <div className="min-w-0">
              <h1 className="font-semibold text-slate-800 truncate">{p.nombre}</h1>
              <p className="text-xs text-slate-400">
                <span className="font-semibold text-navy-600">{p.numero}</span>
                {' · '}{p.cliente_nombre || 'Sin cliente'}
                {' · '}{p.actualizado ? new Date(p.actualizado).toLocaleDateString('es-CO') : ''}
                {' · '}{guardando ? 'Guardando...' : 'Guardado ✓'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {eventos?.total_vistas > 0 && (
              <span className="hidden sm:flex items-center gap-1 text-xs text-blue-600 bg-blue-50 px-2.5 py-1.5 rounded-full font-medium">
                <Eye className="w-3 h-3" /> {eventos.total_vistas} vista{eventos.total_vistas !== 1 ? 's' : ''}
              </span>
            )}
            {eventos?.aceptado && (
              <span className="flex items-center gap-1 text-xs text-emerald-700 bg-emerald-50 px-2.5 py-1.5 rounded-full font-medium">
                <CheckCircle2 className="w-3 h-3" /> Aceptado
              </span>
            )}
            <button onClick={() => exportar('excel')} className="p-2 hover:bg-slate-100 rounded-lg" title="Excel">
              <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
            </button>
            <button onClick={() => exportar('pdf')} className="p-2 hover:bg-slate-100 rounded-lg" title="PDF">
              <FileText className="w-4 h-4 text-red-500" />
            </button>
            {p.estado === 'terminado' && calificacion?.respondida && (
              <span className="flex items-center gap-1 text-xs text-amber-600 bg-amber-50 px-2.5 py-1.5 rounded-full font-medium"
                    title={calificacion.comentario || ''}>
                ⭐ {calificacion.estrellas}/5
              </span>
            )}
            {p.estado === 'aceptado' && (
              <button onClick={async () => {
                        if (!confirm('¿Solicitar la entrega de la obra?\n\n• Tu cliente verá en su enlace: "El contratista reporta la obra terminada"\n• Al confirmar, firmará el Acta de Entrega\n• Si encuentra pendientes, te los reporta y la obra continúa')) return
                        try {
                          const d = await proyectosAPI.actualizar(id, { estado: 'entrega_solicitada' })
                          setP(d)
                          toast.success('Entrega solicitada — avísale a tu cliente')
                          avisarCliente(`Hola! La obra "${p.nombre}" está terminada 🏁 Por favor confirma el recibido a satisfacción aquí:`)
                        } catch (e2) { toast.error(e2.message) }
                      }}
                      className="flex items-center gap-1.5 border border-slate-300 text-slate-600 text-sm font-medium px-3 py-2 rounded-xl transition hover:bg-slate-50"
                      title="Solicitar acta de entrega al cliente">
                🤝 <span className="hidden sm:inline">Solicitar entrega</span>
              </button>
            )}
            {p.estado === 'entrega_solicitada' && (
              <span className="text-xs bg-violet-100 text-violet-700 px-2.5 py-1.5 rounded-full font-medium">
                🤝 Esperando confirmación del cliente
              </span>
            )}
            {p.estado === 'terminado' && p.share_token && (
              <a href={`/api/share/publico/${p.share_token}/acta.pdf`} target="_blank" rel="noreferrer"
                 className="text-[11px] font-medium text-navy-600 border border-navy-200 rounded-lg px-2.5 py-1.5">
                📄 Acta de Entrega
              </a>
            )}
            {['aceptado', 'entrega_solicitada', 'terminado'].includes(p.estado) && (
              <button onClick={() => {
                        setShowGastos(true)
                        gastosAPI.listar(id).then(setGastosData).catch(e => toast.error(e.message))
                      }}
                      className="flex items-center gap-1.5 border border-slate-300 text-slate-600 text-sm font-medium px-3 py-2 rounded-xl transition hover:bg-slate-50"
                      title="Gastos reales vs presupuesto">
                💸 <span className="hidden sm:inline">Gastos</span>
              </button>
            )}
            {['aceptado', 'entrega_solicitada', 'terminado'].includes(p.estado) && (
              <button onClick={() => {
                        setShowCobros(true)
                        setLiquidacion(null)
                        cuentasAPI.listar(id).then(setCobrosData).catch(e => toast.error(e.message))
                        avancesAPI.listar(id).then(res => setAvances(res.avances || [])).catch(() => {})
                      }}
                      className="flex items-center gap-1.5 border border-emerald-300 bg-emerald-50 text-emerald-700 text-sm font-medium px-3 py-2 rounded-xl transition"
                      title="Cuentas de cobro">
                💵 <span className="hidden sm:inline">Cobros</span>
              </button>
            )}
            {p.estado === 'aceptado' && (
              <button onClick={() => {
                        setShowAvances(true)
                        avancesAPI.listar(id).then(res => {
                          setAvances(res.avances || [])
                          setValorTotalDirecto(res.valor_total_directo || 0)
                          // Prefill: continuar desde el ultimo avance publicado
                          const ultimo = (res.avances || [])[0]
                          const map = {}
                          if (ultimo?.items) ultimo.items.forEach(it => { map[it.id] = it.pct })
                          setAvanceItems(map)
                        }).catch(() => {})
                      }}
                      className="flex items-center gap-1.5 border border-amber-300 bg-amber-50 text-amber-700 text-sm font-medium px-3 py-2 rounded-xl transition"
                      title="Avances de obra">
                <HardHat className="w-4 h-4" /> <span className="hidden sm:inline">Avances</span>
              </button>
            )}
            <button onClick={() => setShowPreview(true)}
                    className="flex items-center gap-1.5 border border-slate-200 hover:border-navy-300 text-slate-600 text-sm font-medium px-3 py-2 rounded-xl transition"
                    title="Ver como lo verá tu cliente">
              <Eye className="w-4 h-4" /> <span className="hidden sm:inline">Ver</span>
            </button>
            <button onClick={compartir}
                    className="flex items-center gap-1.5 bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-medium px-4 py-2 rounded-xl transition">
              <MessageCircle className="w-4 h-4" /> <span className="hidden sm:inline">WhatsApp</span>
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-5">
        {/* Boton agregar actividades */}
        <button onClick={() => setShowBuscador(true)}
                className="w-full flex items-center gap-3 bg-white border-2 border-dashed border-slate-300 hover:border-navy-400 rounded-xl p-4 text-slate-500 hover:text-navy-600 transition mb-5">
          <Search className="w-5 h-5" />
          <span className="font-medium">Buscar actividades en la base APU 2026...</span>
        </button>

        {/* Items agrupados por capitulo */}
        {Object.keys(grupos).length === 0 ? (
          <div className="text-center py-12 text-slate-400 text-sm">
            El presupuesto está vacío. Busca actividades para empezar.
          </div>
        ) : (
          Object.entries(grupos).map(([cap, itemsCap]) => (
            <div key={cap} className="mb-5">
              <div className="flex items-center justify-between mb-2 px-1">
                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wide">{cap}</h3>
                <span className="text-xs text-slate-400">
                  {COP(itemsCap.reduce((s, it) => s + (parseFloat(it.cantidad) || 0) * (parseFloat(it.precio_unitario) || 0), 0))}
                </span>
              </div>
              <div className="bg-white rounded-xl border border-slate-200 divide-y divide-slate-100">
                {itemsCap.map(it => (
                  <div key={it._idx}>
                  <div className="p-3 flex items-center gap-3">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-700 leading-snug">{it.descripcion}</p>
                      <div className="flex items-center gap-2">
                        {it.precio_editado && <span className="text-[10px] text-amber-600 font-medium">precio ajustado</span>}
                        {it.calc && (it.calc.largo || it.calc.n) && (
                          <span className="text-[10px] text-blue-500 font-medium">
                            calc: {it.calc.n || 1} × {it.calc.largo || '?'}{tipoCalc(it.unidad) !== 'lineal' ? ` × ${it.calc.ancho || '?'}` : ''}{tipoCalc(it.unidad) === 'volumen' ? ` × ${it.calc.alto || '?'}` : ''}m
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      {tipoCalc(it.unidad) && (
                        <button onClick={() => setCalcAbierta(calcAbierta === it._idx ? null : it._idx)}
                                className={`p-1.5 rounded-lg transition ${calcAbierta === it._idx ? 'bg-blue-100 text-blue-600' : 'hover:bg-slate-100 text-slate-300 hover:text-blue-500'}`}
                                title="Calcular cantidad por dimensiones">
                          <Calculator className="w-4 h-4" />
                        </button>
                      )}
                      <div className="text-right">
                        <input type="number" step="any" min="0" value={it.cantidad}
                               onChange={e => actualizarItem(it._idx, 'cantidad', e.target.value)}
                               className="w-20 text-right text-sm border border-slate-200 rounded-lg px-2 py-1.5 focus:border-navy-400 outline-none" />
                        <p className="text-[10px] text-slate-400 mt-0.5 text-center">{it.unidad}</p>
                      </div>
                      <span className="text-slate-300">×</span>
                      <div className="text-right">
                        <input type="number" step="any" min="0" value={it.precio_unitario}
                               onChange={e => actualizarItem(it._idx, 'precio_unitario', e.target.value)}
                               className="w-28 text-right text-sm border border-slate-200 rounded-lg px-2 py-1.5 focus:border-navy-400 outline-none" />
                        <p className="text-[10px] text-slate-400 mt-0.5 text-center">precio unit.</p>
                      </div>
                      <div className="w-28 text-right font-semibold text-sm text-slate-800">
                        {COP((parseFloat(it.cantidad) || 0) * (parseFloat(it.precio_unitario) || 0))}
                      </div>
                      <button onClick={() => eliminarItem(it._idx)} className="p-1.5 hover:bg-red-50 rounded-lg">
                        <Trash2 className="w-3.5 h-3.5 text-slate-300 hover:text-red-500" />
                      </button>
                    </div>
                  </div>

                  {/* Calculadora de cantidades */}
                  {calcAbierta === it._idx && tipoCalc(it.unidad) && (
                    <div className="px-3 pb-3 bg-blue-50/50">
                      <div className="flex items-end gap-2 flex-wrap pt-2">
                        <div>
                          <label className="text-[10px] text-blue-600 font-medium block mb-0.5"># Elementos</label>
                          <input type="number" step="1" min="1" placeholder="1"
                                 value={it.calc?.n ?? ''}
                                 onChange={e => actualizarCalc(it._idx, 'n', e.target.value)}
                                 className="w-20 text-sm border border-blue-200 rounded-lg px-2 py-1.5 bg-white outline-none focus:border-blue-400" />
                        </div>
                        <span className="text-blue-300 pb-2">×</span>
                        <div>
                          <label className="text-[10px] text-blue-600 font-medium block mb-0.5">Largo (m)</label>
                          <input type="number" step="any" min="0" placeholder="0.00"
                                 value={it.calc?.largo ?? ''}
                                 onChange={e => actualizarCalc(it._idx, 'largo', e.target.value)}
                                 className="w-24 text-sm border border-blue-200 rounded-lg px-2 py-1.5 bg-white outline-none focus:border-blue-400" />
                        </div>
                        {tipoCalc(it.unidad) !== 'lineal' && (
                          <>
                            <span className="text-blue-300 pb-2">×</span>
                            <div>
                              <label className="text-[10px] text-blue-600 font-medium block mb-0.5">{tipoCalc(it.unidad) === 'area' ? 'Ancho/Alto (m)' : 'Ancho (m)'}</label>
                              <input type="number" step="any" min="0" placeholder="0.00"
                                     value={it.calc?.ancho ?? ''}
                                     onChange={e => actualizarCalc(it._idx, 'ancho', e.target.value)}
                                     className="w-24 text-sm border border-blue-200 rounded-lg px-2 py-1.5 bg-white outline-none focus:border-blue-400" />
                            </div>
                          </>
                        )}
                        {tipoCalc(it.unidad) === 'volumen' && (
                          <>
                            <span className="text-blue-300 pb-2">×</span>
                            <div>
                              <label className="text-[10px] text-blue-600 font-medium block mb-0.5">Alto (m)</label>
                              <input type="number" step="any" min="0" placeholder="0.00"
                                     value={it.calc?.alto ?? ''}
                                     onChange={e => actualizarCalc(it._idx, 'alto', e.target.value)}
                                     className="w-24 text-sm border border-blue-200 rounded-lg px-2 py-1.5 bg-white outline-none focus:border-blue-400" />
                            </div>
                          </>
                        )}
                        <div className="pb-1 pl-2 text-sm text-blue-700">
                          = <strong>{it.cantidad}</strong> {it.unidad}
                        </div>
                      </div>
                      <p className="text-[10px] text-blue-400 mt-1.5">
                        {tipoCalc(it.unidad) === 'volumen' && 'Volumen: # elementos × largo × ancho × alto — la cantidad se llena sola'}
                        {tipoCalc(it.unidad) === 'area' && 'Área: # elementos × largo × ancho — la cantidad se llena sola'}
                        {tipoCalc(it.unidad) === 'lineal' && 'Lineal: # elementos × largo — la cantidad se llena sola'}
                      </p>
                    </div>
                  )}
                  </div>
                ))}
              </div>
            </div>
          ))
        )}

        {/* Panel AIU */}
        {items.length > 0 && (
          <div className="bg-white rounded-xl border border-slate-200 p-4 mb-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-slate-700">AIU e IVA</h3>
              <label className="flex items-center gap-2 text-xs text-slate-500">
                <input type="checkbox" checked={aiu.aplicar}
                       onChange={e => setAiuYGuardar({ ...aiu, aplicar: e.target.checked })} />
                Aplicar AIU
              </label>
            </div>
            {aiu.aplicar && (
              <>
                <div className="grid grid-cols-3 gap-3 mb-3">
                  {[['admin', 'Administración'], ['imprevistos', 'Imprevistos'], ['utilidad', 'Utilidad']].map(([k, lbl]) => (
                    <div key={k}>
                      <label className="text-[11px] text-slate-400 block mb-1">{lbl} %</label>
                      <input type="number" step="0.5" min="0" max="50" value={aiu[k]}
                             onChange={e => setAiuYGuardar({ ...aiu, [k]: parseFloat(e.target.value) || 0 })}
                             className="w-full text-sm border border-slate-200 rounded-lg px-2.5 py-2 focus:border-navy-400 outline-none" />
                    </div>
                  ))}
                </div>
                <label className="flex items-start gap-2 text-xs text-slate-500 bg-blue-50 rounded-lg p-2.5">
                  <input type="checkbox" className="mt-0.5" checked={aiu.iva_sobre_utilidad}
                         onChange={e => setAiuYGuardar({ ...aiu, iva_sobre_utilidad: e.target.checked })} />
                  <span>
                    <strong className="text-blue-700">IVA solo sobre la utilidad</strong> (Art. 462-1 ET — contratos de construcción).
                    Desmárcalo solo si tu contrato es de otro tipo.
                  </span>
                </label>
              </>
            )}
          </div>
        )}

        {/* Condiciones del contrato */}
        {items.length > 0 && (
          <div className="bg-white rounded-xl border border-slate-200 p-4 mb-5">
            <div className="flex items-center justify-between mb-1">
              <h3 className="text-sm font-semibold text-slate-700">Contrato de obra</h3>
              {p.estado === 'aceptado' && p.share_token && (
                <a href={`/api/share/publico/${p.share_token}/contrato.pdf`} target="_blank" rel="noreferrer"
                   className="text-[11px] font-medium text-navy-600 border border-navy-200 rounded-lg px-2.5 py-1">
                  📄 Contrato firmado (PDF)
                </a>
              )}
            </div>
            <p className="text-[11px] text-slate-400 mb-3">
              Al aceptar, tu cliente firma un Contrato de Ejecución de Obra Civil generado con estas condiciones.
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div>
                <label className="text-[10px] text-slate-400 block mb-1">Plazo (días hábiles)</label>
                <input type="number" min="1" max="720" className="input !py-2 text-sm"
                       value={contrato.plazo_dias}
                       onChange={e => setContratoYGuardar({ ...contrato, plazo_dias: parseInt(e.target.value) || 45 })} />
              </div>
              <div>
                <label className="text-[10px] text-slate-400 block mb-1">Anticipo %</label>
                <input type="number" min="0" max="90" step="5" className="input !py-2 text-sm"
                       value={contrato.anticipo_pct}
                       onChange={e => setContratoYGuardar({ ...contrato, anticipo_pct: parseFloat(e.target.value) || 0 })} />
              </div>
              <div>
                <label className="text-[10px] text-slate-400 block mb-1">Fecha de inicio</label>
                <input type="text" placeholder="15 de agosto de 2026" className="input !py-2 text-sm"
                       value={contrato.fecha_inicio}
                       onChange={e => setContratoYGuardar({ ...contrato, fecha_inicio: e.target.value })} />
              </div>
              <div>
                <label className="text-[10px] text-slate-400 block mb-1">Lugar / Municipio</label>
                <input type="text" placeholder="Coveñas, Sucre" className="input !py-2 text-sm"
                       value={contrato.lugar}
                       onChange={e => setContratoYGuardar({ ...contrato, lugar: e.target.value })} />
              </div>
            </div>
            {totales && contrato.anticipo_pct > 0 && (
              <p className="text-[11px] text-slate-500 mt-2.5 bg-slate-50 rounded-lg p-2">
                Forma de pago: anticipo {contrato.anticipo_pct}% = <strong>{COP(totales.total * contrato.anticipo_pct / 100)}</strong>
                {' · '}saldo {100 - contrato.anticipo_pct}% = <strong>{COP(totales.total * (100 - contrato.anticipo_pct) / 100)}</strong>
              </p>
            )}
          </div>
        )}
      </main>

      {/* Barra de totales fija */}
      {totales && items.length > 0 && (
        <div className="fixed bottom-0 left-0 right-0 bg-navy-800 text-white z-40">
          <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between gap-4">
            <div className="flex gap-4 text-xs text-blue-200 overflow-x-auto">
              <span className="whitespace-nowrap">Directo: <strong className="text-white">{COP(totales.subtotal_directo)}</strong></span>
              {aiu.aplicar && <span className="whitespace-nowrap">AIU: <strong className="text-white">{COP(totales.aiu_total)}</strong></span>}
              <span className="whitespace-nowrap">IVA: <strong className="text-white">{COP(totales.iva)}</strong></span>
            </div>
            <div className="text-right shrink-0">
              <p className="text-[10px] text-blue-200 uppercase tracking-wide">Total</p>
              <p className="text-xl font-black">{COP(totales.total)}</p>
            </div>
          </div>
        </div>
      )}

      {/* Modal buscador */}
      {showBuscador && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-start justify-center p-4 pt-[8vh]" onClick={() => setShowBuscador(false)}>
          <div className="bg-white rounded-2xl w-full max-w-2xl max-h-[80vh] flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="p-4 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Search className="w-4 h-4 text-slate-400 shrink-0" />
                <input autoFocus className="flex-1 outline-none text-sm" placeholder="Buscar: pañete, mampostería, pintura, cerámica..."
                       value={q} onChange={e => setQ(e.target.value)} />
                <button onClick={() => setShowBuscador(false)} className="p-1 hover:bg-slate-100 rounded-lg">
                  <X className="w-4 h-4 text-slate-400" />
                </button>
              </div>
              <div className="flex gap-1.5 mt-3 overflow-x-auto pb-1">
                <button onClick={() => setCategoria('')}
                        className={`text-xs px-3 py-1.5 rounded-full whitespace-nowrap transition ${!categoria ? 'bg-navy-600 text-white' : 'bg-slate-100 text-slate-600'}`}>
                  Todas
                </button>
                {categorias.slice(0, 12).map(c => (
                  <button key={c} onClick={() => setCategoria(c === categoria ? '' : c)}
                          className={`text-xs px-3 py-1.5 rounded-full whitespace-nowrap transition ${categoria === c ? 'bg-navy-600 text-white' : 'bg-slate-100 text-slate-600'}`}>
                    {c.charAt(0) + c.slice(1).toLowerCase()}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-2">
              {buscando ? (
                <p className="text-center py-8 text-sm text-slate-400">Buscando...</p>
              ) : resultados.length === 0 ? (
                <p className="text-center py-8 text-sm text-slate-400">
                  {q ? 'Sin resultados — prueba otra palabra' : 'Escribe para buscar en 2,288 actividades'}
                </p>
              ) : (
                resultados.map(apu => (
                  <button key={apu.codigo} onClick={() => agregarItem(apu)}
                          className="w-full flex items-center gap-3 p-3 hover:bg-slate-50 rounded-xl text-left transition group">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-700 leading-snug">{apu.descripcion}</p>
                      <p className="text-[11px] text-slate-400 mt-0.5">{apu.categoria} · {apu.codigo}</p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="text-sm font-semibold text-slate-800">{COP(apu.precio)}</p>
                      <p className="text-[10px] text-slate-400">/{apu.unidad}</p>
                    </div>
                    <Plus className="w-4 h-4 text-slate-300 group-hover:text-navy-600 shrink-0" />
                  </button>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modal COBROS */}
      {showCobros && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50" onClick={() => setShowCobros(false)}>
          <div className="bg-white rounded-2xl p-5 w-full max-w-lg max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-slate-800">💵 Cuentas de cobro</h3>
              <button onClick={() => setShowCobros(false)} className="text-slate-400 text-lg">×</button>
            </div>

            {/* Resumen de caja del proyecto */}
            {cobrosData && totales && (
              <div className="bg-slate-50 rounded-xl p-3.5 mb-4">
                <div className="flex justify-between text-[10px] text-slate-500 mb-1.5">
                  <span>💰 Cobrado: <strong className="text-emerald-600">{COP(cobrosData.resumen.cobrado)}</strong></span>
                  <span>⏳ Por cobrar: <strong className="text-amber-600">{COP(cobrosData.resumen.por_cobrar)}</strong></span>
                  <span>Contrato: {COP(totales.total)}</span>
                </div>
                <div className="flex justify-between text-[10px] text-slate-500 mb-1.5">
                  <span>💸 Gastado: <strong className="text-slate-600">{COP(cobrosData.resumen.gastado)}</strong></span>
                  <span>💼 Caja neta del proyecto: <strong className={cobrosData.resumen.caja_neta >= 0 ? 'text-emerald-600' : 'text-red-500'}>{COP(cobrosData.resumen.caja_neta)}</strong></span>
                </div>
                <div className="h-2 bg-white rounded-full overflow-hidden flex">
                  <div className="h-full bg-emerald-500" style={{ width: `${Math.min(100, cobrosData.resumen.cobrado / totales.total * 100)}%` }} />
                  <div className="h-full bg-amber-400" style={{ width: `${Math.min(100, cobrosData.resumen.por_cobrar / totales.total * 100)}%` }} />
                </div>
              </div>
            )}

            {/* Liquidacion preview */}
            {liquidacion ? (
              <div className="border-2 border-emerald-300 bg-emerald-50/50 rounded-xl p-4 mb-4">
                <p className="text-xs font-bold text-slate-700 mb-2">Liquidación del corte</p>
                <p className="text-[11px] text-slate-500 mb-3">"{liquidacion.avance_titulo}" · {liquidacion.avance_pct}% acumulado</p>
                <div className="space-y-1.5 text-xs">
                  <div className="flex justify-between"><span className="text-slate-500">Ejecutado acumulado</span><span>{COP(liquidacion.ejecutado_acumulado)}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">(−) Ya cobrado en cortes previos</span><span>− {COP(liquidacion.cobrado_previo)}</span></div>
                  <div className="flex justify-between font-medium"><span className="text-slate-600">Valor de este corte</span><span>{COP(liquidacion.valor_corte)}</span></div>
                  {liquidacion.amortizacion > 0 && (
                    <div className="flex justify-between"><span className="text-slate-500">(−) Amortización anticipo ({liquidacion.anticipo_pct}%)</span><span>− {COP(liquidacion.amortizacion)}</span></div>
                  )}
                  <div className="flex justify-between text-sm font-black text-emerald-700 border-t border-emerald-200 pt-1.5 mt-1.5">
                    <span>NETO A COBRAR</span><span>{COP(liquidacion.neto)}</span>
                  </div>
                </div>
                <div className="flex gap-2 mt-3">
                  <button onClick={() => setLiquidacion(null)}
                          className="flex-1 py-2 rounded-xl border border-slate-200 text-slate-600 text-xs">Cancelar</button>
                  <button onClick={async () => {
                            try {
                              const c = await cuentasAPI.crear(id, liquidacion.avance_id)
                              setLiquidacion(null)
                              cuentasAPI.listar(id).then(setCobrosData)
                              toast.success(`Cuenta ${c.numero} generada por ${COP(c.neto)}`)
                            } catch (e) { toast.error(e.message) }
                          }}
                          className="flex-[2] py-2 rounded-xl bg-emerald-500 text-white text-xs font-bold">
                    ✓ Generar cuenta de cobro
                  </button>
                </div>
              </div>
            ) : (
              <div className="mb-4">
                <p className="text-[10px] text-slate-400 uppercase font-semibold mb-1.5">Generar desde un corte de avance</p>
                {avances.length === 0 ? (
                  <p className="text-xs text-slate-400 bg-slate-50 rounded-xl p-3">Publica un avance primero — la cuenta se liquida sobre el valor ejecutado del corte</p>
                ) : (
                  <div className="space-y-1.5">
                    {avances.slice(0, 5).map(a => (
                      <button key={a.id}
                              onClick={() => cuentasAPI.preview(id, a.id).then(setLiquidacion).catch(e => toast.error(e.message))}
                              className="w-full flex items-center justify-between border border-slate-100 hover:border-emerald-300 rounded-xl px-3 py-2.5 transition text-left">
                        <div>
                          <p className="text-xs text-slate-600">{a.titulo}</p>
                          <p className="text-[9px] text-slate-400">{a.fecha} · {a.porcentaje}%</p>
                        </div>
                        <span className="text-xs font-bold text-emerald-600">{COP(a.valor_ejecutado)} →</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Cuentas generadas */}
            <div className="space-y-1.5">
              {cobrosData?.cuentas?.map(c => (
                <div key={c.id} className={`border rounded-xl px-3 py-2.5 ${c.estado === 'pagada' ? 'border-emerald-200 bg-emerald-50/40' : 'border-amber-200 bg-amber-50/30'}`}>
                  <div className="flex items-center justify-between gap-2">
                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-slate-700">{c.numero} · {COP(c.neto)}</p>
                      <p className="text-[9px] text-slate-400">{c.fecha}{c.fecha_pago && ` · pagada ${c.fecha_pago}`}</p>
                    </div>
                    <span className={`shrink-0 text-[9px] font-bold px-2 py-1 rounded-full ${c.estado === 'pagada' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
                      {c.estado === 'pagada' ? '✓ Pagada' : '⏳ Enviada'}
                    </span>
                  </div>
                  <div className="flex gap-1.5 mt-2 flex-wrap">
                    <a href={`/api/cuentas/publico/${p.share_token}/${c.id}.pdf`} target="_blank" rel="noreferrer"
                       className="text-[10px] font-medium text-navy-600 border border-navy-200 rounded-lg px-2 py-1">📄 PDF</a>
                    <button onClick={() => {
                              const url = `${window.location.origin}/api/cuentas/publico/${p.share_token}/${c.id}.pdf`
                              avisarCliente(`Hola! Te envío la cuenta de cobro ${c.numero} por ${COP(c.neto)} del corte de obra de "${p.nombre}". Puedes verla aquí: ${url}\n\nY el avance que la sustenta:`)
                            }}
                            className="text-[10px] font-medium text-emerald-600 border border-emerald-200 rounded-lg px-2 py-1">📲 Enviar</button>
                    {c.estado === 'enviada' && (
                      <>
                        <button onClick={async () => {
                                  await cuentasAPI.pagada(c.id)
                                  cuentasAPI.listar(id).then(setCobrosData)
                                  toast.success('💰 Marcada como pagada')
                                }}
                                className="text-[10px] font-bold text-white bg-emerald-500 rounded-lg px-2 py-1">💰 Ya me pagaron</button>
                        <button onClick={async () => {
                                  if (!confirm('¿Eliminar esta cuenta de cobro?')) return
                                  await cuentasAPI.eliminar(c.id)
                                  cuentasAPI.listar(id).then(setCobrosData)
                                }}
                                className="text-[10px] text-slate-400 border border-slate-200 rounded-lg px-2 py-1">×</button>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Modal GASTOS */}
      {showGastos && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50" onClick={() => setShowGastos(false)}>
          <div className="bg-white rounded-2xl p-5 w-full max-w-lg max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-slate-800">💸 Gastos de obra</h3>
              <button onClick={() => setShowGastos(false)} className="text-slate-400 text-lg">×</button>
            </div>

            {gastosData && (() => {
              const r = gastosData.resumen
              const sana = r.utilidad_real >= r.utilidad_proyectada * 0.9
              const alerta = r.utilidad_real < r.utilidad_proyectada * 0.5
              return (
                <div className={`rounded-xl p-3.5 mb-4 ${alerta ? 'bg-red-50' : sana ? 'bg-emerald-50' : 'bg-amber-50'}`}>
                  <div className="grid grid-cols-2 gap-3 text-center">
                    <div>
                      <p className="text-[10px] uppercase font-semibold text-slate-500">Utilidad proyectada</p>
                      <p className="text-base font-black text-slate-700">{COP(r.utilidad_proyectada)}</p>
                    </div>
                    <div>
                      <p className="text-[10px] uppercase font-semibold text-slate-500">Utilidad real</p>
                      <p className={`text-base font-black ${alerta ? 'text-red-600' : sana ? 'text-emerald-600' : 'text-amber-600'}`}>
                        {COP(r.utilidad_real)}
                      </p>
                    </div>
                  </div>
                  <div className="mt-3">
                    <div className="flex justify-between text-[10px] text-slate-500 mb-1">
                      <span>Gastado: <strong>{COP(r.gastado)}</strong></span>
                      <span>Presupuesto directo: {COP(r.presupuesto_directo)}</span>
                    </div>
                    <div className="h-2 bg-white rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${r.pct_ejecutado_gasto > 100 ? 'bg-red-500' : r.pct_ejecutado_gasto > 85 ? 'bg-amber-400' : 'bg-emerald-500'}`}
                           style={{ width: `${Math.min(100, r.pct_ejecutado_gasto)}%` }} />
                    </div>
                    <p className="text-[9px] text-slate-400 mt-1">{r.pct_ejecutado_gasto}% del costo directo presupuestado{r.pct_ejecutado_gasto > 100 && ' — ¡SOBRECOSTO!'}</p>
                  </div>
                  {Object.keys(r.por_categoria).length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2.5">
                      {Object.entries(r.por_categoria).map(([cat, v]) => (
                        <span key={cat} className="text-[9px] bg-white text-slate-500 px-2 py-1 rounded-full">
                          {cat}: <strong>{COP(v)}</strong>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              )
            })()}

            <div className="bg-slate-50 rounded-xl p-3.5 space-y-2.5 mb-4">
              <div className="flex gap-2">
                <select className="input !py-2 text-xs w-32"
                        value={nuevoGasto.categoria}
                        onChange={e => setNuevoGasto(g => ({ ...g, categoria: e.target.value }))}>
                  <option value="materiales">🧱 Materiales</option>
                  <option value="nomina">👷 Nómina</option>
                  <option value="transporte">🚚 Transporte</option>
                  <option value="herramienta">🔧 Herramienta</option>
                  <option value="otros">📦 Otros</option>
                </select>
                <input className="input !py-2 text-xs flex-1" placeholder="¿Qué compraste? (ej: 20 bultos de cemento)"
                       value={nuevoGasto.descripcion}
                       onChange={e => setNuevoGasto(g => ({ ...g, descripcion: e.target.value }))} />
              </div>
              <div className="flex gap-2 items-center">
                <input type="number" className="input !py-2 text-xs flex-1" placeholder="Valor $"
                       value={nuevoGasto.valor}
                       onChange={e => setNuevoGasto(g => ({ ...g, valor: e.target.value }))} />
                <label className="text-[10px] text-navy-600 border border-navy-200 rounded-lg px-2.5 py-2 cursor-pointer whitespace-nowrap">
                  {nuevoGasto.foto ? '✓ Recibo' : '📷 Recibo'}
                  <input type="file" accept="image/*" className="hidden"
                         onChange={e => {
                           const file = e.target.files?.[0]
                           if (!file) return
                           if (file.size > 450 * 1024) { toast.error('Máximo 450KB'); return }
                           const r = new FileReader()
                           r.onload = () => setNuevoGasto(g => ({ ...g, foto: r.result }))
                           r.readAsDataURL(file)
                         }} />
                </label>
                <button onClick={async () => {
                          if (!nuevoGasto.descripcion.trim() || !nuevoGasto.valor) { toast.error('Descripción y valor'); return }
                          try {
                            await gastosAPI.crear(id, { ...nuevoGasto, valor: parseInt(nuevoGasto.valor) })
                            setNuevoGasto(g => ({ categoria: g.categoria, descripcion: '', valor: '', foto: '' }))
                            gastosAPI.listar(id).then(setGastosData)
                            toast.success('Gasto registrado')
                          } catch (e) { toast.error(e.message) }
                        }}
                        className="bg-navy-600 text-white text-xs font-bold px-4 py-2 rounded-lg">
                  Registrar
                </button>
              </div>
            </div>

            <div className="space-y-1.5">
              {gastosData?.gastos?.length === 0 && (
                <p className="text-center text-xs text-slate-400 py-4">Registra tu primer gasto — cada peso cuenta</p>
              )}
              {gastosData?.gastos?.map(g => (
                <div key={g.id} className="flex items-center gap-2.5 border border-slate-100 rounded-xl px-3 py-2">
                  {g.foto ? (
                    <a href={g.foto} target="_blank" rel="noreferrer">
                      <img src={g.foto} alt="" className="w-9 h-9 rounded-lg object-cover border border-slate-100" />
                    </a>
                  ) : (
                    <span className="w-9 h-9 rounded-lg bg-slate-50 flex items-center justify-center text-sm">
                      {{ materiales: '🧱', nomina: '👷', transporte: '🚚', herramienta: '🔧', otros: '📦' }[g.categoria]}
                    </span>
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-slate-600 truncate">{g.descripcion}</p>
                    <p className="text-[9px] text-slate-400">{g.fecha} · {g.categoria}</p>
                  </div>
                  <p className="text-xs font-bold text-slate-700 shrink-0">{COP(g.valor)}</p>
                  <button onClick={async () => {
                            if (!confirm('¿Eliminar este gasto?')) return
                            await gastosAPI.eliminar(id, g.id)
                            gastosAPI.listar(id).then(setGastosData)
                          }}
                          className="text-slate-300 hover:text-red-400 text-sm shrink-0">×</button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Modal AVANCES DE OBRA (contratista) */}
      {showAvances && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-start justify-center p-4 pt-[5vh] overflow-y-auto" onClick={() => setShowAvances(false)}>
          <div className="bg-white rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="p-4 border-b border-slate-100 sticky top-0 bg-white z-10 flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-slate-800">Avances de obra</h3>
                <p className="text-[11px] text-slate-400">Tu cliente los ve con su mismo enlace del presupuesto</p>
              </div>
              <button onClick={() => setShowAvances(false)} className="p-1.5 hover:bg-slate-100 rounded-lg">
                <X className="w-4 h-4 text-slate-400" />
              </button>
            </div>

            {/* Form nuevo avance */}
            <div className="p-4 bg-slate-50 space-y-3">
              <input className="input" placeholder="Título (ej: Cimentación terminada) *"
                     value={nuevoAvance.titulo}
                     onChange={e => setNuevoAvance(a => ({ ...a, titulo: e.target.value }))} />
              <textarea className="input min-h-[60px] text-xs" placeholder="Descripción del avance (opcional)"
                        value={nuevoAvance.descripcion}
                        onChange={e => setNuevoAvance(a => ({ ...a, descripcion: e.target.value }))} />
              {/* Avance por actividad del presupuesto */}
              <div className="bg-white rounded-xl border border-slate-200 max-h-64 overflow-y-auto">
                <div className="px-3 py-2 border-b border-slate-100 sticky top-0 bg-white">
                  <p className="text-[11px] font-semibold text-slate-500 uppercase">% de avance por actividad</p>
                </div>
                {items.map(it => {
                  const valorItem = Math.round((parseFloat(it.cantidad)||0) * (parseFloat(it.precio_unitario)||0))
                  const pct = avanceItems[it.id] ?? 0
                  return (
                    <div key={it.id} className="px-3 py-2 border-b border-slate-50 flex items-center gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="text-[11px] text-slate-600 leading-snug truncate">{it.descripcion}</p>
                        <p className="text-[10px] text-slate-400">{COP(valorItem)}</p>
                      </div>
                      <input type="number" min="0" max="100" step="5" value={pct}
                             onChange={e => setAvanceItems(m => ({ ...m, [it.id]: Math.max(0, Math.min(100, parseFloat(e.target.value) || 0)) }))}
                             className="w-16 text-right text-xs border border-slate-200 rounded-lg px-2 py-1.5 outline-none focus:border-emerald-400" />
                      <span className="text-[10px] text-slate-400 w-4">%</span>
                      <span className="text-[10px] text-emerald-600 font-medium w-20 text-right">
                        {COP(Math.round(valorItem * pct / 100))}
                      </span>
                    </div>
                  )
                })}
              </div>

              {/* Resumen en vivo: % ponderado + $ ejecutado */}
              {(() => {
                let total = 0, ejec = 0
                items.forEach(it => {
                  const v = Math.round((parseFloat(it.cantidad)||0) * (parseFloat(it.precio_unitario)||0))
                  total += v
                  ejec += Math.round(v * (avanceItems[it.id] ?? 0) / 100)
                })
                const pctPond = total > 0 ? Math.round(ejec / total * 1000) / 10 : 0
                return (
                  <div className="bg-emerald-50 rounded-xl p-3 flex items-center justify-between">
                    <div>
                      <p className="text-[10px] text-emerald-600 uppercase font-semibold">Avance ponderado por valor</p>
                      <p className="text-lg font-black text-emerald-700">{pctPond}%</p>
                    </div>
                    <div className="text-right">
                      <p className="text-[10px] text-emerald-600 uppercase font-semibold">Valor ejecutado</p>
                      <p className="text-sm font-bold text-emerald-700">{COP(ejec)} <span className="font-normal text-emerald-500">de {COP(total)}</span></p>
                    </div>
                  </div>
                )
              })()}
              <div className="flex items-center gap-2">
                <label className="flex items-center gap-2 text-xs text-navy-600 font-medium border border-navy-200 rounded-xl px-3 py-2 cursor-pointer hover:bg-navy-50">
                  <Camera className="w-4 h-4" /> Fotos ({nuevoAvance.fotos.length}/3)
                  <input type="file" accept="image/*" multiple className="hidden"
                         onChange={e => {
                           const files = Array.from(e.target.files || []).slice(0, 3 - nuevoAvance.fotos.length)
                           files.forEach(file => {
                             if (file.size > 450 * 1024) { toast.error(`${file.name}: máximo 450KB por foto`); return }
                             const r = new FileReader()
                             r.onload = () => setNuevoAvance(a => ({ ...a, fotos: [...a.fotos, r.result].slice(0, 3) }))
                             r.readAsDataURL(file)
                           })
                           e.target.value = ''
                         }} />
                </label>
                {nuevoAvance.fotos.map((f, i) => (
                  <div key={i} className="relative">
                    <img src={f} alt="" className="w-10 h-10 rounded-lg object-cover" />
                    <button onClick={() => setNuevoAvance(a => ({ ...a, fotos: a.fotos.filter((_, j) => j !== i) }))}
                            className="absolute -top-1.5 -right-1.5 bg-red-500 text-white rounded-full w-4 h-4 text-[9px] leading-none">×</button>
                  </div>
                ))}
              </div>
              <button disabled={subiendoAvance}
                      onClick={async () => {
                        if (!nuevoAvance.titulo.trim()) { toast.error('El avance necesita un título'); return }
                        setSubiendoAvance(true)
                        try {
                          const payload = {
                            ...nuevoAvance,
                            items: items.map(it => ({ id: it.id, pct: avanceItems[it.id] ?? 0 })),
                          }
                          const a = await avancesAPI.crear(id, payload)
                          setAvances(prev => [a, ...prev])
                          setNuevoAvance({ titulo: '', descripcion: '', fotos: [] })
                          toast.success(`Avance publicado: ${a.porcentaje}% = ${COP(a.valor_ejecutado)}`)
                          setTimeout(() => {
                            if (confirm('¿Avisar al cliente por WhatsApp del nuevo avance?')) {
                              avisarCliente(`Hola! Publiqué el avance de tu obra "${p.nombre}": ${a.porcentaje}% completado (${COP(a.valor_ejecutado)} ejecutados) 🏗️ Míralo aquí:`)
                            }
                          }, 600)
                        } catch (e) { toast.error(e.message) }
                        finally { setSubiendoAvance(false) }
                      }}
                      className="w-full py-2.5 rounded-xl bg-navy-600 text-white text-sm font-medium disabled:opacity-50">
                {subiendoAvance ? 'Publicando...' : 'Publicar avance'}
              </button>
            </div>

            {/* Lista de avances */}
            <div className="p-4 space-y-2">
              {avances.length === 0 ? (
                <p className="text-center text-xs text-slate-400 py-4">Aún no has publicado avances</p>
              ) : avances.map(a => (
                <div key={a.id} className="border border-slate-100 rounded-xl p-3">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="text-sm font-medium text-slate-700">{a.titulo}</p>
                      <p className="text-[10px] text-slate-400">{a.fecha} · {a.porcentaje}% · <span className="text-emerald-600 font-medium">{COP(a.valor_ejecutado)}</span></p>
                    </div>
                    <button onClick={async () => {
                              if (!confirm('¿Eliminar este avance?')) return
                              await avancesAPI.eliminar(id, a.id)
                              setAvances(prev => prev.filter(x => x.id !== a.id))
                            }}
                            className="p-1 hover:bg-red-50 rounded">
                      <Trash2 className="w-3.5 h-3.5 text-slate-300 hover:text-red-500" />
                    </button>
                  </div>
                  {a.fotos?.length > 0 && (
                    <div className="flex gap-1.5 mt-2">
                      {a.fotos.map((f, i) => (
                        <img key={i} src={f} alt="" className="w-14 h-14 rounded-lg object-cover" />
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Modal VER PRESUPUESTO (preview como lo ve el cliente) */}
      {showPreview && totales && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-start justify-center p-4 pt-[4vh] overflow-y-auto" onClick={() => setShowPreview(false)}>
          <div className="bg-slate-100 rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            {/* Header estilo cliente */}
            <div className="bg-navy-800 text-white px-5 py-6 rounded-t-2xl sticky top-0 z-10">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-blue-200 text-[10px] uppercase tracking-wide">Vista previa — así lo verá tu cliente</p>
                  <h3 className="font-bold text-lg leading-tight mt-1">{p.nombre}</h3>
                  {p.cliente_nombre && <p className="text-xs text-blue-200 mt-0.5">Para: {p.cliente_nombre}</p>}
                </div>
                <button onClick={() => setShowPreview(false)} className="p-2 hover:bg-white/10 rounded-lg shrink-0">
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Total */}
            <div className="px-4 -mt-3">
              <div className="bg-white rounded-xl shadow p-4 text-center">
                <p className="text-[10px] text-slate-400 uppercase tracking-wide">Valor total</p>
                <p className="text-2xl font-black text-slate-800">{COP(totales.total)}</p>
              </div>
            </div>

            {/* Items por capitulo */}
            <div className="px-4 py-3 space-y-2">
              {Object.entries(grupos).map(([cap, itemsCap]) => (
                <div key={cap} className="bg-white rounded-xl p-3">
                  <div className="flex justify-between items-center mb-2">
                    <p className="text-xs font-bold text-slate-600 uppercase">{cap}</p>
                    <p className="text-xs font-semibold text-slate-700">
                      {COP(itemsCap.reduce((s, it) => s + (parseFloat(it.cantidad)||0) * (parseFloat(it.precio_unitario)||0), 0))}
                    </p>
                  </div>
                  <div className="space-y-1.5">
                    {itemsCap.map(it => (
                      <div key={it._idx} className="flex justify-between gap-2 text-[11px]">
                        <span className="text-slate-500 leading-snug">{it.descripcion}</span>
                        <span className="text-slate-600 whitespace-nowrap shrink-0">
                          {it.cantidad} {it.unidad} · {COP((parseFloat(it.cantidad)||0)*(parseFloat(it.precio_unitario)||0))}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}

              {/* Resumen financiero */}
              <div className="bg-white rounded-xl p-4 text-xs space-y-1.5">
                <div className="flex justify-between text-slate-500">
                  <span>Costo directo</span><span>{COP(totales.subtotal_directo)}</span>
                </div>
                {aiu.aplicar && (
                  <>
                    <div className="flex justify-between text-slate-400">
                      <span>Administración ({aiu.admin}%)</span><span>{COP(totales.admin_valor)}</span>
                    </div>
                    <div className="flex justify-between text-slate-400">
                      <span>Imprevistos ({aiu.imprevistos}%)</span><span>{COP(totales.imprevistos_valor)}</span>
                    </div>
                    <div className="flex justify-between text-slate-400">
                      <span>Utilidad ({aiu.utilidad}%)</span><span>{COP(totales.utilidad_valor)}</span>
                    </div>
                  </>
                )}
                <div className="flex justify-between text-slate-500">
                  <span>IVA</span><span>{COP(totales.iva)}</span>
                </div>
                <div className="flex justify-between font-bold text-slate-800 pt-1.5 border-t border-slate-100 text-sm">
                  <span>Total</span><span>{COP(totales.total)}</span>
                </div>
                <p className="text-[9px] text-slate-300 pt-1">{totales.regimen_iva}</p>
              </div>
            </div>

            {/* Acciones */}
            <div className="sticky bottom-0 bg-white border-t border-slate-200 p-3 rounded-b-2xl flex gap-2">
              <button onClick={() => setShowPreview(false)}
                      className="flex-1 py-2.5 rounded-xl border border-slate-200 text-slate-600 text-sm font-medium">
                Seguir editando
              </button>
              <button onClick={() => { setShowPreview(false); compartir() }}
                      className="flex-[2] flex items-center justify-center gap-2 py-2.5 rounded-xl bg-emerald-500 text-white text-sm font-bold">
                <MessageCircle className="w-4 h-4" /> Todo bien, enviar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal compartir */}
      {showShare && shareData && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={() => setShowShare(false)}>
          <div className="bg-white rounded-2xl w-full max-w-md p-6 space-y-4" onClick={e => e.stopPropagation()}>
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-12 h-12 bg-emerald-100 rounded-2xl mb-2">
                <MessageCircle className="w-6 h-6 text-emerald-600" />
              </div>
              <h3 className="font-semibold text-slate-800">Compartir presupuesto</h3>
              <p className="text-xs text-slate-400 mt-1">
                El cliente lo abre en su celular, ve el desglose y puede aceptar con un botón.
                Tú verás cuándo lo abrió.
              </p>
            </div>

            <div className="bg-slate-50 rounded-xl p-3 text-xs text-slate-600 break-all">
              {urlPublica}
            </div>

            <div className="grid grid-cols-2 gap-2">
              <button onClick={copiarLink}
                      className="flex items-center justify-center gap-2 py-2.5 rounded-xl border border-slate-200 text-sm font-medium text-slate-600">
                <CopyIcon className="w-4 h-4" /> Copiar link
              </button>
              <button onClick={abrirWhatsApp}
                      className="flex items-center justify-center gap-2 py-2.5 rounded-xl bg-emerald-500 text-white text-sm font-medium">
                <MessageCircle className="w-4 h-4" /> Enviar por WhatsApp
              </button>
            </div>

            {eventos && (
              <div className="text-xs text-slate-500 text-center pt-1">
                {eventos.total_vistas === 0
                  ? 'Aún no lo han abierto'
                  : `Visto ${eventos.total_vistas} ${eventos.total_vistas === 1 ? 'vez' : 'veces'}${eventos.ultima_vista ? ' · última: ' + new Date(eventos.ultima_vista).toLocaleString('es-CO') : ''}`}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
