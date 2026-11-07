# Neoplasias de pulmón, colon-recto y páncreas en el Boletín Epidemiológico de México (2023–2025)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24026370.svg)](https://doi.org/10.5281/zenodo.24026370)

Extracción, validación y visualización de los casos nuevos notificados de tres neoplasias
publicados en el Boletín Epidemiológico semanal de la Dirección General de Epidemiología
(Secretaría de Salud). Forma parte de la justificación de la tesis de Maestría en Ciencias en
Innovación Biotecnológica (CIATEJ) de Andrés Rivera Chávez.

## Fuente
- Boletín Epidemiológico, Sistema Nacional de Vigilancia Epidemiológica, DGE – Secretaría de Salud.
  <https://www.gob.mx/salud/acciones-y-programas/historico-boletin-epidemiologico>
- Periodo: 2023 (primera aparición de estas neoplasias en el boletín) a 2025, PDF semanales.
- Población: CONAPO, *Conciliación Demográfica 1950–2019 y Proyecciones de la Población de México
  y de las Entidades Federativas 2020–2070*, población a mitad de año.
- Geometría estatal: `Estado.json` (repositorio DanaRoji/GeoJsonMexico).
- Los PDF no se incluyen; `datos/fuentes_pdfs.csv` contiene el nombre, tamaño y SHA256 de cada archivo.

| Neoplasia | Rótulo en el boletín | Posición en el cuadro | Columnas extraídas |
|---|---|---|---|
| Tráquea, bronquios y pulmón | C33–C34 | 1 | Column1, Column2–5 |
| Colon y recto | C18–C21 (mismo cuadro que pulmón) | 3 | Column1, Column10–13 |
| Páncreas | C26* | 3 | Column1, Column10–13 |

\* El boletín rotula páncreas como C26; en la CIE-10 corresponde a C25.

## Alcance y limitaciones
- Son **casos nuevos notificados** (información preliminar), no incidencia.
- La clasificación es topográfica (CIE-10); no distingue tipo histológico.
- 2023 es el primer año de notificación; el aumento 2023→2024 refleja en parte la consolidación del registro.
- 2023 y 2024 cierran con el boletín de la semana 1 del año siguiente; 2025 se corta en su semana 53.

## Estructura
powerquery/ Código M (Power Query): Boletin.pq, Verificacion.pq, Conteo.pq
src/ 00_inventario_pdfs.py, 01_preparar_datos.py, 01b_poblacion_conapo.py, 02_figuras.py
datos/ boletin_neoplasias.csv (extracción cruda), fuentes_pdfs.csv
externos/ Estado.json, poblacion_conapo.csv
procesados/ semanal.csv, anual_estatal.csv, anual_nacional.csv, tabla_anual_nacional.tex, validacion.txt
figuras/ comparativas/, pulmon/, colon/, pancreas/ (PDF y PNG)


## Cómo reproducir
1. Descargar los PDF semanales y colocarlos en `pdfs/2023`, `pdfs/2024`, `pdfs/2025`;
   comprobar contra `datos/fuentes_pdfs.csv`.
2. En Excel, crear consultas en blanco con el código de `powerquery/` (consulta `Boletin`,
   luego `Verificacion` y `Conteo`) y ajustar `CarpetaRaiz`. `Verificacion` debe dar TRUE en las
   27 filas y `Conteo` debe quedar vacía.
3. Exportar la consulta `Boletin` como CSV UTF-8 a `datos/boletin_neoplasias.csv`.
4. Descargar de datos.gob.mx la población a mitad de año de CONAPO como `datos/externos/conapo_mitad_anio.csv`.
5. `pip install -r requirements.txt`
6. Ejecutar en orden: `01_preparar_datos.py` → `01b_poblacion_conapo.py` → `02_figuras.py`.

## Tratamiento de los datos
- Los números con separador de miles ("1 213") se limpian en Power Query.
- El boletín de la semana 1 de cada año contiene el **cierre del año anterior**; se reasigna a
  ese año como semana de cierre.
- Páncreas 2024, semanas 6 y 10: la extracción desplazó el bloque una columna; se corrigió en
  `01_preparar_datos.py` (bloque 1a) y se verificó contra la fila TOTAL del PDF. En la semana 6
  el acumulado de mujeres se reconstruyó (acumulado previo + casos de la semana − acumulado de hombres).
- Casos nuevos por sexo = diferencia semanal del acumulado; cuando un boletín publicó un
  acumulado menor que el previo se conservó el previo (máximo acumulado).
- Total anual = acumulado de la última semana del año.
- Tasa = casos / población a mitad de año × 100 000; el mapa muestra el promedio de las tasas anuales.

## Diccionario de variables
| Variable | Descripción |
|---|---|
| Sem_Total | Casos nuevos de la semana (ambos sexos) |
| Acum_M / Acum_F | Acumulado del año, hombres / mujeres |
| Acum_AnioPrevio | Acumulado del año anterior a la misma semana |
| Nuevos_M / Nuevos_F | Casos nuevos por sexo (diferencia del acumulado corregido) |
| Cierre | TRUE si la fila proviene del boletín de cierre |
| ArchivoOrigen / IdTabla | PDF y tabla de los que se extrajo la fila |

## Validación
| Control | Resultado |
|---|---|
| Cotejo manual de la fila TOTAL (27 casos, 3 neoplasias × 3 semanas × 3 años) | 27/27 |
| Filas duplicadas | 0 |
| Semanas con ≠ 33 filas (32 entidades + TOTAL) | 0 |
| Suma de entidades − TOTAL | 0 en todas las columnas |
| Series idénticas entre neoplasias | Ninguna |
| Correcciones negativas tras el ajuste | 0 |

## Cómo citar
Rivera Chávez, A. (2026). *boletin-neoplasias-mx* (v1.0.0) [Software]. Zenodo. https://doi.org/10.5281/zenodo.24026370

## Licencia
Código: MIT. Los datos provienen de fuentes públicas del Gobierno de México y conservan sus
condiciones de uso originales.