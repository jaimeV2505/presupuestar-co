# -*- coding: utf-8 -*-
"""
Cronograma de obra — SOLO para proyectos de sector publico.

Regla de negocio: cada fila (actividad o capitulo, el usuario decide el nivel
de detalle) tiene una duracion en semanas. Si NO tiene predecesora, arranca en
la semana que el usuario indique a mano (semana_inicio). Si SI tiene
predecesora, su inicio se calcula solo: arranca justo cuando termina la
predecesora (dependencia fin-a-inicio, la unica que soportamos — es la que
cubre el 95% de los cronogramas reales de obra, sin la complejidad de
solapes/adelantos que trae un motor de ruta critica completo tipo MS Project).

MAX_FILAS: candado de volumen, igual de espiritu que MAX_PRECIOS/MAX_APUS.
"""
from typing import List, Dict, Optional

MAX_FILAS = 200


class CronogramaError(Exception):
    """Error de validacion del cronograma (ciclo, predecesora inexistente, etc.)."""
    pass


def resolver_cronograma(filas: List[Dict]) -> List[Dict]:
    """Recibe las filas tal como las guardo el usuario y devuelve la MISMA
    lista, enriquecida con semana_inicio_efectiva y semana_fin_efectiva ya
    resueltas (calculadas para las que tienen predecesora). No muta la
    entrada. Lanza CronogramaError si hay un ciclo o una predecesora que no
    existe."""
    if len(filas) > MAX_FILAS:
        raise CronogramaError(f"Maximo {MAX_FILAS} filas en el cronograma")

    por_id = {f["id"]: f for f in filas}
    resueltas: Dict[str, Dict] = {}
    en_progreso = set()  # deteccion de ciclos (DFS)

    def _resolver(fid: str, cadena: List[str]) -> Dict:
        if fid in resueltas:
            return resueltas[fid]
        if fid in en_progreso:
            raise CronogramaError(
                f"Ciclo de dependencias: {' → '.join(cadena + [fid])} — "
                f"una actividad no puede depender (directa o indirectamente) de si misma"
            )
        f = por_id.get(fid)
        if not f:
            raise CronogramaError(f"La fila '{fid}' no existe")

        en_progreso.add(fid)
        pred_id = f.get("predecesora_id")
        if pred_id:
            if pred_id not in por_id:
                raise CronogramaError(f"'{f.get('nombre', fid)}' depende de una fila que no existe")
            pred = _resolver(pred_id, cadena + [fid])
            inicio = pred["semana_fin_efectiva"]
        else:
            inicio = max(0, float(f.get("semana_inicio") or 0))

        dur = max(0.1, float(f.get("duracion_semanas") or 1))
        out = {**f, "semana_inicio_efectiva": round(inicio, 2), "semana_fin_efectiva": round(inicio + dur, 2)}
        en_progreso.discard(fid)
        resueltas[fid] = out
        return out

    for f in filas:
        _resolver(f["id"], [])

    # devolver en el mismo orden que llegaron (no el orden de resolucion del DFS)
    return [resueltas[f["id"]] for f in filas]


def duracion_total_semanas(filas_resueltas: List[Dict]) -> float:
    """La semana en que termina la ultima actividad — el largo real del cronograma."""
    if not filas_resueltas:
        return 0.0
    return max(f["semana_fin_efectiva"] for f in filas_resueltas)


def cruzar_con_avance_real(filas_resueltas: List[Dict], pct_avance_real: Optional[float]) -> List[Dict]:
    """Le pega a cada fila un mismo % de avance real global (el que ya existe
    en avances.py) para dibujar planeado-vs-real en la misma barra. Cruce
    simple a proposito: repartir el avance real POR fila individual exigiria
    mapear cada fila del cronograma a items especificos del presupuesto, y las
    filas son libres (capitulo, item, o una mezcla) — eso queda para una
    iteracion futura si hace falta ese nivel de detalle."""
    if pct_avance_real is None:
        return filas_resueltas
    return [{**f, "pct_avance_real": pct_avance_real} for f in filas_resueltas]
