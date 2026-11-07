# -*- coding: utf-8 -*-
"""
Created on Fri Nov  6 18:50:27 2026

@author: river
"""

"""
02_figuras.py
Genera las figuras de la tesis a partir de datos/procesados.
Salida: figuras/comparativas y figuras/<cancer>, en PDF y PNG.
"""
from pathlib import Path
import json
import requests
import pandas as pd
import plotly.express as px
import plotly.io as pio

#%% Rutas y estilo
RAIZ = Path(r"D:\boletin-neoplasias-mx")
PROC = RAIZ / "datos" / "procesados"
EXT  = RAIZ / "datos" / "externos"
FIG  = RAIZ / "figuras"
EXT.mkdir(parents=True, exist_ok=True)

MOSTRAR = False                      # True = abrir cada figura en el navegador
pio.renderers.default = "browser"

NOMBRE  = {"Pulmon":   "Tráquea, bronquios y pulmón (C33–C34)",
           "Colon":    "Colon y recto (C18–C21)",
           "Pancreas": "Páncreas"}
COLOR   = {"Pulmon": "#1f77b4", "Colon": "#2ca02c", "Pancreas": "#d62728"}
ESCALA  = {"Pulmon": "Blues",   "Colon": "Greens",  "Pancreas": "Reds"}
CARPETA = {"Pulmon": "pulmon",  "Colon": "colon",   "Pancreas": "pancreas"}

def guardar(fig, carpeta, nombre, w=1200, h=800):
    destino = FIG / carpeta
    destino.mkdir(parents=True, exist_ok=True)
    fig.update_layout(template="plotly_white")
    for ext in ("pdf", "png"):
        fig.write_image(destino / f"{nombre}.{ext}", width=w, height=h, scale=3)
    if MOSTRAR:
        fig.show()
    print("✓", destino / nombre)

#%% Datos
sem   = pd.read_csv(PROC / "semanal.csv", encoding="utf-8-sig")
anual = pd.read_csv(PROC / "anual_estatal.csv", encoding="utf-8-sig")
nac   = sem[sem.EntidadFederativa == "TOTAL"].sort_values(
            ["Cancer", "Anio", "SemanaEpidemiologica"])
nac52 = nac[nac.SemanaEpidemiologica <= 52].copy()        # series semanales sin S53
orden52 = sorted(nac52.Periodo.unique()) # Agregado para combatir errores de visualización con huecos anuales
orden = sorted(sem.Periodo.unique())

#%% GeoJSON (se descarga una sola vez y queda guardado)
geo_path = EXT / "Estado.json"
if not geo_path.exists():
    url = "https://raw.githubusercontent.com/DanaRoji/GeoJsonMexico/refs/heads/main/Estado.json"
    geo_path.write_text(requests.get(url, timeout=60).text, encoding="utf-8")
geo = json.loads(geo_path.read_text(encoding="utf-8"))
geo_set = {f["properties"]["estado"] for f in geo["features"]}
A_GEO = {"Coahuila": "Coahuila de Zaragoza", "Veracruz": "Veracruz de Ignacio de la Llave"}

#%% Tasas (solo si existe el archivo de población; si no, casos absolutos)
pob_path = EXT / "poblacion_conapo.csv"
if pob_path.exists():
    pob = pd.read_csv(pob_path, encoding="utf-8-sig")
    anual = anual.merge(pob, on=["EntidadFederativa", "Anio"], how="left")
    faltan = anual[anual.Poblacion.isna()][["EntidadFederativa", "Anio"]].drop_duplicates()
    assert faltan.empty, f"Sin población para:\n{faltan}"
    anual["Valor"] = anual.Casos / anual.Poblacion * 1e5
    ETQ = "Tasa promedio anual por 100 000 hab."
else:
    print("⚠ No hay poblacion_conapo.csv: los mapas mostrarán CASOS, no tasas.")
    anual["Valor"] = anual.Casos
    ETQ = "Casos promedio anuales"

prom = anual.groupby(["Cancer", "EntidadFederativa"], as_index=False)["Valor"].mean()
prom["Entidad_Geo"] = prom.EntidadFederativa.replace(A_GEO)
sin_match = set(prom.Entidad_Geo) - geo_set
assert not sin_match, f"Estados sin match en GeoJSON: {sin_match}"

