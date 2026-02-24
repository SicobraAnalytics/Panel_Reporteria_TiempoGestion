import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Reporte Tiempo Sin Gestión", layout="wide")

st.title("📊 Reporte Tiempo Sin Gestión")

# -------------------------------------------------
# 1. CARGAR ARCHIVOS
# -------------------------------------------------

@st.cache_data
def load_data():
    adherencia = pd.read_csv("DataFinal/adherencia_20251119.csv", encoding="latin-1")
    llamadas = pd.read_csv("DataFinal/detalle_llamadas_20251119.csv", encoding="latin-1")
    return adherencia, llamadas

adherencia, llamadas = load_data()

# -------------------------------------------------
# 2. FORMATEAR DATOS
# -------------------------------------------------

# Convertir tiempos adherencia
columnas_tiempo = [
    "TotalTiempoAwait",
    "TiempoAwaitBreak",
    "TiempoAwaitBanio",
    "TiempoAwaitInvestigacion",
    "TiempoAwaitNetworkSic"
]

for col in columnas_tiempo:
    adherencia[col] = pd.to_timedelta(adherencia[col])

adherencia["HoraLogueo"] = pd.to_timedelta(adherencia["HoraLogueo"])
adherencia["HoraDeslogueo"] = pd.to_timedelta(adherencia["HoraDeslogueo"])

# Llamadas
llamadas["DIFERENCI"] = pd.to_timedelta(llamadas["DIFERENCI"])

# -------------------------------------------------
# 3. CRUCE DE DATA
# -------------------------------------------------

df = llamadas.merge(
    adherencia,
    left_on="IdUsuario",
    right_on="IdUser",
    how="left"
)

# -------------------------------------------------
# 4. SEPARAR TIEMPO DENTRO Y FUERA DE JORNADA
# -------------------------------------------------

llamadas["HoraFin_td"] = pd.to_timedelta(llamadas["FechaFin"].str[11:19])

df["DentroJornada"] = np.where(
    (llamadas["HoraFin_td"] >= df["HoraLogueo"]) &
    (llamadas["HoraFin_td"] <= df["HoraDeslogueo"]),
    True,
    False
)

LIMITE = pd.Timedelta(seconds=35)

df["TiempoSinGestion"] = np.where(
    (df["DIFERENCI"] > LIMITE) & (df["DentroJornada"]),
    df["DIFERENCI"],
    pd.Timedelta(seconds=0)
)

df["TiempoRecuperado"] = np.where(
    (df["DIFERENCI"] > LIMITE) & (~df["DentroJornada"]),
    df["DIFERENCI"],
    pd.Timedelta(seconds=0)
)

# -------------------------------------------------
# 5. DETERMINAR PART / FULL TIME
# -------------------------------------------------

df["DuracionJornada"] = df["HoraDeslogueo"] - df["HoraLogueo"]

df["TipoContrato"] = np.where(
    df["DuracionJornada"] <= pd.Timedelta(hours=6),
    "PART TIME",
    "FULL TIME"
)

# -------------------------------------------------
# 6. CALCULAR EXCESOS
# -------------------------------------------------

def calcular_exceso(row):

    exceso = pd.Timedelta(0)

    # BREAK
    if row["TipoContrato"] == "PART TIME":
        limite_break = pd.Timedelta(minutes=15)
    else:
        limite_break = pd.Timedelta(minutes=30)

    exceso += max(pd.Timedelta(0), row["TiempoAwaitBreak"] - limite_break)

    # BAÑO
    exceso += max(pd.Timedelta(0), row["TiempoAwaitBanio"] - pd.Timedelta(minutes=20))

    # INVESTIGACION
    exceso += max(pd.Timedelta(0), row["TiempoAwaitInvestigacion"] - pd.Timedelta(hours=1))

    # NETWORK
    exceso += max(pd.Timedelta(0), row["TiempoAwaitNetworkSic"] - pd.Timedelta(hours=1))

    return exceso

