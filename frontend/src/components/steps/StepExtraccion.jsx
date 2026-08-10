import React, { useState, useCallback } from 'react'
import toast from 'react-hot-toast'
import { CheckCircle, AlertTriangle, Edit3, Plus, Trash2, Loader2, ArrowLeft,
         Calculator, ChevronDown, ChevronRight, Brain, Zap, Send } from 'lucide-react'
import { clsx } from 'clsx'
import { presupuestoAPI, feedbackAPI } from '../../services/api'
import { TIPO_COLORS } from '../../utils/format'

const TIPOS = ['columnas','vigas','losa','cimentacion','muros','escaleras',
               'cubierta','viga_amarre','caisson','muro_contencion','otros']
const UNIDADES = ['un','m','m²','m³','kg','pto','gl']
const CONF = {
  alta:  {cls:'text-emerald-700 bg-emerald-50 border-emerald-200',Icon:CheckCircle, lbl:'Alta confianza'},
  media: {cls:'text-amber-700 bg-amber-50 border-amber-200',  Icon:AlertTriangle,lbl:'Confianza media — revisar'},
  baja:  {cls:'text-red-700 bg-red-50 border-red-200',        Icon:AlertTriangle,lbl:'Baja — validar todo'},
}
const TIPO_ICONS = {
  columnas:'🏛',vigas:'🔩',losa:'⬜',cimentacion:'⬇️',muros:'🧱',
  escaleras:'📐',cubierta:'🏠',viga_amarre:'📏',caisson:'🕳',
  muro_contencion:'🗻',otros:'📦',
  columna_metalica:'🏗',viga_metalica:'🔧',correa_metalica:'➖',
  anclaje_placa_base:'🔩',conexion_soldada:'⚡',cercha:'🔺',
  tensor:'〰️',platina:'▬',arriostramiento:'✖️'
}

// Normalizar tipos que vienen de la extraccion a los tipos del sistema
const normalizarTipo = (t) => {
  const mapa = {
    columna_metalica:'columnas', viga_metalica:'vigas',
    correa_metalica:'cubierta', cercha:'cubierta',
    anclaje_placa_base:'otros', conexion_soldada:'otros',
    tensor:'cubierta', platina:'otros', arriostramiento:'otros',
  }
  return mapa[t] || t
}

