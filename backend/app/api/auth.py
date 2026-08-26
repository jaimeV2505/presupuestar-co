# -*- coding: utf-8 -*-
"""Autenticacion: registro, login, JWT. Seguro y estandar."""
import os
import json
import jwt
import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Header, Request
import re
from pydantic import BaseModel, field_validator
import bcrypt
from sqlalchemy.orm import Session
from app.db import get_db, Usuario

logger = logging.getLogger(__name__)
router = APIRouter()

def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False
JWT_SECRET = os.environ.get("JWT_SECRET", "")
if not JWT_SECRET:
    # Local: persistir en archivo. En serverless (filesystem solo-lectura) sera efimero.
    try:
        secret_file = "/app/data_db/.jwt_secret"
        os.makedirs(os.path.dirname(secret_file), exist_ok=True)
        if os.path.exists(secret_file):
            JWT_SECRET = open(secret_file).read().strip()
        else:
            import secrets
            JWT_SECRET = secrets.token_urlsafe(48)
            with open(secret_file, "w") as f:
                f.write(JWT_SECRET)
    except Exception:
        import secrets
        JWT_SECRET = secrets.token_urlsafe(48)
        logging.getLogger(__name__).warning(
            "JWT_SECRET efimero — define la variable JWT_SECRET en produccion "
            "o las sesiones se cerraran en cada deploy"
        )
JWT_ALG = "HS256"
JWT_DIAS = 30


EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class RegistroRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def _email(cls, v):
        v = (v or "").lower().strip()
        if not EMAIL_RE.match(v):
            raise ValueError("Email invalido")
        return v
    nombre: str
    empresa: str = ""
    telefono: str = ""
    ciudad: str = "bogota"
    acepta_terminos: bool = False   # Habeas Data: sin esto no hay cuenta

    @field_validator("password")
    @classmethod
    def _pw(cls, v):
        if len(v) < 8:
            raise ValueError("La contrasena debe tener al menos 8 caracteres")
        return v

    @field_validator("nombre")
    @classmethod
    def _nom(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError("Nombre requerido")
        return v.strip()


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def _email(cls, v):
        return (v or "").lower().strip()


def crear_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_DIAS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def usuario_actual(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> Usuario:
    """Dependency: extrae y valida el usuario del token JWT."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "No autenticado")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        user_id = int(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Sesion expirada — inicia sesion de nuevo")
    except Exception:
        raise HTTPException(401, "Token invalido")
    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not user:
        raise HTTPException(401, "Usuario no existe")
    # Degradar plan Pro vencido automaticamente
    if user.plan == "pro" and user.plan_vence:
        vence = user.plan_vence
        if vence.tzinfo is None:
            from datetime import timezone as _tz
            vence = vence.replace(tzinfo=_tz.utc)
        if vence < datetime.now(timezone.utc):
            user.plan = "gratis"
            user.plan_vence = None
            db.commit()
    return user


def _user_out(u: Usuario) -> dict:
    return {
        "id": u.id, "email": u.email, "nombre": u.nombre,
        "empresa": u.empresa, "telefono": u.telefono,
        "ciudad": u.ciudad, "plan": u.plan,
        "tiene_logo": bool(u.logo_b64),
        "logo_b64": u.logo_b64 or "",
        "condiciones": getattr(u, "condiciones", "") or "",
        "documento": getattr(u, "documento", "") or "",
        "plan_vence": u.plan_vence.strftime("%d/%m/%Y") if getattr(u, "plan_vence", None) else None,
        "pago_info": getattr(u, "pago_info", "") or "",
        "firma_b64": getattr(u, "firma_b64", "") or "",
    }


@router.post("/registro")
def registro(req: RegistroRequest, request: Request, db: Session = Depends(get_db)):
    # anti-bots: maximo 5 registros por IP por hora (la misma guardia del login)
    _ip = (request.headers.get("x-forwarded-for", "") or (request.client.host if request.client else "?")).split(",")[0].strip()
    _rl_verificar(f"registro-ip:{_ip}", db)   # el 429 si ya esta bloqueada
    _rl_fallo(f"registro-ip:{_ip}", db, max_intentos=5, bloqueo_min=60)
    if not req.acepta_terminos:
        raise HTTPException(400, "Debes aceptar los terminos y la politica de datos para crear tu cuenta")
    try:
        email = req.email.lower().strip()
        if db.query(Usuario).filter(Usuario.email == email).first():
            raise HTTPException(400, "Ese email ya esta registrado")
        user = Usuario(
            email=email,
            password_hash=_hash_password(req.password),
            nombre=req.nombre,
            empresa=req.empresa.strip(),
            # evidencia Habeas Data SIN tocar el esquema: fecha ISO en el JSON existente
            onboarding_json=json.dumps({"terminos_aceptado": datetime.now(timezone.utc).isoformat()}),
            telefono=req.telefono.strip(),
            ciudad=req.ciudad,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        try:
            from app.api.onboarding import sembrar_demo
            sembrar_demo(user, db)
        except Exception as _e:
            logger.warning(f"Siembra demo en registro: {_e}")
        logger.info(f"Registro: {email}")
        return {"token": crear_token(user.id), "usuario": _user_out(user)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en registro: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(500, f"Error creando la cuenta: {type(e).__name__}")



# ── RATE LIMITING (proteccion de fuerza bruta) ──────────────────────────────
from app.db import IntentoAcceso


def _rl_verificar(clave: str, db: Session):
    """Lanza 429 si la clave esta bloqueada."""
    r = db.query(IntentoAcceso).filter(IntentoAcceso.clave == clave).first()
    if r and r.bloqueado_hasta:
        hasta = r.bloqueado_hasta if r.bloqueado_hasta.tzinfo else r.bloqueado_hasta.replace(tzinfo=timezone.utc)
        ahora = datetime.now(timezone.utc)
        if hasta > ahora:
            mins = int((hasta - ahora).total_seconds() // 60) + 1
            raise HTTPException(429, f"Demasiados intentos — espera {mins} min e intenta de nuevo")
        r.bloqueado_hasta = None
        r.fallidos = 0
        db.commit()


def _rl_fallo(clave: str, db: Session, max_intentos: int = 5, bloqueo_min: int = 15):
    """Registra un fallo; al llegar al maximo, bloquea."""
    try:
        r = db.query(IntentoAcceso).filter(IntentoAcceso.clave == clave).first()
        if not r:
            r = IntentoAcceso(clave=clave, fallidos=0)
            db.add(r)
        r.fallidos = (r.fallidos or 0) + 1
        r.actualizado = datetime.now(timezone.utc)
        if r.fallidos >= max_intentos:
            r.bloqueado_hasta = datetime.now(timezone.utc) + timedelta(minutes=bloqueo_min)
            r.fallidos = 0
            logger.warning(f"Rate limit: {clave} bloqueada {bloqueo_min} min")
        db.commit()
    except Exception as e:
        logger.warning(f"rate limit fallo: {e}")
        db.rollback()


def _rl_exito(clave: str, db: Session):
    try:
        db.query(IntentoAcceso).filter(IntentoAcceso.clave == clave).delete()
        db.commit()
    except Exception:
        db.rollback()


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    email = req.email.lower().strip()
    _rl_verificar(f"login:{email}", db)
    user = db.query(Usuario).filter(Usuario.email == email).first()
    if not user or not _verify_password(req.password, user.password_hash):
        _rl_fallo(f"login:{email}", db, max_intentos=5, bloqueo_min=15)
        raise HTTPException(401, "Email o contrasena incorrectos")
    _rl_exito(f"login:{email}", db)
    return {"token": crear_token(user.id), "usuario": _user_out(user)}


@router.get("/yo")
def yo(user: Usuario = Depends(usuario_actual)):
    return _user_out(user)


class PerfilUpdate(BaseModel):
    nombre: str = None
    empresa: str = None
    telefono: str = None
    ciudad: str = None
    logo_b64: str = None  # data URL o base64 del logo
    condiciones: str = None  # condiciones estandar del contratista
    documento: str = None     # cedula/NIT (aparece en el contrato)
    pago_info: str = None     # cuenta bancaria (forma de pago del contrato)
    firma_b64: str = None     # firma manuscrita del contratista


@router.put("/perfil")
def actualizar_perfil(req: PerfilUpdate, user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    if req.nombre is not None: user.nombre = req.nombre.strip()[:120]
    if req.empresa is not None: user.empresa = req.empresa.strip()[:160]
    if req.telefono is not None: user.telefono = req.telefono.strip()[:30]
    if req.ciudad is not None: user.ciudad = req.ciudad
    if req.logo_b64 is not None:
        if len(req.logo_b64) > 700_000:
            raise HTTPException(400, "Logo muy grande — usa una imagen de menos de 500KB")
        user.logo_b64 = req.logo_b64
    if req.condiciones is not None:
        user.condiciones = req.condiciones[:3000]
    if req.documento is not None:
        user.documento = req.documento.strip()[:30]
    if req.pago_info is not None:
        user.pago_info = req.pago_info.strip()[:200]
    if req.firma_b64 is not None:
        f = req.firma_b64
        user.firma_b64 = f if (f.startswith("data:image") and len(f) < 600_000) else ""

    db.commit()
    return _user_out(user)


# ── RECUPERACION DE CONTRASENA ───────────────────────────────────────────────
import hashlib
import secrets as _secrets
from datetime import timedelta as _td

APP_URL = os.environ.get("APP_URL", "https://presupuestar-co.vercel.app").rstrip("/")


def _enviar_email_reset(destino: str, nombre: str, link: str) -> bool:
    api_key = os.environ.get("RESEND_API_KEY", "").strip()
    if not api_key:
        logger.warning("RESEND_API_KEY no configurada — email de reset no enviado")
        return False
    try:
        import httpx
        html = f"""
        <div style="font-family:sans-serif;max-width:480px;margin:0 auto">
          <h2 style="color:#1C3A5E">Restablece tu contrasena</h2>
          <p>Hola {nombre or ''},</p>
          <p>Recibimos una solicitud para restablecer la contrasena de tu cuenta
          en <b>PresupuestarCO</b>. Toca el boton (valido por 30 minutos):</p>
          <p style="text-align:center;margin:28px 0">
            <a href="{link}" style="background:#1C3A5E;color:#fff;padding:12px 28px;
               border-radius:10px;text-decoration:none;font-weight:bold">
               Crear nueva contrasena</a>
          </p>
          <p style="color:#64748B;font-size:13px">Si no fuiste tu, ignora este
          correo — tu cuenta sigue segura y nada cambia.</p>
        </div>"""
        r = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "from": "PresupuestarCO <onboarding@resend.dev>",
                "to": [destino],
                "subject": "Restablece tu contrasena — PresupuestarCO",
                "html": html,
            }, timeout=15)
        ok = r.status_code in (200, 201)
        if not ok:
            logger.warning(f"Resend reset fallo {r.status_code}: {r.text[:200]}")
        return ok
    except Exception as e:
        logger.warning(f"Email reset no enviado: {e}")
        return False


class OlvideRequest(BaseModel):
    email: str


@router.post("/olvide")
def olvide(req: OlvideRequest, db: Session = Depends(get_db)):
    """Siempre responde ok (sin revelar si el email existe)."""
    email = req.email.strip().lower()
    _rl_verificar(f"olvide:{email}", db)
    _rl_fallo(f"olvide:{email}", db, max_intentos=3, bloqueo_min=60)
    user = db.query(Usuario).filter(Usuario.email == email).first()
    if user:
        token = _secrets.token_urlsafe(32)
        user.reset_token_hash = hashlib.sha256(token.encode()).hexdigest()
        user.reset_expira = datetime.now(timezone.utc) + _td(minutes=30)
        db.commit()
        link = f"{APP_URL}/restablecer?email={email}&token={token}"
        enviado = _enviar_email_reset(email, user.nombre, link)
        logger.info(f"Reset solicitado para {email} — email {'enviado' if enviado else 'NO enviado'}")
    return {"ok": True, "mensaje": "Si el correo existe, te enviamos el enlace de recuperacion"}


class RestablecerRequest(BaseModel):
    email: str
    token: str
    password: str

    @field_validator("password")
    @classmethod
    def _pw(cls, v):
        if len(v) < 8:
            raise ValueError("La contrasena debe tener al menos 8 caracteres")
        return v


@router.post("/restablecer")
def restablecer(req: RestablecerRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    _rl_verificar(f"reset:{email}", db)
    user = db.query(Usuario).filter(Usuario.email == email).first()
    generico = HTTPException(400, "El enlace no es valido o ya expiro — pide uno nuevo")
    if not user or not user.reset_token_hash or not user.reset_expira:
        raise generico
    expira = user.reset_expira if user.reset_expira.tzinfo else user.reset_expira.replace(tzinfo=timezone.utc)
    if expira < datetime.now(timezone.utc):
        raise generico
    import hmac as _hmac
    recibido = hashlib.sha256(req.token.encode()).hexdigest()
    if not _hmac.compare_digest(recibido, user.reset_token_hash):
        _rl_fallo(f"reset:{email}", db, max_intentos=10, bloqueo_min=30)
        raise generico
    user.password_hash = _hash_password(req.password)
    user.reset_token_hash = None
    user.reset_expira = None
    db.commit()
    logger.info(f"Contrasena restablecida para {email}")
    return {"ok": True, "mensaje": "Contrasena actualizada — ya puedes iniciar sesion"}
