import streamlit as st
from supabase import create_client
from datetime import datetime

st.set_page_config(
    page_title="VietnamitApp",
    page_icon="✅",
    layout="centered"
)

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; max-width: 600px; }
    h1 { font-size: 1.6rem; font-weight: 700; }
    h2 { font-size: 1.2rem; font-weight: 600; }
    .paso-card {
        background: #1e2130;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .paso-num {
        font-size: 0.8rem;
        color: #888;
        margin-bottom: 0.3rem;
    }
    .paso-titulo {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .paso-desc {
        font-size: 0.95rem;
        color: #ccc;
        line-height: 1.5;
    }
    div[data-testid="stButton"] button {
        width: 100%;
        font-size: 1rem;
        padding: 0.6rem;
        border-radius: 8px;
    }
    .logo-container {
        display: flex;
        justify-content: center;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="logo-container"><img src="https://rwtpjqvgiiuvniixqapu.supabase.co/storage/v1/object/public/assets/Logo%20Vietnamito%20Final.png" style="width:180px;background:black;border-radius:12px;padding:12px;"></div>', unsafe_allow_html=True)

LOGO_URL = "https://rwtpjqvgiiuvniixqapu.supabase.co/storage/v1/object/public/assets/Logo%20Vietnamito%20Final.png"

SUPABASE_URL = "https://rwtpjqvgiiuvniixqapu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ3dHBqcXZnaWl1dm5paXhxYXB1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzcxMzIyMjMsImV4cCI6MjA5MjcwODIyM30.jznrwuusfgtVkrzz_bfdsxq3tVsv-uV2tyMeIlh3bZg"

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def init_state():
    for key in ["empleado_id", "empleado_nombre", "proceso_id", "proceso_nombre",
                "pasos", "paso_actual", "ejecucion_id", "no_puedo_activo"]:
        if key not in st.session_state:
            st.session_state[key] = None
    if "paso_actual" not in st.session_state or st.session_state.paso_actual is None:
        st.session_state.paso_actual = 0
    if "no_puedo_activo" not in st.session_state:
        st.session_state.no_puedo_activo = False

def reset():
    for key in ["empleado_id", "empleado_nombre", "proceso_id", "proceso_nombre",
                "pasos", "paso_actual", "ejecucion_id", "no_puedo_activo"]:
        st.session_state[key] = None
    st.session_state.paso_actual = 0
    st.session_state.no_puedo_activo = False

init_state()
sb = get_supabase()

# ── PANTALLA 1: Selección de empleado ────────────────────────
if st.session_state.empleado_id is None:
    st.title("🍜 VietnamitApp")
    st.markdown("### ¿Quién eres?")

    emp_res = sb.table("empleados").select("*").order("nombre").execute()
    empleados = emp_res.data or []

    if not empleados:
        st.warning("No hay empleados configurados. Contacta con el administrador.")
        st.stop()

    for emp in empleados:
        if st.button(emp["nombre"], key=f"emp_{emp['id']}", use_container_width=True):
            st.session_state.empleado_id = emp["id"]
            st.session_state.empleado_nombre = emp["nombre"]
            st.rerun()
    st.stop()

# ── PANTALLA 2: Selección de proceso ─────────────────────────
if st.session_state.proceso_id is None:
    st.title(f"Hola, {st.session_state.empleado_nombre} 👋")
    st.markdown("### ¿Qué vas a hacer?")

    proc_res = sb.table("procesos").select("*").eq("activo", True).order("orden").execute()
    procesos = proc_res.data or []

    if not procesos:
        st.warning("No hay procesos configurados. Contacta con el administrador.")
    else:
        for proc in procesos:
            if st.button(f"**{proc['nombre']}**" + (f"\n{proc['descripcion']}" if proc.get('descripcion') else ""),
                        key=f"proc_{proc['id']}", use_container_width=True):
                # Cargar pasos
                pasos_res = sb.table("pasos").select("*").eq("proceso_id", proc["id"]).order("orden").execute()
                pasos = pasos_res.data or []
                if not pasos:
                    st.warning("Este proceso no tiene pasos configurados.")
                else:
                    st.session_state.proceso_id = proc["id"]
                    st.session_state.proceso_nombre = proc["nombre"]
                    st.session_state.pasos = pasos
                    st.session_state.paso_actual = 0
                    # Crear ejecución
                    ejec = sb.table("ejecuciones").insert({
                        "empleado_id": st.session_state.empleado_id,
                        "proceso_id": proc["id"],
                    }).execute()
                    st.session_state.ejecucion_id = ejec.data[0]["id"]
                    st.rerun()

    st.markdown("---")
    if st.button("← Cambiar empleado", key="back_emp"):
        reset()
        st.rerun()
    st.stop()

# ── PANTALLA 3: Pasos ─────────────────────────────────────────
pasos = st.session_state.pasos or []
paso_actual = st.session_state.paso_actual or 0

# Completado
if paso_actual >= len(pasos):
    # Marcar ejecución como completada
    sb.table("ejecuciones").update({
        "completado": True,
        "completado_at": datetime.utcnow().isoformat()
    }).eq("id", st.session_state.ejecucion_id).execute()

    st.balloons()
    st.title("✅ ¡Todo listo!")
    st.markdown(f"**{st.session_state.proceso_nombre}** completado por **{st.session_state.empleado_nombre}**.")
    st.markdown(f"*{datetime.now().strftime('%d/%m/%Y %H:%M')}*")
    st.markdown("---")
    if st.button("🔄 Hacer otro proceso", use_container_width=True):
        st.session_state.proceso_id = None
        st.session_state.proceso_nombre = None
        st.session_state.pasos = None
        st.session_state.paso_actual = 0
        st.session_state.ejecucion_id = None
        st.session_state.no_puedo_activo = False
        st.rerun()
    if st.button("👋 Salir", use_container_width=True):
        reset()
        st.rerun()
    st.stop()

paso = pasos[paso_actual]
n_total = len(pasos)

# Barra de progreso
st.progress((paso_actual) / n_total)
st.caption(f"Paso {paso_actual + 1} de {n_total} · {st.session_state.proceso_nombre} · {st.session_state.empleado_nombre}")

# Tarjeta del paso
st.markdown(f'<div class="paso-num">Paso {paso_actual + 1}</div>', unsafe_allow_html=True)
st.markdown(f"## {paso['titulo']}")

if paso.get("descripcion"):
    desc = paso["descripcion"]
    # Separar líneas normales de líneas (check)
    lineas = desc.split("\n")
    for i, linea in enumerate(lineas):
        if "(check)" in linea.lower():
            texto_check = linea.replace("(check)", "").replace("(Check)", "").replace("(CHECK)", "").strip()
            checks_pendientes[f"check_{paso['id']}_{i}"] = texto_check
        else:
            if linea.strip():
                st.markdown(linea)
            else:
                st.markdown("")

    if checks_pendientes:
        st.markdown("**Verifica cada punto:**")
        for key, texto in checks_pendientes.items():
            st.checkbox(texto, key=key)

if paso.get("foto_url"):
    st.image(paso["foto_url"], use_container_width=True)

st.markdown("---")

# Botones
if not st.session_state.no_puedo_activo:
    col1, col2 = st.columns([3, 1])
    if col1.button("✅ Hecho", key="btn_hecho", type="primary", use_container_width=True):
        sb.table("ejecucion_pasos").insert({
            "ejecucion_id": st.session_state.ejecucion_id,
            "paso_id": paso["id"],
            "estado": "hecho",
        }).execute()
        st.session_state.paso_actual += 1
        st.session_state.no_puedo_activo = False
        st.rerun()

    if col2.button("⚠️ No puedo", key="btn_nopuedo", use_container_width=True):
        st.session_state.no_puedo_activo = True
        st.rerun()
else:
    st.warning("¿Por qué no puedes completar este paso?")
    nota = st.text_area("Explica el motivo:", key="nota_nopuedo", placeholder="Describe el problema...")
    col1, col2 = st.columns(2)
    if col1.button("📝 Confirmar y continuar", key="btn_confirmar_nopuedo", type="primary", use_container_width=True):
        sb.table("ejecucion_pasos").insert({
            "ejecucion_id": st.session_state.ejecucion_id,
            "paso_id": paso["id"],
            "estado": "no_puedo",
            "nota": nota or "(sin nota)",
        }).execute()
        st.session_state.paso_actual += 1
        st.session_state.no_puedo_activo = False
        st.rerun()
    if col2.button("← Cancelar", key="btn_cancel_nopuedo", use_container_width=True):
        st.session_state.no_puedo_activo = False
        st.rerun()
