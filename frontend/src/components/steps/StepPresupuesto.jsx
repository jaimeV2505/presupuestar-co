import React, { useState, useMemo } from 'react'
import toast from 'react-hot-toast'
import { Download, FileSpreadsheet, FileText, RotateCcw, TrendingUp, Layers,
         DollarSign, Maximize2, Info, ChevronDown, ChevronRight, AlertTriangle,
         CheckCircle, Package, Hammer } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, PieChart, Pie, Cell,
         ResponsiveContainer, Legend } from 'recharts'
import { clsx } from 'clsx'
import { exportarAPI } from '../../services/api'
import { COP, MILL, NUM, CAP_COLORS } from '../../utils/format'
import NSR10Panel from '../ui/NSR10Panel'
import SensibilidadPanel from '../ui/SensibilidadPanel'
import DesglosePanel from '../ui/DesglosePanel'

const PIE_COLORS = ['#1C3A5E','#2D6A9F','#10B981','#F59E0B','#8B5CF6',
                    '#EF4444','#06B6D4','#84CC16','#F97316','#EC4899']

function Metric({icon:Icon, label, value, sub, color='blue', large=false}) {
  const cls = {
    blue: 'bg-blue-50 text-blue-600',
    green:'bg-emerald-50 text-emerald-600',
    navy: 'bg-navy-50 text-navy-600',
    amber:'bg-amber-50 text-amber-600',
    purple:'bg-purple-50 text-purple-600',
  }
  return (
    <div className="card p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-3">
        <div className={clsx('w-9 h-9 rounded-xl flex items-center justify-center shrink-0', cls[color])}>
          <Icon size={17}/>
        </div>
        <div>
          <p className="text-[11px] text-slate-400 font-medium">{label}</p>
          <p className={clsx('font-bold text-slate-800 mt-0.5', large?'text-2xl':'text-xl')}>{value}</p>
          {sub && <p className="text-[11px] text-slate-400 mt-0.5">{sub}</p>}
        </div>
      </div>
    </div>
  )
}

function CapSection({capitulo, items}) {
  const [open, setOpen] = useState(true)
  const total = items.reduce((s,i)=>s+i.precio_total, 0)
  const dot = CAP_COLORS[capitulo] || 'bg-slate-400'
  const isMetal = capitulo === 'ESTRUCTURA METÁLICA'

  return (
    <div className="mb-2">
      <button onClick={()=>setOpen(o=>!o)}
        className={clsx(
          'w-full flex items-center justify-between px-4 py-2.5 rounded-xl text-white transition-colors',
          isMetal ? 'bg-purple-900 hover:bg-purple-800' : 'bg-slate-800 hover:bg-slate-700'
        )}>
        <div className="flex items-center gap-2.5">
          <div className={clsx('w-2.5 h-2.5 rounded-full shrink-0', dot)}/>
          <span className="text-sm font-semibold">{isMetal ? '⚙️ ' : ''}{capitulo}</span>
          <span className="text-xs text-slate-400">{items.length} ítems</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="font-bold text-sm">{COP(total)}</span>
          {open ? <ChevronDown size={14}/> : <ChevronRight size={14}/>}
        </div>
      </button>

      {open && (
        <div className="mt-1 overflow-x-auto rounded-xl border border-slate-100">
          <table className="w-full text-xs min-w-[680px]">
            <thead>
              <tr className="text-slate-400 border-b border-slate-100 bg-slate-50/50">
                <th className="text-left py-2 px-3 font-medium w-8">#</th>
                <th className="text-left py-2 px-3 font-medium w-20">Código</th>
                <th className="text-left py-2 px-3 font-medium">Ítem / Actividad</th>
                <th className="text-center py-2 px-3 font-medium w-14">Und.</th>
                <th className="text-right py-2 px-3 font-medium w-20">Cant.</th>
                <th className="text-right py-2 px-3 font-medium w-28">V. Unitario</th>
                <th className="text-right py-2 px-3 font-medium w-28">V. Total</th>
                <th className="text-left py-2 px-3 font-medium w-28 hidden lg:table-cell">Rendimiento</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item,i)=>(
                <tr key={item.idx} className={clsx(
                  'border-b border-slate-50 hover:bg-slate-50/80 transition-colors',
                  i%2===1 && 'bg-slate-50/30'
                )}>
                  <td className="py-2.5 px-3 text-slate-400 font-medium">{item.idx}</td>
                  <td className="py-2.5 px-3 font-mono text-slate-400 text-[11px]">{item.codigo||'—'}</td>
                  <td className="py-2.5 px-3 text-slate-700">
                    {item.nombre}
                    {item.notas_calculo && <span className="block text-[10px] text-slate-400 mt-0.5 italic">{item.notas_calculo}</span>}
                  </td>
                  <td className="py-2.5 px-3 text-center text-slate-500">{item.unidad}</td>
                  <td className="py-2.5 px-3 text-right font-mono">{NUM(item.cantidad)}</td>
                  <td className="py-2.5 px-3 text-right font-mono text-slate-600">{COP(item.precio_unitario)}</td>
                  <td className="py-2.5 px-3 text-right font-bold text-slate-800">{COP(item.precio_total)}</td>
                  <td className="py-2.5 px-3 text-slate-400 hidden lg:table-cell text-[11px]">{item.rendimiento||'—'}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="bg-slate-100">
                <td colSpan={6} className="py-2 px-3 text-xs font-semibold text-slate-600 text-right">
                  Subtotal {capitulo}
                </td>
                <td className="py-2 px-3 text-right font-bold text-slate-800">{COP(total)}</td>
                <td className="hidden lg:table-cell"/>
              </tr>
            </tfoot>
          </table>
        </div>
      )}
    </div>
  )
}

