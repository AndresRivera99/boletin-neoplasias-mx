# -*- coding: utf-8 -*-
"""
Created on Fri Nov  6 19:23:11 2026

@author: river
"""

"""01b_poblacion_conapo.py — Reduce el CSV de CONAPO a EntidadFederativa, Anio, Poblacion."""
from pathlib import Path
import pandas as pd

RAIZ = Path(r"D:\boletin-neoplasias-mx")
EXT  = RAIZ / "datos" / "externos"
f    = EXT / "conapo_mitad_anio.csv"

try:
    p = pd.read_csv(f, encoding="utf-8")
except UnicodeDecodeError:
    p = pd.read_csv(f, encoding="latin-1")
p.columns = [c.strip().upper() for c in p.columns]
print("Columnas del archivo:", p.columns.tolist())   # deben incluir AÑO, ENTIDAD, POBLACION

# p = p[p["AÑO"].between(2023, 2025)]
# p = p[~p["ENTIDAD"].str.contains("República", case=False)]
# pob = (p.groupby(["ENTIDAD", "AÑO"], as_index=False)["POBLACION"].sum()
#         .rename(columns={"ENTIDAD": "EntidadFederativa", "AÑO": "Anio", "POBLACION": "Poblacion"}))

'''
Agrupo por entidad y año y sumo POBLACION sobre todas las filas restantes, es decir, todas las edades (0 a 109) y ambos sexos. El resultado es la población total de cada estado al 1 de julio de cada año, que es el denominador estándar para una tasa anual.

Algunos detalles de cómo se usa esa población:

Una población por año. 2023, 2024 y 2025 tienen cada uno la suya. En 02_figuras.py se calcula la tasa de cada año con la población de ese mismo año, y el mapa muestra el promedio de las 3 tasas anuales. No se suma la población de los tres años.
No hay doble conteo. Solo pasaría si el archivo tuviera además una fila SEXO = "Total"; con solo Hombres y Mujeres, la suma es correcta.
'''


p["ANIO"] = pd.to_numeric(p["ANIO"], errors="coerce")
p = p[p["ANIO"].between(2023, 2025)]
p = p[~p["ENTIDAD"].astype(str).str.contains("República", case=False, na=False)]
pob = (p.groupby(["ENTIDAD", "ANIO"], as_index=False)["POBLACION"].sum()
         .rename(columns={"ENTIDAD": "EntidadFederativa", "ANIO": "Anio", "POBLACION": "Poblacion"}))
pob["Anio"] = pob["Anio"].astype(int)


A_BOLETIN = {"Coahuila de Zaragoza": "Coahuila",
             "Veracruz de Ignacio de la Llave": "Veracruz",
             "Michoacán de Ocampo": "Michoacán",
             "Estado de México": "México"}
pob["EntidadFederativa"] = pob.EntidadFederativa.str.strip().replace(A_BOLETIN)

boletin = set(pd.read_csv(RAIZ / "datos" / "procesados" / "anual_estatal.csv",
                          encoding="utf-8-sig").EntidadFederativa)
print("Nombres que NO empatan:", set(pob.EntidadFederativa) ^ boletin)   # debe salir set()
print("Filas:", len(pob), "(deben ser 96)")

pob.to_csv(EXT / "poblacion_conapo.csv", index=False, encoding="utf-8-sig")