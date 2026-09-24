
import streamlit as st
import streamlit.components.v1 as components
import json
from pathlib import Path
from datetime import datetime

st.set_page_config(
    page_title="Sky Jumper",
    page_icon="🟨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

SCORES_FILE = Path("scores.json")

def load_scores():
    if not SCORES_FILE.exists():
        return []
    try:
        data = json.loads(SCORES_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []

def save_score(name, score):
    scores = load_scores()
    scores.append({
        "nombre": name.strip()[:30] or "Anónimo",
        "puntaje": int(score),
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    scores = sorted(scores, key=lambda x: x["puntaje"], reverse=True)[:50]
    SCORES_FILE.write_text(
        json.dumps(scores, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

st.markdown("""
<style>
    .stApp {
        background: radial-gradient(circle at top, #182033 0%, #0b0f17 52%, #07090d 100%);
        color: #f4f4f4;
    }
    [data-testid="stHeader"] { background: transparent; }
    .block-container {
        max-width: 1180px;
        padding-top: 1.2rem;
        padding-bottom: 2rem;
    }
    .hero-title {
        font-size: clamp(2.2rem, 6vw, 4.8rem);
        font-weight: 900;
        letter-spacing: -0.05em;
        margin-bottom: 0;
        line-height: 0.95;
    }
    .hero-accent { color: #ffd54a; }
    .subtitle {
        color: #b9c2d0;
        font-size: 1.05rem;
        margin-top: .7rem;
        margin-bottom: 1.4rem;
    }
    .info-card {
        border: 1px solid rgba(255,255,255,.10);
        background: rgba(255,255,255,.04);
        border-radius: 18px;
        padding: 14px 16px;
        min-height: 88px;
    }
    .info-card b { color: #ffd54a; }
    .stButton > button {
        border-radius: 12px;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="hero-title">SKY <span class="hero-accent">JUMPER</span></div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="subtitle">Salta de plataforma en plataforma, evita los obstáculos y llega lo más alto posible.</div>',
    unsafe_allow_html=True
)

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown('<div class="info-card"><b>← → / A D</b><br>Mueve al personaje.</div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="info-card"><b>Plataformas móviles</b><br>Cada vez son más difíciles.</div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="info-card"><b>Obstáculos rojos</b><br>Te empujan hacia abajo.</div>', unsafe_allow_html=True)

game_html = r"""
<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<style>
html,body{margin:0;background:transparent;font-family:Inter,system-ui,Arial,sans-serif;overflow:hidden}
.wrap{
  width:100%;
  display:flex;
  justify-content:center;
  padding:14px 0 4px;
}
.shell{
  width:min(920px,96vw);
  background:#0d121c;
  border:1px solid rgba(255,255,255,.12);
  border-radius:24px;
  box-shadow:0 24px 80px rgba(0,0,0,.38);
  overflow:hidden;
}
.topbar{
  display:flex;
  justify-content:space-between;
  gap:12px;
  padding:12px 18px;
  background:#111827;
  color:white;
  font-weight:800;
}
.pill{
  background:#1c2534;
  border:1px solid rgba(255,255,255,.08);
  border-radius:999px;
  padding:7px 12px;
}
canvas{
  display:block;
  width:100%;
  background:linear-gradient(#121b2d,#0a0e16 72%);
}
.overlay{
  position:absolute;
  inset:0;
  display:flex;
  align-items:center;
  justify-content:center;
  pointer-events:none;
}
.panel{
  pointer-events:auto;
  width:min(430px,82%);
  padding:24px;
  border-radius:22px;
  color:white;
  text-align:center;
  background:rgba(7,10,16,.93);
  border:1px solid rgba(255,255,255,.15);
  box-shadow:0 24px 90px rgba(0,0,0,.55);
}
.panel h2{font-size:34px;margin:0 0 8px}
.panel p{color:#b8c0ce}
button{
  border:0;
  border-radius:12px;
  padding:12px 18px;
  font-weight:800;
  cursor:pointer;
  background:#ffd54a;
  color:#171717;
  font-size:16px;
}
.small{font-size:13px;color:#8893a5;margin-top:12px}
.game{position:relative}
</style>
</head>
<body>
<div class="wrap">
  <div class="shell">
    <div class="topbar">
      <div class="pill">ALTURA: <span id="height">0</span> m</div>
      <div class="pill">PUNTAJE: <span id="score">0</span></div>
      <div class="pill">RÉCORD: <span id="best">0</span></div>
    </div>
    <div class="game">
      <canvas id="game" width="900" height="560"></canvas>
      <div class="overlay" id="overlay">
        <div class="panel">
          <h2>Sky Jumper</h2>
          <p>Llega tan alto como puedas. El personaje salta automáticamente.</p>
          <button onclick="startGame()">JUGAR</button>
          <div class="small">Controles: ← → o A / D</div>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");
const W = canvas.width, H = canvas.height;
const overlay = document.getElementById("overlay");
const heightEl = document.getElementById("height");
const scoreEl = document.getElementById("score");
const bestEl = document.getElementById("best");

let keys = {};
let player, platforms, hazards, cameraY, score, best, running, worldTop, frame;

best = Number(localStorage.getItem("skyJumperBest") || 0);
bestEl.textContent = best;

addEventListener("keydown", e => {
  keys[e.key.toLowerCase()] = true;
  if(["arrowleft","arrowright"," "].includes(e.key.toLowerCase())) e.preventDefault();
});
addEventListener("keyup", e => keys[e.key.toLowerCase()] = false);

function resetGame(){
  player = {x:W/2-16, y:H-90, w:32, h:42, vx:0, vy:-12.2, grounded:false};
  platforms = [];
  hazards = [];
  cameraY = 0;
  score = 0;
  worldTop = -2200;
  frame = 0;

  platforms.push({x:W/2-80,y:H-35,w:160,h:16,vx:0,base:true});
  let y = H-130;
  for(let i=0;i<34;i++){
    const w = 90 + Math.random()*80;
    const x = 30 + Math.random()*(W-w-60);
    const speed = i < 3 ? 0 : (Math.random() < .72 ? (0.7 + Math.random()*1.7) * (Math.random()<.5?-1:1) : 0);
    platforms.push({x,y,w,h:14,vx:speed, minX:16, maxX:W-w-16});
    if(i > 4 && i % 4 === 0){
      hazards.push({
        x: 45 + Math.random()*(W-110),
        y: y-55-Math.random()*80,
        w: 50+Math.random()*45,
        h: 18,
        vx: (1.2+Math.random()*1.6)*(Math.random()<.5?-1:1)
      });
    }
    y -= 90 + Math.random()*45;
  }
}

function startGame(){
  resetGame();
  running = true;
  overlay.style.display = "none";
  requestAnimationFrame(loop);
}

function endGame(){
  running = false;
  const finalScore = Math.max(0, Math.floor(score));
  if(finalScore > best){
    best = finalScore;
    localStorage.setItem("skyJumperBest", best);
    bestEl.textContent = best;
  }
  overlay.style.display = "flex";
  overlay.innerHTML = `
    <div class="panel">
      <h2>Fin del juego</h2>
      <p>Llegaste a <b>${Math.floor(score/10)} m</b> y lograste <b>${finalScore} puntos</b>.</p>
      <button onclick="startGame()">VOLVER A JUGAR</button>
      <div class="small">Anota tu puntaje en el formulario de Streamlit debajo del juego.</div>
    </div>`;
  try {
    window.parent.postMessage({type:"sky_jumper_score", score:finalScore}, "*");
  } catch(e){}
}

function collidePlatform(p){
  const prevBottom = player.y + player.h - player.vy;
  const bottom = player.y + player.h;
  return player.vy > 0 &&
    player.x + player.w > p.x &&
    player.x < p.x + p.w &&
    prevBottom <= p.y + 6 &&
    bottom >= p.y &&
    bottom <= p.y + p.h + 12;
}

function intersects(a,b){
  return a.x < b.x+b.w && a.x+a.w > b.x && a.y < b.y+b.h && a.y+a.h > b.y;
}

function update(){
  frame++;

  let dir = 0;
  if(keys["arrowleft"] || keys["a"]) dir--;
  if(keys["arrowright"] || keys["d"]) dir++;
  player.vx += dir * .72;
  player.vx *= .86;
  player.vx = Math.max(-6.2,Math.min(6.2,player.vx));

  player.vy += .53;
  player.x += player.vx;
  player.y += player.vy;

  if(player.x < -player.w) player.x = W;
  if(player.x > W) player.x = -player.w;

  for(const p of platforms){
    p.x += p.vx || 0;
    if(p.vx){
      if(p.x <= 10 || p.x+p.w >= W-10) p.vx *= -1;
    }
    if(collidePlatform(p)){
      player.y = p.y-player.h;
      player.vy = -12.2;
    }
  }

  for(const h of hazards){
    h.x += h.vx;
    if(h.x <= 10 || h.x+h.w >= W-10) h.vx *= -1;
    if(intersects(player,h)){
      player.vy = 13;
      player.vx += h.vx*1.4;
      score = Math.max(0, score-80);
    }
  }

  const screenY = player.y - cameraY;
  if(screenY < H*0.40){
    const delta = H*0.40-screenY;
    cameraY -= delta;
    score += delta * .36;
  }

  const height = Math.max(0, Math.floor((-cameraY)/10));
  heightEl.textContent = height;
  scoreEl.textContent = Math.floor(score);

  if(player.y-cameraY > H+140) endGame();
}

function drawBackground(){
  ctx.fillStyle="#0a0f18";
  ctx.fillRect(0,0,W,H);

  for(let i=0;i<55;i++){
    const sx=(i*173)%W;
    const sy=((i*97 + Math.floor(-cameraY*.12))%H+H)%H;
    ctx.globalAlpha=.3+(i%4)*.13;
    ctx.fillStyle="#dfe9ff";
    ctx.fillRect(sx,sy,2,2);
  }
  ctx.globalAlpha=1;

  const grad=ctx.createLinearGradient(0,0,0,H);
  grad.addColorStop(0,"rgba(38,58,94,.28)");
  grad.addColorStop(1,"rgba(0,0,0,0)");
  ctx.fillStyle=grad;
  ctx.fillRect(0,0,W,H);
}

function draw(){
  drawBackground();

  ctx.save();
  ctx.translate(0,-cameraY);

  for(const p of platforms){
    ctx.fillStyle=p.base ? "#ffd54a" : "#e8edf4";
    ctx.fillRect(p.x,p.y,p.w,p.h);
    ctx.fillStyle="rgba(0,0,0,.22)";
    ctx.fillRect(p.x,p.y+p.h,p.w,5);
  }

  for(const h of hazards){
    ctx.fillStyle="#ff4d5a";
    ctx.fillRect(h.x,h.y,h.w,h.h);
    ctx.fillStyle="#7b1722";
    for(let x=h.x+6;x<h.x+h.w-2;x+=14){
      ctx.beginPath();
      ctx.moveTo(x,h.y);
      ctx.lineTo(x+7,h.y-10);
      ctx.lineTo(x+14,h.y);
      ctx.fill();
    }
  }

  // character
  ctx.fillStyle="#ffd54a";
  ctx.fillRect(player.x,player.y,player.w,player.h);
  ctx.fillStyle="#171717";
  ctx.fillRect(player.x+7,player.y+10,5,5);
  ctx.fillRect(player.x+21,player.y+10,5,5);
  ctx.fillRect(player.x+10,player.y+28,13,4);

  ctx.restore();
}

function loop(){
  if(!running) return;
  update();
  draw();
  requestAnimationFrame(loop);
}

resetGame();
draw();
</script>
</body>
</html>
"""

components.html(game_html, height=690, scrolling=False)

st.markdown("### Registrar puntaje")
st.caption(
    "Escribe el puntaje mostrado al terminar la partida. "
    "En Streamlit Community Cloud el archivo de puntajes puede reiniciarse si la app se vuelve a desplegar."
)

with st.form("score_form", clear_on_submit=True):
    col_a, col_b = st.columns([2,1])
    with col_a:
        name = st.text_input("Nombre", placeholder="Ej. Jorge")
    with col_b:
        score_input = st.number_input("Puntaje", min_value=0, step=1)
    submitted = st.form_submit_button("Guardar puntaje", use_container_width=True)

    if submitted:
        save_score(name, score_input)
        st.success("Puntaje guardado.")

scores = load_scores()

st.markdown("### 🏆 Tabla de puntajes")
if scores:
    top = scores[:10]
    st.dataframe(
        top,
        column_order=("nombre", "puntaje", "fecha"),
        hide_index=True,
        use_container_width=True,
    )
else:
    st.info("Todavía no hay puntajes registrados.")

with st.expander("Cómo jugar"):
    st.markdown("""
- El personaje salta automáticamente.
- Muévete con **← / →** o **A / D**.
- Aterriza sobre las plataformas blancas.
- Algunas plataformas se mueven horizontalmente.
- Los obstáculos rojos te empujan hacia abajo y descuentan puntos.
- Mientras más alto llegues, mayor será tu puntuación.
- Cuando caigas fuera de la pantalla, termina la partida.
""")
