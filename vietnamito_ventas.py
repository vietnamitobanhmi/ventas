import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from supabase import create_client

st.set_page_config(
    page_title="Vietnamito — Ventas",
    page_icon="☕",
    layout="wide"
)

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    h1 { font-size: 1.6rem; font-weight: 600; }
    .stTabs [data-baseweb="tab"] { font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

SUPABASE_URL = "https://rwtpjqvgiiuvniixqapu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ3dHBqcXZnaWl1dm5paXhxYXB1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzcxMzIyMjMsImV4cCI6MjA5MjcwODIyM30.jznrwuusfgtVkrzz_bfdsxq3tVsv-uV2tyMeIlh3bZg"

DIAS = {0: "Lun", 1: "Mar", 2: "Mié", 3: "Jue", 4: "Vie", 5: "Sáb", 6: "Dom"}
DIAS_ORDER = [0, 1, 2, 3, 4, 5, 6]
COLORS = ["#378ADD", "#5DCAA5", "#D85A30", "#7F77DD", "#BA7517", "#D4537E", "#639922"]

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def parse_csv(file):
    content = file.read()
    try:
        text = content.decode("utf-8-sig")
    except:
        text = content.decode("latin-1")
    lines = [l for l in text.strip().split("\n") if l.strip()]
    sep = ";" if ";" in lines[0] else ","
    rows = []
    for line in lines[1:]:
        parts = line.strip().split(sep)
        if len(parts) < 12:
            continue
        try:
            date_str = parts[0].strip().strip('"')
            val = float(parts[11].replace(",", "."))
            if val == 0:
                continue
            dt = datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")
            rows.append({
                "fecha": dt.strftime("%Y-%m-%d"),
                "hora": dt.hour,
                "dow": dt.weekday(),
                "valor": val,
                "ntrans": int(parts[1]) if parts[1].strip().isdigit() else 0,
                "items": int(parts[7]) if parts[7].strip().isdigit() else 0,
            })
        except:
            continue
    return rows

def save_to_supabase(rows):
    sb = get_supabase()
    fechas = list(set(r["fecha"] for r in rows))
    for fecha in fechas:
        sb.table("ventas").delete().eq("fecha", fecha).execute()
    for i in range(0, len(rows), 500):
        sb.table("ventas").insert(rows[i:i+500]).execute()

def load_from_supabase():
    sb = get_supabase()
    result = sb.table("ventas").select("*").execute()
    if not result.data:
        return pd.DataFrame()
    df = pd.DataFrame(result.data)
    df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
    return df

def calcular_promedios_dia(df):
    dias_unicos = df.groupby("dow")["fecha"].nunique()
    totales = df.groupby("dow")["valor"].sum()
    return (totales / dias_unicos).reindex(DIAS_ORDER, fill_value=0)

def calcular_promedios_hora(df):
    dias_por_hora = df.groupby("hora")["fecha"].nunique()
    totales = df.groupby("hora")["valor"].sum()
    return (totales / dias_por_hora).sort_index()

def calcular_heatmap(df):
    dias_unicos = df.groupby(["dow", "hora"])["fecha"].nunique()
    totales = df.groupby(["dow", "hora"])["valor"].sum()
    avg = (totales / dias_unicos).reset_index()
    avg.columns = ["dow", "hora", "avg"]
    return avg

def render_dashboard(df):
    fecha_min = df["fecha"].min()
    fecha_max = df["fecha"].max()
    n_dias = df["fecha"].nunique()
    total_ventas = df["valor"].sum()
    mejor_dow = calcular_promedios_dia(df).idxmax()
    mejor_hora = calcular_promedios_hora(df).idxmax()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Período", f"{fecha_min.strftime('%d/%m')} – {fecha_max.strftime('%d/%m/%Y')}")
    col2.metric("Días con datos", n_dias)
    col3.metric("Total ventas", f"€{total_ventas:,.2f}")
    col4.metric("Mejor día", DIAS[mejor_dow])
    col5.metric("Mejor franja", f"{mejor_hora}:00h")

    st.divider()

    tab1, tab2, tab3 = st.tabs(["📅 Por día de semana", "🕐 Por franja horaria", "🌡️ Mapa de calor"])

    with tab1:
        avg_dow = calcular_promedios_dia(df)
        labels = [DIAS[d] for d in DIAS_ORDER]
        values = [round(avg_dow.get(d, 0), 2) for d in DIAS_ORDER]
        fig = go.Figure(go.Bar(
            x=labels, y=values, marker_color=COLORS, marker_line_width=0,
            text=[f"€{v:.0f}" for v in values], textposition="outside",
        ))
        fig.update_layout(
            title="Venta media por día de la semana (€)", yaxis_title="€ promedio",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(gridcolor="rgba(128,128,128,0.15)", zeroline=False),
            xaxis=dict(showgrid=False), showlegend=False, height=400, margin=dict(t=50, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)
        with st.expander("Ver datos"):
            st.dataframe(pd.DataFrame({"Día": labels, "Promedio (€)": [f"€{v:.2f}" for v in values]}), hide_index=True, use_container_width=True)

    with tab2:
        avg_hora = calcular_promedios_hora(df)
        horas = list(avg_hora.index)
        vals = [round(v, 2) for v in avg_hora.values]
        fig2 = go.Figure(go.Bar(
            x=[f"{h}:00" for h in horas], y=vals, marker_color="#5DCAA5", marker_line_width=0,
            text=[f"€{v:.0f}" for v in vals], textposition="outside",
        ))
        fig2.update_layout(
            title="Venta media por franja horaria (€)", yaxis_title="€ promedio", xaxis_title="Hora",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(gridcolor="rgba(128,128,128,0.15)", zeroline=False),
            xaxis=dict(showgrid=False), showlegend=False, height=400, margin=dict(t=50, b=20),
        )
        st.plotly_chart(fig2, use_container_width=True)
        with st.expander("Ver datos"):
            st.dataframe(pd.DataFrame({"Hora": [f"{h}:00" for h in horas], "Promedio (€)": [f"€{v:.2f}" for v in vals]}), hide_index=True, use_container_width=True)

    with tab3:
        hm = calcular_heatmap(df)
        pivot = hm.pivot(index="dow", columns="hora", values="avg").reindex(DIAS_ORDER)
        pivot.index = [DIAS[d] for d in DIAS_ORDER]
        pivot.columns = [f"{h}:00" for h in pivot.columns]
        fig3 = px.imshow(
            pivot, color_continuous_scale=[[0, "#E1F5EE"], [0.5, "#1D9E75"], [1, "#04342C"]],
            aspect="auto", text_auto=".0f", labels={"color": "€ promedio"},
        )
        fig3.update_layout(
            title="Venta media por día y franja horaria (€)",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            height=350, margin=dict(t=50, b=20), xaxis_title="Hora", yaxis_title="",
        )
        fig3.update_traces(textfont_size=11)
        st.plotly_chart(fig3, use_container_width=True)

    st.divider()
    st.caption(f"Datos: {fecha_min.strftime('%d/%m/%Y')} → {fecha_max.strftime('%d/%m/%Y')} · {len(df)} franjas · Total €{total_ventas:,.2f}")

# ── UI principal ──────────────────────────────────────────────
st.title("☕ Vietnamito — Dashboard de Ventas")

uploaded = st.file_uploader(
    "Sube un CSV nuevo de Epos Now para actualizar los datos",
    type=["csv"],
    help="Descárgalo desde Epos Now → Reports → Sales Breakdown by Hour"
)

if uploaded:
    with st.spinner("Procesando y guardando en la nube..."):
        rows = parse_csv(uploaded)
        if rows:
            save_to_supabase(rows)
            st.success(f"✅ {len(rows)} registros guardados. Los datos se han actualizado.")
        else:
            st.error("No se pudieron leer datos del CSV.")

with st.spinner("Cargando datos..."):
    df = load_from_supabase()

if df.empty:
    st.info("Sube un CSV para empezar. La próxima vez los datos se cargarán automáticamente.")
else:
    render_dashboard(df)