function ElementCard({el, idx, onUpdate, onDelete, tipoPlano, contexto}) {
  const [editing, setEditing] = useState(false)
  const [local, setLocal] = useState({...el})
  const [saving, setSaving] = useState(false)
  const c = TIPO_COLORS[el.tipo] || TIPO_COLORS.otros

  const save = async () => {
    setSaving(true)
    try {
      // Si hubo cambios, enviar corrección al sistema de feedback
      const changed = Object.keys(local).some(k => local[k] !== el[k])
      if (changed) {
        await feedbackAPI.correccion(el, local, tipoPlano, contexto)
        toast.success('Corrección guardada — el sistema aprende de esto', {
          icon: '🧠', duration: 2500
        })
      }
      onUpdate(idx, local)
      setEditing(false)
    } catch(e) {
      // La corrección falla silenciosamente — no bloquear al usuario
      console.warn('Feedback no registrado:', e.message)
      onUpdate(idx, local)
      setEditing(false)
    } finally {
      setSaving(false)
    }
  }

  if (editing) return (
    <div className="card p-4 ring-2 ring-navy-300 animate-fade-in">
      {/* Banner de feedback */}
      <div className="flex items-center gap-2 mb-3 p-2 bg-blue-50 rounded-lg border border-blue-100">
        <Brain size={13} className="text-blue-500 shrink-0"/>
        <p className="text-[11px] text-blue-700">
          Al guardar, esta corrección alimenta el sistema de aprendizaje para futuros análisis
        </p>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div><label className="label-xs">Tipo</label>
          <select className="select" value={local.tipo}
            onChange={e=>setLocal(p=>({...p,tipo:e.target.value}))}>
            {TIPOS.map(t=><option key={t}>{t}</option>)}
          </select></div>
        <div><label className="label-xs">Referencia (ej: C1, Z-1, PTE250)</label>
          <input className="input" value={local.referencia||''}
            onChange={e=>setLocal(p=>({...p,referencia:e.target.value}))}/></div>
        <div className="col-span-2"><label className="label-xs">Nombre / Perfil exacto</label>
          <input className="input" placeholder="Ej: Columna C1 30x30cm o PTE 250x250x9mm"
            value={local.nombre}
            onChange={e=>setLocal(p=>({...p,nombre:e.target.value}))}/></div>
        <div><label className="label-xs">Cantidad</label>
          <input className="input" type="number" step="any" value={local.cantidad}
            onChange={e=>setLocal(p=>({...p,cantidad:parseFloat(e.target.value)||0}))}/></div>
        <div><label className="label-xs">Unidad</label>
          <select className="select" value={local.unidad}
            onChange={e=>setLocal(p=>({...p,unidad:e.target.value}))}>
            {UNIDADES.map(u=><option key={u}>{u}</option>)}
          </select></div>
        <div><label className="label-xs">Ancho (cm)</label>
          <input className="input" type="number" placeholder="30" value={local.dimension_ancho_cm||''}
            onChange={e=>setLocal(p=>({...p,dimension_ancho_cm:parseFloat(e.target.value)||null}))}/></div>
        <div><label className="label-xs">Alto / Espesor (cm)</label>
          <input className="input" type="number" placeholder="30" value={local.dimension_alto_cm||''}
            onChange={e=>setLocal(p=>({...p,dimension_alto_cm:parseFloat(e.target.value)||null}))}/></div>
        <div><label className="label-xs">Longitud (m)</label>
          <input className="input" type="number" step="any" placeholder="5.80" value={local.dimension_largo_m||''}
            onChange={e=>setLocal(p=>({...p,dimension_largo_m:parseFloat(e.target.value)||null}))}/></div>
        <div><label className="label-xs">Altura libre (m)</label>
          <input className="input" type="number" step="any" placeholder="3.00" value={local.altura_libre_m||''}
            onChange={e=>setLocal(p=>({...p,altura_libre_m:parseFloat(e.target.value)||null}))}/></div>
        <div><label className="label-xs">Diámetro (cm) — caissons</label>
          <input className="input" type="number" placeholder="60" value={local.dimension_diametro_cm||''}
            onChange={e=>setLocal(p=>({...p,dimension_diametro_cm:parseFloat(e.target.value)||null}))}/></div>
        <div><label className="label-xs">Área (m²)</label>
          <input className="input" type="number" step="any" placeholder="120" value={local.area_m2||''}
            onChange={e=>setLocal(p=>({...p,area_m2:parseFloat(e.target.value)||null}))}/></div>
        <div className="col-span-2"><label className="label-xs">Material / Perfil / Especificación</label>
          <input className="input" placeholder="Ej: PTE 250x250x9mm ASTM A500 Gr.C"
            value={local.material||''}
            onChange={e=>setLocal(p=>({...p,material:e.target.value}))}/></div>
        <div className="col-span-2"><label className="label-xs">Acero longitudinal</label>
          <input className="input" placeholder='Ej: 4Ø5/8" o 4#5+2#4'
            value={local.acero_longitudinal||''}
            onChange={e=>setLocal(p=>({...p,acero_longitudinal:e.target.value}))}/></div>
        <div className="col-span-2"><label className="label-xs">Notas</label>
          <input className="input" value={local.notas||''}
            onChange={e=>setLocal(p=>({...p,notas:e.target.value}))}/></div>
      </div>
      <div className="flex gap-2 mt-3 justify-end">
        <button className="btn-ghost text-xs"
          onClick={()=>{setLocal({...el});setEditing(false)}}>Cancelar</button>
        <button className="btn-primary text-xs px-4 py-1.5 flex items-center gap-1.5"
          onClick={save} disabled={saving}>
          {saving ? <><Loader2 size={13} className="animate-spin"/>Guardando...</>
                  : <><Send size={13}/>Guardar + Enseñar al sistema</>}
        </button>
      </div>
    </div>
  )

  return (
    <div className={clsx('card-flat p-3.5 flex gap-3 items-start group border',
                          c.border, 'hover:shadow-sm transition-shadow')}>
      <div className="text-base shrink-0 mt-0.5">{TIPO_ICONS[el.tipo]||'📦'}</div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 flex-wrap">
          {el.referencia && (
            <span className="text-[10px] font-mono bg-slate-100 px-1.5 py-0.5 rounded text-slate-600 font-semibold">
              {el.referencia}
            </span>
          )}
          <p className="font-semibold text-slate-800 text-sm leading-tight">{el.nombre}</p>
          <span className={clsx('badge text-[10px]', c.bg, c.text)}>{el.tipo}</span>
          {el.dato_estimado && <span className="badge badge-amber text-[10px]">estimado</span>}
          {el.confianza_extraccion && el.confianza_extraccion < 0.75 &&
            <span className="badge badge-red text-[10px]">⚠ revisar</span>}
        </div>
        <div className="flex flex-wrap gap-x-3 gap-y-0.5 mt-1.5 text-xs text-slate-400 items-center">
          {(!el.cantidad || el.cantidad <= 0) ? (
            <span className="inline-flex items-center gap-1.5 bg-amber-50 border border-amber-300 rounded-lg px-2 py-1">
              <AlertTriangle size={11} className="text-amber-500"/>
              <input
                type="number" step="any" placeholder="cantidad"
                className="w-20 bg-transparent text-xs font-semibold text-amber-800 placeholder-amber-400 outline-none"
                onBlur={e => {
                  const v = parseFloat(e.target.value)
                  if (v > 0) onUpdate(idx, {...el, cantidad: v})
                }}
                onKeyDown={e => {
                  if (e.key === 'Enter') {
                    const v = parseFloat(e.target.value)
                    if (v > 0) onUpdate(idx, {...el, cantidad: v})
                  }
                }}
              />
              <span className="text-amber-600 font-medium">{el.unidad || 'un'}</span>
            </span>
          ) : (
            <span><strong className="text-slate-600">{el.cantidad}</strong> {el.unidad}</span>
          )}
          {el.dimension_ancho_cm && <span>{el.dimension_ancho_cm}×{el.dimension_alto_cm}cm</span>}
          {el.altura_libre_m && <span>h={el.altura_libre_m}m</span>}
          {el.dimension_largo_m && <span>L={el.dimension_largo_m}m</span>}
          {el.espesor_cm && <span>e={el.espesor_cm}cm</span>}
          {el.area_m2 && <span>{el.area_m2}m²</span>}
          {el.dimension_diametro_cm && <span>D={el.dimension_diametro_cm}cm</span>}
          {el.material && <span className="truncate max-w-[200px]">{el.material}</span>}
        </div>
        {el.acero_longitudinal && (
          <p className="text-[11px] text-indigo-600 mt-1">
            ↳ {el.acero_longitudinal}
            {el.acero_transversal && ` | ${el.acero_transversal}`}
          </p>
        )}
        {el.notas && <p className="text-[11px] text-slate-400 mt-0.5 italic">{el.notas}</p>}
      </div>
      <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
        <button className="btn-ghost p-1.5" title="Editar y enseñar al sistema"
          onClick={()=>setEditing(true)}>
          <Edit3 size={13}/>
        </button>
        <button className="btn-ghost p-1.5 hover:text-red-500 hover:bg-red-50"
          onClick={()=>onDelete(idx)}>
          <Trash2 size={13}/>
        </button>
      </div>
    </div>
  )
}

