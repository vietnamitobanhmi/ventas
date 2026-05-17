import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from supabase import create_client

st.set_page_config(page_title="Vietnamito — Ventas", page_icon="☕", layout="wide")

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
WEEK_COLORS = [
    "#E63946","#F4A261","#2A9D8F","#457B9D","#9B2226",
    "#6A4C93","#1982C4","#8AC926","#FF595E","#6A994E",
    "#BC6C25","#4CC9F0","#F72585","#3A0CA3","#4361EE",
]

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_foto(sb, file, prefix):
    import urllib.parse
    ext = file.name.split(".")[-1].lower()
    fname = f"pasos/{prefix}_{file.name}"
    fname_encoded = urllib.parse.quote(fname, safe="/")
    try:
        sb.storage.from_("assets").upload(fname, file.read(), {"content-type": f"image/{ext}", "upsert": "true"})
    except Exception:
        file.seek(0)
        sb.storage.from_("assets").update(fname, file.read(), {"content-type": f"image/{ext}"})
    return f"{SUPABASE_URL}/storage/v1/object/public/assets/{fname_encoded}"

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
    sb.table("ventas").delete().neq("id", 0).execute()
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

def calcular_por_semana(df):
    df2 = df.copy()
    df2["fecha_ts"] = pd.to_datetime(df2["fecha"])
    df2["lunes"] = df2["fecha_ts"] - pd.to_timedelta(df2["fecha_ts"].dt.weekday, unit="D")
    df2["semana"] = df2["lunes"].dt.strftime("%Y-%m-%d")
    dia_totales = df2.groupby(["semana", "fecha", "dow"])["valor"].sum().reset_index()
    semana_dow = dia_totales.groupby(["semana", "dow"])["valor"].mean().reset_index()
    semana_labels = {}
    for s in semana_dow["semana"].unique():
        lunes = pd.Timestamp(s)
        domingo = lunes + timedelta(days=6)
        semana_labels[s] = f"{lunes.strftime('%d/%m')} – {domingo.strftime('%d/%m/%y')}"
    semana_dow["label"] = semana_dow["semana"].map(semana_labels)
    return semana_dow, semana_labels

