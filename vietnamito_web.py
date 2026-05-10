import streamlit as st
from supabase import create_client
from datetime import datetime, date, timedelta

st.set_page_config(
    page_title="Vietnamito — Banh mi & Café",
    page_icon="https://rwtpjqvgiiuvniixqapu.supabase.co/storage/v1/object/public/assets/Logo%20Vietnamito%20Final.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

SUPABASE_URL = "https://rwtpjqvgiiuvniixqapu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ3dHBqcXZnaWl1dm5paXhxYXB1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzcxMzIyMjMsImV4cCI6MjA5MjcwODIyM30.jznrwuusfgtVkrzz_bfdsxq3tVsv-uV2tyMeIlh3bZg"
LOGO_URL = "https://rwtpjqvgiiuvniixqapu.supabase.co/storage/v1/object/public/assets/Logo%20Vietnamito%20Final.png"
FOTO_LOCAL1 = "https://rwtpjqvgiiuvniixqapu.supabase.co/storage/v1/object/public/assets/local1.jpg"
FOTO_LOCAL2 = "https://rwtpjqvgiiuvniixqapu.supabase.co/storage/v1/object/public/assets/local2.jpg"
FOTO_MURAL = "https://rwtpjqvgiiuvniixqapu.supabase.co/storage/v1/object/public/assets/mural.jpg"

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
    mins = (inicio.minute // 15 + 1) * 15
    inicio = inicio.replace(minute=0) + timedelta(minutes=mins)
    slots = []
    for i in range(12):
        t = inicio + timedelta(minutes=15 * i)
        if t.hour < 22:
            slots.append(t.strftime("%H:%M"))
    return slots

# ── CSS ──────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;1,400&family=DM+Sans:wght@300;400;500&display=swap');

* {{ box-sizing: border-box; margin: 0; padding: 0; }}
.block-container {{ padding: 0 !important; max-width: 100% !important; }}
header {{ display: none !important; }}
.stApp {{ background: #F5F0E8; }}
[data-testid="stHorizontalBlock"] {{ display: none !important; }}

:root {{
    --cream: #F5F0E8;
    --cream-dark: #EDE7D9;
    --stone: #C8BEA8;
    --stone-dark: #8B7D6B;
    --brown: #5C4033;
    --orange: #D85A30;
    --orange-dark: #B84A22;
    --text: #2C1810;
    --text-muted: #7A6055;
    --white: #FDFAF5;
}}

body, .viet-body {{ font-family: 'DM Sans', sans-serif; color: var(--text); }}

/* NAV */
.viet-nav {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 48px; height: 72px;
    background: var(--white); border-bottom: 1px solid var(--stone);
    position: sticky; top: 0; z-index: 100;
}}
.viet-nav-logo {{ display: flex; align-items: center; gap: 14px; }}
.viet-nav-logo img {{ height: 44px; }}
.viet-nav-name {{ font-family: 'Playfair Display', serif; font-size: 20px; color: var(--brown); }}
.viet-nav-links {{ display: flex; gap: 32px; }}
.viet-nav-link {{
    font-size: 14px; font-weight: 400; color: var(--text-muted);
    text-decoration: none; letter-spacing: 0.03em; cursor: pointer;
    transition: color 0.2s; border: none; background: none; padding: 0;
}}
.viet-nav-link:hover {{ color: var(--orange); }}
.viet-nav-link.active {{ color: var(--orange); font-weight: 500; }}
.viet-nav-cta {{
    background: var(--orange); color: white; border: none;
    padding: 10px 22px; border-radius: 6px; font-size: 14px;
    font-weight: 500; cursor: pointer; font-family: 'DM Sans', sans-serif;
    transition: background 0.2s;
}}
.viet-nav-cta:hover {{ background: var(--orange-dark); }}

/* HERO */
.viet-hero {{
    position: relative; height: 580px; overflow: hidden;
    display: flex; align-items: center;
}}
.viet-hero-bg {{
    position: absolute; inset: 0;
    background-image: url('{FOTO_LOCAL2}');
    background-size: cover; background-position: center 30%;
    filter: brightness(0.55);
}}
.viet-hero-overlay {{
    position: absolute; inset: 0;
    background: linear-gradient(to right, rgba(44,24,16,0.7) 0%, rgba(44,24,16,0.2) 60%, transparent 100%);
}}
.viet-hero-content {{
    position: relative; z-index: 2; padding: 0 64px; max-width: 620px;
}}
.viet-hero-tag {{
    display: inline-block; background: var(--orange); color: white;
    font-size: 11px; font-weight: 500; letter-spacing: 0.12em;
    text-transform: uppercase; padding: 5px 14px; border-radius: 4px;
    margin-bottom: 20px;
}}
.viet-hero-title {{
    font-family: 'Playfair Display', serif; font-size: 52px; font-weight: 400;
    color: white; line-height: 1.15; margin-bottom: 16px;
}}
.viet-hero-title em {{ font-style: italic; color: #F4A261; }}
.viet-hero-sub {{
    font-size: 16px; color: rgba(255,255,255,0.75); margin-bottom: 32px;
    font-weight: 300; line-height: 1.6;
}}
.viet-hero-btns {{ display: flex; gap: 12px; flex-wrap: wrap; }}
.viet-btn-primary {{
    background: var(--orange); color: white; border: none;
    padding: 14px 28px; border-radius: 6px; font-size: 15px;
    font-weight: 500; cursor: pointer; font-family: 'DM Sans', sans-serif;
    transition: background 0.2s; display: inline-block;
}}
.viet-btn-primary:hover {{ background: var(--orange-dark); }}
.viet-btn-ghost {{
    background: transparent; color: white;
    border: 1.5px solid rgba(255,255,255,0.6);
    padding: 14px 28px; border-radius: 6px; font-size: 15px;
    cursor: pointer; font-family: 'DM Sans', sans-serif;
    transition: border-color 0.2s; display: inline-block;
}}
.viet-btn-ghost:hover {{ border-color: white; }}

/* INFO STRIP */
.viet-strip {{
    background: var(--brown); color: rgba(255,255,255,0.85);
    display: flex; justify-content: center; gap: 48px; padding: 18px 48px;
    font-size: 13px; letter-spacing: 0.02em; flex-wrap: wrap;
}}
.viet-strip-item {{ display: flex; align-items: center; gap: 8px; }}
.viet-strip-icon {{ font-size: 15px; opacity: 0.7; }}

/* SECCIONES */
.viet-section {{ padding: 64px 48px; background: var(--cream); }}
.viet-section-alt {{ padding: 64px 48px; background: var(--white); }}
.viet-section-title {{
    font-family: 'Playfair Display', serif; font-size: 34px; font-weight: 400;
    color: var(--brown); margin-bottom: 8px;
}}
.viet-section-sub {{ font-size: 15px; color: var(--text-muted); margin-bottom: 36px; font-weight: 300; }}

/* HORARIOS */
.viet-horario-grid {{
    display: grid; grid-template-columns: repeat(7, 1fr); gap: 10px;
}}
.viet-horario-dia {{
    background: var(--white); border: 1px solid var(--stone);
    border-radius: 10px; padding: 14px 10px; text-align: center;
}}
.viet-horario-dia.hoy {{
    background: var(--brown); border-color: var(--brown);
}}
.viet-horario-dia .dia-nombre {{ font-size: 11px; font-weight: 500; letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-muted); margin-bottom: 6px; }}
.viet-horario-dia.hoy .dia-nombre {{ color: rgba(255,255,255,0.6); }}
.viet-horario-dia .dia-hora {{ font-size: 12px; color: var(--text); }}
.viet-horario-dia.hoy .dia-hora {{ color: white; }}

/* FOTOS GALERÍA */
.viet-gallery {{
    display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 32px;
}}
.viet-gallery img {{ width: 100%; height: 280px; object-fit: cover; border-radius: 12px; }}
.viet-gallery img:first-child {{ grid-row: span 2; height: 572px; }}

/* MENÚ */
.viet-cat-bar {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 32px; }}
.viet-cat-btn {{
    padding: 8px 20px; border-radius: 24px; font-size: 13px; font-weight: 500;
    cursor: pointer; border: 1.5px solid var(--stone); color: var(--text-muted);
    background: transparent; font-family: 'DM Sans', sans-serif; transition: all 0.2s;
}}
.viet-cat-btn:hover {{ border-color: var(--orange); color: var(--orange); }}
.viet-cat-btn.active {{ background: var(--orange); border-color: var(--orange); color: white; }}

.viet-products-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 20px; }}
.viet-product {{
    background: var(--white); border: 1px solid var(--stone);
    border-radius: 14px; overflow: hidden; transition: transform 0.2s, box-shadow 0.2s;
}}
.viet-product:hover {{ transform: translateY(-3px); box-shadow: 0 8px 24px rgba(92,64,51,0.12); }}
.viet-product-img {{ width: 100%; height: 170px; object-fit: cover; background: var(--cream-dark); display: flex; align-items: center; justify-content: center; font-size: 36px; }}
.viet-product-body {{ padding: 16px; }}
.viet-product-name {{ font-family: 'Playfair Display', serif; font-size: 17px; color: var(--brown); margin-bottom: 6px; }}
.viet-product-desc {{ font-size: 12px; color: var(--text-muted); line-height: 1.6; margin-bottom: 14px; }}
.viet-product-foot {{ display: flex; align-items: center; justify-content: space-between; }}
.viet-product-price {{ font-size: 18px; font-weight: 500; color: var(--orange); }}
.viet-add-btn {{
    background: var(--orange); color: white; border: none;
    width: 32px; height: 32px; border-radius: 50%; font-size: 20px;
    cursor: pointer; display: flex; align-items: center; justify-content: center;
    line-height: 1; transition: background 0.2s;
}}
.viet-add-btn:hover {{ background: var(--orange-dark); }}

/* CARRITO FLOTANTE */
.viet-cart-fab {{
    position: fixed; bottom: 28px; right: 28px; z-index: 200;
    background: var(--brown); color: white; border: none;
    border-radius: 14px; padding: 14px 24px; font-size: 15px; font-weight: 500;
    cursor: pointer; font-family: 'DM Sans', sans-serif;
    box-shadow: 0 6px 24px rgba(92,64,51,0.35);
    display: flex; align-items: center; gap: 10px;
}}

/* FORMULARIO */
.viet-form-wrap {{ max-width: 800px; margin: 0 auto; padding: 48px; }}
.viet-form-title {{ font-family: 'Playfair Display', serif; font-size: 32px; color: var(--brown); margin-bottom: 8px; }}
.viet-form-sub {{ font-size: 14px; color: var(--text-muted); margin-bottom: 32px; }}
.viet-label {{ font-size: 13px; font-weight: 500; color: var(--text-muted); margin-bottom: 4px; letter-spacing: 0.03em; text-transform: uppercase; }}

/* HORA CHIPS */
.viet-hora-row {{ display: flex; gap: 8px; flex-wrap: wrap; margin: 10px 0 20px; }}
.viet-hora-chip {{
    padding: 7px 16px; border-radius: 24px; font-size: 13px;
    cursor: pointer; border: 1.5px solid var(--stone); color: var(--text-muted);
    background: transparent; font-family: 'DM Sans', sans-serif;
    transition: all 0.2s;
}}
.viet-hora-chip.sel {{ background: var(--orange); border-color: var(--orange); color: white; font-weight: 500; }}

/* CARRITO RESUMEN */
.viet-cart-line {{
    display: flex; align-items: center; padding: 12px 0;
    border-bottom: 1px solid var(--cream-dark); gap: 8px;
}}
.viet-cart-line-name {{ flex: 1; font-size: 14px; color: var(--text); }}
.viet-cart-line-price {{ font-size: 14px; color: var(--orange); font-weight: 500; min-width: 50px; text-align: right; }}

/* SUCCESS */
.viet-success {{
    text-align: center; padding: 80px 32px;
    background: var(--cream);
}}
.viet-success-circle {{
    width: 80px; height: 80px; background: var(--orange);
    border-radius: 50%; display: flex; align-items: center; justify-content: center;
    margin: 0 auto 24px; font-size: 36px;
}}
.viet-success h2 {{ font-family: 'Playfair Display', serif; font-size: 28px; color: var(--brown); margin-bottom: 12px; }}
.viet-success p {{ font-size: 15px; color: var(--text-muted); line-height: 1.7; }}

/* FOOTER */
.viet-footer {{
    background: var(--brown); color: rgba(255,255,255,0.6);
    padding: 40px 48px; text-align: center;
}}
.viet-footer img {{ height: 40px; margin-bottom: 16px; filter: brightness(10); }}
.viet-footer p {{ font-size: 13px; margin: 4px 0; }}

/* Streamlit overrides */
div[data-testid="stButton"] > button {{
    background: var(--orange) !important; color: white !important;
    border: none !important; border-radius: 8px !important;
    font-size: 15px !important; font-weight: 500 !important;
    padding: 12px 24px !important; width: 100% !important;
    font-family: 'DM Sans', sans-serif !important;
    transition: background 0.2s !important;
}}
div[data-testid="stButton"] > button:hover {{ background: var(--orange-dark) !important; }}
</style>
""", unsafe_allow_html=True)

# ── State ─────────────────────────────────────────────────────
for k, v in [("pagina","inicio"),("carrito",{}),("cat_sel",None),
              ("hora_sel","Lo antes posible"),("pedido_ok",None),
              ("reserva_ok",False),("hora_res_sel","13:00")]:
    if k not in st.session_state:
        st.session_state[k] = v

config = get_config()
categorias = get_categorias()
productos = get_productos()

if st.session_state.cat_sel is None and categorias:
    st.session_state.cat_sel = categorias[0]["id"]

n_carrito = sum(v["cantidad"] for v in st.session_state.carrito.values())
total_carrito = sum(v["precio"] * v["cantidad"] for v in st.session_state.carrito.values())

dias_es = ["lunes","martes","miercoles","jueves","viernes","sabado","domingo"]
dias_label = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]
hoy_idx = datetime.now().weekday()
horario_hoy = config.get(f"horario_{dias_es[hoy_idx]}", "")

# ── NAV ──────────────────────────────────────────────────────
pagina = st.session_state.pagina
st.markdown(f"""
<nav class="viet-nav">
  <div class="viet-nav-logo">
    <img src="{LOGO_URL}" alt="Vietnamito">
    <span class="viet-nav-name">{config.get('nombre_local','Vietnamito')}</span>
  </div>
  <div class="viet-nav-links">
    <span class="viet-nav-link {'active' if pagina=='inicio' else ''}" onclick="">Inicio</span>
    <span class="viet-nav-link {'active' if pagina=='menu' else ''}" onclick="">Menú</span>
    <span class="viet-nav-link {'active' if pagina=='pedido' else ''}" onclick="">Pedir</span>
    <span class="viet-nav-link {'active' if pagina=='reserva' else ''}" onclick="">Reservar</span>
  </div>
  <button class="viet-nav-cta">🛒 Pedir para recoger</button>
</nav>
""", unsafe_allow_html=True)

# Nav funcional (oculto visualmente via CSS)
nc = st.columns(4)
if nc[0].button("Inicio", key="nav_i"): st.session_state.pagina = "inicio"; st.rerun()
if nc[1].button("Menú", key="nav_m"): st.session_state.pagina = "menu"; st.rerun()
if nc[2].button("Pedir", key="nav_p"): st.session_state.pagina = "pedido"; st.rerun()
if nc[3].button("Reservar", key="nav_r"): st.session_state.pagina = "reserva"; st.rerun()

# ── INICIO ────────────────────────────────────────────────────
if st.session_state.pagina == "inicio":
    st.markdown(f"""
    <div class="viet-hero">
      <div class="viet-hero-bg"></div>
      <div class="viet-hero-overlay"></div>
      <div class="viet-hero-content">
        <span class="viet-hero-tag">Barcelona · Eixample Esquerra</span>
        <h1 class="viet-hero-title">Banh mi &<br><em>sabores</em> de Vietnam</h1>
        <p class="viet-hero-sub">{config.get('direccion','')} · Hoy: {horario_hoy}</p>
      </div>
    </div>
    <div class="viet-strip">
      <div class="viet-strip-item"><span class="viet-strip-icon">📍</span> {config.get('direccion','')}</div>
      <div class="viet-strip-item"><span class="viet-strip-icon">📞</span> {config.get('telefono','')}</div>
      <div class="viet-strip-item"><span class="viet-strip-icon">🕐</span> Hoy: {horario_hoy}</div>
    </div>
    """, unsafe_allow_html=True)

    # Botones hero funcionales
    hc1, hc2, hc3 = st.columns([2,2,4])
    with hc1:
        if st.button("🛵 Pedir para recoger", key="h_ped"): st.session_state.pagina = "menu"; st.rerun()
    with hc2:
        if st.button("🍽️ Reservar mesa", key="h_res"): st.session_state.pagina = "reserva"; st.rerun()

    # Sección del local
    st.markdown("""
    <div class="viet-section-alt">
      <p class="viet-section-title">Nuestro espacio</p>
      <p class="viet-section-sub">Un rincón de Vietnam en el corazón de Barcelona</p>
    </div>
    """, unsafe_allow_html=True)

    col_txt, col_img = st.columns([1, 1])
    with col_txt:
        st.markdown(f"""
        <div style="padding:40px 32px 40px 48px;background:var(--white);">
          <p class="viet-section-title">Un rincón de<br><em style="font-family:'Playfair Display',serif;font-style:italic;color:var(--orange);">Vietnam</em><br>en Barcelona</p>
          <p style="font-size:15px;color:var(--text-muted);line-height:1.8;margin:20px 0 32px;font-weight:300;">
            Banh mi artesanal, pho reconfortante y café vietnamita de especialidad.<br>
            Un espacio cálido y acogedor para disfrutar de los sabores auténticos del sudeste asiático.
          </p>
          <p style="font-size:13px;color:var(--text-muted);"><strong style="color:var(--brown);">{config.get('direccion','')}</strong></p>
        </div>
        """, unsafe_allow_html=True)
    with col_img:
        st.markdown(f'<img src="{FOTO_LOCAL1}" style="width:100%;height:400px;object-fit:cover;display:block;">', unsafe_allow_html=True)

    # Horarios
    st.markdown("""
    <div class="viet-section">
      <p class="viet-section-title">Horario</p>
      <div class="viet-horario-grid">
    """, unsafe_allow_html=True)
    for i, (dia, label) in enumerate(zip(dias_es, dias_label)):
        horario = config.get(f"horario_{dia}", "—")
        es_hoy = i == hoy_idx
        st.markdown(f"""
        <div class="viet-horario-dia {'hoy' if es_hoy else ''}">
          <p class="dia-nombre">{label}</p>
          <p class="dia-hora">{horario}</p>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

    # Mural/foto final
    st.markdown(f'<img src="{FOTO_MURAL}" style="width:100%;height:340px;object-fit:cover;object-position:center 20%;display:block;">', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="viet-footer">
      <img src="{LOGO_URL}" alt="Vietnamito">
      <p><strong style="color:white;">{config.get('nombre_local','Vietnamito')}</strong> · Banh mi & Café</p>
      <p>{config.get('direccion','')}</p>
      <p style="margin-top:8px;">{config.get('telefono','')} · {config.get('email_pedidos','')}</p>
    </div>
    """, unsafe_allow_html=True)

# ── MENÚ ──────────────────────────────────────────────────────
elif st.session_state.pagina == "menu":
    st.markdown("""
    <div class="viet-section">
      <p class="viet-section-title">Nuestra carta</p>
      <p class="viet-section-sub">Ingredientes frescos, recetas auténticas</p>
      <div class="viet-cat-bar">
    """, unsafe_allow_html=True)

    for cat in categorias:
        active = "active" if st.session_state.cat_sel == cat["id"] else ""
        st.markdown(f'<span class="viet-cat-btn {active}">{cat["nombre"]}</span>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    cat_cols = st.columns(len(categorias))
    for i, cat in enumerate(categorias):
        with cat_cols[i]:
            if st.button(cat["nombre"], key=f"cat_{cat['id']}", use_container_width=True):
                st.session_state.cat_sel = cat["id"]
                st.rerun()

    prods_cat = [p for p in productos if p["categoria_id"] == st.session_state.cat_sel]

    if prods_cat:
        st.markdown('<div class="viet-products-grid">', unsafe_allow_html=True)
        cols = st.columns(3)
        for i, prod in enumerate(prods_cat):
            with cols[i % 3]:
                foto = prod.get("foto_url")
                if foto:
                    st.markdown(f'<div class="viet-product"><img src="{foto}" style="width:100%;height:170px;object-fit:cover;">', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="viet-product"><div class="viet-product-img">🍜</div>', unsafe_allow_html=True)

                st.markdown(f"""
                <div class="viet-product-body">
                  <p class="viet-product-name">{prod['nombre']}</p>
                  <p class="viet-product-desc">{prod.get('descripcion','')}</p>
                  <div class="viet-product-foot">
                    <span class="viet-product-price">€{prod['precio']:.2f}</span>
                  </div>
                </div></div>
                """, unsafe_allow_html=True)

                pid = prod["id"]
                qty = st.session_state.carrito.get(pid, {}).get("cantidad", 0)
                if qty == 0:
                    if st.button("Añadir", key=f"add_{pid}", use_container_width=True):
                        st.session_state.carrito[pid] = {"nombre": prod["nombre"], "precio": prod["precio"], "cantidad": 1}
                        st.rerun()
                else:
                    c1, c2, c3 = st.columns([1,2,1])
                    if c1.button("−", key=f"m_{pid}"):
                        if st.session_state.carrito[pid]["cantidad"] > 1:
                            st.session_state.carrito[pid]["cantidad"] -= 1
                        else:
                            del st.session_state.carrito[pid]
                        st.rerun()
                    c2.markdown(f'<p style="text-align:center;color:var(--orange);font-size:16px;font-weight:500;padding:8px 0;">{qty}</p>', unsafe_allow_html=True)
                    if c3.button("+", key=f"p_{pid}"):
                        st.session_state.carrito[pid]["cantidad"] += 1
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    if n_carrito > 0:
        st.markdown(f"""
        <div class="viet-cart-fab">
          🛒 {n_carrito} artículo{"s" if n_carrito>1 else ""} · €{total_carrito:.2f} →
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"🛒 Ver pedido — €{total_carrito:.2f}", key="go_ped", use_container_width=True):
            st.session_state.pagina = "pedido"; st.rerun()

# ── PEDIDO ────────────────────────────────────────────────────
elif st.session_state.pagina == "pedido":
    if st.session_state.pedido_ok:
        st.markdown(f"""
        <div class="viet-success">
          <div class="viet-success-circle">✓</div>
          <h2>¡Pedido confirmado!</h2>
          <p>Tu pedido #{st.session_state.pedido_ok} está siendo preparado.<br>
          Recogida: <strong style="color:var(--orange);">{st.session_state.hora_sel}</strong><br><br>
          Te esperamos en {config.get('direccion','')}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Hacer otro pedido", key="otro"):
            st.session_state.carrito = {}; st.session_state.pedido_ok = None
            st.session_state.pagina = "menu"; st.rerun()
        st.stop()

    if not st.session_state.carrito:
        st.markdown('<div class="viet-form-wrap"><p style="color:var(--text-muted);text-align:center;padding:40px;">Tu carrito está vacío.</p></div>', unsafe_allow_html=True)
        if st.button("Ver el menú", key="back_m"): st.session_state.pagina = "menu"; st.rerun()
        st.stop()

    col_f, col_c = st.columns([3, 2])
    with col_f:
        st.markdown('<div style="padding:40px 32px 40px 48px;background:var(--cream);">', unsafe_allow_html=True)
        st.markdown('<p class="viet-form-title">Tu pedido</p>', unsafe_allow_html=True)
        st.markdown('<p class="viet-form-sub">Recogida en Calle Berlín 76 · Pago al recoger</p>', unsafe_allow_html=True)

        nombre = st.text_input("Nombre *", placeholder="Tu nombre", key="pnom")
        c1, c2 = st.columns(2)
        telefono = c1.text_input("Teléfono *", placeholder="600 000 000", key="ptel")
        email = c2.text_input("Email", placeholder="tu@email.com", key="pemail")

        st.markdown(f'<p class="viet-label" style="margin-top:20px;">Hora de recogida</p>', unsafe_allow_html=True)
        st.caption(f"Tiempo estimado: {config.get('tiempo_espera_min','15')} min")

        slots = ["Lo antes posible"] + get_slots_recogida(config)
        hora_sel = st.radio("", slots, index=slots.index(st.session_state.hora_sel) if st.session_state.hora_sel in slots else 0,
                           key="hora_r", horizontal=True, label_visibility="collapsed")
        st.session_state.hora_sel = hora_sel

        notas = st.text_area("Notas / alergias", placeholder="Sin cilantro, sin picante...", key="pnot", height=80)

        if st.button("✓ Confirmar pedido", key="conf_ped", use_container_width=True):
            if not nombre.strip() or not telefono.strip():
                st.error("Por favor rellena nombre y teléfono.")
            else:
                sb = get_supabase()
                res = sb.table("pedidos").insert({
                    "nombre": nombre.strip(), "telefono": telefono.strip(),
                    "email": email.strip() or None, "hora_recogida": hora_sel,
                    "notas": notas.strip() or None, "total": round(total_carrito, 2), "estado": "pendiente"
                }).execute()
                pid_new = res.data[0]["id"]
                sb.table("pedido_items").insert([{
                    "pedido_id": pid_new, "producto_id": int(k),
                    "nombre_producto": v["nombre"], "cantidad": v["cantidad"], "precio_unitario": v["precio"]
                } for k, v in st.session_state.carrito.items()]).execute()
                st.session_state.pedido_ok = pid_new; st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    with col_c:
        st.markdown('<div style="padding:40px 32px;background:var(--white);min-height:500px;">', unsafe_allow_html=True)
        st.markdown('<p style="font-family:\'Playfair Display\',serif;font-size:20px;color:var(--brown);margin-bottom:20px;">Resumen</p>', unsafe_allow_html=True)
        for pid, item in st.session_state.carrito.items():
            st.markdown(f"""
            <div class="viet-cart-line">
              <span class="viet-cart-line-name">{item['nombre']} ×{item['cantidad']}</span>
              <span class="viet-cart-line-price">€{item['precio']*item['cantidad']:.2f}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;padding:20px 0 8px;margin-top:4px;">
          <span style="font-size:18px;font-weight:500;color:var(--brown);">Total</span>
          <span style="font-size:20px;font-weight:500;color:var(--orange);">€{total_carrito:.2f}</span>
        </div>
        <p style="font-size:12px;color:var(--text-muted);">IVA incluido · Pago al recoger en caja</p>
        """, unsafe_allow_html=True)
        if st.button("← Seguir comprando", key="back_men"): st.session_state.pagina = "menu"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ── RESERVA ───────────────────────────────────────────────────
elif st.session_state.pagina == "reserva":
    if st.session_state.reserva_ok:
        st.markdown(f"""
        <div class="viet-success">
          <div class="viet-success-circle">✓</div>
          <h2>¡Reserva recibida!</h2>
          <p>Confirmaremos tu reserva por teléfono o email en breve.<br>
          ¡Te esperamos en {config.get('direccion','')}!</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Volver al inicio", key="bi"):
            st.session_state.reserva_ok = False; st.session_state.pagina = "inicio"; st.rerun()
        st.stop()

    st.markdown(f"""
    <div style="background:var(--cream);">
      <div style="display:grid;grid-template-columns:1fr 1fr;min-height:500px;">
        <img src="{FOTO_LOCAL2}" style="width:100%;height:100%;object-fit:cover;min-height:400px;">
        <div style="padding:56px 48px;">
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <p class="viet-form-title">Reservar mesa</p>
    <p class="viet-form-sub" style="margin-bottom:28px;">{config.get('mesas_total','15')} comensales · Confirmaremos por email o teléfono</p>
    """, unsafe_allow_html=True)

    r_nom = st.text_input("Nombre *", placeholder="Tu nombre", key="rnom")
    rc1, rc2 = st.columns(2)
    r_tel = rc1.text_input("Teléfono *", placeholder="600 000 000", key="rtel")
    r_email = rc2.text_input("Email", placeholder="tu@email.com", key="remail")
    rd1, rd2 = st.columns(2)
    r_fecha = rd1.date_input("Fecha *", min_value=date.today(), value=date.today()+timedelta(days=1), key="rfecha")
    r_pers = rd2.number_input("Personas *", min_value=1, max_value=int(config.get("mesas_total","15")), value=2, key="rpers")

    st.markdown('<p class="viet-label" style="margin-top:16px;">Hora *</p>', unsafe_allow_html=True)
    horas_res = ["13:00","13:30","14:00","14:30","15:00","20:00","20:30","21:00","21:30"]
    hora_cols = st.columns(len(horas_res))
    for i, h in enumerate(horas_res):
        with hora_cols[i]:
            sel = st.session_state.hora_res_sel == h
            if st.button(h, key=f"hr_{h}"):
                st.session_state.hora_res_sel = h; st.rerun()

    r_notas = st.text_area("Notas", placeholder="Cumpleaños, silla de bebé...", key="rnot", height=70)

    if st.button("✓ Solicitar reserva", key="conf_res", use_container_width=True):
        if not r_nom.strip() or not r_tel.strip():
            st.error("Por favor rellena nombre y teléfono.")
        else:
            sb = get_supabase()
            sb.table("reservas").insert({
                "nombre": r_nom.strip(), "telefono": r_tel.strip(),
                "email": r_email.strip() or None, "fecha": str(r_fecha),
                "hora": st.session_state.hora_res_sel, "personas": int(r_pers),
                "notas": r_notas.strip() or None, "estado": "pendiente"
            }).execute()
            st.session_state.reserva_ok = True; st.rerun()

    st.markdown('</div></div></div>', unsafe_allow_html=True)
