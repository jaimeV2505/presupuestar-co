# -*- coding: utf-8 -*-
"""Base de datos SQLite — simple, confiable, cero configuracion."""
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime, timezone

# Postgres en produccion (Vercel/Neon via DATABASE_URL), SQLite en local
DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL") or ""

if DATABASE_URL:
    # Normalizar scheme: Neon/Vercel dan postgres:// pero SQLAlchemy quiere postgresql://
    url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://") and "+psycopg2" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    engine = create_engine(url, pool_pre_ping=True, pool_size=2, max_overflow=3)
    ES_POSTGRES = True
else:
    DB_PATH = os.environ.get("DB_PATH", "/app/data_db/presupuestar.db")
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    engine = create_engine(
        f"sqlite:///{DB_PATH}",
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )
    ES_POSTGRES = False
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def utcnow():
    return datetime.now(timezone.utc)


class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    nombre = Column(String(120), nullable=False)
    empresa = Column(String(160), default="")
    telefono = Column(String(30), default="")
    ciudad = Column(String(60), default="bogota")
    logo_b64 = Column(Text, default="")          # logo en base64 para PDF/Excel
    condiciones = Column(Text, default="")       # condiciones estandar auto-incluidas
    documento = Column(String(30), default="")   # cedula/NIT del contratista (para el contrato)
    pago_info = Column(String(200), default="")  # cuenta bancaria para forma de pago
    slug = Column(String(80), unique=True, nullable=True, index=True)  # perfil publico /c/{slug}
    firma_b64 = Column(Text, default="")         # firma manuscrita del contratista (PNG base64)
    onboarding_json = Column(Text, default="{}")  # {tipo, flags de misiones, cerrado}
    reset_token_hash = Column(String(64), nullable=True)   # sha256 del token de recuperacion
    reset_expira = Column(DateTime, nullable=True)
    plan = Column(String(20), default="gratis")  # gratis | pro
    plan_vence = Column(DateTime, nullable=True)  # cuando expira el plan pro
    presupuestos_mes = Column(Integer, default=0)
    mes_actual = Column(String(7), default="")   # "2026-08" para reset mensual
    creado = Column(DateTime, default=utcnow)


class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    nombre = Column(String(160), nullable=False)
    telefono = Column(String(30), default="")
    notas = Column(Text, default="")
    creado = Column(DateTime, default=utcnow)


class Proyecto(Base):
    __tablename__ = "proyectos"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    numero = Column(String(30), default="", index=True)   # COT-2026-0001
    nombre = Column(String(200), nullable=False)
    es_demo = Column(Boolean, default=False)     # proyecto de ejemplo del onboarding
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True, index=True)
    cliente_nombre = Column(String(160), default="")
    cliente_telefono = Column(String(30), default="")
    direccion = Column(String(250), default="")
    region = Column(String(60), default="bogota")
    estado = Column(String(20), default="borrador")  # borrador | enviado | aceptado
    items_json = Column(Text, default="[]")     # lista de items del presupuesto
    aiu_json = Column(Text, default='{"admin":15,"imprevistos":5,"utilidad":8,"aplicar":true,"iva_sobre_utilidad":true}')
    notas = Column(Text, default="")
    contrato_json = Column(Text, default="{}")  # {plazo_dias, anticipo_pct, fecha_inicio, lugar}
    share_token = Column(String(40), unique=True, index=True, nullable=True)
    creado = Column(DateTime, default=utcnow)
    actualizado = Column(DateTime, default=utcnow, onupdate=utcnow)


