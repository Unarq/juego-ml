
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
    st.markdown('<div class="info-card"><b>Ruta alcanzable</b><br>Siempre existe una plataforma posible.</div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="info-card"><b>Power-ups</b><br>Super salto o modo mini aleatorio.</div>', unsafe_allow_html=True)

game_html = r"""
<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<style>
html,body{margin:0;background:transparent;font-family:Inter,system-ui,Arial,sans-serif;overflow:hidden}
.wrap{width:100%;display:flex;justify-content:center;padding:14px 0 4px}
.shell{width:min(920px,96vw);background:#0d121c;border:1px solid rgba(255,255,255,.12);
border-radius:24px;box-shadow:0 24px 80px rgba(0,0,0,.38);overflow:hidden}
.topbar{display:flex;justify-content:space-between;gap:8px;padding:12px 14px;background:#111827;color:white;font-weight:800;flex-wrap:wrap}
.pill{background:#1c2534;border:1px solid rgba(255,255,255,.08);border-radius:999px;padding:7px 11px;font-size:14px}
canvas{display:block;width:100%;background:linear-gradient(#15233a,#0a0e16 72%)}
.overlay{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;pointer-events:none}
.panel{pointer-events:auto;width:min(440px,82%);padding:24px;border-radius:22px;color:white;text-align:center;
background:rgba(7,10,16,.94);border:1px solid rgba(255,255,255,.15);box-shadow:0 24px 90px rgba(0,0,0,.55)}
.panel h2{font-size:34px;margin:0 0 8px}.panel p{color:#b8c0ce}
button{border:0;border-radius:12px;padding:12px 18px;font-weight:800;cursor:pointer;background:#ffd54a;color:#171717;font-size:16px}
.small{font-size:13px;color:#8893a5;margin-top:12px}.game{position:relative}
</style>
</head>
<body>
<div class="wrap">
<div class="shell">
  <div class="topbar">
    <div class="pill">ALTURA: <span id="height">0</span> m</div>
    <div class="pill">PUNTAJE: <span id="score">0</span></div>
    <div class="pill">EFECTO: <span id="effect">NORMAL</span></div>
    <div class="pill">RÉCORD: <span id="best">0</span></div>
  </div>
  <div class="game">
    <canvas id="game" width="900" height="560"></canvas>
    <div class="overlay" id="overlay">
      <div class="panel">
        <h2>🦗 Sky Jumper</h2>
        <p>Un saltamontes que quiere llegar hasta el cielo. Las plataformas se vuelven más rápidas y aparecen mejoras aleatorias.</p>
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
const effectEl = document.getElementById("effect");

let keys = {};
let player, platforms, hazards, powerups, cameraY, score, best, running, frame;
let effectTimer = 0;
let currentEffect = "NORMAL";

best = Number(localStorage.getItem("skyJumperBest") || 0);
bestEl.textContent = best;

addEventListener("keydown", e => {
  keys[e.key.toLowerCase()] = true;
  if(["arrowleft","arrowright"," "].includes(e.key.toLowerCase())) e.preventDefault();
});
addEventListener("keyup", e => keys[e.key.toLowerCase()] = false);

function rand(a,b){ return a + Math.random()*(b-a); }
function clamp(v,a,b){ return Math.max(a,Math.min(b,v)); }

function addReachablePlatforms(){
  platforms = [];
  hazards = [];
  powerups = [];

  const base = {x:W/2-90,y:H-35,w:180,h:16,vx:0,base:true,safe:true};
  platforms.push(base);

  let prev = base;

  for(let i=0;i<42;i++){
    // Guaranteed reachable vertical separation.
    // Normal jump rises roughly 135 px, so safe gap stays <= 100–112 px.
    const difficulty = Math.min(1, i/34);
    const gapY = rand(78, 96 + difficulty*14);

    // Limit horizontal displacement from previous platform.
    // This keeps at least one route physically reachable.
    const maxDx = 125 + difficulty*35;
    let center = prev.x + prev.w/2 + rand(-maxDx,maxDx);

    const w = rand(90,145) - difficulty*18;
    center = clamp(center, 35+w/2, W-35-w/2);

    const p = {
      x:center-w/2,
      y:prev.y-gapY,
      w:w,
      h:14,
      vx: i<4 ? 0 : (Math.random()<0.68 ? rand(.55,1.2+difficulty*1.25)*(Math.random()<.5?-1:1) : 0),
      safe:true
    };
    platforms.push(p);

    // Decorative/bonus platform, not required for progression.
    if(i>4 && Math.random()<0.23){
      const bw = rand(65,95);
      platforms.push({
        x:rand(20,W-bw-20),
        y:p.y-rand(28,60),
        w:bw,h:12,
        vx:rand(.8,1.7)*(Math.random()<.5?-1:1),
        bonus:true
      });
    }

    // Hazards never completely block the guaranteed landing platform.
    if(i>5 && i%4===0){
      let hx = rand(25,W-95);
      if(hx < p.x+p.w+35 && hx+70 > p.x-35){
        hx = p.x > W/2 ? 25 : W-105;
      }
      hazards.push({
        x:hx,
        y:p.y-rand(45,78),
        w:rand(48,72),
        h:18,
        vx:rand(.85,1.65)*(Math.random()<.5?-1:1)
      });
    }

    // Random power-ups on reachable platforms.
    if(i>3 && Math.random()<0.18){
      const type = Math.random()<0.52 ? "SUPER" : "TINY";
      powerups.push({
        x:p.x+p.w/2-12,
        y:p.y-31,
        w:24,h:24,
        type,
        active:true,
        bob:Math.random()*6.28
      });
    }

    prev = p;
  }
}

function resetGame(){
  player = {
    x:W/2-18, y:H-90,
    normalW:36, normalH:34,
    w:36,h:34,
    vx:0, vy:-12.2,
    jumpPower:12.2
  };
  cameraY=0; score=0; frame=0;
  effectTimer=0; currentEffect="NORMAL";
  effectEl.textContent="NORMAL";
  addReachablePlatforms();
}

function startGame(){
  resetGame();
  running=true;
  overlay.style.display="none";
  requestAnimationFrame(loop);
}

function setEffect(type){
  currentEffect=type;
  effectTimer=60*7;

  if(type==="SUPER"){
    player.jumpPower=16.2;
    player.w=player.normalW;
    player.h=player.normalH;
    effectEl.textContent="⚡ SUPER SALTO";
  }else{
    player.jumpPower=11.5;
    player.w=20;
    player.h=19;
    effectEl.textContent="🔹 MINI";
  }
}

function clearEffect(){
  currentEffect="NORMAL";
  player.jumpPower=12.2;
  player.w=player.normalW;
  player.h=player.normalH;
  effectEl.textContent="NORMAL";
}

function endGame(){
  running=false;
  const finalScore=Math.max(0,Math.floor(score));
  if(finalScore>best){
    best=finalScore;
    localStorage.setItem("skyJumperBest",best);
    bestEl.textContent=best;
  }
  overlay.style.display="flex";
  overlay.innerHTML=`
    <div class="panel">
      <h2>Fin del salto</h2>
      <p>Tu saltamontes llegó a <b>${Math.floor(score/10)} m</b> y consiguió <b>${finalScore} puntos</b>.</p>
      <button onclick="startGame()">VOLVER A JUGAR</button>
      <div class="small">Registra tu nombre y puntaje debajo del juego.</div>
    </div>`;
}

function collidePlatform(p){
  const prevBottom=player.y+player.h-player.vy;
  const bottom=player.y+player.h;
  return player.vy>0 &&
    player.x+player.w>p.x &&
    player.x<p.x+p.w &&
    prevBottom<=p.y+7 &&
    bottom>=p.y &&
    bottom<=p.y+p.h+14;
}

function intersects(a,b){
  return a.x<b.x+b.w && a.x+a.w>b.x && a.y<b.y+b.h && a.y+a.h>b.y;
}

function update(){
  frame++;

  let dir=0;
  if(keys["arrowleft"]||keys["a"]) dir--;
  if(keys["arrowright"]||keys["d"]) dir++;

  let accel=currentEffect==="TINY" ? .61 : .72;
  let maxSpeed=currentEffect==="TINY" ? 5.2 : 6.2;

  player.vx += dir*accel;
  player.vx *= .86;
  player.vx=clamp(player.vx,-maxSpeed,maxSpeed);

  player.vy += .53;
  player.x += player.vx;
  player.y += player.vy;

  if(player.x<-player.w) player.x=W;
  if(player.x>W) player.x=-player.w;

  for(const p of platforms){
    p.x += p.vx||0;
    if(p.vx && (p.x<=10 || p.x+p.w>=W-10)) p.vx*=-1;

    if(collidePlatform(p)){
      player.y=p.y-player.h;
      player.vy=-player.jumpPower;
      if(p.bonus) score+=22;
    }
  }

  for(const h of hazards){
    h.x += h.vx;
    if(h.x<=10 || h.x+h.w>=W-10) h.vx*=-1;
    if(intersects(player,h)){
      player.vy=13.5;
      player.vx += h.vx*1.55;
      score=Math.max(0,score-90);
    }
  }

  for(const pu of powerups){
    if(!pu.active) continue;
    pu.bob += .06;
    if(intersects(player,pu)){
      pu.active=false;
      setEffect(pu.type);
      score += 40;
    }
  }

  if(effectTimer>0){
    effectTimer--;
    if(effectTimer===0) clearEffect();
  }

  const screenY=player.y-cameraY;
  if(screenY<H*.40){
    const delta=H*.40-screenY;
    cameraY-=delta;
    score+=delta*.36;
  }

  const height=Math.max(0,Math.floor((-cameraY)/10));
  heightEl.textContent=height;
  scoreEl.textContent=Math.floor(score);

  if(player.y-cameraY>H+150) endGame();
}

function drawGrasshopper(){
  const x=player.x, y=player.y, w=player.w, h=player.h;
  const cx=x+w/2, cy=y+h/2;

  ctx.strokeStyle="#9fd43b";
  ctx.lineWidth=Math.max(2,w*.09);

  // rear legs
  ctx.beginPath();
  ctx.moveTo(cx-w*.20,cy+h*.12);
  ctx.lineTo(x-w*.28, y+h*.78);
  ctx.lineTo(x+w*.05, y+h*.68);
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(cx+w*.15,cy+h*.12);
  ctx.lineTo(x+w*1.23,y+h*.78);
  ctx.lineTo(x+w*.93,y+h*.68);
  ctx.stroke();

  // body
  ctx.fillStyle="#72b52e";
  ctx.beginPath();
  ctx.ellipse(cx,cy,w*.37,h*.32,0,0,Math.PI*2);
  ctx.fill();

  // head
  ctx.fillStyle="#9fd43b";
  ctx.beginPath();
  ctx.arc(x+w*.66,y+h*.34,Math.max(4,w*.20),0,Math.PI*2);
  ctx.fill();

  // eye
  ctx.fillStyle="#101711";
  ctx.beginPath();
  ctx.arc(x+w*.72,y+h*.29,Math.max(1.7,w*.045),0,Math.PI*2);
  ctx.fill();

  // antennae
  ctx.strokeStyle="#b9e75e";
  ctx.lineWidth=1.5;
  ctx.beginPath();
  ctx.moveTo(x+w*.73,y+h*.18);
  ctx.lineTo(x+w*.92,y-h*.14);
  ctx.moveTo(x+w*.66,y+h*.17);
  ctx.lineTo(x+w*.72,y-h*.18);
  ctx.stroke();
}

function drawBackground(){
  ctx.fillStyle="#0a0f18";ctx.fillRect(0,0,W,H);
  for(let i=0;i<55;i++){
    const sx=(i*173)%W;
    const sy=((i*97+Math.floor(-cameraY*.12))%H+H)%H;
    ctx.globalAlpha=.3+(i%4)*.13;
    ctx.fillStyle="#dfe9ff";ctx.fillRect(sx,sy,2,2);
  }
  ctx.globalAlpha=1;
  const grad=ctx.createLinearGradient(0,0,0,H);
  grad.addColorStop(0,"rgba(38,58,94,.28)");
  grad.addColorStop(1,"rgba(0,0,0,0)");
  ctx.fillStyle=grad;ctx.fillRect(0,0,W,H);
}

function draw(){
  drawBackground();
  ctx.save();
  ctx.translate(0,-cameraY);

  for(const p of platforms){
    ctx.fillStyle=p.base?"#ffd54a":(p.bonus?"#58c8ff":"#e8edf4");
    ctx.fillRect(p.x,p.y,p.w,p.h);
    ctx.fillStyle="rgba(0,0,0,.22)";
    ctx.fillRect(p.x,p.y+p.h,p.w,5);
  }

  for(const h of hazards){
    ctx.fillStyle="#ff4d5a";ctx.fillRect(h.x,h.y,h.w,h.h);
    ctx.fillStyle="#7b1722";
    for(let x=h.x+6;x<h.x+h.w-2;x+=14){
      ctx.beginPath();
      ctx.moveTo(x,h.y);ctx.lineTo(x+7,h.y-10);ctx.lineTo(x+14,h.y);ctx.fill();
    }
  }

  for(const pu of powerups){
    if(!pu.active) continue;
    const yy=pu.y+Math.sin(pu.bob)*5;
    ctx.fillStyle=pu.type==="SUPER"?"#ffd54a":"#70e1ff";
    ctx.beginPath();ctx.arc(pu.x+12,yy+12,12,0,Math.PI*2);ctx.fill();
    ctx.fillStyle="#111827";
    ctx.font="bold 14px Arial";
    ctx.textAlign="center";
    ctx.fillText(pu.type==="SUPER"?"⚡":"↘",pu.x+12,yy+17);
  }

  drawGrasshopper();
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
- Siempre existe al menos una ruta físicamente alcanzable.
- Algunas plataformas se mueven horizontalmente.
- **⚡ Super salto:** aumenta temporalmente la altura del salto.
- **🔹 Mini:** te vuelve más pequeño, pero también reduce un poco el control y hace más difícil aterrizar.
- Los obstáculos rojos te empujan hacia abajo y descuentan puntos.
- Mientras más alto llegues, mayor será tu puntuación.
- Cuando caigas fuera de la pantalla, termina la partida.
""")
