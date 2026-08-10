from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict, Any

class ElementoEstructural(BaseModel):
    tipo: Optional[str] = "otros"
    referencia: Optional[str] = None
    nombre: Optional[str] = ""
    cantidad: Optional[float] = 0
    unidad: Optional[str] = "un"

    @field_validator('tipo', mode='before')
    @classmethod
    def _coerce_tipo(cls, v):
        return v if v else "otros"

    @field_validator('nombre', mode='before')
    @classmethod
    def _coerce_nombre(cls, v):
        return v if v else ""

    @field_validator('cantidad', mode='before')
    @classmethod
    def _coerce_cantidad(cls, v):
        if v is None or v == "":
            return 0
        if isinstance(v, str):
            try:
                return float(v.replace(',', '.'))
            except ValueError:
                return 0
        return v

    @field_validator('unidad', mode='before')
    @classmethod
    def _coerce_unidad(cls, v):
        return v if v else "un"
    dimension: Optional[str] = None
    dimension_ancho_cm: Optional[float] = None
    dimension_alto_cm: Optional[float] = None
    dimension_largo_m: Optional[float] = None
    altura_libre_m: Optional[float] = None
    espesor_cm: Optional[float] = None
    area_m2: Optional[float] = None
    dimension_diametro_cm: Optional[float] = None
    material: Optional[str] = None
    acero_longitudinal: Optional[str] = None
    acero_transversal: Optional[str] = None
    ubicacion: Optional[str] = None
    notas: Optional[str] = None
    confianza_extraccion: Optional[float] = None
    dato_estimado: Optional[bool] = False

class PresupuestoRequest(BaseModel):
    elementos: List[ElementoEstructural]
    region: str = "bogota"
    fc_concreto_mpa: float = 20.7
    fy_acero_mpa: float = 420.0
    zona_sismica: str = "alta"
    incluir_iva: bool = True
    incluir_aiu: bool = True
    porcentaje_aiu: float = 28.0
    proyecto_nombre: Optional[str] = "Proyecto"

class ItemPresupuesto(BaseModel):
    idx: int
    capitulo: str
    codigo: Optional[str] = None
    nombre: str
    unidad: str
    cantidad: float
    precio_unitario: float
    precio_total: float
    rendimiento: Optional[str] = None
    notas_calculo: Optional[str] = None

class ResumenFinanciero(BaseModel):
    subtotal_directo: float
    aiu: float
    subtotal_con_aiu: float
    iva: float
    total: float
    costo_m2: Optional[float] = None
    area_ref_m2: Optional[float] = None
    porcentaje_aiu: float
    porcentaje_iva: float

class PresupuestoResponse(BaseModel):
    items: List[ItemPresupuesto]
    resumen: ResumenFinanciero
    region: str
    fc_concreto: str
    fecha: str
    fuente_precios: str
    notas: List[str]
    correcciones: Optional[List[str]] = []
    alertas_tecnicas: Optional[List[str]] = []
    desglose_apu: Optional[Dict] = None
    flete: Optional[Dict] = None