#%% FIGURA COMPARATIVA: tendencia semanal nacional (media móvil 4 semanas)
nac52["Media4"] = nac52.groupby("Cancer")["Sem_Total"].transform(
                    lambda s: s.rolling(4, min_periods=1).mean())
nac52["Neoplasia"] = nac52.Cancer.map(NOMBRE)
fig = px.line(nac52, x="Periodo", y="Media4", color="Neoplasia",
              # category_orders={"Periodo": orden},
              category_orders={"Periodo": orden52},
              color_discrete_map={NOMBRE[k]: v for k, v in COLOR.items()},
              labels={"Media4": "Casos nuevos (media móvil de 4 semanas)",
                      "Periodo": "Semana epidemiológica"})
fig.update_xaxes(dtick=8, tickangle=-45)
fig.update_layout(legend=dict(orientation="h", y=1.08, x=0))
guardar(fig, "comparativas", "tendencia_semanal_3_neoplasias")

#%% FIGURAS POR CÁNCER
for c in ["Pulmon", "Colon", "Pancreas"]:
    car = CARPETA[c]

    # (a) Mapa
    d = prom[prom.Cancer == c]
    fig = px.choropleth(d, geojson=geo, locations="Entidad_Geo",
                        featureidkey="properties.estado", color="Valor",
                        color_continuous_scale=ESCALA[c],
                        labels={"Valor": ETQ}, title=f"{NOMBRE[c]}, 2023–2025")
    fig.update_geos(fitbounds="geojson", visible=False)
    guardar(fig, car, "mapa")

    # (b) Top 10 entidades
    top = d.nlargest(10, "Valor").sort_values("Valor")
    fig = px.bar(top, x="Valor", y="EntidadFederativa", orientation="h",
                 color="Valor", color_continuous_scale=ESCALA[c],
                 labels={"Valor": ETQ, "EntidadFederativa": ""},
                 title=f"Top 10 entidades – {NOMBRE[c]}")
    guardar(fig, car, "top10_entidades")

    # (c) Casos nuevos por sexo, nacional (semanas 1–52)
    s = nac52[nac52.Cancer == c].melt(id_vars="Periodo",
            value_vars=["Nuevos_M", "Nuevos_F"], var_name="Sexo", value_name="Casos")
    s["Sexo"] = s.Sexo.map({"Nuevos_M": "Hombres", "Nuevos_F": "Mujeres"})
    fig = px.bar(s, x="Periodo", y="Casos", color="Sexo", barmode="stack",
                 # category_orders={"Periodo": orden},
                 category_orders={"Periodo": orden52},
                 color_discrete_map={"Hombres": "#3366CC", "Mujeres": "#FF6B6B"},
                 labels={"Casos": "Casos nuevos", "Periodo": "Semana epidemiológica"},
                 title=f"Casos nuevos por sexo – {NOMBRE[c]}")
    fig.update_xaxes(dtick=8, tickangle=-45)
    guardar(fig, car, "nuevos_por_sexo")

    # (d) Heatmap entidad × semana (para Anexo)
    # Qué cambia: el heatmap queda solo con las semanas 1 a 52, igual que las otras figuras semanales. 
    # Las figuras de tendencia y de sexo no necesitan cambios, porque ya usan solo las semanas 1 a 52.
    
    # p = sem[(sem.Cancer == c) & (sem.EntidadFederativa != "TOTAL")].pivot_table(
    p = sem[(sem.Cancer == c) & (sem.EntidadFederativa != "TOTAL")
            & (sem.SemanaEpidemiologica <= 52)].pivot_table(
            index="EntidadFederativa", columns="Periodo", values="Sem_Total", aggfunc="sum")
    p = p.loc[p.sum(axis=1).sort_values(ascending=False).index]
    fig = px.imshow(p, color_continuous_scale=ESCALA[c], aspect="auto",
                    labels=dict(x="Semana epidemiológica", y="", color="Casos"),
                    title=f"Casos nuevos por entidad y semana – {NOMBRE[c]}")
    guardar(fig, car, "heatmap_entidad_semana", h=1000)

print("\nListo. Revisa la carpeta:", FIG)