const CustomTooltip = ({active, payload, label}) => {
  if(!active || !payload?.length) return null
  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-lg p-3 text-xs">
      <p className="font-semibold text-slate-700 mb-1">{label}</p>
      <p className="text-navy-600 font-bold">{COP(payload[0]?.value)}</p>
    </div>
  )
}

export default function StepPresupuesto({presupuesto:p, nombre, onReset}) {
  const [exporting, setExporting] = useState(null)
  const [activeTab, setActiveTab] = useState('detalle')

  const byCapitulo = useMemo(()=>p.items.reduce((acc,item)=>{
    acc[item.capitulo]=acc[item.capitulo]||[]; acc[item.capitulo].push(item); return acc
  },{}), [p.items])

  const pieData = useMemo(()=>Object.entries(byCapitulo)
    .map(([cap,items])=>({name:cap,value:items.reduce((s,i)=>s+i.precio_total,0)}))
    .sort((a,b)=>b.value-a.value), [byCapitulo])

  const barData = pieData.slice(0,7).map(d=>({
    cap:d.name.replace('INSTALACIONES','INST.').split(' ')[0].substring(0,12),
    valor:d.value, full:d.name
  }))

  const tieneMetal = Object.keys(byCapitulo).includes('ESTRUCTURA METÁLICA')
  const totalKgMetal = p.items
    .filter(i=>i.capitulo==='ESTRUCTURA METÁLICA' && i.unidad==='Kg')
    .reduce((s,i)=>s+(i.cantidad||0),0)

  const doExport = async(fmt) => {
    setExporting(fmt)
    try {
      if(fmt==='excel') await exportarAPI.excel(p, nombre||'Proyecto')
      else await exportarAPI.pdf(p, nombre||'Proyecto')
      toast.success(`${fmt.toUpperCase()} descargado exitosamente`)
    } catch(e) { toast.error(`Error: ${e.message}`) }
    finally { setExporting(null) }
  }

  return (
    <div className="animate-fade-up space-y-5">
      {/* Header */}
      <div className="flex flex-wrap gap-3 items-start justify-between">
        <div>
          <h2 className="text-lg font-bold text-slate-800">{nombre||'Presupuesto de obra'}</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            {p.region} · {p.fc_concreto} · {p.fecha} · {p.fuente_precios}
          </p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <button className="btn-ghost text-xs" onClick={onReset}><RotateCcw size={13}/>Nuevo análisis</button>
          <button className="btn-secondary text-xs" onClick={()=>doExport('pdf')} disabled={exporting==='pdf'}>
            <FileText size={13}/>{exporting==='pdf'?'Generando...':'Descargar PDF'}
          </button>
          <button className="btn-primary text-xs" onClick={()=>doExport('excel')} disabled={exporting==='excel'}>
            <FileSpreadsheet size={13}/>{exporting==='excel'?'Generando...':'Exportar Excel APU'}
          </button>
        </div>
      </div>

      {/* HERO: Total prominente */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-navy-800 to-navy-600 text-white p-6 shadow-xl">
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/3"></div>
        <div className="relative flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-blue-200 text-xs font-medium uppercase tracking-wider mb-1">Total presupuesto de obra</p>
            <p className="text-4xl sm:text-5xl font-black tracking-tight">{COP(p.resumen.total)}</p>
            <div className="flex flex-wrap gap-x-4 gap-y-1 mt-3 text-xs text-blue-200">
              <span>📍 {p.region}</span>
              <span>🏗 {p.fc_concreto}</span>
              {p.resumen.costo_m2 && <span>📐 {COP(p.resumen.costo_m2)}/m²</span>}
              <span>📅 {p.fecha}</span>
            </div>
          </div>
          <div className="flex flex-col items-end gap-1.5 text-right">
            <div className="text-xs text-blue-200">
              <span className="block">Directo: <strong className="text-white">{MILL(p.resumen.subtotal_directo)}</strong></span>
              <span className="block">AIU {p.resumen.porcentaje_aiu}%: <strong className="text-white">{MILL(p.resumen.aiu)}</strong></span>
              {p.resumen.iva > 0 && <span className="block">IVA: <strong className="text-white">{MILL(p.resumen.iva)}</strong></span>}
            </div>
          </div>
        </div>
      </div>

      {/* Desglose APU + Flete (v7) */}
      <DesglosePanel desglose={p.desglose_apu} flete={p.flete} />

      {/* Alertas */}
      {(p.alertas_tecnicas?.length > 0 || p.correcciones?.length > 0) && (
        <NSR10Panel
          alertas={p.alertas_tecnicas}
          correcciones={p.correcciones}
          puntuacion={p.alertas_tecnicas?.length === 0 ? 100 : 100 - (p.alertas_tecnicas?.filter(a=>a.includes('ERROR')||a.startsWith('[C.')).length||0)*15}
        />
      )}

      {/* Métricas */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Metric icon={DollarSign} color="navy" label="Total con IVA"
          value={MILL(p.resumen.total)} sub="COP" large/>
        <Metric icon={TrendingUp} color="blue" label="Subtotal directo"
          value={MILL(p.resumen.subtotal_directo)} sub="Sin AIU ni IVA"/>
        {p.resumen.costo_m2
          ? <Metric icon={Maximize2} color="green" label="Costo/m²"
              value={COP(p.resumen.costo_m2)} sub={`${NUM(p.resumen.area_ref_m2||0,0)} m² referencia`}/>
          : tieneMetal
          ? <Metric icon={Package} color="purple" label="Acero estructural"
              value={`${NUM(totalKgMetal,0)} kg`} sub="Total perfiles metálicos"/>
          : null
        }
        <Metric icon={Layers} color="amber" label="Ítems presupuesto"
          value={p.items.length} sub={`${Object.keys(byCapitulo).length} capítulos`}/>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-slate-100 rounded-xl w-fit">
        {['detalle','graficas','notas'].map(tab=>(
          <button key={tab} onClick={()=>setActiveTab(tab)}
            className={clsx('px-4 py-1.5 rounded-lg text-sm font-medium transition-all capitalize',
              activeTab===tab ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700')}>
            {tab==='detalle'?'📋 Detalle APU':tab==='graficas'?'📊 Gráficas':'📝 Notas'}
          </button>
        ))}
      </div>

      {/* Tab: Detalle */}
      {activeTab === 'detalle' && (
        <div className="card p-5 animate-fade-in">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-slate-800 flex items-center gap-2">
              Presupuesto detallado
              <span className="badge badge-blue text-[10px]">APU 2026 Escuela de Contratistas</span>
              {tieneMetal && <span className="badge badge-purple text-[10px]">⚙️ Motor metálico</span>}
            </h3>
          </div>
          {Object.entries(byCapitulo).map(([cap,items])=>(
            <CapSection key={cap} capitulo={cap} items={items}/>
          ))}

          {/* Totales */}
          <div className="mt-5 border-t border-slate-200 pt-4 space-y-2">
            {[
              [`Subtotal directo (${Object.keys(byCapitulo).length} capítulos)`, p.resumen.subtotal_directo, false],
              [`AIU ${p.resumen.porcentaje_aiu}%`, p.resumen.aiu, false],
              ['Base imponible con AIU', p.resumen.subtotal_con_aiu, false],
              [`IVA ${p.resumen.porcentaje_iva?.toFixed(0)||19}%`, p.resumen.iva, false],
            ].map(([lbl,val,bold])=>(
              <div key={lbl} className="flex justify-between text-sm text-slate-600 py-0.5">
                <span>{lbl}</span>
                <span className="font-semibold">{COP(val)}</span>
              </div>
            ))}
            <div className="mt-3 bg-gradient-to-r from-navy-500 to-steel-500 text-white px-5 py-4 rounded-2xl flex justify-between items-center shadow-lg">
              <div>
                <p className="font-bold text-lg">TOTAL PRESUPUESTO</p>
                {p.resumen.costo_m2 && <p className="text-blue-200 text-xs mt-0.5">{COP(p.resumen.costo_m2)}/m²</p>}
              </div>
              <p className="text-3xl font-black">{COP(p.resumen.total)}</p>
            </div>
          </div>
        </div>
      )}

      {/* Tab: Gráficas */}
      {activeTab === 'graficas' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 animate-fade-in">
          <div className="card p-5">
            <h3 className="text-sm font-bold text-slate-700 mb-4">Distribución por capítulo</h3>
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" outerRadius={90} innerRadius={40}
                  dataKey="value" paddingAngle={2}
                  label={({name,percent})=>percent>0.05?`${name.split(' ')[0]} ${(percent*100).toFixed(0)}%`:''}
                  labelLine={false} fontSize={9}>
                  {pieData.map((_,i)=><Cell key={i} fill={PIE_COLORS[i%PIE_COLORS.length]}/>)}
                </Pie>
                <Tooltip formatter={v=>COP(v)}/>
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="card p-5">
            <h3 className="text-sm font-bold text-slate-700 mb-4">Valor por capítulo</h3>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={barData} margin={{left:-15,bottom:5}}>
                <XAxis dataKey="cap" tick={{fontSize:9}} angle={-15} textAnchor="end"/>
                <YAxis tickFormatter={v=>MILL(v)} tick={{fontSize:9}}/>
                <Tooltip content={<CustomTooltip/>} />
                <Bar dataKey="valor" radius={[6,6,0,0]}>
                  {barData.map((_,i)=>(
                    <Cell key={i} fill={PIE_COLORS[i%PIE_COLORS.length]}/>
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Tabla resumen */}
          <div className="card p-5 lg:col-span-2">
            <h3 className="text-sm font-bold text-slate-700 mb-3">Resumen por capítulo</h3>
            <table className="w-full text-sm">
              <thead><tr className="text-slate-400 border-b border-slate-100 text-xs">
                <th className="text-left py-2 font-medium">Capítulo</th>
                <th className="text-right py-2 font-medium">Ítems</th>
                <th className="text-right py-2 font-medium">Valor</th>
                <th className="text-right py-2 font-medium">%</th>
              </tr></thead>
              <tbody>
                {pieData.map((d,i)=>(
                  <tr key={d.name} className="border-b border-slate-50">
                    <td className="py-2 flex items-center gap-2">
                      <div className="w-3 h-3 rounded-sm" style={{background:PIE_COLORS[i%PIE_COLORS.length]}}/>
                      <span className="text-slate-700 text-xs">{d.name}</span>
                    </td>
                    <td className="py-2 text-right text-xs text-slate-500">{byCapitulo[d.name]?.length}</td>
                    <td className="py-2 text-right font-semibold text-xs">{COP(d.value)}</td>
                    <td className="py-2 text-right text-xs text-slate-500">
                      {((d.value/p.resumen.subtotal_directo)*100).toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Análisis de sensibilidad */}
      {activeTab === 'detalle' && (
        <SensibilidadPanel items={p.items} total={p.resumen.total}/>
      )}

      {/* Tab: Notas */}
      {activeTab === 'notas' && (
        <div className="card p-5 animate-fade-in">
          <div className="flex items-center gap-2 mb-4"><Info size={16} className="text-slate-400"/>
            <h3 className="font-bold text-slate-700 text-sm">Notas técnicas y metodología</h3>
          </div>
          <ul className="space-y-2.5">
            {p.notas?.map((nota,i)=>(
              <li key={i} className="flex gap-3 text-xs text-slate-600">
                <span className="text-navy-400 font-bold mt-0.5 shrink-0">{(i+1).toString().padStart(2,'0')}.</span>
                <span className="leading-relaxed">{nota}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
