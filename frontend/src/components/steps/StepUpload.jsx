import React, { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import toast from 'react-hot-toast'
import { Upload, FileText, Image, X, Loader2, MapPin, Info, Zap, Building, HardHat } from 'lucide-react'
import { clsx } from 'clsx'
import { planosAPI } from '../../services/api'

const REGIONES = [
  {value:'bogota',label:'Bogotá D.C.',factor:'1.00'},
  {value:'barranquilla',label:'Barranquilla',factor:'0.96'},
  {value:'medellin',label:'Medellín / Antioquia',factor:'0.93'},
  {value:'bucaramanga',label:'Bucaramanga',factor:'0.91'},
  {value:'cali',label:'Cali / Valle',factor:'0.89'},
  {value:'pereira',label:'Pereira',factor:'0.87'},
  {value:'manizales',label:'Manizales',factor:'0.86'},
  {value:'cartagena',label:'Cartagena',factor:'0.94'},
  {value:'cucuta',label:'Cúcuta',factor:'0.85'},
  {value:'ibague',label:'Ibagué',factor:'0.88'},
]
const FC_OPTIONS = [
  {v:17.2,l:'17.2 MPa (2500 PSI)'},
  {v:20.7,l:'20.7 MPa (3000 PSI) ★'},
  {v:24.2,l:'24.2 MPa (3500 PSI)'},
  {v:27.6,l:'27.6 MPa (4000 PSI)'},
  {v:28.0,l:'28.0 MPa (4000 PSI)'},
  {v:35.0,l:'35.0 MPa (5000 PSI)'},
  {v:42.0,l:'42.0 MPa (6000 PSI)'},
]
const TIPOS_ESTRUCTURA = [
  {v:'',l:'No especificado'},
  {v:'Pórticos concreto reforzado NSR-10',l:'Pórticos concreto reforzado'},
  {v:'Estructura metálica PTE/PHR A500',l:'Estructura metálica (PTE/PHR)'},
  {v:'Sistema mixto concreto y metálica',l:'Sistema mixto'},
  {v:'Mampostería estructural NSR-10',l:'Mampostería estructural'},
  {v:'Muros de contención f\'c=28MPa',l:'Muros de contención'},
]
const ZONAS = ['No especificada','Alta (Aa≥0.25g) — montañosa','Intermedia (0.10≤Aa<0.25g)','Baja (Aa<0.10g) — llanos/costa']

export default function StepUpload({ region, setRegion, contexto, setContexto,
  nombre, setNombre, fcMpa, setFcMpa, fyMpa, setFyMpa, onDone }) {

  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [logs, setLogs] = useState([])
  const [zona, setZona] = useState('')
  const [tipoEstr, setTipoEstr] = useState('')

  const addLog = (msg, type='info') => setLogs(p => [...p, {msg, type}])

  const onDrop = useCallback(acc => { setFiles(acc.slice(0,1)); setLogs([]) }, [])
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/png': ['.png'],
      'image/jpeg': ['.jpg','.jpeg'],
      'image/webp': ['.webp'],
      'application/octet-stream': ['.dwg','.dxf'],
      'application/dwg': ['.dwg'],
      'application/dxf': ['.dxf'],
    },
    maxSize: 30*1024*1024,
    onDropRejected: errs => errs.forEach(e => toast.error(`${e.file.name}: ${e.errors[0].message}`))
  })

  const buildCtx = () => {
    const p = []
    if(nombre) p.push(`Proyecto: ${nombre}`)
    if(tipoEstr) p.push(`Sistema estructural: ${tipoEstr}`)
    p.push(`f'c=${fcMpa}MPa, fy=${fyMpa}MPa`)
    if(zona) p.push(`Zona sísmica: ${zona}`)
    if(contexto) p.push(contexto)
    return p.join('. ')
  }

  const analizar = async () => {
    if(!files.length) { toast.error('Sube un plano primero'); return }
    setLoading(true); setLogs([]); setProgress(0)
    try {
      addLog(`Preparando ${files[0].name} (${(files[0].size/1024/1024).toFixed(1)}MB)...`)
      const fd = new FormData()
      fd.append('file', files[0])
      fd.append('contexto', buildCtx())
      fd.append('region', region)
      addLog('Paso 1: Reconocimiento del plano y sistema estructural (Haiku)...')
      const res = await planosAPI.extraer(fd, p => {
        setProgress(p)
        if(p===100) addLog('Paso 2: Extracción detallada de elementos y perfiles (Sonnet)...')
      })
      const data = res.data
      const sistMet = data.reconocimiento?.tiene_perfiles_metalicos
      addLog(`✓ Sistema: ${data.sistema_estructural || data.tipo_plano}`, 'ok')
      addLog(`✓ ${data.elementos?.length||0} elemento(s) identificados`, 'ok')
      addLog(`✓ Confianza: ${data.confianza}`, data.confianza==='baja'?'warn':'ok')
      if(sistMet) addLog('✓ Perfiles metálicos detectados — motor metálico activado', 'ok')
      if(data.correcciones?.length) addLog(`✓ ${data.correcciones.length} validación(es) NSR-10 aplicadas`, 'ok')
      data.advertencias?.forEach(a => addLog(`⚠ ${a}`, 'warn'))
      if(data.datos_faltantes?.length) data.datos_faltantes.slice(0,3).forEach(d => addLog(`ℹ Dato faltante: ${d}`, 'warn'))
      await new Promise(r => setTimeout(r,500))
      toast.success('Plano analizado exitosamente')
      onDone(data)
    } catch(e) {
      addLog(`✗ ${e.message}`, 'err')
      toast.error(e.message)
    } finally { setLoading(false) }
  }

  return (
    <div className="animate-fade-up space-y-4">
      {/* Banner de capacidades */}
      <div className="grid grid-cols-3 gap-3">
        {[
          {icon:Building,label:'Concreto Reforzado',sub:'Columnas, vigas, losas, zapatas'},
          {icon:HardHat,label:'Estructura Metálica',sub:'PTE, PHR, ángulos, cerchas'},
          {icon:Zap,label:'Elementos Especiales',sub:'Caissones, muros contención'},
        ].map(({icon:Icon,label,sub})=>(
          <div key={label} className="card-flat p-3 flex items-start gap-2.5">
            <div className="w-8 h-8 bg-navy-50 rounded-lg flex items-center justify-center shrink-0">
              <Icon size={15} className="text-navy-600"/>
            </div>
            <div><p className="text-xs font-semibold text-slate-700">{label}</p>
              <p className="text-[10px] text-slate-400 mt-0.5">{sub}</p></div>
          </div>
        ))}
      </div>

      {/* Datos proyecto */}
      <div className="card p-5">
        <h2 className="font-semibold text-slate-800 mb-4 flex items-center gap-2 text-sm">
          <span className="w-6 h-6 bg-navy-500 text-white rounded-lg text-xs flex items-center justify-center font-bold">1</span>
          Datos del proyecto
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
          <div className="sm:col-span-2">
            <label className="label-xs">Nombre del proyecto</label>
            <input className="input" placeholder="Ej: Cubierta metálica Coliseo Jorge Robledo — Rionegro, Antioquia"
              value={nombre} onChange={e=>setNombre(e.target.value)}/>
          </div>
          <div>
            <label className="label-xs"><MapPin size={11} className="inline mr-1"/>Región de precios</label>
            <select className="select" value={region} onChange={e=>setRegion(e.target.value)}>
              {REGIONES.map(r=><option key={r.value} value={r.value}>{r.label} (×{r.factor})</option>)}
            </select>
          </div>
          <div>
            <label className="label-xs">Sistema estructural</label>
            <select className="select" value={tipoEstr} onChange={e=>setTipoEstr(e.target.value)}>
              {TIPOS_ESTRUCTURA.map(o=><option key={o.v} value={o.v}>{o.l}</option>)}
            </select>
          </div>
          <div>
            <label className="label-xs">f'c concreto</label>
            <select className="select" value={fcMpa} onChange={e=>setFcMpa(parseFloat(e.target.value))}>
              {FC_OPTIONS.map(o=><option key={o.v} value={o.v}>{o.l}</option>)}
            </select>
          </div>
          <div>
            <label className="label-xs">Zona sísmica NSR-10</label>
            <select className="select" value={zona} onChange={e=>setZona(e.target.value)}>
              {ZONAS.map(z=><option key={z} value={z}>{z}</option>)}
            </select>
          </div>
          <div className="sm:col-span-2">
            <label className="label-xs">Observaciones adicionales (opcional)</label>
            <input className="input" placeholder="Ej: 3 pisos, uso institucional, suelo S2, cubierta arco Warren..."
              value={contexto} onChange={e=>setContexto(e.target.value)}/>
          </div>
        </div>
      </div>

      {/* Upload */}
      <div className="card p-5">
        <h2 className="font-semibold text-slate-800 mb-4 flex items-center gap-2 text-sm">
          <span className="w-6 h-6 bg-navy-500 text-white rounded-lg text-xs flex items-center justify-center font-bold">2</span>
          Subir plano estructural
        </h2>
        <div {...getRootProps()} className={clsx(
          'border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all',
          isDragActive ? 'border-navy-400 bg-navy-50/50' : 'border-slate-200 hover:border-navy-300 hover:bg-slate-50/80'
        )}>
          <input {...getInputProps()}/>
          <div className="flex flex-col items-center gap-3">
            <div className={clsx('w-16 h-16 rounded-2xl flex items-center justify-center transition-all',
              isDragActive ? 'bg-navy-100' : 'bg-slate-100')}>
              <Upload size={26} className={isDragActive ? 'text-navy-500' : 'text-slate-400'}/>
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-700">
                {isDragActive ? 'Suelta el plano aquí' : 'Arrastra el plano estructural'}
              </p>
              <p className="text-xs text-slate-400 mt-1">o <span className="text-navy-500 font-semibold">haz clic para seleccionar</span></p>
            </div>
            <div className="flex gap-2 flex-wrap justify-center">
              {['PDF','PNG','JPG','DWG','DXF'].map(e=><span key={e} className="badge badge-slate">{e}</span>)}
              <span className="badge badge-slate">Máx. 30MB</span>
              <span className="badge badge-navy">150 DPI optimizado</span>
            </div>
          </div>
        </div>

        {files.length > 0 && (
          <div className="mt-3">
            <div className="flex items-center gap-3 p-3 bg-emerald-50 rounded-xl border border-emerald-200">
              {files[0].name?.toLowerCase().endsWith('.dwg') || files[0].name?.toLowerCase().endsWith('.dxf')
                ? <span className="text-orange-500 font-bold text-sm shrink-0">DWG</span>
                : files[0].type==='application/pdf'
                ? <FileText size={18} className="text-red-500 shrink-0"/>
                : <Image size={18} className="text-blue-500 shrink-0"/>}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-700 truncate">{files[0].name}</p>
                <p className="text-xs text-slate-400">{(files[0].size/1024/1024).toFixed(2)} MB</p>
              </div>
              <button onClick={()=>setFiles([])} className="text-slate-300 hover:text-red-400 p-1">
                <X size={15}/>
              </button>
            </div>
          </div>
        )}

        {loading && progress > 0 && progress < 100 && (
          <div className="mt-3">
            <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-navy-500 to-steel-400 rounded-full transition-all duration-500"
                style={{width:`${progress}%`}}/>
            </div>
            <p className="text-xs text-slate-400 mt-1 text-right">Subiendo... {progress}%</p>
          </div>
        )}

        {logs.length > 0 && (
          <div className="terminal mt-4">
            {logs.map((l,i)=>(
              <div key={i} className={clsx(
                l.type==='ok'&&'terminal-ok', l.type==='warn'&&'terminal-warn',
                l.type==='err'&&'terminal-err',  l.type==='info'&&'terminal-info'
              )}>{l.msg}</div>
            ))}
            {loading && <div className="terminal-info animate-pulse-soft">▋</div>}
          </div>
        )}
      </div>

      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-2 p-3.5 bg-blue-50 border border-blue-100 rounded-xl flex-1">
          <Info size={14} className="text-blue-500 shrink-0 mt-0.5"/>
          <p className="text-xs text-blue-700 leading-relaxed">
            <strong>Análisis multi-pasada:</strong> Reconocimiento → Extracción (cuadros columnas, perfiles PTE/PHR, zapatas Z-1/Z-2, caissones) → Validación NSR-10.
            BD APU 2026 con <strong>2,288 actividades</strong> reales incluyendo estructura metálica.
          </p>
        </div>
        <button onClick={analizar} disabled={loading||!files.length}
          className="btn-primary px-6 py-3 text-sm shrink-0">
          {loading
            ? <><Loader2 size={17} className="animate-spin"/>Analizando...</>
            : <><Zap size={17}/>Analizar plano</>}
        </button>
      </div>
    </div>
  )
}
