let
    Esperado = #table({"Cancer","Anio","SemanaEpidemiologica","Esperado"}, {
        {"Pancreas",2023,2,6},  {"Colon",2023,2,20},  {"Pulmon",2023,2,7},
        {"Pancreas",2023,26,25},{"Colon",2023,26,103},{"Pulmon",2023,26,50},
        {"Pancreas",2023,52,16},{"Colon",2023,52,91}, {"Pulmon",2023,52,40},
        {"Pancreas",2024,2,45}, {"Colon",2024,2,82},  {"Pulmon",2024,2,27},
        {"Pancreas",2024,26,37},{"Colon",2024,26,219},{"Pulmon",2024,26,49},
        {"Pancreas",2024,52,27},{"Colon",2024,52,97}, {"Pulmon",2024,52,30},
        {"Pancreas",2025,2,22}, {"Colon",2025,2,48},  {"Pulmon",2025,2,38},
        {"Pancreas",2025,26,20},{"Colon",2025,26,76}, {"Pulmon",2025,26,27},
        {"Pancreas",2025,52,13},{"Colon",2025,52,93}, {"Pulmon",2025,52,36}}),
    Totales = Table.SelectColumns(
                Table.SelectRows(Boletin, each [EntidadFederativa] = "TOTAL"),
                {"Cancer","Anio","SemanaEpidemiologica","Sem_Total"}),
    Unido   = Table.NestedJoin(Esperado, {"Cancer","Anio","SemanaEpidemiologica"},
                Totales, {"Cancer","Anio","SemanaEpidemiologica"}, "Ext", JoinKind.LeftOuter),
    Exp     = Table.ExpandTableColumn(Unido, "Ext", {"Sem_Total"}, {"Obtenido"}),
    Revision = Table.AddColumn(Exp, "Coincide", each [Esperado] = [Obtenido], type logical)
in
    Revision