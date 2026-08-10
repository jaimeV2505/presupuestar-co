import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { ArrowLeft, Search, Plus, Trash2, Share2, FileSpreadsheet, FileText,
         Eye, CheckCircle2, X, MessageCircle, Copy as CopyIcon, Pencil } from 'lucide-react'
import { proyectosAPI, preciosAPI, shareAPI, exportarAPI } from '../services/api'

const COP = (v) => '$' + Math.round(v || 0).toLocaleString('es-CO')

export default function Editor() {
  const { id } = useParams()
  const nav = useNavigate()
  const [p, setP] = useState(null)
  const [items, setItems] = useState([])
  const [aiu, setAiu] = useState({ admin: 15, imprevistos: 5, utilidad: 8, aplicar: true, iva_sobre_utilidad: true })
  const [totales, setTotales] = useState(null)
  const [guardando, setGuardando] = useState(false)

  // Buscador
  const [q, setQ] = useState('')
  const [categoria, setCategoria] = useState('')
  const [resultados, setResultados] = useState([])
  const [categorias, setCategorias] = useState([])
  const [buscando, setBuscando] = useState(false)
  const [showBuscador, setShowBuscador] = useState(false)

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
      setTotales(data.totales)
      if (data.share_token) shareAPI.eventos(id).then(setEventos).catch(() => {})
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
                {p.cliente_nombre || 'Sin cliente'} · {guardando ? 'Guardando...' : 'Guardado ✓'}
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
                  <div key={it._idx} className="p-3 flex items-center gap-3">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-700 leading-snug">{it.descripcion}</p>
                      {it.precio_editado && <span className="text-[10px] text-amber-600 font-medium">precio ajustado</span>}
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
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
