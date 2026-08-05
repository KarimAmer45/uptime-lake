// Paste into Power Query Advanced Editor and replace the three parameters.
let
    Source = Databricks.Catalogs(
        DatabricksServerHostname,
        DatabricksHttpPath,
        [Catalog = DatabricksCatalog, Database = null, Implementation = "2.0"]
    ),
    Catalog = Source{[Name = DatabricksCatalog, Kind = "Database"]}[Data],
    GoldSchema = Catalog{[Name = "gold", Kind = "Schema"]}[Data],
    EquipmentHealth = GoldSchema{[Name = "powerbi_equipment_health", Kind = "View"]}[Data]
in
    EquipmentHealth
