#!/usr/bin/env node
// ═══════════════════════════════════════════════════════════════════════════
// VERIFICAR_JSX — el cazador de hermanos sueltos y tags sin cerrar.
// Escaner char-a-char que respeta {expresiones} dentro de los atributos
// (los `=>` de las arrow functions ya no lo engañan). Sin npm, sin red.
// Uso:  node scripts/verificar_jsx.mjs            (todos los .jsx de src)
// Nace del incidente del panel ⇄rinde (16/8/2026).
// ═══════════════════════════════════════════════════════════════════════════
import { readFileSync, readdirSync, statSync } from 'fs'
import { join } from 'path'

const VOID = new Set(['input', 'br', 'img', 'hr', 'textarea', 'meta', 'link'])

function verificar(ruta) {
  let src = readFileSync(ruta, 'utf8')
  src = src.replace(/'(?:[^'\\\n]|\\.)*'/g, m => m.replace(/[^\n]/g, ' '))
           .replace(/"(?:[^"\\\n]|\\.)*"/g, m => m.replace(/[^\n]/g, ' '))
           .replace(/`(?:[^`\\]|\\.)*`/g, m => m.replace(/[^\n]/g, ' '))
  const linea = idx => src.slice(0, idx).split('\n').length
  const pila = []
  let i = 0
  while (i < src.length) {
    if (src[i] !== '<') { i++; continue }
    // ¿arranque de tag? el siguiente debe ser letra o '/'
    const sig = src[i + 1]
    if (!sig || (!/[A-Za-z/]/.test(sig))) { i++; continue }
    const cierra = sig === '/'
    let j = i + (cierra ? 2 : 1)
    let nombre = ''
    while (j < src.length && /[A-Za-z0-9.]/.test(src[j])) nombre += src[j++]
    if (!nombre) { i++; continue }
    // avanzar hasta el '>' REAL respetando profundidad de llaves
    let depth = 0, auto = false
    while (j < src.length) {
      const ch = src[j]
      if (ch === '{') depth++
      else if (ch === '}') depth--
      else if (ch === '>' && depth === 0) { auto = src[j - 1] === '/'; j++; break }
      j++
    }
    const ln = linea(i)
    if (!auto && !VOID.has(nombre)) {
      if (cierra) {
        const top = pila.pop()
        if (!top || top.n !== nombre)
          return `❌ ${ruta}: linea ${ln} cierra </${nombre}> pero la pila tenia ${top ? `<${top.n}> (linea ${top.l})` : 'NADA'}`
      } else pila.push({ n: nombre, l: ln })
    }
    if (auto && cierra) { /* </x/> imposible */ }
    i = j
  }
  if (pila.length) return `❌ ${ruta}: sin cerrar → ${pila.map(x => `<${x.n}> linea ${x.l}`).join(', ')}`
  return null
}

function jsxDe(dir) {
  const out = []
  for (const f of readdirSync(dir)) {
    const p = join(dir, f)
    if (statSync(p).isDirectory()) out.push(...jsxDe(p))
    else if (f.endsWith('.jsx')) out.push(p)
  }
  return out
}

const objetivos = process.argv[2] ? [process.argv[2]] : jsxDe('frontend/src')
let rotos = 0
for (const f of objetivos) {
  const err = verificar(f)
  if (err) { console.log(err); rotos++ }
}
if (rotos) { console.log(`\n${rotos} archivo(s) con tags rotos — esbuild va a reventar`); process.exit(1) }
console.log(`OK: ${objetivos.length} .jsx con tags balanceados`)