def boxplot_horario(df_filtrado, titulo, color="#5DCAA5", line_color="#2A9D8F", ymax=None, turnos_data=None, empleados_data=None, dow_filter=None):
    df_filtrado = df_filtrado.copy()
    df_filtrado["fecha_ts"] = pd.to_datetime(df_filtrado["fecha"])
    df_filtrado["dow_label"] = df_filtrado["fecha_ts"].dt.weekday.map(DIAS)
    df_filtrado["fecha_str"] = df_filtrado["fecha_ts"].dt.strftime("%d/%m/%Y")
    dia_hora = df_filtrado.groupby(["fecha", "fecha_str", "dow_label", "hora"])["valor"].sum().reset_index()
    horas_sorted = sorted(dia_hora["hora"].unique())
    fig = go.Figure()
    for h in horas_sorted:
        subset = dia_hora[dia_hora["hora"] == h]
        hover = subset.apply(lambda r: f"{r['dow_label']} {r['fecha_str']}<br>€{r['valor']:.2f}", axis=1).tolist()
        fig.add_trace(go.Box(
            y=subset["valor"].tolist(), name=f"{h}:00",
            marker_color=color, line_color=line_color,
            boxmean=True, boxpoints="all", jitter=0.3,
            marker=dict(size=5, opacity=0.5, color=color),
            text=hover, hovertemplate="%{text}<extra></extra>",
        ))
    fig.update_layout(
        title=titulo, yaxis_title="€ ventas", xaxis_title="Hora",
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(gridcolor="rgba(128,128,128,0.15)", zeroline=False, range=[0, ymax] if ymax else None),
        xaxis=dict(showgrid=False), showlegend=False, height=480, margin=dict(t=60, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("La caja = rango central del 50% de días. Línea = mediana. Cruz = media. Cada punto = un día real.")

    if turnos_data and empleados_data:
        emp_coste = {e["id"]: e["coste_hora"] for e in empleados_data}
        coste_hora = {}
        for tr in turnos_data:
            dow_tr = int(tr["dia_semana"])
            if dow_filter is not None and dow_tr != int(dow_filter):
                continue
            slot = tr["slot"]
            h = int(slot.split(":")[0])
            coste_slot = emp_coste.get(tr["empleado_id"], 10) * 0.5
            coste_hora[h] = coste_hora.get(h, 0) + coste_slot

        if dow_filter is None and coste_hora:
            dias_con_turnos = len(set(tr["dia_semana"] for tr in turnos_data))
            if dias_con_turnos > 0:
                coste_hora = {h: v / dias_con_turnos for h, v in coste_hora.items()}

        avg_ventas = dia_hora.groupby("hora")["valor"].mean()
        horas_comunes = sorted(avg_ventas.index)
        ventas_vals = [avg_ventas.get(h, 0) * 0.75 for h in horas_comunes]
        coste_vals = [coste_hora.get(h, 0) for h in horas_comunes]
        margen_vals = [v - c for v, c in zip(ventas_vals, coste_vals)]
        margen_colors = ["#5DCAA5" if m >= 0 else "#E63946" for m in margen_vals]
        horas_labels = [f"{h}:00" for h in horas_comunes]

        fig_rent = go.Figure()
        fig_rent.add_trace(go.Bar(x=horas_labels, y=ventas_vals, name="Ventas promedio", marker_color="rgba(93,202,165,0.5)", marker_line_width=0))
        fig_rent.add_trace(go.Bar(x=horas_labels, y=coste_vals, name="Coste personal", marker_color="rgba(230,57,70,0.5)", marker_line_width=0))
        fig_rent.add_trace(go.Scatter(
            x=horas_labels, y=margen_vals, name="Margen",
            mode="lines+markers+text", line=dict(color="#F4A261", width=2),
            marker=dict(size=7, color=margen_colors),
            text=[f"€{m:+.0f}" for m in margen_vals],
            textposition="top center", textfont=dict(size=10),
        ))
        fig_rent.add_hline(y=0, line_dash="dot", line_color="rgba(128,128,128,0.5)")
        fig_rent.update_layout(
            title="Ventas netas (−25% producto) vs coste de personal por franja horaria",
            yaxis_title="€", xaxis_title="Hora",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(gridcolor="rgba(128,128,128,0.15)", zeroline=False),
            xaxis=dict(showgrid=False), barmode="overlay",
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="left", x=0),
            height=380, margin=dict(t=50, b=80),
        )
        st.plotly_chart(fig_rent, use_container_width=True)
        st.caption("Ventas netas = venta media × 75% (descontado 25% coste de producto). Margen = ventas netas − coste de personal. Verde = rentable, rojo = coste supera ventas netas.")

    with st.expander("Ver datos"):
        resumen = dia_hora.groupby("hora")["valor"].agg(
            Media="mean", Mediana="median", Min="min", Max="max", Std="std", Instancias="count"
        ).round(2).reset_index()
        resumen["hora"] = resumen["hora"].apply(lambda h: f"{h}:00")
        resumen.columns = ["Hora", "Media (€)", "Mediana (€)", "Mín (€)", "Máx (€)", "Desv. típica", "Nº instancias"]
        st.dataframe(resumen, hide_index=True, use_container_width=True)

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

    sb_counts = get_supabase()
    ped_pend = len((sb_counts.table("pedidos").select("id").eq("estado","pendiente").execute().data or []))
    res_pend = len((sb_counts.table("reservas").select("id").eq("estado","pendiente").execute().data or []))

    ped_label = f"🛵 Pedidos {'🔴 ' + str(ped_pend) if ped_pend > 0 else ''}"
    res_label = f"🍽️ Reservas {'🔴 ' + str(res_pend) if res_pend > 0 else ''}"

    tab0, tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "💰 Rentabilidad",
        "📅 Por día de semana",
        "🕐 Por franja horaria",
        "🌡️ Mapa de calor",
        "📈 Por semana",
        "👥 Turnos",
        "📋 Checklists",
        ped_label,
        res_label,
        "🌐 Web",
    ])

    # ── TAB 0: Rentabilidad ─────────────────────────────────
    with tab0:
        import datetime as dt_rent
        sb0 = get_supabase()

        st.markdown("### Dashboard de rentabilidad")

        # Periodo selector
        periodo = st.radio("Periodo:", [
            "Semana en curso", "Últimos 7 días",
            "Mes en curso", "Últimos 30 días",
            "Últimos 90 días", "Total registrado"
        ], horizontal=True, key="rent_periodo")

        hoy = dt_rent.date.today()
        if periodo == "Semana en curso":
            inicio = hoy - dt_rent.timedelta(days=hoy.weekday())
            fin = hoy
        elif periodo == "Últimos 7 días":
            inicio = hoy - dt_rent.timedelta(days=6)
            fin = hoy
        elif periodo == "Mes en curso":
            inicio = hoy.replace(day=1)
            fin = hoy
        elif periodo == "Últimos 30 días":
            inicio = hoy - dt_rent.timedelta(days=29)
            fin = hoy
        elif periodo == "Últimos 90 días":
            inicio = hoy - dt_rent.timedelta(days=89)
            fin = hoy
        else:
            inicio = df["fecha"].min()
            fin = df["fecha"].max()

        # Filtrar datos por periodo
        df_rent = df[(df["fecha"] >= inicio) & (df["fecha"] <= fin)].copy()

        if df_rent.empty:
            st.warning("No hay datos para ese periodo.")
        else:
            # Cargar turnos y empleados actuales
            turnos_data = sb0.table("turnos").select("*").execute().data or []
            empleados_data = sb0.table("empleados").select("*").execute().data or []
            emp_coste = {e["id"]: e["coste_hora"] for e in empleados_data}

            # Calcular coste de personal por slot (dow, slot) -> coste
            # Usar slot completo (HH:MM) como key para no perder los :30
            coste_por_slot_full = {}  # (dow, slot) -> coste total ese slot
            horas_con_staff = set()  # (dow, hora_entera) con al menos 1 trabajador
            for tr in turnos_data:
                dow = int(tr["dia_semana"])
                slot = tr["slot"]
                h = int(slot.split(":")[0])
                coste = emp_coste.get(tr["empleado_id"], 10) * 0.5
                key = (dow, slot)
                coste_por_slot_full[key] = coste_por_slot_full.get(key, 0) + coste
                horas_con_staff.add((dow, h))

            # Coste total por día de la semana (suma de todos sus slots)
            coste_por_slot = {}  # (dow,) -> coste diario total
            for (dow, slot), coste in coste_por_slot_full.items():
                coste_por_slot[(dow, slot)] = coste

            # Filtrar ventas solo en horas con staff
            df_rent["dow"] = pd.to_datetime(df_rent["fecha"]).dt.weekday
            df_rent_staff = df_rent[df_rent.apply(
                lambda r: (int(r["dow"]), int(r["hora"])) in horas_con_staff, axis=1
            )].copy()

            # Calcular días únicos en el periodo para escalar coste semanal
            n_dias = (fin - inicio).days + 1
            n_semanas = n_dias / 7

            # Días reales abiertos por dow (días con al menos una venta)
            dias_abiertos_por_dow = {}
            for dow_idx in range(7):
                df_dow_check = df_rent[df_rent["dow"] == dow_idx]
                dias_con_venta = df_dow_check.groupby("fecha")["valor"].sum()
                dias_abiertos_por_dow[dow_idx] = int((dias_con_venta > 0).sum())

            # Coste diario por dow = suma de todos sus slots
            coste_dia_por_dow = {}
            for (dow_idx, slot), coste in coste_por_slot.items():
                coste_dia_por_dow[dow_idx] = coste_dia_por_dow.get(dow_idx, 0) + coste

            # Coste real del periodo: coste/día × días abiertos
            coste_periodo = sum(
                coste_dia_por_dow.get(dow_idx, 0) * dias_abiertos_por_dow.get(dow_idx, 0)
                for dow_idx in range(7)
            )
            coste_semanal = sum(coste_dia_por_dow.values())

            # Ventas brutas (solo horas con staff)
            ventas_brutas = df_rent_staff["valor"].sum()

            # Ventas netas (descontando 25% coste producto)
            ventas_netas = ventas_brutas * 0.75

            # Margen final
            margen = ventas_netas - coste_periodo
            margen_pct = (margen / ventas_brutas * 100) if ventas_brutas > 0 else 0

            # Días con datos en el periodo
            dias_con_datos = df_rent_staff["fecha"].nunique()

            # Métricas principales
            st.markdown(f"**{inicio.strftime('%d/%m/%Y')} → {fin.strftime('%d/%m/%Y')}** · {dias_con_datos} días con ventas · {n_dias} días en periodo")
            st.markdown("")

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Ventas brutas", f"€{ventas_brutas:,.2f}",
                       help="Solo horas con personal según configuración actual")
            col2.metric("Ventas netas (−25%)", f"€{ventas_netas:,.2f}",
                       help="Descontado 25% de coste de producto")
            col3.metric("Coste personal", f"€{coste_periodo:,.2f}",
                       help="Basado en turnos y costes actuales × semanas del periodo")
            delta_color = "normal" if margen >= 0 else "inverse"
            col4.metric("Margen", f"€{margen:,.2f}", f"{margen_pct:.1f}% s/ventas",
                       delta_color=delta_color)

            st.markdown("")

            # Semáforo visual
            if margen > 0:
                st.success(f"✅ **Rentable** — €{margen:,.2f} de beneficio en el periodo ({margen_pct:.1f}% sobre ventas brutas)")
            else:
                st.error(f"🔴 **Pérdidas** — €{abs(margen):,.2f} de déficit en el periodo ({margen_pct:.1f}% sobre ventas brutas)")

            st.divider()

            # Desglose por día de la semana
            st.markdown("#### Desglose por día de la semana")
            st.caption("Solo horas con personal. Ventas netas = ventas × 75%. Margen = ventas netas − coste personal.")

            rows_dow = []
            for dow_idx in range(7):
                # Ventas de ese dow en el periodo con staff
                df_dow = df_rent_staff[df_rent_staff["dow"] == dow_idx]
                v_brutas = df_dow["valor"].sum()
                v_netas = v_brutas * 0.75

                # Coste personal ese día (por semana × semanas)
                coste_dia_sem = sum(v for (d,h), v in coste_por_slot.items() if d == dow_idx)
                coste_dia_periodo = coste_dia_sem * n_semanas

                margen_dia = v_netas - coste_dia_periodo
                n_dias_dow = df_dow["fecha"].nunique()

                rows_dow.append({
                    "Día": DIAS[dow_idx],
                    "Días c/datos": n_dias_dow,
                    "Ventas brutas": f"€{v_brutas:,.2f}",
                    "Ventas netas": f"€{v_netas:,.2f}",
                    "Coste personal": f"€{coste_dia_periodo:,.2f}",
                    "Margen": f"€{margen_dia:,.2f}",
                    "✓": "✅" if margen_dia >= 0 else "🔴"
                })

            st.dataframe(pd.DataFrame(rows_dow), hide_index=True, use_container_width=True)

            st.divider()

            # Evolución semanal del margen
            st.markdown("#### Evolución semanal del margen")
            df_rent2 = df_rent_staff.copy()
            df_rent2["fecha_ts"] = pd.to_datetime(df_rent2["fecha"])
            df_rent2["lunes"] = df_rent2["fecha_ts"] - pd.to_timedelta(df_rent2["fecha_ts"].dt.weekday, unit="D")
            df_rent2["semana"] = df_rent2["lunes"].dt.strftime("%Y-%m-%d")

            semana_margen = df_rent2.groupby("semana")["valor"].sum().reset_index()
            semana_margen.columns = ["semana","ventas_brutas"]
            semana_margen["ventas_netas"] = semana_margen["ventas_brutas"] * 0.75
            # Coste real por semana: contar días abiertos en cada semana
            def coste_semana(semana_str):
                lunes = pd.Timestamp(semana_str)
                coste = 0
                for d in range(7):
                    fecha_dia = (lunes + pd.Timedelta(days=d)).date()
                    if fecha_dia < inicio or fecha_dia > fin:
                        continue
                    ventas_dia = df_rent[df_rent["fecha"] == fecha_dia]["valor"].sum()
                    if ventas_dia > 0:
                        coste += coste_dia_por_dow.get(d, 0)
                return coste
            semana_margen["coste"] = semana_margen["semana"].apply(coste_semana)
            semana_margen["margen"] = semana_margen["ventas_netas"] - semana_margen["coste"]
            semana_margen["label"] = semana_margen["semana"].apply(
                lambda s: pd.Timestamp(s).strftime("%d/%m")
            )
            semana_margen = semana_margen.sort_values("semana")

            fig_margen = go.Figure()
            fig_margen.add_trace(go.Bar(
                x=semana_margen["label"], y=semana_margen["ventas_netas"].round(2),
                name="Ventas netas", marker_color="rgba(93,202,165,0.6)", marker_line_width=0,
            ))
            fig_margen.add_trace(go.Bar(
                x=semana_margen["label"], y=semana_margen["coste"].round(2),
                name="Coste personal", marker_color="rgba(230,57,70,0.6)", marker_line_width=0,
            ))
            fig_margen.add_trace(go.Scatter(
                x=semana_margen["label"], y=semana_margen["margen"].round(2),
                name="Margen", mode="lines+markers+text",
                line=dict(color="#F4A261", width=2),
                marker=dict(size=8, color=["#5DCAA5" if v >= 0 else "#E63946" for v in semana_margen["margen"]]),
                text=[f"€{v:+.0f}" for v in semana_margen["margen"]],
                textposition="top center", textfont=dict(size=11),
            ))
            fig_margen.add_hline(y=0, line_dash="dot", line_color="rgba(128,128,128,0.4)")
            fig_margen.update_layout(
                title="Ventas netas vs coste personal por semana (€)",
                yaxis_title="€", barmode="group",
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(gridcolor="rgba(128,128,128,0.15)", zeroline=False),
                xaxis=dict(showgrid=False),
                legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="left", x=0),
                height=420, margin=dict(t=50, b=80),
            )
            st.plotly_chart(fig_margen, use_container_width=True)

            st.caption(f"⚠️ El coste de personal es estimado basándose en la configuración de turnos actual, aplicada a todas las semanas del periodo. Los turnos pasados pueden haber sido diferentes.")

    with tab1:
        avg_dow = calcular_promedios_dia(df)
        labels = [DIAS[d] for d in DIAS_ORDER]
        values = [round(avg_dow.get(d, 0), 2) for d in DIAS_ORDER]
        fig = go.Figure(go.Bar(
            x=labels, y=values, marker_color=COLORS, marker_line_width=0,
            text=[f"€{v:.0f}" for v in values], textposition="outside",
        ))
        fig.update_layout(
            title="Venta media por día de la semana (€, IVA incl.)", yaxis_title="€ promedio",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(gridcolor="rgba(128,128,128,0.15)", zeroline=False),
            xaxis=dict(showgrid=False), showlegend=False, height=400, margin=dict(t=50, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)
        with st.expander("Ver datos"):
            st.dataframe(pd.DataFrame({"Día": labels, "Promedio (€)": [f"€{v:.2f}" for v in values]}), hide_index=True, use_container_width=True)

        st.divider()
        st.markdown("**Evolución semanal por día**")
        st.caption("Cada línea es un día de la semana. Cada punto es el total de ventas de ese día en cada semana.")

        df_evo = df.copy()
        df_evo["fecha_ts"] = pd.to_datetime(df_evo["fecha"])
        df_evo["lunes"] = df_evo["fecha_ts"] - pd.to_timedelta(df_evo["fecha_ts"].dt.weekday, unit="D")
        df_evo["semana"] = df_evo["lunes"].dt.strftime("%Y-%m-%d")
        df_evo["dow"] = df_evo["fecha_ts"].dt.weekday
        dia_sem = df_evo.groupby(["semana","fecha","dow"])["valor"].sum().reset_index()

        semana_labels_evo = {}
        for s in sorted(dia_sem["semana"].unique()):
            lunes = pd.Timestamp(s)
            semana_labels_evo[s] = lunes.strftime("%d/%m")

        fig_evo = go.Figure()
        for dow_idx in DIAS_ORDER:
            d = dia_sem[dia_sem["dow"] == dow_idx].sort_values("semana")
            if d.empty:
                continue
            fig_evo.add_trace(go.Scatter(
                x=d["semana"].map(semana_labels_evo),
                y=d["valor"].round(2),
                mode="lines+markers",
                name=DIAS[dow_idx],
                line=dict(color=COLORS[dow_idx % len(COLORS)], width=2),
                marker=dict(size=7, color=COLORS[dow_idx % len(COLORS)]),
                connectgaps=False,
            ))

        fig_evo.update_layout(
            title="Evolución de ventas por día de la semana (€, IVA incl.)",
            yaxis_title="€ ventas", xaxis_title="Semana (lunes)",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(gridcolor="rgba(128,128,128,0.15)", zeroline=False),
            xaxis=dict(showgrid=False, tickangle=-30),
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="left", x=0),
            height=480, margin=dict(t=50, b=100),
        )
        st.plotly_chart(fig_evo, use_container_width=True)

    with tab2:
        import datetime as dt_franja
        fecha_min_data = df["fecha"].min()
        fecha_max_data = df["fecha"].max()
        today = dt_franja.date.today()

        opciones = ["Todos los días"] + [DIAS[d] for d in DIAS_ORDER]
        seleccion = st.selectbox("Día de la semana:", opciones, key="sel_franja")
        fc2, fc3 = st.columns(2)
        fecha_desde = fc2.date_input("Desde:", value=fecha_min_data, min_value=fecha_min_data, max_value=fecha_max_data, key="f_desde")
        fecha_hasta = fc3.date_input("Hasta:", value=min(today, fecha_max_data), min_value=fecha_min_data, max_value=fecha_max_data, key="f_hasta")

        df_f = df.copy()
        df_f["fecha_ts"] = pd.to_datetime(df_f["fecha"])
        df_f["dow_label"] = df_f["fecha_ts"].dt.weekday.map(DIAS)
        df_f = df_f[(df_f["fecha"] >= fecha_desde) & (df_f["fecha"] <= fecha_hasta)]
        if seleccion != "Todos los días":
            df_f = df_f[df_f["dow_label"] == seleccion]

        if df_f.empty:
            st.warning("No hay datos para ese filtro.")
        else:
            n_inst = df_f["fecha"].nunique()
            titulo_sel = seleccion if seleccion != "Todos los días" else "todos los días"
            st.caption(f"{n_inst} instancias de {titulo_sel} con datos · {fecha_desde.strftime('%d/%m/%Y')} – {fecha_hasta.strftime('%d/%m/%Y')}")
            dia_hora_global = df.groupby(["fecha", "hora"])["valor"].sum()
            ymax_global = dia_hora_global.max() * 1.15
            sb_t2 = get_supabase()
            turnos_t2 = sb_t2.table("turnos").select("*").execute().data or []
            empleados_t2 = sb_t2.table("empleados").select("*").execute().data or []
            dow_filter_t2 = None
            if seleccion != "Todos los días":
                dow_filter_t2 = [d for d in DIAS_ORDER if DIAS[d] == seleccion][0]
            boxplot_horario(df_f, f"Distribución de ventas por franja horaria — {titulo_sel} (€, IVA incl.)",
                ymax=ymax_global, turnos_data=turnos_t2, empleados_data=empleados_t2, dow_filter=dow_filter_t2)

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
            title="Venta media por día y franja horaria (€, IVA incl.)",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            height=350, margin=dict(t=50, b=20), xaxis_title="Hora", yaxis_title="",
        )
        fig3.update_traces(textfont_size=11)
        st.plotly_chart(fig3, use_container_width=True)

    with tab4:
        semana_dow, semana_labels = calcular_por_semana(df)
        semanas_sorted = sorted(semana_labels.keys())
        labels_sorted = [semana_labels[s] for s in semanas_sorted]

        st.markdown("**Selecciona las semanas a mostrar:**")
        cols = st.columns(min(len(semanas_sorted), 4))
        seleccionadas = []
        for i, (s, lbl) in enumerate(zip(semanas_sorted, labels_sorted)):
            col = cols[i % len(cols)]
            color_sem = WEEK_COLORS[i % len(WEEK_COLORS)]
            c_icon, c_check = col.columns([1, 6])
            c_icon.markdown(f'<div style="width:18px;height:18px;background:{color_sem};border-radius:3px;margin-top:6px;"></div>', unsafe_allow_html=True)
            if c_check.checkbox(lbl, value=True, key=f"semana_{s}"):
                seleccionadas.append(s)

        if not seleccionadas:
            st.warning("Selecciona al menos una semana.")
        else:
            fig4 = go.Figure()
            for i, s in enumerate(semanas_sorted):
                if s not in seleccionadas:
                    continue
                color = WEEK_COLORS[i % len(WEEK_COLORS)]
                datos = semana_dow[semana_dow["semana"] == s].set_index("dow")
                vals = [round(datos.loc[d, "valor"], 2) if d in datos.index else None for d in DIAS_ORDER]
                fig4.add_trace(go.Scatter(
                    x=[DIAS[d] for d in DIAS_ORDER], y=vals, mode="lines+markers",
                    name=semana_labels[s], line=dict(color=color, width=2),
                    marker=dict(size=7, color=color), connectgaps=False,
                ))
            fig4.update_layout(
                title="Ventas por día de semana — comparativa semanal (€, IVA incl.)",
                yaxis_title="€ ventas", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(gridcolor="rgba(128,128,128,0.15)", zeroline=False, range=[0, 1200]),
                xaxis=dict(showgrid=False),
                legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="left", x=0),
                height=480, margin=dict(t=50, b=120),
            )
            st.plotly_chart(fig4, use_container_width=True)

            df2 = df.copy()
            df2["fecha_ts"] = pd.to_datetime(df2["fecha"])
            df2["lunes"] = df2["fecha_ts"] - pd.to_timedelta(df2["fecha_ts"].dt.weekday, unit="D")
            df2["semana"] = df2["lunes"].dt.strftime("%Y-%m-%d")
            avg_semana = df2.groupby("semana").agg(total=("valor","sum"), franjas=("valor","count")).reset_index()
            avg_semana["avg_franja"] = (avg_semana["total"] / avg_semana["franjas"]).round(2)
            avg_semana = avg_semana[avg_semana["semana"].isin(semanas_sorted)]
            avg_semana["label"] = avg_semana["semana"].map(semana_labels)
            avg_semana = avg_semana.sort_values("semana")

            fig5 = go.Figure(go.Scatter(
                x=avg_semana["label"], y=avg_semana["avg_franja"],
                mode="lines+markers+text", line=dict(color="#5DCAA5", width=2),
                marker=dict(size=8, color="#5DCAA5"),
                text=[f"€{v:.0f}" for v in avg_semana["avg_franja"]],
                textposition="top center", textfont=dict(size=11),
            ))
            fig5.update_layout(
                title="Evolución del promedio de ventas por franja horaria trabajada (€, IVA incl.)",
                yaxis_title="€ promedio/franja", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(gridcolor="rgba(128,128,128,0.15)", zeroline=False),
                xaxis=dict(showgrid=False, tickangle=-30),
                showlegend=False, height=350, margin=dict(t=50, b=80),
            )
            st.plotly_chart(fig5, use_container_width=True)

            total_semana = df2.groupby("semana")["valor"].sum().reset_index()
            total_semana = total_semana[total_semana["semana"].isin(semanas_sorted)]
            total_semana["label"] = total_semana["semana"].map(semana_labels)
            total_semana = total_semana.sort_values("semana")
            bar_colors = [WEEK_COLORS[semanas_sorted.index(s) % len(WEEK_COLORS)] for s in total_semana["semana"]]

            fig6 = go.Figure(go.Bar(
                x=total_semana["label"], y=total_semana["valor"].round(2),
                marker_color=bar_colors, marker_line_width=0,
                text=[f"€{v:.0f}" for v in total_semana["valor"]], textposition="outside",
            ))
            fig6.update_layout(
                title="Total de ventas por semana (€, IVA incl.)",
                yaxis_title="€ total", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(gridcolor="rgba(128,128,128,0.15)", zeroline=False),
                xaxis=dict(showgrid=False, tickangle=-30),
                showlegend=False, height=380, margin=dict(t=50, b=80),
            )
            st.plotly_chart(fig6, use_container_width=True)

    with tab5:
        import datetime as dt_mod
        sb = get_supabase()

        emp_res = sb.table("empleados").select("*").order("id").execute()
        empleados = emp_res.data if emp_res.data else []

        st.markdown("### Empleados")
        st.caption("Edita nombres y coste/hora. Los turnos se eliminan automáticamente al borrar un empleado.")

        header = st.columns([3, 2, 1, 1])
        header[0].markdown("**Nombre**")
        header[1].markdown("**€/hora**")
        header[2].markdown("**Guardar**")
        header[3].markdown("**Eliminar**")

        for emp in empleados:
            c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
            nuevo_nombre = c1.text_input("n", value=emp["nombre"], label_visibility="collapsed", key=f"nom_{emp['id']}")
            nuevo_coste = c2.number_input("c", value=float(emp["coste_hora"]), min_value=0.0, step=0.5, format="%.2f", label_visibility="collapsed", key=f"cos_{emp['id']}")
            if c3.button("💾", key=f"saveemp_{emp['id']}"):
                sb.table("empleados").update({"nombre": nuevo_nombre, "coste_hora": nuevo_coste}).eq("id", emp["id"]).execute()
                st.success(f"✅ {nuevo_nombre} guardado")
                st.rerun()
            if c4.button("🗑️", key=f"delemp_{emp['id']}"):
                st.session_state[f"confirm_del_{emp['id']}"] = True
            if st.session_state.get(f"confirm_del_{emp['id']}"):
                st.warning(f"¿Seguro que quieres eliminar a **{emp['nombre']}** y todos sus turnos?")
                conf1, conf2 = st.columns(2)
                if conf1.button("✅ Sí, eliminar", key=f"yes_del_{emp['id']}"):
                    sb.table("turnos").delete().eq("empleado_id", emp["id"]).execute()
                    sb.table("empleados").delete().eq("id", emp["id"]).execute()
                    st.session_state.pop(f"confirm_del_{emp['id']}", None)
                    st.success(f"✅ {emp['nombre']} eliminado")
                    st.rerun()
                if conf2.button("❌ Cancelar", key=f"no_del_{emp['id']}"):
                    st.session_state.pop(f"confirm_del_{emp['id']}", None)
                    st.rerun()

        st.markdown("")
        with st.expander("➕ Añadir empleado"):
            na1, na2, na3 = st.columns([3, 2, 1])
            nuevo_emp_nombre = na1.text_input("Nombre:", key="new_emp_nombre")
            nuevo_emp_coste = na2.number_input("€/hora:", value=10.0, min_value=0.0, step=0.5, format="%.2f", key="new_emp_coste")
            if na3.button("➕ Añadir", key="add_emp"):
                if nuevo_emp_nombre.strip():
                    sb.table("empleados").insert({"nombre": nuevo_emp_nombre.strip(), "coste_hora": nuevo_emp_coste}).execute()
                    st.success(f"✅ {nuevo_emp_nombre} añadido")
                    st.rerun()
                else:
                    st.warning("Escribe un nombre.")

        st.divider()
        st.markdown("### Turnos por día")

        slots = []
        current = dt_mod.datetime(2000, 1, 1, 7, 0)
        end = dt_mod.datetime(2000, 1, 2, 1, 30)
        while current < end:
            slots.append(current.strftime("%H:%M"))
            current += dt_mod.timedelta(minutes=30)

        emp_ids = [e["id"] for e in empleados]
        emp_nombres = {e["id"]: e["nombre"] for e in empleados}
        emp_coste = {e["id"]: e["coste_hora"] for e in empleados}

        with st.expander("📋 Copiar turnos de un día a otro"):
            cc1, cc2, cc3 = st.columns([2, 2, 2])
            dia_origen = cc1.selectbox("Copiar de:", [DIAS[d] for d in DIAS_ORDER], key="copy_from")
            dias_destino_opts = [DIAS[d] for d in DIAS_ORDER if DIAS[d] != dia_origen]
            dias_destino_sel = cc2.multiselect("Copiar a:", dias_destino_opts, key="copy_to")
            if cc3.button("📋 Copiar", key="do_copy"):
                if not dias_destino_sel:
                    st.warning("Selecciona al menos un día destino.")
                else:
                    dow_origen = [d for d in DIAS_ORDER if DIAS[d] == dia_origen][0]
                    turnos_res_copy = sb.table("turnos").select("*").execute()
                    turnos_origen = [(tr["empleado_id"], tr["slot"]) for tr in (turnos_res_copy.data or []) if tr["dia_semana"] == dow_origen]
                    for dia_dest_label in dias_destino_sel:
                        dow_dest = [d for d in DIAS_ORDER if DIAS[d] == dia_dest_label][0]
                        sb.table("turnos").delete().eq("dia_semana", dow_dest).execute()
                        if turnos_origen:
                            sb.table("turnos").insert([
                                {"empleado_id": eid, "dia_semana": dow_dest, "slot": slot}
                                for eid, slot in turnos_origen
                            ]).execute()
                    st.success(f"✅ Turnos del {dia_origen} copiados a: {', '.join(dias_destino_sel)}")
                    st.rerun()

        turnos_res = sb.table("turnos").select("*").execute()
        turnos_set = set()
        for tr in (turnos_res.data or []):
            turnos_set.add((tr["empleado_id"], tr["dia_semana"], tr["slot"]))

        dias_tabs = st.tabs([DIAS[d] for d in DIAS_ORDER])

        for di, dow in enumerate(DIAS_ORDER):
            with dias_tabs[di]:
                data = {}
                for slot in slots:
                    row = {}
                    for eid in emp_ids:
                        row[emp_nombres.get(eid, f"Emp {eid}")] = (eid, dow, slot) in turnos_set
                    data[slot] = row
                df_grid = pd.DataFrame(data).T
                df_grid.index.name = "Hora"
                df_grid = df_grid.reset_index()

                edited = st.data_editor(
                    df_grid,
                    key=f"grid_{dow}",
                    hide_index=True,
                    use_container_width=True,
                    column_config={"Hora": st.column_config.TextColumn("Hora", disabled=True)},
                    height=min(400, len(slots) * 35 + 40),
                )

                if st.button(f"💾 Guardar turnos {DIAS[dow]}", key=f"saveturno_{dow}", type="primary"):
                    sb.table("turnos").delete().eq("dia_semana", dow).execute()
                    to_insert = []
                    for _, row in edited.iterrows():
                        slot = row["Hora"]
                        for eid in emp_ids:
                            col_name = emp_nombres.get(eid, f"Emp {eid}")
                            if row.get(col_name, False):
                                to_insert.append({"empleado_id": eid, "dia_semana": dow, "slot": slot})
                    if to_insert:
                        sb.table("turnos").insert(to_insert).execute()
                    turnos_res = sb.table("turnos").select("*").execute()
                    turnos_set = set((tr["empleado_id"], tr["dia_semana"], tr["slot"]) for tr in (turnos_res.data or []))
                    st.success(f"✅ {len(to_insert)} slots guardados para {DIAS[dow]}")
                    st.rerun()

                horas_dia = {}
                for _, row in edited.iterrows():
                    for eid in emp_ids:
                        col_name = emp_nombres.get(eid, f"Emp {eid}")
                        if row.get(col_name, False):
                            horas_dia[eid] = horas_dia.get(eid, 0) + 0.5
                if any(horas_dia.values()):
                    st.markdown("**Resumen del día:**")
                    res_cols = st.columns(len(emp_ids))
                    for ei, eid in enumerate(emp_ids):
                        h = horas_dia.get(eid, 0)
                        coste = h * emp_coste.get(eid, 10)
                        res_cols[ei].metric(emp_nombres.get(eid, f"Emp {eid}"), f"{h:.1f}h", f"€{coste:.2f}")

                st.divider()

        st.markdown("### Resumen semanal")
        turnos_all = sb.table("turnos").select("*").execute().data or []
        resumen_rows = []
        for emp in empleados:
            eid = emp["id"]
            total_h = sum(0.5 for tr in turnos_all if tr["empleado_id"] == eid)
            total_coste = total_h * emp["coste_hora"]
            resumen_rows.append({
                "Empleado": emp["nombre"],
                "Horas/semana": f"{total_h:.1f}h",
                "Coste semanal": f"€{total_coste:.2f}",
                "Coste mensual est.": f"€{total_coste * 4.33:.2f}",
            })
        st.dataframe(pd.DataFrame(resumen_rows), hide_index=True, use_container_width=True)
        total_sem = sum(
            sum(0.5 for tr in turnos_all if tr["empleado_id"] == e["id"]) * e["coste_hora"]
            for e in empleados
        )
        st.metric("💰 Coste total semanal staff", f"€{total_sem:.2f}", f"€{total_sem * 4.33:.2f} /mes est.")

    # ── TAB 6: Checklists (admin) ────────────────────────────
    with tab6:
        sb6 = get_supabase()
        st.markdown("### Procesos")

        proc_res = sb6.table("procesos").select("*").order("orden").execute()
        procesos = proc_res.data or []

        with st.expander("➕ Nuevo proceso"):
            new_proc_nombre = st.text_input("Nombre:", key="new_proc_nombre")
            new_proc_desc = st.text_input("Descripción (opcional):", key="new_proc_desc")
            new_proc_orden = st.number_input("Orden:", value=len(procesos)+1, min_value=1, key="new_proc_orden")
            if st.button("➕ Añadir proceso", key="add_proc"):
                if new_proc_nombre.strip():
                    try:
                        sb6.table("procesos").insert({
                            "nombre": new_proc_nombre.strip(),
                            "descripcion": new_proc_desc.strip() or None,
                            "orden": int(new_proc_orden),
                            "activo": True
                        }).execute()
                        st.success(f"✅ Proceso '{new_proc_nombre}' creado")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al crear proceso: {e}")
                else:
                    st.warning("Escribe un nombre.")

        if not procesos:
            st.info("No hay procesos. Crea uno arriba.")
        else:
            proc_sel = st.selectbox(
                "Selecciona proceso para editar:",
                options=[p["id"] for p in procesos],
                format_func=lambda x: next(p["nombre"] for p in procesos if p["id"] == x),
                key="proc_sel"
            )
            proc = next(p for p in procesos if p["id"] == proc_sel)

            with st.expander(f"✏️ Editar proceso: {proc['nombre']}"):
                e1, e2 = st.columns([3, 1])
                edit_nombre = e1.text_input("Nombre:", value=proc["nombre"], key=f"ep_nom_{proc['id']}")
                edit_orden = e2.number_input("Orden:", value=int(proc.get("orden") or 0), key=f"ep_ord_{proc['id']}")
                edit_desc = st.text_input("Descripción:", value=proc.get("descripcion") or "", key=f"ep_desc_{proc['id']}")
                edit_activo = st.checkbox("Activo", value=proc.get("activo", True), key=f"ep_act_{proc['id']}")
                ec1, ec2 = st.columns(2)
                if ec1.button("💾 Guardar cambios", key=f"save_proc_{proc['id']}"):
                    sb6.table("procesos").update({
                        "nombre": edit_nombre,
                        "descripcion": edit_desc or None,
                        "orden": int(edit_orden),
                        "activo": edit_activo
                    }).eq("id", proc["id"]).execute()
                    st.success("✅ Proceso actualizado")
                    st.rerun()
                if ec2.button("🗑️ Eliminar proceso", key=f"del_proc_{proc['id']}"):
                    st.session_state[f"confirm_del_proc_{proc['id']}"] = True
                if st.session_state.get(f"confirm_del_proc_{proc['id']}"):
                    st.error(f"¿Eliminar '{proc['nombre']}' y todos sus pasos?")
                    dc1, dc2 = st.columns(2)
                    if dc1.button("✅ Sí, eliminar", key=f"yes_del_proc_{proc['id']}"):
                        sb6.table("procesos").delete().eq("id", proc["id"]).execute()
                        st.session_state.pop(f"confirm_del_proc_{proc['id']}", None)
                        st.success("✅ Proceso eliminado")
                        st.rerun()
                    if dc2.button("❌ Cancelar", key=f"no_del_proc_{proc['id']}"):
                        st.session_state.pop(f"confirm_del_proc_{proc['id']}", None)
                        st.rerun()

            st.markdown(f"### Pasos de: {proc['nombre']}")

            pasos_res = sb6.table("pasos").select("*").eq("proceso_id", proc_sel).order("orden").execute()
            pasos = sorted(pasos_res.data or [], key=lambda p: p.get("orden", 0))

            if "add_paso_counter" not in st.session_state:
                st.session_state.add_paso_counter = 0
            counter = st.session_state.add_paso_counter

            with st.expander("➕ Añadir paso"):
                pa1, pa2 = st.columns([3, 1])
                new_paso_titulo = pa1.text_input("Título del paso:", key=f"new_paso_titulo_{counter}")
                new_paso_orden = pa2.number_input("Orden:", value=len(pasos)+1, min_value=1, key=f"new_paso_orden_{counter}")
                new_paso_desc = st.text_area("Descripción (opcional):", key=f"new_paso_desc_{counter}", height=80)
                new_paso_foto_url = st.text_input("URL de foto (opcional):", key=f"new_paso_foto_{counter}", placeholder="https://...")
                new_paso_foto_file = st.file_uploader("O sube una foto:", type=["jpg","jpeg","png","webp"], key=f"new_paso_foto_file_{counter}")
                if new_paso_foto_file:
                    st.image(new_paso_foto_file, width=200)
                if st.button("➕ Añadir paso", key=f"add_paso_{counter}"):
                    if new_paso_titulo.strip():
                        foto_url = new_paso_foto_url.strip() or None
                        if new_paso_foto_file:
                            try:
                                foto_url = upload_foto(sb6, new_paso_foto_file, f"{proc_sel}_{len(pasos)+1}")
                            except Exception as e:
                                st.warning(f"No se pudo subir la foto: {e}")
                        nuevo_orden = int(new_paso_orden)
                        # Si el orden ya existe, correr hacia abajo los posteriores
                        ordenes_existentes = [p["orden"] for p in pasos]
                        if nuevo_orden in ordenes_existentes:
                            pasos_a_mover = [p for p in pasos if p["orden"] >= nuevo_orden]
                            for p in pasos_a_mover:
                                sb6.table("pasos").update({"orden": p["orden"] + 1}).eq("id", p["id"]).execute()
                        sb6.table("pasos").insert({
                            "proceso_id": proc_sel,
                            "titulo": new_paso_titulo.strip(),
                            "descripcion": new_paso_desc.strip() or None,
                            "foto_url": foto_url,
                            "orden": nuevo_orden,
                        }).execute()
                        st.session_state.add_paso_counter += 1
                        st.success("✅ Paso añadido")
                        st.rerun()
                    else:
                        st.warning("Escribe un título.")

            if not pasos:
                st.info("Este proceso no tiene pasos. Añade uno arriba.")
            else:
                for paso in pasos:
                    with st.expander(f"**{paso['orden']}.** {paso['titulo']}", key=f"exp_paso_{paso['id']}_{paso['orden']}"):
                        sp1, sp2 = st.columns([3, 1])
                        s_titulo = sp1.text_input("Título:", value=paso["titulo"], key=f"sp_tit_{paso['id']}")
                        s_orden = sp2.number_input("Orden:", value=int(paso["orden"]), min_value=1, key=f"sp_ord_{paso['id']}")
                        s_desc = st.text_area("Descripción:", value=paso.get("descripcion") or "", key=f"sp_desc_{paso['id']}", height=80)
                        s_foto = st.text_input("URL foto:", value=paso.get("foto_url") or "", key=f"sp_foto_{paso['id']}")
                        s_foto_file = st.file_uploader("O sube foto nueva:", type=["jpg","jpeg","png","webp"], key=f"sp_foto_file_{paso['id']}")
                        if s_foto_file:
                            st.image(s_foto_file, width=200)
                            try:
                                s_foto = upload_foto(sb6, s_foto_file, str(paso['id']))
                                st.success("✅ Foto lista — pulsa Guardar para confirmar")
                            except Exception as e:
                                st.warning(f"No se pudo subir: {e}")
                        elif s_foto:
                            st.image(s_foto, width=200)
                        sc1, sc2 = st.columns(2)
                        if sc1.button("💾 Guardar", key=f"save_paso_{paso['id']}"):
                            sb6.table("pasos").update({
                                "titulo": s_titulo,
                                "descripcion": s_desc or None,
                                "foto_url": s_foto or None,
                                "orden": int(s_orden),
                            }).eq("id", paso["id"]).execute()
                            st.success("✅ Paso guardado")
                            st.rerun()
                        if sc2.button("🗑️ Eliminar", key=f"del_paso_{paso['id']}"):
                            st.session_state[f"confirm_del_paso_{paso['id']}"] = True
                        if st.session_state.get(f"confirm_del_paso_{paso['id']}"):
                            st.warning(f"¿Eliminar el paso **{paso['titulo']}**? Esta acción no se puede deshacer.")
                            dp1, dp2 = st.columns(2)
                            if dp1.button("✅ Sí, eliminar", key=f"yes_del_paso_{paso['id']}"):
                                sb6.table("pasos").delete().eq("id", paso["id"]).execute()
                                st.session_state.pop(f"confirm_del_paso_{paso['id']}", None)
                                st.success("✅ Paso eliminado")
                                st.rerun()
                            if dp2.button("❌ Cancelar", key=f"no_del_paso_{paso['id']}"):
                                st.session_state.pop(f"confirm_del_paso_{paso['id']}", None)
                                st.rerun()

        st.divider()
        st.markdown("### Historial de ejecuciones")

        ejec_res = sb6.table("ejecuciones").select("*").order("iniciado_at", desc=True).limit(50).execute()
        ejecuciones = ejec_res.data or []

        emp_lookup = {e["id"]: e["nombre"] for e in (sb6.table("empleados").select("id, nombre").execute().data or [])}
        proc_lookup = {p["id"]: p["nombre"] for p in (sb6.table("procesos").select("id, nombre").execute().data or [])}

        if not ejecuciones:
            st.info("Aún no hay ejecuciones registradas.")
        else:
            rows = []
            for e in ejecuciones:
                rows.append({
                    "Fecha": pd.Timestamp(e["iniciado_at"]).strftime("%d/%m/%Y %H:%M"),
                    "Empleado": emp_lookup.get(e["empleado_id"], "—"),
                    "Proceso": proc_lookup.get(e["proceso_id"], "—"),
                    "Completado": "✅" if e["completado"] else "⏳",
                })
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

            ejec_ids = {
                f"{emp_lookup.get(e['empleado_id'],'?')} — {proc_lookup.get(e['proceso_id'],'?')} — {pd.Timestamp(e['iniciado_at']).strftime('%d/%m %H:%M')}": e["id"]
                for e in ejecuciones
            }
            sel_ejec = st.selectbox("Ver detalle de ejecución:", list(ejec_ids.keys()), key="sel_ejec")
            if sel_ejec:
                ejec_id = ejec_ids[sel_ejec]
                ep_res = sb6.table("ejecucion_pasos").select("*").eq("ejecucion_id", ejec_id).order("timestamp").execute()
                ep_data = ep_res.data or []
                paso_lookup = {p["id"]: p for p in (sb6.table("pasos").select("id, titulo, orden").execute().data or [])}
                if ep_data:
                    for ep in ep_data:
                        estado = "✅ Hecho" if ep["estado"] == "hecho" else "⚠️ No pudo"
                        paso = paso_lookup.get(ep["paso_id"], {})
                        titulo = paso.get("titulo", "—")
                        orden = paso.get("orden", "?")
                        st.markdown(f"**{orden}. {titulo}** — {estado}")
                        if ep.get("nota"):
                            st.caption(f"📝 {ep['nota']}")
                else:
                    st.info("No hay pasos registrados para esta ejecución.")

    # ── TAB 7: Pedidos ──────────────────────────────────────
    with tab7:
        sb7 = get_supabase()
        st.markdown("### Pedidos")
        
        filtro_ped = st.selectbox("Filtrar:", ["Todos", "Pendientes", "Preparando", "Listos", "Entregados", "Cancelados"], key="filtro_ped")
        filtro_map = {"Todos": None, "Pendientes": "pendiente", "Preparando": "preparando", "Listos": "listo", "Entregados": "entregado", "Cancelados": "cancelado"}
        
        q = sb7.table("pedidos").select("*").order("creado_at", desc=True)
        if filtro_map[filtro_ped]:
            q = q.eq("estado", filtro_map[filtro_ped])
        pedidos = q.limit(100).execute().data or []
        
        if not pedidos:
            st.info("No hay pedidos con ese filtro.")
        else:
            for ped in pedidos:
                items_res = sb7.table("pedido_items").select("*").eq("pedido_id", ped["id"]).execute().data or []
                productos_str = ", ".join([f"{i['nombre_producto']} ×{i['cantidad']}" for i in items_res])
                
                estado = ped["estado"]
                color_map = {"pendiente": "🔴", "preparando": "🟡", "listo": "🟢", "entregado": "✅", "cancelado": "⚫"}
                icono = color_map.get(estado, "⚪")
                
                with st.expander(f"{icono} #{ped['id']} · {ped['nombre']} · €{ped['total']:.2f} · {ped['hora_recogida']} · {pd.Timestamp(ped['creado_at']).strftime('%d/%m %H:%M')}"):
                    c1, c2 = st.columns(2)
                    c1.markdown(f"**Nombre:** {ped['nombre']}")
                    c1.markdown(f"**Teléfono:** {ped['telefono']}")
                    c1.markdown(f"**Email:** {ped.get('email') or '—'}")
                    c1.markdown(f"**Recogida:** {ped['hora_recogida']}")
                    c2.markdown(f"**Total:** €{ped['total']:.2f}")
                    c2.markdown(f"**Estado:** {estado}")
                    c2.markdown(f"**Fecha:** {pd.Timestamp(ped['creado_at']).strftime('%d/%m/%Y %H:%M')}")
                    if ped.get("notas"):
                        st.markdown(f"**Notas:** {ped['notas']}")
                    st.markdown(f"**Productos:** {productos_str}")
                    
                    st.markdown("**Cambiar estado:**")
                    estados = ["pendiente", "preparando", "listo", "entregado", "cancelado"]
                    cols = st.columns(len(estados))
                    for i, est in enumerate(estados):
                        with cols[i]:
                            if est != estado:
                                if st.button(est.capitalize(), key=f"ped_{ped['id']}_{est}"):
                                    sb7.table("pedidos").update({"estado": est}).eq("id", ped["id"]).execute()
                                    st.success(f"✅ Pedido #{ped['id']} → {est}")
                                    st.rerun()
                            else:
                                st.markdown(f"<div style='text-align:center;padding:8px;background:var(--color-background-info);color:var(--color-text-info);border-radius:6px;font-size:13px;'>{est.capitalize()} ✓</div>", unsafe_allow_html=True)

    # ── TAB 8: Reservas ─────────────────────────────────────
    with tab8:
        sb8 = get_supabase()
        st.markdown("### Reservas")
        
        filtro_res = st.selectbox("Filtrar:", ["Todos", "Pendientes", "Confirmadas", "Canceladas"], key="filtro_res")
        filtro_res_map = {"Todos": None, "Pendientes": "pendiente", "Confirmadas": "confirmada", "Canceladas": "cancelada"}
        
        q2 = sb8.table("reservas").select("*").order("creado_at", desc=True)
        if filtro_res_map[filtro_res]:
            q2 = q2.eq("estado", filtro_res_map[filtro_res])
        reservas = q2.limit(100).execute().data or []
        
        if not reservas:
            st.info("No hay reservas con ese filtro.")
        else:
            for res in reservas:
                estado = res["estado"]
                color_map = {"pendiente": "🔴", "confirmada": "🟢", "cancelada": "⚫"}
                icono = color_map.get(estado, "⚪")
                
                with st.expander(f"{icono} #{res['id']} · {res['nombre']} · {res['personas']} pax · {res['fecha']} {res['hora']} · {pd.Timestamp(res['creado_at']).strftime('%d/%m %H:%M')}"):
                    c1, c2 = st.columns(2)
                    c1.markdown(f"**Nombre:** {res['nombre']}")
                    c1.markdown(f"**Teléfono:** {res['telefono']}")
                    c1.markdown(f"**Email:** {res.get('email') or '—'}")
                    c2.markdown(f"**Fecha:** {res['fecha']} a las {res['hora']}")
                    c2.markdown(f"**Personas:** {res['personas']}")
                    c2.markdown(f"**Estado:** {estado}")
                    if res.get("notas"):
                        st.markdown(f"**Notas:** {res['notas']}")
                    
                    st.markdown("**Cambiar estado:**")
                    rc1, rc2, rc3 = st.columns(3)
                    for col, est in zip([rc1, rc2, rc3], ["pendiente", "confirmada", "cancelada"]):
                        with col:
                            if est != estado:
                                if st.button(est.capitalize(), key=f"res_{res['id']}_{est}"):
                                    sb8.table("reservas").update({"estado": est}).eq("id", res["id"]).execute()
                                    st.success(f"✅ Reserva #{res['id']} → {est}")
                                    st.rerun()
                            else:
                                st.markdown(f"<div style='text-align:center;padding:8px;background:var(--color-background-info);color:var(--color-text-info);border-radius:6px;font-size:13px;'>{est.capitalize()} ✓</div>", unsafe_allow_html=True)

    # ── TAB 9: Web ──────────────────────────────────────────
    with tab9:
        sb9 = get_supabase()
        st.markdown("### Gestión de la web")

        web_tab1, web_tab2, web_tab3 = st.tabs(["⚙️ Configuración", "🍜 Menú", "📸 Categorías"])

        # ── CONFIG ──
        with web_tab1:
            st.markdown("#### Datos del local y horarios")
            cfg_res = sb9.table("config").select("*").execute()
            cfg = {r["clave"]: r["valor"] for r in (cfg_res.data or [])}

            st.markdown("**Información general**")
            c1, c2 = st.columns(2)
            new_cfg = {}
            new_cfg["nombre_local"] = c1.text_input("Nombre del local", value=cfg.get("nombre_local","Vietnamito"), key="cfg_nombre")
            new_cfg["direccion"] = c2.text_input("Dirección", value=cfg.get("direccion",""), key="cfg_dir")
            new_cfg["telefono"] = c1.text_input("Teléfono", value=cfg.get("telefono",""), key="cfg_tel")
            new_cfg["email_pedidos"] = c2.text_input("Email pedidos", value=cfg.get("email_pedidos",""), key="cfg_email")
            new_cfg["tiempo_espera_min"] = c1.text_input("Tiempo espera recogida (min)", value=cfg.get("tiempo_espera_min","15"), key="cfg_espera")
            new_cfg["mesas_total"] = c2.text_input("Nº máximo comensales", value=cfg.get("mesas_total","15"), key="cfg_mesas")
            new_cfg["barrio"] = c1.text_input("Barrio", value=cfg.get("barrio","Sants - Les Corts"), key="cfg_barrio")
            st.markdown("**Textos del hero (página de inicio)**")
            new_cfg["hero_titulo"] = st.text_input("Título hero (HTML permitido, ej: El mejor<br>Banh mi de<br><em>Barcelona</em>)", value=cfg.get("hero_titulo","El mejor<br>Banh mi de<br><em>Barcelona</em>"), key="cfg_hero_titulo")
            new_cfg["hero_subtitulo"] = st.text_input("Subtítulo hero", value=cfg.get("hero_subtitulo",""), placeholder="Ej: Comida vietnamita auténtica en el corazón de Barcelona", key="cfg_hero_sub")

            st.markdown("**Horarios**")
            dias_cfg = [("lunes","Lun"),("martes","Mar"),("miercoles","Mié"),("jueves","Jue"),("viernes","Vie"),("sabado","Sáb"),("domingo","Dom")]
            cols_h = st.columns(7)
            for (dia, label), col in zip(dias_cfg, cols_h):
                new_cfg[f"horario_{dia}"] = col.text_input(label, value=cfg.get(f"horario_{dia}",""), key=f"cfg_h_{dia}")

            st.markdown("**Activar / desactivar**")
            act1, act2 = st.columns(2)
            new_cfg["pedidos_activos"] = "true" if act1.checkbox("Pedidos activos", value=cfg.get("pedidos_activos","true")=="true", key="cfg_ped_act") else "false"
            new_cfg["reservas_activas"] = "true" if act2.checkbox("Reservas activas", value=cfg.get("reservas_activas","true")=="true", key="cfg_res_act") else "false"

            if st.button("💾 Guardar configuración", key="save_cfg", type="primary"):
                for clave, valor in new_cfg.items():
                    sb9.table("config").upsert({"clave": clave, "valor": valor}).execute()
                st.success("✅ Configuración guardada")
                st.rerun()

            st.divider()
            st.markdown("#### Fotos de la web")
            st.caption("Estas fotos aparecen en la página de inicio de vietnamito.es")

            fotos_config = [
                ("foto_hero", "Hero principal (fondo grande al entrar)"),
                ("foto_franja", "Franja intermedia (segunda foto)"),
                ("foto_split", "Sección 'Nuestro espacio' (tercera foto)"),
                ("foto_reserva", "Página de reservas (fondo lateral)"),
                ("foto_mural_banner", "Banner inferior (encima del footer)"),
            ]

            import urllib.parse as _ul
            for clave_foto, label_foto in fotos_config:
                st.markdown(f"**{label_foto}**")
                url_actual = cfg.get(clave_foto, "")
                fc1, fc2 = st.columns([3, 1])
                new_url = fc1.text_input("URL actual:", value=url_actual, key=f"furl_{clave_foto}")
                if url_actual:
                    fc2.image(url_actual, width=100)
                foto_upload = st.file_uploader(f"Subir nueva foto:", type=["jpg","jpeg","png","webp"], key=f"fup_{clave_foto}")
                if foto_upload:
                    try:
                        ext = foto_upload.name.split(".")[-1].lower()
                        fname = f"web/{clave_foto}.{ext}"
                        sb9.storage.from_("assets").upload(fname, foto_upload.read(), {"content-type": f"image/{ext}", "upsert": "true"})
                        new_url = f"{SUPABASE_URL}/storage/v1/object/public/assets/{_ul.quote(fname, safe='/')}"
                        sb9.table("config").upsert({"clave": clave_foto, "valor": new_url}).execute()
                        st.success(f"✅ Foto subida y guardada")
                        st.rerun()
                    except Exception as e:
                        st.warning(f"Error: {e}")
                elif new_url != url_actual:
                    if st.button(f"💾 Guardar URL", key=f"fsave_{clave_foto}"):
                        sb9.table("config").upsert({"clave": clave_foto, "valor": new_url}).execute()
                        st.success("✅ URL guardada")
                        st.rerun()
                st.markdown("")

        # ── MENÚ ──
        with web_tab2:
            cats_res = sb9.table("categorias").select("*").order("orden").execute()
            cats_web = cats_res.data or []
            prods_res = sb9.table("productos").select("*").order("orden").execute()
            prods_web = prods_res.data or []

            if not cats_web:
                st.info("No hay categorías. Créalas en la pestaña Categorías primero.")
            else:
                cat_sel_web = st.selectbox("Categoría:", [c["nombre"] for c in cats_web], key="cat_sel_web")
                cat_obj = next(c for c in cats_web if c["nombre"] == cat_sel_web)
                prods_cat_web = [p for p in prods_web if p["categoria_id"] == cat_obj["id"]]

                # Añadir producto
                with st.expander("➕ Añadir producto"):
                    if "prod_counter" not in st.session_state:
                        st.session_state.prod_counter = 0
                    pc = st.session_state.prod_counter
                    pa1, pa2 = st.columns([3,1])
                    new_prod_nom = pa1.text_input("Nombre:", key=f"pn_{pc}")
                    new_prod_precio = pa2.number_input("Precio €:", value=6.50, min_value=0.0, step=0.5, format="%.2f", key=f"pp_{pc}")
                    new_prod_desc = st.text_area("Descripción:", key=f"pd_{pc}", height=70)
                    new_prod_foto_url = st.text_input("URL foto (opcional):", key=f"pf_{pc}")
                    new_prod_foto_file = st.file_uploader("O sube foto:", type=["jpg","jpeg","png","webp"], key=f"pff_{pc}")
                    if new_prod_foto_file:
                        st.image(new_prod_foto_file, width=150)
                    new_prod_orden = st.number_input("Orden:", value=len(prods_cat_web)+1, min_value=1, key=f"po_{pc}")

                    if st.button("➕ Añadir producto", key=f"add_prod_{pc}"):
                        if new_prod_nom.strip():
                            foto_url = new_prod_foto_url.strip() or None
                            if new_prod_foto_file:
                                try:
                                    import urllib.parse
                                    ext = new_prod_foto_file.name.split(".")[-1].lower()
                                    fname = f"productos/{cat_obj['id']}_{new_prod_nom.strip().replace(' ','_')}.{ext}"
                                    sb9.storage.from_("assets").upload(fname, new_prod_foto_file.read(), {"content-type": f"image/{ext}", "upsert": "true"})
                                    foto_url = f"{SUPABASE_URL}/storage/v1/object/public/assets/{urllib.parse.quote(fname, safe='/')}"
                                except Exception as e:
                                    st.warning(f"No se pudo subir foto: {e}")
                            sb9.table("productos").insert({
                                "categoria_id": cat_obj["id"],
                                "nombre": new_prod_nom.strip(),
                                "descripcion": new_prod_desc.strip() or None,
                                "precio": float(new_prod_precio),
                                "foto_url": foto_url,
                                "orden": int(new_prod_orden),
                                "disponible": True
                            }).execute()
                            st.session_state.prod_counter += 1
                            st.success("✅ Producto añadido")
                            st.rerun()
                        else:
                            st.warning("Escribe un nombre.")

                # Editar productos existentes
                st.markdown(f"**{len(prods_cat_web)} productos en {cat_sel_web}:**")
                for prod in sorted(prods_cat_web, key=lambda p: p.get("orden",0)):
                    with st.expander(f"{'✅' if prod['disponible'] else '❌'} {prod['orden']}. {prod['nombre']} — €{prod['precio']:.2f}"):
                        ep1, ep2 = st.columns([3,1])
                        e_nom = ep1.text_input("Nombre:", value=prod["nombre"], key=f"en_{prod['id']}")
                        e_precio = ep2.number_input("€:", value=float(prod["precio"]), min_value=0.0, step=0.5, format="%.2f", key=f"epr_{prod['id']}")
                        e_desc = st.text_area("Descripción:", value=prod.get("descripcion") or "", key=f"ed_{prod['id']}", height=70)
                        e_orden = ep2.number_input("Orden:", value=int(prod.get("orden",0)), min_value=1, key=f"eord_{prod['id']}")
                        e_disp = ep1.checkbox("Disponible", value=prod.get("disponible",True), key=f"edis_{prod['id']}")
                        e_foto = st.text_input("URL foto:", value=prod.get("foto_url") or "", key=f"ef_{prod['id']}")
                        e_foto_file = st.file_uploader("Cambiar foto:", type=["jpg","jpeg","png","webp"], key=f"eff_{prod['id']}")
                        if e_foto_file:
                            st.image(e_foto_file, width=150)
                            try:
                                import urllib.parse
                                ext = e_foto_file.name.split(".")[-1].lower()
                                fname = f"productos/{prod['id']}.{ext}"
                                sb9.storage.from_("assets").upload(fname, e_foto_file.read(), {"content-type": f"image/{ext}", "upsert": "true"})
                                e_foto = f"{SUPABASE_URL}/storage/v1/object/public/assets/{urllib.parse.quote(fname, safe='/')}"
                                st.success("✅ Foto lista — pulsa Guardar")
                            except Exception as ex:
                                st.warning(f"Error foto: {ex}")
                        elif e_foto:
                            st.image(e_foto, width=150)

                        sc1, sc2 = st.columns(2)
                        if sc1.button("💾 Guardar", key=f"save_prod_{prod['id']}"):
                            sb9.table("productos").update({
                                "nombre": e_nom, "descripcion": e_desc or None,
                                "precio": float(e_precio), "foto_url": e_foto or None,
                                "orden": int(e_orden), "disponible": e_disp
                            }).eq("id", prod["id"]).execute()
                            st.success("✅ Guardado")
                            st.rerun()
                        if sc2.button("🗑️ Eliminar", key=f"del_prod_{prod['id']}"):
                            st.session_state[f"confirm_del_prod_{prod['id']}"] = True
                        if st.session_state.get(f"confirm_del_prod_{prod['id']}"):
                            st.warning(f"¿Eliminar '{prod['nombre']}'?")
                            dc1, dc2 = st.columns(2)
                            if dc1.button("✅ Sí", key=f"yes_prod_{prod['id']}"):
                                sb9.table("productos").delete().eq("id", prod["id"]).execute()
                                st.session_state.pop(f"confirm_del_prod_{prod['id']}", None)
                                st.success("✅ Eliminado")
                                st.rerun()
                            if dc2.button("❌ No", key=f"no_prod_{prod['id']}"):
                                st.session_state.pop(f"confirm_del_prod_{prod['id']}", None)
                                st.rerun()

        # ── CATEGORÍAS ──
        with web_tab3:
            st.markdown("#### Categorías del menú")

            with st.expander("➕ Nueva categoría"):
                nc1, nc2 = st.columns([3,1])
                new_cat_nom = nc1.text_input("Nombre:", key="new_cat_nom")
                new_cat_ord = nc2.number_input("Orden:", value=len(cats_web)+1, min_value=1, key="new_cat_ord")
                new_cat_desc = st.text_input("Descripción (opcional):", key="new_cat_desc")
                if st.button("➕ Añadir categoría", key="add_cat_web"):
                    if new_cat_nom.strip():
                        sb9.table("categorias").insert({
                            "nombre": new_cat_nom.strip(),
                            "descripcion": new_cat_desc.strip() or None,
                            "orden": int(new_cat_ord),
                            "activo": True
                        }).execute()
                        st.success(f"✅ Categoría '{new_cat_nom}' creada")
                        st.rerun()
                    else:
                        st.warning("Escribe un nombre.")

            for cat in cats_web:
                n_prods = len([p for p in prods_web if p["categoria_id"] == cat["id"]])
                with st.expander(f"{'✅' if cat['activo'] else '❌'} {cat['orden']}. {cat['nombre']} ({n_prods} productos)"):
                    cc1, cc2 = st.columns([3,1])
                    c_nom = cc1.text_input("Nombre:", value=cat["nombre"], key=f"cnom_{cat['id']}")
                    c_ord = cc2.number_input("Orden:", value=int(cat.get("orden",0)), min_value=1, key=f"cord_{cat['id']}")
                    c_desc = st.text_input("Descripción:", value=cat.get("descripcion") or "", key=f"cdesc_{cat['id']}")
                    c_act = st.checkbox("Activa", value=cat.get("activo",True), key=f"cact_{cat['id']}")
                    csc1, csc2 = st.columns(2)
                    if csc1.button("💾 Guardar", key=f"save_cat_{cat['id']}"):
                        sb9.table("categorias").update({
                            "nombre": c_nom, "descripcion": c_desc or None,
                            "orden": int(c_ord), "activo": c_act
                        }).eq("id", cat["id"]).execute()
                        st.success("✅ Categoría guardada")
                        st.rerun()
                    if csc2.button("🗑️ Eliminar", key=f"del_cat_{cat['id']}"):
                        st.session_state[f"confirm_del_cat_{cat['id']}"] = True
                    if st.session_state.get(f"confirm_del_cat_{cat['id']}"):
                        st.warning(f"¿Eliminar '{cat['nombre']}' y todos sus productos?")
                        dc1, dc2 = st.columns(2)
                        if dc1.button("✅ Sí", key=f"yes_cat_{cat['id']}"):
                            sb9.table("categorias").delete().eq("id", cat["id"]).execute()
                            st.session_state.pop(f"confirm_del_cat_{cat['id']}", None)
                            st.success("✅ Eliminada")
                            st.rerun()
                        if dc2.button("❌ No", key=f"no_cat_{cat['id']}"):
                            st.session_state.pop(f"confirm_del_cat_{cat['id']}", None)
                            st.rerun()

    st.divider()
    st.caption(f"Datos: {fecha_min.strftime('%d/%m/%Y')} → {fecha_max.strftime('%d/%m/%Y')} · {len(df)} franjas · Total €{total_ventas:,.2f} (IVA incl.)")

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
