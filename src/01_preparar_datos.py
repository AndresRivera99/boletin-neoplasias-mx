# -*- coding: utf-8 -*-
"""
Created on Fri Nov  6 18:44:02 2026

@author: river
"""

"""
01_preparar_datos.py
Lee el CSV exportado de Power Query, valida la extracción y genera las
tablas procesadas (semanal, anual estatal y anual nacional).
"""
from pathlib import Path
import pandas as pd

#%% Rutas
RAIZ    = Path(r"D:\boletin-neoplasias-mx")
ENTRADA = RAIZ / "datos" / "boletin_neoplasias.csv"
SALIDA  = RAIZ / "datos" / "procesados"
SALIDA.mkdir(parents=True, exist_ok=True)

CLAVE = ["Cancer", "Anio", "SemanaEpidemiologica", "EntidadFederativa"]
NUM   = ["Sem_Total", "Acum_M", "Acum_F", "Acum_AnioPrevio"]

#%% 1. Cargar
df = pd.read_csv(ENTRADA, encoding="utf-8-sig")
df["EntidadFederativa"] = df["EntidadFederativa"].str.strip()
df[NUM] = df[NUM].fillna(0).astype(int)
df = df.sort_values(CLAVE).reset_index(drop=True)

#%% 1a. Corrección de extracción: bloque desplazado una columna a la derecha
#     (verificado manualmente contra el PDF en la fila TOTAL)
#     "columna"     → los 3 valores están, solo se recorren
#     "reconstruir" → Acum_F = acumulado total semana previa + Sem - Acum_M
DESPLAZADOS = [("Pancreas", 2024, 6, "reconstruir"),
               ("Pancreas", 2024, 10, "columna")]

for c, a, s, metodo in DESPLAZADOS:
    m = (df.Cancer == c) & (df.Anio == a) & (df.SemanaEpidemiologica == s)
    sem_ok   = df.loc[m, "Acum_M"].to_numpy(copy=True)
    acumM_ok = df.loc[m, "Acum_F"].to_numpy(copy=True)
    if metodo == "columna":
        acumF_ok = df.loc[m, "Acum_AnioPrevio"].to_numpy(copy=True)
    else:
        previo = (df[(df.Cancer == c) & (df.Anio == a) & (df.SemanaEpidemiologica == s - 1)]
                    .set_index("EntidadFederativa").eval("Acum_M + Acum_F"))
        acumF_ok = df.loc[m, "EntidadFederativa"].map(previo).to_numpy() + sem_ok - acumM_ok
    df.loc[m, "Sem_Total"]       = sem_ok
    df.loc[m, "Acum_M"]          = acumM_ok
    df.loc[m, "Acum_F"]          = acumF_ok
    df.loc[m, "Acum_AnioPrevio"] = 0          # no recuperable; esta columna ya no se usa

print("Verificación de semanas corregidas (TOTAL):")
print(df[df.EntidadFederativa.eq("TOTAL")
         & df.set_index(["Cancer", "Anio", "SemanaEpidemiologica"]).index.isin(
             [d[:3] for d in DESPLAZADOS])]
      [["Cancer", "Anio", "SemanaEpidemiologica", "Sem_Total", "Acum_M", "Acum_F"]]
      .to_string(index=False))

#%% 1b. El boletín sem01 de cada año trae el CIERRE del año anterior → reasignarlo

'''
Qué hace este bloque:

Detecta el cierre: si el acumulado de sem01 es mayor que el de sem02, ese sem01 es el cierre del año anterior.
Lo reasigna: lo mueve al año anterior como la semana siguiente a su última semana. Quedan así:
2023 → semana 53;
2024 → semana 53;
2025 → semana 54, porque 2025 ya tiene su semana 53 propia.
Lo marca: agrega la columna Cierre para que puedas identificar esas filas.
'''