export default function StepExtraccion({data, region, fcMpa, fyMpa, aiu, setAiu, iva, setIva, onBack, onDone}) {
  const [elementos, setElementos] = useState(data.elementos || [])
  const [loading, setLoading] = useState(false)
  const [showNotas, setShowNotas] = useState(false)
  const conf = CONF[data.confianza] || CONF.media
  const ConfIcon = conf.Icon

  const tipoCount = elementos.reduce((acc,el)=>{acc[el.tipo]=(acc[el.tipo]||0)+1;return acc},{})
  const tieneMetal = elementos.some(el =>
    el.nombre?.toUpperCase().includes('PTE') ||
    el.nombre?.toUpperCase().includes('PHR') ||
    el.tipo === 'cubierta'
  )

  const update = (i, u) => setElementos(p => p.map((el, idx) => idx===i ? u : el))
  const del = i => setElementos(p => p.filter((_, idx) => idx!==i))
  const add = () => setElementos(p => [...p, {
    tipo:'otros', nombre:'Nuevo elemento', cantidad:1, unidad:'un',
    referencia:'', material:'', notas:''
  }])

  const calcular = async () => {
    if (!elementos.length) { toast.error('No hay elementos para calcular'); return }
    setLoading(true)
    try {
      // Sanear: normalizar tipos + asegurar cantidad numerica
      const elementosSaneados = elementos.map(e => ({
        ...e,
        tipo: normalizarTipo(e.tipo) || 'otros',
        nombre: e.nombre || e.material || e.referencia || `elemento ${e.tipo || 'otros'}`,
        cantidad: parseFloat(e.cantidad) || 0,
        unidad: e.unidad || 'un',
      }))
      const sinCantidad = elementosSaneados.filter(e => e.cantidad <= 0).length
      if (sinCantidad > 0) {
        toast(`${sinCantidad} elemento(s) sin cantidad serán omitidos`, {icon: '⚠️', duration: 3500})
      }
      const res = await presupuestoAPI.calcular({
        elementos: elementosSaneados, region,
        fc_concreto_mpa: fcMpa, fy_acero_mpa: fyMpa,
        incluir_iva: iva, incluir_aiu: true, porcentaje_aiu: aiu,
      })
      toast.success('Presupuesto APU 2026 generado')
      onDone(res.data)
    } catch(e) { toast.error(e.message) }
    finally { setLoading(false) }
  }

  return (
    <div className="animate-fade-up space-y-4">
      {/* Header del plano */}
      <div className="card p-5">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div className="flex-1">
            <h2 className="font-bold text-slate-800 text-base">{data.descripcion_proyecto}</h2>
            <div className="flex flex-wrap gap-2 mt-2">
              {data.tipo_plano && <span className="badge badge-slate">📐 {data.tipo_plano}</span>}
              {data.escala && <span className="badge badge-slate">📏 {data.escala}</span>}
              {data.sistema_estructural && (
                <span className={clsx('badge', tieneMetal ? 'badge-purple' : 'badge-blue')}>
                  {tieneMetal ? '⚙️' : '🏛'} {data.sistema_estructural}
                </span>
              )}
            </div>
            {data.especificaciones && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {data.especificaciones.fc_concreto_mpa &&
                  <span className="badge badge-blue">f'c={data.especificaciones.fc_concreto_mpa}MPa</span>}
                {data.especificaciones.fy_acero_mpa &&
                  <span className="badge badge-slate">fy={data.especificaciones.fy_acero_mpa}MPa</span>}
                {data.especificaciones.zona_sismica &&
                  <span className="badge badge-amber">Zona {data.especificaciones.zona_sismica}</span>}
              {data.escala_detectada && (
                <span className="badge badge-green text-[10px]">
                  {data.escala_detectada.split(' ')[1] || 'Escala detectada'}
                </span>
              )}
                {data.especificaciones.acero_perfiles &&
                  <span className="badge badge-purple">ASTM {data.especificaciones.acero_perfiles}</span>}
              </div>
            )}
          </div>
          <span className={clsx('flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border shrink-0', conf.cls)}>
            <ConfIcon size={13}/>{conf.lbl}
          </span>
        </div>

        {/* Resumen tipos */}
        <div className="mt-3 pt-3 border-t border-slate-100 flex flex-wrap gap-2">
          {Object.entries(tipoCount).map(([tipo, n]) => (
            <span key={tipo} className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1">
              {TIPO_ICONS[tipo]||'📦'} <strong>{n}</strong> {tipo}
            </span>
          ))}
        </div>

        {(data.correcciones?.length > 0 || data.alertas_tecnicas?.length > 0 || data.advertencias?.length > 0) && (
          <button className="mt-2 text-xs text-slate-400 flex items-center gap-1.5 hover:text-slate-600"
            onClick={()=>setShowNotas(!showNotas)}>
            {showNotas ? <ChevronDown size={13}/> : <ChevronRight size={13}/>}
            {(data.correcciones?.length||0)+(data.alertas_tecnicas?.length||0)+(data.advertencias?.length||0)} nota(s)
          </button>
        )}
        {showNotas && (
          <div className="mt-2 space-y-1 pl-3 border-l-2 border-slate-100">
            {data.correcciones?.map((c,i)=>(
              <div key={i} className="text-xs text-blue-600 flex gap-2">
                <CheckCircle size={11} className="shrink-0 mt-0.5"/>{c}
              </div>
            ))}
            {data.alertas_tecnicas?.map((a,i)=>(
              <div key={i} className="text-xs text-amber-600 flex gap-2">
                <AlertTriangle size={11} className="shrink-0 mt-0.5"/>{a}
              </div>
            ))}
            {data.advertencias?.map((a,i)=>(
              <div key={i} className="text-xs text-orange-600">⚠ {a}</div>
            ))}
          </div>
        )}
        {data.observaciones && (
          <p className="text-xs text-slate-500 mt-2 pl-3 border-l-2 border-slate-200 italic">
            {data.observaciones}
          </p>
        )}
      </div>

      {/* Banner de feedback */}
      <div className="flex items-start gap-2.5 p-3.5 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-100 rounded-xl">
        <Brain size={16} className="text-blue-500 shrink-0 mt-0.5"/>
        <div>
          <p className="text-xs font-semibold text-blue-800">Sistema de aprendizaje activo</p>
          <p className="text-xs text-blue-600 mt-0.5">
            Cada corrección que hagas aquí mejora la extracción de futuros planos.
            Haz clic en <Edit3 size={10} className="inline"/> para editar cualquier elemento.
          </p>
        </div>
      </div>

      {/* Elementos */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-slate-800 text-sm">
            Elementos estructurales
            <span className="ml-2 text-xs font-normal text-slate-400">
              ({elementos.length} identificados)
            </span>
          </h3>
          <button className="btn-secondary text-xs" onClick={add}>
            <Plus size={13}/>Agregar
          </button>
        </div>
        {elementos.length === 0
          ? <div className="text-center py-12 text-slate-400 text-sm">
              Sin elementos. <button className="text-navy-500 underline" onClick={add}>Agregar</button>
            </div>
          : <div className="space-y-2">
              {elementos.map((el, i) => (
                <ElementCard
                  key={i} el={el} idx={i}
                  onUpdate={update} onDelete={del}
                  tipoPlano={data.tipo_plano || ''} contexto={''}
                />
              ))}
            </div>
        }
      </div>

      {/* Parámetros */}
      <div className="card p-5">
        <h3 className="font-semibold text-slate-800 text-sm mb-4">Parámetros financieros</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <div>
            <label className="label-xs">AIU — Admin + Imprevistos + Utilidad</label>
            <div className="flex items-center gap-3 mt-2">
              <input type="range" min="15" max="45" value={aiu} step="1"
                onChange={e=>setAiu(parseInt(e.target.value))}
                className="flex-1 accent-navy-500"/>
              <span className="text-lg font-bold text-navy-600 w-14 text-right">{aiu}%</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              Estándar Camacol: 28% = Admin 15% + Imprevistos 5% + Utilidad 8%
            </p>
          </div>
          <div>
            <label className="label-xs">IVA</label>
            <div className="mt-2 flex items-center gap-3 p-3 bg-slate-50 rounded-xl border border-slate-200">
              <input type="checkbox" id="iva" checked={iva}
                onChange={e=>setIva(e.target.checked)} className="w-4 h-4 accent-navy-500"/>
              <label htmlFor="iva" className="text-sm text-slate-700">
                Incluir IVA 19%
                <span className="text-slate-400 text-xs ml-1">(sobre base con AIU)</span>
              </label>
            </div>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <button className="btn-secondary" onClick={onBack}>
          <ArrowLeft size={15}/>Volver
        </button>
        <button className="btn-primary px-6 py-2.5" onClick={calcular} disabled={loading}>
          {loading
            ? <><Loader2 size={17} className="animate-spin"/>Calculando APU...</>
            : <><Calculator size={17}/>Generar presupuesto APU 2026</>}
        </button>
      </div>
    </div>
  )
}
