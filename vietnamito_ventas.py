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
    <span class="logo-text">Vietnamito Dashboard <span class="kds-version">v20260708-1952</span></span>
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
const SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ3dHBqcXZnaWl1dm5paXhxYXB1Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NjkzNjE5NCwiZXhwIjoyMDYyNTEyMTk0fQ.mMOSwlrEEnLmyMcWLZaS_HP2HdyRq4TF2CqBaVn9Dw0";
const headers = {'apikey': SUPABASE_KEY, 'Authorization': `Bearer ${SUPABASE_KEY}`, 'Content-Type': 'application/json'};

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
    // Solicitados + aceptados (pendiente/preparando/listo/entregado) + rechazados/cancelados de hoy
    const hoy = new Date();
    const hoyStr = `${hoy.getFullYear()}-${String(hoy.getMonth()+1).padStart(2,'0')}-${String(hoy.getDate()).padStart(2,'0')}`;
    const inicioDia = `${hoyStr}T00:00:00`;

    const r = await fetch(
      `${SUPABASE_URL}/rest/v1/pedidos?or=(estado.eq.solicitado,estado.eq.pendiente,estado.eq.preparando,estado.eq.listo,estado.eq.entregado,and(estado.in.(rechazado,cancelado),creado_at.gte.${inicioDia}))&order=creado_at.asc&limit=200`,
      {headers}
    );
    if(!r.ok) throw new Error(r.status);
    const data = await r.json();

    // Items cache — solo pedimos los que no tenemos
    const newIds = data.map(p=>p.id).filter(id => !itemsCache[id]);
    if(newIds.length){
      const ri = await fetch(`${SUPABASE_URL}/rest/v1/pedido_items?pedido_id=in.(${newIds.join(',')})`, {headers});
      const items = await ri.json();
      newIds.forEach(id => { itemsCache[id] = items.filter(i => i.pedido_id === id); });
    }

    // Detectar nuevos solicitados para alarma
    const currentSolicIds = new Set(data.filter(p=>p.estado==='solicitado').map(p=>p.id));
    const isNewSolic = [...currentSolicIds].filter(id => !lastPendienteIds.has(id));
    lastPendienteIds = currentSolicIds;

    pedidos = data;

    // Modal para el más antiguo solicitado
    soliPendientes = data.filter(p => p.estado === 'solicitado').sort((a,b) => new Date(a.creado_at) - new Date(b.creado_at));
    actualizarModal();

    render();
    setOnline(true);
  } catch(e){
    console.error(e);
    setOnline(false);
  }
}

