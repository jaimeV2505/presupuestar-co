# -*- coding: utf-8 -*-
"""
Punto de entrada para Vercel Serverless.
Importa la app FastAPI del backend. Los modulos IA pesados
(Tesseract, PyMuPDF) no estan en requirements de Vercel y
main.py los omite limpiamente con su try/except.
"""
import os
import sys

# El backend vive en /backend del repo; incluirlo en el path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.main import app  # noqa: E402

# Vercel detecta la variable `app` como ASGI handler
