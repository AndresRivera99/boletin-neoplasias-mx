# -*- coding: utf-8 -*-
"""
Created on Fri Nov  6 20:17:31 2026

@author: river
"""

"""00_inventario_pdfs.py — Huella SHA256 de cada PDF usado (los PDF no se suben)."""
from pathlib import Path
import hashlib
import pandas as pd

RAIZ = Path(r"D:\boletin-neoplasias-mx")
filas = [{"Anio": p.parent.name, "Archivo": p.name, "Bytes": p.stat().st_size,
          "SHA256": hashlib.sha256(p.read_bytes()).hexdigest()}
         for p in sorted((RAIZ / "pdfs").rglob("*.pdf"))]
pd.DataFrame(filas).to_csv(RAIZ / "datos" / "fuentes_pdfs.csv", index=False, encoding="utf-8-sig")
print(len(filas), "PDFs inventariados")