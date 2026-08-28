import React, { useState, useEffect, useLayoutEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { ArrowLeft, Search, Plus, Trash2, Share2, FileSpreadsheet, FileText,
         Eye, CheckCircle2, X, MessageCircle, Copy as CopyIcon, Pencil, Calculator, Camera, Upload, HardHat } from 'lucide-react'
import { otrosiesAPI, proyectosAPI, preciosAPI, shareAPI, exportarAPI, avancesAPI, gastosAPI, cuentasAPI, onboardingAPI , apusAPI, proveedoresAPI, insumosAPI, disenosAPI, cronogramaAPI } from '../services/api'
import { comprimirImagen } from '../utils/imagen'
import InfoTip from '../components/InfoTip'
import { pedirTexto, confirmarDialogo } from '../components/Dialogo'

const COP = (v) => '$' + Math.round(v || 0).toLocaleString('es-CO')

export default function Editor() {
  const { id } = useParams()
  const nav = useNavigate()
  const [p, setP] = useState(null)
  const [items, setItems] = useState([])
  const [aiu, setAiu] = useState({ admin: 15, imprevistos: 5, utilidad: 8, aplicar: true, iva_sobre_utilidad: true })
  const [contrato, setContrato] = useState({ plazo_dias: 45, anticipo_pct: 50, retegarantia_pct: 0, fecha_inicio: '', lugar: '', deducciones: [] })
  const [totales, setTotales] = useState(null)
  const [guardando, setGuardando] = useState(false)

  // Buscador
  const [q, setQ] = useState('')
  const [categoria, setCategoria] = useState('')
  const [resultados, setResultados] = useState([])
  const [categorias, setCategorias] = useState([])
  const [buscando, setBuscando] = useState(false)
  const [showBuscador, setShowBuscador] = useState(false)
  const [fuenteApu, setFuenteApu] = useState('base')        // base | mios
  const [previewBase, setPreviewBase] = useState(null)       // {codigo, descripcion, cargando, data, error}
  const [misApus, setMisApus] = useState([])
  const [showProveedores, setShowProveedores] = useState(false)
  const [proveedores, setProveedores] = useState([])
  const [provSel, setProvSel] = useState(null)              // {id, nombre, precios: []}
  const [nuevoProv, setNuevoProv] = useState({ nombre: '', telefono: '' })
  const [nuevoPrecio, setNuevoPrecio] = useState({ insumo: '', unidad: 'un', precio: '' })
  const [cargandoMasivo, setCargandoMasivo] = useState(false)
  const [conflictosMasivo, setConflictosMasivo] = useState(null)   // {proveedorId, lista: [...]}
  const fileMasivoRef = useRef(null)
  const [showConstructor, setShowConstructor] = useState(false)
  const [construyendo, setConstruyendo] = useState({ descripcion: '', unidad: 'm2', insumos: [], mano_obra: '', herramienta_pct: 5, transporte: '' })
  const [previewComp, setPreviewComp] = useState(null)
  const [showBalance, setShowBalance] = useState(false)
  const [showSeguimiento, setShowSeguimiento] = useState(false)
  const [seguimiento, setSeguimiento] = useState(null)   // {balance, cuentas, avancesList}
  const [balanceData, setBalanceData] = useState(null)
  const [sugerencias, setSugerencias] = useState([])   // autocomplete de insumos
  const [sugerenciaPara, setSugerenciaPara] = useState(-1)
  const [charla, setCharla] = useState(null)          // interacciones del cliente, por avance
  const [respondiendo, setRespondiendo] = useState({})  // {avance_id: texto}
  const [catalogo, setCatalogo] = useState(null)        // {categorias} | {insumos}
  const [showCatalogo, setShowCatalogo] = useState(false)

  // Calculadora de cantidades + Preview
  const [calcAbierta, setCalcAbierta] = useState(null)  // idx del item con calc abierta
  const [showAnalisis, setShowAnalisis] = useState(false)   // F3: incidencia por capitulos
  const [showDescuento, setShowDescuento] = useState(false) // F7: negociacion
  const [descuentoPct, setDescuentoPct] = useState('')
  const [showPreview, setShowPreview] = useState(false)

  // Avances de obra (cuando el presupuesto esta aceptado)
  const [showAvances, setShowAvances] = useState(false)
  const [avances, setAvances] = useState([])
  const [nuevoAvance, setNuevoAvance] = useState({ titulo: '', descripcion: '', fotos: [] })
  const [avanceItems, setAvanceItems] = useState({})  // {itemId: pct}
  // ── Adicionales (otrosies) ──
  const [otrosies, setOtrosies] = useState([])
  const [showOtrosi, setShowOtrosi] = useState(false)
  const [showCronograma, setShowCronograma] = useState(false)
  const [cronoData, setCronoData] = useState(null)
  const [cronoFilas, setCronoFilas] = useState([])
  const [cronoGuardando, setCronoGuardando] = useState(false)
  const [otMotivo, setOtMotivo] = useState('')
  const [otItems, setOtItems] = useState([{ descripcion: '', unidad: 'un', cantidad: 1, precio_unitario: '' }])
  const [otBusca, setOtBusca] = useState('')
  const [otResultados, setOtResultados] = useState([])
  const [valorTotalDirecto, setValorTotalDirecto] = useState(0)
  const [subiendoAvance, setSubiendoAvance] = useState(false)
  const [calificacion, setCalificacion] = useState(null)
  const [showGastos, setShowGastos] = useState(false)
  const [gastosData, setGastosData] = useState(null)
  const [nuevoGasto, setNuevoGasto] = useState({ categoria: 'materiales', descripcion: '', valor: '', foto: '' })
  const [showCobros, setShowCobros] = useState(false)
  const [cobrosData, setCobrosData] = useState(null)
  const [abonando, setAbonando] = useState(null)   // {cuenta, monto, nota}
  const [showPanel, setShowPanel] = useState(false) // panel lateral de herramientas
  const [hiloTexto, setHiloTexto] = useState({})    // {avanceId: texto} respuesta al cliente
  const [liquidacion, setLiquidacion] = useState(null)  // preview antes de crear
  const [tipEditor, setTipEditor] = useState(!localStorage.getItem('tip_editor'))
  const [tipObra, setTipObra] = useState(false)

  // Share
  const [showShare, setShowShare] = useState(false)
  const [shareData, setShareData] = useState(null)
  const [eventos, setEventos] = useState(null)

  const timerGuardar = useRef(null)
  const timerBuscar = useRef(null)

  // ── Cargar proyecto ──────────────────────────────────────────────────
  useEffect(() => {
    proyectosAPI.obtener(id).then(data => {
      if (data.es_demo) { onboardingAPI.marcar('explora').catch(() => {}) }
      if (!['borrador', 'enviado', 'visto', 'rechazado'].includes(data.estado)) {
        otrosiesAPI.listar(id).then(setOtrosies).catch(() => {})
      }
      if (['aceptado', 'entrega_solicitada', 'terminado'].includes(data.estado) && !localStorage.getItem('tip_obra')) {
        setTipObra(true)
      }
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
    let sub = 0, subLista = 0
    const porCap = {}
    itemsAct.forEach(it => {
      const cant = parseFloat(it.cantidad) || 0
      const pu = parseFloat(it.precio_unitario) || 0
      const pl = parseFloat(it.precio_lista) || 0
      const v = Math.round(cant * pu)
      sub += v
      subLista += Math.round(cant * (pl > pu ? pl : pu))
      const cap = it.capitulo || 'OTROS'
      porCap[cap] = (porCap[cap] || 0) + v
    })
    sub = Math.round(sub)
    const capitulos = Object.entries(porCap)
      .map(([capitulo, valor]) => ({ capitulo, valor, pct: sub ? Math.round(valor * 1000 / sub) / 10 : 0 }))
      .sort((x, y) => y.valor - x.valor)
    const descuento_valor = Math.max(0, subLista - sub)
    const descuento_pct = subLista ? Math.round(descuento_valor * 1000 / subLista) / 10 : 0
    const a = aiuAct.aplicar ? Math.round(sub * (aiuAct.admin || 0) / 100) : 0
    const i = aiuAct.aplicar ? Math.round(sub * (aiuAct.imprevistos || 0) / 100) : 0
    const u = aiuAct.aplicar ? Math.round(sub * (aiuAct.utilidad || 0) / 100) : 0
    const base = sub + a + i + u
    const iva = aiuAct.aplicar
      ? (aiuAct.iva_sobre_utilidad ? Math.round(u * 0.19) : Math.round(base * 0.19))
      : (aiuAct.con_iva ? Math.round(sub * 0.19) : 0)
    return {
      subtotal_directo: sub, admin_valor: a, imprevistos_valor: i, utilidad_valor: u,
      aiu_total: a + i + u, base_con_aiu: base, iva, total: base + iva, num_items: itemsAct.length,
      capitulos, subtotal_lista: subLista, descuento_valor, descuento_pct,
      regimen_iva: aiuAct.aplicar ? (aiuAct.iva_sobre_utilidad ? 'IVA 19% solo sobre utilidad (Art. 462-1 ET)' : 'IVA 19% sobre base + AIU') : (aiuAct.con_iva ? 'IVA 19% sobre el total' : 'Sin IVA'),
    }
  }, [])

  // ── Autoguardado robusto: debounce + reintentos con backoff ──────────
  // Siempre envia la ULTIMA version (pendienteRef), reintenta 3 veces en
  // silencio ante fallas de red, y muestra UN solo aviso deduplicado.
  const pendienteRef = useRef(null)
  const enviandoRef = useRef(false)
  const [sinRed, setSinRed] = useState(false)

  const _enviar = useCallback(async (intento = 0) => {
    if (enviandoRef.current || !pendienteRef.current) return
    enviandoRef.current = true
    const payload = pendienteRef.current
    pendienteRef.current = null
    setGuardando(true)
    try {
      const data = await proyectosAPI.actualizar(id, payload)
      setTotales(data.totales) // el backend es la fuente de verdad
      setSinRed(false)
      toast.dismiss('save-err')
      enviandoRef.current = false
      if (pendienteRef.current) _enviar(0) // llegaron cambios mientras guardaba
    } catch (e) {
      enviandoRef.current = false
      const esRed = !e.response // sin respuesta = problema de conexion
      // Reencolar lo que fallo (sin pisar cambios mas nuevos)
      if (!pendienteRef.current) pendienteRef.current = payload
      if (esRed && intento < 3) {
        setSinRed(true)
        setTimeout(() => _enviar(intento + 1), [1500, 4000, 8000][intento])
      } else if (esRed) {
        setSinRed(true)
        const offline = typeof navigator !== 'undefined' && navigator.onLine === false
        toast.error(offline
          ? 'Sin conexión — tus cambios se guardarán al volver la señal'
          : 'El servidor tarda en responder — seguiré reintentando tus cambios', { id: 'save-err', duration: 5000 })
        setTimeout(() => _enviar(0), 15000) // sigue intentando en segundo plano
      } else {
        const motivo = e.response?.data?.detail || e.message
        toast.error(motivo, { id: 'save-err', duration: 6000 })
      }
    } finally {
      setGuardando(false)
    }
  }, [id])

  const guardar = useCallback((itemsAct, aiuAct) => {
    setTotales(calcularLocal(itemsAct, aiuAct))
    pendienteRef.current = { items: itemsAct, aiu: aiuAct }
    clearTimeout(timerGuardar.current)
    timerGuardar.current = setTimeout(() => _enviar(0), 1000)
  }, [calcularLocal, _enviar])

  // Blindaje contra perdida de datos: si el usuario recarga o cierra la pestaña
  // MIENTRAS hay un guardado pendiente/reintentando (ej. servidor lento), ese
  // cambio se pierde en silencio — pendienteRef vive solo en memoria del navegador,
  // no sobrevive un reload. El aviso nativo del navegador es la unica red de
  // seguridad real aqui: obliga a confirmar antes de irse con cambios sin guardar.
  useEffect(() => {
    const handler = (e) => {
      if (pendienteRef.current || guardando || sinRed) {
        e.preventDefault()
        e.returnValue = ''
        return ''
      }
    }
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [guardando, sinRed])

  // Fuerza el guardado pendiente ANTES de exportar: el autoguardado es debounced 1s
  // y exportar lee la verdad del SERVIDOR — sin este flush, exportar justo tras editar
  // puede pegarle a un backend todavia con el presupuesto viejo (o vacio).
  const flushGuardado = useCallback(async () => {
    clearTimeout(timerGuardar.current)
    if (pendienteRef.current) await _enviar(0)
  }, [_enviar])

  const setItemsYGuardar = (fn) => {
    if (p?.estado === 'terminado') {
      toast.error('Proyecto terminado — solo lectura. Duplícalo para reutilizar el presupuesto.', { id: 'ro' })
      return
    }
    setItems(prev => {
      const next = typeof fn === 'function' ? fn(prev) : fn
      guardar(next, aiu)
      return next
    })
  }

  const timerContrato = useRef(null)
  const setContratoYGuardar = (nuevo) => {
    if (p?.estado === 'terminado') {
      toast.error('Proyecto terminado — solo lectura. Duplícalo para reutilizar el presupuesto.', { id: 'ro' })
      return
    }
    setContrato(nuevo)
    // Deducciones >50%: se ve en pantalla (chip rojo) pero NO viaja al servidor
    const totalDed = (nuevo.deducciones || []).reduce((s, x) => s + (parseFloat(x.pct) || 0), 0)
    if (totalDed > 50) {
      clearTimeout(timerContrato.current)
      toast.error('Las deducciones suman más del 50% del corte — ajusta antes de guardar', { id: 'ded50' })
      return
    }
    toast.dismiss('ded50')
    clearTimeout(timerContrato.current)
    timerContrato.current = setTimeout(() => {
      proyectosAPI.actualizar(id, { contrato: nuevo }).catch(e => toast.error(e.message))
    }, 800)
  }

  const avisarCliente = (mensaje) => {
    const link = `${window.location.origin}/api/s/${p.share_token}`   // URL con preview OG de la obra
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

  const esPublico = p?.sector === 'publico'
  const soloLectura = p?.estado === 'terminado'   // 🔒 terminado: solo vista, duplicar para reutilizar
  const selladoUI = soloLectura || ['aceptado', 'entrega_solicitada'].includes(p?.estado)  // la tabla firmada no se teclea

  // ── F1: visibilidad del ANÁLISIS del ítem (desglose de Mis APUs) ────────
  const [desgloses, setDesgloses] = useState({ porId: {}, porCodigo: {} })
  const [analisisAbierto, setAnalisisAbierto] = useState(null)  // _idx del item expandido

  // La barra fija de totales tapa SIEMPRE los ultimos ~64-90px del VIEWPORT ACTUAL
  // (asi es "fixed" — no importa cuanto padding le pongamos DESPUES al contenido,
  // eso no mueve nada que ya este ARRIBA de ese padding). En pantallas cortas, con
  // poco contenido (ej: un solo item, panel de analisis cerrado), el final real del
  // documento (Contrato de obra) puede caer justo en esa franja SIN que nadie haya
  // scrolleado — geometria pura en scrollY=0, no una condicion de carrera.
  // El fix real es mover el scroll de verdad. Corre SINCRONO (antes del primer paint),
  // no con un timer que ya demostramos que llega tarde una y otra vez.
  useLayoutEffect(() => {
    const el = document.scrollingElement || document.documentElement
    const ALTO_FOOTER_MAX = 140  // mas generoso que cualquier alto real (con badge de descuento + AIU + IVA)
    const maxScroll = Math.max(0, el.scrollHeight - window.innerHeight)
    // Solo empujamos si hay ADONDE scrollear y si el usuario esta cerca del tope
    // (si ya scrolleo manualmente mas abajo, no le peleamos su scroll).
    if (maxScroll > 0 && el.scrollTop < ALTO_FOOTER_MAX) {
      el.scrollTop = Math.min(ALTO_FOOTER_MAX, maxScroll)
    }
  }, [items.length, analisisAbierto])
  const [showExplosion, setShowExplosion] = useState(false)     // F2: lista de materiales
  const [rindeIdx, setRindeIdx] = useState(-1)                  // R2: calculadora de rendimiento
  const [showDisenos, setShowDisenos] = useState(false)         // 🎨 renders/planos para el cliente
  const [disenos, setDisenos] = useState([])
  const [comentarioDiseno, setComentarioDiseno] = useState({})  // did -> texto en curso
  const [explosionData, setExplosionData] = useState(null)
  useEffect(() => {
    apusAPI.listar({}).then(r => {
      const porId = {}, porCodigo = {}, codigoAId = {}
      for (const a of (r.items || [])) {
        if (a.desglose?.insumos?.length) {
          porId[a.id] = a.desglose
          if (a.codigo) { porCodigo[a.codigo] = a.desglose; codigoAId[a.codigo] = a.id }
        }
      }
      setDesgloses({ porId, porCodigo, codigoAId })
    }).catch(() => {})
  }, [id])
  const desgloseDe = (it) => {
    if (it.apu_id && desgloses.porId[it.apu_id]) return desgloses.porId[it.apu_id]
    const cod = (it.codigo || '').trim()
    if (cod.startsWith('MIO-') && desgloses.porId[parseInt(cod.slice(4))]) return desgloses.porId[parseInt(cod.slice(4))]
    return desgloses.porCodigo[cod] || null
  }
  const apuIdDe = (it) => {
    if (it.apu_id && desgloses.porId[it.apu_id]) return it.apu_id
    const cod = (it.codigo || '').trim()
    if (cod.startsWith('MIO-') && desgloses.porId[parseInt(cod.slice(4))]) return parseInt(cod.slice(4))
    return desgloses.codigoAId?.[cod] || null
  }
  const [anEdit, setAnEdit] = useState(null)          // copia editable del desglose abierto
  const [anGuardando, setAnGuardando] = useState(false)
  const abrirAnalisis = (it) => {
    if (analisisAbierto === it._idx) { setAnalisisAbierto(null); setAnEdit(null); return }
    const d = desgloseDe(it)
    setAnalisisAbierto(it._idx)
    setAnEdit(d ? JSON.parse(JSON.stringify({ ...d, transporte: d.transporte || 0 })) : null)
  }
  const recalcularAnalisis = async (it, aplicarAlItem) => {
    const apuId = apuIdDe(it)
    if (!apuId || !anEdit) return
    // Pre-validación didáctica: el 400 del servidor jamás debe sorprender
    const herr = parseFloat(anEdit.herramienta_pct) || 0
    if (herr > 30) { toast.error('La herramienta es un % de la MO (máx 30). ¿Era un flete en pesos? Va en Transporte 🚚'); return }
    const despMalo = (anEdit.insumos || []).find(x => (parseFloat(x.desperdicio_pct) || 0) > 50)
    if (despMalo) { toast.error(`Desperdicio de "${despMalo.nombre}" fuera de rango (máx 50%)`); return }
    setAnGuardando(true)
    try {
      const r = await apusAPI.guardarDesglose(apuId, {
        insumos: anEdit.insumos.map(x => ({ nombre: x.nombre, unidad: x.unidad,
          cantidad: parseFloat(x.cantidad) || 0, precio: parseFloat(x.precio) || 0,
          desperdicio_pct: parseFloat(x.desperdicio_pct) || 0 })),
        mano_obra: Math.round(parseFloat(anEdit.mano_obra) || 0),
        herramienta_pct: parseFloat(anEdit.herramienta_pct) || 0,
        transporte: Math.round(parseFloat(anEdit.transporte) || 0),
      })
      // el servidor es la fuente de verdad: refrescamos mapa y copia editable
      setDesgloses(prev => {
        const porId = { ...prev.porId, [apuId]: r.desglose }
        const porCodigo = { ...prev.porCodigo }
        if (r.codigo) porCodigo[r.codigo] = r.desglose
        return { ...prev, porId, porCodigo }
      })
      setAnEdit(JSON.parse(JSON.stringify({ ...r.desglose, transporte: r.desglose.transporte || 0 })))
      if (aplicarAlItem) {
        // bug real: x._idx no existe en los items crudos (solo en la copia de render de la linea 469);
        // el match correcto es por POSICION, igual que actualizarItem/eliminarItem/actualizarCalc
        setItemsYGuardar(prev => prev.map((x, i) => i === it._idx
          ? { ...x, precio_unitario: r.precio, precio_lista: null, precio_editado: false } : x))
        toast.success(`APU recalculado y aplicado: ${COP(r.precio)} — totales, anexo y lista de materiales al día ✨`)
        // el trabajo esta hecho: cerramos el panel y volvemos a ver el item ya actualizado
        // en la lista (ademas, un panel colgante en movil no tiene por que competir con
        // la barra fija de totales que viene despues).
        setAnalisisAbierto(null)
        setAnEdit(null)
      } else {
        toast.success(`APU recalculado: ${COP(r.precio)} (guardado en Mis APUs)`)
      }
    } catch (e2) { toast.error(e2.response?.data?.detail || e2.message) }
    setAnGuardando(false)
  }
  const nAnalizados = items.filter(it => desgloseDe(it)).length

  useEffect(() => {
    if (!showBuscador || fuenteApu !== 'mios') return
    apusAPI.listar({ q: q || undefined, sector: esPublico ? 'publico' : 'privado' })
      .then(r => setMisApus(r.items || [])).catch(() => setMisApus([]))
  }, [q, showBuscador, fuenteApu, esPublico])

  const duplicarComoMio = async (apu, e) => {
    e.stopPropagation()
    try {
      await apusAPI.duplicarDeBase(apu.codigo, p?.region || 'bogota')
      toast.success('Copiado a Mis APUs — edítalo a tu gusto ⧉')
    } catch (err) { toast.error(err.message) }
  }

  const verDesgloseBase = async (apu, e) => {
    e.stopPropagation()
    setPreviewBase({ codigo: apu.codigo, descripcion: apu.descripcion, cargando: true, data: null, error: null })
    try {
      const data = await apusAPI.desgloseBase(apu.codigo, p?.region || 'bogota')
      setPreviewBase(prev => prev?.codigo === apu.codigo ? { ...prev, cargando: false, data } : prev)
    } catch (err) {
      setPreviewBase(prev => prev?.codigo === apu.codigo ? { ...prev, cargando: false, error: err.message } : prev)
    }
  }

  const cargarProveedores = () => proveedoresAPI.listar().then(r => setProveedores(r.proveedores || [])).catch(() => {})

  const agregarItem = (apu) => {
    const esMio = apu.id && !apu.categoria   // mis APUs traen id numerico y no categoria
    const nuevo = {
      id: `${apu.codigo || (esMio ? `mio${apu.id}` : 'apu')}-${Date.now()}`,
      codigo: apu.codigo || (esMio ? `MIO-${apu.id}` : ''),
      capitulo: apu.categoria || 'MIS ACTIVIDADES',
      descripcion: apu.descripcion,
      unidad: apu.unidad,
      cantidad: 1,
      precio_unitario: apu.precio,
      precio_editado: false,
      ...(esMio ? { apu_id: apu.id } : {}),   // F1: enlaza el desglose para el anexo de APUs
    }
    setItemsYGuardar(prev => [...prev, nuevo])
    toast.success(`«${(apu.descripcion || '').slice(0, 32)}» → al presupuesto ✓ (cierra el buscador y lo ves en la tabla, capítulo ${nuevo.capitulo})`, { duration: 2600 })
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
  // La URL con preview OG (muestra nombre de la obra, monto y foto en el chat)
  const urlPreview = shareData ? `${window.location.origin}${shareData.ruta_preview || shareData.ruta_publica}` : ''
  const abrirWhatsApp = () => {
    const texto = encodeURIComponent(`${shareData.mensaje_whatsapp} ${urlPreview}`)
    const base = shareData.telefono_cliente ? shareData.whatsapp_url_base : 'https://wa.me/'
    window.open(`${base}?text=${texto}`, '_blank')
  }

  const copiarLink = () => {
    navigator.clipboard.writeText(urlPreview)
    toast.success('Enlace copiado')
  }

  // ── Exportar ──────────────────────────────────────────────────────────
  const exportar = async (tipo) => {
    try {
      await flushGuardado()
      toast.loading('Generando ' + tipo.toUpperCase() + '...', { id: 'exp' })
      const payload = { proyecto_id: parseInt(id) }
      const res = tipo === 'excel' ? await exportarAPI.excel(payload)
                : tipo === 'apus' ? await exportarAPI.apusPdf(payload)
                : await exportarAPI.pdf(payload)
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url
      a.download = `${p.nombre.replace(/[^a-z0-9]/gi, '_')}${tipo === 'apus' ? '_APUs' : ''}.${tipo === 'excel' ? 'xlsx' : 'pdf'}`
      a.click()
      URL.revokeObjectURL(url)
      toast.success('Descargado', { id: 'exp' })
    } catch (e) { toast.error('Error exportando: ' + e.message, { id: 'exp' }) }
  }

  if (!p) return <div className="min-h-screen bg-slate-50 flex items-center justify-center text-slate-400">Cargando...</div>

  // Items EFECTIVOS para el avance: contrato + adicionales (otrosi) APROBADOS,
  // con el MISMO prefijo "ot{n}:" que espera items_efectivos() en el backend.
  // Se calcula UNA sola vez y se reutiliza en el checklist, el resumen en vivo
  // y el payload de envio — antes el payload solo tomaba `items` (sin otrosies)
  // y cualquier % marcado sobre un adicional se descartaba en silencio: nunca
  // llegaba al backend, nunca contaba en valor_ejecutado ni en cuentas de cobro.
  const itemsParaAvance = [...items, ...otrosies.filter(o => o.estado === 'aprobado').flatMap(o =>
    o.items.map(it => ({ ...it, id: `ot${o.numero}:${it.id || it.codigo || ''}`,
                         descripcion: `[Otrosí ${o.numero}] ${it.descripcion}` })))]

  // Agrupar items por capitulo
  const grupos = {}
  items.forEach((it, idx) => {
    const cap = it.capitulo || 'OTROS'
    if (!grupos[cap]) grupos[cap] = []
    grupos[cap].push({ ...it, _idx: idx })
  })

  // Contenido del panel de herramientas — compartido: sidebar fija (desktop) y drawer (movil)
  const panelHerramientas = (
    <div className="p-3 space-y-1">
              {!esPublico && (
                <button onClick={() => {
                          setShowPanel(false); setShowDisenos(true)
                          disenosAPI.listar(id).then(r => setDisenos(r.disenos || [])).catch(() => {})
                        }}
                        className="w-full flex items-start gap-2.5 p-2 rounded-xl hover:bg-slate-50 text-left">
                  <span className="text-lg">🎨</span>
                  <span>
                    <span data-testid="menu-disenos" className="block text-sm font-semibold text-slate-700">Diseños</span>
                    <span className="block text-[10px] text-slate-400">Renders y planos — tu cliente los ve y comenta</span>
                  </span>
                </button>
              )}
              {!esPublico && eventos?.total_vistas > 0 && (
                <p className="text-[11px] text-blue-600 bg-blue-50 rounded-lg px-3 py-2 mb-2">
                  👁 {eventos.total_vistas} vista{eventos.total_vistas !== 1 ? 's' : ''} del cliente
                  {eventos?.aceptado && ' · ✓ contrato firmado'}
                </p>
              )}

              {(esPublico || ['aceptado', 'entrega_solicitada', 'terminado'].includes(p.estado)) ? (
                <>
                  <p className="text-[9px] text-slate-400 uppercase font-bold px-1 pt-1">Ejecución</p>
                  {(p.estado === 'aceptado' || (esPublico && p.estado !== 'terminado')) && (
                    <button onClick={() => {
                              setShowPanel(false); setShowAvances(true)
                              avancesAPI.listar(id).then(res => {
                                setAvances(res.avances || [])
                                setValorTotalDirecto(res.valor_total_directo || 0)
                                const ultimo = (res.avances || [])[0]
                                const map = {}
                                if (ultimo?.items) ultimo.items.forEach(it => { map[it.id] = it.pct })
                                setAvanceItems(map)
                              }).catch(() => {})
                            }}
                            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-amber-50 text-left">
                      <span className="text-lg">🏗️</span>
                      <span><span className="block text-sm font-semibold text-slate-700">Avances</span>
                      <span className="block text-[10px] text-slate-400">% por actividad — tu cliente lo ve en vivo</span></span>
                    </button>
                  )}
                  <button onClick={() => {
                            setShowPanel(false); setShowGastos(true)
                            gastosAPI.listar(id).then(setGastosData).catch(e => toast.error(e.message))
                          }}
                          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-slate-50 text-left">
                    <span className="text-lg">💸</span>
                    <span><span className="block text-sm font-semibold text-slate-700">Gastos</span>
                    <span className="block text-[10px] text-slate-400">Utilidad real con semáforo — privado</span></span>
                  </button>
                  <button onClick={() => {
                            setShowPanel(false); setShowCobros(true); setLiquidacion(null)
                            cuentasAPI.listar(id).then(setCobrosData).catch(e => toast.error(e.message))
                            avancesAPI.listar(id).then(res => setAvances(res.avances || [])).catch(() => {})
                          }}
                          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-emerald-50 text-left">
                    <span className="text-lg">💵</span>
                    <span><span className="block text-sm font-semibold text-slate-700">Cobros</span>
                    <span className="block text-[10px] text-slate-400">Cuentas, abonos y retegarantía</span></span>
                  </button>
                  {(['aceptado', 'entrega_solicitada'].includes(p.estado) || (esPublico && p.estado !== 'terminado')) && (
                    <button onClick={() => { setShowPanel(false); setShowOtrosi(true) }}
                            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-amber-50 text-left">
                      <span className="text-lg">➕</span>
                      <span className="flex-1"><span className="block text-sm font-semibold text-slate-700">Adicionales
                        {otrosies.filter(o => o.estado === 'aprobado').length > 0 &&
                          <span className="ml-1.5 text-[9px] font-bold bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded-full">{otrosies.filter(o => o.estado === 'aprobado').length} {esPublico ? 'aprobado' : 'firmado'}{otrosies.filter(o => o.estado === 'aprobado').length !== 1 ? 's' : ''}</span>}
                      </span>
                      <span className="block text-[10px] text-slate-400">Trabajo extra con otrosí firmado</span></span>
                    </button>
                  )}
                  {esPublico && (
                    <button onClick={() => {
                              setShowPanel(false); setShowCronograma(true)
                              cronogramaAPI.obtener(id).then(d => { setCronoData(d); setCronoFilas(d.filas || []) }).catch(e => toast.error(e.message))
                            }}
                            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-sky-50 text-left">
                      <span className="text-lg">📅</span>
                      <span className="flex-1"><span className="block text-sm font-semibold text-slate-700">Cronograma</span>
                      <span className="block text-[10px] text-slate-400">Diagrama de Gantt — solo obra pública</span></span>
                    </button>
                  )}

                  <p className="text-[9px] text-slate-400 uppercase font-bold px-1 pt-2">Cierre</p>
                  {esPublico && p.estado !== 'terminado' && (
                    <button onClick={async () => {
                              if (!(await confirmarDialogo({ titulo: '🏁 ¿Terminar el contrato?',
                                mensaje: '• El proyecto pasa a TERMINADO\n• Podrás liberar la retegarantía acumulada\n• La bitácora del Seguimiento queda como historial',
                                confirmar: 'Terminar contrato' }))) return
                              try {
                                const d = await proyectosAPI.terminar(id)
                                setP(d); setShowPanel(false)
                                toast.success('Contrato terminado — ya puedes liberar la retegarantía 🔓')
                              } catch (e2) { toast.error(e2.message) }
                            }}
                            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-violet-50 text-left">
                      <span className="text-lg">🏁</span>
                      <span><span className="block text-sm font-semibold text-slate-700">Terminar y liquidar</span>
                      <span className="block text-[10px] text-slate-400">Cierra el contrato y libera la retegarantía</span></span>
                    </button>
                  )}
                  {!esPublico && p.estado === 'aceptado' && (
                    <button onClick={async () => {
                              if (!(await confirmarDialogo({ titulo: '📦 ¿Solicitar la entrega de la obra?',
                                mensaje: '• Tu cliente verá: "El contratista reporta la obra terminada"\n• Al confirmar, firmará el Acta de Entrega\n• Si hay pendientes, te los reporta y la obra continúa',
                                confirmar: 'Solicitar entrega' }))) return
                              try {
                                const d = await proyectosAPI.actualizar(id, { estado: 'entrega_solicitada' })
                                setP(d); setShowPanel(false)
                                toast.success('Entrega solicitada — avísale a tu cliente')
                                avisarCliente(`Hola! La obra "${p.nombre}" está terminada 🏁 Por favor confirma el recibido a satisfacción aquí:`)
                              } catch (e2) { toast.error(e2.message) }
                            }}
                            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-violet-50 text-left">
                      <span className="text-lg">🤝</span>
                      <span><span className="block text-sm font-semibold text-slate-700">Solicitar entrega</span>
                      <span className="block text-[10px] text-slate-400">El cliente firma el acta bilateral</span></span>
                    </button>
                  )}
                  {p.estado === 'terminado' && p.share_token && (
                    <a href={`/api/share/publico/${p.share_token}/acta.pdf`} target="_blank" rel="noreferrer"
                       className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-slate-50 text-left">
                      <span className="text-lg">📄</span>
                      <span><span className="block text-sm font-semibold text-slate-700">Acta de Entrega</span>
                      <span className="block text-[10px] text-slate-400">PDF con las dos firmas</span></span>
                    </a>
                  )}
                </>
              ) : (
                <p className="text-[11px] text-slate-400 bg-slate-50 rounded-xl p-3">
                  🔒 Las herramientas de obra (avances, gastos, cobros, adicionales) se activan cuando
                  tu cliente <strong>firme el contrato</strong> desde su enlace.
                </p>
              )}

              <p className="text-[9px] text-slate-400 uppercase font-bold px-1 pt-2">Exportar</p>
              <div className="flex gap-2 px-1">
                <button data-testid="btn-export-excel" onClick={() => { setShowPanel(false); exportar('excel') }}
                        className="flex-1 flex items-center justify-center gap-1.5 border border-slate-200 rounded-xl py-2 text-xs font-medium text-emerald-600 hover:bg-emerald-50">
                  <FileSpreadsheet className="w-3.5 h-3.5" /> Excel
                </button>
                <button onClick={() => { setShowPanel(false); exportar('pdf') }}
                        className="flex-1 flex items-center justify-center gap-1.5 border border-slate-200 rounded-xl py-2 text-xs font-medium text-red-500 hover:bg-red-50">
                  <FileText className="w-3.5 h-3.5" /> PDF
                </button>
              </div>
              <button onClick={() => { setShowPanel(false); exportar('apus') }}
                      data-testid="btn-export-apus" className="w-full mt-1.5 mx-1 flex items-center justify-center gap-1.5 border border-violet-200 rounded-xl py-2 text-xs font-bold text-violet-600 hover:bg-violet-50"
                      style={{ width: 'calc(100% - 8px)' }}>
                📑 APUs detallados (anexo de propuesta)
              </button>
              <p className="text-[9px] text-slate-400 px-1 mt-1 text-center">
                {nAnalizados} de {items.length} ítems con análisis completo
                {nAnalizados < items.length && ' — constrúyelos por insumos 🧱 para una propuesta 100% sustentada'}
              </p>
              <button onClick={async () => {
                        setShowPanel(false)
                        try {
                          toast.loading('Consolidando insumos...', { id: 'exp2' })
                          const d = await exportarAPI.explosion({ proyecto_id: parseInt(id) })
                          toast.dismiss('exp2')
                          setExplosionData(d); setShowExplosion(true)
                        } catch (e2) { toast.error(e2.response?.data?.detail || e2.message, { id: 'exp2' }) }
                      }}
                      data-testid="btn-export-explosion" className="w-full mt-1.5 mx-1 flex items-center justify-center gap-1.5 border border-amber-200 rounded-xl py-2 text-xs font-bold text-amber-700 hover:bg-amber-50"
                      style={{ width: 'calc(100% - 8px)' }}>
                🧱 Lista de materiales (explosión de insumos)
              </button>
            </div>
  )

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
                {' · '}{p.sector === 'publico' ? ('🏛️ ' + (p.entidad_nombre || 'Sin entidad')) : (p.cliente_nombre || 'Sin cliente')}
                {' · '}{p.actualizado ? new Date(p.actualizado).toLocaleDateString('es-CO') : ''}
                {' · '}{sinRed ? (navigator.onLine === false ? '⚠️ Sin conexión — reintentando' : '⏳ Servidor lento — reintentando') : guardando ? 'Guardando...' : 'Guardado ✓'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {eventos?.total_vistas > 0 && (
              <span className="hidden sm:flex items-center gap-1 text-xs text-blue-600 bg-blue-50 px-2.5 py-1.5 rounded-full font-medium">
                <Eye className="w-3 h-3" /> {eventos.total_vistas} vista{eventos.total_vistas !== 1 ? 's' : ''}
              </span>
            )}
            {p.estado === 'terminado' && (
              <span className="flex items-center gap-1 text-xs text-slate-600 bg-slate-100 px-2.5 py-1.5 rounded-full font-medium">
                🏁 Terminada
              </span>
            )}
            {p.estado !== 'terminado' && eventos?.aceptado && (
              <span className="flex items-center gap-1 text-xs text-emerald-700 bg-emerald-50 px-2.5 py-1.5 rounded-full font-medium">
                <CheckCircle2 className="w-3 h-3" /> {esPublico ? '🏗️ En ejecución' : 'Aceptado'}
              </span>
            )}
            {p.estado !== 'terminado' && !eventos?.aceptado && esPublico && p.estado === 'aceptado' && (
              <span className="flex items-center gap-1 text-xs text-emerald-700 bg-emerald-50 px-2.5 py-1.5 rounded-full font-medium">
                🏗️ En ejecución
              </span>
            )}
            {p.estado === 'entrega_solicitada' && (
              <span className="hidden sm:inline text-xs bg-violet-100 text-violet-700 px-2.5 py-1.5 rounded-full font-medium">
                🤝 Esperando al cliente
              </span>
            )}
            {p.estado === 'terminado' && calificacion?.respondida && (
              <span className="flex items-center gap-1 text-xs text-amber-600 bg-amber-50 px-2.5 py-1.5 rounded-full font-medium"
                    title={calificacion.comentario || ''}>
                ⭐ {calificacion.estrellas}/5
              </span>
            )}
            <button onClick={() => setShowPanel(true)}
                    className="relative flex lg:hidden items-center gap-1.5 border border-slate-300 text-slate-700 text-sm font-medium px-3 py-2 rounded-xl transition hover:bg-slate-50"
                    data-testid="btn-herramientas" title="Herramientas de la obra">
              🛠️ <span className="hidden sm:inline">Obra</span>
              {!['borrador', 'enviado', 'visto', 'rechazado'].includes(p.estado) && (
                <span className="absolute -top-1 -right-1 w-2 h-2 bg-emerald-500 rounded-full" />
              )}
            </button>
            <button onClick={() => setShowPreview(true)}
                    className="flex items-center gap-1.5 border border-slate-200 hover:border-navy-300 text-slate-600 text-sm font-medium px-3 py-2 rounded-xl transition"
                    title="Ver como lo verá tu cliente">
              <Eye className="w-4 h-4" /> <span className="hidden sm:inline">Ver</span>
            </button>
            <button onClick={() => { cargarProveedores(); setShowProveedores(true) }}
                    className="flex items-center gap-1.5 border border-slate-200 hover:border-emerald-300 text-slate-600 text-sm font-medium px-3 py-2 rounded-xl transition"
                    title="Mis proveedores y sus precios">
              🏪 <span className="hidden sm:inline">Proveedores</span>
            </button>
            {esPublico && (
            <button onClick={async () => {
                      try { setBalanceData(await proyectosAPI.balance(id)); setShowBalance(true) }
                      catch (e) { toast.error(e.message) }
                    }}
                    className="flex items-center gap-1.5 border border-slate-200 hover:border-navy-300 text-slate-600 text-sm font-medium px-3 py-2 rounded-xl transition">
              📊 <span className="hidden sm:inline">Balance</span>
            </button>
            )}
            {esPublico && (
            <button onClick={async () => {
                      try {
                        const [bal, cts, avs] = await Promise.all([
                          proyectosAPI.balance(id),
                          cuentasAPI.listar(id),
                          avancesAPI.listar(id).catch(() => []),
                        ])
                        setSeguimiento({ balance: bal, cuentas: cts.cuentas || cts || [], avancesList: avs.avances || avs || [] })
                        setShowSeguimiento(true)
                      } catch (e) { toast.error(e.message) }
                    }}
                    className="flex items-center gap-1.5 bg-navy-600 hover:bg-navy-700 text-white text-sm font-medium px-4 py-2 rounded-xl transition">
              📋 <span className="hidden sm:inline">Seguimiento</span>
            </button>
            )}
            {!esPublico && (
            <button onClick={compartir}
                    className="flex items-center gap-1.5 bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-medium px-4 py-2 rounded-xl transition">
              <MessageCircle className="w-4 h-4" /> <span className="hidden sm:inline">WhatsApp</span>
            </button>
            )}
          </div>
        </div>
      </header>

      {/* ⚠️ PENDIENTES REPORTADOS POR EL CLIENTE (la entrega fue devuelta) */}
      {!esPublico && (p?.pendientes_reportados || []).length > 0 && p?.estado === 'aceptado' && (
        <div className="max-w-5xl mx-auto px-4 mt-3">
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4">
            <p className="text-xs font-bold text-amber-700 mb-1.5">⚠️ Tu cliente devolvió la entrega con pendientes:</p>
            {p.pendientes_reportados.map((pd, i) => (
              <div key={i} className="text-sm text-slate-700 bg-white rounded-xl px-3 py-2 mb-1.5 ring-1 ring-amber-100">
                “{pd.detalle}”
                <span className="block text-[10px] text-slate-400 mt-0.5">{pd.fecha}{pd.precio_viejo && <strong className="text-amber-600 ml-1">⚠ hace {Math.round(pd.edad_dias / 30)} meses — actualízalo</strong>}</span>
              </div>
            ))}
            <p className="text-[11px] text-amber-600">Resuélvelos, registra el avance y vuelve a solicitar la entrega 🤝</p>
          </div>
        </div>
      )}


      {/* Drawer de herramientas — SOLO movil (en desktop la sidebar es fija) */}
      {showPanel && (
        <div className="fixed inset-0 z-50 flex lg:hidden bg-black/30" onClick={() => setShowPanel(false)}>
          <div className="w-72 max-w-[85vw] bg-white h-full shadow-2xl overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="px-4 py-3 border-b border-slate-100 flex justify-between items-center sticky top-0 bg-white z-10">
              <div>
                <p className="font-bold text-slate-800 text-sm">🛠️ Herramientas</p>
                <p className="text-[10px] text-slate-400 truncate max-w-[190px]">{p.numero} · {p.nombre}</p>
              </div>
              <button onClick={() => setShowPanel(false)}><X className="w-4 h-4 text-slate-400" /></button>
            </div>
            {panelHerramientas}
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto lg:flex lg:items-start lg:gap-3 lg:px-4">
        {/* Sidebar fija de herramientas — desktop */}
        <aside className="hidden lg:block w-60 shrink-0 sticky top-[70px] max-h-[calc(100vh-84px)] overflow-y-auto pt-5">
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm pb-1">
            <p className="px-4 pt-3 text-xs font-bold text-slate-700">🛠️ Herramientas</p>
            {panelHerramientas}
          </div>
        </aside>

      <main className="flex-1 min-w-0 max-w-6xl mx-auto px-4 py-5">
        {soloLectura && (
          <div className="flex items-center gap-3 bg-slate-100 border border-slate-200 rounded-xl p-3 mb-4">
            <span className="text-xl">🔒</span>
            <p className="flex-1 text-xs text-slate-600">
              <strong data-testid="banner-terminado" className="text-slate-800">Proyecto terminado — solo lectura.</strong>{' '}
              El historial queda intacto como evidencia (actas, cuentas, bitácora).
              Para una obra nueva con este mismo presupuesto, duplícalo.
            </p>
            <button data-testid="btn-duplicar-terminado" onClick={async () => {
                      const nombre = await pedirTexto({ titulo: '📄 Duplicar proyecto',
                        mensaje: 'La copia es 100% independiente del original.',
                        valorInicial: `${p.nombre} (copia)`, confirmar: 'Crear copia' })
                      if (nombre === null) return
                      try {
                        const copia = await proyectosAPI.duplicar(id, { nombre: nombre.trim() })
                        toast.success(`Copia creada: "${copia.nombre}" — lista para editar`)
                        nav(`/editor/${copia.id}`); window.location.reload()
                      } catch (e2) { toast.error(e2.response?.data?.detail || e2.message) }
                    }}
                    className="shrink-0 px-3 py-2 rounded-xl bg-navy-600 text-white text-xs font-bold hover:bg-navy-700">
              📄 Duplicar proyecto
            </button>
          </div>
        )}
        {selladoUI && !soloLectura && (
          <div className="flex items-center gap-3 bg-amber-50 border border-amber-200 rounded-xl p-3 mb-4">
            <span className="text-xl">✍️</span>
            <p className="flex-1 text-xs text-slate-700">
              <strong data-testid="banner-firmado" className="text-slate-800">Este contrato ya está firmado.</strong>{' '}
              Las cantidades y precios de la tabla quedan fijas — es lo que el cliente aceptó.
              Para trabajo nuevo o extra, usá <strong>Adicionales</strong>: queda registrado con su propia
              firma, sin tocar el contrato original.
            </p>
            <button data-testid="btn-ir-adicionales" onClick={() => setShowOtrosi(true)}
                    className="shrink-0 px-3 py-2 rounded-xl bg-amber-600 text-white text-xs font-bold hover:bg-amber-700">
              ➕ Ir a Adicionales
            </button>
          </div>
        )}
        {tipEditor && (
          <div className="flex items-start gap-2 bg-navy-50 border border-navy-100 rounded-xl p-3 mb-4 text-[11px] text-navy-700">
            <span className="text-base">💡</span>
            <p className="flex-1">
              <strong>Así se cotiza aquí:</strong> 1️⃣ Busca actividades en la base APU (el botón grande de abajo) →
              2️⃣ ajusta cantidades con la calculadora 📐 → 3️⃣ tu AIU e IVA se configuran al final de la tabla.
            </p>
            <button onClick={() => { localStorage.setItem('tip_editor', '1'); setTipEditor(false) }}
                    className="text-navy-400 font-bold px-1">✕</button>
          </div>
        )}
        {tipObra && (
          <div className="flex items-start gap-2 bg-emerald-50 border border-emerald-100 rounded-xl p-3 mb-4 text-[11px] text-emerald-700">
            <span className="text-base">🏗️</span>
            <p className="flex-1">
              <strong>¡Obra ganada!</strong> Se activaron tus herramientas de ejecución:
              🏗️ Avances (informes al cliente) · 💸 Gastos (utilidad real) · 💵 Cobros (cuentas con amortización de anticipo).
            </p>
            <button onClick={() => { localStorage.setItem('tip_obra', '1'); setTipObra(false) }}
                    className="text-emerald-400 font-bold px-1">✕</button>
          </div>
        )}
        {/* Boton agregar actividades — oculto tambien en firmado, no solo terminado:
            agregar un item directo a un contrato ya aceptado siempre lo rechaza el
            backend (400, correcto por diseno) — mejor no dejar llegar hasta ahi. */}
        {!selladoUI && (
        <button onClick={() => setShowBuscador(true)}
                className="w-full flex items-center gap-3 bg-white border-2 border-dashed border-slate-300 hover:border-navy-400 rounded-xl p-4 text-slate-500 hover:text-navy-600 transition mb-5">
          <Search className="w-5 h-5" />
          <span data-testid="abrir-buscador" className="font-medium">Buscar actividades en la base APU 2026...</span>
        </button>
        )}

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
                        {desgloseDe(it) && (
                          <button data-testid="chip-analisis" onClick={() => abrirAnalisis(it)}
                                  className={`text-[10px] font-bold rounded-full px-2 py-0.5 transition ${analisisAbierto === it._idx ? 'bg-violet-600 text-white' : 'bg-violet-50 text-violet-600 hover:bg-violet-100'}`}
                                  title="Este ítem entra ESPECIFICADO al anexo de APUs">
                            🔬 Análisis {analisisAbierto === it._idx ? '▲' : '▼'}
                          </button>
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
                        <input type="number" disabled={selladoUI} step="any" min="0" value={it.cantidad}
                               onChange={e => actualizarItem(it._idx, 'cantidad', e.target.value)}
                               className="w-20 text-right text-sm border border-slate-200 rounded-lg px-2 py-1.5 focus:border-navy-400 outline-none" />
                        <p className="text-[10px] text-slate-400 mt-0.5 text-center">{it.unidad}</p>
                      </div>
                      <span className="text-slate-300">×</span>
                      <div className="text-right">
                        <input type="number" disabled={selladoUI} step="any" min="0" value={it.precio_unitario}
                               onChange={e => actualizarItem(it._idx, 'precio_unitario', e.target.value)}
                               className="w-28 text-right text-sm border border-slate-200 rounded-lg px-2 py-1.5 focus:border-navy-400 outline-none" />
                        <p className="text-[10px] text-slate-400 mt-0.5 text-center">precio unit.</p>
                      </div>
                      <div className="w-28 text-right font-semibold text-sm text-slate-800">
                        {COP((parseFloat(it.cantidad) || 0) * (parseFloat(it.precio_unitario) || 0))}
                      </div>
                      {!selladoUI && (
                      <button onClick={() => eliminarItem(it._idx)} className="p-1.5 hover:bg-red-50 rounded-lg">
                        <Trash2 className="w-3.5 h-3.5 text-slate-300 hover:text-red-500" />
                      </button>
                      )}
                    </div>
                  </div>

                  {/* Calculadora de cantidades */}
                  {analisisAbierto === it._idx && anEdit && (() => {
                    const _in = "w-full text-right text-[10px] border border-violet-200 rounded px-1 py-0.5 bg-white outline-none focus:border-violet-400"
                    const _upd = (k, i2, campo, v) => setAnEdit(prev => {
                      const n = { ...prev }
                      // Campos de % se defienden solos (misma medicina que deducciones)
                      let vv = v
                      if (campo === 'herramienta_pct') vv = Math.max(0, Math.min(30, parseFloat(v) || 0))
                      if (campo === 'desperdicio_pct') vv = Math.max(0, Math.min(50, parseFloat(v) || 0))
                      if (k === 'insumo') { n.insumos = prev.insumos.map((x, j) => j === i2 ? { ...x, [campo]: vv } : x) }
                      else n[campo] = vv
                      return n
                    })
                    const _num2 = (v) => parseFloat(v) || 0
                    const _prevMat = anEdit.insumos.reduce((s, x) => s + _num2(x.cantidad) * _num2(x.precio) * (1 + _num2(x.desperdicio_pct) / 100), 0)
                    const _prevTot = Math.round(_prevMat + _num2(anEdit.mano_obra) + _num2(anEdit.mano_obra) * _num2(anEdit.herramienta_pct) / 100 + _num2(anEdit.transporte))
                    return (
                      <div className="px-3 pb-3 bg-violet-50/60">
                        <div className="pt-2 text-[10px]">
                          <p className="font-bold text-violet-700 mb-1">🔬 Juega con el análisis — el servidor recalcula y todo se actualiza (ítem, totales, anexo y lista de materiales):</p>
                          <div className="bg-white rounded-lg border border-violet-100 overflow-hidden">
                            <div className="grid grid-cols-12 gap-1 px-2 py-1 bg-violet-600 text-white font-bold">
                              <span className="col-span-5">1. MATERIALES</span><span>Und</span><span className="text-right">Cant.</span><span className="text-right">Desp.%</span><span className="col-span-2 text-right">Vr. unit.</span><span className="col-span-2 text-right">Parcial</span>
                            </div>
                            {anEdit.insumos.map((ins, k) => (
                              <div key={k} className="grid grid-cols-12 gap-1 px-2 py-1 border-t border-violet-50 text-slate-600 items-center">
                                <span className="col-span-5 truncate" title={ins.nombre}>{ins.nombre}</span>
                                <span>{ins.unidad}</span>
                                <input type="number" disabled={soloLectura} step="any" min="0" value={ins.cantidad} onChange={e => _upd('insumo', k, 'cantidad', e.target.value)} className={_in} />
                                <input type="number" disabled={soloLectura} step="any" min="0" max="50" value={ins.desperdicio_pct || 0} onChange={e => _upd('insumo', k, 'desperdicio_pct', e.target.value)} className={_in} />
                                <input type="number" disabled={soloLectura} step="any" min="0" value={ins.precio} onChange={e => _upd('insumo', k, 'precio', e.target.value)} className={`${_in} col-span-2`} />
                                <span className="col-span-2 text-right">{COP(_num2(ins.cantidad) * _num2(ins.precio) * (1 + _num2(ins.desperdicio_pct) / 100))}</span>
                              </div>
                            ))}
                            <div className="grid grid-cols-12 gap-1 px-2 py-1 border-t border-violet-50 text-slate-700 items-center">
                              <span className="col-span-8">2. Mano de obra (por {it.unidad})</span>
                              <input type="number" disabled={soloLectura} step="any" min="0" value={anEdit.mano_obra} onChange={e => _upd(null, null, 'mano_obra', e.target.value)} className={`${_in} col-span-2`} />
                              <span className="col-span-2 text-right">{COP(_num2(anEdit.mano_obra))}</span>
                            </div>
                            <div className="grid grid-cols-12 gap-1 px-2 py-1 border-t border-violet-50 text-slate-700 items-center">
                              <span className="col-span-8">3. Herramienta menor — <strong>% de la MO</strong> (0-30)</span>
                              <div className="col-span-2 flex items-center gap-0.5">
                                <input type="number" disabled={soloLectura} step="any" min="0" max="30" value={anEdit.herramienta_pct} onChange={e => _upd(null, null, 'herramienta_pct', e.target.value)} className={_in} />
                                <span className="text-violet-500 font-bold">%</span>
                              </div>
                              <span className="col-span-2 text-right">{COP(_num2(anEdit.mano_obra) * _num2(anEdit.herramienta_pct) / 100)}</span>
                            </div>
                            <div className="grid grid-cols-12 gap-1 px-2 py-1 border-t border-violet-50 text-slate-700 items-center">
                              <span className="col-span-8">4. Transporte (por {it.unidad}) 🚚</span>
                              <input type="number" disabled={soloLectura} step="any" min="0" value={anEdit.transporte || 0} onChange={e => _upd(null, null, 'transporte', e.target.value)} className={`${_in} col-span-2`} />
                              <span className="col-span-2 text-right">{COP(_num2(anEdit.transporte))}</span>
                            </div>
                            <div className="grid grid-cols-12 gap-1 px-2 py-1 border-t border-violet-200 bg-violet-100 font-black text-violet-800">
                              <span className="col-span-10">PRECIO UNITARIO ANALIZADO (previo)</span><span className="col-span-2 text-right">{COP(_prevTot)}</span>
                            </div>
                          </div>
                          <p className="text-slate-400 mt-1">💡 Herramienta es un <strong>porcentaje</strong> de la mano de obra (práctica estándar 3-10%). Si lo tuyo es un flete en <strong>pesos</strong>, ese va en la fila 4 · Transporte 🚚.</p>
                          <div className="flex gap-2 mt-2 items-center">
                            <button disabled={anGuardando} onClick={() => recalcularAnalisis(it, false)}
                                    data-testid="btn-guardar-apu" className="flex-1 py-1.5 rounded-lg border border-violet-300 text-violet-700 font-bold hover:bg-violet-100 disabled:opacity-50">
                              💾 Recalcular y guardar el APU
                            </button>
                            <InfoTip texto="Guarda la receta en tu BIBLIOTECA (Mis APUs) con el precio recalculado por el servidor. Este presupuesto NO cambia — útil si ya enviaste la cotización y solo quieres afinar tu recetario para futuras obras." />
                            {!soloLectura && !['aceptado', 'entrega_solicitada'].includes(p.estado) && (
                              <>
                              <button disabled={anGuardando} onClick={() => recalcularAnalisis(it, true)}
                                      data-testid="btn-aplicar-apu" className="flex-1 py-1.5 rounded-lg bg-violet-600 text-white font-bold hover:bg-violet-700 disabled:opacity-50">
                                ⚡ Recalcular y APLICAR al ítem
                              </button>
                              <InfoTip texto="Hace lo mismo que guardar Y ADEMÁS pone el precio analizado en ESTE ítem. En cadena se actualizan: el total del presupuesto, el AIU, la incidencia por capítulos, el anexo de APUs y la lista de materiales. Un solo dato madre — nada se digita dos veces. (Si el ítem tenía descuento de lista, se retira.)" />
                              </>
                            )}
                          </div>
                          {Math.round(_prevTot) !== Math.round(_num2(it.precio_unitario)) && (
                            <p className="text-amber-600 mt-1">⚠️ El ítem está a {COP(it.precio_unitario)} — "aplicar" lo actualiza al analizado{it.precio_lista ? ' (y retira su descuento de lista)' : ''}.
                              <InfoTip texto="La receta dice un precio y el presupuesto tiene otro — pasa cuando editas el análisis sin aplicar, o cuando ajustaste el precio a mano. No es error: puedes dejarlo así (el anexo lo anota como 'ajuste comercial del proponente') o pulsar ⚡ para sincronizarlos." />
                            </p>
                          )}
                        </div>
                      </div>
                    )
                  })()}
                  {calcAbierta === it._idx && tipoCalc(it.unidad) && (
                    <div className="px-3 pb-3 bg-blue-50/50">
                      <div className="flex items-end gap-2 flex-wrap pt-2">
                        <div>
                          <label className="text-[10px] text-blue-600 font-medium block mb-0.5"># Elementos</label>
                          <input type="number" disabled={soloLectura} step="1" min="1" placeholder="1"
                                 value={it.calc?.n ?? ''}
                                 onChange={e => actualizarCalc(it._idx, 'n', e.target.value)}
                                 className="w-20 text-sm border border-blue-200 rounded-lg px-2 py-1.5 bg-white outline-none focus:border-blue-400" />
                        </div>
                        <span className="text-blue-300 pb-2">×</span>
                        <div>
                          <label className="text-[10px] text-blue-600 font-medium block mb-0.5">Largo (m)</label>
                          <input type="number" disabled={soloLectura} step="any" min="0" placeholder="0.00"
                                 value={it.calc?.largo ?? ''}
                                 onChange={e => actualizarCalc(it._idx, 'largo', e.target.value)}
                                 className="w-24 text-sm border border-blue-200 rounded-lg px-2 py-1.5 bg-white outline-none focus:border-blue-400" />
                        </div>
                        {tipoCalc(it.unidad) !== 'lineal' && (
                          <>
                            <span className="text-blue-300 pb-2">×</span>
                            <div>
                              <label className="text-[10px] text-blue-600 font-medium block mb-0.5">{tipoCalc(it.unidad) === 'area' ? 'Ancho/Alto (m)' : 'Ancho (m)'}</label>
                              <input type="number" disabled={soloLectura} step="any" min="0" placeholder="0.00"
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
                              <input type="number" disabled={soloLectura} step="any" min="0" placeholder="0.00"
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
                      <input type="number" disabled={soloLectura} step="0.5" min="0" max="50" value={aiu[k]}
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
            {!aiu.aplicar && (
              <label className="flex items-start gap-2 mt-2 text-[11px] text-slate-600 cursor-pointer">
                <input type="checkbox" data-testid="check-con-iva" className="mt-0.5" checked={!!aiu.con_iva}
                       onChange={e2 => setAiuYGuardar({ ...aiu, con_iva: e2.target.checked })} />
                <span><strong className="text-slate-700">Responsable de IVA</strong> — factura 19% sobre el total del presupuesto.
                  Déjalo apagado si no eres responsable de IVA (régimen simple / persona natural).</span>
              </label>
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
                <input type="number" disabled={soloLectura} min="1" max="720" className="input !py-2 text-sm"
                       value={contrato.plazo_dias}
                       onChange={e => setContratoYGuardar({ ...contrato, plazo_dias: parseInt(e.target.value) || 45 })} />
              </div>
              <div>
                <label className="text-[10px] text-slate-400 block mb-1">Anticipo %</label>
                <input type="number" disabled={soloLectura} min="0" max="90" step="5" className="input !py-2 text-sm"
                       value={contrato.anticipo_pct}
                       onChange={e => setContratoYGuardar({ ...contrato, anticipo_pct: parseFloat(e.target.value) || 0 })} />
              </div>
              <div>
                <label className="text-[10px] text-slate-400 uppercase font-semibold">Retegarantía % <span className="normal-case">(opcional)</span></label>
                <input disabled={soloLectura} className="input !py-2" type="number" min="0" max="20"
                       value={contrato.retegarantia_pct || 0}
                       onChange={e => setContratoYGuardar({ ...contrato, retegarantia_pct: Math.max(0, Math.min(20, parseFloat(e.target.value) || 0)) })} />
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
            {esPublico && (
              <div className="mt-3 border-t border-slate-100 pt-3">
                <div className="flex items-center justify-between mb-1.5">
                  <p className="text-[10px] text-slate-400 uppercase font-semibold">
                    Deducciones de ley por acta 🏛️ <span className="normal-case">(la entidad las retiene de cada pago)</span>
                    <InfoTip texto="Aquí NO se descuenta nada todavía — solo configuras las reglas del contrato. Se aplican DESPUÉS, cada vez que generes un acta parcial: neto = corte − amortización del anticipo − retegarantía − ESTAS deducciones. Cada % se calcula sobre el valor del corte, línea por línea con redondeo a peso (igual que liquida la entidad). Así sabes desde HOY cuánta plata de verdad entra a tu caja en cada pago — sin sorpresas el día del giro." />
                  </p>
                  {(contrato.deducciones || []).length > 0 && (() => {
                    const totalDed = (contrato.deducciones || []).reduce((s, x) => s + (parseFloat(x.pct) || 0), 0)
                    return (
                      <span className={`text-[10px] font-black rounded-full px-2 py-0.5 ${totalDed > 50 ? 'bg-red-100 text-red-600' : 'bg-emerald-50 text-emerald-600'}`}>
                        Total {Math.round(totalDed * 10) / 10}% {totalDed > 50 ? '— máx 50%, NO se guarda' : 'de cada corte'}
                        <InfoTip texto={`De cada $1.000.000 que factures en un acta, la entidad te retendrá ~$${Math.round((contrato.deducciones || []).reduce((s, x) => s + (parseFloat(x.pct) || 0), 0) * 10000).toLocaleString('es-CO')} por estas deducciones (además del anticipo amortizado y la retegarantía). El NETO REAL lo ves calculado a peso en cada cuenta de cobro.`} />
                      </span>
                    )
                  })()}
                </div>
                {(contrato.deducciones || []).map((dd, i) => {
                  // 🕵️ Vigía semántico: el nombre y el número no pueden contradecirse
                  const nom = (dd.nombre || '').toLowerCase()
                  const pct = parseFloat(dd.pct) || 0
                  let alerta = null
                  if ((nom.includes('1106') || nom.includes('5%')) && pct !== 5)
                    alerta = { msg: `La contribución de la Ley 1106 es 5% FIJO — tienes ${pct}%`, fix: 5 }
                  else if (nom.includes('retefuente') && pct > 4)
                    alerta = { msg: `La retefuente de construcción real es ≈2% — ${pct}% no existe ni para honorarios`, fix: 2 }
                  else if (nom.includes('estampilla') && pct > 10)
                    alerta = { msg: `Las estampillas territoriales suelen sumar 2-8% — verifica tu contrato`, fix: null }
                  else if (!alerta && pct > 15)
                    alerta = { msg: `${pct}% es inusualmente alto para una deducción — verifica el contrato con la entidad`, fix: null }
                  return (
                  <div key={i} className="mb-1.5">
                  <div className="flex gap-1.5">
                    <input className="flex-1 text-xs border border-slate-200 rounded-lg px-2 py-1.5" value={dd.nombre}
                           onChange={e => setContratoYGuardar({ ...contrato, deducciones: contrato.deducciones.map((x, j) => j === i ? { ...x, nombre: e.target.value } : x) })} />
                    <input type="number" disabled={soloLectura} min="0" max="25" className={`w-16 text-xs border rounded-lg px-2 py-1.5 ${alerta ? 'border-amber-400 bg-amber-50' : 'border-slate-200'}`} value={dd.pct}
                           onChange={e => setContratoYGuardar({ ...contrato, deducciones: contrato.deducciones.map((x, j) => j === i ? { ...x, pct: Math.max(0, Math.min(25, parseFloat(e.target.value) || 0)) } : x) })} />
                    <button onClick={() => setContratoYGuardar({ ...contrato, deducciones: contrato.deducciones.filter((_, j) => j !== i) })}
                            className="text-slate-300 hover:text-red-400 px-1">×</button>
                  </div>
                  {alerta && (
                    <p className="text-[10px] text-amber-700 mt-0.5 flex items-center gap-1.5">
                      ⚠️ {alerta.msg}
                      {alerta.fix !== null && (
                        <button onClick={() => setContratoYGuardar({ ...contrato, deducciones: contrato.deducciones.map((x, j) => j === i ? { ...x, pct: alerta.fix } : x) })}
                                className="font-black text-emerald-700 underline">corregir a {alerta.fix}%</button>
                      )}
                    </p>
                  )}
                  </div>
                  )
                })}
                {(contrato.deducciones || []).length === 0 && (
                  <button onClick={() => setContratoYGuardar({ ...contrato, deducciones: [
                            { nombre: 'Contribución obra pública 5% (Ley 1106/2006)', pct: 5 },
                            { nombre: 'Estampillas territoriales', pct: 4 },
                            { nombre: 'Retefuente construcción', pct: 2 }] })}
                          className="text-xs font-medium text-navy-600">+ cargar las 3 típicas (5% + 4% + 2%) — ajusta las estampillas a tu territorio</button>
                )}
                {(contrato.deducciones || []).length > 0 && (
                  <button onClick={() => setContratoYGuardar({ ...contrato, deducciones: [...contrato.deducciones, { nombre: '', pct: 0 }] })}
                          className="text-xs font-medium text-navy-600">+ agregar deducción</button>
                )}
                {(contrato.deducciones || []).length > 0 && (
                  <p className="text-[10px] text-slate-400 mt-1.5">
                    📖 Referencia real: Ley 1106 = <strong>5% fijo</strong> · estampillas territoriales = 2-8% según
                    departamento/municipio (revisa tu contrato) · retefuente construcción ≈ <strong>2%</strong>.
                    Cada línea máx 25%, total máx 50% — como liquida la entidad, con redondeo por línea.
                  </p>
                )}
              </div>
            )}
            {totales && contrato.anticipo_pct > 0 && (
              <p className="text-[11px] text-slate-500 mt-2.5 bg-slate-50 rounded-lg p-2">
                Forma de pago: anticipo {contrato.anticipo_pct}% = <strong>{COP(totales.total * contrato.anticipo_pct / 100)}</strong>
                {' · '}saldo {100 - contrato.anticipo_pct}% = <strong>{COP(totales.total * (100 - contrato.anticipo_pct) / 100)}</strong>
                <InfoTip texto={`El anticipo te lo pagan al arrancar — pero no es tuyo todavía: se AMORTIZA en cada acta (a cada corte se le descuenta el ${contrato.anticipo_pct}% hasta devolverlo completo, con tope: jamás amortizas más de lo que te dieron). Junto con la retegarantía y las deducciones, así se calcula el NETO que de verdad recibes en cada pago.`} />
              </p>
            )}
          </div>
        )}
        {/* Colchón de seguridad: la barra fija de totales SIEMPRE tapa los ultimos
            ~64-90px del viewport. Sin este espacio de sobra al final de main, en
            pantallas cortas el ultimo contenido real (Contrato de obra, o cualquier
            seccion que termine siendo la ultima) puede quedar bajo la barra fija sin
            que nada haya scrolleado — no es un problema de timing, es geometria pura:
            content quieto en la franja fija. Un colchon fijo, siempre presente, hace
            que esa franja SIEMPRE caiga sobre este relleno vacio, nunca sobre algo
            clicable. Mas generoso que cualquier alto real del footer (incluso con el
            badge de descuento + AIU + IVA).
        */}
        <div className="h-32" aria-hidden="true" />
      </main>
      </div>

      {/* ── F3+F7: Análisis del presupuesto (incidencia) + Negociación ── */}
      {showAnalisis && totales?.capitulos?.length > 0 && (
        <div className="fixed bottom-16 left-0 right-0 z-40 px-4">
          <div className="max-w-6xl mx-auto bg-white rounded-2xl shadow-2xl border border-slate-200 p-4">
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs font-black text-slate-700">📊 Incidencia por capítulos
                <InfoTip texto="El % que pesa cada capítulo sobre el costo directo. Es lo primero que revisa un presupuestador con experiencia: si ESTRUCTURA pesa 3% en una casa nueva, algo falta. Úsalo para cazar errores gruesos antes de enviar." />
              </p>
              <button onClick={() => setShowAnalisis(false)} className="text-slate-400 text-xs">✕ cerrar</button>
            </div>
            <div className="max-h-44 overflow-y-auto space-y-1.5">
              {totales.capitulos.map(c => (
                <div key={c.capitulo} className="flex items-center gap-2">
                  <span className="text-[10px] text-slate-500 w-40 truncate" title={c.capitulo}>{c.capitulo}</span>
                  <div className="flex-1 h-3 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-navy-500 rounded-full" style={{ width: `${Math.min(100, c.pct)}%` }} />
                  </div>
                  <span className="text-[10px] font-bold text-slate-600 w-10 text-right">{c.pct}%</span>
                  <span className="text-[10px] text-slate-400 w-20 text-right">{COP(c.valor)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── F2: Lista de materiales (explosión de insumos) ── */}
      {showExplosion && explosionData && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={() => setShowExplosion(false)}>
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full p-5 max-h-[85vh] flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="flex items-start justify-between">
              <h3 className="font-black text-slate-800">🧱 Lista de materiales de la obra
                <InfoTip texto="El presupuesto habla en actividades; la ferretería vende insumos. Aquí están TODOS los materiales de la obra consolidados (con desperdicio incluido) y cruzados con tus precios negociados. Es tu lista de compras — y tu control de materiales." />
              </h3>
              <button onClick={() => setShowExplosion(false)} className="text-slate-400">✕</button>
            </div>
            <p className="text-[11px] text-slate-500 mt-1">
              {explosionData.items_explotados} actividades explotadas · {explosionData.n_insumos} insumos ·{' '}
              {explosionData.con_precio_negociado > 0 && <span className="text-emerald-600 font-semibold">{explosionData.con_precio_negociado} con precio de TU proveedor · </span>}
              desperdicio ya incluido
            </p>
            {explosionData.n_insumos === 0 ? (
              <div className="mt-4 bg-amber-50 border border-amber-100 rounded-xl p-4 text-xs text-amber-800">
                Ninguna actividad tiene desglose todavía. Construye tus APUs por insumos (🧱 el constructor)
                y esta lista se arma sola — cemento, arena y todo lo demás, sumado y con desperdicio.
              </div>
            ) : (
              <div className="mt-3 overflow-y-auto flex-1 border border-slate-100 rounded-xl">
                <div className="grid grid-cols-12 gap-1 px-3 py-2 bg-navy-700 text-white text-[10px] font-bold sticky top-0">
                  <span className="col-span-4">Insumo</span><span>Und</span><span className="text-right col-span-2">Cantidad</span><span className="text-right col-span-2">Precio</span><span className="text-right col-span-3">Subtotal</span>
                </div>
                {explosionData.insumos.map((i, k) => (
                  <div key={k} className="grid grid-cols-12 gap-1 px-3 py-2 border-t border-slate-50 text-[11px] text-slate-700 items-center">
                    <span className="col-span-4">
                      <span className="block truncate font-medium" title={i.nombre}>{i.nombre}</span>
                      {i.fuente_precio === 'mi_proveedor' && (
                        <span className="text-[9px] text-emerald-600">🏪 {i.proveedor} · {i.fecha_precio}</span>
                      )}
                      {i.en_items > 1 && <span className="text-[9px] text-slate-400"> · en {i.en_items} actividades</span>}
                    </span>
                    <span className="text-slate-400">{i.unidad}</span>
                    <span className="text-right col-span-2 font-semibold">{i.cantidad}</span>
                    <span className="text-right col-span-2">{i.precio ? COP(i.precio) : '—'}</span>
                    <span className="text-right col-span-3 font-semibold">{i.subtotal ? COP(i.subtotal) : '—'}</span>
                  </div>
                ))}
                <div className="grid grid-cols-12 gap-1 px-3 py-2 border-t border-slate-200 bg-slate-50 text-xs font-black text-slate-800">
                  <span className="col-span-9">TOTAL MATERIALES ESTIMADO</span>
                  <span className="text-right col-span-3">{COP(explosionData.total_estimado)}</span>
                </div>
              </div>
            )}
            {explosionData.items_sin_desglose > 0 && (
              <p className="text-[10px] text-amber-700 mt-2">
                ⚠️ {explosionData.items_sin_desglose} actividad(es) sin desglose no entran a la lista:{' '}
                {explosionData.sin_desglose.slice(0, 3).join('; ')}{explosionData.sin_desglose.length > 3 ? '…' : ''}
              </p>
            )}
            {explosionData.n_insumos > 0 && (
              <button onClick={async () => {
                        try {
                          const res = await exportarAPI.explosionExcel({ proyecto_id: parseInt(id) })
                          const url = URL.createObjectURL(res.data)
                          const a = document.createElement('a')
                          a.href = url; a.download = `${p.nombre.replace(/[^a-z0-9]/gi, '_')}_materiales.xlsx`
                          a.click(); URL.revokeObjectURL(url)
                        } catch (e2) { toast.error(e2.response?.data?.detail || e2.message) }
                      }}
                      className="mt-3 w-full py-2.5 rounded-xl bg-emerald-600 text-white text-sm font-bold hover:bg-emerald-700">
                📥 Descargar Excel — para llevar a la ferretería
              </button>
            )}
          </div>
        </div>
      )}

      {/* ── 🎨 DISEÑOS: renders/planos que el cliente ve y comenta ── */}
      {showDisenos && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={() => setShowDisenos(false)}>
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full p-5 max-h-[88vh] flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="flex items-start justify-between">
              <h3 className="font-black text-slate-800">🎨 Diseños del proyecto
                <InfoTip texto="Sube renders, planos fotografiados o moodboards (máx 12, se comprimen solos). Tu cliente los ve en su mismo enlace y puede comentar cada uno — tú respondes aquí. Cuando los abra, lo verás en la bitácora: cliente que mira diseños es cliente caliente." />
              </h3>
              <button onClick={() => setShowDisenos(false)} className="text-slate-400">✕</button>
            </div>
            {!soloLectura && (
              <label className="mt-3 flex items-center justify-center gap-2 border-2 border-dashed border-slate-300 hover:border-navy-400 rounded-xl py-3 text-sm text-slate-500 cursor-pointer">
                📤 Subir diseño (JPG/PNG — se comprime solo)
                <input data-testid="input-diseno" type="file" accept="image/*" className="hidden"
                       onChange={async e => {
                         const file = e.target.files?.[0]
                         if (!file) return
                         const titulo = await pedirTexto({ titulo: '🎨 Título del diseño',
                           placeholder: 'Ej: Render cocina — opción 1', confirmar: 'Subir diseño' })
                         if (titulo === null) return
                         comprimirImagen(file).then(img =>
                           disenosAPI.crear(id, { titulo, imagen_b64: img })
                             .then(d => { setDisenos(prev => [...prev, d]); toast.success(!p.share_token
                                 ? 'Diseño guardado 🎨 — será visible cuando compartas el enlace con tu cliente'
                                 : ['aceptado', 'entrega_solicitada'].includes(p.estado)
                                   ? 'Diseño subido — tu cliente ya lo puede ver en su enlace 🎨'
                                   : 'Diseño subido 🎨 — quedó en tu propuesta; tu cliente lo verá cuando abra el enlace') })
                             .catch(e2 => toast.error(e2.response?.data?.detail || e2.message))
                         ).catch(() => toast.error('Imagen no válida'))
                         e.target.value = ''
                       }} />
              </label>
            )}
            <div className="mt-3 overflow-y-auto flex-1 grid grid-cols-1 sm:grid-cols-2 gap-3">
              {disenos.length === 0 && (
                <p className="col-span-2 text-xs text-slate-400 text-center py-6">
                  Sin diseños todavía. El cliente que VE su baño renderizado firma más rápido que el que ve un número.
                </p>
              )}
              {disenos.map(d => (
                <div key={d.id} className="border border-slate-100 rounded-xl overflow-hidden">
                  <img src={d.imagen_b64} alt={d.titulo} className="w-full h-36 object-cover" />
                  <div className="p-2">
                    <div className="flex items-center justify-between">
                      <p className="text-xs font-semibold text-slate-700 truncate">{d.titulo || 'Diseño'}</p>
                      {!soloLectura && (
                        <button onClick={async () => {
                                  if (!(await confirmarDialogo({ titulo: '¿Eliminar este diseño?',
                                    mensaje: 'Tu cliente dejará de verlo en su enlace.', peligro: true, confirmar: 'Eliminar' }))) return
                                  disenosAPI.eliminar(id, d.id)
                                    .then(() => setDisenos(prev => prev.filter(x => x.id !== d.id)))
                                    .catch(e2 => toast.error(e2.response?.data?.detail || e2.message))
                                }} className="text-slate-300 hover:text-red-400 text-xs">🗑</button>
                      )}
                    </div>
                    {(d.comentarios || []).map((cm, k) => (
                      <p key={k} className={`text-[10px] mt-1 rounded-lg px-2 py-1 ${cm.autor === 'cliente' ? 'bg-blue-50 text-blue-700' : 'bg-slate-50 text-slate-600'}`}>
                        <strong>{cm.autor === 'cliente' ? '💬 ' : '↩️ '}{cm.nombre}:</strong> {cm.texto}
                      </p>
                    ))}
                    <div className="flex gap-1 mt-1.5">
                      <input value={comentarioDiseno[d.id] || ''} placeholder="Responder..."
                             onChange={e => setComentarioDiseno(prev => ({ ...prev, [d.id]: e.target.value }))}
                             className="flex-1 text-[10px] border border-slate-200 rounded-lg px-2 py-1" />
                      <button onClick={() => {
                                const txt = (comentarioDiseno[d.id] || '').trim()
                                if (!txt) return
                                disenosAPI.comentar(id, d.id, txt).then(r => {
                                  setDisenos(prev => prev.map(x => x.id === d.id ? { ...x, comentarios: r.comentarios } : x))
                                  setComentarioDiseno(prev => ({ ...prev, [d.id]: '' }))
                                }).catch(e2 => toast.error(e2.response?.data?.detail || e2.message))
                              }}
                              className="text-[10px] font-bold text-navy-600 px-2">↩️</button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {showDescuento && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={() => setShowDescuento(false)}>
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-5" onClick={e => e.stopPropagation()}>
            <h3 className="font-black text-slate-800">💸 Descuento de negociación
              <InfoTip texto="El cliente pidió rebaja. En vez de dañar tus APUs uno a uno, este descuento se prorratea en todos los ítems y GUARDA el precio de lista: el PDF muestra 'valor de lista − descuento = precio pactado'. Tus análisis quedan honestos y el cliente ve cuánto ganó." />
            </h3>
            {totales?.descuento_valor > 0 ? (
              <div className="mt-3">
                <p className="text-sm text-slate-600">Descuento vigente: <strong className="text-emerald-600">{totales.descuento_pct}%</strong> — el cliente ahorra <strong>{COP(totales.descuento_valor)}</strong> (lista {COP(totales.subtotal_lista)}).</p>
                <button onClick={() => {
                          setItemsYGuardar(prev => prev.map(it => it.precio_lista
                            ? { ...it, precio_unitario: it.precio_lista, precio_lista: null } : it))
                          toast.success('Descuento retirado — precios de lista restaurados')
                          setShowDescuento(false)
                        }}
                        className="mt-3 w-full py-2.5 rounded-xl border border-slate-200 text-sm font-bold text-slate-600 hover:bg-slate-50">
                  Quitar descuento (volver a lista)
                </button>
              </div>
            ) : (
              <div className="mt-3">
                <label className="text-xs font-semibold text-slate-500">¿Qué % le rebajas al costo directo?</label>
                <div className="flex gap-2 mt-1.5">
                  <input type="number" disabled={soloLectura} min="0.1" max="30" step="0.1" data-testid="input-descuento" value={descuentoPct}
                         onChange={e => setDescuentoPct(e.target.value)} placeholder="Ej: 5"
                         className="flex-1 border border-slate-200 rounded-xl px-3 py-2 text-sm" />
                  <span className="self-center text-sm text-slate-400">%</span>
                </div>
                {parseFloat(descuentoPct) > 0 && totales && (
                  <p className="text-[11px] text-slate-500 mt-2 bg-emerald-50 rounded-lg p-2">
                    Nuevo directo ≈ <strong>{COP(Math.round(totales.subtotal_directo * (1 - parseFloat(descuentoPct) / 100)))}</strong>
                    {' '}· ahorro para el cliente ≈ <strong>{COP(Math.round(totales.subtotal_directo * parseFloat(descuentoPct) / 100))}</strong>
                  </p>
                )}
                <button onClick={() => {
                          const d = parseFloat(descuentoPct)
                          if (!d || d <= 0 || d > 30) { toast.error('Un descuento sano va entre 0.1% y 30%'); return }
                          setItemsYGuardar(prev => prev.map(it => {
                            const lista = parseFloat(it.precio_lista) || parseFloat(it.precio_unitario) || 0
                            return { ...it, precio_lista: lista, precio_unitario: Math.round(lista * (1 - d / 100)) }
                          }))
                          toast.success(`Descuento del ${d}% aplicado a todos los ítems 🤝`)
                          setShowDescuento(false); setDescuentoPct('')
                        }}
                        data-testid="btn-aplicar-descuento" className="mt-3 w-full py-2.5 rounded-xl bg-navy-600 text-white text-sm font-bold hover:bg-navy-700">
                  Aplicar descuento prorrateado
                </button>
              </div>
            )}
            <p className="text-[10px] text-slate-400 mt-3">Disponible antes de la firma/sello. Tras el sello, los cambios entran por adicionales.</p>
          </div>
        </div>
      )}

      {/* Barra de totales fija */}
      {totales && items.length > 0 && (
        <div className="fixed bottom-0 left-0 right-0 bg-navy-800 text-white z-40">
          <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between gap-4">
            <div className="flex gap-4 text-xs text-blue-200 overflow-x-auto items-center">
              <button onClick={() => setShowAnalisis(v => !v)} data-testid="btn-incidencia" title="Incidencia por capítulos"
                      className="whitespace-nowrap px-2 py-1 rounded-lg bg-navy-700 hover:bg-navy-600 font-bold">📊</button>
              {!['aceptado', 'entrega_solicitada', 'terminado'].includes(p.estado) && (
                <button onClick={() => setShowDescuento(true)} data-testid="btn-descuento" title="Descuento de negociación"
                        className="whitespace-nowrap px-2 py-1 rounded-lg bg-navy-700 hover:bg-navy-600 font-bold">💸</button>
              )}
              {totales.descuento_valor > 0 && (
                <span className="whitespace-nowrap text-emerald-300 font-bold">−{totales.descuento_pct}% ({COP(totales.descuento_valor)})</span>
              )}
              <span data-testid="total-directo" className="whitespace-nowrap">Directo: <strong className="text-white">{COP(totales.subtotal_directo)}</strong></span>
              {aiu.aplicar && <span className="whitespace-nowrap">AIU: <strong className="text-white">{COP(totales.aiu_total)}</strong></span>}
              <span className="whitespace-nowrap">IVA: <strong className="text-white">{COP(totales.iva)}</strong></span>
            </div>
            <div className="text-right shrink-0">
              <p className="text-[10px] text-blue-200 uppercase tracking-wide">Total</p>
              <p data-testid="total-obra" className="text-xl font-black">{COP(totales.total)}</p>
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
              <div className="flex gap-1.5 mt-3">
                {[['base', '📚 Base 2026'], ['mios', '⭐ Mis APUs']].map(([v, t]) => (
                  <button key={v} onClick={() => setFuenteApu(v)}
                          className={`text-xs font-bold px-3 py-1.5 rounded-lg transition ${fuenteApu === v ? 'bg-emerald-500 text-white' : 'bg-slate-100 text-slate-500'}`}>
                    {t}
                  </button>
                ))}
                {fuenteApu === 'mios' && (
                  <>
                  <button onClick={() => { setShowConstructor(true); setPreviewComp(null); setConstruyendo({ descripcion: '', unidad: 'm2', insumos: [], mano_obra: '', herramienta_pct: 5, transporte: '' }) }}
                          data-testid="btn-abrir-constructor" className="text-xs font-bold px-3 py-1.5 rounded-lg bg-navy-600 text-white ml-auto">
                    + Construir APU
                  </button>
                  <button onClick={() => { insumosAPI.catalogo().then(setCatalogo).catch(() => {}); setShowCatalogo(true) }}
                          className="text-xs font-bold px-3 py-1.5 rounded-lg bg-emerald-500 text-white">
                    📦 Catálogo
                  </button>
                  </>
                )}
              </div>
              <div className="flex gap-1.5 mt-2 overflow-x-auto pb-1" style={{ display: fuenteApu === 'base' ? 'flex' : 'none' }}>
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
                (fuenteApu === 'mios' ? misApus : resultados).map(apu => (
                  <button key={apu.id || apu.codigo} onClick={() => agregarItem(apu)}
                          className="w-full flex items-center gap-3 p-3 hover:bg-slate-50 rounded-xl text-left transition group">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-700 leading-snug">{apu.descripcion}</p>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        {fuenteApu === 'mios'
                          ? <>⭐ {apu.codigo || 'mío'}{apu.origen_base ? ` · de la base ${apu.origen_base}` : ''}{apu.desglose ? ' · compuesto' : ''}</>
                          : <>{apu.categoria} · {apu.codigo}</>}
                      </p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="text-sm font-semibold text-slate-800">{COP(apu.precio)}</p>
                      <p className="text-[10px] text-slate-400">/{apu.unidad}</p>
                    </div>
                    {fuenteApu === 'base' && (
                      <>
                      <span onClick={(e) => verDesgloseBase(apu, e)} title="Ver desglose: materiales, mano de obra, transporte"
                            className="text-[10px] font-bold text-violet-500 border border-violet-200 rounded-lg px-1.5 py-1 hover:bg-violet-50 shrink-0">👁</span>
                      <span onClick={(e) => duplicarComoMio(apu, e)} title="Duplicar como mío (editable)"
                            className="text-[10px] font-bold text-navy-500 border border-navy-200 rounded-lg px-1.5 py-1 hover:bg-navy-50 shrink-0">⧉</span>
                      </>
                    )}
                    <Plus className="w-4 h-4 text-slate-300 group-hover:text-navy-600 shrink-0" />
                  </button>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modal VISTA PREVIA del desglose — Base 2026, antes de agregar/duplicar */}
      {previewBase && (
        <div className="fixed inset-0 bg-black/40 z-[65] flex items-start justify-center p-4 pt-[8vh]" onClick={() => setPreviewBase(null)}>
          <div className="bg-white rounded-2xl p-5 w-full max-w-lg max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="flex items-start justify-between gap-3 mb-1">
              <h3 className="font-semibold text-slate-800 text-sm leading-snug">👁 {previewBase.descripcion}</h3>
              <button onClick={() => setPreviewBase(null)} className="shrink-0 text-slate-300 hover:text-slate-500"><X className="w-4 h-4" /></button>
            </div>
            <p className="text-[10px] text-slate-400 mb-3">Código {previewBase.codigo} · vista previa de solo lectura — para editarlo, duplícalo primero (⧉)</p>

            {previewBase.cargando ? (
              <p className="text-center text-xs text-slate-400 py-8">Cargando desglose...</p>
            ) : previewBase.error ? (
              <p className="text-center text-xs text-amber-600 bg-amber-50 rounded-xl py-6 px-3">
                Esta actividad no tiene desglose detallado disponible todavía — solo precio de referencia.
              </p>
            ) : previewBase.data && (
              <>
                <div className="bg-violet-50/60 rounded-xl border border-violet-100 overflow-hidden text-[11px]">
                  {previewBase.data.insumos.length > 0 && (
                    <>
                      <div className="grid grid-cols-12 gap-1 px-2 py-1.5 bg-violet-600 text-white font-bold">
                        <span className="col-span-5">Materiales / Equipo</span><span className="col-span-2">Und</span>
                        <span className="col-span-2 text-right">Cant.</span><span className="col-span-2 text-right">Parcial</span><span className="col-span-1"></span>
                      </div>
                      {previewBase.data.insumos.map((ins, k) => (
                        <div key={k} className="grid grid-cols-12 gap-1 px-2 py-1 border-t border-violet-100 text-slate-600 items-center bg-white">
                          <span className="col-span-5 truncate" title={ins.nombre}>{ins.nombre}</span>
                          <span className="col-span-2">{ins.unidad}</span>
                          <span className="col-span-2 text-right">{ins.cantidad}</span>
                          <span className="col-span-2 text-right font-medium">{COP(ins.parcial)}</span>
                          <button onClick={() => {
                                    setConstruyendo(c => ({ ...c, insumos: [...c.insumos, { nombre: ins.nombre, cantidad: ins.cantidad, precio: ins.precio }] }))
                                    if (!showConstructor) { setPreviewComp(null); setShowConstructor(true) }
                                    toast.success(`${ins.nombre} al constructor — ajusta la cantidad 📦`, { duration: 1800 })
                                  }}
                                  title="Agregar este material a mi propio APU"
                                  className="col-span-1 text-emerald-600 hover:bg-emerald-50 rounded font-bold text-center">+</button>
                        </div>
                      ))}
                    </>
                  )}
                  <div className="grid grid-cols-12 gap-1 px-2 py-1.5 border-t border-violet-200 bg-white items-center">
                    <span className="col-span-8 font-medium text-slate-600">Mano de obra</span>
                    <span className="col-span-4 text-right font-medium">{COP(previewBase.data.mano_obra)}</span>
                  </div>
                  <div className="grid grid-cols-12 gap-1 px-2 py-1.5 border-t border-violet-100 bg-white items-center">
                    <span className="col-span-8 font-medium text-slate-600">Herramienta menor ({previewBase.data.herramienta_pct}% MO)</span>
                    <span className="col-span-4 text-right font-medium">{COP(previewBase.data.herramienta)}</span>
                  </div>
                  <div className="grid grid-cols-12 gap-1 px-2 py-1.5 border-t border-violet-100 bg-white items-center">
                    <span className="col-span-8 font-medium text-slate-600">Transporte 🚚</span>
                    <span className="col-span-4 text-right font-medium">{COP(previewBase.data.transporte)}</span>
                  </div>
                  <div className="grid grid-cols-12 gap-1 px-2.5 py-2 border-t-2 border-violet-300 bg-violet-100 items-center">
                    <span className="col-span-8 font-bold text-violet-800">PRECIO UNITARIO</span>
                    <span className="col-span-4 text-right font-black text-violet-800">{COP(previewBase.data.precio_unitario)}</span>
                  </div>
                </div>
                <button onClick={(e) => { duplicarComoMio({ codigo: previewBase.codigo }, e); setPreviewBase(null) }}
                        className="w-full mt-3 py-2.5 rounded-xl bg-navy-600 text-white text-xs font-bold hover:bg-navy-700">
                  ⧉ Duplicar como mío para editarlo
                </button>
              </>
            )}
          </div>
        </div>
      )}

      {/* Modal CONSTRUCTOR DE APU (componer con mis insumos) */}
      {showConstructor && (
        <div className="fixed inset-0 bg-black/40 z-[60] flex items-start justify-center p-4 pt-[6vh]" onClick={() => setShowConstructor(false)}>
          <div className="bg-white rounded-2xl p-5 w-full max-w-lg max-h-[86vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <h3 className="font-semibold text-slate-800 mb-1">🧱 Construir mi APU</h3>
            <p className="text-[11px] text-slate-400 mb-2">Insumos + mano de obra + herramienta + transporte 🚚 → tu precio unitario compuesto (los 4 componentes del APU oficial)</p>
            {desgloses.porCodigo['REC-PANETE'] ? (
              <button onClick={() => { setShowConstructor(false); setQ(''); setFuenteApu('mios'); setShowBuscador(true) }}
                      data-testid="btn-recetario-atajo" className="w-full mb-3 py-2 rounded-xl border border-emerald-200 bg-emerald-50 text-emerald-700 text-xs font-bold hover:bg-emerald-100">
                🍳 Recetario cargado ✓ — ver mis 16 recetas en ⭐ Mis APUs
              </button>
            ) : (
            <button onClick={async () => {
                      try {
                        toast.loading('Sembrando recetas...', { id: 'rec' })
                        const r = await apusAPI.recetario()
                        if (r.creados > 0) toast.success(`🍳 ${r.creados} recetas listas — aquí están, en ⭐ Mis APUs`, { id: 'rec', duration: 5000 })
                        else toast.success('Tu recetario ya estaba cargado — aquí está, en ⭐ Mis APUs ✓', { id: 'rec' })
                        // Llevar al usuario DIRECTO a verlas: cerrar constructor, abrir buscador en Mis APUs
                        setShowConstructor(false)
                        setQ('')
                        setFuenteApu('mios')
                        setShowBuscador(true)
                        // refresco EXPLICITO: si ya estabas parado en Mis APUs, el effect
                        // no re-dispara y verias la lista congelada (bug cazado por el robot)
                        apusAPI.listar({ sector: esPublico ? 'publico' : 'privado' })
                          .then(rr => setMisApus(rr.items || [])).catch(() => {})
                        apusAPI.listar({}).then(r2 => {
                          const porId = {}, porCodigo = {}, codigoAId = {}
                          for (const a of (r2.items || [])) if (a.desglose?.insumos?.length) { porId[a.id] = a.desglose; if (a.codigo) { porCodigo[a.codigo] = a.desglose; codigoAId[a.codigo] = a.id } }
                          setDesgloses({ porId, porCodigo, codigoAId })
                        }).catch(() => {})
                      } catch (e2) { toast.error(e2.response?.data?.detail || e2.message, { id: 'rec' }) }
                    }}
                    data-testid="btn-recetario" className="w-full mb-3 py-2 rounded-xl border border-amber-200 bg-amber-50 text-amber-700 text-xs font-bold hover:bg-amber-100">
              🍳 Cargar recetario de arranque — 16 recetas típicas con su análisis, listas para ajustar a TUS precios
            </button>
            )}
            <input className="w-full text-sm border border-slate-200 rounded-xl px-3 py-2.5 mb-2" placeholder="Descripción (ej: Pañete 1:4 muros interiores)"
                   value={construyendo.descripcion} onChange={e => setConstruyendo(c => ({ ...c, descripcion: e.target.value }))} />
            <div className="flex flex-wrap gap-2 mb-2">
              <input className="w-20 text-sm border border-slate-200 rounded-xl px-3 py-2" placeholder="unidad"
                     value={construyendo.unidad} onChange={e => setConstruyendo(c => ({ ...c, unidad: e.target.value }))} />
              <div className="flex-1 min-w-[180px] flex items-center gap-1">
                <input type="number" disabled={soloLectura} className="flex-1 text-sm border border-slate-200 rounded-xl px-3 py-2" placeholder="Mano de obra por unidad ($)"
                       value={construyendo.mano_obra} onChange={e => setConstruyendo(c => ({ ...c, mano_obra: e.target.value }))} />
                <InfoTip texto="Lo que le pagas a la cuadrilla por hacer 1 unidad (1 m², 1 m³...). Va en PESOS. Tip: jornal con prestaciones ÷ rendimiento del día = MO por unidad." />
              </div>
            </div>
            <div className="flex flex-wrap gap-2 mb-3">
              <div className="flex items-center gap-1">
                <input type="number" disabled={soloLectura} min="0" max="30" className="w-20 text-sm border border-slate-200 rounded-xl px-3 py-2" placeholder="herr %"
                       value={construyendo.herramienta_pct} onChange={e => setConstruyendo(c => ({ ...c, herramienta_pct: Math.max(0, Math.min(30, parseFloat(e.target.value) || 0)) }))} />
                <span className="text-xs font-bold text-slate-400">%</span>
                <InfoTip texto="Herramienta menor: desgaste de palas, baldes, taladro. Es un PORCENTAJE de la mano de obra (práctica estándar 3-10%, máx 30). NO va en pesos — si lo tuyo es un flete, ese es el campo de transporte 🚚." />
              </div>
              <div className="flex-1 min-w-[160px] flex items-center gap-1">
                <input type="number" disabled={soloLectura} min="0" className="flex-1 text-sm border border-slate-200 rounded-xl px-3 py-2" placeholder="🚚 Transporte por unidad ($)"
                       value={construyendo.transporte} onChange={e => setConstruyendo(c => ({ ...c, transporte: e.target.value }))} />
                <InfoTip texto="Flete o acarreo por unidad del APU — el 4to componente del formato oficial que exigen las entidades. Va en PESOS por unidad. Si no aplica, déjalo en 0 y no cambia nada." />
              </div>
            </div>
            <p className="text-[10px] font-bold text-slate-400 uppercase mb-1.5">Insumos</p>
            {construyendo.insumos.map((ins, i) => (
              <div key={i}>
              <div className="flex gap-1.5 mb-1.5">
                <div className="flex-1 relative">
                  <input className="w-full text-xs border border-slate-200 rounded-lg px-2 py-1.5" placeholder="insumo" value={ins.nombre}
                         onChange={e => {
                           const v = e.target.value
                           setConstruyendo(c => ({ ...c, insumos: c.insumos.map((x, j) => j === i ? { ...x, nombre: v } : x) }))
                           if (v.trim().length >= 3) {
                             setSugerenciaPara(i)
                             insumosAPI.buscar(v.trim()).then(r => setSugerencias(r.resultados.slice(0, 5))).catch(() => setSugerencias([]))
                           } else { setSugerencias([]); setSugerenciaPara(-1) }
                         }} />
                  {sugerenciaPara === i && sugerencias.length > 0 && (
                    <div className="absolute z-10 left-0 right-0 top-full mt-0.5 bg-white border border-slate-200 rounded-lg shadow-lg overflow-hidden">
                      {sugerencias.map((s, k) => (
                        <button key={k}
                                onClick={() => {
                                  setConstruyendo(c => ({ ...c, insumos: c.insumos.map((x, j) => j === i ? { ...x, nombre: s.nombre, precio: s.precio } : x) }))
                                  setSugerencias([]); setSugerenciaPara(-1)
                                }}
                                className="w-full flex items-center justify-between gap-1.5 px-2 py-1.5 text-[10px] hover:bg-slate-50 text-left">
                          <span className="flex items-center gap-1.5 min-w-0">
                            {s.imagen
                              ? <img src={s.imagen} alt="" className="w-5 h-5 rounded object-contain bg-slate-50 shrink-0" onError={e => { e.target.style.display = 'none' }} />
                              : <span className="shrink-0">{s.fuente === 'mi_proveedor' ? '🏪' : '📖'}</span>}
                            <span className="text-slate-600 truncate">{s.nombre}</span>
                          </span>
                          <span className="font-bold text-slate-700 tabular-nums shrink-0 ml-2">{COP(s.precio)}
                            <span className="font-normal text-slate-300 ml-1">{s.fuente === 'mi_proveedor' ? s.detalle : s.fecha}</span>{s.precio_viejo && <span className="text-amber-600 font-bold ml-1">⚠ precio de hace {Math.round(s.edad_dias / 30)} meses</span>}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                <input type="number" disabled={soloLectura} className="w-16 text-xs border border-slate-200 rounded-lg px-2 py-1.5" placeholder="cant" value={ins.cantidad}
                       onChange={e => setConstruyendo(c => ({ ...c, insumos: c.insumos.map((x, j) => j === i ? { ...x, cantidad: e.target.value } : x) }))} />
                <button onClick={() => setRindeIdx(rindeIdx === i ? -1 : i)}
                        className={`text-[9px] font-bold rounded-lg px-1.5 transition ${rindeIdx === i ? 'bg-blue-600 text-white' : 'bg-blue-50 text-blue-600 hover:bg-blue-100'}`}
                        title="¿No sabes la cantidad? Dime cuánto te RINDE y yo hago la división">
                  ⇄rinde
                </button>
                <input type="number" disabled={soloLectura} className="w-24 text-xs border border-slate-200 rounded-lg px-2 py-1.5" placeholder="precio" value={ins.precio}
                       onChange={e => setConstruyendo(c => ({ ...c, insumos: c.insumos.map((x, j) => j === i ? { ...x, precio: e.target.value } : x) }))} />
                <button onClick={() => setConstruyendo(c => ({ ...c, insumos: c.insumos.filter((_, j) => j !== i) }))}
                        className="text-slate-300 hover:text-red-400 px-1">×</button>
              </div>
              {rindeIdx === i && (
                <div className="flex items-center gap-1.5 mb-1.5 ml-2 bg-blue-50 border border-blue-100 rounded-lg px-2 py-1.5 text-[11px] text-blue-700">
                  <span>1 {ins.unidad || 'un'} me rinde</span>
                  <input type="number" disabled={soloLectura} step="any" min="0.01" autoFocus placeholder="3"
                         className="w-16 text-xs border border-blue-200 rounded-lg px-2 py-1 bg-white text-center"
                         onChange={e => {
                           const r = parseFloat(e.target.value)
                           if (r > 0) setConstruyendo(c => ({ ...c, insumos: c.insumos.map((x, j) => j === i ? { ...x, cantidad: +(1 / r).toFixed(4) } : x) }))
                         }} />
                  <span>{construyendo.unidad || 'un'} → cantidad = <strong>{ins.cantidad || '?'}</strong> por {construyendo.unidad || 'un'}</span>
                  <button onClick={() => setRindeIdx(-1)} className="ml-auto font-bold text-blue-400">✓ listo</button>
                </div>
              )}
              </div>
            ))}
            <div className="flex gap-3 mb-3">
              <button onClick={() => setConstruyendo(c => ({ ...c, insumos: [...c.insumos, { nombre: '', cantidad: '', precio: '' }] }))}
                      className="text-xs font-medium text-navy-600">+ agregar insumo</button>
              <button onClick={() => { insumosAPI.catalogo().then(setCatalogo).catch(() => {}); setShowCatalogo(true) }}
                      className="text-xs font-medium text-emerald-600">📦 Catálogo de referencia</button>
            </div>

            <button onClick={async () => {
                      try {
                        const r = await apusAPI.componer({
                          insumos: construyendo.insumos.map(i => ({ nombre: i.nombre, cantidad: parseFloat(i.cantidad) || 0, precio: parseFloat(i.precio) || 0 })),
                          mano_obra: parseInt(construyendo.mano_obra) || 0,
                          herramienta_pct: parseFloat(construyendo.herramienta_pct) || 0,
                          transporte: Math.round(parseFloat(construyendo.transporte) || 0),
                        })
                        setPreviewComp(r)
                      } catch (e) { toast.error(e.message) }
                    }}
                    className="w-full py-2.5 rounded-xl border border-navy-300 text-navy-600 text-sm font-bold mb-2">
              Calcular precio compuesto
            </button>
            {previewComp && (
              <div className="bg-emerald-50 rounded-xl p-3 mb-2 text-xs text-slate-600">
                Materiales {COP(previewComp.materiales)} + MO {COP(previewComp.mano_obra)} + herramienta {COP(previewComp.herramienta)}
                <p className="text-lg font-black text-emerald-700 mt-1">= {COP(previewComp.precio_unitario)} <span className="text-xs font-medium">/{construyendo.unidad}</span></p>
              </div>
            )}
            <button disabled={!previewComp || !construyendo.descripcion.trim()}
                    onClick={async () => {
                      try {
                        const a = await apusAPI.crear({ descripcion: construyendo.descripcion, unidad: construyendo.unidad, precio: 0, sector_tag: esPublico ? 'publico' : 'ambos' })
                        await apusAPI.guardarDesglose(a.id, {
                          insumos: construyendo.insumos.map(i => ({ nombre: i.nombre, cantidad: parseFloat(i.cantidad) || 0, precio: parseFloat(i.precio) || 0 })),
                          mano_obra: parseInt(construyendo.mano_obra) || 0,
                          herramienta_pct: parseFloat(construyendo.herramienta_pct) || 0,
                          transporte: Math.round(parseFloat(construyendo.transporte) || 0),
                        })
                        toast.success('APU compuesto guardado en Mis APUs 🧱')
                        setShowConstructor(false); setFuenteApu('mios'); setQ('')
                      } catch (e) { toast.error(e.message) }
                    }}
                    className="w-full py-3 rounded-xl bg-emerald-500 text-white text-sm font-bold disabled:opacity-40">
              Guardar en Mis APUs
            </button>
          </div>
        </div>
      )}

      {/* Modal SEGUIMIENTO (obra publica: las dos caras, todo adentro) */}
      {showSeguimiento && seguimiento && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-start justify-center p-4 pt-[5vh]" onClick={() => setShowSeguimiento(false)}>
          <div className="bg-white rounded-2xl w-full max-w-2xl max-h-[88vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="p-5 border-b border-slate-100 sticky top-0 bg-white z-10">
              <h3 className="font-semibold text-slate-800">📋 Seguimiento del contrato</h3>
              <p className="text-[11px] text-slate-400 mt-0.5">
                {p?.entidad_nombre || 'Entidad contratante'}
                {p?.contrato_numero && <> · Contrato <strong>{p.contrato_numero}</strong></>}
                {p?.supervisor_nombre && <> · Supervisión: {p.supervisor_nombre}</>}
              </p>
            </div>
            <div className="p-5 space-y-5">

              {/* CARA FISICA: el balance resumido */}
              <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase mb-2">🏗️ Cara física — ejecución</p>
                <div className="grid grid-cols-3 gap-2">
                  {[['Avance físico', `${seguimiento.balance.resumen.avance_fisico_pct}%`, 'text-emerald-600'],
                    ['Ejecutado', COP(seguimiento.balance.resumen.valor_ejecutado), 'text-slate-800'],
                    ['Por ejecutar', COP(seguimiento.balance.resumen.saldo_por_ejecutar), 'text-amber-600']].map(([t, v, cls]) => (
                    <div key={t} className="bg-slate-50 rounded-xl p-2.5">
                      <p className="text-[9px] text-slate-400 uppercase font-bold">{t}</p>
                      <p className={`text-sm font-black tabular-nums ${cls}`}>{v}</p>
                    </div>
                  ))}
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden mt-2">
                  <div className="h-full bg-emerald-400 rounded-full transition-all" style={{ width: `${seguimiento.balance.resumen.avance_fisico_pct}%` }} />
                </div>
              </div>

              {/* CARA FINANCIERA: actas y caja */}
              <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase mb-2">💵 Cara financiera — actas y pagos</p>
                <div className="grid grid-cols-3 gap-2">
                  {[['Avance financiero', `${seguimiento.balance.resumen.avance_financiero_pct}%`, 'text-navy-600'],
                    ['Facturado', COP(seguimiento.balance.resumen.facturado), 'text-slate-800'],
                    ['Pagado', COP(seguimiento.balance.resumen.pagado), 'text-emerald-600']].map(([t, v, cls]) => (
                    <div key={t} className="bg-slate-50 rounded-xl p-2.5">
                      <p className="text-[9px] text-slate-400 uppercase font-bold">{t}</p>
                      <p className={`text-sm font-black tabular-nums ${cls}`}>{v}</p>
                    </div>
                  ))}
                </div>
                {seguimiento.balance.resumen.valor_adicionales > 0 && (
                  <p className="text-[11px] text-amber-600 mt-2">➕ Adicionales aprobados: <strong>{COP(seguimiento.balance.resumen.valor_adicionales)}</strong> (valor total actualizado: {COP(seguimiento.balance.resumen.valor_total)})</p>
                )}
              </div>

              {/* BITACORA cronologica interna */}
              <div>
                <p className="text-[10px] font-bold text-slate-400 uppercase mb-2">📖 Bitácora del contrato</p>
                <div className="space-y-0">
                  {(() => { const clave = f => { const s = String(f || ''); const m = s.match(/(\d{2})\/(\d{2})\/(\d{4})(.*)/); return m ? `${m[3]}${m[2]}${m[1]}${m[4]}` : s }; return [
                    ...(seguimiento.avancesList || []).map(a => ({ f: a.creado || a.fecha || '', icono: '🏗️', texto: `${a.titulo} — ${a.porcentaje ?? a.pct ?? ''}% acumulado` })),
                    ...(seguimiento.cuentas || []).filter(cta => cta.tipo !== 'retegarantia').map(cta => ({ f: cta.fecha || '', icono: '📄', texto: `Acta ${cta.numero}: ${COP(cta.neto)} neto${cta.deducciones > 0 ? ` (deducciones de ley ${COP(cta.deducciones)})` : ''}` })),
                    ...(seguimiento.cuentas || []).filter(cta => cta.estado === 'pagada' && cta.fecha_pago).map(cta => ({ f: cta.fecha_pago, icono: '✅', texto: `Acta ${cta.numero} pagada por la entidad` })),
                    ...(seguimiento.cuentas || []).filter(cta => cta.tipo === 'retegarantia').map(cta => ({ f: cta.fecha || '', icono: '🔓', texto: `Retegarantía liberada: ${COP(cta.neto)}` })),
                    ...(otrosies || []).filter(o => o.estado === 'aprobado').map(o => ({ f: o.resuelto || '', icono: '➕', texto: `Adicional N.${o.numero} aprobado: ${COP(o.totales?.total || 0)}` })),
                  ].sort((a, b) => clave(b.f).localeCompare(clave(a.f))).map((ev, i) => (
                    <div key={i} className="flex gap-2.5 text-xs py-2 border-b border-slate-50 last:border-0">
                      <span className="shrink-0">{ev.icono}</span>
                      <span className="flex-1 text-slate-600">{ev.texto}</span>
                      <span className="text-[10px] text-slate-300 shrink-0 tabular-nums">{String(ev.f).slice(0, 10)}</span>
                    </div>
                  )) })()}
                  {!(seguimiento.avancesList || []).length && !(seguimiento.cuentas || []).length && (
                    <p className="text-xs text-slate-300">Aún no hay movimientos — registra tu primer avance de obra</p>
                  )}
                </div>
              </div>

              <p className="text-[10px] text-slate-300 border-t border-slate-50 pt-3">
                🔒 Este seguimiento vive solo aquí: en obra pública nada viaja fuera de tu plataforma.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Modal BALANCE DE OBRA */}
      {showBalance && balanceData && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-start justify-center p-4 pt-[6vh]" onClick={() => setShowBalance(false)}>
          <div className="bg-white rounded-2xl p-5 w-full max-w-2xl max-h-[86vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <h3 className="font-semibold text-slate-800 mb-1">📊 Balance de obra</h3>
            <p className="text-[11px] text-slate-400 mb-3">Oficial vs ejecutado — contrato + adicionales × avances × actas</p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-4">
              {[['Valor total', balanceData.resumen.valor_total, 'text-slate-800'],
                ['Ejecutado', balanceData.resumen.valor_ejecutado, 'text-emerald-600'],
                ['Por ejecutar', balanceData.resumen.saldo_por_ejecutar, 'text-amber-600'],
                ['Facturado', balanceData.resumen.facturado, 'text-navy-600']].map(([t, v, cls]) => (
                <div key={t} className="bg-slate-50 rounded-xl p-2.5">
                  <p className="text-[9px] text-slate-400 uppercase font-bold">{t}</p>
                  <p className={`text-sm font-black tabular-nums ${cls}`}>{COP(v)}</p>
                </div>
              ))}
            </div>
            <div className="flex gap-3 mb-4 text-xs">
              <span className="text-slate-500">Avance físico <strong className="text-emerald-600">{balanceData.resumen.avance_fisico_pct}%</strong></span>
              <span className="text-slate-500">Avance financiero <strong className="text-navy-600">{balanceData.resumen.avance_financiero_pct}%</strong></span>
              {balanceData.resumen.valor_adicionales > 0 && (
                <span className="text-slate-500">Adicionales <strong className="text-amber-600">{COP(balanceData.resumen.valor_adicionales)}</strong></span>
              )}
            </div>
            <div className="border border-slate-100 rounded-xl overflow-hidden">
              {balanceData.filas.map(f => (
                <div key={f.id} className={`flex items-center gap-2 px-3 py-2 text-xs border-b border-slate-50 ${f.es_adicional ? 'bg-amber-50/40' : ''}`}>
                  <div className="flex-1 min-w-0">
                    <p className="text-slate-700 truncate">{f.es_adicional ? '➕ ' : ''}{f.descripcion}</p>
                    <p className="text-[10px] text-slate-400">{f.cantidad_ejecutada}/{f.cantidad_contratada} {f.unidad}</p>
                  </div>
                  <div className="w-20 text-right shrink-0">
                    <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden mb-0.5">
                      <div className="h-full bg-emerald-400 rounded-full" style={{ width: `${f.pct}%` }} />
                    </div>
                    <span className="text-[10px] text-slate-500 tabular-nums">{f.pct}%</span>
                  </div>
                  <p className="w-24 text-right font-semibold text-slate-700 tabular-nums shrink-0">{COP(f.valor_ejecutado)}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Modal CATALOGO DE INSUMOS (referencia curada, dentro del constructor) */}
      {showCatalogo && (
        <div className="fixed inset-0 bg-black/40 z-[70] flex items-start justify-center p-4 pt-[8vh]" onClick={() => { setShowCatalogo(false); setCatalogo(null) }}>
          <div className="bg-white rounded-2xl p-5 w-full max-w-md max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <h3 className="font-semibold text-slate-800 mb-1">📦 Catálogo de referencia</h3>
            <p className="text-[10px] text-slate-400 mb-3">Precios de vitrina del mercado (v{catalogo?.version || '2026'}) — referencia, no precio en vivo. Toca uno para llevarlo al constructor.</p>
            {catalogo?.categorias && (
              <div className="grid grid-cols-2 gap-1.5">
                {catalogo.categorias.map(ct => (
                  <button key={ct.nombre} onClick={() => insumosAPI.catalogo(ct.nombre).then(setCatalogo).catch(() => {})}
                          className="rounded-xl border border-slate-100 hover:border-emerald-300 p-2.5 text-left transition">
                    <p className="text-xs font-semibold text-slate-700 capitalize">{ct.nombre.replace('-', ' ')}</p>
                    <p className="text-[9px] text-slate-400">{ct.n} insumos</p>
                  </button>
                ))}
              </div>
            )}
            {catalogo?.insumos && (
              <>
                <button onClick={() => insumosAPI.catalogo().then(setCatalogo).catch(() => {})}
                        className="text-xs text-slate-400 mb-2">← categorías</button>
                {catalogo.insumos.map((ins, k) => (
                  <button key={k}
                          onClick={() => {
                            setConstruyendo(c => ({ ...c, insumos: [...c.insumos, { nombre: ins.nombre, cantidad: '', precio: ins.precio }] }))
                            if (!showConstructor) { setPreviewComp(null); setShowConstructor(true) }
                            setShowCatalogo(false); setCatalogo(null)
                            toast.success(`${ins.nombre} al constructor — ajusta la cantidad 📦`, { duration: 1800 })
                          }}
                          className="w-full flex items-center gap-2 px-2.5 py-2 rounded-xl hover:bg-emerald-50 text-left border-b border-slate-50">
                    {ins.imagen
                      ? <img src={ins.imagen} alt="" className="w-8 h-8 rounded-lg object-contain bg-slate-50 border border-slate-100 shrink-0" onError={e => { e.target.style.display = 'none' }} />
                      : <span className="w-8 h-8 rounded-lg bg-slate-50 border border-slate-100 shrink-0 flex items-center justify-center text-slate-300 text-xs">📦</span>}
                    <span className="text-xs text-slate-600 flex-1 pr-2">{ins.nombre}</span>
                    <span className="text-xs font-bold text-slate-700 tabular-nums shrink-0">{COP(ins.precio)}
                      <span className="font-normal text-slate-300 text-[10px]"> /{ins.unidad}</span></span>
                  </button>
                ))}
              </>
            )}
          </div>
        </div>
      )}

      {/* Modal MIS PROVEEDORES */}
      {showProveedores && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={() => { setShowProveedores(false); setProvSel(null) }}>
          <div className="bg-white rounded-2xl p-5 w-full max-w-lg max-h-[86vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <h3 className="font-semibold text-slate-800 mb-3">🏪 Mis proveedores</h3>
            {!provSel ? (
              <>
                {proveedores.map(pr => (
                  <div key={pr.id} className="flex items-center justify-between border border-slate-100 rounded-xl px-3 py-2.5 mb-1.5">
                    <button onClick={() => proveedoresAPI.precios(pr.id).then(r => setProvSel({ ...pr, precios: r.precios }))} className="text-left flex-1">
                      <p className="text-sm font-medium text-slate-700">{pr.nombre}</p>
                      <p className="text-[10px] text-slate-400">{pr.n_precios} precio{pr.n_precios !== 1 ? 's' : ''} capturado{pr.n_precios !== 1 ? 's' : ''}</p>
                    </button>
                    <button onClick={async () => { if (await confirmarDialogo({ titulo: '¿Eliminar proveedor?', mensaje: 'Se borran también sus precios guardados.', peligro: true, confirmar: 'Eliminar' })) { await proveedoresAPI.eliminar(pr.id); cargarProveedores() } }}
                            className="text-slate-300 hover:text-red-400 text-sm px-2">×</button>
                  </div>
                ))}
                <div className="flex gap-1.5 mt-3">
                  <input className="flex-1 text-sm border border-slate-200 rounded-xl px-3 py-2" placeholder="Nombre (ej: Ferretería El Roble)"
                         value={nuevoProv.nombre} onChange={e => setNuevoProv(n => ({ ...n, nombre: e.target.value }))} />
                  <button onClick={async () => {
                            if (!nuevoProv.nombre.trim()) return
                            try { await proveedoresAPI.crear(nuevoProv); setNuevoProv({ nombre: '', telefono: '' }); cargarProveedores() }
                            catch (e) { toast.error(e.message) }
                          }}
                          className="text-sm font-bold text-white bg-navy-600 rounded-xl px-4">+</button>
                </div>
              </>
            ) : (
              <>
                <button onClick={() => setProvSel(null)} className="text-xs text-slate-400 mb-2">← volver</button>
                <p className="text-sm font-bold text-slate-700 mb-2">{provSel.nombre}</p>
                <input ref={fileMasivoRef} type="file" accept=".xlsx,.xlsm,.csv" className="hidden"
                       onChange={async (e) => {
                         const archivo = e.target.files?.[0]
                         e.target.value = ''  // permite re-subir el mismo archivo si hace falta
                         if (!archivo) return
                         setCargandoMasivo(true)
                         try {
                           const fd = new FormData()
                           fd.append('archivo', archivo)
                           const r = await proveedoresAPI.cargarMasivo(provSel.id, fd)
                           const partes = [`${r.nuevos} nuevo${r.nuevos !== 1 ? 's' : ''}`]
                           if (r.sin_cambios) partes.push(`${r.sin_cambios} sin cambios`)
                           if (r.invalidas) partes.push(`${r.invalidas} inválida${r.invalidas !== 1 ? 's' : ''}`)
                           if (r.duplicados_en_archivo) partes.push(`${r.duplicados_en_archivo} repetido${r.duplicados_en_archivo !== 1 ? 's' : ''} en el archivo`)
                           toast.success(`Carga completa: ${partes.join(' · ')}`, { duration: 5000 })
                           const rp = await proveedoresAPI.precios(provSel.id)
                           setProvSel(s => ({ ...s, precios: rp.precios })); cargarProveedores()
                           if (r.conflictos?.length) {
                             setConflictosMasivo({ proveedorId: provSel.id, lista: r.conflictos.map(c => ({ ...c, accion: 'mantener' })) })
                           }
                         } catch (err) { toast.error(err.message) }
                         finally { setCargandoMasivo(false) }
                       }} />
                <button onClick={() => fileMasivoRef.current?.click()} disabled={cargandoMasivo}
                        className="w-full mb-3 py-2 rounded-xl border border-dashed border-emerald-300 bg-emerald-50 text-emerald-700 text-xs font-bold hover:bg-emerald-100 disabled:opacity-50">
                  {cargandoMasivo ? 'Cargando...' : `📤 Cargar mi base de precios (Excel/CSV) — hasta ${2500} filas`}
                </button>
                <p className="text-[10px] text-slate-400 -mt-2 mb-3">
                  Columnas: nombre del insumo, unidad (opcional), precio. En cualquier orden.
                </p>
                {provSel.precios.map(pc => (
                  <div key={pc.id} className="flex items-center justify-between text-xs border-b border-slate-50 py-1.5">
                    <span className="text-slate-600 flex-1">{pc.insumo} <span className="text-slate-300">/{pc.unidad}</span></span>
                    <span className="font-semibold text-slate-700 tabular-nums">{COP(pc.precio)}</span>
                    <span className="text-[9px] text-slate-300 ml-2">{pc.capturado}</span>
                    <button onClick={async () => { await proveedoresAPI.eliminarPrecio(pc.id); const r = await proveedoresAPI.precios(provSel.id); setProvSel(s => ({ ...s, precios: r.precios })); cargarProveedores() }}
                            className="text-slate-300 hover:text-red-400 ml-2">×</button>
                  </div>
                ))}
                <div className="flex gap-1.5 mt-3">
                  <input className="flex-1 text-xs border border-slate-200 rounded-lg px-2 py-2" placeholder="Insumo (ej: Cemento gris)"
                         value={nuevoPrecio.insumo} onChange={e => setNuevoPrecio(n => ({ ...n, insumo: e.target.value }))} />
                  <input className="w-14 text-xs border border-slate-200 rounded-lg px-2 py-2" placeholder="un"
                         value={nuevoPrecio.unidad} onChange={e => setNuevoPrecio(n => ({ ...n, unidad: e.target.value }))} />
                  <input type="number" disabled={soloLectura} className="w-24 text-xs border border-slate-200 rounded-lg px-2 py-2" placeholder="precio"
                         value={nuevoPrecio.precio} onChange={e => setNuevoPrecio(n => ({ ...n, precio: e.target.value }))} />
                  <button onClick={async () => {
                            try {
                              await proveedoresAPI.agregarPrecio(provSel.id, { ...nuevoPrecio, precio: parseInt(nuevoPrecio.precio) || 0 })
                              const r = await proveedoresAPI.precios(provSel.id)
                              setProvSel(s => ({ ...s, precios: r.precios })); setNuevoPrecio({ insumo: '', unidad: 'un', precio: '' }); cargarProveedores()
                            } catch (e) { toast.error(e.message) }
                          }}
                          className="text-xs font-bold text-white bg-emerald-500 rounded-lg px-3">+</button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Modal CONFLICTOS de carga masiva — precios que ya existían con otro valor */}
      {conflictosMasivo && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-[70]" onClick={() => setConflictosMasivo(null)}>
          <div className="bg-white rounded-2xl p-5 w-full max-w-lg max-h-[86vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <h3 className="font-semibold text-slate-800 mb-1">⚠️ {conflictosMasivo.lista.length} precio{conflictosMasivo.lista.length !== 1 ? 's' : ''} con valor distinto</h3>
            <p className="text-[11px] text-slate-400 mb-3">
              Estos insumos ya existían con otro precio. Elegí cuáles actualizar — el resto se queda como estaba.
            </p>
            <div className="flex gap-2 mb-3">
              <button onClick={() => setConflictosMasivo(c => ({ ...c, lista: c.lista.map(x => ({ ...x, accion: 'actualizar' })) }))}
                      className="text-[11px] font-bold text-emerald-600 border border-emerald-200 rounded-lg px-2.5 py-1.5">Actualizar todos</button>
              <button onClick={() => setConflictosMasivo(c => ({ ...c, lista: c.lista.map(x => ({ ...x, accion: 'mantener' })) }))}
                      className="text-[11px] font-bold text-slate-500 border border-slate-200 rounded-lg px-2.5 py-1.5">Mantener todos</button>
            </div>
            <div className="space-y-1.5">
              {conflictosMasivo.lista.map((c, i) => (
                <div key={c.id_existente} className="flex items-center gap-2 border border-slate-100 rounded-xl p-2.5">
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-slate-700 truncate">{c.insumo}</p>
                    <p className="text-[10px] text-slate-400">
                      Actual: <span className="line-through">{COP(c.precio_actual)}</span> → Nuevo: <strong className="text-slate-600">{COP(c.precio_nuevo)}</strong>
                    </p>
                  </div>
                  <div className="flex gap-1 shrink-0">
                    <button onClick={() => setConflictosMasivo(cm => ({ ...cm, lista: cm.lista.map((x, j) => j === i ? { ...x, accion: 'actualizar' } : x) }))}
                            className={`text-[10px] font-bold rounded-lg px-2 py-1 ${c.accion === 'actualizar' ? 'bg-emerald-500 text-white' : 'bg-slate-100 text-slate-400'}`}>Actualizar</button>
                    <button onClick={() => setConflictosMasivo(cm => ({ ...cm, lista: cm.lista.map((x, j) => j === i ? { ...x, accion: 'mantener' } : x) }))}
                            className={`text-[10px] font-bold rounded-lg px-2 py-1 ${c.accion === 'mantener' ? 'bg-slate-500 text-white' : 'bg-slate-100 text-slate-400'}`}>Mantener</button>
                  </div>
                </div>
              ))}
            </div>
            <button onClick={async () => {
                      try {
                        const decisiones = conflictosMasivo.lista.map(c => ({
                          id_existente: c.id_existente, accion: c.accion,
                          precio_nuevo: c.precio_nuevo, unidad_nueva: c.unidad_nueva,
                        }))
                        const r = await proveedoresAPI.resolverConflictos(decisiones)
                        toast.success(`${r.actualizados} precio${r.actualizados !== 1 ? 's' : ''} actualizado${r.actualizados !== 1 ? 's' : ''}`)
                        if (provSel?.id === conflictosMasivo.proveedorId) {
                          const rp = await proveedoresAPI.precios(provSel.id)
                          setProvSel(s => ({ ...s, precios: rp.precios }))
                        }
                        setConflictosMasivo(null)
                      } catch (err) { toast.error(err.message) }
                    }}
                    className="w-full mt-3 py-2.5 rounded-xl bg-navy-600 text-white text-xs font-bold hover:bg-navy-700">
              Confirmar
            </button>
          </div>
        </div>
      )}

      {/* Modal COBROS */}
      {showCobros && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50" onClick={() => setShowCobros(false)}>
          <div className="bg-white rounded-2xl p-5 w-full max-w-lg max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-slate-800">💵 {esPublico ? 'Actas parciales de obra' : 'Cuentas de cobro'}</h3>
              {(contrato.anticipo_pct > 0) && !(cobrosData?.cuentas || cobrosData || []).some?.(x => x.tipo === 'anticipo') && (
                <button data-testid="btn-acta-anticipo"
                        onClick={async () => {
                          try {
                            const r = await cuentasAPI.anticipo(id)
                            toast.success(`Acta de anticipo ${r.numero}: ${COP(r.neto)}`)
                            cuentasAPI.listar(id).then(setCobrosData).catch(() => {})
                          } catch (err) { toast.error(err.message) }
                        }}
                        className="text-[11px] font-bold border border-emerald-300 text-emerald-700 rounded-lg px-2.5 py-1 hover:bg-emerald-50">
                  💵 Facturar anticipo ({contrato.anticipo_pct}%)
                </button>
              )}
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
                  {liquidacion.retencion > 0 && (
                    <div className="flex justify-between"><span className="text-slate-500">(−) Retegarantía ({liquidacion.retegarantia_pct}%) 🔒</span><span>− {COP(liquidacion.retencion)}</span></div>
                  )}
                  {(liquidacion.deducciones || []).map((dd, k) => (
                    <div key={k} className="flex justify-between"><span className="text-slate-500">(−) {dd.nombre} ({dd.pct}%) 🏛️</span><span>− {COP(dd.valor)}</span></div>
                  ))}
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

            {/* Retegarantia acumulada / liberar */}
            {cobrosData?.cuentas?.some(c => c.retencion > 0) && (
              <div className="flex items-center justify-between bg-violet-50 border border-violet-200 rounded-xl px-3 py-2 mb-2">
                <p className="text-[11px] text-violet-700">
                  🔒 Retegarantía retenida: <strong>{COP(cobrosData.cuentas.reduce((s, c) => s + (c.retencion || 0), 0))}</strong>
                  <span className="text-violet-400"> — se libera al firmar el acta</span>
                </p>
                {p.estado === 'terminado' && !cobrosData.cuentas.some(c => c.tipo === 'retegarantia') && (
                  <button onClick={async () => {
                            try {
                              const r = await cuentasAPI.retegarantia(id)
                              cuentasAPI.listar(id).then(setCobrosData)
                              toast.success(`🔓 Cuenta ${r.cuenta.numero} generada — cobra tu retegarantía`)
                            } catch (e) { toast.error(e.message) }
                          }}
                          className="shrink-0 text-[10px] font-bold text-white bg-violet-500 rounded-lg px-2.5 py-1.5">
                    🔓 Liberar
                  </button>
                )}
              </div>
            )}

            {/* Cuentas generadas */}
            <div className="space-y-1.5">
              {cobrosData?.cuentas?.map(c => (
                <div key={c.id} className={`border rounded-xl px-3 py-2.5 ${c.estado === 'pagada' ? 'border-emerald-200 bg-emerald-50/40' : 'border-amber-200 bg-amber-50/30'}`}>
                  <div className="flex items-center justify-between gap-2">
                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-slate-700">
                        {c.tipo === 'retegarantia' ? '🔓 ' : ''}{c.numero} · {COP(c.neto)}
                        {c.tipo === 'retegarantia' && <span className="text-[9px] text-violet-600 font-bold"> RETEGARANTÍA</span>}
                      </p>
                      <p className="text-[9px] text-slate-400">
                        {c.fecha}{c.fecha_pago && ` · pagada ${c.fecha_pago}`}
                        {c.retencion > 0 && ` · retuvo ${COP(c.retencion)}`}
                        {c.deducciones > 0 && ` · deducciones de ley ${COP(c.deducciones)}`}
                      </p>
                      {c.estado !== 'pagada' && c.abonado > 0 && (
                        <div className="mt-1">
                          <div className="h-1 bg-slate-100 rounded-full overflow-hidden w-32">
                            <div className="h-full bg-emerald-400" style={{ width: `${Math.min(100, c.abonado / c.neto * 100)}%` }} />
                          </div>
                          <p className="text-[9px] text-emerald-600">Abonado {COP(c.abonado)} · saldo {COP(c.neto - c.abonado)}</p>
                        </div>
                      )}
                    </div>
                    <span className={`shrink-0 text-[9px] font-bold px-2 py-1 rounded-full ${c.estado === 'pagada' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
                      {c.estado === 'pagada' ? '✓ Pagada' : '⏳ Enviada'}
                    </span>
                  </div>
                  {esPublico && o.estado !== 'aprobado' && o.estado !== 'rechazado' && (
                    <button onClick={async () => {
                              try {
                                await otrosiesAPI.aprobarInterno(o.id)
                                toast.success('Adicional aprobado — ya entra en avances y actas ✍️')
                                otrosiesAPI.listar(id).then(setOtrosies).catch(() => {})
                              } catch (e) { toast.error(e.message) }
                            }}
                            className="mt-1.5 text-[10px] font-bold text-white bg-navy-600 rounded-lg px-2.5 py-1.5">
                      ✍️ Aprobar internamente
                    </button>
                  )}
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
                                className="text-[10px] font-bold text-white bg-emerald-500 rounded-lg px-2 py-1">💰 Ya me pagaron{c.abonado > 0 ? ' (saldo)' : ''}</button>
                        <button onClick={() => setAbonando({ cuenta: c, monto: '', nota: '' })}
                                className="text-[10px] font-bold text-emerald-700 border border-emerald-300 rounded-lg px-2 py-1">＋ Abono</button>
                        <button onClick={async () => {
                                  if (!(await confirmarDialogo({ titulo: '¿Eliminar esta cuenta de cobro?', peligro: true, confirmar: 'Eliminar' }))) return
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

      {/* Modal ABONO PARCIAL */}
      {abonando && (
        <div className="fixed inset-0 bg-black/40 z-[60] flex items-center justify-center p-4" onClick={() => setAbonando(null)}>
          <div className="bg-white w-full max-w-xs rounded-2xl p-4" onClick={e => e.stopPropagation()}>
            <h3 className="text-sm font-bold text-slate-800">＋ Abono a {abonando.cuenta.numero}</h3>
            <p className="text-[11px] text-slate-400 mb-3">
              Saldo pendiente: <strong className="text-slate-600">{COP(abonando.cuenta.neto - (abonando.cuenta.abonado || 0))}</strong>
            </p>
            <input disabled={soloLectura} className="input mb-2" type="number" placeholder="Monto del abono *" autoFocus
                   value={abonando.monto}
                   onChange={e => setAbonando(a => ({ ...a, monto: e.target.value }))} />
            <input className="input mb-3" placeholder="Nota (ej: Nequi viernes)" maxLength={150}
                   value={abonando.nota}
                   onChange={e => setAbonando(a => ({ ...a, nota: e.target.value }))} />
            <button onClick={async () => {
                      const monto = Math.round(parseFloat(abonando.monto) || 0)
                      if (monto <= 0) { toast.error('Escribe el monto'); return }
                      try {
                        const r = await cuentasAPI.abonar(abonando.cuenta.id, monto, abonando.nota)
                        setAbonando(null)
                        cuentasAPI.listar(id).then(setCobrosData)
                        toast.success(r.cuenta.estado === 'pagada' ? '💰 ¡Cuenta pagada completa!' : `Abono de ${COP(monto)} registrado`)
                      } catch (e) { toast.error(e.message) }
                    }}
                    className="w-full py-2.5 rounded-xl bg-emerald-500 text-white text-xs font-bold">Registrar abono</button>
          </div>
        </div>
      )}

      {/* Modal ADICIONALES (otrosies) */}
      {showOtrosi && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4"
             onClick={() => setShowOtrosi(false)}>
          <div className="bg-white w-full sm:max-w-lg sm:rounded-2xl rounded-t-2xl max-h-[92vh] overflow-y-auto"
               onClick={e => e.stopPropagation()}>
            <div className="px-4 py-3 border-b border-slate-100 flex justify-between items-center sticky top-0 bg-white z-10">
              <h3 className="font-semibold text-slate-800">➕ {esPublico ? 'Adicionales / Mayores cantidades' : 'Adicionales de obra'}</h3>
              <button onClick={() => setShowOtrosi(false)}><X className="w-4 h-4 text-slate-400" /></button>
            </div>

            <div className="p-4 space-y-3">
              <p className="text-[11px] text-slate-400 -mt-1">
                Trabajos extra que aparecieron tras la firma. Tu cliente los aprueba con nueva firma
                {esPublico ? 'Se aprueban internamente (obra pública: sin cliente final) y entran a avances y actas automáticamente.' : <>desde su enlace y se genera el <strong>Otrosí en PDF</strong> — entran a avances y cuentas automáticamente.</>}
              </p>

              {otrosies.map(o => (
                <div key={o.id} className={`border rounded-xl p-3 ${o.estado === 'aprobado' ? 'border-emerald-200 bg-emerald-50/40' : o.estado === 'rechazado' ? 'border-slate-200 opacity-60' : 'border-amber-200 bg-amber-50/40'}`}>
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-semibold text-slate-700">Otrosí N.{o.numero} · {COP(o.totales?.total || 0)}</p>
                    <span className={`text-[9px] font-bold px-2 py-1 rounded-full ${o.estado === 'aprobado' ? 'bg-emerald-100 text-emerald-700' : o.estado === 'rechazado' ? 'bg-slate-100 text-slate-500' : 'bg-amber-100 text-amber-700'}`}>
                      {o.estado === 'aprobado' ? `✍️ ${esPublico ? 'Aprobado' : 'Firmado'} por ${o.nombre_firma}` : o.estado === 'rechazado' ? 'Rechazado' : esPublico ? '⏳ Por aprobar' : '⏳ Esperando al cliente'}
                    </span>
                  </div>
                  {o.motivo && <p className="text-[10px] text-slate-400 mt-0.5">{o.motivo}</p>}
                  <p className="text-[11px] text-slate-500 mt-1">
                    {o.items.map(i => i.descripcion).join(' · ').slice(0, 120)}
                  </p>
                  <div className="flex gap-2 mt-2">
                    {o.estado === 'aprobado' && p.share_token && (
                      <a href={`/api/share/publico/${p.share_token}/otrosi/${o.id}.pdf`} target="_blank" rel="noreferrer"
                         className="text-[10px] font-bold text-navy-600 border border-navy-200 rounded-lg px-2 py-1">
                        📄 Otrosí PDF
                      </a>
                    )}
                    {o.estado === 'propuesto' && (
                      <>
                        <button onClick={() => avisarCliente(`Hola! Te propuse un adicional para tu obra "${p.nombre}" por ${COP(o.totales?.total || 0)}. Apruébalo con tu firma aquí:`)}
                                className="text-[10px] font-bold bg-emerald-500 text-white rounded-lg px-2 py-1">
                          Enviar por WhatsApp
                        </button>
                        <button onClick={async () => {
                                  try { await otrosiesAPI.eliminar(o.id); setOtrosies(prev => prev.filter(x => x.id !== o.id)); toast.success('Eliminado') }
                                  catch (e) { toast.error(e.message) }
                                }}
                                className="text-[10px] text-red-500 border border-red-200 rounded-lg px-2 py-1">
                          Eliminar
                        </button>
                      </>
                    )}
                  </div>
                </div>
              ))}

              {/* Nuevo adicional */}
              <div className="border-2 border-dashed border-slate-200 rounded-xl p-3 space-y-2">
                <p className="text-xs font-semibold text-slate-600">Proponer nuevo adicional</p>
                <input className="input !py-2 text-xs" placeholder="Motivo (ej: El cliente pidió además el mesón en granito)"
                       value={otMotivo} onChange={e => setOtMotivo(e.target.value)} maxLength={300} />

                <div className="relative">
                  <input className="input !py-2 text-xs" placeholder="🔍 Buscar en la base APU para agregar..."
                         value={otBusca}
                         onChange={e => {
                           const q = e.target.value
                           setOtBusca(q)
                           if (q.trim().length >= 3) {
                             preciosAPI.buscar({ query: q, region: p.region || 'bogota', limit: 5 })
                               .then(r => setOtResultados(r.items || [])).catch(() => {})
                           } else setOtResultados([])
                         }} />
                  {otResultados.length > 0 && (
                    <div className="absolute z-20 left-0 right-0 bg-white border border-slate-200 rounded-xl shadow-xl max-h-40 overflow-y-auto">
                      {otResultados.map((r, i) => (
                        <button key={i} onClick={() => {
                                  setOtItems(rows => [...rows.filter(x => x.descripcion || x.precio_unitario),
                                    { descripcion: r.descripcion, unidad: r.unidad, cantidad: 1, precio_unitario: r.precio, codigo: r.codigo }])
                                  setOtBusca(''); setOtResultados([])
                                }}
                                className="w-full text-left px-3 py-2 text-[11px] text-slate-600 hover:bg-slate-50 border-b border-slate-50">
                          {r.descripcion} · <span className="text-slate-400">{COP(r.precio)}/{r.unidad}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {otItems.map((row, i) => (
                  <div key={i} className="flex gap-1.5 items-center">
                    <input className="input !py-1.5 text-[11px] flex-1" placeholder="Descripción del trabajo"
                           value={row.descripcion}
                           onChange={e => setOtItems(rows => rows.map((r, j) => j === i ? { ...r, descripcion: e.target.value } : r))} />
                    <input className="input !py-1.5 text-[11px] !w-14" placeholder="und" value={row.unidad}
                           onChange={e => setOtItems(rows => rows.map((r, j) => j === i ? { ...r, unidad: e.target.value } : r))} />
                    <input disabled={soloLectura} className="input !py-1.5 text-[11px] !w-14 text-right" type="number" placeholder="cant" value={row.cantidad}
                           onChange={e => setOtItems(rows => rows.map((r, j) => j === i ? { ...r, cantidad: e.target.value } : r))} />
                    <input disabled={soloLectura} className="input !py-1.5 text-[11px] !w-24 text-right" type="number" placeholder="$ unit" value={row.precio_unitario}
                           onChange={e => setOtItems(rows => rows.map((r, j) => j === i ? { ...r, precio_unitario: e.target.value } : r))} />
                    <button onClick={() => setOtItems(rows => rows.length > 1 ? rows.filter((_, j) => j !== i) : rows)}
                            className="text-slate-300 hover:text-red-400"><X className="w-3.5 h-3.5" /></button>
                  </div>
                ))}
                <div className="flex items-center justify-between">
                  <button onClick={() => setOtItems(rows => [...rows, { descripcion: '', unidad: 'un', cantidad: 1, precio_unitario: '' }])}
                          className="text-[11px] font-medium text-navy-600">＋ Agregar fila</button>
                  <p className="text-[11px] text-slate-500">
                    Total con tu AIU: <strong className="text-slate-700">
                      {COP(calcularLocal(otItems.filter(r => r.descripcion && r.precio_unitario), aiu)?.total || 0)}
                    </strong>
                  </p>
                </div>
                <button onClick={async () => {
                          const filas = otItems.filter(r => r.descripcion.trim() && parseFloat(r.precio_unitario) > 0)
                          if (filas.length === 0) { toast.error('Agrega al menos un trabajo con precio'); return }
                          try {
                            const nuevo = await otrosiesAPI.crear({ proyecto_id: parseInt(id), motivo: otMotivo, items: filas })
                            setOtrosies(prev => [...prev, nuevo])
                            setOtItems([{ descripcion: '', unidad: 'un', cantidad: 1, precio_unitario: '' }])
                            setOtMotivo('')
                            toast.success(`Otrosí N.${nuevo.numero} propuesto — envíaselo al cliente por WhatsApp`)
                          } catch (e) { toast.error(e.message) }
                        }}
                        className="w-full py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-white text-xs font-bold transition">
                  Proponer al cliente
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal CRONOGRAMA (Gantt) — solo obra publica */}
      {showCronograma && (
        <div className="fixed inset-0 bg-black/40 flex items-start justify-center p-4 pt-[5vh] z-[60]" onClick={() => setShowCronograma(false)}>
          <div className="bg-white rounded-2xl p-5 w-full max-w-4xl max-h-[88vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-1">
              <h3 className="font-semibold text-slate-800">📅 Cronograma de obra</h3>
              <button onClick={() => setShowCronograma(false)} className="text-slate-300 hover:text-slate-500"><X className="w-4 h-4" /></button>
            </div>
            <p className="text-[11px] text-slate-400 mb-4">
              Cada fila puede arrancar en una semana fija, o "empezar cuando termine" otra fila de la lista.
              {cronoData?.fecha_inicio && <> Fecha de inicio del contrato: <strong>{cronoData.fecha_inicio}</strong>.</>}
            </p>

            {cronoData?.error && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-3 mb-3 text-xs text-red-700">
                ⚠ {cronoData.error} — corrígelo abajo antes de guardar.
              </div>
            )}

            {/* Editor de filas */}
            <div className="space-y-2 mb-3">
              {cronoFilas.map((f, i) => (
                <div key={f.id} className="flex items-center gap-1.5 bg-slate-50 rounded-xl p-2">
                  <input value={f.nombre} placeholder="Nombre de la actividad"
                         onChange={e => setCronoFilas(fs => fs.map((x, j) => j === i ? { ...x, nombre: e.target.value } : x))}
                         className="flex-1 min-w-0 text-xs border border-slate-200 rounded-lg px-2 py-1.5" />
                  <input type="number" min="0.1" step="0.5" value={f.duracion_semanas} title="Duración en semanas"
                         onChange={e => setCronoFilas(fs => fs.map((x, j) => j === i ? { ...x, duracion_semanas: e.target.value } : x))}
                         className="w-16 text-xs text-right border border-slate-200 rounded-lg px-2 py-1.5" />
                  <span className="text-[10px] text-slate-400 shrink-0">sem.</span>
                  <select value={f.predecesora_id || ''} title="Empieza cuando termina..."
                          onChange={e => setCronoFilas(fs => fs.map((x, j) => j === i ? { ...x, predecesora_id: e.target.value || null } : x))}
                          className="w-36 text-[11px] border border-slate-200 rounded-lg px-1.5 py-1.5">
                    <option value="">— fecha manual —</option>
                    {cronoFilas.filter(o => o.id !== f.id).map(o => (
                      <option key={o.id} value={o.id}>tras: {o.nombre || '(sin nombre)'}</option>
                    ))}
                  </select>
                  {!f.predecesora_id && (
                    <input type="number" min="0" step="0.5" value={f.semana_inicio ?? 0} title="Semana de inicio manual"
                           onChange={e => setCronoFilas(fs => fs.map((x, j) => j === i ? { ...x, semana_inicio: e.target.value } : x))}
                           className="w-14 text-xs text-right border border-slate-200 rounded-lg px-2 py-1.5" />
                  )}
                  <button onClick={() => setCronoFilas(fs => fs.filter((_, j) => j !== i))}
                          className="shrink-0 p-1.5 hover:bg-red-50 rounded-lg">
                    <Trash2 className="w-3.5 h-3.5 text-slate-300 hover:text-red-500" />
                  </button>
                </div>
              ))}
              <button onClick={() => setCronoFilas(fs => [...fs, {
                        id: 'f' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
                        nombre: '', duracion_semanas: 1, semana_inicio: 0, predecesora_id: null,
                      }])}
                      className="text-xs font-medium text-navy-600 hover:text-navy-800">+ agregar fila</button>
            </div>

            <button disabled={cronoGuardando || !cronoFilas.length}
                    onClick={async () => {
                      setCronoGuardando(true)
                      try {
                        const filasLimpias = cronoFilas.map(f => ({
                          id: f.id, nombre: f.nombre, orden: f.orden || 0,
                          duracion_semanas: parseFloat(f.duracion_semanas) || 1,
                          semana_inicio: parseFloat(f.semana_inicio) || 0,
                          predecesora_id: f.predecesora_id || null,
                        }))
                        const d = await cronogramaAPI.guardar(id, filasLimpias)
                        setCronoData(d); setCronoFilas(d.filas || [])
                        toast.success('Cronograma guardado ✓')
                      } catch (err) { toast.error(err.message) }
                      finally { setCronoGuardando(false) }
                    }}
                    className="w-full py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold transition disabled:opacity-50 mb-5">
              {cronoGuardando ? 'Guardando...' : '💾 Guardar cronograma'}
            </button>

            {/* Gantt visual */}
            {cronoData?.filas?.length > 0 && (() => {
              const total = Math.max(cronoData.duracion_total_semanas || 1, 2)
              const pctHoy = cronoData.pct_avance_real
              return (
                <div className="border border-slate-200 rounded-xl p-3 overflow-x-auto">
                  <div className="min-w-[500px]">
                    {pctHoy != null && (
                      <p className="text-[11px] text-emerald-600 font-bold mb-2">📍 Avance real cargado: {pctHoy}%</p>
                    )}
                    <div className="relative">
                      {pctHoy != null && (
                        <div className="absolute top-0 bottom-0 w-0.5 bg-emerald-500 z-10"
                             style={{ left: `${Math.min(100, pctHoy)}%` }} title={`${pctHoy}% del plazo total`} />
                      )}
                      {cronoData.filas.map(f => (
                        <div key={f.id} className="flex items-center gap-2 py-1">
                          <span className="w-32 shrink-0 text-[11px] text-slate-600 truncate" title={f.nombre}>{f.nombre}</span>
                          <div className="flex-1 h-5 bg-slate-100 rounded relative">
                            <div className="absolute top-0 bottom-0 rounded bg-sky-500 flex items-center justify-end pr-1"
                                 style={{
                                   left: `${(f.semana_inicio_efectiva / total) * 100}%`,
                                   width: `${Math.max(2, (f.duracion_semanas / total) * 100)}%`,
                                 }}>
                              <span className="text-[9px] text-white font-bold">{f.duracion_semanas}sem</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                    <p className="text-[10px] text-slate-400 mt-2 text-right">duración total: {total} semanas</p>
                  </div>
                </div>
              )
            })()}
          </div>
        </div>
      )}

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
                <input type="number" disabled={soloLectura} className="input !py-2 text-xs flex-1" placeholder="Valor $"
                       value={nuevoGasto.valor}
                       onChange={e => setNuevoGasto(g => ({ ...g, valor: e.target.value }))} />
                <label className="text-[10px] text-navy-600 border border-navy-200 rounded-lg px-2.5 py-2 cursor-pointer whitespace-nowrap">
                  {nuevoGasto.foto ? '✓ Recibo' : '📷 Recibo'}
                  <input type="file" accept="image/*" className="hidden"
                         onChange={e => {
                           const file = e.target.files?.[0]
                           if (!file) return
                           if (file.size > 450 * 1024) { toast.error('Máximo 450KB'); return }
                           comprimirImagen(file).then(foto => setNuevoGasto(g => ({ ...g, foto }))).catch(() => toast.error('Imagen no valida'))
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
                            if (!(await confirmarDialogo({ titulo: '¿Eliminar este gasto?', peligro: true, confirmar: 'Eliminar' }))) return
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
      {showAvances && !charla && (() => { avancesAPI.interacciones(id).then(setCharla).catch(() => setCharla({ avances: [], total_comentarios: 0 })); return null })()}
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

            {/* 💬 Lo que dice tu cliente (seguimiento de reacciones y comentarios) */}
            {charla && charla.avances.length > 0 && (
              <div className="p-4 border-b border-slate-100 bg-emerald-50/40">
                <p className="text-[10px] font-bold text-slate-500 uppercase mb-2">
                  💬 Lo que dice tu {esPublico ? 'interventor' : 'cliente'}
                  {charla.total_comentarios > 0 && <span className="ml-1.5 bg-emerald-500 text-white rounded-full px-1.5 py-0.5">{charla.total_comentarios}</span>}
                </p>
                {charla.avances.map(g => (
                  <div key={g.avance_id} className="mb-2.5 last:mb-0">
                    <p className="text-[11px] font-semibold text-slate-600">
                      {g.titulo}
                      {Object.entries(g.reacciones).map(([e2, n]) => <span key={e2} className="ml-1.5">{e2}{n > 1 ? `×${n}` : ''}</span>)}
                    </p>
                    {g.comentarios.map((cm, k) => (
                      <div key={k} className={`mt-1 text-xs rounded-xl px-2.5 py-1.5 ${cm.autor === 'contratista' ? 'bg-navy-600 text-white ml-6' : 'bg-white ring-1 ring-slate-100 text-slate-600'}`}>
                        <span className="font-semibold">{cm.autor === 'contratista' ? '👷 ' : '💬 '}{cm.nombre}:</span> {cm.texto}
                        <span className={`block text-[9px] mt-0.5 ${cm.autor === 'contratista' ? 'text-white/50' : 'text-slate-300'}`}>{cm.fecha}</span>
                      </div>
                    ))}
                    {g.comentarios.some(cm => cm.autor !== 'contratista') && (
                      <div className="flex gap-1.5 mt-1.5">
                        <input className="flex-1 text-xs border border-slate-200 rounded-lg px-2 py-1.5" placeholder="Responder…"
                               value={respondiendo[g.avance_id] || ''}
                               onChange={e => setRespondiendo(r => ({ ...r, [g.avance_id]: e.target.value }))} />
                        <button onClick={async () => {
                                  const t = (respondiendo[g.avance_id] || '').trim()
                                  if (!t) return
                                  try {
                                    await avancesAPI.responder(g.avance_id, t)
                                    setRespondiendo(r => ({ ...r, [g.avance_id]: '' }))
                                    avancesAPI.interacciones(id).then(setCharla).catch(() => {})
                                    toast.success('Respuesta enviada — tu cliente la verá en su enlace 👷')
                                  } catch (e) { toast.error(e.message) }
                                }}
                                className="text-xs font-bold text-white bg-navy-600 rounded-lg px-3">→</button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

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
                {itemsParaAvance.map(it => {
                  const valorItem = Math.round((parseFloat(it.cantidad)||0) * (parseFloat(it.precio_unitario)||0))
                  const pct = avanceItems[it.id] ?? 0
                  return (
                    <div key={it.id} className="px-3 py-2 border-b border-slate-50 flex items-center gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="text-[11px] text-slate-600 leading-snug truncate">{it.descripcion}</p>
                        <p className="text-[10px] text-slate-400">{COP(valorItem)}</p>
                      </div>
                      <input type="number" disabled={soloLectura} min="0" max="100" step="5" value={pct}
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
                itemsParaAvance.forEach(it => {
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
                             comprimirImagen(file).then(f => setNuevoAvance(a => ({ ...a, fotos: [...a.fotos, f].slice(0, 3) }))).catch(() => toast.error('Imagen no valida'))
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
                            items: itemsParaAvance.map(it => ({ id: it.id, pct: avanceItems[it.id] ?? 0 })),
                          }
                          const a = await avancesAPI.crear(id, payload)
                          setAvances(prev => [a, ...prev])
                          setNuevoAvance({ titulo: '', descripcion: '', fotos: [] })
                          toast.success(`Avance publicado: ${a.porcentaje}% = ${COP(a.valor_ejecutado)}`)
                          setTimeout(async () => {
                            if (await confirmarDialogo({ titulo: '📲 ¿Avisar al cliente por WhatsApp?',
                              mensaje: 'Se abrirá WhatsApp con el mensaje del avance listo para enviar.',
                              confirmar: 'Abrir WhatsApp' })) {
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
                              if (!(await confirmarDialogo({ titulo: '¿Eliminar este avance?', mensaje: 'Se recalcula el acumulado de la obra.', peligro: true, confirmar: 'Eliminar' }))) return
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

                  {/* ═══ EL HILO: el cliente comenta, tu respondes ═══ */}
                  {((a.comentarios?.length || 0) > 0 || Object.keys(a.reacciones || {}).length > 0) && (
                    <div className="mt-2 border-t border-slate-50 pt-2">
                      {Object.keys(a.reacciones || {}).length > 0 && (
                        <p className="text-[11px] mb-1.5">
                          {Object.entries(a.reacciones).map(([e, n]) => `${e} ${n}`).join('  ')}
                          <span className="text-slate-400 text-[9px] ml-1">de tu cliente</span>
                        </p>
                      )}
                      {(a.comentarios || []).map((cm, i) => (
                        <div key={i} className={`rounded-lg px-2.5 py-1.5 text-[11px] mb-1 ${cm.autor === 'contratista' ? 'bg-navy-50 text-slate-700 ml-4' : 'bg-amber-50 text-slate-600'}`}>
                          <span className="font-bold text-[9px] opacity-70">{cm.autor === 'contratista' ? '👷 Tú' : `💬 ${cm.nombre}`} · {cm.fecha}</span>
                          <p className="whitespace-pre-wrap">{cm.texto}</p>
                        </div>
                      ))}
                    </div>
                  )}
                  {(a.comentarios?.length || 0) > 0 && (
                    <div className="flex gap-1.5 mt-1.5">
                      <input className="flex-1 text-[11px] border border-slate-200 rounded-lg px-2.5 py-1.5"
                             placeholder="Responder a tu cliente..." maxLength={300}
                             value={hiloTexto[a.id] || ''}
                             onChange={e => setHiloTexto(h => ({ ...h, [a.id]: e.target.value }))} />
                      <button onClick={async () => {
                                const t = (hiloTexto[a.id] || '').trim()
                                if (!t) return
                                try {
                                  const r = await avancesAPI.responderComentario(a.id, t)
                                  setAvances(prev => prev.map(x => x.id === a.id ? { ...x, comentarios: r.comentarios } : x))
                                  setHiloTexto(h => ({ ...h, [a.id]: '' }))
                                  toast.success('Tu cliente lo verá en su enlace 💬')
                                } catch (e) { toast.error(e.message) }
                              }}
                              className="text-[11px] font-bold text-white bg-navy-600 rounded-lg px-3">
                        Responder
                      </button>
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
