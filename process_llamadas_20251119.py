import pandas as pd
import os

# -------------------------------------------------
# 1. RUTAS
# -------------------------------------------------

FILE_PATH = r"C:\Users\amaldonado\OneDrive - Sicontac Center S.A\Documentos\Documentos Analytics\Paneles\Panel Reportería Tiempo de Gestion\Panel_ReporteriaTG\Data\LlamadasDiaria_20251119.csv"

OUTPUT_DIR = r"C:\Users\amaldonado\OneDrive - Sicontac Center S.A\Documentos\Documentos Analytics\Paneles\Panel Reportería Tiempo de Gestion\Panel_ReporteriaTG\Data\processed"

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "llamadas_procesadas_20251119.csv"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

# -------------------------------------------------
# 2. CARGAR ARCHIVO
# -------------------------------------------------

df = pd.read_csv(FILE_PATH, sep=";", encoding="utf-8")

print("Columnas detectadas:")
print(df.columns.tolist())

# -------------------------------------------------
# 3. CAMBIAR FORMATO FECHA Y HORA
# (Requisito del RFU)
# -------------------------------------------------

df["FechaInicio"] = pd.to_datetime(df["FechaInicio"])
df["FechaFin"] = pd.to_datetime(df["FechaFin"])

# Separar fecha
df["Fecha"] = df["FechaInicio"].dt.date

# Separar hora
df["HoraInicio"] = df["FechaInicio"].dt.time
df["HoraFin"] = df["FechaFin"].dt.time

# -------------------------------------------------
# 4. ORDENAR POR GESTOR Y HORA INICIO
# (Requisito del RFU)
# -------------------------------------------------

df = df.sort_values(by=["Gestor", "Fecha", "HoraInicio"])

# -------------------------------------------------
# 5. CALCULAR DIFERENCI
# (Hora inicio siguiente - Hora fin actual)
# -------------------------------------------------

# Obtener siguiente FechaInicio por gestor
df["SiguienteFechaInicio"] = df.groupby("Gestor")["FechaInicio"].shift(-1)

# Calcular diferencia
df["DIFERENCI"] = df["SiguienteFechaInicio"] - df["FechaFin"]

# Rellenar nulos con 0
df["DIFERENCI"] = df["DIFERENCI"].fillna(pd.Timedelta(seconds=0))

# Si diferencia negativa → poner en 0
df.loc[df["DIFERENCI"] < pd.Timedelta(seconds=0), "DIFERENCI"] = pd.Timedelta(seconds=0)

# -------------------------------------------------
# 6. TIEMPO SIN GESTION (> 00:00:35)
# -------------------------------------------------

LIMITE = pd.Timedelta(seconds=35)

df["TiempoSinGestion"] = df["DIFERENCI"].apply(
    lambda x: x if x > LIMITE else pd.Timedelta(seconds=0)
)

# -------------------------------------------------
# 7. CONSOLIDADO POR GESTOR Y FECHA
# -------------------------------------------------

resumen = (
    df.groupby(["Gestor", "Fecha"])["TiempoSinGestion"]
    .sum()
    .reset_index()
)

# -------------------------------------------------
# 8. GUARDAR RESULTADOS
# -------------------------------------------------

df.to_csv(
    os.path.join(OUTPUT_DIR, "detalle_llamadas_20251119.csv"),
    index=False
)

resumen.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\n✅ Archivo detalle generado correctamente")
print("\n✅ Archivo resumen generado correctamente")
print(OUTPUT_FILE)