// ── FETCH RESERVAS ──
let reservas = [];
async function fetchReservas(){
  try {
    const hoy = new Date();
    const hoyStr = `${hoy.getFullYear()}-${String(hoy.getMonth()+1).padStart(2,'0')}-${String(hoy.getDate()).padStart(2,'0')}`;
    const r = await fetch(`${SUPABASE_URL}/rest/v1/reservas?fecha=eq.${hoyStr}&order=hora.asc&limit=50`, {headers});
    if(!r.ok) return;
    reservas = await r.json();
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
  const activas = reservas.filter(r => r.estado !== 'cancelada');
  document.getElementById('badge-reservas').textContent = activas.length;
  if(!reservas.length){
    container.innerHTML = `<div class="empty">Sin reservas hoy</div>`;
    return;
  }
  container.innerHTML = reservas.map(r => {
    const cls = r.estado === 'cancelada' ? 'cancelada' : (r.estado === 'confirmada' ? 'confirmada' : '');
    const notas = r.notas ? `<div class="reserva-notas">📝 ${r.notas}</div>` : '';
    return `<div class="reserva ${cls}">
      <div class="reserva-hora">${r.hora}</div>
      <div class="reserva-nombre">${r.nombre}</div>
      <div class="reserva-info"><span class="reserva-personas">${r.personas} pax</span>📞 ${r.telefono||'—'}</div>
      ${notas}
    </div>`;
  }).join('');
}

// ── ACCIONES ──
async function pedidoAceptar(id){
  try {
    await fetch(`${SUPABASE_URL}/rest/v1/pedidos?id=eq.${id}`, {
      method:'PATCH', headers, body: JSON.stringify({estado:'pendiente'})
    });
    fetchPedidos();
  } catch(e){ alert('Error al aceptar'); }
}

async function pedidoRechazar(id){
  if(!confirm('¿Rechazar este pedido? El cliente recibirá un email de aviso.')) return;
  try {
    await fetch(`${SUPABASE_URL}/rest/v1/pedidos?id=eq.${id}`, {
      method:'PATCH', headers, body: JSON.stringify({estado:'rechazado'})
    });
    fetchPedidos();
  } catch(e){ alert('Error al rechazar'); }
}

async function pedidoCancelar(id, nombre){
  if(!confirm(`⚠️ ¿Cancelar el pedido ya aceptado de ${nombre}?\n\nSe enviará un email de cancelación al cliente.\n\nSolo hazlo si es realmente necesario.`)) return;
  try {
    await fetch(`${SUPABASE_URL}/rest/v1/pedidos?id=eq.${id}`, {
      method:'PATCH', headers, body: JSON.stringify({estado:'cancelado'})
    });
    fetchPedidos();
  } catch(e){ alert('Error al cancelar'); }
}

async function borrarSilencioso(id, nombre){
  if(!confirm(`🗑️ ¿Borrar el pedido #${id} de ${nombre} SIN enviar email al cliente?\n\nEsto no se puede deshacer.`)) return;
  try {
    await fetch(`${SUPABASE_URL}/rest/v1/pedido_items?pedido_id=eq.${id}`, {method:'DELETE', headers});
    await fetch(`${SUPABASE_URL}/rest/v1/pedidos?id=eq.${id}`, {method:'DELETE', headers});
    delete itemsCache[id];
    fetchPedidos();
  } catch(e){ alert('Error al borrar'); }
}

// ── MODAL SOLICITADO ──
function actualizarModal(){
  const overlay = document.getElementById('solicModal');
  if(!soliPendientes.length){
    if(modalActivoId !== null){
      modalActivoId = null;
      overlay.classList.remove('show');
      pararAlarma();
    }
    return;
  }
  const ped = soliPendientes[0];
  if(modalActivoId === ped.id){
    actualizarTiempoModal(ped);
    return;
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
      method:'PATCH', headers, body: JSON.stringify({estado:'pendiente'})
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
      method:'PATCH', headers, body: JSON.stringify({estado:'rechazado'})
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
    const r = await fetch(`${SUPABASE_URL}/rest/v1/kds_mensajes?atendido=eq.false&order=creado_at.asc&limit=5`, {headers});
    if(!r.ok) return;
    const msgs = await r.json();
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
      method:'PATCH', headers,
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
    const inicioDia = `${hoyStr}T00:00:00`;
    // Solo eliminamos rechazados/cancelados anteriores a hoy — no tocamos los de hoy
    const r = await fetch(`${SUPABASE_URL}/rest/v1/pedidos?estado=in.(rechazado,cancelado)&creado_at=lt.${inicioDia}&select=id`, {headers});
    if(!r.ok) return;
    const antiguos = await r.json();
    if(!antiguos.length) return;
    const ids = antiguos.map(p => p.id).join(',');
    await fetch(`${SUPABASE_URL}/rest/v1/pedido_items?pedido_id=in.(${ids})`, {method:'DELETE', headers});
    await fetch(`${SUPABASE_URL}/rest/v1/pedidos?id=in.(${ids})`, {method:'DELETE', headers});
    console.log(`✅ Limpieza: ${antiguos.length} pedidos rechazados/cancelados de días anteriores eliminados`);
  } catch(e){}
}

// ── INIT ──
fetchPedidos();
fetchReservas();
fetchMensajes();
limpiarRechazadosAntiguos();

setInterval(fetchPedidos, 3000);
setInterval(fetchReservas, 30000); // reservas cambian menos
setInterval(fetchMensajes, 3000);
setInterval(limpiarRechazadosAntiguos, 3600000); // cada hora

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
