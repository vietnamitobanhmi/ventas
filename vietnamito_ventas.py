<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<meta name="theme-color" content="#0D1117">
<link rel="manifest" href="/kds-manifest.json">
<link rel="icon" type="image/png" href="https://rwtpjqvgiiuvniixqapu.supabase.co/storage/v1/object/public/assets/Logo%20Vietnamito%20Final.png">
<link rel="apple-touch-icon" href="https://rwtpjqvgiiuvniixqapu.supabase.co/storage/v1/object/public/assets/Logo%20Vietnamito%20Final.png">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
<title>Vietnamito Dashboard</title>
<style>
:root{
  --bg:#0D1117; --surface:#161B22; --surface-2:#1F2937; --border:#30363D;
  --text:#F0F6FC; --muted:#8B949E;
  --pendiente:#EAB308; --aceptado:#22C55E; --finalizado:#6B7280;
  --red:#EF4444; --orange:#F59E0B; --blue:#3B82F6;
  --reserva:#8B5CF6;
}
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
html,body{overflow-x:hidden}
body{font-family:'SF Pro Display',-apple-system,BlinkMacSystemFont,sans-serif;background:var(--bg);color:var(--text);height:100vh;overflow:hidden;user-select:none}

/* HEADER */
.status-bar{display:flex;justify-content:space-between;align-items:center;padding:10px 20px;background:var(--surface);border-bottom:1px solid var(--border);flex-shrink:0}
.logo{display:flex;align-items:center;gap:10px}
.logo img{height:32px}
.logo-text{font-size:16px;font-weight:700;color:var(--text)}
.kds-version{font-size:10px;font-weight:400;color:var(--muted);margin-left:6px;letter-spacing:.05em;opacity:.7}
.status-right{display:flex;align-items:center;gap:16px}
.sound-btn{background:var(--surface-2);border:1px solid var(--border);color:var(--text);padding:6px 12px;border-radius:6px;cursor:pointer;font-size:13px;font-family:inherit}
.sound-btn.on{background:rgba(34,197,94,0.15);border-color:#22C55E;color:#22C55E}
.conn-dot{width:10px;height:10px;border-radius:50%;background:#22C55E;box-shadow:0 0 8px #22C55E}
.conn-dot.off{background:#EF4444;box-shadow:0 0 8px #EF4444}
.conn-label{font-size:12px;color:var(--muted)}
.time-now{font-size:18px;font-weight:600;font-variant-numeric:tabular-nums;color:var(--text)}

/* MAIN LAYOUT */
.dashboard{display:grid;grid-template-columns:1fr 1fr 1fr 380px;gap:12px;padding:12px;height:calc(100vh - 54px);overflow:hidden}
@media(max-width:1200px){.dashboard{grid-template-columns:1fr 1fr 1fr 320px}}

.col{display:flex;flex-direction:column;background:var(--surface);border:1px solid var(--border);border-radius:10px;overflow:hidden;min-height:0}
.col-header{display:flex;justify-content:space-between;align-items:center;padding:14px 18px;font-weight:700;font-size:15px;letter-spacing:.05em;text-transform:uppercase;border-bottom:1px solid var(--border);flex-shrink:0}
.col-header.pendiente{background:linear-gradient(180deg,rgba(234,179,8,0.15),transparent);color:var(--pendiente)}
.col-header.aceptado{background:linear-gradient(180deg,rgba(34,197,94,0.15),transparent);color:var(--aceptado)}
.col-header.finalizado{background:linear-gradient(180deg,rgba(107,114,128,0.15),transparent);color:var(--finalizado)}
.col-header.reservas{background:linear-gradient(180deg,rgba(139,92,246,0.15),transparent);color:var(--reserva)}
.col-badge{background:var(--surface-2);color:var(--text);padding:2px 10px;border-radius:12px;font-size:13px;font-weight:700;min-width:26px;text-align:center}

.cards{flex:1;overflow-y:auto;padding:10px 10px calc(120px + env(safe-area-inset-bottom,0px));display:flex;flex-direction:column;gap:8px;-webkit-overflow-scrolling:touch;scroll-padding-bottom:120px}
.cards::after{content:'';display:block;min-height:80px;flex-shrink:0}
.cards::-webkit-scrollbar{width:8px}
.cards::-webkit-scrollbar-track{background:transparent}
.cards::-webkit-scrollbar-thumb{background:var(--border);border-radius:4px}

/* CARDS */
.card{background:var(--surface-2);border:1px solid var(--border);border-radius:8px;padding:12px;font-size:13px;position:relative;transition:opacity .2s}
.card.solicitado{border-color:var(--pendiente);border-width:2px;animation:cardPulse 1.5s ease infinite}
@keyframes cardPulse{0%,100%{box-shadow:0 0 0 rgba(234,179,8,0)}50%{box-shadow:0 0 16px rgba(234,179,8,0.3)}}
.card-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}
.card-id{font-size:12px;color:var(--muted);font-weight:600}
.card-time{font-size:12px;color:var(--text);font-weight:600;background:rgba(255,255,255,0.06);padding:2px 8px;border-radius:6px}
.card-name{font-size:15px;font-weight:700;color:var(--text);margin-bottom:2px}
.card-tel{font-size:11px;color:var(--muted);margin-bottom:8px}
.card-items{font-size:12px;color:#D1D5DB;line-height:1.5;padding:6px 0;border-top:1px dashed var(--border);border-bottom:1px dashed var(--border);margin-bottom:8px}
.card-item{padding:2px 0}
.card-item-qty{color:var(--orange);font-weight:700;margin-right:6px}
.card-total{font-size:14px;font-weight:700;color:var(--text);margin-bottom:8px;display:flex;justify-content:space-between}
.card-notas{background:rgba(234,179,8,0.1);border-left:3px solid var(--pendiente);padding:6px 10px;font-size:12px;color:#FCD34D;margin-bottom:8px;border-radius:4px}
.card-actions{display:flex;gap:6px}
.act-btn{flex:1;padding:8px 10px;border:none;border-radius:6px;font-size:12px;font-weight:700;cursor:pointer;font-family:inherit;transition:transform .1s}
.act-btn:active{transform:scale(.96)}
.btn-aceptar{background:linear-gradient(180deg,#22C55E,#16A34A);color:#fff}
.btn-rechazar{background:transparent;border:1px solid #EF4444;color:#EF4444}
.btn-cancelar{background:transparent;border:1px solid rgba(239,68,68,0.4);color:#F87171}
.card-silent-del{width:100%;margin-top:6px;padding:5px;background:transparent;color:rgba(255,255,255,0.3);border:1px dashed rgba(255,255,255,0.15);border-radius:5px;font-size:10px;cursor:pointer;font-family:inherit}
.card-silent-del:hover,.card-silent-del:active{background:rgba(239,68,68,0.15);color:#fca5a5}
.card-estado-badge{position:absolute;top:12px;right:12px;font-size:10px;padding:2px 6px;border-radius:4px;text-transform:uppercase;letter-spacing:.05em}
.badge-rechazado{background:rgba(239,68,68,0.2);color:#F87171}
.badge-cancelado{background:rgba(239,68,68,0.2);color:#F87171}

.empty{color:var(--muted);text-align:center;padding:30px 20px;font-size:13px;font-style:italic}

/* RESERVAS TIMELINE */
.reserva{background:var(--surface-2);border:1px solid var(--border);border-radius:8px;padding:12px;margin-bottom:8px;position:relative}
.reserva-hora{font-size:22px;font-weight:700;color:var(--reserva);margin-bottom:4px;font-variant-numeric:tabular-nums}
.reserva-nombre{font-size:14px;font-weight:700;color:var(--text);margin-bottom:2px}
.reserva-info{font-size:12px;color:var(--muted);margin-bottom:4px}
.reserva-personas{display:inline-block;background:rgba(139,92,246,0.15);color:var(--reserva);padding:2px 8px;border-radius:6px;font-size:11px;font-weight:700;margin-right:6px}
.reserva-notas{font-size:11px;color:#D1D5DB;margin-top:6px;background:rgba(255,255,255,0.04);padding:6px 8px;border-radius:4px;font-style:italic}
.reserva.cancelada{opacity:0.5}
.reserva.cancelada::after{content:'CANCELADA';position:absolute;top:6px;right:6px;font-size:9px;color:#EF4444;font-weight:700;letter-spacing:.05em}
.reserva.confirmada{border-left:3px solid var(--aceptado)}
.reserva.pendiente-conf{border-color:var(--pendiente);border-width:2px;animation:cardPulse 1.5s ease infinite}
.reserva-fecha{display:inline-block;background:rgba(234,179,8,0.15);color:var(--pendiente);padding:2px 8px;border-radius:6px;font-size:11px;font-weight:700;margin-bottom:4px}
.reserva-email{font-size:11px;color:var(--muted);margin-top:2px;word-break:break-all}
.reserva-seccion{font-size:12px;font-weight:700;color:var(--reserva);text-transform:uppercase;letter-spacing:.08em;padding:8px 4px 6px;border-bottom:1px solid var(--border);margin-bottom:8px}

/* MODALES */
.modal-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.85);z-index:9999;align-items:center;justify-content:center;padding:20px;animation:overlayIn .2s ease}
.modal-overlay.show{display:flex}
@keyframes overlayIn{from{background:rgba(0,0,0,0)}to{background:rgba(0,0,0,0.85)}}
.modal-card{background:var(--surface);border:3px solid var(--red);border-radius:16px;max-width:520px;width:100%;max-height:90vh;overflow-y:auto;box-shadow:0 0 0 6px rgba(239,68,68,0.25),0 20px 60px rgba(0,0,0,0.6);animation:modalPulse 1.2s ease infinite,modalIn .25s ease}
@keyframes modalPulse{0%,100%{box-shadow:0 0 0 6px rgba(239,68,68,0.25),0 20px 60px rgba(0,0,0,0.6)}50%{box-shadow:0 0 0 14px rgba(239,68,68,0.05),0 20px 60px rgba(0,0,0,0.6)}}
@keyframes modalIn{from{transform:scale(0.85);opacity:0}to{transform:scale(1);opacity:1}}
.modal-head{padding:18px 22px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:12px;background:linear-gradient(180deg,rgba(239,68,68,0.15),transparent)}
.modal-bell{font-size:28px;animation:bellShake .5s ease infinite}
@keyframes bellShake{0%,100%{transform:rotate(0)}25%{transform:rotate(-15deg)}75%{transform:rotate(15deg)}}
.modal-title{font-size:18px;font-weight:700;color:var(--red);letter-spacing:.04em;text-transform:uppercase;flex:1}
.modal-id{font-size:13px;color:var(--muted)}
.modal-body{padding:20px 22px}
.modal-info{display:grid;grid-template-columns:auto 1fr;gap:8px 14px;margin-bottom:18px}
.modal-info-label{color:var(--muted);font-size:13px;align-self:center}
.modal-info-value{color:var(--text);font-size:15px;font-weight:600}
.modal-pickup{background:rgba(252,211,77,0.12);border:1px solid #FCD34D;padding:10px 14px;border-radius:8px;margin-bottom:14px;font-size:15px;color:#FCD34D;font-weight:700;text-align:center}
.modal-items{background:rgba(255,255,255,0.04);border-radius:10px;padding:12px 14px;margin-bottom:14px}
.modal-items-title{font-size:11px;text-transform:uppercase;color:var(--muted);letter-spacing:.1em;margin-bottom:8px}
.modal-item{display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px dashed var(--border);font-size:14px}
.modal-item:last-child{border-bottom:none}
.modal-item-name{color:var(--text)}
.modal-item-qty{color:var(--orange);font-weight:700;margin-right:8px}
.modal-item-price{color:var(--muted);font-variant-numeric:tabular-nums}
.modal-total{display:flex;justify-content:space-between;align-items:center;padding-top:10px;margin-top:6px;border-top:1px solid var(--border);font-size:17px;font-weight:700}
.modal-total .modal-item-price{color:var(--text)}
.modal-notas{background:rgba(234,179,8,0.1);border-left:3px solid var(--pendiente);padding:10px 12px;border-radius:6px;font-size:13px;color:var(--pendiente);margin-bottom:14px}
.modal-actions{display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:16px 22px 22px}
.modal-btn{padding:14px 12px;border:none;border-radius:10px;font-size:15px;font-weight:700;cursor:pointer;font-family:inherit;letter-spacing:.04em;transition:transform .1s,opacity .2s}
.modal-btn:active{transform:scale(.97)}
.modal-btn-aceptar{background:linear-gradient(180deg,#22C55E,#16A34A);color:#fff}
.modal-btn-rechazar{background:linear-gradient(180deg,#EF4444,#DC2626);color:#fff}
.modal-btn:disabled{opacity:.5;cursor:wait}
.modal-tiempo{text-align:center;font-size:11px;color:var(--muted);padding:0 22px 14px;margin-top:-6px}
</style>
</head>
<body>

<div class="status-bar">
  <div class="logo">
    <img src="https://rwtpjqvgiiuvniixqapu.supabase.co/storage/v1/object/public/assets/Logo%20Vietnamito%20Final.png" alt="V">
    <span class="logo-text">Vietnamito Dashboard <span class="kds-version">v20260711-1015</span></span>
  </div>
  <div class="status-right">
    <button class="sound-btn on" id="soundBtn" onclick="toggleSound()">🔔 Sonido</button>
    <div class="conn-dot" id="connDot"></div>
    <span class="conn-label" id="connLabel">Conectado</span>
    <span class="time-now" id="clockEl">--:--</span>
  </div>
</div>

<div class="dashboard">
  <div class="col">
    <div class="col-header pendiente">
      <span>🆕 Pendientes</span>
      <div class="col-badge" id="badge-pendiente">0</div>
    </div>
    <div class="cards" id="col-pendiente"></div>
  </div>
  <div class="col">
    <div class="col-header aceptado">
      <span>✅ Aceptados</span>
      <div class="col-badge" id="badge-aceptado">0</div>
    </div>
    <div class="cards" id="col-aceptado"></div>
  </div>
  <div class="col">
    <div class="col-header finalizado">
      <span>📋 Finalizados hoy</span>
      <div class="col-badge" id="badge-finalizado">0</div>
    </div>
    <div class="cards" id="col-finalizado"></div>
  </div>
  <div class="col">
    <div class="col-header reservas">
      <span>🍽️ Reservas hoy</span>
      <div class="col-badge" id="badge-reservas">0</div>
    </div>
    <div class="cards" id="col-reservas"></div>
  </div>
</div>

<script>
const SUPABASE_URL = "https://rwtpjqvgiiuvniixqapu.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ3dHBqcXZnaWl1dm5paXhxYXB1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzcxMzIyMjMsImV4cCI6MjA5MjcwODIyM30.jznrwuusfgtVkrzz_bfdsxq3tVsv-uV2tyMeIlh3bZg";
const KDS_USER_EMAIL = "kds@vietnamito.es";
const AUTH_STORAGE_KEY = "kds_auth_v1";
let authToken = null;
let authRefreshToken = null;

// Getter dinámico para los headers — usa JWT si estamos autenticados, si no la anon key
function getHeaders() {
  return {
    'apikey': SUPABASE_ANON_KEY,
    'Authorization': `Bearer ${authToken || SUPABASE_ANON_KEY}`,
    'Content-Type': 'application/json'
  };
}

// Reloj
function tick(){
  const d = new Date();
  document.getElementById('clockEl').textContent = `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
}
tick(); setInterval(tick, 30000);

// Sonido
let audioCtx = null;
let soundOn = true;
function toggleSound(){
  soundOn = !soundOn;
  const b = document.getElementById('soundBtn');
  b.classList.toggle('on', soundOn);
  b.textContent = soundOn ? '🔔 Sonido' : '🔕 Sin sonido';
}
function playNewOrder(){
  if(!soundOn) return;
  try {
    if(!audioCtx) audioCtx = new (window.AudioContext||window.webkitAudioContext)();
    if(audioCtx.state === 'suspended') audioCtx.resume();
    [880, 1100].forEach((freq, i) => {
      const o = audioCtx.createOscillator();
      const g = audioCtx.createGain();
      o.connect(g); g.connect(audioCtx.destination);
      o.frequency.value = freq;
      const t = audioCtx.currentTime + i * 0.15;
      g.gain.setValueAtTime(0, t);
      g.gain.linearRampToValueAtTime(0.15, t + 0.02);
      g.gain.exponentialRampToValueAtTime(0.001, t + 0.3);
      o.start(t); o.stop(t + 0.3);
    });
  } catch(e){}
}

// Conexión
function setOnline(ok){
  document.getElementById('connDot').classList.toggle('off', !ok);
  document.getElementById('connLabel').textContent = ok ? 'Conectado' : 'Sin conexión';
}

// Cache items
let itemsCache = {};
let pedidos = [];
let soliPendientes = [];
let modalActivoId = null;
let alarmaInterval = null;
let lastPendienteIds = new Set();

// ── FETCH PEDIDOS ──
async function fetchPedidos(){
  try {
    // Una sola query: todos los pedidos de los últimos 200. En JS filtramos según estado y fecha
    const r = await fetch(
      `${SUPABASE_URL}/rest/v1/pedidos?order=creado_at.desc&limit=200`,
      {headers: getHeaders()}
    );
    if(!r.ok) throw new Error(r.status);
    const all = await r.json();

    // Separar en JS: activos (todos) + rechazados/cancelados solo de hoy
    const hoy = new Date();
    const hoyStr = `${hoy.getFullYear()}-${String(hoy.getMonth()+1).padStart(2,'0')}-${String(hoy.getDate()).padStart(2,'0')}`;
    const activos = all.filter(p => ['solicitado','pendiente','preparando','listo','entregado'].includes(p.estado));
    const finalizados = all.filter(p => {
      if (!['rechazado','cancelado'].includes(p.estado)) return false;
      const fechaP = new Date(p.creado_at);
      const fPStr = `${fechaP.getFullYear()}-${String(fechaP.getMonth()+1).padStart(2,'0')}-${String(fechaP.getDate()).padStart(2,'0')}`;
      return fPStr === hoyStr;
    });

    const data = [...activos, ...finalizados];

    // Items cache
    const newIds = data.map(p=>p.id).filter(id => !itemsCache[id]);
    if(newIds.length){
      const ri = await fetch(`${SUPABASE_URL}/rest/v1/pedido_items?pedido_id=in.(${newIds.join(',')})`, {headers: getHeaders()});
      const items = await ri.json();
      newIds.forEach(id => { itemsCache[id] = items.filter(i => i.pedido_id === id); });
    }

    const currentSolicIds = new Set(data.filter(p=>p.estado==='solicitado').map(p=>p.id));
    lastPendienteIds = currentSolicIds;

    pedidos = data;

    // ACK: marcar como recibidos en KDS los que aún no lo estén
    const sinAck = data.filter(p => !p.kds_recibido).map(p => p.id);
    if(sinAck.length){
      fetch(`${SUPABASE_URL}/rest/v1/pedidos?id=in.(${sinAck.join(',')})`, {
        method:'PATCH', headers: getHeaders(),
        body: JSON.stringify({kds_recibido: true, kds_recibido_at: new Date().toISOString()})
      }).catch(()=>{});
    }
    soliPendientes = data.filter(p => p.estado === 'solicitado').sort((a,b) => new Date(a.creado_at) - new Date(b.creado_at));
    actualizarModal();

    render();
    setOnline(true);
  } catch(e){
    console.error('fetchPedidos error:', e);
    setOnline(false);
  }
}

// ── FETCH RESERVAS ──
let reservas = [];
let reservasPendientes = [];
let modalReservaActivaId = null;
let alarmaReservaInterval = null;

async function fetchReservas(){
  try {
    const hoy = new Date();
    const hoyStr = `${hoy.getFullYear()}-${String(hoy.getMonth()+1).padStart(2,'0')}-${String(hoy.getDate()).padStart(2,'0')}`;
    // Una sola query: todas las reservas desde hoy en adelante
    const r = await fetch(`${SUPABASE_URL}/rest/v1/reservas?fecha=gte.${hoyStr}&order=fecha.asc,hora.asc&limit=100`, {headers: getHeaders()});
    if(!r.ok) return;
    reservas = await r.json();
    reservasPendientes = reservas.filter(x => x.estado === 'pendiente').sort((a,b) => new Date(a.creado_at) - new Date(b.creado_at));
    cancelacionesSinVer = reservas.filter(x => x.estado === 'cancelada' && x.cancelada_por_cliente && !x.kds_cancelacion_vista);
    actualizarModalCancelacion();

    // ACK: marcar como recibidas en KDS
    const resSinAck = reservas.filter(x => !x.kds_recibido).map(x => x.id);
    if(resSinAck.length){
      fetch(`${SUPABASE_URL}/rest/v1/reservas?id=in.(${resSinAck.join(',')})`, {
        method:'PATCH', headers: getHeaders(),
        body: JSON.stringify({kds_recibido: true, kds_recibido_at: new Date().toISOString()})
      }).catch(()=>{});
    }
    actualizarModalReserva();
    renderReservas();
  } catch(e){}
}

// ── RENDER ──
function render(){
  const cols = {solicitado:[], aceptado:[], finalizado:[]};
  pedidos.forEach(p => {
    if(p.estado === 'solicitado') cols.solicitado.push(p);
    else if(['pendiente','preparando','listo','entregado'].includes(p.estado)) cols.aceptado.push(p);
    else if(['rechazado','cancelado'].includes(p.estado)) cols.finalizado.push(p);
  });

  renderColumn('pendiente', cols.solicitado, 'solicitado');
  renderColumn('aceptado', cols.aceptado, 'aceptado');
  renderColumn('finalizado', cols.finalizado.sort((a,b)=>new Date(b.creado_at)-new Date(a.creado_at)), 'finalizado');

  document.getElementById('badge-pendiente').textContent = cols.solicitado.length;
  document.getElementById('badge-aceptado').textContent = cols.aceptado.length;
  document.getElementById('badge-finalizado').textContent = cols.finalizado.length;
}

function renderColumn(colName, items, tipo){
  const container = document.getElementById('col-'+colName);
  if(!items.length){
    container.innerHTML = `<div class="empty">Sin pedidos</div>`;
    return;
  }
  container.innerHTML = items.map(p => cardHtml(p, tipo)).join('');
}

function cardHtml(p, tipo){
  const items = itemsCache[p.id] || [];
  const itemsHtml = items.map(i =>
    `<div class="card-item"><span class="card-item-qty">${i.cantidad}×</span>${i.nombre_producto}</div>`
  ).join('') || '<div style="color:var(--muted);font-size:11px;">...</div>';

  const notasHtml = p.notas ? `<div class="card-notas">📝 ${p.notas}</div>` : '';
  const horaCreado = new Date(p.creado_at).toLocaleTimeString('es',{hour:'2-digit',minute:'2-digit'});

  let estadoBadge = '';
  let actionsHtml = '';

  if(tipo === 'solicitado'){
    actionsHtml = `<div class="card-actions">
      <button class="act-btn btn-rechazar" onclick="pedidoRechazar(${p.id})">❌ Rechazar</button>
      <button class="act-btn btn-aceptar" onclick="pedidoAceptar(${p.id})">✅ Aceptar</button>
    </div>`;
  } else if(tipo === 'aceptado'){
    actionsHtml = `<div class="card-actions">
      <button class="act-btn btn-cancelar" onclick="pedidoCancelar(${p.id}, '${(p.nombre||'').replace(/'/g,"\\'")}')">🚫 Cancelar (con email)</button>
    </div>`;
  } else if(tipo === 'finalizado'){
    const cls = p.estado === 'rechazado' ? 'badge-rechazado' : 'badge-cancelado';
    estadoBadge = `<span class="card-estado-badge ${cls}">${p.estado}</span>`;
  }

  return `<div class="card ${tipo==='solicitado'?'solicitado':''}" id="card-${p.id}">
    ${estadoBadge}
    <div class="card-top">
      <span class="card-id">#${p.id} · ${horaCreado}</span>
      <span class="card-time">${p.hora_recogida||'—'}</span>
    </div>
    <div class="card-name">${p.nombre}</div>
    <div class="card-tel">📞 ${p.telefono||'—'}</div>
    <div class="card-items">${itemsHtml}</div>
    <div class="card-total"><span>Total</span><span>€${parseFloat(p.total||0).toFixed(2)}</span></div>
    ${notasHtml}
    ${actionsHtml}
    <button class="card-silent-del" onclick="borrarSilencioso(${p.id}, '${(p.nombre||'').replace(/'/g,"\\'")}')">🗑️ Borrar sin email</button>
  </div>`;
}

function renderReservas(){
  const container = document.getElementById('col-reservas');
  const hoy = new Date();
  const hoyStr = `${hoy.getFullYear()}-${String(hoy.getMonth()+1).padStart(2,'0')}-${String(hoy.getDate()).padStart(2,'0')}`;
  const activas = reservas.filter(r => r.estado !== 'cancelada' && r.estado !== 'rechazada');
  document.getElementById('badge-reservas').textContent = activas.length;
  if(!reservas.length){
    container.innerHTML = `<div class="empty">Sin reservas</div>`;
    return;
  }

  const deHoy = reservas.filter(r => r.fecha === hoyStr).sort((a,b) => a.hora.localeCompare(b.hora));
  const proximas = reservas.filter(r => r.fecha > hoyStr).sort((a,b) => (a.fecha + a.hora).localeCompare(b.fecha + b.hora));

  let html = '';
  html += `<div class="reserva-seccion">📅 Reservas HOY (${deHoy.filter(r=>r.estado!=='cancelada'&&r.estado!=='rechazada').length})</div>`;
  html += deHoy.length ? deHoy.map(r => reservaCardHtml(r, true)).join('') : `<div class="empty" style="padding:14px;">Sin reservas hoy</div>`;
  html += `<div class="reserva-seccion" style="margin-top:14px;">🗓️ Próximos días (${proximas.filter(r=>r.estado!=='cancelada'&&r.estado!=='rechazada').length})</div>`;
  html += proximas.length ? proximas.map(r => reservaCardHtml(r, false)).join('') : `<div class="empty" style="padding:14px;">Sin reservas futuras</div>`;

  container.innerHTML = html;
}

function reservaCardHtml(r, esHoy){
  const pendiente = r.estado === 'pendiente';
  const cls = r.estado === 'cancelada' || r.estado === 'rechazada' ? 'cancelada' : (r.estado === 'confirmada' ? 'confirmada' : (pendiente ? 'pendiente-conf' : ''));
  const notas = r.notas ? `<div class="reserva-notas">📝 ${r.notas}</div>` : '';
  const fechaLabel = esHoy ? '' : `<div class="reserva-fecha">📅 ${formatFechaCorta(r.fecha)}</div>`;
  const email = r.email ? `<div class="reserva-email">✉️ ${r.email}</div>` : '';
  const acciones = pendiente ? `
    <div class="card-actions" style="margin-top:8px;">
      <button class="act-btn btn-rechazar" onclick="reservaRechazarPedirMotivo(${r.id})">❌ Rechazar</button>
      <button class="act-btn btn-aceptar" onclick="reservaAceptar(${r.id})">✅ Aceptar</button>
    </div>` : '';
  return `<div class="reserva ${cls}">
    ${fechaLabel}
    <div class="reserva-hora">${r.hora}</div>
    <div class="reserva-nombre">${r.nombre}</div>
    <div class="reserva-info"><span class="reserva-personas">${r.personas} pax</span>📞 ${r.telefono||'—'}</div>
    ${email}
    ${notas}
    ${acciones}
  </div>`;
}

function formatFechaCorta(fechaStr){
  try {
    const d = new Date(fechaStr + 'T12:00:00');
    return d.toLocaleDateString('es', {weekday:'long', day:'numeric', month:'long'});
  } catch(e){ return fechaStr; }
}

// ── ACCIONES ──
async function pedidoAceptar(id){
  try {
    await fetch(`${SUPABASE_URL}/rest/v1/pedidos?id=eq.${id}`, {
      method:'PATCH', headers: getHeaders(), body: JSON.stringify({estado:'pendiente'})
    });
    fetchPedidos();
  } catch(e){ alert('Error al aceptar'); }
}

async function pedidoRechazar(id){
  if(!confirm('¿Rechazar este pedido? El cliente recibirá un email de aviso.')) return;
  try {
    await fetch(`${SUPABASE_URL}/rest/v1/pedidos?id=eq.${id}`, {
      method:'PATCH', headers: getHeaders(), body: JSON.stringify({estado:'rechazado'})
    });
    fetchPedidos();
  } catch(e){ alert('Error al rechazar'); }
}

async function pedidoCancelar(id, nombre){
  if(!confirm(`⚠️ ¿Cancelar el pedido ya aceptado de ${nombre}?\n\nSe enviará un email de cancelación al cliente.\n\nSolo hazlo si es realmente necesario.`)) return;
  try {
    await fetch(`${SUPABASE_URL}/rest/v1/pedidos?id=eq.${id}`, {
      method:'PATCH', headers: getHeaders(), body: JSON.stringify({estado:'cancelado'})
    });
    fetchPedidos();
  } catch(e){ alert('Error al cancelar'); }
}

async function borrarSilencioso(id, nombre){
  if(!confirm(`🗑️ ¿Borrar el pedido #${id} de ${nombre} SIN enviar email al cliente?\n\nEsto no se puede deshacer.`)) return;
  try {
    await fetch(`${SUPABASE_URL}/rest/v1/pedido_items?pedido_id=eq.${id}`, {method:'DELETE', headers: getHeaders()});
    await fetch(`${SUPABASE_URL}/rest/v1/pedidos?id=eq.${id}`, {method:'DELETE', headers: getHeaders()});
    delete itemsCache[id];
    fetchPedidos();
  } catch(e){ alert('Error al borrar'); }
}

// ── ACCIONES RESERVAS ──
const MOTIVOS_RECHAZO = [
  "Restaurante cerrado a la hora solicitada",
  "Sin espacio disponible para esa hora",
  "Grupo demasiado grande para nuestra capacidad",
  "Fecha no disponible (festivo o evento privado)",
];

let reservaRechazoId = null;

async function reservaAceptar(id){
  try {
    await fetch(`${SUPABASE_URL}/rest/v1/reservas?id=eq.${id}`, {
      method:'PATCH', headers: getHeaders(), body: JSON.stringify({estado:'confirmada'})
    });
    cerrarModalReserva();
    fetchReservas();
  } catch(e){ alert('Error al aceptar la reserva'); }
}

function reservaRechazarPedirMotivo(id){
  reservaRechazoId = id;
  // Rellenar los botones de motivos
  const cont = document.getElementById('motivosPredef');
  cont.innerHTML = MOTIVOS_RECHAZO.map((m,i) =>
    `<button class="motivo-btn" onclick="seleccionarMotivo(${i})">${m}</button>`
  ).join('');
  document.getElementById('motivoCustom').value = '';
  document.getElementById('motivoModal').classList.add('show');
}

function seleccionarMotivo(idx){
  confirmarRechazoReserva(MOTIVOS_RECHAZO[idx]);
}

function rechazarConMotivoCustom(){
  const txt = document.getElementById('motivoCustom').value.trim();
  if(!txt){ alert('Escribe el motivo o elige uno predefinido.'); return; }
  confirmarRechazoReserva(txt);
}

async function confirmarRechazoReserva(motivo){
  if(reservaRechazoId === null) return;
  const id = reservaRechazoId;
  try {
    await fetch(`${SUPABASE_URL}/rest/v1/reservas?id=eq.${id}`, {
      method:'PATCH', headers: getHeaders(),
      body: JSON.stringify({estado:'rechazada', motivo_rechazo: motivo})
    });
    reservaRechazoId = null;
    document.getElementById('motivoModal').classList.remove('show');
    cerrarModalReserva();
    fetchReservas();
  } catch(e){ alert('Error al rechazar la reserva'); }
}

function cancelarModalMotivo(){
  reservaRechazoId = null;
  document.getElementById('motivoModal').classList.remove('show');
}

// ── MODAL RESERVA NUEVA ──
function actualizarModalReserva(){
  const overlay = document.getElementById('reservaModal');
  if(!reservasPendientes.length){
    if(modalReservaActivaId !== null){
      modalReservaActivaId = null;
      overlay.classList.remove('show');
      pararAlarmaReserva();
    }
    return;
  }
  // No mostrar si hay un modal de pedido activo (prioridad pedidos)
  if(modalActivoId !== null) return;
  const res = reservasPendientes[0];
  if(modalReservaActivaId === res.id) return;
  modalReservaActivaId = res.id;
  renderModalReserva(res);
  overlay.classList.add('show');
  iniciarAlarmaReserva();
}

function renderModalReserva(res){
  document.getElementById('reservaModalId').textContent = `#${res.id}`;
  const notasHtml = res.notas ? `<div class="modal-notas">📝 ${res.notas}</div>` : '';
  document.getElementById('reservaModalBody').innerHTML = `
    <div class="modal-pickup" style="background:rgba(139,92,246,0.12);border-color:#8B5CF6;color:#C4B5FD;">📅 ${formatFechaCorta(res.fecha)} · 🕐 ${res.hora}</div>
    <div class="modal-info">
      <div class="modal-info-label">Cliente</div><div class="modal-info-value">${res.nombre}</div>
      <div class="modal-info-label">Personas</div><div class="modal-info-value">${res.personas} pax</div>
      <div class="modal-info-label">Teléfono</div><div class="modal-info-value">${res.telefono || '—'}</div>
      ${res.email ? `<div class="modal-info-label">Email</div><div class="modal-info-value" style="font-size:13px;">${res.email}</div>` : ''}
    </div>
    ${notasHtml}
  `;
  const pendExtra = reservasPendientes.length > 1 ? ` · ${reservasPendientes.length - 1} más esperando` : '';
  document.getElementById('reservaModalTiempo').textContent = `Reserva pendiente de confirmar${pendExtra}`;
}

function cerrarModalReserva(){
  modalReservaActivaId = null;
  document.getElementById('reservaModal').classList.remove('show');
  pararAlarmaReserva();
}

function iniciarAlarmaReserva(){
  if(alarmaReservaInterval) return;
  playNewOrder();
  alarmaReservaInterval = setInterval(() => {
    if(modalReservaActivaId !== null) playNewOrder();
  }, 4000);
}

function pararAlarmaReserva(){
  if(alarmaReservaInterval){
    clearInterval(alarmaReservaInterval);
    alarmaReservaInterval = null;
  }
}

async function modalReservaAceptar(){
  if(modalReservaActivaId === null) return;
  const id = modalReservaActivaId;
  const btn = document.getElementById('btnReservaAceptar');
  btn.disabled = true; btn.textContent = '⏳ Aceptando...';
  await reservaAceptar(id);
  btn.disabled = false; btn.textContent = '✅ Aceptar';
}

function modalReservaRechazar(){
  if(modalReservaActivaId === null) return;
  reservaRechazarPedirMotivo(modalReservaActivaId);
}

// ── MODAL CANCELACIÓN POR CLIENTE ──
let cancelacionesSinVer = [];
let modalCancelacionId = null;
let alarmaCancelacionInterval = null;

function actualizarModalCancelacion(){
  const overlay = document.getElementById('cancelacionModal');
  if(!overlay) return;
  if(!cancelacionesSinVer.length){
    if(modalCancelacionId !== null){
      modalCancelacionId = null;
      overlay.classList.remove('show');
      pararAlarmaCancelacion();
    }
    return;
  }
  // Prioridad: pedidos y reservas nuevas primero
  if(modalActivoId !== null || modalReservaActivaId !== null) return;
  const c = cancelacionesSinVer[0];
  if(modalCancelacionId === c.id) return;
  modalCancelacionId = c.id;
  const comentario = c.comentario_cancelacion ? `<div class="modal-notas" style="border-color:#F59E0B;color:#FCD34D;">💬 "${c.comentario_cancelacion}"</div>` : '';
  document.getElementById('cancelacionModalBody').innerHTML = `
    <div class="modal-pickup" style="background:rgba(239,68,68,0.12);border-color:#EF4444;color:#FCA5A5;">📅 ${formatFechaCorta(c.fecha)} · 🕐 ${c.hora}</div>
    <div class="modal-info">
      <div class="modal-info-label">Cliente</div><div class="modal-info-value">${c.nombre}</div>
      <div class="modal-info-label">Personas</div><div class="modal-info-value">${c.personas} pax</div>
      <div class="modal-info-label">Teléfono</div><div class="modal-info-value">${c.telefono || '—'}</div>
    </div>
    ${comentario}
  `;
  overlay.classList.add('show');
  iniciarAlarmaCancelacion();
}

function iniciarAlarmaCancelacion(){
  if(alarmaCancelacionInterval) return;
  playNewOrder();
  alarmaCancelacionInterval = setInterval(() => {
    if(modalCancelacionId !== null) playNewOrder();
  }, 4000);
}

function pararAlarmaCancelacion(){
  if(alarmaCancelacionInterval){
    clearInterval(alarmaCancelacionInterval);
    alarmaCancelacionInterval = null;
  }
}

async function modalCancelacionOk(){
  if(modalCancelacionId === null) return;
  const id = modalCancelacionId;
  const btn = document.getElementById('btnCancelacionOk');
  btn.disabled = true;
  btn.textContent = '⏳...';
  try {
    await fetch(`${SUPABASE_URL}/rest/v1/reservas?id=eq.${id}`, {
      method:'PATCH', headers: getHeaders(),
      body: JSON.stringify({kds_cancelacion_vista: true})
    });
    modalCancelacionId = null;
    document.getElementById('cancelacionModal').classList.remove('show');
    pararAlarmaCancelacion();
    btn.textContent = '✓ Visto'; btn.disabled = false;
    fetchReservas();
  } catch(e){
    btn.textContent = '✓ Visto'; btn.disabled = false;
  }
}

// ── MODAL SOLICITADO ──
function actualizarModal(){
  const overlay = document.getElementById('solicModal');
  if(!soliPendientes.length){
    if(modalActivoId !== null){
      modalActivoId = null;
      overlay.classList.remove('show');
      pararAlarma();
      // Dar paso al modal de reserva si hay pendientes
      setTimeout(actualizarModalReserva, 300);
    }
    return;
  }
  const ped = soliPendientes[0];
  if(modalActivoId === ped.id){
    actualizarTiempoModal(ped);
    return;
  }
  // Prioridad pedidos: si hay modal de reserva abierto, cerrarlo temporalmente
  if(modalReservaActivaId !== null){
    cerrarModalReserva();
  }
  modalActivoId = ped.id;
  renderModalContenido(ped);
  overlay.classList.add('show');
  iniciarAlarma();
}

function renderModalContenido(ped){
  document.getElementById('modalId').textContent = `#${ped.id}`;
  const items = itemsCache[ped.id] || [];
  const itemsHtml = items.map(i =>
    `<div class="modal-item">
      <span><span class="modal-item-qty">${i.cantidad}×</span><span class="modal-item-name">${i.nombre_producto}</span></span>
      <span class="modal-item-price">€${(i.precio_unitario * i.cantidad).toFixed(2)}</span>
    </div>`
  ).join('');
  const notasHtml = ped.notas ? `<div class="modal-notas">📝 ${ped.notas}</div>` : '';
  document.getElementById('modalBody').innerHTML = `
    <div class="modal-pickup">🕐 Recogida: ${ped.hora_recogida || '—'}</div>
    <div class="modal-info">
      <div class="modal-info-label">Cliente</div><div class="modal-info-value">${ped.nombre}</div>
      <div class="modal-info-label">Teléfono</div><div class="modal-info-value">${ped.telefono || '—'}</div>
      ${ped.email ? `<div class="modal-info-label">Email</div><div class="modal-info-value" style="font-size:13px;">${ped.email}</div>` : ''}
    </div>
    ${notasHtml}
    <div class="modal-items">
      <div class="modal-items-title">Productos</div>
      ${itemsHtml || '<div style="color:var(--muted);font-size:13px;">...</div>'}
      <div class="modal-total">
        <span>Total</span>
        <span class="modal-item-price">€${parseFloat(ped.total || 0).toFixed(2)}</span>
      </div>
    </div>
  `;
  actualizarTiempoModal(ped);
}

function actualizarTiempoModal(ped){
  const diffMin = Math.floor((Date.now() - new Date(ped.creado_at)) / 60000);
  let tiempoStr = diffMin < 1 ? 'recién llegado' : (diffMin === 1 ? 'hace 1 minuto' : `hace ${diffMin} minutos`);
  const pendientesExtra = soliPendientes.length > 1 ? ` · ${soliPendientes.length - 1} más esperando` : '';
  document.getElementById('modalTiempo').textContent = `Pedido ${tiempoStr}${pendientesExtra}`;
}

function iniciarAlarma(){
  if(alarmaInterval) return;
  playNewOrder();
  alarmaInterval = setInterval(() => {
    if(soliPendientes.length && modalActivoId !== null) playNewOrder();
  }, 4000);
}

function pararAlarma(){
  if(alarmaInterval){
    clearInterval(alarmaInterval);
    alarmaInterval = null;
  }
}

async function modalAceptar(){
  if(modalActivoId === null) return;
  const id = modalActivoId;
  const btnA = document.getElementById('btnAceptar');
  const btnR = document.getElementById('btnRechazar');
  btnA.disabled = true; btnR.disabled = true;
  btnA.textContent = '⏳ Aceptando...';
  try {
    await fetch(`${SUPABASE_URL}/rest/v1/pedidos?id=eq.${id}`, {
      method:'PATCH', headers: getHeaders(), body: JSON.stringify({estado:'pendiente'})
    });
    modalActivoId = null;
    soliPendientes = soliPendientes.filter(p => p.id !== id);
    document.getElementById('solicModal').classList.remove('show');
    pararAlarma();
    btnA.textContent = '✅ Aceptar'; btnA.disabled = false; btnR.disabled = false;
    fetchPedidos();
  } catch(e){
    btnA.textContent = '✅ Aceptar'; btnA.disabled = false; btnR.disabled = false;
    alert('Error al aceptar. Comprueba la conexión.');
  }
}

async function modalRechazar(){
  if(modalActivoId === null) return;
  if(!confirm('¿Rechazar este pedido? El cliente recibirá un email de aviso.')) return;
  const id = modalActivoId;
  const btnA = document.getElementById('btnAceptar');
  const btnR = document.getElementById('btnRechazar');
  btnA.disabled = true; btnR.disabled = true;
  btnR.textContent = '⏳ Rechazando...';
  try {
    await fetch(`${SUPABASE_URL}/rest/v1/pedidos?id=eq.${id}`, {
      method:'PATCH', headers: getHeaders(), body: JSON.stringify({estado:'rechazado'})
    });
    modalActivoId = null;
    soliPendientes = soliPendientes.filter(p => p.id !== id);
    document.getElementById('solicModal').classList.remove('show');
    pararAlarma();
    btnR.textContent = '❌ Rechazar'; btnA.disabled = false; btnR.disabled = false;
    fetchPedidos();
  } catch(e){
    btnR.textContent = '❌ Rechazar'; btnA.disabled = false; btnR.disabled = false;
    alert('Error al rechazar. Comprueba la conexión.');
  }
}

// ── MENSAJES DEL BACKOFFICE ──
let msgActivoId = null;
let msgAlarmaInterval = null;

async function fetchMensajes(){
  try {
    const r = await fetch(`${SUPABASE_URL}/rest/v1/kds_mensajes?atendido=eq.false&order=creado_at.asc&limit=5`, {headers: getHeaders()});
    if(!r.ok) return;
    const msgs = await r.json();

    // ACK: marcar mensajes como recibidos en KDS
    const msgSinAck = msgs.filter(m => !m.kds_recibido).map(m => m.id);
    if(msgSinAck.length){
      fetch(`${SUPABASE_URL}/rest/v1/kds_mensajes?id=in.(${msgSinAck.join(',')})`, {
        method:'PATCH', headers: getHeaders(),
        body: JSON.stringify({kds_recibido: true, kds_recibido_at: new Date().toISOString()})
      }).catch(()=>{});
    }
    if(!msgs.length){
      if(msgActivoId !== null){
        msgActivoId = null;
        document.getElementById('msgModal').classList.remove('show');
        pararAlarmaMsg();
      }
      return;
    }
    const m = msgs[0];
    if(msgActivoId === m.id) return;
    msgActivoId = m.id;
    document.getElementById('msgModalText').textContent = m.mensaje;
    const t = new Date(m.creado_at);
    document.getElementById('msgModalTime').textContent = `${String(t.getHours()).padStart(2,'0')}:${String(t.getMinutes()).padStart(2,'0')}`;
    document.getElementById('msgModal').classList.add('show');
    iniciarAlarmaMsg();
  } catch(e){}
}

function iniciarAlarmaMsg(){
  if(msgAlarmaInterval) return;
  playNewOrder();
  msgAlarmaInterval = setInterval(() => {
    if(msgActivoId !== null) playNewOrder();
  }, 4000);
}

function pararAlarmaMsg(){
  if(msgAlarmaInterval){
    clearInterval(msgAlarmaInterval);
    msgAlarmaInterval = null;
  }
}

async function modalMsgOk(){
  if(msgActivoId === null) return;
  const id = msgActivoId;
  const btn = document.getElementById('btnMsgOk');
  btn.disabled = true;
  btn.textContent = '⏳ Confirmando...';
  try {
    await fetch(`${SUPABASE_URL}/rest/v1/kds_mensajes?id=eq.${id}`, {
      method:'PATCH', headers: getHeaders(),
      body: JSON.stringify({atendido: true, atendido_at: new Date().toISOString()})
    });
    msgActivoId = null;
    document.getElementById('msgModal').classList.remove('show');
    pararAlarmaMsg();
    btn.textContent = '✓ OK, entendido'; btn.disabled = false;
    fetchMensajes();
  } catch(e){
    btn.textContent = '✓ OK, entendido'; btn.disabled = false;
  }
}

// ── LIMPIEZA MEDIANOCHE ──
// Borra rechazados/cancelados de días anteriores (no de hoy)
async function limpiarRechazadosAntiguos(){
  try {
    const hoy = new Date();
    const hoyStr = `${hoy.getFullYear()}-${String(hoy.getMonth()+1).padStart(2,'0')}-${String(hoy.getDate()).padStart(2,'0')}`;
    const inicioDia = encodeURIComponent(`${hoyStr}T00:00:00`);
    // Solo eliminamos rechazados/cancelados anteriores a hoy — no tocamos los de hoy
    const r = await fetch(`${SUPABASE_URL}/rest/v1/pedidos?estado=in.(rechazado,cancelado)&creado_at=lt.${inicioDia}&select=id`, {headers: getHeaders()});
    if(!r.ok) return;
    const antiguos = await r.json();
    if(!antiguos.length) return;
    const ids = antiguos.map(p => p.id).join(',');
    await fetch(`${SUPABASE_URL}/rest/v1/pedido_items?pedido_id=in.(${ids})`, {method:'DELETE', headers: getHeaders()});
    await fetch(`${SUPABASE_URL}/rest/v1/pedidos?id=in.(${ids})`, {method:'DELETE', headers: getHeaders()});
    console.log(`✅ Limpieza: ${antiguos.length} pedidos rechazados/cancelados de días anteriores eliminados`);
  } catch(e){}
}

// ── LOGIN GATE (Supabase Auth) ──
async function doLogin(){
  const passwordInput = document.getElementById('loginPassword');
  const password = passwordInput.value.trim();
  const errorEl = document.getElementById('loginError');
  const btn = document.getElementById('loginBtn');
  const gate = document.getElementById('loginGate');
  if(!password){
    errorEl.textContent = 'Introduce la contraseña';
    return;
  }
  errorEl.textContent = '';
  btn.disabled = true;
  btn.textContent = 'Comprobando...';
  try {
    const r = await fetch(`${SUPABASE_URL}/auth/v1/token?grant_type=password`, {
      method: 'POST',
      headers: {
        'apikey': SUPABASE_ANON_KEY,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({email: KDS_USER_EMAIL, password})
    });
    if(!r.ok){
      throw new Error('auth_failed');
    }
    const data = await r.json();
    authToken = data.access_token;
    authRefreshToken = data.refresh_token;
    const expiresAt = Date.now() + (data.expires_in * 1000);
    try {
      localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({
        access_token: authToken,
        refresh_token: authRefreshToken,
        expires_at: expiresAt
      }));
    } catch(e){}
    gate.style.display = 'none';
    passwordInput.value = '';
    startKds();
    // Programar refresh antes de que caduque (5 min antes)
    setTimeout(refreshAuthToken, Math.max(60000, (data.expires_in - 300) * 1000));
  } catch(e){
    gate.classList.add('shake');
    errorEl.textContent = 'Contraseña incorrecta';
    setTimeout(() => {
      gate.classList.remove('shake');
      passwordInput.value = '';
      passwordInput.focus();
    }, 400);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Entrar';
  }
}

async function refreshAuthToken(){
  if(!authRefreshToken) return;
  try {
    const r = await fetch(`${SUPABASE_URL}/auth/v1/token?grant_type=refresh_token`, {
      method: 'POST',
      headers: {
        'apikey': SUPABASE_ANON_KEY,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({refresh_token: authRefreshToken})
    });
    if(!r.ok) throw new Error('refresh_failed');
    const data = await r.json();
    authToken = data.access_token;
    authRefreshToken = data.refresh_token;
    const expiresAt = Date.now() + (data.expires_in * 1000);
    try {
      localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({
        access_token: authToken,
        refresh_token: authRefreshToken,
        expires_at: expiresAt
      }));
    } catch(e){}
    setTimeout(refreshAuthToken, Math.max(60000, (data.expires_in - 300) * 1000));
  } catch(e){
    console.error('Refresh token failed, requiring new login', e);
    try { localStorage.removeItem(AUTH_STORAGE_KEY); } catch(err){}
    authToken = null;
    authRefreshToken = null;
    location.reload();
  }
}

function comprobarLogin(){
  let stored = null;
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY);
    if(raw) stored = JSON.parse(raw);
  } catch(e){}

  if(stored && stored.access_token && stored.expires_at && stored.expires_at > Date.now() + 60000){
    // Token válido — usarlo
    authToken = stored.access_token;
    authRefreshToken = stored.refresh_token;
    startKds();
    const timeLeft = stored.expires_at - Date.now();
    setTimeout(refreshAuthToken, Math.max(60000, timeLeft - 300000));
  } else if(stored && stored.refresh_token){
    // Token caducado — intentar refresh
    authRefreshToken = stored.refresh_token;
    refreshAuthToken().then(() => startKds()).catch(() => mostrarLogin());
  } else {
    mostrarLogin();
  }
}

function mostrarLogin(){
  const gate = document.getElementById('loginGate');
  if(gate){
    gate.style.display = 'flex';
    setTimeout(() => document.getElementById('loginPassword')?.focus(), 100);
  } else {
    console.error('loginGate element not found');
  }
}

function startKds(){
  fetchPedidos();
  fetchReservas();
  fetchMensajes();
  limpiarRechazadosAntiguos();
  enviarHeartbeat();
  setInterval(fetchPedidos, 3000);
  setInterval(fetchReservas, 5000);
  setInterval(fetchMensajes, 3000);
  setInterval(limpiarRechazadosAntiguos, 3600000);
  setInterval(enviarHeartbeat, 30000);
}

// Heartbeat doble:
//  - last_seen: la app está corriendo (aunque sea en background)
//  - last_visible: la app está EN PANTALLA (visible, puede sonar y verse)
// El backoffice y las alertas distinguen: activo / oculto / sin señal.
function enviarHeartbeat(){
  const ahora = new Date().toISOString();
  const body = { last_seen: ahora, visibility_state: document.visibilityState };
  if(document.visibilityState === 'visible') body.last_visible = ahora;
  fetch(`${SUPABASE_URL}/rest/v1/kds_status?id=eq.1`, {
    method:'PATCH', headers: getHeaders(),
    body: JSON.stringify(body),
    keepalive: true
  }).catch(()=>{});
}

// Latido inmediato al cambiar de visibilidad (en ambos sentidos:
// al ocultarse registra el estado 'hidden'; al volver, acelera el 🟢)
document.addEventListener('visibilitychange', enviarHeartbeat);

// ── INIT ──
if(document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', comprobarLogin);
} else {
  comprobarLogin();
}

// Wake lock
let wakeLockRef = null;
async function keepAwake(){
  try {
    if('wakeLock' in navigator){
      wakeLockRef = await navigator.wakeLock.request('screen');
      wakeLockRef.addEventListener('release', () => { wakeLockRef = null; });
    }
  } catch(e){}
}
keepAwake();
document.addEventListener('visibilitychange', ()=>{
  if(document.visibilityState==='visible' && !wakeLockRef) keepAwake();
});
setInterval(() => { if(!wakeLockRef) keepAwake(); }, 60000);

// Service Worker
if('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/kds-sw.js').catch(()=>{});
}

// Fullscreen al desbloquear audio
function tryFullscreen(){
  const el = document.documentElement;
  if(el.requestFullscreen && !document.fullscreenElement) el.requestFullscreen().catch(()=>{});
  else if(el.webkitRequestFullscreen && !document.webkitFullscreenElement) el.webkitRequestFullscreen();
}

function unlockAudio(){
  try {
    if(!audioCtx) audioCtx = new (window.AudioContext||window.webkitAudioContext)();
    const o = audioCtx.createOscillator();
    const g = audioCtx.createGain();
    o.connect(g); g.connect(audioCtx.destination);
    g.gain.value = 0.001;
    o.frequency.value = 440;
    o.start(audioCtx.currentTime);
    o.stop(audioCtx.currentTime + 0.05);
    if(audioCtx.state === 'suspended') audioCtx.resume();
  } catch(e){}
  document.getElementById('audioUnlock').style.display = 'none';
  setTimeout(tryFullscreen, 100);
}
</script>

<!-- LOGIN GATE -->
<div id="loginGate" style="position:fixed;inset:0;background:#0D1117;z-index:99998;display:none;flex-direction:column;align-items:center;justify-content:center;padding:20px;">
  <img src="https://rwtpjqvgiiuvniixqapu.supabase.co/storage/v1/object/public/assets/Logo%20Vietnamito%20Final.png" alt="V" style="height:56px;margin-bottom:24px;">
  <div style="color:#F0F6FC;font-size:22px;font-weight:700;margin-bottom:6px;letter-spacing:.05em;">Vietnamito Dashboard</div>
  <div style="color:#8B949E;font-size:14px;margin-bottom:32px;">Introduce la contraseña de acceso</div>
  <input type="password" id="loginPassword" placeholder="Contraseña" autocomplete="current-password" style="width:280px;padding:14px 18px;background:#161B22;border:1px solid #30363D;color:#F0F6FC;font-size:18px;border-radius:10px;font-family:inherit;text-align:center;letter-spacing:.05em;" onkeypress="if(event.key==='Enter')doLogin()">
  <div id="loginError" style="color:#EF4444;font-size:13px;height:20px;margin-top:12px;font-weight:600;"></div>
  <button id="loginBtn" onclick="doLogin()" style="margin-top:12px;width:280px;padding:14px;background:linear-gradient(180deg,#22C55E,#16A34A);color:#fff;border:none;border-radius:10px;font-size:16px;font-weight:700;font-family:inherit;cursor:pointer;letter-spacing:.05em;">Entrar</button>
</div>

<style>
#loginGate.shake{animation:pinShake .35s ease}
@keyframes pinShake{0%,100%{transform:translateX(0)}20%,60%{transform:translateX(-8px)}40%,80%{transform:translateX(8px)}}
#loginPassword:focus{outline:none;border-color:#22C55E;box-shadow:0 0 0 3px rgba(34,197,94,0.15)}
#loginBtn:active{transform:scale(.97)}
#loginBtn:disabled{opacity:.6;cursor:wait}
</style>

<!-- UNLOCK AUDIO -->
<div id="audioUnlock" style="position:fixed;inset:0;background:rgba(0,0,0,0.95);z-index:99999;display:flex;align-items:center;justify-content:center;cursor:pointer;flex-direction:column;gap:18px;text-align:center;padding:30px;" onclick="unlockAudio()">
  <div style="font-size:64px;">🔔</div>
  <div style="color:#fff;font-size:22px;font-weight:700;letter-spacing:.05em;">Toca para activar el sonido</div>
  <div style="color:#888;font-size:14px;max-width:360px;line-height:1.5;">El navegador bloquea el audio hasta que interactúes. Sin esto, el dashboard no podrá avisarte cuando llegue un pedido.</div>
  <button style="margin-top:14px;background:#22C55E;color:#fff;border:none;padding:16px 40px;border-radius:10px;font-size:17px;font-weight:700;cursor:pointer;">Activar y entrar</button>
</div>

<!-- SOLICITADO MODAL -->
<div class="modal-overlay" id="solicModal" onclick="event.stopPropagation()">
  <div class="modal-card">
    <div class="modal-head">
      <div class="modal-bell">🔔</div>
      <div class="modal-title">Nuevo pedido — esperando confirmación</div>
      <div class="modal-id" id="modalId"></div>
    </div>
    <div class="modal-body" id="modalBody"></div>
    <div class="modal-tiempo" id="modalTiempo"></div>
    <div class="modal-actions">
      <button class="modal-btn modal-btn-rechazar" id="btnRechazar" onclick="modalRechazar()">❌ Rechazar</button>
      <button class="modal-btn modal-btn-aceptar" id="btnAceptar" onclick="modalAceptar()">✅ Aceptar</button>
    </div>
  </div>
</div>

<!-- RESERVA MODAL -->
<div class="modal-overlay" id="reservaModal" onclick="event.stopPropagation()">
  <div class="modal-card" style="border-color:#8B5CF6;">
    <div class="modal-head" style="background:linear-gradient(180deg, rgba(139,92,246,0.15), transparent);">
      <div class="modal-bell">🍽️</div>
      <div class="modal-title" style="color:#8B5CF6;">Nueva reserva — esperando confirmación</div>
      <div class="modal-id" id="reservaModalId"></div>
    </div>
    <div class="modal-body" id="reservaModalBody"></div>
    <div class="modal-tiempo" id="reservaModalTiempo"></div>
    <div class="modal-actions">
      <button class="modal-btn modal-btn-rechazar" id="btnReservaRechazar" onclick="modalReservaRechazar()">❌ Rechazar</button>
      <button class="modal-btn modal-btn-aceptar" id="btnReservaAceptar" onclick="modalReservaAceptar()">✅ Aceptar</button>
    </div>
  </div>
</div>

<!-- MOTIVO RECHAZO MODAL -->
<div class="modal-overlay" id="motivoModal" onclick="event.stopPropagation()" style="z-index:10000;">
  <div class="modal-card" style="border-color:#EF4444;animation:modalIn .25s ease;">
    <div class="modal-head">
      <div style="font-size:28px;">📝</div>
      <div class="modal-title">Motivo del rechazo</div>
    </div>
    <div class="modal-body">
      <div style="font-size:13px;color:var(--muted);margin-bottom:12px;">El cliente recibirá un email con este motivo:</div>
      <div id="motivosPredef" style="display:flex;flex-direction:column;gap:8px;margin-bottom:16px;"></div>
      <div style="font-size:12px;color:var(--muted);margin-bottom:6px;">O escribe un motivo personalizado:</div>
      <textarea id="motivoCustom" rows="3" style="width:100%;background:var(--surface-2);border:1px solid var(--border);border-radius:8px;color:var(--text);padding:10px 12px;font-family:inherit;font-size:14px;resize:none;box-sizing:border-box;" placeholder="Ej: Esa noche tenemos un evento privado..."></textarea>
    </div>
    <div class="modal-actions">
      <button class="modal-btn" onclick="cancelarModalMotivo()" style="background:transparent;border:1px solid var(--border);color:var(--muted);">← Volver</button>
      <button class="modal-btn modal-btn-rechazar" onclick="rechazarConMotivoCustom()">Rechazar con este motivo</button>
    </div>
  </div>
</div>

<style>
.motivo-btn{padding:12px 14px;background:var(--surface-2);border:1px solid var(--border);border-radius:8px;color:var(--text);font-size:14px;font-family:inherit;cursor:pointer;text-align:left;transition:all .15s}
.motivo-btn:hover,.motivo-btn:active{background:rgba(239,68,68,0.12);border-color:#EF4444;color:#FCA5A5}
</style>

<!-- CANCELACIÓN POR CLIENTE MODAL -->
<div class="modal-overlay" id="cancelacionModal" onclick="event.stopPropagation()">
  <div class="modal-card" style="border-color:#F59E0B;">
    <div class="modal-head" style="background:linear-gradient(180deg, rgba(245,158,11,0.15), transparent);">
      <div class="modal-bell">⚠️</div>
      <div class="modal-title" style="color:#F59E0B;">Reserva cancelada por el cliente</div>
    </div>
    <div class="modal-body" id="cancelacionModalBody"></div>
    <div class="modal-actions" style="grid-template-columns:1fr;">
      <button class="modal-btn" id="btnCancelacionOk" onclick="modalCancelacionOk()" style="background:linear-gradient(180deg, #F59E0B, #D97706);color:#fff;">✓ Visto</button>
    </div>
  </div>
</div>

<!-- MENSAJE MODAL -->
<div class="modal-overlay" id="msgModal" onclick="event.stopPropagation()">
  <div class="modal-card" style="border-color:#3B82F6;">
    <div class="modal-head" style="background:linear-gradient(180deg, rgba(59,130,246,0.15), transparent);">
      <div class="modal-bell">📢</div>
      <div class="modal-title" style="color:#3B82F6;">Mensaje del backoffice</div>
      <div class="modal-id" id="msgModalTime"></div>
    </div>
    <div class="modal-body">
      <div id="msgModalText" style="font-size:19px;line-height:1.55;color:var(--text);padding:14px 4px;font-weight:500;"></div>
    </div>
    <div class="modal-actions" style="grid-template-columns:1fr;">
      <button class="modal-btn" id="btnMsgOk" onclick="modalMsgOk()" style="background:linear-gradient(180deg, #3B82F6, #1D4ED8);color:#fff;">✓ OK, entendido</button>
    </div>
  </div>
</div>

</body>
</html>
