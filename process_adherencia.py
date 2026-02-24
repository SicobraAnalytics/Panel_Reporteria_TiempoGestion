import pandas as pd
import os

# -------------------------------------------------
# 1. RUTAS
# -------------------------------------------------

FILE_PATH = r"C:\Users\amaldonado\OneDrive - Sicontac Center S.A\Documentos\Documentos Analytics\Paneles\Panel Reportería Tiempo de Gestion\Data\adherencia_2025-11-19.csv"

OUTPUT_DIR = r"C:\Users\amaldonado\OneDrive - Sicontac Center S.A\Documentos\Documentos Analytics\Paneles\Panel Reportería Tiempo de Gestion\data\processed"

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "adherencia_limpia_2025-11-19.csv"
)

FECHA_ANALISIS = "19/11/2025"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# -------------------------------------------------
# 2. CARGAR CSV (DELIMITADOR ;)
# -------------------------------------------------

df = pd.read_csv(
    FILE_PATH,
    encoding="utf-8",
    sep=";"
)

# Limpiar nombres de columnas
df.columns = df.columns.str.strip()

print("Columnas detectadas:")
print(df.columns.tolist())

# -------------------------------------------------
# 3. FILTRAR POR FECHA
# -------------------------------------------------

df["Fecha"] = df["Fecha"].astype(str).str.strip()
df = df[df["Fecha"] == FECHA_ANALISIS]

# -------------------------------------------------
# 4. COLUMNAS DEFINIDAS POR RFU
# -------------------------------------------------

columnas_rfu = [
    "Fecha",
    "IdUser",
    "NombreGestor",
    "NombreSupervisor",
    "HoraLogueo",
    "HoraDeslogueo",
    "TotalTiempoAwait",
    "TiempoAwaitBreak",
    "TiempoAwaitBanio",
    "TiempoAwaitAlmuerzo",
    "TiempoAwaitMedico",
    "TiempoAwaitReunion",
    "TiempoAwaitInvestigacion",
    "TiempoAwaitPausaActiva",
    "TiempoAwaitprePostTurno",
    "TiempoAwaitSinSistema",
    "TiempoAwaitCapacitacion",
    "TiempoAwaitNetworkSic"
]

df = df[columnas_rfu]

# -------------------------------------------------
# 5. LIMPIEZA BÁSICA (SIN CAMBIAR FORMATO DE HORA)
# -------------------------------------------------

# Quitar espacios en nombres
df["NombreGestor"] = df["NombreGestor"].astype(str).str.strip()
df["NombreSupervisor"] = df["NombreSupervisor"].astype(str).str.strip()

# Reemplazar nulos por 00:00:00 en columnas de tiempo
columnas_tiempo = columnas_rfu[3:]

df[columnas_tiempo] = df[columnas_tiempo].fillna("00:00:00")

# -------------------------------------------------
# 6. VALIDACIÓN
# -------------------------------------------------

print(f"Filas finales procesadas: {len(df)}")
print(df.head())

# -------------------------------------------------
# 7. GUARDAR ARCHIVO LIMPIO
# -------------------------------------------------

df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8"
)

print("\n✅ Archivo generado correctamente:")
print(OUTPUT_FILE)
