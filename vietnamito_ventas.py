import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
TZ_MADRID = ZoneInfo("Europe/Madrid")

def hoy_madrid():
    """Devuelve la fecha de HOY en zona horaria Europe/Madrid (no UTC del servidor)."""
    return datetime.now(TZ_MADRID).date()
from supabase import create_client

st.set_page_config(page_title="Vietnamito — Ventas", page_icon="☕", layout="wide")

# ── AUTENTICACIÓN ──
import hashlib
import requests as _rq
from datetime import datetime as _dt, timezone as _tz, timedelta as _td

# Guard anti fuerza bruta persistido en Supabase (no se salta ni refrescando ni borrando caché)
_BO_SB_URL = "https://rwtpjqvgiiuvniixqapu.supabase.co"
_BO_SB_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ3dHBqcXZnaWl1dm5paXhxYXB1Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzEzMjIyMywiZXhwIjoyMDkyNzA4MjIzfQ.GH-3IsaWLUbivHzkjjNmC3Vwg1V5gcaXZx06wom8TB4"
_GUARD_HDRS = {"apikey": _BO_SB_KEY, "Authorization": f"Bearer {_BO_SB_KEY}", "Content-Type": "application/json"}


def _auth_token(pwd: str) -> str:
    """Token derivado de la contraseña (no expone la contraseña en la URL)."""
    return hashlib.sha256(("vietnamito_bo_salt::" + pwd).encode()).hexdigest()[:32]


def _guard_leer():
    try:
        r = _rq.get(f"{_BO_SB_URL}/rest/v1/backoffice_login_guard?id=eq.1&select=*", headers=_GUARD_HDRS, timeout=5)
        rows = r.json()
        if rows:
            return rows[0]
    except Exception:
        pass
    return {"fails": 0, "lock_until": None}


def _guard_escribir(fails, lock_until_iso):
    try:
        _rq.patch(f"{_BO_SB_URL}/rest/v1/backoffice_login_guard?id=eq.1", headers=_GUARD_HDRS,
                  json={"fails": fails, "lock_until": lock_until_iso}, timeout=5)
    except Exception:
        pass


def _guard_lock_restante_s(g):
    """Segundos restantes de bloqueo (0 si no hay bloqueo activo)."""
    lu = g.get("lock_until")
    if not lu:
        return 0
    try:
        t = _dt.fromisoformat(str(lu).replace("Z", "+00:00"))
        return max(0, (t - _dt.now(_tz.utc)).total_seconds())
    except Exception:
        return 0


def _guard_duracion_min(fails):
    """Escalado: 3 fallos→5min · 6→15 · 9→30 · 12+→180 (3h) cada vez."""
    ronda = fails // 3
    return {1: 5, 2: 15, 3: 30}.get(ronda, 180 if ronda >= 4 else 0)