class EventoShare(Base):
    __tablename__ = "eventos_share"
    id = Column(Integer, primary_key=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"), nullable=False, index=True)
    tipo = Column(String(20), nullable=False)  # visto | aceptado | rechazado
    nombre_firma = Column(String(160), default="")     # quien firma la aceptacion
    firma_imagen = Column(Text, default="")            # firma dibujada/subida (base64 PNG)
    documento_firma = Column(String(30), default="")   # cedula/NIT del firmante
    user_agent = Column(String(300), default="")
    creado = Column(DateTime, default=utcnow)


class TicketSoporte(Base):
    __tablename__ = "tickets_soporte"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    asunto = Column(String(200), nullable=False)
    descripcion = Column(Text, default="")
    contexto = Column(String(300), default="")   # pagina, plan, navegador
    fotos_json = Column(Text, default="[]")      # evidencia (max 2 imagenes base64)
    estado = Column(String(20), default="abierto")  # abierto | resuelto
    respuesta = Column(Text, default="")            # respuesta del equipo de soporte
    email_enviado = Column(Boolean, default=False)
    creado = Column(DateTime, default=utcnow)
    respondido = Column(DateTime, nullable=True)


class SolicitudPro(Base):
    __tablename__ = "solicitudes_pro"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    metodo = Column(String(30), default="nequi")      # nequi | bancolombia | otro
    referencia = Column(String(120), default="")      # nro de comprobante que reporta el usuario
    estado = Column(String(20), default="pendiente")  # pendiente | aprobada | rechazada
    creado = Column(DateTime, default=utcnow)
    resuelto = Column(DateTime, nullable=True)


class Encuesta(Base):
    __tablename__ = "encuestas"
    id = Column(Integer, primary_key=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"), nullable=False, unique=True, index=True)
    estrellas = Column(Integer, default=0)          # 1-5
    recomendaria = Column(Boolean, default=True)
    comentario = Column(Text, default="")
    publico = Column(Boolean, default=False)   # el contratista elige mostrarlo en su perfil
    creado = Column(DateTime, default=utcnow)


class Gasto(Base):
    __tablename__ = "gastos"
    id = Column(Integer, primary_key=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"), nullable=False, index=True)
    categoria = Column(String(30), default="materiales")  # materiales|nomina|transporte|herramienta|otros
    descripcion = Column(String(300), nullable=False)
    valor = Column(Integer, nullable=False)
    foto_b64 = Column(Text, default="")   # recibo/factura (opcional)
    creado = Column(DateTime, default=utcnow)


class CuentaCobro(Base):
    __tablename__ = "cuentas_cobro"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"), nullable=False, index=True)
    avance_id = Column(Integer, nullable=True)         # corte que sustenta el cobro
    numero = Column(String(20), default="")            # CC-2026-0001 consecutivo por usuario
    concepto = Column(Text, default="")
    valor_corte = Column(Integer, default=0)           # ejecutado de este corte
    anticipo_pct = Column(Integer, default=0)          # % amortizado (del contrato)
    amortizacion = Column(Integer, default=0)
    neto = Column(Integer, default=0)                  # a cobrar
    retencion = Column(Integer, default=0)       # retegarantia del corte
    tipo = Column(String(15), default="corte")    # corte | retegarantia
    estado = Column(String(20), default="enviada")     # enviada | pagada
    creado = Column(DateTime, default=utcnow)
    pagado = Column(DateTime, nullable=True)


class PagoWompi(Base):
    __tablename__ = "pagos_wompi"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    referencia = Column(String(80), unique=True, nullable=False, index=True)
    monto_centavos = Column(Integer, nullable=False)
    estado = Column(String(20), default="creado")  # creado | APPROVED | DECLINED | VOIDED | ERROR
    transaction_id = Column(String(80), default="")
    medio = Column(String(40), default="")          # CARD | NEQUI | PSE | BANCOLOMBIA_TRANSFER...
    creado = Column(DateTime, default=utcnow)
    actualizado = Column(DateTime, nullable=True)


class IntentoAcceso(Base):
    """Rate limiting de login/olvide/restablecer — compatible con serverless."""
    __tablename__ = "intentos_acceso"
    id = Column(Integer, primary_key=True)
    clave = Column(String(200), unique=True, nullable=False, index=True)  # ej: login:email
    fallidos = Column(Integer, default=0)
    bloqueado_hasta = Column(DateTime, nullable=True)
    actualizado = Column(DateTime, default=utcnow)


class InteraccionCliente(Base):
    """Participacion del cliente en su link: reacciones y comentarios sobre avances."""
    __tablename__ = "interacciones_cliente"
    id = Column(Integer, primary_key=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"), nullable=False, index=True)
    avance_id = Column(Integer, ForeignKey("avances.id"), nullable=False, index=True)
    tipo = Column(String(12), default="reaccion")   # reaccion | comentario
    valor = Column(String(300), default="")          # emoji o texto
    nombre = Column(String(120), default="")         # quien (nombre de la firma o "Cliente")
    creado = Column(DateTime, default=utcnow)


class Abono(Base):
    """Pagos parciales de una cuenta de cobro — la norma en obra colombiana."""
    __tablename__ = "abonos"
    id = Column(Integer, primary_key=True)
    cuenta_id = Column(Integer, ForeignKey("cuentas_cobro.id"), nullable=False, index=True)
    monto = Column(Integer, nullable=False)
    nota = Column(String(150), default="")
    creado = Column(DateTime, default=utcnow)


class Otrosi(Base):
    """Adicionales de obra: items extra aprobados por el cliente con nueva firma."""
    __tablename__ = "otrosies"
    id = Column(Integer, primary_key=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"), nullable=False, index=True)
    numero = Column(Integer, default=1)              # Otrosi N.1, N.2...
    items_json = Column(Text, default="[]")          # items adicionales (mismo formato)
    totales_json = Column(Text, default="{}")        # congelado al aprobar (mismo AIU del contrato)
    estado = Column(String(15), default="propuesto")  # propuesto | aprobado | rechazado
    motivo = Column(String(300), default="")          # "El cliente pidio ademas..."
    nombre_firma = Column(String(120), default="")
    documento_firma = Column(String(30), default="")
    firma_imagen = Column(Text, default="")
    creado = Column(DateTime, default=utcnow)
    resuelto = Column(DateTime, nullable=True)        # fecha de aprobacion/rechazo


class MensajeSoporte(Base):
    """Hilo de conversacion de cada ticket."""
    __tablename__ = "mensajes_soporte"
    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("tickets_soporte.id"), nullable=False, index=True)
    autor = Column(String(10), default="usuario")  # usuario | soporte
    texto = Column(Text, nullable=False)
    creado = Column(DateTime, default=utcnow)


class Notificacion(Base):
    __tablename__ = "notificaciones"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    proyecto_id = Column(Integer, nullable=True)
    tipo = Column(String(30), default="info")   # visto|firmado|rechazado|entrega|pendientes|encuesta|soporte
    titulo = Column(String(200), nullable=False)
    cuerpo = Column(String(400), default="")
    leida = Column(Boolean, default=False)
    creado = Column(DateTime, default=utcnow)


class Avance(Base):
    __tablename__ = "avances"
    id = Column(Integer, primary_key=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"), nullable=False, index=True)
    titulo = Column(String(160), nullable=False)
    descripcion = Column(Text, default="")
    porcentaje = Column(Integer, default=0)        # avance ponderado por valor 0-100
    valor_ejecutado = Column(Integer, default=0)   # $ ejecutado segun % por actividad
    items_json = Column(Text, default="[]")        # detalle por actividad: [{id, descripcion, valor_item, pct, valor_ejec}]
    fotos_json = Column(Text, default="[]")        # lista de fotos base64 (max 3)
    creado = Column(DateTime, default=utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)
    # Migracion simple: agregar columnas nuevas a BDs existentes
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            if ES_POSTGRES:
                for sql in [
                    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS condiciones TEXT DEFAULT ''",
                    "ALTER TABLE proyectos ADD COLUMN IF NOT EXISTS numero VARCHAR(30) DEFAULT ''",
                    "ALTER TABLE eventos_share ADD COLUMN IF NOT EXISTS nombre_firma VARCHAR(160) DEFAULT ''",
                    "ALTER TABLE eventos_share ADD COLUMN IF NOT EXISTS documento_firma VARCHAR(30) DEFAULT ''",
                    "ALTER TABLE avances ADD COLUMN IF NOT EXISTS valor_ejecutado INTEGER DEFAULT 0",
                    "ALTER TABLE avances ADD COLUMN IF NOT EXISTS items_json TEXT DEFAULT '[]'",
                    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS documento VARCHAR(30) DEFAULT ''",
                    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS pago_info VARCHAR(200) DEFAULT ''",
                    "ALTER TABLE proyectos ADD COLUMN IF NOT EXISTS contrato_json TEXT DEFAULT '{}'",
                    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS plan_vence TIMESTAMP",
                    "ALTER TABLE tickets_soporte ADD COLUMN IF NOT EXISTS respuesta TEXT DEFAULT ''",
                    "ALTER TABLE tickets_soporte ADD COLUMN IF NOT EXISTS respondido TIMESTAMP",
                    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS slug VARCHAR(80)",
                    "ALTER TABLE eventos_share ADD COLUMN IF NOT EXISTS firma_imagen TEXT DEFAULT ''",
                    "ALTER TABLE encuestas ADD COLUMN IF NOT EXISTS publico BOOLEAN DEFAULT FALSE",
                    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS firma_b64 TEXT DEFAULT ''",
                    "ALTER TABLE proyectos ADD COLUMN IF NOT EXISTS cliente_id INTEGER",
                    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS onboarding_json TEXT DEFAULT '{}'",
                    "ALTER TABLE proyectos ADD COLUMN IF NOT EXISTS es_demo BOOLEAN DEFAULT FALSE",
                    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS reset_token_hash VARCHAR(64)",
                    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS reset_expira TIMESTAMP",
                    "ALTER TABLE cuentas_cobro ADD COLUMN IF NOT EXISTS retencion INTEGER DEFAULT 0",
                    "ALTER TABLE cuentas_cobro ADD COLUMN IF NOT EXISTS tipo VARCHAR(15) DEFAULT 'corte'",
                ]:
                    conn.execute(text(sql))
                conn.commit()
            else:
                migs = [
                    ("usuarios", "condiciones", "ALTER TABLE usuarios ADD COLUMN condiciones TEXT DEFAULT ''"),
                    ("proyectos", "numero", "ALTER TABLE proyectos ADD COLUMN numero VARCHAR(30) DEFAULT ''"),
                    ("eventos_share", "nombre_firma", "ALTER TABLE eventos_share ADD COLUMN nombre_firma VARCHAR(160) DEFAULT ''"),
                    ("eventos_share", "documento_firma", "ALTER TABLE eventos_share ADD COLUMN documento_firma VARCHAR(30) DEFAULT ''"),
                    ("avances", "valor_ejecutado", "ALTER TABLE avances ADD COLUMN valor_ejecutado INTEGER DEFAULT 0"),
                    ("avances", "items_json", "ALTER TABLE avances ADD COLUMN items_json TEXT DEFAULT '[]'"),
                    ("usuarios", "documento", "ALTER TABLE usuarios ADD COLUMN documento VARCHAR(30) DEFAULT ''"),
                    ("usuarios", "pago_info", "ALTER TABLE usuarios ADD COLUMN pago_info VARCHAR(200) DEFAULT ''"),
                    ("proyectos", "contrato_json", "ALTER TABLE proyectos ADD COLUMN contrato_json TEXT DEFAULT '{}'"),
                    ("usuarios", "plan_vence", "ALTER TABLE usuarios ADD COLUMN plan_vence TIMESTAMP"),
                    ("tickets_soporte", "respuesta", "ALTER TABLE tickets_soporte ADD COLUMN respuesta TEXT DEFAULT ''"),
                    ("tickets_soporte", "respondido", "ALTER TABLE tickets_soporte ADD COLUMN respondido TIMESTAMP"),
                    ("usuarios", "slug", "ALTER TABLE usuarios ADD COLUMN slug VARCHAR(80)"),
                    ("eventos_share", "firma_imagen", "ALTER TABLE eventos_share ADD COLUMN firma_imagen TEXT DEFAULT ''"),
                    ("encuestas", "publico", "ALTER TABLE encuestas ADD COLUMN publico BOOLEAN DEFAULT 0"),
                    ("usuarios", "firma_b64", "ALTER TABLE usuarios ADD COLUMN firma_b64 TEXT DEFAULT ''"),
                    ("proyectos", "cliente_id", "ALTER TABLE proyectos ADD COLUMN cliente_id INTEGER"),
                    ("usuarios", "onboarding_json", "ALTER TABLE usuarios ADD COLUMN onboarding_json TEXT DEFAULT '{}'"),
                    ("proyectos", "es_demo", "ALTER TABLE proyectos ADD COLUMN es_demo BOOLEAN DEFAULT 0"),
                    ("usuarios", "reset_token_hash", "ALTER TABLE usuarios ADD COLUMN reset_token_hash VARCHAR(64)"),
                    ("usuarios", "reset_expira", "ALTER TABLE usuarios ADD COLUMN reset_expira TIMESTAMP"),
                    ("cuentas_cobro", "retencion", "ALTER TABLE cuentas_cobro ADD COLUMN retencion INTEGER DEFAULT 0"),
                    ("cuentas_cobro", "tipo", "ALTER TABLE cuentas_cobro ADD COLUMN tipo VARCHAR(15) DEFAULT 'corte'"),
                ]
                for tabla, col, sql in migs:
                    cols = [r[1] for r in conn.execute(text(f"PRAGMA table_info({tabla})"))]
                    if col not in cols:
                        conn.execute(text(sql))
                conn.commit()
    except Exception:
        pass
    _backfill_clientes()


def _backfill_clientes():
    """Convierte los cliente_nombre historicos en entidades Cliente (una vez)."""
    db = SessionLocal()
    try:
        huerfanos = (db.query(Proyecto)
                     .filter(Proyecto.cliente_id.is_(None), Proyecto.cliente_nombre != "", Proyecto.es_demo == False)  # noqa: E712
                     .limit(500).all())
        for p in huerfanos:
            nombre = (p.cliente_nombre or "").strip()
            if not nombre:
                continue
            c = (db.query(Cliente)
                 .filter(Cliente.user_id == p.user_id, Cliente.nombre.ilike(nombre))
                 .first())
            if not c:
                c = Cliente(user_id=p.user_id, nombre=nombre,
                            telefono=(p.cliente_telefono or "").strip()[:30])
                db.add(c)
                db.flush()
            p.cliente_id = c.id
        db.commit()
    except Exception as e:
        logger.warning(f"Backfill clientes: {e}")
        db.rollback()
    finally:
        db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
