import streamlit as st
from supabase import create_client
from datetime import datetime, date, timedelta
import re

st.set_page_config(
    page_title="Vietnamito — Banh mi & Café",
    page_icon="🍜",
    layout="wide",
    initial_sidebar_state="collapsed"
)

SUPABASE_URL = "https://rwtpjqvgiiuvniixqapu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ3dHBqcXZnaWl1dm5paXhxYXB1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzcxMzIyMjMsImV4cCI6MjA5MjcwODIyM30.jznrwuusfgtVkrzz_bfdsxq3tVsv-uV2tyMeIlh3bZg"
LOGO_URL = "https://rwtpjqvgiiuvniixqapu.supabase.co/storage/v1/object/public/assets/Logo%20Vietnamito%20Final.png"

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=300)
def get_config():
    sb = get_supabase()
    rows = sb.table("config").select("*").execute().data or []
    return {r["clave"]: r["valor"] for r in rows}

@st.cache_data(ttl=60)
def get_categorias():
    sb = get_supabase()
    return sb.table("categorias").select("*").eq("activo", True).order("orden").execute().data or []

@st.cache_data(ttl=60)
def get_productos():
    sb = get_supabase()
    return sb.table("productos").select("*").eq("disponible", True).order("orden").execute().data or []

def get_slots_recogida(config):
    try:
        espera = int(config.get("tiempo_espera_min", "15"))
    except:
        espera = 15
    ahora = datetime.now()
    inicio = ahora + timedelta(minutes=espera + 5)
    inicio = inicio.replace(second=0, microsecond=0)
    # Round up to next 15 min
    mins = (inicio.minute // 15 + 1) * 15
    inicio = inicio.replace(minute=0) + timedelta(minutes=mins)
    slots = []
    for i in range(12):
        t = inicio + timedelta(minutes=15 * i)
        if t.hour < 22:
            slots.append(t.strftime("%H:%M"))
    return slots

# ── CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding: 0 !important; max-width: 100% !important; }
    header { display: none !important; }
    .stApp { background: #0e0e0e; }

    .viet-nav {
        display: flex; align-items: center; justify-content: space-between;
        padding: 12px 32px; background: #111; border-bottom: 1px solid #222;
        position: sticky; top: 0; z-index: 100;
    }
    .viet-nav-logo { display: flex; align-items: center; gap: 12px; }
    .viet-nav-logo img { height: 40px; }
    .viet-nav-links { display: flex; gap: 24px; }
    .viet-nav-links a {
        color: #aaa; text-decoration: none; font-size: 14px;
        cursor: pointer; transition: color 0.2s;
    }
    .viet-nav-links a:hover, .viet-nav-links a.active { color: #D85A30; }

    .viet-hero {
        background: linear-gradient(135deg, #1a0800 0%, #2d1500 100%);
        padding: 64px 32px; text-align: center;
    }
    .viet-hero h1 { font-size: 42px; font-weight: 500; color: #fff; margin-bottom: 12px; }
    .viet-hero p { font-size: 16px; color: rgba(255,255,255,0.6); margin-bottom: 28px; }
    .viet-hero-info { display: flex; justify-content: center; gap: 32px; margin-top: 28px; flex-wrap: wrap; }
    .viet-hero-info span { font-size: 13px; color: rgba(255,255,255,0.5); }

    .viet-btn-primary {
        background: #D85A30; color: #fff; border: none;
        padding: 12px 28px; border-radius: 8px; font-size: 15px;
        font-weight: 500; cursor: pointer; margin: 4px;
        display: inline-block;
    }
    .viet-btn-outline {
        background: transparent; color: #fff;
        border: 1px solid rgba(255,255,255,0.3);
        padding: 12px 28px; border-radius: 8px; font-size: 15px;
        cursor: pointer; margin: 4px; display: inline-block;
    }

    .viet-section { padding: 40px 32px; }
    .viet-section-title { font-size: 22px; font-weight: 500; color: #fff; margin-bottom: 24px; }

    .viet-cat-tabs { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 24px; }
    .viet-cat-tab {
        padding: 7px 16px; border-radius: 20px; font-size: 13px;
        cursor: pointer; border: 1px solid #333; color: #aaa; background: transparent;
    }
    .viet-cat-tab.active { background: #D85A30; color: #fff; border-color: #D85A30; }

    .viet-products { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
    .viet-product-card {
        background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 12px;
        overflow: hidden; transition: border-color 0.2s;
    }
    .viet-product-card:hover { border-color: #D85A30; }
    .viet-product-img { width: 100%; height: 160px; object-fit: cover; background: #222; display: flex; align-items: center; justify-content: center; font-size: 40px; }
    .viet-product-body { padding: 14px; }
    .viet-product-name { font-size: 15px; font-weight: 500; color: #fff; margin-bottom: 4px; }
    .viet-product-desc { font-size: 12px; color: #888; line-height: 1.5; margin-bottom: 12px; }
    .viet-product-bottom { display: flex; align-items: center; justify-content: space-between; }
    .viet-product-price { font-size: 17px; font-weight: 500; color: #D85A30; }

    .viet-cart-float {
        position: fixed; bottom: 24px; right: 24px; z-index: 200;
        background: #D85A30; color: #fff; border: none; border-radius: 12px;
        padding: 14px 24px; font-size: 15px; font-weight: 500; cursor: pointer;
        box-shadow: 0 4px 20px rgba(216,90,48,0.4);
    }

    .viet-form-section {
        max-width: 760px; margin: 0 auto; padding: 40px 32px;
    }
    .viet-form-title { font-size: 22px; font-weight: 500; color: #fff; margin-bottom: 8px; }
    .viet-form-subtitle { font-size: 14px; color: #888; margin-bottom: 28px; }

    .viet-cart-item {
        display: flex; align-items: center; gap: 12px;
        padding: 12px 0; border-bottom: 1px solid #222;
    }
    .viet-cart-item-name { flex: 1; font-size: 14px; color: #fff; }
    .viet-cart-item-price { font-size: 14px; color: #D85A30; min-width: 50px; text-align: right; }

    .viet-total { display: flex; justify-content: space-between; padding: 16px 0 0;
        font-size: 18px; font-weight: 500; color: #fff; }

    .viet-hora-chips { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }
    .viet-hora-chip {
        padding: 6px 14px; border-radius: 20px; font-size: 13px;
        cursor: pointer; border: 1px solid #333; color: #aaa; background: transparent;
    }
    .viet-hora-chip.selected { background: #D85A30; color: #fff; border-color: #D85A30; }

    .viet-success {
        text-align: center; padding: 60px 32px;
    }
    .viet-success-icon { font-size: 64px; margin-bottom: 16px; }
    .viet-success h2 { font-size: 24px; font-weight: 500; color: #fff; margin-bottom: 8px; }
    .viet-success p { font-size: 15px; color: #888; }

    .viet-footer { background: #111; border-top: 1px solid #222; padding: 32px; text-align: center; }
    .viet-footer p { font-size: 13px; color: #555; }

    div[data-testid="stButton"] button {
        background: #D85A30 !important; color: #fff !important;
        border: none !important; border-radius: 8px !important;
        font-size: 14px !important; font-weight: 500 !important;
        width: 100% !important; padding: 12px !important;
    }
    div[data-testid="stButton"] button:hover { background: #c04d25 !important; }
</style>
""", unsafe_allow_html=True)

# ── State ─────────────────────────────────────────────────────
if "pagina" not in st.session_state:
    st.session_state.pagina = "inicio"
if "carrito" not in st.session_state:
    st.session_state.carrito = {}  # producto_id -> {nombre, precio, cantidad}
if "cat_sel" not in st.session_state:
    st.session_state.cat_sel = None
if "hora_sel" not in st.session_state:
    st.session_state.hora_sel = "Lo antes posible"
if "pedido_ok" not in st.session_state:
    st.session_state.pedido_ok = None
if "reserva_ok" not in st.session_state:
    st.session_state.reserva_ok = False

config = get_config()
categorias = get_categorias()
productos = get_productos()

n_carrito = sum(v["cantidad"] for v in st.session_state.carrito.values())
total_carrito = sum(v["precio"] * v["cantidad"] for v in st.session_state.carrito.values())

# ── NAV ──────────────────────────────────────────────────────
horario_hoy = config.get(f"horario_{['lunes','martes','miercoles','jueves','viernes','sabado','domingo'][datetime.now().weekday()]}", "")

st.markdown(f"""
<div class="viet-nav">
  <div class="viet-nav-logo">
    <img src="{LOGO_URL}" alt="Vietnamito" style="height:40px;background:#000;border-radius:6px;padding:3px;">
    <span style="color:#fff;font-size:16px;font-weight:500;">{config.get('nombre_local','Vietnamito')}</span>
  </div>
  <div class="viet-nav-links">
    <a class="{'active' if st.session_state.pagina=='inicio' else ''}" onclick="">Inicio</a>
    <a class="{'active' if st.session_state.pagina=='menu' else ''}">Menú</a>
    <a class="{'active' if st.session_state.pagina=='pedido' else ''}">Pedir</a>
    <a class="{'active' if st.session_state.pagina=='reserva' else ''}">Reservar</a>
  </div>
  <span style="color:#aaa;font-size:13px;">Hoy: {horario_hoy}</span>
</div>
""", unsafe_allow_html=True)

# Nav buttons (hidden but functional)
nav_cols = st.columns(4)
if nav_cols[0].button("Inicio", key="nav_inicio"):
    st.session_state.pagina = "inicio"
    st.rerun()
if nav_cols[1].button("Menú", key="nav_menu"):
    st.session_state.pagina = "menu"
    st.rerun()
if nav_cols[2].button("Pedir", key="nav_pedido"):
    st.session_state.pagina = "pedido"
    st.rerun()
if nav_cols[3].button("Reservar", key="nav_reserva"):
    st.session_state.pagina = "reserva"
    st.rerun()

st.markdown('<style>div[data-testid="stHorizontalBlock"] { display: none !important; }</style>', unsafe_allow_html=True)

# ── PÁGINA: INICIO ────────────────────────────────────────────
if st.session_state.pagina == "inicio":
    st.markdown(f"""
    <div class="viet-hero">
      <h1>🍜 {config.get('nombre_local','Vietnamito')}</h1>
      <p>Banh mi & café vietnamita · {config.get('direccion','')}</p>
      <div>
        <span class="viet-btn-primary" onclick="">Pedir para recoger</span>
        <span class="viet-btn-outline" onclick="">Reservar mesa</span>
      </div>
      <div class="viet-hero-info">
        <span>📍 {config.get('direccion','')}</span>
        <span>📞 {config.get('telefono','')}</span>
        <span>🕐 Hoy: {horario_hoy}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("")
        if st.button("🛵 Pedir para recoger", key="hero_pedido", use_container_width=True):
            st.session_state.pagina = "menu"
            st.rerun()
    with col2:
        st.markdown("")
        if st.button("🍽️ Reservar mesa", key="hero_reserva", use_container_width=True):
            st.session_state.pagina = "reserva"
            st.rerun()

    # Horarios
    st.markdown("""
    <div class="viet-section">
      <p class="viet-section-title">Horario</p>
    </div>
    """, unsafe_allow_html=True)

    dias = ["lunes","martes","miercoles","jueves","viernes","sabado","domingo"]
    dias_label = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
    hoy_idx = datetime.now().weekday()
    cols = st.columns(7)
    for i, (dia, label) in enumerate(zip(dias, dias_label)):
        horario = config.get(f"horario_{dia}", "—")
        es_hoy = i == hoy_idx
        with cols[i]:
            st.markdown(f"""
            <div style="text-align:center;padding:12px 8px;background:{'#2d1500' if es_hoy else '#1a1a1a'};border-radius:10px;border:1px solid {'#D85A30' if es_hoy else '#2a2a2a'};">
              <p style="font-size:12px;color:{'#D85A30' if es_hoy else '#888'};margin:0;font-weight:{'500' if es_hoy else '400'};">{label}</p>
              <p style="font-size:12px;color:#fff;margin:4px 0 0;">{horario}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="viet-footer">
      <p>{config.get('nombre_local','Vietnamito')} · {config.get('direccion','')} · {config.get('telefono','')}</p>
    </div>
    """, unsafe_allow_html=True)

# ── PÁGINA: MENÚ ──────────────────────────────────────────────
elif st.session_state.pagina == "menu":
    if st.session_state.cat_sel is None and categorias:
        st.session_state.cat_sel = categorias[0]["id"]

    st.markdown('<div class="viet-section">', unsafe_allow_html=True)
    st.markdown('<p class="viet-section-title">Menú</p>', unsafe_allow_html=True)

    # Tabs de categorías
    cat_cols = st.columns(len(categorias))
    for i, cat in enumerate(categorias):
        with cat_cols[i]:
            active = st.session_state.cat_sel == cat["id"]
            if st.button(cat["nombre"], key=f"cat_{cat['id']}", use_container_width=True):
                st.session_state.cat_sel = cat["id"]
                st.rerun()

    # Productos de la categoría seleccionada
    prods_cat = [p for p in productos if p["categoria_id"] == st.session_state.cat_sel]

    if not prods_cat:
        st.markdown('<p style="color:#888;text-align:center;padding:40px;">No hay productos en esta categoría.</p>', unsafe_allow_html=True)
    else:
        cols = st.columns(3)
        for i, prod in enumerate(prods_cat):
            with cols[i % 3]:
                foto = prod.get("foto_url")
                if foto:
                    st.markdown(f'<div class="viet-product-card">', unsafe_allow_html=True)
                    st.image(foto, use_container_width=True)
                else:
                    st.markdown(f'<div class="viet-product-card"><div class="viet-product-img">🍜</div>', unsafe_allow_html=True)

                st.markdown(f"""
                <div class="viet-product-body">
                  <p class="viet-product-name">{prod['nombre']}</p>
                  <p class="viet-product-desc">{prod.get('descripcion','')}</p>
                  <div class="viet-product-bottom">
                    <span class="viet-product-price">€{prod['precio']:.2f}</span>
                  </div>
                </div></div>
                """, unsafe_allow_html=True)

                pid = prod["id"]
                qty = st.session_state.carrito.get(pid, {}).get("cantidad", 0)
                if qty == 0:
                    if st.button(f"Añadir al carrito", key=f"add_{pid}", use_container_width=True):
                        st.session_state.carrito[pid] = {
                            "nombre": prod["nombre"],
                            "precio": prod["precio"],
                            "cantidad": 1
                        }
                        st.rerun()
                else:
                    c1, c2, c3 = st.columns([1, 2, 1])
                    if c1.button("−", key=f"minus_{pid}"):
                        if st.session_state.carrito[pid]["cantidad"] > 1:
                            st.session_state.carrito[pid]["cantidad"] -= 1
                        else:
                            del st.session_state.carrito[pid]
                        st.rerun()
                    c2.markdown(f'<p style="text-align:center;color:#D85A30;font-size:16px;font-weight:500;margin:8px 0;">{qty}</p>', unsafe_allow_html=True)
                    if c3.button("+", key=f"plus_{pid}"):
                        st.session_state.carrito[pid]["cantidad"] += 1
                        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    if n_carrito > 0:
        st.markdown(f'<div class="viet-cart-float">🛒 {n_carrito} producto{"s" if n_carrito > 1 else ""} · €{total_carrito:.2f} → Ver pedido</div>', unsafe_allow_html=True)
        if st.button(f"🛒 Ver pedido ({n_carrito}) · €{total_carrito:.2f}", key="go_pedido", use_container_width=True):
            st.session_state.pagina = "pedido"
            st.rerun()

# ── PÁGINA: PEDIDO ────────────────────────────────────────────
elif st.session_state.pagina == "pedido":
    if st.session_state.pedido_ok:
        num = st.session_state.pedido_ok
        st.markdown(f"""
        <div class="viet-success">
          <div class="viet-success-icon">✅</div>
          <h2>¡Pedido confirmado!</h2>
          <p>Tu pedido #{num} está siendo preparado.<br>
          Te avisaremos cuando esté listo.<br><br>
          <strong style="color:#D85A30;">Hora de recogida: {st.session_state.hora_sel}</strong></p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Hacer otro pedido", key="otro_pedido"):
            st.session_state.carrito = {}
            st.session_state.pedido_ok = None
            st.session_state.pagina = "menu"
            st.rerun()
        st.stop()

    if not st.session_state.carrito:
        st.markdown('<div class="viet-form-section">', unsafe_allow_html=True)
        st.markdown('<p style="color:#888;text-align:center;padding:40px;">Tu carrito está vacío.</p>', unsafe_allow_html=True)
        if st.button("Ver el menú", key="go_menu_empty"):
            st.session_state.pagina = "menu"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    col_form, col_cart = st.columns([3, 2])

    with col_form:
        st.markdown('<div style="padding:32px;">', unsafe_allow_html=True)
        st.markdown('<p class="viet-form-title">Tus datos</p>', unsafe_allow_html=True)

        nombre = st.text_input("Nombre *", placeholder="Tu nombre completo", key="ped_nombre")
        telefono = st.text_input("Teléfono *", placeholder="600 000 000", key="ped_tel")
        email = st.text_input("Email (para confirmación)", placeholder="tu@email.com", key="ped_email")

        st.markdown('<p style="color:#fff;font-size:15px;font-weight:500;margin:20px 0 8px;">Hora de recogida</p>', unsafe_allow_html=True)
        espera = config.get("tiempo_espera_min", "15")
        st.caption(f"Tiempo estimado de preparación: {espera} minutos")

        slots = ["Lo antes posible"] + get_slots_recogida(config)
        hora_idx = slots.index(st.session_state.hora_sel) if st.session_state.hora_sel in slots else 0
        hora_sel = st.radio("", slots, index=hora_idx, key="hora_radio", horizontal=True, label_visibility="collapsed")
        st.session_state.hora_sel = hora_sel

        notas = st.text_area("Notas o alergias", placeholder="Sin cilantro, sin picante...", key="ped_notas", height=80)

        st.markdown('<p style="color:#555;font-size:12px;margin:16px 0 8px;">* Pago al recoger en el local</p>', unsafe_allow_html=True)

        if st.button("✅ Confirmar pedido", key="confirmar_pedido", use_container_width=True):
            if not nombre.strip() or not telefono.strip():
                st.error("Por favor rellena nombre y teléfono.")
            else:
                sb = get_supabase()
                pedido_data = {
                    "nombre": nombre.strip(),
                    "telefono": telefono.strip(),
                    "email": email.strip() or None,
                    "hora_recogida": hora_sel,
                    "notas": notas.strip() or None,
                    "total": round(total_carrito, 2),
                    "estado": "pendiente"
                }
                result = sb.table("pedidos").insert(pedido_data).execute()
                pedido_id = result.data[0]["id"]

                items = []
                for pid, item in st.session_state.carrito.items():
                    items.append({
                        "pedido_id": pedido_id,
                        "producto_id": int(pid),
                        "nombre_producto": item["nombre"],
                        "cantidad": item["cantidad"],
                        "precio_unitario": item["precio"]
                    })
                sb.table("pedido_items").insert(items).execute()

                # Email si está configurado
                email_dest = config.get("email_pedidos", "")

                st.session_state.pedido_ok = pedido_id
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    with col_cart:
        st.markdown('<div style="padding:32px;border-left:1px solid #222;">', unsafe_allow_html=True)
        st.markdown('<p style="color:#fff;font-size:18px;font-weight:500;margin-bottom:16px;">Tu pedido</p>', unsafe_allow_html=True)

        for pid, item in st.session_state.carrito.items():
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            c1.markdown(f'<p style="color:#fff;font-size:13px;margin:8px 0;">{item["nombre"]}</p>', unsafe_allow_html=True)
            if c2.button("−", key=f"cart_minus_{pid}"):
                if st.session_state.carrito[pid]["cantidad"] > 1:
                    st.session_state.carrito[pid]["cantidad"] -= 1
                else:
                    del st.session_state.carrito[pid]
                st.rerun()
            c3.markdown(f'<p style="text-align:center;color:#D85A30;font-size:14px;margin:8px 0;">{item["cantidad"]}</p>', unsafe_allow_html=True)
            if c4.button("+", key=f"cart_plus_{pid}"):
                st.session_state.carrito[pid]["cantidad"] += 1
                st.rerun()
            st.markdown(f'<p style="color:#D85A30;font-size:13px;text-align:right;margin:0 0 8px;">€{item["precio"]*item["cantidad"]:.2f}</p>', unsafe_allow_html=True)
            st.markdown('<hr style="border:none;border-top:1px solid #222;margin:4px 0;">', unsafe_allow_html=True)

        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;padding:16px 0 0;">
          <span style="color:#fff;font-size:18px;font-weight:500;">Total</span>
          <span style="color:#D85A30;font-size:20px;font-weight:500;">€{total_carrito:.2f}</span>
        </div>
        <p style="color:#555;font-size:12px;margin-top:4px;">IVA incluido · Pago al recoger</p>
        """, unsafe_allow_html=True)

        if st.button("← Seguir comprando", key="back_menu"):
            st.session_state.pagina = "menu"
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

# ── PÁGINA: RESERVA ───────────────────────────────────────────
elif st.session_state.pagina == "reserva":
    if st.session_state.reserva_ok:
        st.markdown("""
        <div class="viet-success">
          <div class="viet-success-icon">🍽️</div>
          <h2>¡Reserva recibida!</h2>
          <p>Confirmaremos tu reserva por email o teléfono en breve.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Volver al inicio", key="back_inicio_reserva"):
            st.session_state.reserva_ok = False
            st.session_state.pagina = "inicio"
            st.rerun()
        st.stop()

    st.markdown('<div class="viet-form-section">', unsafe_allow_html=True)
    st.markdown('<p class="viet-form-title">Reservar mesa</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="viet-form-subtitle">Disponemos de {config.get("mesas_total","15")} comensales. Te confirmamos por email o teléfono.</p>', unsafe_allow_html=True)

    r_nombre = st.text_input("Nombre *", placeholder="Tu nombre completo", key="res_nombre")
    col1, col2 = st.columns(2)
    r_tel = col1.text_input("Teléfono *", placeholder="600 000 000", key="res_tel")
    r_email = col2.text_input("Email", placeholder="tu@email.com", key="res_email")

    col3, col4 = st.columns(2)
    r_fecha = col3.date_input("Fecha *", min_value=date.today(), value=date.today() + timedelta(days=1), key="res_fecha")
    r_personas = col4.number_input("Personas *", min_value=1, max_value=int(config.get("mesas_total","15")), value=2, key="res_personas")

    # Slots de hora
    st.markdown('<p style="color:#aaa;font-size:13px;margin:12px 0 6px;">Hora *</p>', unsafe_allow_html=True)
    horas_disponibles = ["13:00","13:30","14:00","14:30","15:00","15:30","20:00","20:30","21:00","21:30"]
    if "hora_res_sel" not in st.session_state:
        st.session_state.hora_res_sel = "13:00"
    hora_res_cols = st.columns(len(horas_disponibles))
    for i, h in enumerate(horas_disponibles):
        with hora_res_cols[i]:
            sel = st.session_state.hora_res_sel == h
            if st.button(h, key=f"hora_res_{h}"):
                st.session_state.hora_res_sel = h
                st.rerun()

    r_notas = st.text_area("Notas (alergias, ocasión especial...)", placeholder="Cumpleaños, silla de bebé...", key="res_notas", height=80)

    if st.button("✅ Solicitar reserva", key="confirmar_reserva", use_container_width=True):
        if not r_nombre.strip() or not r_tel.strip():
            st.error("Por favor rellena nombre y teléfono.")
        else:
            sb = get_supabase()
            sb.table("reservas").insert({
                "nombre": r_nombre.strip(),
                "telefono": r_tel.strip(),
                "email": r_email.strip() or None,
                "fecha": str(r_fecha),
                "hora": st.session_state.hora_res_sel,
                "personas": int(r_personas),
                "notas": r_notas.strip() or None,
                "estado": "pendiente"
            }).execute()
            st.session_state.reserva_ok = True
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