def _guard_texto_espera(segundos):
    m = int(segundos // 60) + (1 if segundos % 60 else 0)
    if m >= 60:
        h, mm = divmod(m, 60)
        return f"{h}h {mm}min" if mm else f"{h}h"
    return f"{m} min"


def check_password():
    """Devuelve True si el usuario está autenticado (sesión, URL token o login)."""
    correct_pwd = st.secrets.get("backoffice_password", "cambiame_en_secrets")
    expected_token = _auth_token(correct_pwd)

    # 1. Ya validado en esta sesión
    if st.session_state.get("password_correct"):
        # Asegurar que el token está en la URL para persistir tras refresh
        if st.query_params.get("auth") != expected_token:
            st.query_params["auth"] = expected_token
        return True

    # 2. Token válido en la URL (persiste entre sesiones/refresh/marcadores)
    #    Los tokens válidos NO se ven afectados por el bloqueo (son credenciales correctas)
    if st.query_params.get("auth") == expected_token:
        st.session_state["password_correct"] = True
        return True

    # 3. Login por contraseña, protegido por bloqueo escalado
    guard = _guard_leer()
    bloqueado_s = _guard_lock_restante_s(guard)

    def password_entered():
        g = _guard_leer()
        if _guard_lock_restante_s(g) > 0:
            # Bloqueado: ignorar el intento por completo
            st.session_state["password_correct"] = None
            return
        if st.session_state.get("password") == correct_pwd:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
            _guard_escribir(0, None)  # login correcto → contadores a cero
        else:
            st.session_state["password_correct"] = False
            fails = int(g.get("fails") or 0) + 1
            lock_iso = None
            if fails % 3 == 0:
                mins = _guard_duracion_min(fails)
                lock_iso = (_dt.now(_tz.utc) + _td(minutes=mins)).isoformat()
            _guard_escribir(fails, lock_iso)

    # Pantalla de login
    st.markdown("""
    <div style="max-width:400px;margin:80px auto;padding:40px;background:var(--background-color, #fff);border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.08);text-align:center;">
      <h1 style="margin:0 0 8px;font-size:24px;">☕ Vietnamito</h1>
      <p style="color:#666;margin:0 0 24px;font-size:14px;">Backoffice — Acceso restringido</p>
    </div>
    """, unsafe_allow_html=True)

    if bloqueado_s > 0:
        st.error(f"🔒 Demasiados intentos fallidos. Vuelve a intentarlo en {_guard_texto_espera(bloqueado_s)}.")
        st.caption("El bloqueo se levanta automáticamente. Recarga la página pasado ese tiempo.")
        return False

    st.text_input("Contraseña", type="password", on_change=password_entered, key="password")
    if st.session_state.get("password_correct") is False:
        g_post = _guard_leer()
        rest_post = _guard_lock_restante_s(g_post)
        if rest_post > 0:
            st.error(f"🔒 Demasiados intentos fallidos. Vuelve a intentarlo en {_guard_texto_espera(rest_post)}.")
        else:
            quedan = 3 - (int(g_post.get("fails") or 0) % 3)
            st.error(f"❌ Contraseña incorrecta ({quedan} intento{'s' if quedan != 1 else ''} antes de bloqueo)")
    st.caption("Este backoffice contiene datos confidenciales del negocio. Solo personal autorizado.")
    return False

if not check_password():
    st.stop()

# ── FIN AUTENTICACIÓN ──

SUPABASE_URL = "https://rwtpjqvgiiuvniixqapu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ3dHBqcXZnaWl1dm5paXhxYXB1Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzEzMjIyMywiZXhwIjoyMDkyNzA4MjIzfQ.GH-3IsaWLUbivHzkjjNmC3Vwg1V5gcaXZx06wom8TB4"

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    h1 { font-size: 1.6rem; font-weight: 600; }
    .stTabs [data-baseweb="tab"] { font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

try:
    RESEND_API_KEY = st.secrets["RESEND_API_KEY"]
except Exception:
    RESEND_API_KEY = ""
RESEND_FROM = "Vietnamito <reservas@vietnamito.es>"

MAPS_URL = "https://maps.app.goo.gl/LWR4Sm5mdAfR3H7v5"

def formato_fecha_email(fecha_str):
    """Convierte '2026-06-11' a 'Jueves 11/06/2026'."""
    try:
        from datetime import datetime
        dias = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo']
        dt = datetime.strptime(fecha_str, "%Y-%m-%d")
        return f"{dias[dt.weekday()]} {dt.strftime('%d/%m/%Y')}"
    except:
        return fecha_str

def _resend_send(to, subject, html_body):
    """Envía email via Resend API usando requests."""
    if not RESEND_API_KEY:
        st.warning("⚠️ RESEND_API_KEY no configurada en Secrets.")
        return False
    try:
        import requests as _req
        r = _req.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            json={"from": RESEND_FROM, "to": [to], "bcc": ["reservas@vietnamito.es"], "subject": subject, "html": html_body},
            timeout=10
        )
        if r.status_code not in [200, 201, 202]:
            st.warning(f"⚠️ Error Resend {r.status_code}: {r.text[:200]}")
            return False
        return True
    except Exception as e:
        st.warning(f"⚠️ Error enviando email: {e}")
        return False

def _html_base(titulo, subtitulo, contenido):
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:Georgia,serif;background:#FDF6EC;margin:0;padding:20px 0;">
  <div style="max-width:560px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.1);">
    <div style="background:linear-gradient(135deg,#8B3A1A,#D85A30);padding:36px 40px 28px;text-align:center;">
      <img src="https://rwtpjqvgiiuvniixqapu.supabase.co/storage/v1/object/public/assets/Logo%20Vietnamito%20Final.png" style="height:56px;margin-bottom:14px;" alt="Vietnamito">
      <h1 style="color:#fff;font-size:24px;font-weight:400;margin:0;font-family:Georgia,serif;">{titulo}</h1>
      <p style="color:rgba(255,255,255,0.75);font-size:14px;margin:8px 0 0;">{subtitulo}</p>
    </div>
    <div style="padding:36px 40px;">{contenido}</div>
    <div style="background:#3D1C0A;padding:20px 40px;text-align:center;">
      <a href="{MAPS_URL}" style="display:inline-block;background:#D85A30;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;font-family:Georgia,serif;font-size:13px;margin-bottom:14px;">📍 Ver en Google Maps</a>
      <p style="color:rgba(255,255,255,0.4);font-size:11px;margin:0;">Vietnamito · Banh mi & Café · Carrer Berlín 64, Barcelona · Sants – Les Corts<br>Tus datos se usan únicamente para gestionar tu reserva.</p>
    </div>
  </div>
</body></html>"""

def _tabla_reserva(fecha, hora, personas, notas, cfg=None):
    dir_local = (cfg or {}).get("direccion", "Carrer Berlín 64, Barcelona")
    notas_row = f"<tr><td style='padding:8px 0;color:#7A6055;font-size:14px;vertical-align:top;'>📝 Notas</td><td style='padding:8px 0;color:#3D1C0A;font-size:14px;'>{notas}</td></tr>" if notas else ""
    return f"""
    <div style="background:#FDF6EC;border-radius:10px;padding:22px 24px;margin:20px 0;border:1px solid rgba(216,90,48,0.15);">
      <table style="width:100%;border-collapse:collapse;">
        <tr><td style="padding:8px 0;color:#7A6055;font-size:14px;">📅 Fecha</td><td style="padding:8px 0;color:#3D1C0A;font-weight:600;font-size:14px;">{fecha}</td></tr>
        <tr><td style="padding:8px 0;color:#7A6055;font-size:14px;">🕐 Hora</td><td style="padding:8px 0;color:#3D1C0A;font-weight:600;font-size:14px;">{hora}</td></tr>
        <tr><td style="padding:8px 0;color:#7A6055;font-size:14px;">👥 Personas</td><td style="padding:8px 0;color:#3D1C0A;font-weight:600;font-size:14px;">{personas}</td></tr>
        {notas_row}
        <tr><td style="padding:8px 0;color:#7A6055;font-size:14px;">📍 Dirección</td><td style="padding:8px 0;font-size:14px;"><a href="{MAPS_URL}" style="color:#D85A30;">{dir_local}</a></td></tr>
      </table>
    </div>"""

def enviar_email_recibida(reserva, cfg=None):
    """Email automático al recibir la solicitud — aún pendiente de confirmar."""
    if not reserva.get("email"):
        return False
    nombre = reserva.get("nombre", "")
    fecha = formato_fecha_email(reserva.get("fecha", ""))
    hora = reserva.get("hora", "")
    personas = reserva.get("personas", "")
    notas = reserva.get("notas", "")
    tabla = _tabla_reserva(fecha, hora, personas, notas, cfg)
    contenido = f"""
      <p style="font-size:16px;color:#3D1C0A;margin:0 0 16px;">Hola <strong>{nombre}</strong>,</p>
      <p style="font-size:15px;color:#5C4033;line-height:1.7;margin:0 0 20px;">Hemos recibido tu solicitud de reserva en <strong>Vietnamito</strong>. La revisaremos y te confirmaremos por email en breve.</p>
      {tabla}
      <p style="font-size:13px;color:#7A6055;line-height:1.7;margin:16px 0 0;">¿Tienes alguna duda? Responde a este email o llámanos al <strong>+34 711 216 862</strong>.</p>"""
    html = _html_base("Solicitud recibida 📬", "Te confirmaremos la reserva por email", contenido)
    return _resend_send(reserva["email"], f"Solicitud de reserva recibida — Vietnamito {fecha} {hora}", html)

def enviar_email_confirmacion(reserva, cfg=None):
    """Email de confirmación cuando se acepta la reserva desde el backoffice."""
    if not reserva.get("email"):
        return False
    nombre = reserva.get("nombre", "")
    fecha = formato_fecha_email(reserva.get("fecha", ""))
    hora = reserva.get("hora", "")
    personas = reserva.get("personas", "")
    notas = reserva.get("notas", "")
    tabla = _tabla_reserva(fecha, hora, personas, notas, cfg)
    contenido = f"""
      <p style="font-size:16px;color:#3D1C0A;margin:0 0 16px;">Hola <strong>{nombre}</strong>,</p>
      <p style="font-size:15px;color:#5C4033;line-height:1.7;margin:0 0 20px;">Tu reserva en <strong>Vietnamito</strong> ha sido <strong style="color:#2E7D32;">confirmada</strong>. ¡Te esperamos!</p>
      {tabla}
      <p style="font-size:13px;color:#7A6055;line-height:1.7;margin:16px 0 0;">Para modificar o cancelar tu reserva, responde a este email o llámanos al <strong>+34 711 216 862</strong>.</p>"""
    html = _html_base("Reserva confirmada ✓", f"{fecha} a las {hora} · {personas} personas", contenido)
    return _resend_send(reserva["email"], f"✓ Reserva confirmada — Vietnamito {fecha} {hora}", html)

def enviar_email_cancelacion(reserva, cfg=None):
    """Email de cancelación cuando se cancela la reserva desde el backoffice."""
    if not reserva.get("email"):
        return False
    nombre = reserva.get("nombre", "")
    fecha = formato_fecha_email(reserva.get("fecha", ""))
    hora = reserva.get("hora", "")
    personas = reserva.get("personas", "")
    notas = reserva.get("notas", "")
    tabla = _tabla_reserva(fecha, hora, personas, notas, cfg)
    contenido = f"""
      <p style="font-size:16px;color:#3D1C0A;margin:0 0 16px;">Hola <strong>{nombre}</strong>,</p>
      <p style="font-size:15px;color:#5C4033;line-height:1.7;margin:0 0 20px;">Tu reserva en <strong>Vietnamito</strong> ha sido <strong style="color:#C62828;">cancelada</strong>.</p>
      {tabla}
      <p style="font-size:15px;color:#5C4033;line-height:1.7;margin:0 0 20px;">Si quieres hacer una nueva reserva o tienes alguna duda, responde a este email o llámanos al <strong>+34 711 216 862</strong>. ¡Esperamos verte pronto!</p>"""
    html = _html_base("Reserva cancelada", f"{fecha} a las {hora}", contenido)
    return _resend_send(reserva["email"], f"Reserva cancelada — Vietnamito {fecha} {hora}", html)


# ── Emails de PEDIDOS ──
def _tabla_pedido(ped, items, cfg=None):
    """Tabla resumen del pedido para emails."""
    rows = ""
    for it in items:
        subtotal = float(it["cantidad"]) * float(it["precio_unitario"])
        rows += f"""<tr><td style="padding:8px 12px;border-bottom:1px solid #EEDCC8;color:#5C4033;font-size:14px;">{it['cantidad']}× {it['nombre_producto']}</td><td style="padding:8px 12px;border-bottom:1px solid #EEDCC8;text-align:right;color:#5C4033;font-size:14px;">€{subtotal:.2f}</td></tr>"""
    notas_html = ""
    if ped.get("notas"):
        notas_html = f"""<tr><td colspan="2" style="padding:10px 12px;background:#FFF6E5;color:#5C4033;font-size:13px;font-style:italic;">📝 {ped['notas']}</td></tr>"""
    return f"""
      <table style="width:100%;border-collapse:collapse;margin:20px 0;background:#FFFCF6;border:1px solid #EEDCC8;border-radius:8px;overflow:hidden;">
        <tr><td style="padding:12px;background:#FFF3E0;color:#3D1C0A;font-size:13px;"><strong>🕐 Recogida:</strong> {ped.get('hora_recogida','—')}</td><td style="padding:12px;background:#FFF3E0;color:#3D1C0A;font-size:13px;text-align:right;"><strong>#{ped.get('id','')}</strong></td></tr>
        {rows}
        {notas_html}
        <tr><td style="padding:12px;color:#3D1C0A;font-size:15px;font-weight:600;">Total</td><td style="padding:12px;text-align:right;color:#3D1C0A;font-size:15px;font-weight:600;">€{float(ped.get('total',0)):.2f}</td></tr>
      </table>"""


def enviar_email_pedido_recibido(ped, items, cfg=None):
    """Email automático al recibir el pedido — aún pendiente de aceptar."""
    if not ped.get("email"):
        return False
    nombre = ped.get("nombre", "")
    tabla = _tabla_pedido(ped, items, cfg)
    contenido = f"""
      <p style="font-size:16px;color:#3D1C0A;margin:0 0 16px;">Hola <strong>{nombre}</strong>,</p>
      <p style="font-size:15px;color:#5C4033;line-height:1.7;margin:0 0 20px;">Hemos recibido tu pedido en <strong>Vietnamito</strong>. Lo revisaremos y te confirmaremos por email en breve si podemos prepararlo a tiempo.</p>
      {tabla}
      <p style="font-size:13px;color:#7A6055;line-height:1.7;margin:16px 0 0;">¿Tienes alguna duda? Responde a este email o llámanos al <strong>+34 711 216 862</strong>.</p>"""
    html = _html_base("Pedido recibido 📬", "Te confirmaremos en breve", contenido)
    return _resend_send(ped["email"], f"Pedido recibido — Vietnamito #{ped.get('id','')}", html)


def enviar_email_pedido_aceptado(ped, items, cfg=None):
    """Email de aceptación — el pedido entra en cocina."""
    if not ped.get("email"):
        return False
    nombre = ped.get("nombre", "")
    tabla = _tabla_pedido(ped, items, cfg)
    contenido = f"""
      <p style="font-size:16px;color:#3D1C0A;margin:0 0 16px;">Hola <strong>{nombre}</strong>,</p>
      <p style="font-size:15px;color:#5C4033;line-height:1.7;margin:0 0 20px;">Tu pedido en <strong>Vietnamito</strong> ha sido <strong style="color:#2E7D32;">aceptado</strong> y lo estamos preparando.</p>
      {tabla}
      <p style="font-size:13px;color:#7A6055;line-height:1.7;margin:16px 0 0;">Te esperamos a la hora de recogida indicada. Para cualquier cambio, responde a este email o llámanos al <strong>+34 711 216 862</strong>.</p>"""
    html = _html_base("Pedido aceptado ✓", f"Recogida: {ped.get('hora_recogida','')}", contenido)
    return _resend_send(ped["email"], f"✓ Pedido aceptado — Vietnamito #{ped.get('id','')}", html)


def enviar_email_pedido_rechazado(ped, items, cfg=None):
    """Email cuando se rechaza el pedido."""
    if not ped.get("email"):
        return False
    nombre = ped.get("nombre", "")
    tabla = _tabla_pedido(ped, items, cfg)
    contenido = f"""
      <p style="font-size:16px;color:#3D1C0A;margin:0 0 16px;">Hola <strong>{nombre}</strong>,</p>
      <p style="font-size:15px;color:#5C4033;line-height:1.7;margin:0 0 20px;">Lo sentimos mucho, pero no podemos atender tu pedido en este momento. Puede ser por falta de stock, exceso de demanda en esta franja horaria, o porque la hora de recogida no es viable.</p>
      {tabla}
      <p style="font-size:15px;color:#5C4033;line-height:1.7;margin:0 0 20px;">Esperamos verte pronto en el restaurante o que vuelvas a hacer un pedido más adelante. Si quieres, llámanos al <strong>+34 711 216 862</strong> y vemos qué podemos hacer.</p>"""
    html = _html_base("Pedido no aceptado", "Disculpa las molestias", contenido)
    return _resend_send(ped["email"], f"Pedido no aceptado — Vietnamito #{ped.get('id','')}", html)


def enviar_email_pedido_listo(ped, items, cfg=None):
    """Email cuando el pedido pasa a estado listo."""
    if not ped.get("email"):
        return False
    nombre = ped.get("nombre", "")
    tabla = _tabla_pedido(ped, items, cfg)
    contenido = f"""
      <p style="font-size:16px;color:#3D1C0A;margin:0 0 16px;">Hola <strong>{nombre}</strong>,</p>
      <p style="font-size:15px;color:#5C4033;line-height:1.7;margin:0 0 20px;">¡Tu pedido en <strong>Vietnamito</strong> está <strong style="color:#2E7D32;">listo para recoger</strong>! 🥖</p>
      {tabla}
      <p style="font-size:15px;color:#5C4033;line-height:1.7;margin:0 0 20px;">Te esperamos en <strong>Carrer Berlín 64, Barcelona</strong>. Si necesitas algo, llámanos al <strong>+34 711 216 862</strong>.</p>"""
    html = _html_base("¡Tu pedido está listo! 🥖", "Ven a recogerlo cuando quieras", contenido)
    return _resend_send(ped["email"], f"🥖 Pedido listo para recoger — Vietnamito #{ped.get('id','')}", html)


def enviar_email_pedido_cancelado(ped, items, cfg=None):
    """Email cuando se cancela un pedido ya aceptado."""
    if not ped.get("email"):
        return False
    nombre = ped.get("nombre", "")
    tabla = _tabla_pedido(ped, items, cfg)
    contenido = f"""
      <p style="font-size:16px;color:#3D1C0A;margin:0 0 16px;">Hola <strong>{nombre}</strong>,</p>
      <p style="font-size:15px;color:#5C4033;line-height:1.7;margin:0 0 20px;">Tu pedido en <strong>Vietnamito</strong> ha sido <strong style="color:#C62828;">cancelado</strong>.</p>
      {tabla}
      <p style="font-size:15px;color:#5C4033;line-height:1.7;margin:0 0 20px;">Lo sentimos mucho. Para más información, responde a este email o llámanos al <strong>+34 711 216 862</strong>.</p>"""
    html = _html_base("Pedido cancelado", "", contenido)
    return _resend_send(ped["email"], f"Pedido cancelado — Vietnamito #{ped.get('id','')}", html)



SUPABASE_URL = "https://rwtpjqvgiiuvniixqapu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ3dHBqcXZnaWl1dm5paXhxYXB1Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzEzMjIyMywiZXhwIjoyMDkyNzA4MjIzfQ.GH-3IsaWLUbivHzkjjNmC3Vwg1V5gcaXZx06wom8TB4"

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

def detect_format(lines):
    """Detecta si el CSV es de Epos Now o del nuevo POS."""
    header = lines[0].lower()
    if "id documento" in header or "forma de pago" in header or "id\tdocumento" in header:
        return "nuevo"
    return "epos"

def parse_csv_epos(lines):
    """Parser para Epos Now — una fila por franja horaria."""
    sep = ";"
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
                "forma_pago": None,
                "id_ticket": None,
            })
        except:
            continue
    return rows

def parse_csv_nuevo(lines):
    """Parser para nuevo POS — una fila por ticket individual. Soporta CSV (con comillas), TSV y SCSV."""
    from datetime import timezone
    import re, csv, io

    # Detectar separador — puede ser tab, coma o punto y coma
    primera = lines[0]
    if "\t" in primera:
        sep = "\t"
    elif primera.count(",") > primera.count(";"):
        sep = ","
    else:
        sep = ";"

    rows = []
    # Usar csv.reader que maneja comillas correctamente
    reader = csv.reader(io.StringIO("\n".join(lines)), delimiter=sep, quotechar='"')
    parsed_lines = list(reader)

    for parts in parsed_lines[1:]:  # saltar cabecera
        if len(parts) < 6:
            continue
        try:
            id_ticket = parts[0].strip()
            if not id_ticket:
                continue
            forma_pago = parts[1].strip()
            # Total: puede venir como "6,00" o "6.00" o "6"
            val_str = parts[2].strip().replace(",", ".")
            val = float(val_str)
            if val <= 0:
                # Ignorar líneas con total 0 o negativo (abonos/devoluciones, vacías)
                continue
            fecha_str = parts[5].strip()
            # Parse ISO 8601: 2026-06-07T11:48:34+02:00
            m = re.match(r'(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}:\d{2})', fecha_str)
            if not m:
                continue
            dt = datetime.strptime(f"{m.group(1)} {m.group(2)}", "%Y-%m-%d %H:%M:%S")
            rows.append({
                "fecha": dt.strftime("%Y-%m-%d"),
                "hora": dt.hour,
                "dow": dt.weekday(),
                "valor": val,
                "ntrans": 1,
                "items": 0,
                "forma_pago": forma_pago,
                "id_ticket": id_ticket,
            })
        except Exception:
            continue
    return rows

def parse_csv(file):
    content = file.read()
    try:
        text = content.decode("utf-8-sig")
    except:
        text = content.decode("latin-1")
    lines = [l for l in text.strip().split("\n") if l.strip()]
    if not lines:
        return [], "desconocido"
    fmt = detect_format(lines)
    if fmt == "nuevo":
        return parse_csv_nuevo(lines), "nuevo"
    else:
        return parse_csv_epos(lines), "epos"


def save_to_supabase(rows, fmt="epos"):
    sb = get_supabase()
    if not rows:
        return
    fechas = list(set(r["fecha"] for r in rows))

    if fmt == "epos":
        # Borra solo los registros de Epos Now (id_ticket IS NULL) para las fechas del archivo
        for fecha in fechas:
            sb.table("ventas").delete().eq("fecha", fecha).is_("id_ticket", "null").execute()
    else:
        # Borra solo los registros del nuevo POS (id_ticket IS NOT NULL) para las fechas del archivo
        for fecha in fechas:
            sb.table("ventas").delete().eq("fecha", fecha).not_.is_("id_ticket", "null").execute()
        # Dedupe en memoria: si el CSV trae el mismo ticket varias veces, conservar solo el primero
        # (también evita el error de upsert "cannot affect row a second time")
        vistos = set()
        rows_dedupe = []
        for r in rows:
            clave = (r["fecha"], r.get("id_ticket"))
            if clave in vistos:
                continue
            vistos.add(clave)
            rows_dedupe.append(r)
        rows = rows_dedupe

    # Upsert: el índice único (fecha, id_ticket) garantiza que re-subidas o re-runs
    # concurrentes de Streamlit no puedan duplicar tickets. Para filas Epos
    # (id_ticket NULL) el conflicto nunca aplica y funciona como insert normal.
    for i in range(0, len(rows), 500):
        sb.table("ventas").upsert(rows[i:i+500], on_conflict="fecha,id_ticket").execute()


@st.cache_data(ttl=60)
def load_from_supabase():
    sb = get_supabase()
    # Paginar para superar el límite de 1000 filas de PostgREST
    all_rows = []
    page_size = 1000
    offset = 0
    while True:
        res = sb.table("ventas").select("*").order("fecha", desc=False).range(offset, offset + page_size - 1).execute()
        if not res.data:
            break
        all_rows.extend(res.data)
        if len(res.data) < page_size:
            break
        offset += page_size
    if not all_rows:
        return pd.DataFrame()
    df = pd.DataFrame(all_rows)
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
        title=titulo, yaxis_title="€ ventas brutas (con IVA)", xaxis_title="Hora",
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
        ventas_vals = [avg_ventas.get(h, 0) / 1.10 * 0.75 for h in horas_comunes]
        coste_vals = [coste_hora.get(h, 0) for h in horas_comunes]
        margen_vals = [v - c for v, c in zip(ventas_vals, coste_vals)]
        margen_colors = ["#5DCAA5" if m >= 0 else "#E63946" for m in margen_vals]
        horas_labels = [f"{h}:00" for h in horas_comunes]

        fig_rent = go.Figure()
        fig_rent.add_trace(go.Bar(x=horas_labels, y=ventas_vals, name="Ventas netas promedio (sin IVA, sin coste producto)", marker_color="rgba(93,202,165,0.5)", marker_line_width=0))
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
            title="Ventas netas (sin IVA, sin coste producto) vs coste de personal — por franja horaria",
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

def _kds_recibido_badge(row):
    """Badge de acuse de recibo del KDS para un registro con kds_recibido/kds_recibido_at."""
    if row.get("kds_recibido"):
        try:
            ts = pd.Timestamp(row["kds_recibido_at"]).tz_convert("Europe/Madrid").strftime("%d/%m %H:%M")
        except Exception:
            ts = ""
        return f"📡 Recibido en KDS {ts}"
    return "🔴 NO recibido en KDS todavía"


def render_kds_online_status(sb):
    """Indicador del estado del KDS: activo (visible) / oculto (corre pero no se ve) / sin señal."""
    try:
        status = sb.table("kds_status").select("*").eq("id", 1).execute().data
        if not status:
            st.warning("⚠️ Sin datos de estado del KDS (¿tabla kds_status creada?)")
            return
        s = status[0]
        ahora = pd.Timestamp.now(tz="UTC")

        def _ts(v):
            if not v:
                return None
            t = pd.Timestamp(v)
            return t.tz_localize("UTC") if t.tzinfo is None else t

        last_seen = _ts(s.get("last_seen"))
        last_visible = _ts(s.get("last_visible"))
        seg_seen = (ahora - last_seen).total_seconds() if last_seen is not None else 999999
        seg_vis = (ahora - last_visible).total_seconds() if last_visible is not None else 999999

        UMBRAL = 120  # 2 min (heartbeat 30s + throttling en background)
        proceso_vivo = seg_seen < UMBRAL
        pantalla_activa = seg_vis < UMBRAL

        if pantalla_activa:
            st.success(f"🟢 KDS ACTIVO — visible en pantalla (último latido hace {int(seg_seen)}s)")
        elif proceso_vivo:
            mins_vis = int(seg_vis / 60)
            vis_txt = f"hace {mins_vis} min" if last_visible is not None and mins_vis < 60 else (
                last_visible.tz_convert("Europe/Madrid").strftime("%d/%m %H:%M") if last_visible is not None else "nunca")
            st.warning(f"🟡 KDS OCULTO — la app corre pero NO está en pantalla (última vez visible: {vis_txt}). "
                       f"Pantalla dormida, otra app delante o minimizado. Nadie ve los pedidos ni oirá las alarmas.")
        else:
            mins_seen = int(seg_seen / 60)
            if mins_seen < 60:
                st.error(f"🔴 KDS SIN SEÑAL — ningún latido desde hace {mins_seen} min. App cerrada, tablet apagada o sin WiFi.")
            else:
                seen_txt = last_seen.tz_convert("Europe/Madrid").strftime("%d/%m %H:%M") if last_seen is not None else "nunca"
                st.error(f"🔴 KDS SIN SEÑAL — último latido {seen_txt}. App cerrada, tablet apagada o sin WiFi.")
    except Exception:
        st.warning("⚠️ No se pudo comprobar el estado del KDS")


def render_kds_msg_tab():
    """Pestaña para enviar mensajes al KDS con alarma sonora."""
    sb_kds = get_supabase()
    st.markdown("### Enviar mensaje al KDS")
    render_kds_online_status(sb_kds)

    # Interruptor de alertas Telegram
    try:
        _ks = sb_kds.table("kds_status").select("alertas_activas").eq("id", 1).execute().data
        _alertas_on = bool(_ks[0].get("alertas_activas", True)) if _ks else True
        _nuevo = st.toggle("🔔 Avisos de Telegram si el KDS deja de estar activo", value=_alertas_on, key="kds_alertas_toggle",
                           help="Si lo desactivas, no llegarán avisos de KDS oculto/sin señal al grupo de Telegram. Las notificaciones de pedidos y reservas no se ven afectadas.")
        if _nuevo != _alertas_on:
            update_data = {"alertas_activas": _nuevo}
            if _nuevo:
                update_data["alerta_enviada"] = False  # rearmar limpio al reactivar
            sb_kds.table("kds_status").update(update_data).eq("id", 1).execute()
            st.rerun()
        if not _alertas_on:
            st.caption("🔕 Avisos de KDS silenciados — no llegará nada a Telegram aunque el KDS se caiga.")
    except Exception:
        pass
    st.caption("El mensaje aparecerá en la tablet del KDS con un sonido persistente hasta que alguien pulse 'OK, entendido'.")

    # Mensajes rápidos
    st.markdown("**Mensajes rápidos:**")
    cols_q = st.columns(4)
    quick_msgs = [
        ("⏸️ Pausar pedidos 15 min", "PAUSA · No aceptéis pedidos durante los próximos 15 minutos"),
        ("🍞 Sin pan", "¡Se ha acabado el pan! Rechazar pedidos que necesiten bocadillo"),
        ("📞 Llamar al dueño", "David quiere hablar contigo. Llámalo en cuanto puedas."),
        ("🚨 Emergencia — mira el móvil", "Emergencia · Revisa el WhatsApp o teléfono ahora"),
    ]
    for i, (label, msg) in enumerate(quick_msgs):
        if cols_q[i].button(label, key=f"qmsg_{i}", use_container_width=True):
            sb_kds.table("kds_mensajes").insert({"mensaje": msg}).execute()
            st.success(f"✅ Mensaje enviado al KDS")
            st.rerun()

    st.markdown("---")

    # Mensaje personalizado
    st.markdown("**Mensaje personalizado:**")
    # Si el flag de limpieza está activo, limpiamos ANTES de crear el widget
    if st.session_state.get("kds_msg_clear"):
        st.session_state["kds_custom_msg"] = ""
        st.session_state.pop("kds_msg_clear", None)

    custom_msg = st.text_area("Escribe el mensaje", key="kds_custom_msg", height=100, placeholder="Ej: Necesito que salgas 5 min a por hielo")
    if st.button("📤 Enviar mensaje personalizado", key="send_custom_msg", type="primary", disabled=not custom_msg.strip()):
        sb_kds.table("kds_mensajes").insert({"mensaje": custom_msg.strip()}).execute()
        st.session_state["kds_msg_clear"] = True
        st.success("✅ Mensaje enviado al KDS")
        st.rerun()

    st.markdown("---")

    # Historial de mensajes recientes
    st.markdown("**Historial reciente:**")
    hist = sb_kds.table("kds_mensajes").select("*").order("creado_at", desc=True).limit(10).execute().data or []
    if not hist:
        st.info("Aún no se ha enviado ningún mensaje.")
    else:
        for m in hist:
            icono = "✅" if m.get("atendido") else "⏳"
            estado_txt = f"atendido {pd.Timestamp(m['atendido_at']).strftime('%d/%m %H:%M')}" if m.get("atendido") else "esperando"
            recibido_txt = _kds_recibido_badge(m)
            st.markdown(f"{icono} **{pd.Timestamp(m['creado_at']).strftime('%d/%m %H:%M')}** — {m['mensaje']} · _{estado_txt}_ · {recibido_txt}")


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

    @st.cache_data(ttl=10, show_spinner=False)
    def _contar_pendientes():
        _sb = get_supabase()
        p = len((_sb.table("pedidos").select("id").eq("estado", "solicitado").execute().data or []))
        r = len((_sb.table("reservas").select("id").eq("estado", "pendiente").execute().data or []))
        return p, r

    ped_pend, res_pend = _contar_pendientes()

    # Aviso de pendientes en un slot SIEMPRE presente (st.empty) para que
    # su aparición/desaparición no remonte st.tabs y expulse al usuario de su pestaña.
    aviso_slot = st.empty()
    if ped_pend > 0 or res_pend > 0:
        avisos = []
        if ped_pend > 0:
            avisos.append(f"🛍️ {ped_pend} pedido{'s' if ped_pend != 1 else ''} esperando confirmación")
        if res_pend > 0:
            avisos.append(f"🍽️ {res_pend} reserva{'s' if res_pend != 1 else ''} pendiente{'s' if res_pend != 1 else ''}")
        aviso_slot.error("🔴 " + " · ".join(avisos))

    # Navegación principal con estado REAL (st.radio + key en session_state):
    # a diferencia de st.tabs, la sección activa NUNCA se resetea por re-runs
    # ni cambios estructurales. Además solo se renderiza la sección activa (más rápido).
    _SECCIONES = [
        "💰 Rentabilidad", "📅 Por día de semana", "🕐 Por franja horaria",
        "🌡️ Mapa de calor", "📈 Por semana", "👥 Turnos", "📋 Checklists",
        "🛍️ Pedidos", "🍽️ Reservas", "🌐 Web", "📢 KDS",
    ]
    nav = st.radio("Sección", _SECCIONES, horizontal=True, key="nav_principal", label_visibility="collapsed")
    st.markdown("")

    # ── TAB 0: Rentabilidad ─────────────────────────────────
    if nav == "💰 Rentabilidad":
        import datetime as dt_rent
        sb0 = get_supabase()

        st.markdown("### Dashboard de rentabilidad")

        with st.expander("ℹ️ ¿Cómo se calcula la rentabilidad?"):
            st.markdown("""
El cálculo sigue este orden de descuentos:

**1. Ventas brutas** → suma total facturada al cliente (IVA del 10% incluido, tal como aparece en el ticket).

**2. Ventas sin IVA** = `Ventas brutas ÷ 1.10`
El IVA del 10% **no es dinero del negocio**: lo cobras al cliente y se lo entregas a Hacienda. Solo el 90,91% del importe del ticket es ingreso real.

**3. Ventas netas** = `Ventas sin IVA × 0.75`
Asumimos un **25% de coste de producto** (materia prima, ingredientes, envases) que se descuenta del importe sin IVA. Es una aproximación estándar para fast-casual.

> **Equivalente directo:** `Ventas netas = Ventas brutas × 0.6818` (es decir, ÷1.10 ×0.75)
> Un ticket de **€10,00** → sin IVA **€9,09** → ventas netas **€6,82**

**4. Coste personal** → suma de las horas trabajadas según los turnos configurados, multiplicado por el coste/hora de cada empleado. Se calcula por franja de 30 min.

**5. Coste fijo** → costes fijos mensuales (alquiler, suministros, gestoría, etc.) divididos entre los días del mes y prorrateados por día. Configurables en la sub-pestaña 🏛️ **Costes fijos mensuales**.

**6. Margen** = `Ventas netas − Coste personal − Coste fijo`
Es lo que queda después de pagar a Hacienda, el producto, el personal y los gastos fijos. Si es positivo (verde), el negocio es rentable. Si es negativo (rojo), pierde dinero.

> 💡 Las barras "Ventas netas" en las gráficas ya tienen descontado el IVA y el coste de producto.
            """)

        rent_sub1, rent_sub_dia, rent_sub_sem, rent_sub2 = st.tabs(["📊 Análisis", "📆 Por día", "📅 Por semana", "🏛️ Costes fijos mensuales"])

        # ─── COSTES FIJOS ───
        with rent_sub2:
            st.markdown("#### Costes fijos mensuales")
            st.caption("⚠️ Introduce los importes **SIN IVA**. Estos costes se reparten proporcionalmente entre los días del mes para calcular la rentabilidad diaria real.")

            costes_res = sb0.table("costes_fijos").select("*").eq("activo", True).order("id").execute()
            costes_data = costes_res.data or []

            if costes_data:
                total_mensual = sum(float(c["importe_sin_iva"]) for c in costes_data)
                cm1, cm2 = st.columns(2)
                cm1.metric("Total mensual (sin IVA)", f"€{total_mensual:,.2f}")
                cm2.metric("Coste diario equivalente", f"€{total_mensual/30:,.2f}", help="Asumiendo 30 días/mes")

                st.markdown("##### Conceptos activos")
                for c in costes_data:
                    cc1, cc2, cc3, cc4 = st.columns([3, 2, 1, 1])
                    cc1.markdown(f"**{c['concepto']}**")
                    cc2.markdown(f"€{float(c['importe_sin_iva']):,.2f}/mes")
                    if cc3.button("✏️", key=f"edit_cf_{c['id']}"):
                        st.session_state[f"editing_cf_{c['id']}"] = True
                    if cc4.button("🗑", key=f"del_cf_{c['id']}"):
                        st.session_state[f"confirm_del_cf_{c['id']}"] = True

                    if st.session_state.get(f"confirm_del_cf_{c['id']}"):
                        st.warning(f"¿Borrar **{c['concepto']}** (€{float(c['importe_sin_iva']):,.2f}/mes)?")
                        yc, nc = st.columns(2)
                        if yc.button("✅ Sí", key=f"yes_del_cf_{c['id']}"):
                            sb0.table("costes_fijos").delete().eq("id", c["id"]).execute()
                            st.session_state.pop(f"confirm_del_cf_{c['id']}", None)
                            st.rerun()
                        if nc.button("❌ No", key=f"no_del_cf_{c['id']}"):
                            st.session_state.pop(f"confirm_del_cf_{c['id']}", None)
                            st.rerun()

                    if st.session_state.get(f"editing_cf_{c['id']}"):
                        ec1, ec2, ec3 = st.columns([3, 2, 1])
                        new_concepto = ec1.text_input("Concepto", value=c["concepto"], key=f"e_concepto_{c['id']}", label_visibility="collapsed")
                        new_importe = ec2.number_input("Importe sin IVA", value=float(c["importe_sin_iva"]), min_value=0.0, step=10.0, key=f"e_importe_{c['id']}", label_visibility="collapsed")
                        if ec3.button("💾", key=f"save_cf_{c['id']}"):
                            sb0.table("costes_fijos").update({"concepto": new_concepto, "importe_sin_iva": new_importe}).eq("id", c["id"]).execute()
                            st.session_state.pop(f"editing_cf_{c['id']}", None)
                            st.rerun()
            else:
                st.info("No hay costes fijos configurados. Añade el primero abajo.")

            st.divider()
            st.markdown("##### ➕ Añadir nuevo coste fijo")
            with st.form("nuevo_coste_fijo", clear_on_submit=True):
                nc1, nc2 = st.columns([3, 2])
                nuevo_concepto = nc1.text_input("Concepto", placeholder="Alquiler, suministros, gestoría...")
                nuevo_importe = nc2.number_input("Importe €/mes (sin IVA)", min_value=0.0, step=10.0)
                if st.form_submit_button("➕ Añadir", type="primary"):
                    if nuevo_concepto and nuevo_importe > 0:
                        sb0.table("costes_fijos").insert({"concepto": nuevo_concepto, "importe_sin_iva": nuevo_importe, "activo": True}).execute()
                        st.success(f"✅ Añadido: {nuevo_concepto} · €{nuevo_importe:,.2f}/mes")
                        st.rerun()
                    else:
                        st.error("Concepto y importe son obligatorios.")

        # ─── POR DÍA ───
        with rent_sub_dia:
            st.markdown("#### Rentabilidad por hora")
            st.caption("Selecciona un día concreto o un periodo para ver la rentabilidad agregada por franja horaria.")

            costes_fijos_d = sb0.table("costes_fijos").select("*").eq("activo", True).execute().data or []
            total_cf_mes_d = sum(float(c["importe_sin_iva"]) for c in costes_fijos_d)

            if df.empty:
                st.info("No hay datos de ventas todavía.")
            else:
                hoy_dh = hoy_madrid()
                min_fecha_d = df["fecha"].min()
                max_fecha_d = df["fecha"].max()

                periodo_dia = st.radio("Periodo:", [
                    "Día concreto", "Esta semana", "Últimos 7 días",
                    "Mes en curso", "Últimos 30 días", "Últimos 60 días",
                    "Últimos 90 días", "Todo el histórico", "Personalizado"
                ], horizontal=True, key="periodo_por_dia")

                # Determinar rango
                if periodo_dia == "Día concreto":
                    fechas_disp = sorted(df["fecha"].unique(), reverse=True)
                    fecha_concreta = st.selectbox(
                        "Selecciona el día:",
                        fechas_disp,
                        format_func=lambda f: f"{['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'][pd.Timestamp(f).weekday()]} {pd.Timestamp(f).strftime('%d/%m/%Y')}",
                        key="dia_sel_rent"
                    )
                    inicio_d = fin_d = fecha_concreta
                elif periodo_dia == "Esta semana":
                    inicio_d = hoy_dh - dt_rent.timedelta(days=hoy_dh.weekday())
                    fin_d = hoy_dh
                elif periodo_dia == "Últimos 7 días":
                    inicio_d = hoy_dh - dt_rent.timedelta(days=6)
                    fin_d = hoy_dh
                elif periodo_dia == "Mes en curso":
                    inicio_d = hoy_dh.replace(day=1)
                    fin_d = hoy_dh
                elif periodo_dia == "Últimos 30 días":
                    inicio_d = hoy_dh - dt_rent.timedelta(days=29)
                    fin_d = hoy_dh
                elif periodo_dia == "Últimos 60 días":
                    inicio_d = hoy_dh - dt_rent.timedelta(days=59)
                    fin_d = hoy_dh
                elif periodo_dia == "Últimos 90 días":
                    inicio_d = hoy_dh - dt_rent.timedelta(days=89)
                    fin_d = hoy_dh
                elif periodo_dia == "Todo el histórico":
                    inicio_d = min_fecha_d
                    fin_d = max_fecha_d
                else:  # Personalizado
                    rng_c1, rng_c2 = st.columns(2)
                    inicio_d = rng_c1.date_input("Desde:", value=max(hoy_dh - dt_rent.timedelta(days=6), min_fecha_d), min_value=min_fecha_d, max_value=max_fecha_d, key="dh_desde")
                    fin_d = rng_c2.date_input("Hasta:", value=min(hoy_dh, max_fecha_d), min_value=min_fecha_d, max_value=max_fecha_d, key="dh_hasta")

                df_periodo = df[(df["fecha"] >= inicio_d) & (df["fecha"] <= fin_d)].copy()

                if df_periodo.empty:
                    st.info("No hay ventas registradas para ese periodo.")
                else:
                    # Cargar turnos para calcular coste personal por día de la semana
                    turnos_data_d = sb0.table("turnos").select("*").execute().data or []
                    empleados_data_d = sb0.table("empleados").select("*").execute().data or []
                    emp_coste_d = {e["id"]: e["coste_hora"] for e in empleados_data_d}

                    # Días distintos con ventas en el periodo
                    dias_con_ventas = df_periodo["fecha"].unique()
                    n_dias_con_ventas = len(dias_con_ventas)

                    # Coste personal: sumar por cada día (según su día de la semana) y luego acumular por hora
                    coste_personal_hora_total = {}  # hora → coste personal acumulado en todo el periodo
                    horas_con_staff_total = set()
                    coste_personal_total = 0

                    for fd in dias_con_ventas:
                        dow_d = pd.Timestamp(fd).weekday()
                        for tr in turnos_data_d:
                            if int(tr["dia_semana"]) != dow_d:
                                continue
                            h = int(tr["slot"].split(":")[0])
                            c = emp_coste_d.get(tr["empleado_id"], 10) * 0.5
                            coste_personal_hora_total[h] = coste_personal_hora_total.get(h, 0) + c
                            horas_con_staff_total.add(h)
                            coste_personal_total += c

                    # Coste fijo: prorrateado para cada día del periodo
                    coste_fijo_total = 0
                    cf_por_hora_total = {}  # hora → coste fijo acumulado
                    if total_cf_mes_d > 0:
                        for fd in dias_con_ventas:
                            dias_en_mes_fd = pd.Timestamp(fd).days_in_month
                            cf_dia = total_cf_mes_d / dias_en_mes_fd
                            coste_fijo_total += cf_dia
                            # Repartir el coste fijo del día entre las horas con staff de ese día concreto
                            dow_d = pd.Timestamp(fd).weekday()
                            horas_staff_dia = set()
                            for tr in turnos_data_d:
                                if int(tr["dia_semana"]) == dow_d:
                                    horas_staff_dia.add(int(tr["slot"].split(":")[0]))
                            if horas_staff_dia:
                                cf_por_hora_dia = cf_dia / len(horas_staff_dia)
                                for h in horas_staff_dia:
                                    cf_por_hora_total[h] = cf_por_hora_total.get(h, 0) + cf_por_hora_dia

                    # Métricas del periodo
                    ventas_brutas_d = df_periodo["valor"].sum()
                    ventas_netas_d = ventas_brutas_d / 1.10 * 0.75
                    coste_total_d = coste_personal_total + coste_fijo_total
                    margen_d = ventas_netas_d - coste_total_d
                    n_tickets = df_periodo["ntrans"].sum() if "ntrans" in df_periodo.columns else len(df_periodo)
                    ticket_medio = ventas_brutas_d / n_tickets if n_tickets > 0 else 0

                    if inicio_d == fin_d:
                        titulo_periodo = pd.Timestamp(inicio_d).strftime('%A %d/%m/%Y')
                    else:
                        titulo_periodo = f"{pd.Timestamp(inicio_d).strftime('%d/%m/%Y')} → {pd.Timestamp(fin_d).strftime('%d/%m/%Y')} · {n_dias_con_ventas} día{'s' if n_dias_con_ventas!=1 else ''} con ventas"

                    st.markdown(f"##### Resumen — {titulo_periodo}")
                    if total_cf_mes_d > 0:
                        md1, md2, md3, md4, md5 = st.columns(5)
                        md1.metric("Ventas brutas", f"€{ventas_brutas_d:,.2f}", help="Total facturado al cliente, IVA del 10% incluido")
                        md2.metric("Ventas netas", f"€{ventas_netas_d:,.2f}", help="Sin IVA (10%) y sin coste de producto (25%)")
                        md3.metric("Coste personal", f"€{coste_personal_total:,.2f}")
                        md4.metric("Coste fijo", f"€{coste_fijo_total:,.2f}", help=f"Prorrateado proporcionalmente por días")
                        dc_md = "normal" if margen_d >= 0 else "inverse"
                        md5.metric("Margen", f"€{margen_d:,.2f}", f"{(margen_d/ventas_brutas_d*100 if ventas_brutas_d>0 else 0):.1f}% s/ventas", delta_color=dc_md)
                    else:
                        md1, md2, md3, md4 = st.columns(4)
                        md1.metric("Ventas brutas", f"€{ventas_brutas_d:,.2f}", help="Total facturado al cliente, IVA del 10% incluido")
                        md2.metric("Ventas netas", f"€{ventas_netas_d:,.2f}", help="Sin IVA (10%) y sin coste de producto (25%)")
                        md3.metric("Coste personal", f"€{coste_personal_total:,.2f}")
                        dc_md = "normal" if margen_d >= 0 else "inverse"
                        md4.metric("Margen", f"€{margen_d:,.2f}", f"{(margen_d/ventas_brutas_d*100 if ventas_brutas_d>0 else 0):.1f}% s/ventas", delta_color=dc_md)

                    extra_c1, extra_c2, extra_c3 = st.columns(3)
                    extra_c1.metric("Tickets", f"{int(n_tickets):,}")
                    extra_c2.metric("Ticket medio", f"€{ticket_medio:.2f}")
                    if n_dias_con_ventas > 1:
                        extra_c3.metric("Promedio ventas/día", f"€{ventas_brutas_d/n_dias_con_ventas:,.2f}")

                    st.divider()

                    # Gráfica por hora (agregada en todo el periodo)
                    st.markdown("##### Ventas netas por hora (sin IVA, sin coste producto) — acumulado en el periodo")
                    df_hora = df_periodo.groupby("hora").agg(
                        ventas=("valor", "sum"),
                    ).reset_index()

                    # Rellenar horas sin ventas
                    horas_completas = sorted(set(df_hora["hora"].tolist() + list(horas_con_staff_total)))
                    if horas_completas:
                        h_min, h_max = min(horas_completas), max(horas_completas)
                        full_range = pd.DataFrame({"hora": range(h_min, h_max+1)})
                        df_hora = full_range.merge(df_hora, on="hora", how="left").fillna(0)

                    df_hora["coste_personal"] = df_hora["hora"].map(lambda h: round(coste_personal_hora_total.get(h, 0), 2))
                    df_hora["coste_fijo"] = df_hora["hora"].map(lambda h: round(cf_por_hora_total.get(h, 0), 2))
                    df_hora["ventas_netas"] = (df_hora["ventas"] / 1.10 * 0.75).round(2)
                    # Margen por hora SIN coste fijo (el reparto por horas no es significativo)
                    df_hora["margen"] = (df_hora["ventas_netas"] - df_hora["coste_personal"]).round(2)
                    df_hora["label"] = df_hora["hora"].astype(int).astype(str) + "h"

                    df_hora["break_even"] = (df_hora["coste_personal"] + df_hora["coste_fijo"]).round(2)

                    fig_h = go.Figure()
                    fig_h.add_trace(go.Bar(x=df_hora["label"], y=df_hora["ventas_netas"], name="Ventas netas (sin IVA, sin coste producto)", marker_color="rgba(93,202,165,0.7)", marker_line_width=0, text=[f"€{v:.2f}" if v>0 else "" for v in df_hora["ventas_netas"]], textposition="outside"))
                    fig_h.add_trace(go.Bar(x=df_hora["label"], y=df_hora["coste_personal"], name="Coste personal", marker_color="rgba(230,57,70,0.6)", marker_line_width=0))
                    fig_h.add_trace(go.Scatter(x=df_hora["label"], y=df_hora["margen"], name="Margen", mode="lines+markers", line=dict(color="#F4A261", width=2.5), marker=dict(size=8, color=["#5DCAA5" if v>=0 else "#E63946" for v in df_hora["margen"]])))
                    fig_h.add_hline(y=0, line_dash="dot", line_color="rgba(128,128,128,0.4)")
                    fig_h.update_layout(
                        title=f"Ventas netas vs coste de personal por hora — {titulo_periodo}",
                        yaxis_title="€", barmode="group",
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                        yaxis=dict(gridcolor="rgba(128,128,128,0.15)", zeroline=False),
                        xaxis=dict(showgrid=False),
                        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="left", x=0),
                        height=440, margin=dict(t=50, b=80),
                    )
                    st.plotly_chart(fig_h, use_container_width=True)

                    # Tabla detalle
                    with st.expander("Ver tabla horaria"):
                        tabla_h = df_hora[["label","ventas","ventas_netas","coste_personal","margen"]].copy()
                        tabla_h.columns = ["Hora","Ventas brutas (€)","Ventas netas (€)","Coste personal (€)","Margen (€)"]
                        st.dataframe(tabla_h, hide_index=True, use_container_width=True)

                    # ─── GRÁFICA POR DÍA DE LA SEMANA × FRANJA ───
                    st.divider()
                    st.markdown("##### Margen por día de la semana — mañana vs tarde")
                    st.caption("Mañana: 9h–17h · Tarde: 18h–23h. Aquí sí se incluye el coste fijo prorrateado.")

                    # Para cada día con ventas en el periodo, calcular margen mañana/tarde
                    # incluyendo coste personal real (turnos de ese dow) + coste fijo del día
                    dow_data = {dow: {"ventas_m": 0, "ventas_t": 0, "coste_personal_m": 0, "coste_personal_t": 0, "coste_fijo_m": 0, "coste_fijo_t": 0, "n_dias": 0} for dow in range(7)}

                    df_periodo_copy = df_periodo.copy()
                    df_periodo_copy["dow_calc"] = pd.to_datetime(df_periodo_copy["fecha"]).dt.weekday

                    # Ventas por día y franja
                    for fd in dias_con_ventas:
                        dow_d = pd.Timestamp(fd).weekday()
                        df_d = df_periodo_copy[df_periodo_copy["fecha"] == fd]
                        ventas_m_d = df_d[(df_d["hora"] >= 9) & (df_d["hora"] <= 17)]["valor"].sum()
                        ventas_t_d = df_d[(df_d["hora"] >= 18) & (df_d["hora"] <= 23)]["valor"].sum()
                        dow_data[dow_d]["ventas_m"] += ventas_m_d
                        dow_data[dow_d]["ventas_t"] += ventas_t_d
                        dow_data[dow_d]["n_dias"] += 1

                        # Coste personal de ese día por franja
                        for tr in turnos_data_d:
                            if int(tr["dia_semana"]) != dow_d:
                                continue
                            h = int(tr["slot"].split(":")[0])
                            c = emp_coste_d.get(tr["empleado_id"], 10) * 0.5
                            if 9 <= h <= 17:
                                dow_data[dow_d]["coste_personal_m"] += c
                            elif 18 <= h <= 23:
                                dow_data[dow_d]["coste_personal_t"] += c

                        # Coste fijo de ese día — repartir 50/50 entre mañana y tarde si ambas tienen actividad,
                        # o todo a la franja activa
                        if total_cf_mes_d > 0:
                            dias_en_mes_fd = pd.Timestamp(fd).days_in_month
                            cf_dia = total_cf_mes_d / dias_en_mes_fd
                            tiene_m = ventas_m_d > 0 or dow_data[dow_d]["coste_personal_m"] > 0
                            tiene_t = ventas_t_d > 0 or dow_data[dow_d]["coste_personal_t"] > 0
                            if tiene_m and tiene_t:
                                dow_data[dow_d]["coste_fijo_m"] += cf_dia / 2
                                dow_data[dow_d]["coste_fijo_t"] += cf_dia / 2
                            elif tiene_m:
                                dow_data[dow_d]["coste_fijo_m"] += cf_dia
                            elif tiene_t:
                                dow_data[dow_d]["coste_fijo_t"] += cf_dia
                            else:
                                dow_data[dow_d]["coste_fijo_m"] += cf_dia / 2
                                dow_data[dow_d]["coste_fijo_t"] += cf_dia / 2

                    dias_es = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo']
                    margen_manana = []
                    margen_tarde = []
                    labels_dow = []
                    for dow in range(7):
                        d = dow_data[dow]
                        margen_m = (d["ventas_m"] / 1.10 * 0.75) - d["coste_personal_m"] - d["coste_fijo_m"]
                        margen_t = (d["ventas_t"] / 1.10 * 0.75) - d["coste_personal_t"] - d["coste_fijo_t"]
                        margen_manana.append(round(margen_m, 2))
                        margen_tarde.append(round(margen_t, 2))
                        label_d = dias_es[dow]
                        if d["n_dias"] > 0:
                            label_d += f"<br><span style='font-size:10px;color:#888'>({d['n_dias']}d)</span>"
                        labels_dow.append(label_d)

                    fig_dow = go.Figure()
                    fig_dow.add_trace(go.Bar(
                        x=labels_dow, y=margen_manana, name="Mañana (9h-17h)",
                        marker_color=["rgba(93,202,165,0.85)" if v >= 0 else "rgba(230,57,70,0.85)" for v in margen_manana],
                        marker_line_width=0,
                        text=[f"€{v:+.0f}" if v != 0 else "" for v in margen_manana], textposition="outside",
                    ))
                    fig_dow.add_trace(go.Bar(
                        x=labels_dow, y=margen_tarde, name="Tarde (18h-23h)",
                        marker_color=["rgba(244,162,97,0.85)" if v >= 0 else "rgba(230,57,70,0.55)" for v in margen_tarde],
                        marker_line_width=0,
                        text=[f"€{v:+.0f}" if v != 0 else "" for v in margen_tarde], textposition="outside",
                    ))
                    fig_dow.add_hline(y=0, line_dash="dot", line_color="rgba(128,128,128,0.5)")
                    fig_dow.update_layout(
                        title=f"Margen por día de la semana × franja — {titulo_periodo}",
                        yaxis_title="€ margen", barmode="group",
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                        yaxis=dict(gridcolor="rgba(128,128,128,0.15)", zeroline=False),
                        xaxis=dict(showgrid=False),
                        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="left", x=0),
                        height=440, margin=dict(t=50, b=80),
                    )
                    st.plotly_chart(fig_dow, use_container_width=True)

                    with st.expander("Ver tabla por día de la semana"):
                        tabla_dow_rows = []
                        for dow in range(7):
                            d = dow_data[dow]
                            tabla_dow_rows.append({
                                "Día": dias_es[dow],
                                "Días en periodo": d["n_dias"],
                                "Margen mañana (€)": round((d["ventas_m"] / 1.10 * 0.75) - d["coste_personal_m"] - d["coste_fijo_m"], 2),
                                "Margen tarde (€)": round((d["ventas_t"] / 1.10 * 0.75) - d["coste_personal_t"] - d["coste_fijo_t"], 2),
                                "Margen total (€)": round(margen_manana[dow] + margen_tarde[dow], 2),
                            })
                        st.dataframe(pd.DataFrame(tabla_dow_rows), hide_index=True, use_container_width=True)

        # ─── POR SEMANA ───
        with rent_sub_sem:
            st.markdown("#### Evolución semanal del margen")
            st.caption("Semanas completas de lunes a domingo. Ventas netas = brutas ÷ 1,10 (IVA) × 75% (coste producto).")

            _cf_sem_data = sb0.table("costes_fijos").select("*").eq("activo", True).execute().data or []
            _total_cf_mes = sum(float(c["importe_sin_iva"]) for c in _cf_sem_data)
            _turnos_sem = sb0.table("turnos").select("*").execute().data or []
            _emps_sem = sb0.table("empleados").select("*").execute().data or []
            _emp_coste_sem = {e["id"]: e["coste_hora"] for e in _emps_sem}
            _coste_dow_sem = {}
            for _tr in _turnos_sem:
                _d = int(_tr["dia_semana"])
                _coste_dow_sem[_d] = _coste_dow_sem.get(_d, 0) + _emp_coste_sem.get(_tr["empleado_id"], 10) * 0.5

            _hoy_s = hoy_madrid()
            _lunes_actual = _hoy_s - dt_rent.timedelta(days=_hoy_s.weekday())

            _sel_sem = st.selectbox(
                "Periodo:",
                ["Semana en curso", "Última semana completa", "Últimas 2 semanas",
                 "Últimas 4 semanas", "Últimas 8 semanas", "Últimas 12 semanas", "Personalizado…"],
                index=3, key="rent_sem_periodo")

            if _sel_sem == "Semana en curso":
                _n_sem = 0
                _incluir_curso = True
            else:
                if _sel_sem == "Última semana completa":
                    _n_sem = 1
                elif _sel_sem.startswith("Últimas"):
                    _n_sem = int(_sel_sem.split()[1])
                else:
                    _n_sem = int(st.number_input("Número de semanas completas:", min_value=1, max_value=52, value=6, key="rent_sem_n"))
                _incluir_curso = st.checkbox("➕ Incluir también la semana en curso (parcial)", value=False, key="rent_sem_inc")

            if _n_sem == 0:
                _inicio_sem = _lunes_actual
                _fin_sem = _hoy_s
            else:
                _inicio_sem = _lunes_actual - dt_rent.timedelta(days=7 * _n_sem)
                _fin_sem = _hoy_s if _incluir_curso else (_lunes_actual - dt_rent.timedelta(days=1))

            df_sem = df[(df["fecha"] >= _inicio_sem) & (df["fecha"] <= _fin_sem)].copy()

            if df_sem.empty:
                st.warning("No hay datos de ventas en ese rango de semanas.")
            else:
                df_sem["fecha_ts"] = pd.to_datetime(df_sem["fecha"])
                df_sem["lunes"] = df_sem["fecha_ts"] - pd.to_timedelta(df_sem["fecha_ts"].dt.weekday, unit="D")
                df_sem["semana"] = df_sem["lunes"].dt.strftime("%Y-%m-%d")

                sem_df = df_sem.groupby("semana")["valor"].sum().reset_index()
                sem_df.columns = ["semana", "ventas_brutas"]
                sem_df["ventas_netas"] = (sem_df["ventas_brutas"] / 1.10 * 0.75).round(2)

                def _coste_personal_semana(sem_str):
                    _lun = pd.Timestamp(sem_str).date()
                    _tot = 0
                    for _dd in range(7):
                        _fd = _lun + dt_rent.timedelta(days=_dd)
                        if _fd > _fin_sem:
                            break
                        if df_sem[df_sem["fecha"] == _fd]["valor"].sum() > 0:
                            _tot += _coste_dow_sem.get(_dd, 0)
                    return round(_tot, 2)
                sem_df["coste_personal"] = sem_df["semana"].apply(_coste_personal_semana)

                def _coste_fijo_semana(sem_str):
                    if _total_cf_mes == 0:
                        return 0
                    _lun = pd.Timestamp(sem_str).date()
                    _cf = 0
                    for _dd in range(7):
                        _fd = _lun + dt_rent.timedelta(days=_dd)
                        if _fd > _fin_sem:
                            break
                        _cf += _total_cf_mes / pd.Timestamp(_fd).days_in_month
                    return round(_cf, 2)
                sem_df["coste_fijo"] = sem_df["semana"].apply(_coste_fijo_semana)
                sem_df["coste"] = sem_df["coste_personal"] + sem_df["coste_fijo"]
                sem_df["margen"] = (sem_df["ventas_netas"] - sem_df["coste"]).round(2)

                def _label_semana(sem_str):
                    _lun = pd.Timestamp(sem_str).date()
                    _dom = _lun + dt_rent.timedelta(days=6)
                    _lbl = f"{_lun.strftime('%d/%m')}–{_dom.strftime('%d/%m')}"
                    if _lun == _lunes_actual:
                        _lbl += " ⏳en curso"
                    return _lbl
                sem_df["label"] = sem_df["semana"].apply(_label_semana)
                sem_df = sem_df.sort_values("semana")

                # Métricas del rango
                _mc1, _mc2, _mc3, _mc4 = st.columns(4)
                _mc1.metric("Ventas brutas", f"€{sem_df['ventas_brutas'].sum():,.2f}")
                _mc2.metric("Ventas netas", f"€{sem_df['ventas_netas'].sum():,.2f}")
                _mc3.metric("Costes (personal + fijo)", f"€{sem_df['coste'].sum():,.2f}")
                _mc4.metric("Margen", f"€{sem_df['margen'].sum():,.2f}")

                fig_sem = go.Figure()
                fig_sem.add_trace(go.Bar(x=sem_df["label"], y=sem_df["ventas_netas"], name="Ventas netas (sin IVA, sin coste producto)", marker_color="rgba(93,202,165,0.6)", marker_line_width=0))
                fig_sem.add_trace(go.Bar(x=sem_df["label"], y=sem_df["coste_personal"], name="Coste personal", marker_color="rgba(230,57,70,0.6)", marker_line_width=0))
                if _total_cf_mes > 0:
                    fig_sem.add_trace(go.Bar(x=sem_df["label"], y=sem_df["coste_fijo"], name="Coste fijo", marker_color="rgba(168,162,158,0.6)", marker_line_width=0))
                fig_sem.add_trace(go.Scatter(x=sem_df["label"], y=sem_df["coste"], name="Break-even semanal (personal + fijo)", mode="lines", line=dict(color="#8B5CF6", width=2, dash="dash"), hovertemplate="Break-even: €%{y:.2f}<extra></extra>"))
                fig_sem.add_trace(go.Scatter(x=sem_df["label"], y=sem_df["margen"], name="Margen", mode="lines+markers+text", line=dict(color="#F4A261", width=2), marker=dict(size=8, color=["#5DCAA5" if v >= 0 else "#E63946" for v in sem_df["margen"]]), text=[f"€{v:+.0f}" for v in sem_df["margen"]], textposition="top center", textfont=dict(size=11)))
                fig_sem.add_hline(y=0, line_dash="dot", line_color="rgba(128,128,128,0.4)")
                fig_sem.update_layout(title="Ventas netas vs costes por semana — línea morada: break-even semanal", yaxis_title="€", barmode="group", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", yaxis=dict(gridcolor="rgba(128,128,128,0.15)", zeroline=False), xaxis=dict(showgrid=False), legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="left", x=0), height=420, margin=dict(t=50, b=80))
                st.plotly_chart(fig_sem, use_container_width=True)

        # ─── ANÁLISIS ───
        with rent_sub1:
            # Cargar costes fijos para usar en los cálculos
            costes_fijos_data = sb0.table("costes_fijos").select("*").eq("activo", True).execute().data or []
            total_costes_fijos_mes = sum(float(c["importe_sin_iva"]) for c in costes_fijos_data)
            coste_fijo_dia = total_costes_fijos_mes / 30  # promedio diario

            if total_costes_fijos_mes > 0:
                st.caption(f"💡 Costes fijos mensuales configurados: **€{total_costes_fijos_mes:,.2f}** (~€{coste_fijo_dia:,.2f}/día)")

            # Periodo selector
            periodo = st.radio("Periodo:", [
                "Semana en curso", "Últimos 7 días",
                "Mes en curso", "Últimos 30 días",
                "Últimos 90 días", "Total registrado"
            ], horizontal=True, key="rent_periodo")

            hoy = hoy_madrid()
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

                # Filtrar ventas solo en horas con staff (solo para mostrar en gráficas detalladas)
                df_rent["dow"] = pd.to_datetime(df_rent["fecha"]).dt.weekday
                df_rent_staff = df_rent[df_rent.apply(
                    lambda r: (int(r["dow"]), int(r["hora"])) in horas_con_staff, axis=1
                )].copy()

                # Calcular días únicos en el periodo para escalar coste semanal
                n_dias = (fin - inicio).days + 1
                n_semanas = n_dias / 7

                # Días reales abiertos por dow (días con al menos una venta) — usar TODAS las ventas
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

                # Ventas brutas — TODAS las ventas del periodo (no filtramos por staff)
                ventas_brutas = df_rent["valor"].sum()

                # Ventas netas (sin IVA, sin coste producto)
                ventas_netas = ventas_brutas / 1.10 * 0.75

                # Margen final
                # Coste fijo prorrateado para el periodo
                coste_fijo_periodo = 0
                if total_costes_fijos_mes > 0:
                    current = inicio
                    while current <= fin:
                        coste_fijo_periodo += total_costes_fijos_mes / pd.Timestamp(current).days_in_month
                        current = current + dt_rent.timedelta(days=1)

                coste_total_periodo = coste_periodo + coste_fijo_periodo
                margen = ventas_netas - coste_total_periodo
                margen_pct = (margen / ventas_brutas * 100) if ventas_brutas > 0 else 0

                # Días con ventas — usar TODAS las ventas
                dias_con_datos = df_rent[df_rent["valor"] > 0]["fecha"].nunique()

                # Métricas principales
                st.markdown(f"**{inicio.strftime('%d/%m/%Y')} → {fin.strftime('%d/%m/%Y')}** · {dias_con_datos} días con ventas · {n_dias} días en periodo")
                st.markdown("")

                if total_costes_fijos_mes > 0:
                    col1, col2, col3, col4, col5 = st.columns(5)
                    col1.metric("Ventas brutas", f"€{ventas_brutas:,.2f}", help="Total facturado al cliente, IVA del 10% incluido")
                    col2.metric("Ventas netas", f"€{ventas_netas:,.2f}", help="Sin IVA (10%) y sin coste de producto (25%)")
                    col3.metric("Coste personal", f"€{coste_periodo:,.2f}", help="Según turnos y costes actuales")
                    col4.metric("Coste fijo", f"€{coste_fijo_periodo:,.2f}", help=f"€{total_costes_fijos_mes:,.2f}/mes prorrateado")
                    delta_color = "normal" if margen >= 0 else "inverse"
                    col5.metric("Margen", f"€{margen:,.2f}", f"{margen_pct:.1f}% s/ventas", delta_color=delta_color)
                else:
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Ventas brutas", f"€{ventas_brutas:,.2f}", help="Total facturado al cliente, IVA del 10% incluido")
                    col2.metric("Ventas netas", f"€{ventas_netas:,.2f}", help="Sin IVA (10%) y sin coste de producto (25%)")
                    col3.metric("Coste personal", f"€{coste_periodo:,.2f}", help="Basado en turnos y costes actuales")
                    delta_color = "normal" if margen >= 0 else "inverse"
                    col4.metric("Margen", f"€{margen:,.2f}", f"{margen_pct:.1f}% s/ventas", delta_color=delta_color)

                st.markdown("")

                # Semáforo visual
                if margen > 0:
                    st.success(f"✅ **Rentable** — €{margen:,.2f} de beneficio en el periodo ({margen_pct:.1f}% sobre ventas brutas)")
                else:
                    st.error(f"🔴 **Pérdidas** — €{abs(margen):,.2f} de déficit en el periodo ({margen_pct:.1f}% sobre ventas brutas)")

                st.divider()

                # Desglose por día de la semana
                st.markdown("#### Desglose por día de la semana")
                st.caption("Ventas brutas con IVA, ventas netas sin IVA y sin coste producto. Coste personal = coste diario × días reales abiertos ese dow en el periodo.")

                rows_dow = []
                suma_ventas_brutas_dow = 0
                suma_coste_personal_dow = 0
                for dow_idx in range(7):
                    # Ventas de ese dow en el periodo (TODAS, no solo horas con staff)
                    df_dow = df_rent[df_rent["dow"] == dow_idx]
                    v_brutas = df_dow["valor"].sum()
                    v_netas = v_brutas / 1.10 * 0.75

                    # Coste personal ese día: coste/día × días reales abiertos ese dow
                    coste_dia_sem = coste_dia_por_dow.get(dow_idx, 0)
                    n_dias_dow_abiertos = dias_abiertos_por_dow.get(dow_idx, 0)
                    coste_dia_periodo = coste_dia_sem * n_dias_dow_abiertos

                    margen_dia = v_netas - coste_dia_periodo
                    n_dias_dow = df_dow[df_dow["valor"] > 0]["fecha"].nunique()

                    suma_ventas_brutas_dow += v_brutas
                    suma_coste_personal_dow += coste_dia_periodo

                    rows_dow.append({
                        "Día": DIAS[dow_idx],
                        "Días c/ventas": n_dias_dow,
                        "Ventas brutas": f"€{v_brutas:,.2f}",
                        "Ventas netas": f"€{v_netas:,.2f}",
                        "Coste personal": f"€{coste_dia_periodo:,.2f}",
                        "Margen": f"€{margen_dia:,.2f}",
                        "✓": "✅" if margen_dia >= 0 else "🔴"
                    })

                st.dataframe(pd.DataFrame(rows_dow), hide_index=True, use_container_width=True)

                # Aviso de consistencia: la suma debería cuadrar con los totales superiores
                if abs(suma_ventas_brutas_dow - ventas_brutas) > 0.5:
                    st.warning(f"⚠️ Suma desglose dow ventas: €{suma_ventas_brutas_dow:,.2f} vs total: €{ventas_brutas:,.2f}")
                if abs(suma_coste_personal_dow - coste_periodo) > 0.5:
                    st.warning(f"⚠️ Suma desglose dow coste personal: €{suma_coste_personal_dow:,.2f} vs total: €{coste_periodo:,.2f}")

                st.divider()

                # ── GRÁFICA DIARIA ──
                st.markdown("#### Rentabilidad por día")
                st.caption("Ventas netas = ventas brutas × 75%. Coste = según turnos actuales. Solo días con ventas.")

                hoy_d = hoy_madrid()
                d7_ago = hoy_d - dt_rent.timedelta(days=6)
                min_fecha = df_rent_staff["fecha"].min() if not df_rent_staff.empty else d7_ago
                max_fecha = df_rent_staff["fecha"].max() if not df_rent_staff.empty else hoy_d

                dc1, dc2 = st.columns(2)
                fecha_desde = dc1.date_input("Desde:", value=max(d7_ago, min_fecha), min_value=min_fecha, max_value=max_fecha, key="dia_desde")
                fecha_hasta = dc2.date_input("Hasta:", value=min(hoy_d, max_fecha), min_value=min_fecha, max_value=max_fecha, key="dia_hasta")

                df_dia = df_rent_staff[
                    (df_rent_staff["fecha"] >= fecha_desde) &
                    (df_rent_staff["fecha"] <= fecha_hasta)
                ].copy()

                if df_dia.empty:
                    st.info("No hay datos para ese rango de fechas.")
                else:
                    # Agrupar por día
                    dia_data = df_dia.groupby("fecha")["valor"].sum().reset_index()
                    dia_data.columns = ["fecha", "ventas_brutas"]
                    dia_data["ventas_netas"] = (dia_data["ventas_brutas"] / 1.10 * 0.75).round(2)
                    dia_data["dow"] = pd.to_datetime(dia_data["fecha"]).dt.weekday
                    dia_data["coste_personal"] = dia_data["dow"].map(lambda d: coste_dia_por_dow.get(d, 0)).round(2)
                    # Contribución diaria a costes fijos (importe_mensual / días del mes correspondiente)
                    dia_data["coste_fijo"] = pd.to_datetime(dia_data["fecha"]).apply(
                        lambda d: round(total_costes_fijos_mes / pd.Timestamp(d).days_in_month, 2)
                    )
                    dia_data["coste"] = (dia_data["coste_personal"] + dia_data["coste_fijo"]).round(2)
                    dia_data["margen"] = (dia_data["ventas_netas"] - dia_data["coste"]).round(2)
                    dia_data["label"] = pd.to_datetime(dia_data["fecha"]).dt.strftime("%a %d/%m")
                    dia_data = dia_data.sort_values("fecha")

                    fig_dia = go.Figure()
                    fig_dia.add_trace(go.Bar(
                        x=dia_data["label"], y=dia_data["ventas_netas"],
                        name="Ventas netas (sin IVA, sin coste producto)", marker_color="rgba(93,202,165,0.7)", marker_line_width=0,
                    ))
                    fig_dia.add_trace(go.Bar(
                        x=dia_data["label"], y=dia_data["coste_personal"],
                        name="Coste personal", marker_color="rgba(230,57,70,0.6)", marker_line_width=0,
                    ))
                    if total_costes_fijos_mes > 0:
                        fig_dia.add_trace(go.Bar(
                            x=dia_data["label"], y=dia_data["coste_fijo"],
                            name="Coste fijo", marker_color="rgba(168,162,158,0.6)", marker_line_width=0,
                        ))
                    fig_dia.add_trace(go.Scatter(
                        x=dia_data["label"], y=dia_data["coste"],
                        name="Break-even diario (personal + fijo)", mode="lines",
                        line=dict(color="#8B5CF6", width=2, dash="dash"),
                        hovertemplate="Break-even: €%{y:.2f}<extra></extra>",
                    ))
                    fig_dia.add_trace(go.Scatter(
                        x=dia_data["label"], y=dia_data["margen"],
                        name="Margen", mode="lines+markers+text",
                        line=dict(color="#F4A261", width=2.5),
                        marker=dict(size=9, color=["#5DCAA5" if v >= 0 else "#E63946" for v in dia_data["margen"]]),
                        text=[f"€{v:+.0f}" for v in dia_data["margen"]],
                        textposition="top center", textfont=dict(size=11),
                    ))
                    fig_dia.add_hline(y=0, line_dash="dot", line_color="rgba(128,128,128,0.4)")
                    fig_dia.update_layout(
                        title=f"Rentabilidad diaria — línea morada: break-even (personal + fijo prorrateado) — {fecha_desde.strftime('%d/%m')} → {fecha_hasta.strftime('%d/%m/%Y')}",
                        yaxis_title="€", barmode="group",
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                        yaxis=dict(gridcolor="rgba(128,128,128,0.15)", zeroline=False),
                        xaxis=dict(showgrid=False, tickangle=-30),
                        legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="left", x=0),
                        height=460, margin=dict(t=50, b=100),
                    )
                    st.plotly_chart(fig_dia, use_container_width=True)

                    # Mini tabla resumen
                    resumen_dia = dia_data[["label","ventas_netas","coste_personal","coste_fijo","coste","margen"]].copy()
                    resumen_dia.columns = ["Día","Ventas netas (€)","Coste personal (€)","Coste fijo (€)","Coste total (€)","Margen (€)"]
                    with st.expander("Ver datos"):
                        st.dataframe(resumen_dia, hide_index=True, use_container_width=True)

                st.caption("⚠️ El coste de personal es estimado basándose en la configuración de turnos actual.")

    if nav == "📅 Por día de semana":
        avg_dow = calcular_promedios_dia(df)
        labels = [DIAS[d] for d in DIAS_ORDER]
        values = [round(avg_dow.get(d, 0), 2) for d in DIAS_ORDER]
        fig = go.Figure(go.Bar(
            x=labels, y=values, marker_color=COLORS, marker_line_width=0,
            text=[f"€{v:.2f}" for v in values], textposition="outside",
        ))
        fig.update_layout(
            title="Venta media por día de la semana — ventas brutas (con IVA)", yaxis_title="€ promedio (con IVA)",
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
            title="Evolución de ventas por día de la semana — ventas brutas (con IVA)",
            yaxis_title="€ brutas (con IVA)", xaxis_title="Semana (lunes)",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(gridcolor="rgba(128,128,128,0.15)", zeroline=False),
            xaxis=dict(showgrid=False, tickangle=-30),
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="left", x=0),
            height=480, margin=dict(t=50, b=100),
        )
        st.plotly_chart(fig_evo, use_container_width=True)

    if nav == "🕐 Por franja horaria":
        import datetime as dt_franja
        fecha_min_data = df["fecha"].min()
        fecha_max_data = df["fecha"].max()
        today = hoy_madrid()

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
            boxplot_horario(df_f, f"Distribución de ventas por franja horaria — {titulo_sel} — ventas brutas (con IVA)",
                ymax=ymax_global, turnos_data=turnos_t2, empleados_data=empleados_t2, dow_filter=dow_filter_t2)

    if nav == "🌡️ Mapa de calor":
        hm = calcular_heatmap(df)
        pivot = hm.pivot(index="dow", columns="hora", values="avg").reindex(DIAS_ORDER)
        pivot.index = [DIAS[d] for d in DIAS_ORDER]
        pivot.columns = [f"{h}:00" for h in pivot.columns]
        fig3 = px.imshow(
            pivot, color_continuous_scale=[[0, "#E1F5EE"], [0.5, "#1D9E75"], [1, "#04342C"]],
            aspect="auto", text_auto=".0f", labels={"color": "€ promedio (con IVA)"},
        )
        fig3.update_layout(
            title="Venta media por día y franja horaria — ventas brutas (con IVA)",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            height=350, margin=dict(t=50, b=20), xaxis_title="Hora", yaxis_title="",
        )
        fig3.update_traces(textfont_size=11)
        st.plotly_chart(fig3, use_container_width=True)

    if nav == "📈 Por semana":
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
                title="Ventas por día de semana — comparativa semanal — ventas brutas (con IVA)",
                yaxis_title="€ brutas (con IVA)", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
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
                text=[f"€{v:.2f}" for v in avg_semana["avg_franja"]],
                textposition="top center", textfont=dict(size=11),
            ))
            fig5.update_layout(
                title="Evolución del promedio de ventas por franja horaria trabajada — ventas brutas (con IVA)",
                yaxis_title="€ promedio/franja (con IVA)", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
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
                text=[f"€{v:.2f}" for v in total_semana["valor"]], textposition="outside",
            ))
            fig6.update_layout(
                title="Total de ventas por semana — ventas brutas (con IVA)",
                yaxis_title="€ total (con IVA)", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(gridcolor="rgba(128,128,128,0.15)", zeroline=False),
                xaxis=dict(showgrid=False, tickangle=-30),
                showlegend=False, height=380, margin=dict(t=50, b=80),
            )
            st.plotly_chart(fig6, use_container_width=True)

    if nav == "👥 Turnos":
        @st.fragment
        def _frag_seccion_1():
            import datetime as dt_mod
            sb = get_supabase()

            emp_res = sb.table("empleados").select("*").order("id").execute()
            empleados = emp_res.data if emp_res.data else []

            st.markdown("### Empleados")
            st.caption("Edita nombres y coste/hora. Los cambios se guardan al pulsar el botón al final. Los turnos se eliminan automáticamente al borrar un empleado.")

            header = st.columns([3, 2, 1])
            header[0].markdown("**Nombre**")
            header[1].markdown("**€/hora**")
            header[2].markdown("**Eliminar**")

            cambios_emp = []  # acumula cambios pendientes
            for emp in empleados:
                c1, c2, c3 = st.columns([3, 2, 1])
                nuevo_nombre = c1.text_input("n", value=emp["nombre"], label_visibility="collapsed", key=f"nom_{emp['id']}")
                nuevo_coste = c2.number_input("c", value=float(emp["coste_hora"]), min_value=0.0, step=0.5, format="%.2f", label_visibility="collapsed", key=f"cos_{emp['id']}")
                # Detectar si hay cambios respecto a BBDD
                if nuevo_nombre != emp["nombre"] or float(nuevo_coste) != float(emp["coste_hora"]):
                    cambios_emp.append({"id": emp["id"], "nombre": nuevo_nombre, "coste_hora": nuevo_coste, "orig": emp["nombre"]})
                if c3.button("🗑️", key=f"delemp_{emp['id']}"):
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

            # Botón único de guardado para empleados
            st.markdown("")
            if cambios_emp:
                preview = ", ".join([f"{c['orig']}" for c in cambios_emp])
                st.info(f"📝 Cambios pendientes en: **{preview}**")
            col_save_emp, _ = st.columns([2, 5])
            if col_save_emp.button("💾 Guardar empleados", key="save_all_emp", type="primary", disabled=len(cambios_emp)==0, use_container_width=True):
                for c in cambios_emp:
                    sb.table("empleados").update({"nombre": c["nombre"], "coste_hora": c["coste_hora"]}).eq("id", c["id"]).execute()
                st.success(f"✅ {len(cambios_emp)} empleado{'s' if len(cambios_emp)!=1 else ''} guardado{'s' if len(cambios_emp)!=1 else ''}")
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
                cc1, cc2, cc3 = st.columns([2, 3, 1])
                dia_origen = cc1.selectbox("Copiar de:", [DIAS[d] for d in DIAS_ORDER], key="copy_from")
                dias_destino_sel = cc2.multiselect("Copiar a:", [DIAS[d] for d in DIAS_ORDER if DIAS[d] != dia_origen], key="copy_to")
                cc3.markdown("<br>", unsafe_allow_html=True)
                if cc3.button("📋 Copiar", key="do_copy", type="primary"):
                    if not dias_destino_sel:
                        st.warning("Selecciona al menos un día destino.")
                    else:
                        dow_origen = [d for d in DIAS_ORDER if DIAS[d] == dia_origen][0]
                        turnos_res_copy = sb.table("turnos").select("*").execute()
                        turnos_origen = [(tr["empleado_id"], tr["slot"]) for tr in (turnos_res_copy.data or []) if int(tr["dia_semana"]) == dow_origen]
                        if not turnos_origen:
                            st.warning(f"El día {dia_origen} no tiene turnos configurados.")
                        else:
                            for dia_dest_label in dias_destino_sel:
                                dow_dest = [d for d in DIAS_ORDER if DIAS[d] == dia_dest_label][0]
                                sb.table("turnos").delete().eq("dia_semana", dow_dest).execute()
                                sb.table("turnos").insert([
                                    {"empleado_id": eid, "dia_semana": dow_dest, "slot": slot}
                                    for eid, slot in turnos_origen
                                ]).execute()
                            st.success(f"✅ {len(turnos_origen)} slots del {dia_origen} copiados a: {', '.join(dias_destino_sel)}")
                            st.rerun()

            turnos_res = sb.table("turnos").select("*").execute()
            turnos_set = set()
            for tr in (turnos_res.data or []):
                turnos_set.add((tr["empleado_id"], tr["dia_semana"], tr["slot"]))

            dias_tabs = st.tabs([DIAS[d] for d in DIAS_ORDER])
            # Recolectar los edits de cada día para guardar todo de golpe al final
            ediciones_por_dow = {}
            horas_por_dow = {}

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
                    ediciones_por_dow[dow] = edited

                    horas_dia = {}
                    for _, row in edited.iterrows():
                        for eid in emp_ids:
                            col_name = emp_nombres.get(eid, f"Emp {eid}")
                            if row.get(col_name, False):
                                horas_dia[eid] = horas_dia.get(eid, 0) + 0.5
                    horas_por_dow[dow] = horas_dia
                    if any(horas_dia.values()):
                        st.markdown("**Resumen del día:**")
                        res_cols = st.columns(len(emp_ids))
                        for ei, eid in enumerate(emp_ids):
                            h = horas_dia.get(eid, 0)
                            coste = h * emp_coste.get(eid, 10)
                            res_cols[ei].metric(emp_nombres.get(eid, f"Emp {eid}"), f"{h:.1f}h", f"€{coste:.2f}")

            # ── Botón único de guardar TODOS los turnos ──
            st.divider()
            st.markdown("#### Guardar cambios en turnos")
            st.caption("Cambia los turnos en cualquier día de la semana. Cuando termines, pulsa el botón para guardar todos los cambios de una vez.")
            col_save_t, _ = st.columns([2, 4])
            if col_save_t.button("💾 Guardar TODOS los turnos", key="save_all_turnos", type="primary", use_container_width=True):
                total_insertados = 0
                for dow, edited in ediciones_por_dow.items():
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
                        total_insertados += len(to_insert)
                st.success(f"✅ {total_insertados} slots guardados en total (toda la semana)")
                st.rerun()

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

        _frag_seccion_1()
    # ── TAB 6: Checklists (admin) ────────────────────────────
    if nav == "📋 Checklists":
        @st.fragment
        def _frag_seccion_2():
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
                        with st.expander(f"**{paso['orden']}.** {paso['titulo']}"):
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

        _frag_seccion_2()
    # ── TAB 7: Pedidos ──────────────────────────────────────
    if nav == "🛍️ Pedidos":
        @st.fragment
        def _frag_seccion_3():
            import datetime as dt_mod
            sb7 = get_supabase()
            st.markdown("### Pedidos")

            # Auto-enviar email de recepción a pedidos solicitados sin email enviado
            cfg_p = sb7.table("config").select("*").execute()
            cfg_ped = {r["clave"]: r["valor"] for r in (cfg_p.data or [])}

            # ── Auto-emails: detecta cambios de estado pendientes de notificar ──
            # 1) Pedidos recién recibidos (solicitado, sin email_recibido_ok)
            nuevos_ped = sb7.table("pedidos").select("*").eq("estado","solicitado").eq("email_recibido_ok", False).execute().data or []
            # 2) Pedidos aceptados (pendiente/preparando/listo/entregado, sin email_confirmacion_ok)
            aceptados_ped = sb7.table("pedidos").select("*").in_("estado", ["pendiente","preparando","listo","entregado"]).eq("email_confirmacion_ok", False).execute().data or []
            # 2b) Pedidos en estado listo (sin email_listo_ok)
            listos_ped = sb7.table("pedidos").select("*").eq("estado","listo").eq("email_listo_ok", False).execute().data or []
            # 3) Pedidos rechazados (sin email_rechazo_ok)
            rechazados_ped = sb7.table("pedidos").select("*").eq("estado","rechazado").eq("email_rechazo_ok", False).execute().data or []
            # 4) Pedidos cancelados (sin email_cancelacion_ok)
            cancelados_ped = sb7.table("pedidos").select("*").eq("estado","cancelado").eq("email_cancelacion_ok", False).execute().data or []

            # Bulk de items para todos los pedidos que necesitan emails
            todos_ids_email = [p["id"] for p in (nuevos_ped + aceptados_ped + listos_ped + rechazados_ped + cancelados_ped)]
            items_email_por_id = {}
            if todos_ids_email:
                items_bulk_email = sb7.table("pedido_items").select("*").in_("pedido_id", todos_ids_email).execute().data or []
                for it in items_bulk_email:
                    items_email_por_id.setdefault(it["pedido_id"], []).append(it)

            emails_enviados_count = 0

            for np_ in nuevos_ped:
                if np_.get("email"):
                    items_np = items_email_por_id.get(np_["id"], [])
                    if enviar_email_pedido_recibido(np_, items_np, cfg_ped):
                        sb7.table("pedidos").update({"email_recibido_ok": True}).eq("id", np_["id"]).execute()
                        emails_enviados_count += 1
                else:
                    # sin email del cliente — marcar como "no aplica" para no reintentar
                    sb7.table("pedidos").update({"email_recibido_ok": True}).eq("id", np_["id"]).execute()

            for ap in aceptados_ped:
                if ap.get("email"):
                    items_ap = items_email_por_id.get(ap["id"], [])
                    if enviar_email_pedido_aceptado(ap, items_ap, cfg_ped):
                        sb7.table("pedidos").update({"email_confirmacion_ok": True}).eq("id", ap["id"]).execute()
                        emails_enviados_count += 1
                else:
                    sb7.table("pedidos").update({"email_confirmacion_ok": True}).eq("id", ap["id"]).execute()

            for lp in listos_ped:
                if lp.get("email"):
                    items_lp = items_email_por_id.get(lp["id"], [])
                    if enviar_email_pedido_listo(lp, items_lp, cfg_ped):
                        sb7.table("pedidos").update({"email_listo_ok": True}).eq("id", lp["id"]).execute()
                        emails_enviados_count += 1
                else:
                    sb7.table("pedidos").update({"email_listo_ok": True}).eq("id", lp["id"]).execute()

            for rp in rechazados_ped:
                if rp.get("email"):
                    items_rp = items_email_por_id.get(rp["id"], [])
                    if enviar_email_pedido_rechazado(rp, items_rp, cfg_ped):
                        sb7.table("pedidos").update({"email_rechazo_ok": True}).eq("id", rp["id"]).execute()
                        emails_enviados_count += 1
                else:
                    sb7.table("pedidos").update({"email_rechazo_ok": True}).eq("id", rp["id"]).execute()

            for cp in cancelados_ped:
                if cp.get("email"):
                    items_cp = items_email_por_id.get(cp["id"], [])
                    if enviar_email_pedido_cancelado(cp, items_cp, cfg_ped):
                        sb7.table("pedidos").update({"email_cancelacion_ok": True}).eq("id", cp["id"]).execute()
                        emails_enviados_count += 1
                else:
                    sb7.table("pedidos").update({"email_cancelacion_ok": True}).eq("id", cp["id"]).execute()

            if emails_enviados_count > 0:
                st.toast(f"📧 {emails_enviados_count} email{'s' if emails_enviados_count!=1 else ''} enviado{'s' if emails_enviados_count!=1 else ''} automáticamente")

            ped_sub1, ped_sub2, ped_sub3 = st.tabs(["📥 Solicitados", "🔥 Activos", "📋 Todos"])

            def _items_de(pedido_id, items_por_pedido):
                return items_por_pedido.get(pedido_id, [])

            def _bulk_items(pedido_ids):
                """Trae todos los items de una lista de pedido_ids en una sola query, agrupados por pedido_id."""
                if not pedido_ids:
                    return {}
                res = sb7.table("pedido_items").select("*").in_("pedido_id", pedido_ids).execute().data or []
                grupos = {}
                for it in res:
                    grupos.setdefault(it["pedido_id"], []).append(it)
                return grupos

            def _render_pedido_completo(ped, items_res):
                productos_str = ", ".join([f"{i['nombre_producto']} ×{i['cantidad']}" for i in items_res])
                c1, c2 = st.columns(2)
                c1.markdown(f"**Nombre:** {ped['nombre']}")
                c1.markdown(f"**Teléfono:** {ped['telefono']}")
                c1.markdown(f"**Email:** {ped.get('email') or '—'}")
                c1.markdown(f"**Recogida:** {ped['hora_recogida']}")
                c2.markdown(f"**Total:** €{float(ped['total']):.2f}")
                c2.markdown(f"**Estado:** {ped['estado']}")
                c2.markdown(f"**Solicitado:** {pd.Timestamp(ped['creado_at']).strftime('%d/%m/%Y %H:%M')}")
                if ped.get("notas"):
                    st.markdown(f"**Notas:** {ped['notas']}")
                st.markdown(f"**Productos:** {productos_str}")

            # ─── SOLICITADOS — aceptar/rechazar ───
            with ped_sub1:
                solicitados = sb7.table("pedidos").select("*").eq("estado","solicitado").order("creado_at", desc=True).execute().data or []
                if not solicitados:
                    st.info("No hay pedidos pendientes de aceptar.")
                else:
                    st.caption(f"{len(solicitados)} pedido{'s' if len(solicitados)!=1 else ''} esperando tu aprobación.")
                    items_bulk_s = _bulk_items([p["id"] for p in solicitados])
                    for ped in solicitados:
                        items_res = items_bulk_s.get(ped["id"], [])
                        productos_str = ", ".join([f"{i['nombre_producto']} ×{i['cantidad']}" for i in items_res])
                        with st.expander(f"🆕 #{ped['id']} · {ped['nombre']} · €{float(ped['total']):.2f} · recoger {ped['hora_recogida']} · {pd.Timestamp(ped['creado_at']).strftime('%H:%M')}", expanded=True):
                            st.caption(_kds_recibido_badge(ped))
                            _render_pedido_completo(ped, items_res)
                            st.markdown("")
                            ac1, ac2 = st.columns(2)
                            if ac1.button("✅ Aceptar pedido", key=f"acept_{ped['id']}", type="primary", use_container_width=True):
                                sb7.table("pedidos").update({"estado": "pendiente"}).eq("id", ped["id"]).execute()
                                st.success(f"✅ Pedido #{ped['id']} aceptado")
                                st.rerun()
                            if ac2.button("❌ Rechazar", key=f"rechazar_{ped['id']}", use_container_width=True):
                                st.session_state[f"confirm_rechazar_{ped['id']}"] = True
                            if st.session_state.get(f"confirm_rechazar_{ped['id']}"):
                                st.warning(f"¿Rechazar pedido de **{ped['nombre']}**? Se enviará un email automáticamente.")
                                motivo_bo = st.text_input(
                                    "✉️ Mensaje para el cliente (opcional) — se enviará tal cual como motivo del rechazo:",
                                    key=f"motivo_rechazar_{ped['id']}")
                                yc, nc = st.columns(2)
                                if yc.button("✅ Sí, rechazar", key=f"yes_rechazar_{ped['id']}"):
                                    upd = {"estado": "rechazado"}
                                    if motivo_bo.strip():
                                        upd["motivo_rechazo_tipo"] = "otro"
                                        upd["motivo_rechazo"] = motivo_bo.strip()
                                    sb7.table("pedidos").update(upd).eq("id", ped["id"]).execute()
                                    st.session_state.pop(f"confirm_rechazar_{ped['id']}", None)
                                    st.success("❌ Pedido rechazado")
                                    st.rerun()
                                if nc.button("Cancelar", key=f"no_rechazar_{ped['id']}"):
                                    st.session_state.pop(f"confirm_rechazar_{ped['id']}", None)
                                    st.rerun()

            # ─── ACTIVOS — solo ver estado + cancelar ───
            with ped_sub2:
                activos = sb7.table("pedidos").select("*").in_("estado", ["pendiente","preparando","listo"]).order("creado_at", desc=True).execute().data or []
                if not activos:
                    st.info("No hay pedidos activos en cocina.")
                else:
                    st.caption(f"{len(activos)} pedido{'s' if len(activos)!=1 else ''} en curso. El estado se gestiona desde el KDS.")
                    estado_emoji = {"pendiente":"🔴 Pendiente","preparando":"🟡 Preparando","listo":"🟢 Listo"}
                    items_bulk_a = _bulk_items([p["id"] for p in activos])
                    for ped in activos:
                        items_res = items_bulk_a.get(ped["id"], [])
                        with st.expander(f"{estado_emoji.get(ped['estado'],ped['estado'])} · #{ped['id']} · {ped['nombre']} · €{float(ped['total']):.2f} · recoger {ped['hora_recogida']}"):
                            st.caption(_kds_recibido_badge(ped))
                            _render_pedido_completo(ped, items_res)
                            st.markdown("")
                            st.caption("Para mover entre estados (pendiente → preparando → listo → entregado) usa el KDS.")
                            if st.button("🚫 Cancelar pedido", key=f"cancel_active_{ped['id']}"):
                                st.session_state[f"confirm_cancel_active_{ped['id']}"] = True
                            if st.session_state.get(f"confirm_cancel_active_{ped['id']}"):
                                st.warning(f"¿Cancelar pedido de **{ped['nombre']}**? Se enviará un email automáticamente.")
                                yc2, nc2 = st.columns(2)
                                if yc2.button("✅ Sí, cancelar", key=f"yes_cancel_active_{ped['id']}"):
                                    sb7.table("pedidos").update({"estado": "cancelado"}).eq("id", ped["id"]).execute()
                                    st.session_state.pop(f"confirm_cancel_active_{ped['id']}", None)
                                    st.success("🚫 Cancelado")
                                    st.rerun()
                                if nc2.button("No", key=f"no_cancel_active_{ped['id']}"):
                                    st.session_state.pop(f"confirm_cancel_active_{ped['id']}", None)
                                    st.rerun()

            # ─── TODOS — vista histórica con filtro ───
            with ped_sub3:
                col_filt_p, col_del_p = st.columns([3, 1])
                filtro_ped = col_filt_p.selectbox("Filtrar:", ["Todos", "Solicitados", "Pendientes", "Preparando", "Listos", "Entregados", "Cancelados", "Rechazados"], key="filtro_ped")
                filtro_map = {"Todos": None, "Esperando pago": "esperando_pago", "Solicitados": "solicitado", "Pendientes": "pendiente", "Preparando": "preparando", "Listos": "listo", "Entregados": "entregado", "Cancelados": "cancelado", "Rechazados": "rechazado"}

                if col_del_p.button("🗑️ Borrar finalizados", key="del_finalizados_ped", help="Borra cancelados, rechazados y entregados de más de 7 días"):
                    st.session_state["confirm_del_finalizados"] = True
                if st.session_state.get("confirm_del_finalizados"):
                    st.warning("¿Borrar pedidos cancelados, rechazados y entregados de más de 7 días? No se puede deshacer.")
                    df1, df2 = st.columns(2)
                    if df1.button("✅ Sí", key="yes_del_finalizados"):
                        sb7.table("pedido_items").delete().in_("pedido_id", [p["id"] for p in (sb7.table("pedidos").select("id").in_("estado",["cancelado","rechazado"]).execute().data or [])]).execute()
                        sb7.table("pedidos").delete().in_("estado", ["cancelado","rechazado"]).execute()
                        hace7 = (dt_mod.datetime.now() - dt_mod.timedelta(days=7)).isoformat()
                        old_entreg = sb7.table("pedidos").select("id").eq("estado","entregado").lt("creado_at", hace7).execute().data or []
                        if old_entreg:
                            sb7.table("pedido_items").delete().in_("pedido_id", [p["id"] for p in old_entreg]).execute()
                            sb7.table("pedidos").delete().eq("estado","entregado").lt("creado_at", hace7).execute()
                        st.session_state.pop("confirm_del_finalizados", None)
                        st.success("✅ Limpieza completada")
                        st.rerun()
                    if df2.button("❌", key="no_del_finalizados"):
                        st.session_state.pop("confirm_del_finalizados", None)
                        st.rerun()

                q = sb7.table("pedidos").select("*").order("creado_at", desc=True)
                if filtro_map[filtro_ped]:
                    q = q.eq("estado", filtro_map[filtro_ped])
                pedidos = q.limit(100).execute().data or []
            
                if not pedidos:
                    st.info("No hay pedidos con ese filtro.")
                else:
                    items_bulk_t = _bulk_items([p["id"] for p in pedidos])
                    for ped in pedidos:
                        items_res = items_bulk_t.get(ped["id"], [])
                        productos_str = ", ".join([f"{i['nombre_producto']} ×{i['cantidad']}" for i in items_res])
                        estado = ped["estado"]
                        color_map = {"esperando_pago":"💳⏳","solicitado":"🆕","pendiente":"🔴","preparando":"🟡","listo":"🟢","entregado":"✅","cancelado":"🚫","rechazado":"❌"}
                        icono = color_map.get(estado, "⚪")
                        with st.expander(f"{icono} #{ped['id']} · {ped['nombre']} · €{float(ped['total']):.2f} · {ped['hora_recogida']} · {pd.Timestamp(ped['creado_at']).strftime('%d/%m %H:%M')}"):
                            st.caption(_kds_recibido_badge(ped))
                            _render_pedido_completo(ped, items_res)
                            # Botón cancelar solo para estados activos (no para cancelado/rechazado/entregado)
                            if estado in ["solicitado", "pendiente", "preparando", "listo"]:
                                st.markdown("")
                                if st.button("🚫 Cancelar pedido", key=f"cancel_todos_{ped['id']}"):
                                    st.session_state[f"confirm_cancel_todos_{ped['id']}"] = True
                                if st.session_state.get(f"confirm_cancel_todos_{ped['id']}"):
                                    st.warning(f"¿Cancelar pedido de **{ped['nombre']}**? Se enviará un email automáticamente.")
                                    yc3, nc3 = st.columns(2)
                                    if yc3.button("✅ Sí, cancelar", key=f"yes_cancel_todos_{ped['id']}"):
                                        sb7.table("pedidos").update({"estado": "cancelado"}).eq("id", ped["id"]).execute()
                                        st.session_state.pop(f"confirm_cancel_todos_{ped['id']}", None)
                                        st.success("🚫 Cancelado")
                                        st.rerun()
                                    if nc3.button("No", key=f"no_cancel_todos_{ped['id']}"):
                                        st.session_state.pop(f"confirm_cancel_todos_{ped['id']}", None)
                                        st.rerun()

                            # Botón "Borrar sin email" — disponible en TODOS los estados
                            st.markdown("")
                            st.caption("⚠️ Uso administrativo — no notifica al cliente")
                            if st.button("🗑️ Borrar pedido (sin enviar email)", key=f"delete_silent_{ped['id']}"):
                                st.session_state[f"confirm_del_silent_{ped['id']}"] = True
                            if st.session_state.get(f"confirm_del_silent_{ped['id']}"):
                                st.error(f"⚠️ ¿Borrar el pedido de **{ped['nombre']}** (€{float(ped['total']):.2f}) SIN notificar al cliente? Esto no se puede deshacer.")
                                yds, nds = st.columns(2)
                                if yds.button("✅ Sí, borrar silenciosamente", key=f"yes_del_silent_{ped['id']}"):
                                    sb7.table("pedido_items").delete().eq("pedido_id", ped["id"]).execute()
                                    sb7.table("pedidos").delete().eq("id", ped["id"]).execute()
                                    st.session_state.pop(f"confirm_del_silent_{ped['id']}", None)
                                    st.success(f"🗑️ Pedido #{ped['id']} borrado (sin notificar)")
                                    st.rerun()
                                if nds.button("No", key=f"no_del_silent_{ped['id']}"):
                                    st.session_state.pop(f"confirm_del_silent_{ped['id']}", None)
                                    st.rerun()

        _frag_seccion_3()
    # ── TAB 8: Reservas ─────────────────────────────────────
    if nav == "🍽️ Reservas":
        @st.fragment
        def _frag_seccion_4():
            import datetime as dt_mod
            sb8 = get_supabase()
            st.markdown("### Reservas")

            # Los emails de reservas (recibida/confirmada/rechazada/cancelada) los envía
            # automáticamente la Edge Function `send-reserva-email` vía Database Webhook.
            cfg_res = sb8.table("config").select("*").execute()
            cfg_email = {r["clave"]: r["valor"] for r in (cfg_res.data or [])}

            res_subtab1, res_subtab2, res_subtab3 = st.tabs(["📆 Próximas", "🗓️ Calendario", "📋 Lista completa"])

            def _cambiar_estado_reserva(res, est, sb_ref, cfg_email_ref, key_suffix=""):
                """Helper reutilizable para cambiar estado + enviar email."""
                estado_actual = res["estado"]
                if est == estado_actual:
                    st.markdown(f"<div style='text-align:center;padding:8px;background:rgba(34,197,94,0.1);color:#22C55E;border-radius:6px;font-size:13px;'>{est.capitalize()} ✓</div>", unsafe_allow_html=True)
                    return
                if est == "cancelada":
                    if st.button("Cancelada", key=f"cancel_{key_suffix}_{res['id']}"):
                        st.session_state[f"confirm_cancel_{key_suffix}_{res['id']}"] = True
                    if st.session_state.get(f"confirm_cancel_{key_suffix}_{res['id']}"):
                        st.warning(f"¿Cancelar reserva de **{res['nombre']}**? Se enviará email al cliente.")
                        yc, nc = st.columns(2)
                        if yc.button("✅ Sí", key=f"yes_cancel_{key_suffix}_{res['id']}"):
                            sb_ref.table("reservas").update({"estado": "cancelada"}).eq("id", res["id"]).execute()
                            st.session_state.pop(f"confirm_cancel_{key_suffix}_{res['id']}", None)
                            st.success("✅ Cancelada · El email se envía automáticamente")
                            st.rerun()
                        if nc.button("❌ No", key=f"no_cancel_{key_suffix}_{res['id']}"):
                            st.session_state.pop(f"confirm_cancel_{key_suffix}_{res['id']}", None)
                            st.rerun()
                else:
                    if st.button(est.capitalize(), key=f"chg_{key_suffix}_{res['id']}_{est}"):
                        sb_ref.table("reservas").update({"estado": est}).eq("id", res["id"]).execute()
                        if est == "confirmada" and res.get("email"):
                            st.success("✅ Confirmada · El email se envía automáticamente")
                        else:
                            st.success(f"✅ → {est}")
                        st.rerun()

            # ── SUBTAB: PRÓXIMAS ──
            with res_subtab1:
                hoy_r = hoy_madrid()
                todas_res = sb8.table("reservas").select("*").neq("estado","cancelada").gte("fecha", str(hoy_r)).order("fecha").order("hora").execute().data or []

                grupos = {}
                for r in todas_res:
                    fecha_r = dt_mod.date.fromisoformat(r["fecha"])
                    dias_dif = (fecha_r - hoy_r).days
                    if dias_dif == 0:
                        label = "📅 Hoy"
                    elif dias_dif == 1:
                        label = "📅 Mañana"
                    elif dias_dif < 7:
                        dias_es = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo']
                        label = f"📅 {dias_es[fecha_r.weekday()]} {fecha_r.strftime('%d/%m')}"
                    else:
                        label = f"📅 {fecha_r.strftime('%d/%m/%Y')}"
                    grupos.setdefault((dias_dif, label), []).append(r)

                if not grupos:
                    st.info("No hay próximas reservas.")
                else:
                    for (dias_dif, label), res_grupo in sorted(grupos.items()):
                        st.markdown(f"#### {label} · {len(res_grupo)} reserva{'s' if len(res_grupo)!=1 else ''}")
                        for res in res_grupo:
                            estado = res["estado"]
                            icono = {"pendiente":"🔴","confirmada":"🟢"}.get(estado, "⚪")
                            with st.expander(f"{icono} {res['hora']} · {res['nombre']} · {res['personas']} pax"):
                                st.caption(_kds_recibido_badge(res))
                                c1, c2 = st.columns(2)
                                c1.markdown(f"**Teléfono:** {res['telefono']}")
                                c1.markdown(f"**Email:** {res.get('email') or '—'}")
                                c2.markdown(f"**Estado:** {estado}")
                                if res.get("notas"):
                                    st.markdown(f"**Notas:** {res['notas']}")
                                st.markdown("**Cambiar estado:**")
                                pc1, pc2, pc3 = st.columns(3)
                                for col, est in zip([pc1,pc2,pc3], ["pendiente","confirmada","cancelada"]):
                                    with col:
                                        _cambiar_estado_reserva(res, est, sb8, cfg_email, key_suffix="prox")
                        st.divider()

            # ── SUBTAB: CALENDARIO ──
            with res_subtab2:
                import calendar as _cal

                if "cal_res_year" not in st.session_state:
                    st.session_state.cal_res_year = hoy_madrid().year
                if "cal_res_month" not in st.session_state:
                    st.session_state.cal_res_month = hoy_madrid().month

                nc1, nc2, nc3 = st.columns([1,3,1])
                if nc1.button("◀", key="cal_prev_month"):
                    st.session_state.cal_res_month -= 1
                    if st.session_state.cal_res_month < 1:
                        st.session_state.cal_res_month = 12
                        st.session_state.cal_res_year -= 1
                    st.rerun()
                meses_es = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
                nc2.markdown(f"<h4 style='text-align:center;margin:0;'>{meses_es[st.session_state.cal_res_month-1]} {st.session_state.cal_res_year}</h4>", unsafe_allow_html=True)
                if nc3.button("▶", key="cal_next_month"):
                    st.session_state.cal_res_month += 1
                    if st.session_state.cal_res_month > 12:
                        st.session_state.cal_res_month = 1
                        st.session_state.cal_res_year += 1
                    st.rerun()

                y, m = st.session_state.cal_res_year, st.session_state.cal_res_month
                primer_dia = dt_mod.date(y, m, 1)
                ultimo_dia = dt_mod.date(y, m, _cal.monthrange(y, m)[1])

                res_mes = sb8.table("reservas").select("*").neq("estado","cancelada").gte("fecha", str(primer_dia)).lte("fecha", str(ultimo_dia)).execute().data or []
                res_por_dia = {}
                for r in res_mes:
                    res_por_dia.setdefault(r["fecha"], []).append(r)

                cal_matrix = _cal.Calendar(firstweekday=0).monthdayscalendar(y, m)
                dias_header = ['Lun','Mar','Mié','Jue','Vie','Sáb','Dom']
                hoy_str = str(hoy_madrid())

                # Construir tabla HTML completa de una vez — evita 35+ widgets de Streamlit
                html_rows = []
                header_html = "".join(f"<th style='padding:6px;font-size:11px;font-weight:600;color:#888;width:14.28%;'>{dh}</th>" for dh in dias_header)
                html_rows.append(f"<tr>{header_html}</tr>")

                for semana in cal_matrix:
                    cells = []
                    for dia in semana:
                        if dia == 0:
                            cells.append("<td style='height:64px;'></td>")
                        else:
                            fecha_str = f"{y}-{m:02d}-{dia:02d}"
                            res_dia = res_por_dia.get(fecha_str, [])
                            n_pax = sum(r["personas"] for r in res_dia)
                            es_hoy = fecha_str == hoy_str
                            bg = "rgba(216,90,48,0.18)" if es_hoy else ("rgba(34,197,94,0.10)" if res_dia else "transparent")
                            border = "2px solid #D85A30" if es_hoy else "1px solid rgba(128,128,128,0.15)"
                            badge = f"<div style='font-size:10px;color:#22C55E;font-weight:700;'>{len(res_dia)} res · {n_pax}p</div>" if res_dia else ""
                            cells.append(f"<td style='height:64px;vertical-align:top;border:{border};border-radius:6px;background:{bg};padding:4px 6px;'><div style='font-size:13px;font-weight:600;'>{dia}</div>{badge}</td>")
                    html_rows.append(f"<tr>{''.join(cells)}</tr>")

                calendar_html = "<table style='width:100%;border-collapse:separate;border-spacing:3px;table-layout:fixed;'>" + "".join(html_rows) + "</table>"
                st.markdown(calendar_html, unsafe_allow_html=True)

                # Selector simple para ver detalle de un día con reservas
                dias_con_res = sorted(res_por_dia.keys())
                if dias_con_res:
                    opciones_dia = [f"{dt_mod.date.fromisoformat(d).strftime('%A %d/%m')} ({len(res_por_dia[d])} reservas)" for d in dias_con_res]
                    sel_idx = st.selectbox("Ver detalle del día:", range(len(opciones_dia)), format_func=lambda i: opciones_dia[i], key="cal_dia_selectbox")
                    dia_sel = dias_con_res[sel_idx]
                else:
                    st.caption("No hay reservas este mes.")
                    dia_sel = None

                if dia_sel and dia_sel in res_por_dia:
                    st.divider()
                    st.markdown(f"#### Reservas del {dt_mod.date.fromisoformat(dia_sel).strftime('%d/%m/%Y')}")
                    for res in sorted(res_por_dia[dia_sel], key=lambda r: r["hora"]):
                        estado = res["estado"]
                        icono = {"pendiente":"🔴","confirmada":"🟢"}.get(estado, "⚪")
                        with st.expander(f"{icono} {res['hora']} · {res['nombre']} · {res['personas']} pax"):
                            c1, c2 = st.columns(2)
                            c1.markdown(f"**Teléfono:** {res['telefono']}")
                            c1.markdown(f"**Email:** {res.get('email') or '—'}")
                            c2.markdown(f"**Estado:** {estado}")
                            if res.get("notas"):
                                st.markdown(f"**Notas:** {res['notas']}")
                            st.markdown("**Cambiar estado:**")
                            pc1, pc2, pc3 = st.columns(3)
                            for col, est in zip([pc1,pc2,pc3], ["pendiente","confirmada","cancelada"]):
                                with col:
                                    _cambiar_estado_reserva(res, est, sb8, cfg_email, key_suffix="cal")

            # ── SUBTAB: LISTA COMPLETA ──
            with res_subtab3:
                col_filt_r, col_del_r = st.columns([3,1])
                filtro_res = col_filt_r.selectbox("Filtrar:", ["Todos", "Pendientes", "Confirmadas", "Canceladas"], key="filtro_res")
                filtro_res_map = {"Todos": None, "Pendientes": "pendiente", "Confirmadas": "confirmada", "Canceladas": "cancelada"}

                if col_del_r.button("🗑️ Borrar canceladas", key="del_cancelled_res"):
                    st.session_state["confirm_del_cancelled_res"] = True
                if st.session_state.get("confirm_del_cancelled_res"):
                    st.warning("¿Borrar todas las reservas canceladas? No se puede deshacer.")
                    dc1, dc2 = st.columns(2)
                    if dc1.button("✅ Sí, borrar", key="yes_del_cancelled_res"):
                        sb8.table("reservas").delete().eq("estado", "cancelada").execute()
                        st.session_state.pop("confirm_del_cancelled_res", None)
                        st.success("✅ Reservas canceladas eliminadas")
                        st.rerun()
                    if dc2.button("❌ Cancelar", key="no_del_cancelled_res"):
                        st.session_state.pop("confirm_del_cancelled_res", None)
                        st.rerun()

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
                                    _cambiar_estado_reserva(res, est, sb8, cfg_email, key_suffix="lista")

        _frag_seccion_4()
    # ── TAB 9: Web ──────────────────────────────────────────
    if nav == "🌐 Web":
        @st.fragment
        def _frag_seccion_5():
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

                st.markdown("##### 📅 Días bloqueados para reservas")
                st.caption("Selecciona fechas en las que no se pueden hacer reservas (festivos, cierre, etc.)")
                import json as _json
                dias_bloq_raw = cfg.get("dias_bloqueados", "[]")
                try:
                    dias_bloq_actual = _json.loads(dias_bloq_raw)
                except:
                    dias_bloq_actual = []
                dias_bloq_dates = [dt_mod.date.fromisoformat(d) for d in dias_bloq_actual if d]

                nueva_fecha = st.date_input("Añadir fecha bloqueada:", value=None, key="nueva_fecha_bloq", min_value=hoy_madrid())
                if nueva_fecha and str(nueva_fecha) not in dias_bloq_actual:
                    if st.button("➕ Añadir", key="add_fecha_bloq"):
                        dias_bloq_actual.append(str(nueva_fecha))
                        dias_bloq_actual.sort()
                        sb9.table("config").upsert({"clave": "dias_bloqueados", "valor": _json.dumps(dias_bloq_actual)}).execute()
                        st.success(f"✅ {nueva_fecha} añadida")
                        st.rerun()

                if dias_bloq_actual:
                    st.markdown("**Fechas bloqueadas:**")
                    for d in sorted(dias_bloq_actual):
                        dc1, dc2 = st.columns([4,1])
                        dc1.markdown(f"🚫 {dt_mod.date.fromisoformat(d).strftime('%A %d/%m/%Y')}")
                        if dc2.button("✕", key=f"del_bloq_{d}"):
                            dias_bloq_actual.remove(d)
                            sb9.table("config").upsert({"clave": "dias_bloqueados", "valor": _json.dumps(dias_bloq_actual)}).execute()
                            st.rerun()
                else:
                    st.caption("No hay fechas bloqueadas.")

                new_cfg["dias_bloqueados"] = cfg.get("dias_bloqueados", "[]")

                if st.button("💾 Guardar configuración", key="save_cfg", type="primary"):
                    for clave, valor in new_cfg.items():
                        sb9.table("config").upsert({"clave": clave, "valor": valor}).execute()
                    st.success("✅ Configuración guardada")
                    st.rerun()

                st.divider()
                st.markdown("#### Fotos de la web")
                st.caption("Estas fotos aparecen en la página de inicio de vietnamito.es")

                fotos_config = [
                    ("foto_hero", "🖼️ Hero principal", "Fondo grande al entrar a la web"),
                    ("foto_franja", "🖼️ Franja intermedia", "Segunda sección de la página de inicio"),
                    ("foto_split", "🖼️ Nuestro espacio", "Tercera sección, lado derecho"),
                    ("foto_reserva", "🖼️ Página de reservas", "Foto de fondo lateral en la reserva"),
                    ("foto_mural_banner", "🖼️ Banner inferior", "Justo encima del footer"),
                    ("foto_mapa", "🗺️ Mapa del local", "Mapa ilustrado que aparece debajo de los horarios"),
                ]

                import urllib.parse as _ul
                cols_foto = st.columns(2)
                for idx, (clave_foto, label_foto, desc_foto) in enumerate(fotos_config):
                    with cols_foto[idx % 2]:
                        st.markdown(f"**{label_foto}**")
                        st.caption(desc_foto)
                        url_actual = cfg.get(clave_foto, "")
                        if url_actual:
                            st.image(url_actual, use_container_width=True)
                        foto_upload = st.file_uploader(f"Subir foto", type=["jpg","jpeg","png","webp"], key=f"fup_{clave_foto}", label_visibility="collapsed")
                        if foto_upload:
                            try:
                                ext = foto_upload.name.split(".")[-1].lower()
                                fname = f"web/{clave_foto}.{ext}"
                                sb9.storage.from_("assets").upload(fname, foto_upload.read(), {"content-type": f"image/{ext}", "upsert": "true"})
                                new_url = f"{SUPABASE_URL}/storage/v1/object/public/assets/{_ul.quote(fname, safe='/')}"
                                sb9.table("config").upsert({"clave": clave_foto, "valor": new_url}).execute()
                                st.success(f"✅ Foto guardada")
                                st.rerun()
                            except Exception as e:
                                st.warning(f"Error: {e}")
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
                            e_nom = ep1.text_input("🇪🇸 Nombre:", value=prod["nombre"], key=f"en_{prod['id']}")
                            e_precio = ep2.number_input("€:", value=float(prod["precio"]), min_value=0.0, step=0.5, format="%.2f", key=f"epr_{prod['id']}")
                            e_nom_en = st.text_input("🇬🇧 Name (EN):", value=prod.get("nombre_en") or "", key=f"en_en_{prod['id']}")
                            e_nom_ca = st.text_input("🏴 Nom (CA):", value=prod.get("nombre_ca") or "", key=f"en_ca_{prod['id']}")
                            e_nom_vi = st.text_input("🇻🇳 Tên (VI):", value=prod.get("nombre_vi") or "", key=f"en_vi_{prod['id']}")
                            e_desc = st.text_area("🇪🇸 Descripción:", value=prod.get("descripcion") or "", key=f"ed_{prod['id']}", height=68)
                            e_desc_en = st.text_area("🇬🇧 Description (EN):", value=prod.get("descripcion_en") or "", key=f"ed_en_{prod['id']}", height=68)
                            e_desc_ca = st.text_area("🏴 Descripció (CA):", value=prod.get("descripcion_ca") or "", key=f"ed_ca_{prod['id']}", height=68)
                            e_desc_vi = st.text_area("🇻🇳 Mô tả (VI):", value=prod.get("descripcion_vi") or "", key=f"ed_vi_{prod['id']}", height=68)
                            e_orden = ep2.number_input("Orden:", value=int(prod.get("orden",0)), min_value=1, key=f"eord_{prod['id']}")
                            e_disp = ep1.checkbox("Disponible", value=prod.get("disponible",True), key=f"edis_{prod['id']}")

                            # Cambiar categoría
                            otras_cats = [c for c in cats_web if c["id"] != cat_obj["id"]]
                            if otras_cats:
                                st.markdown("**Mover a otra categoría:**")
                                cat_mover_opts = {c["nombre"]: c["id"] for c in otras_cats}
                                cat_mover_sel = st.selectbox("Categoría destino:", list(cat_mover_opts.keys()), key=f"cat_mover_{prod['id']}")
                                if st.button(f"↗️ Mover a {cat_mover_sel}", key=f"mover_prod_{prod['id']}"):
                                    cat_dest_id = cat_mover_opts[cat_mover_sel]
                                    # Calcular orden máximo en la categoría destino
                                    prods_dest = [p for p in prods_web if p["categoria_id"] == cat_dest_id]
                                    nuevo_orden = max((p.get("orden",0) for p in prods_dest), default=0) + 1
                                    sb9.table("productos").update({"categoria_id": cat_dest_id, "orden": nuevo_orden}).eq("id", prod["id"]).execute()
                                    st.success(f"✅ Movido a {cat_mover_sel} (orden {nuevo_orden})")
                                    st.rerun()

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
                                    "nombre_en": e_nom_en or None, "descripcion_en": e_desc_en or None,
                                    "nombre_ca": e_nom_ca or None, "descripcion_ca": e_desc_ca or None,
                                    "nombre_vi": e_nom_vi or None, "descripcion_vi": e_desc_vi or None,
                                    "precio": float(e_precio), "foto_url": e_foto or None,
                                    "orden": int(e_orden), "disponible": e_disp
                                }).eq("id", prod["id"]).execute()
                                st.success("✅ Guardado")
                                st.rerun()
                            if sc2.button("🗑️ Eliminar", key=f"del_prod_{prod['id']}"):
                                st.session_state[f"confirm_del_prod_{prod['id']}"] = True
                            if st.session_state.get(f"confirm_del_prod_{prod['id']}"):
                                st.warning(f"¿Eliminar '{prod['nombre']}'?")
                                dc1, dc2, dc3 = st.columns(3)
                                if dc1.button("✅ Sí, eliminar", key=f"yes_prod_{prod['id']}"):
                                    try:
                                        sb9.table("productos").delete().eq("id", prod["id"]).execute()
                                        st.session_state.pop(f"confirm_del_prod_{prod['id']}", None)
                                        st.success("✅ Eliminado")
                                        st.rerun()
                                    except Exception as _e:
                                        st.error("No se puede eliminar porque tiene pedidos asociados. Márcalo como no disponible en su lugar.")
                                        st.session_state.pop(f"confirm_del_prod_{prod['id']}", None)
                                if dc2.button("🚫 Desactivar", key=f"dis_prod_{prod['id']}"):
                                    sb9.table("productos").update({"disponible": False}).eq("id", prod["id"]).execute()
                                    st.session_state.pop(f"confirm_del_prod_{prod['id']}", None)
                                    st.success("✅ Producto desactivado — no aparecerá en la web")
                                    st.rerun()
                                if dc3.button("❌ Cancelar", key=f"no_prod_{prod['id']}"):
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
                    new_cat_local = st.checkbox("🪑 Solo pedidos en el local (no aparece en la web para recogida)", key="new_cat_local")
                    if st.button("➕ Añadir categoría", key="add_cat_web"):
                        if new_cat_nom.strip():
                            sb9.table("categorias").insert({
                                "nombre": new_cat_nom.strip(),
                                "descripcion": new_cat_desc.strip() or None,
                                "orden": int(new_cat_ord),
                                "activo": True,
                                "solo_local": bool(new_cat_local)
                            }).execute()
                            st.success(f"✅ Categoría '{new_cat_nom}' creada")
                            st.rerun()
                        else:
                            st.warning("Escribe un nombre.")

                for cat in cats_web:
                    n_prods = len([p for p in prods_web if p["categoria_id"] == cat["id"]])
                    icono_local = " 🪑" if cat.get("solo_local") else ""
                    with st.expander(f"{'✅' if cat['activo'] else '❌'} {cat['orden']}. {cat['nombre']}{icono_local} ({n_prods} productos)"):
                        cc1, cc2 = st.columns([3,1])
                        c_nom = cc1.text_input("Nombre:", value=cat["nombre"], key=f"cnom_{cat['id']}")
                        c_ord = cc2.number_input("Orden:", value=int(cat.get("orden",0)), min_value=1, key=f"cord_{cat['id']}")
                        c_desc = st.text_input("Descripción:", value=cat.get("descripcion") or "", key=f"cdesc_{cat['id']}")
                        c_act = st.checkbox("Activa", value=cat.get("activo",True), key=f"cact_{cat['id']}")
                        c_local = st.checkbox("🪑 Solo pedidos en el local (QR de mesa) — no aparece en la web para recogida",
                                              value=bool(cat.get("solo_local")), key=f"clocal_{cat['id']}")
                        csc1, csc2 = st.columns(2)
                        if csc1.button("💾 Guardar", key=f"save_cat_{cat['id']}"):
                            sb9.table("categorias").update({
                                "nombre": c_nom, "descripcion": c_desc or None,
                                "orden": int(c_ord), "activo": c_act,
                                "solo_local": bool(c_local)
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

        _frag_seccion_5()
    if nav == "📢 KDS":
        @st.fragment
        def _frag_seccion_6():
            render_kds_msg_tab()

        _frag_seccion_6()
    st.divider()
    st.caption(f"Datos: {fecha_min.strftime('%d/%m/%Y')} → {fecha_max.strftime('%d/%m/%Y')} · {len(df)} franjas · Total €{total_ventas:,.2f} (IVA incl.)")

# ── UI principal ──────────────────────────────────────────────
st.title("☕ Vietnamito — Dashboard de Ventas")

uploaded = st.file_uploader(
    "Sube un CSV de ventas (Epos Now o nuevo POS)",
    type=["csv"],
    help="Compatible con Epos Now (Sales Breakdown by Hour) y el nuevo POS (por ticket)"
)

if uploaded:
    with st.spinner("Procesando y guardando en la nube..."):
        rows, fmt = parse_csv(uploaded)
        if rows:
            # Trazabilidad: origen y archivo del que procede cada fila
            _fuente = "glop" if fmt == "nuevo" else "epos"
            _nombre_archivo = getattr(uploaded, "name", None)
            for _r in rows:
                _r["fuente"] = _fuente
                _r["archivo"] = _nombre_archivo
            save_to_supabase(rows, fmt)
            load_from_supabase.clear()
            fmt_label = "nuevo POS (por ticket)" if fmt == "nuevo" else "Epos Now (por franja horaria)"
            st.success(f"✅ {len(rows)} registros guardados · Formato detectado: {fmt_label} · Archivo: {_nombre_archivo}")
        else:
            st.error("No se pudieron leer datos del CSV. Verifica el formato.")

with st.spinner("Cargando datos..."):
    df = load_from_supabase()

if df.empty:
    st.info("No hay datos de ventas. Sube un CSV de Epos Now para ver el dashboard de ventas.")
    st.divider()
    # Mostrar pestañas de gestión completas aunque no haya datos de ventas
    _sb0 = get_supabase()
    _ped_pend = len((_sb0.table("pedidos").select("id").eq("estado","solicitado").execute().data or []))
    _res_pend = len((_sb0.table("reservas").select("id").eq("estado","pendiente").execute().data or []))
    _aviso_slot = st.empty()
    if _ped_pend > 0 or _res_pend > 0:
        _avisos = []
        if _ped_pend > 0:
            _avisos.append(f"🛍️ {_ped_pend} pedido{'s' if _ped_pend != 1 else ''} esperando confirmación")
        if _res_pend > 0:
            _avisos.append(f"🍽️ {_res_pend} reserva{'s' if _res_pend != 1 else ''} pendiente{'s' if _res_pend != 1 else ''}")
        _aviso_slot.error("🔴 " + " · ".join(_avisos))

    _nav = st.radio("Sección", ["👥 Turnos", "📋 Checklists", "🛍️ Pedidos", "🍽️ Reservas", "🌐 Web", "📢 KDS"],
                    horizontal=True, key="nav_sin_datos", label_visibility="collapsed")

    # Reutilizar el mismo código de las pestañas del dashboard
    # Para ello creamos un df vacío con las columnas necesarias
    import pandas as _pd2
    _df_empty = _pd2.DataFrame(columns=["fecha","hora","dow","valor","ntrans","items"])

    if _nav == "👥 Turnos":
        import datetime as _dt_mod
        sb = _sb0
        emp_res = sb.table("empleados").select("*").order("id").execute()
        empleados = emp_res.data if emp_res.data else []
        st.markdown("### Empleados")
        header = st.columns([3, 2, 1, 1])
        header[0].markdown("**Nombre**"); header[1].markdown("**€/hora**"); header[2].markdown("**Guardar**"); header[3].markdown("**Eliminar**")
        for emp in empleados:
            c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
            nuevo_nombre = c1.text_input("n", value=emp["nombre"], label_visibility="collapsed", key=f"nom2_{emp['id']}")
            nuevo_coste = c2.number_input("c", value=float(emp["coste_hora"]), min_value=0.0, step=0.5, format="%.2f", label_visibility="collapsed", key=f"cos2_{emp['id']}")
            if c3.button("💾", key=f"saveemp2_{emp['id']}"):
                sb.table("empleados").update({"nombre": nuevo_nombre, "coste_hora": nuevo_coste}).eq("id", emp["id"]).execute()
                st.success(f"✅ {nuevo_nombre} guardado"); st.rerun()
            if c4.button("🗑️", key=f"delemp2_{emp['id']}"):
                st.session_state[f"confirm_del2_{emp['id']}"] = True
            if st.session_state.get(f"confirm_del2_{emp['id']}"):
                st.warning(f"¿Eliminar a **{emp['nombre']}**?")
                if st.button("✅ Sí", key=f"yes2_{emp['id']}"):
                    sb.table("turnos").delete().eq("empleado_id", emp["id"]).execute()
                    sb.table("empleados").delete().eq("id", emp["id"]).execute()
                    st.session_state.pop(f"confirm_del2_{emp['id']}", None); st.rerun()
                if st.button("❌ No", key=f"no2_{emp['id']}"):
                    st.session_state.pop(f"confirm_del2_{emp['id']}", None); st.rerun()
        with st.expander("➕ Añadir empleado"):
            na1, na2, na3 = st.columns([3, 2, 1])
            nuevo_emp_nombre = na1.text_input("Nombre:", key="new_emp_nombre2")
            nuevo_emp_coste = na2.number_input("€/hora:", value=10.0, min_value=0.0, step=0.5, format="%.2f", key="new_emp_coste2")
            if na3.button("➕", key="add_emp2"):
                if nuevo_emp_nombre.strip():
                    sb.table("empleados").insert({"nombre": nuevo_emp_nombre.strip(), "coste_hora": nuevo_emp_coste}).execute()
                    st.success(f"✅ {nuevo_emp_nombre} añadido"); st.rerun()

    if _nav == "📋 Checklists":
        sb6 = _sb0
        st.markdown("### Procesos")
        proc_res = sb6.table("procesos").select("*").order("orden").execute()
        procesos = proc_res.data or []
        with st.expander("➕ Nuevo proceso"):
            new_proc_nombre2 = st.text_input("Nombre:", key="new_proc_nombre2")
            new_proc_desc2 = st.text_input("Descripción:", key="new_proc_desc2")
            new_proc_orden2 = st.number_input("Orden:", value=len(procesos)+1, min_value=1, key="new_proc_orden2")
            if st.button("➕ Añadir proceso", key="add_proc2"):
                if new_proc_nombre2.strip():
                    try:
                        sb6.table("procesos").insert({"nombre": new_proc_nombre2.strip(), "descripcion": new_proc_desc2.strip() or None, "orden": int(new_proc_orden2), "activo": True}).execute()
                        st.success(f"✅ '{new_proc_nombre2}' creado"); st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
        if procesos:
            proc_sel2 = st.selectbox("Proceso:", options=[p["id"] for p in procesos], format_func=lambda x: next(p["nombre"] for p in procesos if p["id"] == x), key="proc_sel2")
            pasos_res2 = sb6.table("pasos").select("*").eq("proceso_id", proc_sel2).order("orden").execute()
            pasos2 = sorted(pasos_res2.data or [], key=lambda p: p.get("orden",0))
            st.markdown(f"**{len(pasos2)} pasos**")
            with st.expander("➕ Añadir paso"):
                new_paso_titulo2 = st.text_input("Título:", key="new_paso_titulo2")
                new_paso_orden2 = st.number_input("Orden:", value=len(pasos2)+1, min_value=1, key="new_paso_orden2")
                new_paso_desc2 = st.text_area("Descripción:", key="new_paso_desc2", height=80)
                if st.button("➕ Añadir paso", key="add_paso2"):
                    if new_paso_titulo2.strip():
                        sb6.table("pasos").insert({"proceso_id": proc_sel2, "titulo": new_paso_titulo2.strip(), "descripcion": new_paso_desc2.strip() or None, "orden": int(new_paso_orden2)}).execute()
                        st.success("✅ Paso añadido"); st.rerun()

    if _nav == "🛍️ Pedidos":
        sb7 = _sb0
        st.markdown("### Pedidos")
        filtro_ped2 = st.selectbox("Filtrar:", ["Todos","Pendientes","Preparando","Listos","Entregados","Cancelados"], key="filtro_ped2")
        filtro_map2 = {"Todos":None,"Pendientes":"pendiente","Preparando":"preparando","Listos":"listo","Entregados":"entregado","Cancelados":"cancelado"}
        q = sb7.table("pedidos").select("*").order("creado_at", desc=True)
        if filtro_map2[filtro_ped2]: q = q.eq("estado", filtro_map2[filtro_ped2])
        pedidos2 = q.limit(100).execute().data or []
        if not pedidos2:
            st.info("No hay pedidos.")
        for ped in pedidos2:
            items_res2 = sb7.table("pedido_items").select("*").eq("pedido_id", ped["id"]).execute().data or []
            productos_str2 = ", ".join([f"{i['nombre_producto']} ×{i['cantidad']}" for i in items_res2])
            icono2 = {"pendiente":"🔴","preparando":"🟡","listo":"🟢","entregado":"✅","cancelado":"⚫"}.get(ped["estado"],"⚪")
            with st.expander(f"{icono2} #{ped['id']} · {ped['nombre']} · €{ped['total']:.2f} · {ped['hora_recogida']}"):
                st.markdown(f"**{ped['nombre']}** · {ped['telefono']} · {ped.get('email','—')}")
                st.markdown(f"**Productos:** {productos_str2}")
                if ped.get("notas"): st.caption(f"📝 {ped['notas']}")
                cols2 = st.columns(5)
                for i2, est2 in enumerate(["pendiente","preparando","listo","entregado","cancelado"]):
                    with cols2[i2]:
                        if est2 != ped["estado"]:
                            if st.button(est2.capitalize(), key=f"ped2_{ped['id']}_{est2}"):
                                sb7.table("pedidos").update({"estado": est2}).eq("id", ped["id"]).execute()
                                st.rerun()

    if _nav == "🍽️ Reservas":
        sb8 = _sb0
        st.markdown("### Reservas")
        filtro_res2 = st.selectbox("Filtrar:", ["Todos","Pendientes","Confirmadas","Canceladas"], key="filtro_res2")
        filtro_res_map2 = {"Todos":None,"Pendientes":"pendiente","Confirmadas":"confirmada","Canceladas":"cancelada"}
        q2 = sb8.table("reservas").select("*").order("creado_at", desc=True)
        if filtro_res_map2[filtro_res2]: q2 = q2.eq("estado", filtro_res_map2[filtro_res2])
        reservas2 = q2.limit(100).execute().data or []
        if not reservas2:
            st.info("No hay reservas.")
        for res2 in reservas2:
            icono3 = {"pendiente":"🔴","confirmada":"🟢","cancelada":"⚫"}.get(res2["estado"],"⚪")
            with st.expander(f"{icono3} #{res2['id']} · {res2['nombre']} · {res2['personas']} pax · {res2['fecha']} {res2['hora']}"):
                st.markdown(f"**{res2['nombre']}** · {res2['telefono']} · {res2.get('email','—')}")
                if res2.get("notas"): st.caption(f"📝 {res2['notas']}")
                rc1, rc2, rc3 = st.columns(3)
                for col3, est3 in zip([rc1,rc2,rc3], ["pendiente","confirmada","cancelada"]):
                    with col3:
                        if est3 != res2["estado"]:
                            if st.button(est3.capitalize(), key=f"res2_{res2['id']}_{est3}"):
                                sb8.table("reservas").update({"estado": est3}).eq("id", res2["id"]).execute()
                                if est3 == "confirmada" and res2.get("email"):
                                    st.success("✅ Confirmada · El email se envía automáticamente")
                                else:
                                    st.success(f"✅ → {est3}")
                                st.rerun()

    if _nav == "🌐 Web":
        # Reutilizar exactamente el mismo código del tab9
        sb9 = _sb0
        st.markdown("### Gestión de la web")
        web_tab1, web_tab2, web_tab3 = st.tabs(["⚙️ Configuración", "🍜 Menú", "📸 Categorías"])
        cfg_res = sb9.table("config").select("*").execute()
        cfg = {r["clave"]: r["valor"] for r in (cfg_res.data or [])}
        with web_tab1:
            st.markdown("#### Datos del local y horarios")
            c1, c2 = st.columns(2)
            new_cfg = {}
            new_cfg["nombre_local"] = c1.text_input("Nombre del local", value=cfg.get("nombre_local","Vietnamito"), key="cfg_nombre_e")
            new_cfg["direccion"] = c2.text_input("Dirección", value=cfg.get("direccion",""), key="cfg_dir_e")
            new_cfg["telefono"] = c1.text_input("Teléfono", value=cfg.get("telefono",""), key="cfg_tel_e")
            new_cfg["email_pedidos"] = c2.text_input("Email pedidos", value=cfg.get("email_pedidos",""), key="cfg_email_e")
            new_cfg["tiempo_espera_min"] = c1.text_input("Tiempo espera (min)", value=cfg.get("tiempo_espera_min","15"), key="cfg_espera_e")
            new_cfg["mesas_total"] = c2.text_input("Nº máximo comensales", value=cfg.get("mesas_total","15"), key="cfg_mesas_e")
            new_cfg["barrio"] = c1.text_input("Barrio", value=cfg.get("barrio","Sants - Les Corts"), key="cfg_barrio_e")
            new_cfg["hero_titulo"] = st.text_input("Título hero", value=cfg.get("hero_titulo","El mejor<br>Banh mi de<br><em>Barcelona</em>"), key="cfg_hero_titulo_e")
            new_cfg["hero_subtitulo"] = st.text_input("Subtítulo hero", value=cfg.get("hero_subtitulo",""), key="cfg_hero_sub_e")
            st.markdown("**Horarios**")
            dias_cfg = [("lunes","Lun"),("martes","Mar"),("miercoles","Mié"),("jueves","Jue"),("viernes","Vie"),("sabado","Sáb"),("domingo","Dom")]
            cols_h = st.columns(7)
            for (dia, label), col in zip(dias_cfg, cols_h):
                new_cfg[f"horario_{dia}"] = col.text_input(label, value=cfg.get(f"horario_{dia}",""), key=f"cfg_h_{dia}_e")
            st.markdown("**Activar / desactivar**")
            act1, act2 = st.columns(2)
            new_cfg["pedidos_activos"] = "true" if act1.checkbox("Pedidos activos", value=cfg.get("pedidos_activos","true")=="true", key="cfg_ped_act_e") else "false"
            new_cfg["reservas_activas"] = "true" if act2.checkbox("Reservas activas", value=cfg.get("reservas_activas","true")=="true", key="cfg_res_act_e") else "false"
            if st.button("💾 Guardar configuración", key="save_cfg_e", type="primary"):
                for clave, valor in new_cfg.items():
                    sb9.table("config").upsert({"clave": clave, "valor": valor}).execute()
                st.success("✅ Configuración guardada"); st.rerun()

        with web_tab2:
            cats_res_e = sb9.table("categorias").select("*").order("orden").execute()
            cats_web_e = cats_res_e.data or []
            prods_res_e = sb9.table("productos").select("*").order("orden").execute()
            prods_web_e = prods_res_e.data or []
            if cats_web_e:
                cat_sel_web_e = st.selectbox("Categoría:", [c["nombre"] for c in cats_web_e], key="cat_sel_web_e")
                cat_obj_e = next(c for c in cats_web_e if c["nombre"] == cat_sel_web_e)
                prods_cat_e = [p for p in prods_web_e if p["categoria_id"] == cat_obj_e["id"]]
                st.markdown(f"**{len(prods_cat_e)} productos**")
                for prod_e in sorted(prods_cat_e, key=lambda p: p.get("orden",0)):
                    with st.expander(f"{'✅' if prod_e['disponible'] else '❌'} {prod_e['orden']}. {prod_e['nombre']} — €{prod_e['precio']:.2f}"):
                        ep1_e, ep2_e = st.columns([3,1])
                        e_nom_e = ep1_e.text_input("Nombre:", value=prod_e["nombre"], key=f"en_e_{prod_e['id']}")
                        e_precio_e = ep2_e.number_input("€:", value=float(prod_e["precio"]), min_value=0.0, step=0.5, format="%.2f", key=f"epr_e_{prod_e['id']}")
                        e_desc_e = st.text_area("Descripción:", value=prod_e.get("descripcion") or "", key=f"ed_e_{prod_e['id']}", height=70)
                        e_disp_e = st.checkbox("Disponible", value=prod_e.get("disponible",True), key=f"edis_e_{prod_e['id']}")
                        if st.button("💾 Guardar", key=f"save_prod_e_{prod_e['id']}"):
                            sb9.table("productos").update({"nombre": e_nom_e, "descripcion": e_desc_e or None, "precio": float(e_precio_e), "disponible": e_disp_e}).eq("id", prod_e["id"]).execute()
                            st.success("✅ Guardado"); st.rerun()

        with web_tab3:
            st.markdown("#### Categorías")
            for cat_e in cats_web_e:
                with st.expander(f"{cat_e['orden']}. {cat_e['nombre']}"):
                    c_nom_e = st.text_input("🇪🇸 Nombre:", value=cat_e["nombre"], key=f"cnom_e_{cat_e['id']}")
                    c_nom_en = st.text_input("🇬🇧 Name (EN):", value=cat_e.get("nombre_en") or "", key=f"cnom_en_{cat_e['id']}")
                    c_nom_ca = st.text_input("🏴 Nom (CA):", value=cat_e.get("nombre_ca") or "", key=f"cnom_ca_{cat_e['id']}")
                    c_nom_vi = st.text_input("🇻🇳 Tên (VI):", value=cat_e.get("nombre_vi") or "", key=f"cnom_vi_{cat_e['id']}")
                    c_act_e = st.checkbox("Activa", value=cat_e.get("activo",True), key=f"cact_e_{cat_e['id']}")
                    if st.button("💾 Guardar", key=f"save_cat_e_{cat_e['id']}"):
                        sb9.table("categorias").update({
                            "nombre": c_nom_e, "activo": c_act_e,
                            "nombre_en": c_nom_en or None,
                            "nombre_ca": c_nom_ca or None,
                            "nombre_vi": c_nom_vi or None,
                        }).eq("id", cat_e["id"]).execute()
                        st.success("✅ Guardado"); st.rerun()

    if _nav == "📢 KDS":
        render_kds_msg_tab()

else:
    render_dashboard(df)
