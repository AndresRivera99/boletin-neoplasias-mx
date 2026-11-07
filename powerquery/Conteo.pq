let
    Agrupado = Table.Group(Boletin, {"Cancer","Anio","SemanaEpidemiologica"},
                 {{"Filas", each Table.RowCount(_), Int64.Type}}),
    Problemas = Table.SelectRows(Agrupado, each [Filas] <> 33)
in
    Problemas