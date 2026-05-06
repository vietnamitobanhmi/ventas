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

def calcular_coste_staff_por_hora(sb):
    """Devuelve dict {hora: coste_medio_por_hora} basado en turnos y coste/hora de empleados."""
    emp_res = sb.table("empleados").select("*").execute()
    empleados = {e["id"]: e["coste_hora"] for e in (emp_res.data or [])}
    turnos_res = sb.table("turnos").select("*").execute()
    # Cada slot = 30min. Agrupamos coste por hora (slot 09:00 y 09:30 -> hora 9)
    coste_por_hora = {}
    for tr in (turnos_res.data or []):
        slot = tr["slot"]  # "09:00"
        hora = int(slot.split(":")[0])
        if hora == 0 or hora == 1:  # madrugada -> hora 0/1 mapped as-is
            pass
        coste_slot = empleados.get(tr["empleado_id"], 10) * 0.5  # 30min = 0.5h
        coste_por_hora[hora] = coste_por_hora.get(hora, 0) + coste_slot
    # Esto es el coste total semanal por hora. Lo dividimos por 7 para tener promedio diario
    return {h: v / 7 for h, v in coste_por_hora.items()}

def calcular_por_semana(df):
    df2 = df.copy()
    df2["fecha_ts"] = pd.to_datetime(df2["fecha"])
    df2["lunes"] = df2["fecha_ts"] - pd.to_timedelta(df2["fecha_ts"].dt.weekday, unit="d")
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

    # ── Gráfica de rentabilidad por franja ──
    if turnos_data and empleados_data:
        emp_coste = {e["id"]: e["coste_hora"] for e in empleados_data}
        # Calcular coste de personal por hora (slot = 30min = 0.5h)
        # Si hay filtro de día, usar solo los turnos de ese día
        coste_hora = {}
        for tr in turnos_data:
            dow_tr = tr["dia_semana"]
            if dow_filter is not None and dow_tr != dow_filter:
                continue
            slot = tr["slot"]
            h = int(slot.split(":")[0])
            coste_slot = emp_coste.get(tr["empleado_id"], 10) * 0.5
            coste_hora[h] = coste_hora.get(h, 0) + coste_slot

        # Si filtramos por día, ya tenemos el coste de ese día
        # Si es "todos los días", promediamos el coste entre los 7 días
        if dow_filter is None and coste_hora:
            # Promedio de coste por hora entre todos los días configurados
            dias_con_turnos = len(set(tr["dia_semana"] for tr in turnos_data))
            if dias_con_turnos > 0:
                coste_hora = {h: v / dias_con_turnos for h, v in coste_hora.items()}

        # Ventas promedio por hora del filtro actual
        avg_ventas = dia_hora.groupby("hora")["valor"].mean()

        horas_comunes = sorted(set(list(avg_ventas.index)) | set(coste_hora.keys()))
        ventas_vals = [avg_ventas.get(h, 0) for h in horas_comunes]
        coste_vals = [coste_hora.get(h, 0) for h in horas_comunes]
        margen_vals = [v - c for v, c in zip(ventas_vals, coste_vals)]
        margen_colors = ["#5DCAA5" if m >= 0 else "#E63946" for m in margen_vals]
        horas_labels = [f"{h}:00" for h in horas_comunes]

        fig_rent = go.Figure()
        fig_rent.add_trace(go.Bar(
            x=horas_labels, y=ventas_vals, name="Ventas promedio",
            marker_color="rgba(93,202,165,0.5)", marker_line_width=0,
        ))
        fig_rent.add_trace(go.Bar(
            x=horas_labels, y=coste_vals, name="Coste personal",
            marker_color="rgba(230,57,70,0.5)", marker_line_width=0,
        ))
        fig_rent.add_trace(go.Scatter(
            x=horas_labels, y=margen_vals, name="Margen",
            mode="lines+markers+text",
            line=dict(color="#F4A261", width=2),
            marker=dict(size=7, color=margen_colors),
            text=[f"€{m:+.0f}" for m in margen_vals],
            textposition="top center", textfont=dict(size=10),
        ))
        fig_rent.add_hline(y=0, line_dash="dot", line_color="rgba(128,128,128,0.5)")
        fig_rent.update_layout(
            title="Ventas promedio vs coste de personal por franja horaria",
            yaxis_title="€", xaxis_title="Hora",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(gridcolor="rgba(128,128,128,0.15)", zeroline=False),
            xaxis=dict(showgrid=False),
            barmode="overlay",
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="left", x=0),
            height=380, margin=dict(t=50, b=80),
        )
        st.plotly_chart(fig_rent, use_container_width=True)
        st.caption("Margen = ventas promedio − coste de personal en esa franja. Verde = rentable, rojo = coste supera ventas.")

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

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📅 Por día de semana",
        "🕐 Por franja horaria",
        "🌡️ Mapa de calor",
        "📈 Por semana",
        "👥 Turnos"
    ])

    # ── TAB 1: Por día de semana ──────────────────────────────
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

    # ── TAB 2: Por franja horaria (con selector de día) ───────
    with tab2:
        opciones = ["Todos los días"] + [DIAS[d] for d in DIAS_ORDER]
        seleccion = st.selectbox("Filtrar por día de la semana:", opciones, key="sel_franja")

        df_f = df.copy()
        df_f["fecha_ts"] = pd.to_datetime(df_f["fecha"])
        df_f["dow_label"] = df_f["fecha_ts"].dt.weekday.map(DIAS)

        if seleccion != "Todos los días":
            df_f = df_f[df_f["dow_label"] == seleccion]

        if df_f.empty:
            st.warning("No hay datos para ese día.")
        else:
            n_inst = df_f["fecha"].nunique()
            titulo_sel = seleccion if seleccion != "Todos los días" else "todos los días"
            st.caption(f"{n_inst} instancias de {titulo_sel} con datos")
            color = "#5DCAA5" if seleccion == "Todos los días" else COLORS[DIAS_ORDER[[DIAS[d] for d in DIAS_ORDER].index(seleccion)] if seleccion in [DIAS[d] for d in DIAS_ORDER] else 0]
            # Escala fija basada en el máximo global
            df_global = df.copy()
            df_global["fecha_ts"] = pd.to_datetime(df_global["fecha"])
            dia_hora_global = df_global.groupby(["fecha", "hora"])["valor"].sum()
            ymax_global = dia_hora_global.max() * 1.15
            # Cargar turnos y empleados para rentabilidad
            sb_t2 = get_supabase()
            turnos_t2 = sb_t2.table("turnos").select("*").execute().data or []
            empleados_t2 = sb_t2.table("empleados").select("*").execute().data or []
            dow_filter_t2 = None
            if seleccion != "Todos los días":
                dow_filter_t2 = [d for d in DIAS_ORDER if DIAS[d] == seleccion][0]
            boxplot_horario(df_f, f"Distribución de ventas por franja horaria — {titulo_sel} (€, IVA incl.)",
                ymax=ymax_global, turnos_data=turnos_t2, empleados_data=empleados_t2, dow_filter=dow_filter_t2)

    # ── TAB 3: Mapa de calor ──────────────────────────────────
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

    # ── TAB 4: Por semana ─────────────────────────────────────
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

            # Evolución promedio por franja horaria trabajada
            df2 = df.copy()
            df2["fecha_ts"] = pd.to_datetime(df2["fecha"])
            df2["lunes"] = df2["fecha_ts"] - pd.to_timedelta(df2["fecha_ts"].dt.weekday, unit="d")
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

    # ── TAB 5: Turnos ─────────────────────────────────────────
    with tab5:
        import datetime as dt_mod
        sb = get_supabase()

        emp_res = sb.table("empleados").select("*").order("id").execute()
        empleados = emp_res.data if emp_res.data else []

        st.markdown("### Empleados")
        st.caption("Edita nombres y coste/hora y pulsa 💾 para guardar.")

        header = st.columns([3, 2, 1])
        header[0].markdown("**Nombre**")
        header[1].markdown("**€/hora**")
        header[2].markdown("**Guardar**")

        for emp in empleados:
            c1, c2, c3 = st.columns([3, 2, 1])
            nuevo_nombre = c1.text_input("n", value=emp["nombre"], label_visibility="collapsed", key=f"nom_{emp['id']}")
            nuevo_coste = c2.number_input("c", value=float(emp["coste_hora"]), min_value=0.0, step=0.5, format="%.2f", label_visibility="collapsed", key=f"cos_{emp['id']}")
            if c3.button("💾", key=f"saveemp_{emp['id']}"):
                sb.table("empleados").update({"nombre": nuevo_nombre, "coste_hora": nuevo_coste}).eq("id", emp["id"]).execute()
                st.success(f"✅ {nuevo_nombre} guardado")
                st.rerun()

        st.divider()
        st.markdown("### Turnos por día")

        slots = []
        current = dt_mod.datetime(2000, 1, 1, 7, 0)
        end = dt_mod.datetime(2000, 1, 2, 1, 30)
        while current < end:
            slots.append(current.strftime("%H:%M"))
            current += dt_mod.timedelta(minutes=30)

        turnos_res = sb.table("turnos").select("*").execute()
        turnos_set = set()
        for tr in (turnos_res.data or []):
            turnos_set.add((tr["empleado_id"], tr["dia_semana"], tr["slot"]))

        emp_ids = [e["id"] for e in empleados]
        emp_nombres = {e["id"]: e["nombre"] for e in empleados}
        emp_coste = {e["id"]: e["coste_hora"] for e in empleados}

        dias_tabs = st.tabs([DIAS[d] for d in DIAS_ORDER])

        for di, dow in enumerate(DIAS_ORDER):
            with dias_tabs[di]:
                ncols = len(empleados)
                hdr = st.columns([1] + [2] * ncols)
                hdr[0].markdown("**Hora**")
                for ei, eid in enumerate(emp_ids):
                    hdr[ei+1].markdown(f"**{emp_nombres.get(eid, f'Emp {eid}')}**")

                new_state = {}
                for slot in slots:
                    row = st.columns([1] + [2] * ncols)
                    row[0].markdown(f"`{slot}`")
                    for ei, eid in enumerate(emp_ids):
                        checked = row[ei+1].checkbox(
                            " ", value=(eid, dow, slot) in turnos_set,
                            key=f"t_{dow}_{slot}_{eid}", label_visibility="collapsed"
                        )
                        new_state.setdefault(slot, {})[eid] = checked

                if st.button(f"💾 Guardar turnos {DIAS[dow]}", key=f"saveturno_{dow}"):
                    sb.table("turnos").delete().eq("dia_semana", dow).execute()
                    to_insert = [
                        {"empleado_id": eid, "dia_semana": dow, "slot": slot}
                        for slot, emp_checks in new_state.items()
                        for eid, checked in emp_checks.items() if checked
                    ]
                    if to_insert:
                        sb.table("turnos").insert(to_insert).execute()
                    st.success(f"✅ Turnos del {DIAS[dow]} guardados")
                    st.rerun()

                horas_dia = {}
                for slot, emp_checks in new_state.items():
                    for eid, checked in emp_checks.items():
                        if checked:
                            horas_dia[eid] = horas_dia.get(eid, 0) + 0.5

                if any(horas_dia.values()):
                    st.markdown("**Resumen del día:**")
                    res_cols = st.columns(ncols)
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
