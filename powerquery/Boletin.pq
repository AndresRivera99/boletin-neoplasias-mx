let
    // ================== 1. PARÁMETROS (lo único que se edita) ==================
    CarpetaRaiz = "D:\boletin-neoplasias-mx\pdfs",

    // Qué buscar en cada cuadro y en qué columna empieza el grupo de cada cáncer
    // Posición 1 → ColInicio 2 | Posición 2 → 6 | Posición 3 → 10
    Config = #table(
        {"Cancer", "Claves", "ColInicio"},
        {
            {"Pulmon",   {"C33"},                         2},
            {"Colon",    {"C18"},                        10},
            {"Pancreas", {"C26", "Páncreas", "Pancreas"}, 10}
        }),

    Estados = {"Aguascalientes","Baja California","Baja California Sur","Campeche","Coahuila",
        "Colima","Chiapas","Chihuahua","Ciudad de México","Durango","Guanajuato","Guerrero",
        "Hidalgo","Jalisco","México","Michoacán","Morelos","Nayarit","Nuevo León","Oaxaca",
        "Puebla","Querétaro","Quintana Roo","San Luis Potosí","Sinaloa","Sonora","Tabasco",
        "Tamaulipas","Tlaxcala","Veracruz","Yucatán","Zacatecas","TOTAL"},

    NombresFinales = {"EntidadFederativa","Sem_Total","Acum_M","Acum_F","Acum_AnioPrevio"},

    // ================== 2. FUNCIONES DE APOYO ==================
    // Convierte "1 213", "1,213", "-" o vacío en número entero
    ANumero = (v) =>
        let t = Text.Select(Text.From(v ?? ""), {"0".."9"})
        in if t = "" then 0 else Number.From(t),

    // Junta todo el texto de una tabla en una sola cadena para poder buscar
    TextoDeTabla = (t as table) as text =>
        Text.Combine(List.Transform(Table.ToRows(t),
            each Text.Combine(List.Transform(_, (v) => Text.From(v ?? "")), " ")), " "),

    // Saca Column1 (estado) + las 4 columnas del grupo del cáncer
    SacarBloque = (t as table, inicio as number) as table =>
        let
            cols   = {"Column1"} & List.Transform({inicio..inicio + 3}, each "Column" & Text.From(_)),
            existe = List.ContainsAll(Table.ColumnNames(t), cols)
        in
            if existe
            then Table.RenameColumns(Table.SelectColumns(t, cols), List.Zip({cols, NombresFinales}))
            else #table(NombresFinales, {}),

    // ================== 3. LEER LOS PDFs ==================
    Archivos  = Table.SelectRows(Folder.Files(CarpetaRaiz), each Text.Lower([Extension]) = ".pdf"),
    ConAnio   = Table.AddColumn(Archivos, "Anio",
                  each Int64.From(List.Last(List.Select(Text.Split([Folder Path], "\"), each _ <> ""))), Int64.Type),
    ConSemana = Table.AddColumn(ConAnio, "SemanaEpidemiologica",
                  each let n = Text.Lower([Name]), p = Text.PositionOf(n, "sem")
                       in Int64.From(Text.Select(Text.Middle(n, p + 3, 2), {"0".."9"})), Int64.Type),
    ConTablas = Table.AddColumn(ConSemana, "PDF", each Pdf.Tables([Content])),
    Expandido = Table.ExpandTableColumn(ConTablas, "PDF", {"Id","Data","Kind"}, {"IdTabla","Datos","Tipo"}),
    SoloTablas = Table.SelectRows(Expandido, each [Tipo] = "Table"),
    ConTexto  = Table.AddColumn(SoloTablas, "Texto", each TextoDeTabla([Datos]), type text),

    // ================== 4. CRUZAR CADA TABLA CON CADA CÁNCER ==================
    ConConfig = Table.AddColumn(ConTexto, "Cfg", each Config),
    Cruzado   = Table.ExpandTableColumn(ConConfig, "Cfg", {"Cancer","Claves","ColInicio"}),
    Coinciden = Table.SelectRows(Cruzado, each
                  List.AnyTrue(List.Transform([Claves], (k) => Text.Contains([Texto], k, Comparer.OrdinalIgnoreCase)))),
    ConBloque = Table.AddColumn(Coinciden, "Bloque", each SacarBloque([Datos], [ColInicio])),

    // ================== 5. ARMAR LA TABLA FINAL ==================
    Base      = Table.SelectColumns(ConBloque, {"Cancer","Anio","SemanaEpidemiologica","Name","IdTabla","Bloque"}),
    Filas     = Table.ExpandTableColumn(Base, "Bloque", NombresFinales),
    Recortado = Table.TransformColumns(Filas, {{"EntidadFederativa", each Text.Trim(Text.From(_ ?? "")), type text}}),
    SoloEst   = Table.SelectRows(Recortado, each List.Contains(Estados, [EntidadFederativa])),
    Numeros   = Table.TransformColumns(SoloEst, {
                  {"Sem_Total", ANumero, Int64.Type}, {"Acum_M", ANumero, Int64.Type},
                  {"Acum_F", ANumero, Int64.Type},    {"Acum_AnioPrevio", ANumero, Int64.Type}}),
    Renombrado = Table.RenameColumns(Numeros, {{"Name","ArchivoOrigen"}}),
    Final     = Table.Sort(Renombrado, {{"Cancer", Order.Ascending}, {"Anio", Order.Ascending},
                  {"SemanaEpidemiologica", Order.Ascending}, {"EntidadFederativa", Order.Ascending}})
in
    Final