t  = df[df.EntidadFederativa == "TOTAL"].assign(Acum=lambda d: d.Acum_M + d.Acum_F)
s1 = t[t.SemanaEpidemiologica == 1].set_index(["Cancer", "Anio"])["Acum"]
s2 = t[t.SemanaEpidemiologica == 2].set_index(["Cancer", "Anio"])["Acum"]
cierre = s1[s1 > s2.reindex(s1.index).fillna(-1)].index      # sem01 > sem02 → es cierre

idx = pd.MultiIndex.from_frame(df[["Cancer", "Anio"]])
es_cierre = (df.SemanaEpidemiologica == 1) & idx.isin(cierre)
maxsem = df[~es_cierre].groupby(["Cancer", "Anio"])["SemanaEpidemiologica"].max()

df["Cierre"] = es_cierre
df.loc[es_cierre, "Anio"] -= 1
df.loc[es_cierre, "SemanaEpidemiologica"] = [
    maxsem.get((c, a), float("nan")) + 1
    for c, a in zip(df.loc[es_cierre, "Cancer"], df.loc[es_cierre, "Anio"])]

sin_anio = df.SemanaEpidemiologica.isna()            # cierre de un año sin datos (p. ej. 2022)
print(f"Filas de cierre sin año previo (se descartan): {sin_anio.sum()}")
df = df[~sin_anio].copy()
df["SemanaEpidemiologica"] = df.SemanaEpidemiologica.astype(int)
df = df.sort_values(CLAVE).reset_index(drop=True)

print("Boletines reasignados como cierre:")
print(df[df.Cierre & (df.EntidadFederativa == "TOTAL")]
        [["Cancer", "Anio", "SemanaEpidemiologica", "ArchivoOrigen", "Acum_M", "Acum_F"]]
        .to_string(index=False))

print(df.groupby(["Cancer", "Anio"])["SemanaEpidemiologica"]
        .agg(primera="min", ultima="max", semanas="nunique"))

#%% 2. Validaciones
rep = []
rep.append(f"Filas duplicadas: {df.duplicated(CLAVE).sum()}")

n = df.groupby(CLAVE[:3]).size()
rep.append(f"Semanas con != 33 filas: {(n != 33).sum()}")
if (n != 33).any():
    rep.append(n[n != 33].to_string())

estados = df[df.EntidadFederativa != "TOTAL"].groupby(CLAVE[:3])[NUM].sum()
total   = df[df.EntidadFederativa == "TOTAL"].set_index(CLAVE[:3])[NUM]
rep.append("Máx |suma de estados - TOTAL| por columna:\n"
           + (estados - total).abs().max().to_string())

tot = df[df.EntidadFederativa == "TOTAL"].pivot_table(
        index=["Anio", "SemanaEpidemiologica"], columns="Cancer", values="Acum_M")
for a, b in [("Colon", "Pulmon"), ("Colon", "Pancreas"), ("Pancreas", "Pulmon")]:
    rep.append(f"¿Serie {a} idéntica a {b}? {tot[a].equals(tot[b])}  (debe ser False)")

#%% 3. Casos nuevos por sexo (diferencia de acumulados)
# g = df.groupby(["Cancer", "EntidadFederativa", "Anio"])
# for s in ["M", "F"]:
#    df[f"Nuevos_{s}"] = g[f"Acum_{s}"].diff().fillna(df[f"Acum_{s}"]).astype(int)

#%% 3. Casos nuevos por sexo
grp = ["Cancer", "EntidadFederativa", "Anio"]
for s in ["M", "F"]:
    # (a) diferencia directa del acumulado del boletín (se guarda para auditoría)
    df[f"NuevosBruto_{s}"] = (df.groupby(grp)[f"Acum_{s}"].diff()
                                .fillna(df[f"Acum_{s}"]).astype(int))
    # (b) acumulado corregido: mínimo hacia atrás; si un boletín publicó un valor
    #     inflado que después se corrigió a la baja, se usa el valor corregido
    # df[f"AcumCorr_{s}"] = df.groupby(grp)[f"Acum_{s}"].transform(
    #                        lambda x: x[::-1].cummin()[::-1])
    df[f"AcumCorr_{s}"] = df.groupby(grp)[f"Acum_{s}"].cummax()
    
    df[f"Nuevos_{s}"] = (df.groupby(grp)[f"AcumCorr_{s}"].diff()
                           .fillna(df[f"AcumCorr_{s}"]).astype(int))