excesos = adherencia.copy()
excesos["DuracionJornada"] = excesos["HoraDeslogueo"] - excesos["HoraLogueo"]

excesos["TipoContrato"] = np.where(
    excesos["DuracionJornada"] <= pd.Timedelta(hours=6),
    "PART TIME",
    "FULL TIME"
)

excesos["Exceso"] = excesos.apply(calcular_exceso, axis=1)

# -------------------------------------------------
# 7. CONSOLIDADO FINAL
# -------------------------------------------------


# Asegurar tipo timedelta
df["TiempoSinGestion"] = pd.to_timedelta(df["TiempoSinGestion"])
df["TiempoRecuperado"] = pd.to_timedelta(df["TiempoRecuperado"])

consolidado = (
    df.groupby("NombreGestor", as_index=False)
    .agg({
        "TiempoSinGestion": "sum",
        "TiempoRecuperado": "sum"
    })
)

consolidado = consolidado.merge(
    excesos[["NombreGestor", "TotalTiempoAwait", "Exceso"]],
    on="NombreGestor",
    how="left"
)

consolidado["TiempoRealARecuperar"] = (
    consolidado["TiempoSinGestion"]
    - consolidado["TotalTiempoAwait"]
    + consolidado["Exceso"]
)

consolidado["Pendiente"] = (
    consolidado["TiempoRealARecuperar"]
    - consolidado["TiempoRecuperado"]
)

consolidado["Pendiente"] = consolidado["Pendiente"].clip(lower=pd.Timedelta(0))

# -------------------------------------------------
# 8. FILTRO POR GESTOR
# -------------------------------------------------

gestores = ["Todos"] + sorted(consolidado["NombreGestor"].unique().tolist())

gestor_seleccionado = st.selectbox(
    "👤 Filtrar por Gestor",
    gestores
)

if gestor_seleccionado != "Todos":
    consolidado = consolidado[
        consolidado["NombreGestor"] == gestor_seleccionado
    ]

# -------------------------------------------------
# 9. FUNCIONES DE FORMATO Y COLOR
# -------------------------------------------------

def format_timedelta(td):
    if pd.isna(td):
        return "00:00:00"
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def color_pendiente(val):
    if val == pd.Timedelta(0):
        return "background-color: #2ecc71; color: white;"  # Verde
    elif val <= pd.Timedelta(hours=1):
        return "background-color: #f1c40f; color: black;"  # Amarillo
    else:
        return "background-color: #e74c3c; color: white;"  # Rojo

# -------------------------------------------------
# 10. MOSTRAR RESULTADOS
# -------------------------------------------------

st.subheader("📋 Consolidado General")

# Copia para formatear sin alterar original
consolidado_display = consolidado.copy()

# Formatear columnas de tiempo
columnas_formato = [
    "TiempoSinGestion",
    "TiempoRecuperado",
    "TotalTiempoAwait",
    "Exceso",
    "TiempoRealARecuperar",
    "Pendiente"
]

for col in columnas_formato:
    consolidado_display[col] = consolidado_display[col].apply(format_timedelta)

# Aplicar color solo a columna Pendiente
styled_table = consolidado_display.style.apply(
    lambda row: [
        color_pendiente(consolidado.loc[row.name, "Pendiente"])
        if col == "Pendiente" else ""
        for col in consolidado_display.columns
    ],
    axis=1
)

st.dataframe(styled_table, use_container_width=True)

st.subheader("📈 KPIs Generales")


col1, col2, col3 = st.columns(3)

total_sg = consolidado["TiempoSinGestion"].sum()
total_rec = consolidado["TiempoRecuperado"].sum()
total_pen = consolidado["Pendiente"].sum()

col1.metric("Total Sin Gestión", format_timedelta(total_sg))
col2.metric("Total Recuperado", format_timedelta(total_rec))
col3.metric("Total Pendiente", format_timedelta(total_pen))
