import React from 'react'
import { Check } from 'lucide-react'
import { clsx } from 'clsx'

export default function Stepper({ steps, current }) {
  return (
    <div className="flex items-center">
      {steps.map((s, i) => {
        const done = s.id < current, active = s.id === current
        return (
          <React.Fragment key={s.id}>
            <div className="flex flex-col items-center gap-1">
              <div className={clsx('w-9 h-9 rounded-full flex items-center justify-center text-sm font-semibold transition-all',
                done && 'bg-emerald-500 text-white',
                active && 'bg-navy-500 text-white ring-4 ring-navy-100',
                !done && !active && 'bg-slate-200 text-slate-400')}>
                {done ? <Check size={16}/> : s.id}
              </div>
              <div className="text-center">
                <div className={clsx('text-xs font-medium', active?'text-navy-600':done?'text-emerald-600':'text-slate-400')}>{s.label}</div>
                <div className="text-[10px] text-slate-400 hidden sm:block">{s.sub}</div>
              </div>
            </div>
            {i < steps.length-1 && (
              <div className={clsx('flex-1 h-0.5 mx-3 mb-5 transition-all', s.id<current?'bg-emerald-400':'bg-slate-200')}/>
            )}
          </React.Fragment>
        )
      })}
    </div>
  )
}