# Reporte de semanas anómalas (nivel nacional) para cotejar contra el PDF
tn = df[df.EntidadFederativa == "TOTAL"].assign(
        Bruto=lambda d: d.NuevosBruto_M + d.NuevosBruto_F)
anom = pd.concat([tn[tn.Bruto < 0],
                  tn.sort_values("Bruto", ascending=False).groupby("Cancer").head(3)])
rep.append("Semanas a cotejar contra el PDF:\n" + anom[
    ["Cancer", "Anio", "SemanaEpidemiologica", "ArchivoOrigen",
     "Acum_M", "Acum_F", "Bruto"]].drop_duplicates().to_string(index=False))


neg = df[(df.Nuevos_M < 0) | (df.Nuevos_F < 0)]
rep.append(f"Registros con corrección negativa (estado-semana): {len(neg)}")

df["Periodo"] = (df.Anio.astype(str) + "-S"
                 + df.SemanaEpidemiologica.astype(str).str.zfill(2))

#%% 4. Totales anuales = acumulado de la ÚLTIMA semana de cada año
ultima = df.groupby(["Cancer", "Anio"])["SemanaEpidemiologica"].transform("max")
anual = (df[df.SemanaEpidemiologica == ultima]
         .assign(Casos=lambda d: d.Acum_M + d.Acum_F)
         .rename(columns={"Acum_M": "Hombres", "Acum_F": "Mujeres",
                          "SemanaEpidemiologica": "UltimaSemana"})
         [["Cancer", "Anio", "UltimaSemana", "EntidadFederativa",
           "Casos", "Hombres", "Mujeres"]])

# Cifra revisada: columna "año previo" del boletín del año siguiente, misma semana
# rev = (df[df.EntidadFederativa == "TOTAL"]
#       [["Cancer", "Anio", "SemanaEpidemiologica", "Acum_AnioPrevio"]]
#       .assign(Anio=lambda d: d.Anio - 1)
#       .rename(columns={"SemanaEpidemiologica": "UltimaSemana",
#                        "Acum_AnioPrevio": "Casos_revisados"}))
#
# nacional = (anual[anual.EntidadFederativa == "TOTAL"]
#            .merge(rev, on=["Cancer", "Anio", "UltimaSemana"], how="left")
#            .drop(columns="EntidadFederativa"))

# Modificación puntual para los deltas de reinicio de año
# Por qué se borra: el cierre ya es la cifra definitiva de cada año, así que el cálculo con la columna del año previo sobra. Las dos líneas de Razon_H_M que siguen se quedan igual.
nacional = (anual[anual.EntidadFederativa == "TOTAL"]
            .drop(columns="EntidadFederativa").reset_index(drop=True))


nacional["Razon_H_M"] = (nacional.Hombres / nacional.Mujeres).round(2)

#%% 5. Guardar
df.to_csv(SALIDA / "semanal.csv", index=False, encoding="utf-8-sig")
anual[anual.EntidadFederativa != "TOTAL"].to_csv(
    SALIDA / "anual_estatal.csv", index=False, encoding="utf-8-sig")
nacional.to_csv(SALIDA / "anual_nacional.csv", index=False, encoding="utf-8-sig")
nacional.to_latex(SALIDA / "tabla_anual_nacional.tex", index=False,
                  caption="Casos nuevos notificados por año y sexo, 2023--2025.",
                  label="tab:boletin_anual")
(SALIDA / "validacion.txt").write_text("\n\n".join(rep), encoding="utf-8")

print("\n\n".join(rep))
print("\nNacional:\n", nacional.to_string(index=False))