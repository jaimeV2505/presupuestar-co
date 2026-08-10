# -*- coding: utf-8 -*-
"""Autenticacion: registro, login, JWT. Seguro y estandar."""
import os
import jwt
import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Header
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
    return user


def _user_out(u: Usuario) -> dict:
    return {
        "id": u.id, "email": u.email, "nombre": u.nombre,
        "empresa": u.empresa, "telefono": u.telefono,
        "ciudad": u.ciudad, "plan": u.plan,
        "tiene_logo": bool(u.logo_b64),
        "logo_b64": u.logo_b64 or "",
        "condiciones": getattr(u, "condiciones", "") or "",
    }


@router.post("/registro")
def registro(req: RegistroRequest, db: Session = Depends(get_db)):
    try:
        email = req.email.lower().strip()
        if db.query(Usuario).filter(Usuario.email == email).first():
            raise HTTPException(400, "Ese email ya esta registrado")
        user = Usuario(
            email=email,
            password_hash=_hash_password(req.password),
            nombre=req.nombre,
            empresa=req.empresa.strip(),
            telefono=req.telefono.strip(),
            ciudad=req.ciudad,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Registro: {email}")
        return {"token": crear_token(user.id), "usuario": _user_out(user)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en registro: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(500, f"Error creando la cuenta: {type(e).__name__}")


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.email == req.email.lower().strip()).first()
    if not user or not _verify_password(req.password, user.password_hash):
        raise HTTPException(401, "Email o contrasena incorrectos")
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
    db.commit()
    return _user_out(user)
