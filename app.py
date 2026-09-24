
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from datetime import datetime
import json

st.set_page_config(
    page_title="Bomb Arena: Revenge",
    page_icon="💣",
    layout="wide",
    initial_sidebar_state="collapsed"
)

SCORES_FILE = Path("bomb_scores.json")

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
        "nombre": (name.strip() or "Anónimo")[:30],
        "puntaje": int(score),
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    scores.sort(key=lambda x: x["puntaje"], reverse=True)
    SCORES_FILE.write_text(
        json.dumps(scores[:50], ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

st.markdown("""
<style>
.stApp{
    background:radial-gradient(circle at top,#261f45 0%,#10131c 58%,#080a0f 100%);
    color:#f8f8f8;
}
[data-testid="stHeader"]{background:transparent}
.block-container{max-width:1180px;padding-top:1.2rem}
.title{
    font-weight:950;
    font-size:clamp(2.3rem,5vw,4.4rem);
    line-height:.98;
    letter-spacing:-.055em;
}
.accent{color:#ffcf3f}
.sub{color:#adb5c5;margin:.7rem 0 1.2rem;font-size:1.02rem}
.card{
    background:rgba(255,255,255,.045);
    border:1px solid rgba(255,255,255,.1);
    border-radius:16px;
    padding:13px 15px;
    min-height:82px;
}
.card b{color:#ffcf3f}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">BOMB ARENA <span class="accent">REVENGE</span></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub">Destruye bloques, elimina a los NPC y, si mueres, sigue peleando desde el perímetro para poder revivir.</div>',
    unsafe_allow_html=True
)

a,b,c = st.columns(3)
with a:
    st.markdown('<div class="card"><b>WASD / Flechas</b><br>Muévete por la arena.</div>', unsafe_allow_html=True)
with b:
    st.markdown('<div class="card"><b>Espacio</b><br>Coloca una bomba o lánzala desde el perímetro.</div>', unsafe_allow_html=True)
with c:
    st.markdown('<div class="card"><b>Modo Revenge</b><br>Mata un NPC desde afuera y revives.</div>', unsafe_allow_html=True)

game_html = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
html,body{margin:0;background:transparent;font-family:Inter,system-ui,Arial,sans-serif;overflow:hidden}
.outer{display:flex;justify-content:center;padding:14px 0 6px}
.shell{
  width:min(900px,97vw);
  border-radius:22px;
  overflow:hidden;
  border:1px solid rgba(255,255,255,.12);
  background:#0d1118;
  box-shadow:0 30px 90px rgba(0,0,0,.44);
}
.hud{
  display:flex;gap:8px;justify-content:space-between;flex-wrap:wrap;
  padding:10px 12px;background:#151b27;color:white;font-weight:850
}
.pill{
  background:#202838;border:1px solid rgba(255,255,255,.08);
  border-radius:999px;padding:7px 11px;font-size:13px
}
.stage{position:relative;background:#090d13}
canvas{display:block;width:100%;height:auto;image-rendering:pixelated}
.overlay{
  position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
  pointer-events:none;background:rgba(5,7,11,.16)
}
.panel{
  pointer-events:auto;width:min(440px,80%);padding:24px;border-radius:20px;text-align:center;
  color:#fff;background:rgba(9,12,18,.94);border:1px solid rgba(255,255,255,.15);
  box-shadow:0 25px 80px rgba(0,0,0,.55)
}
.panel h2{font-size:31px;margin:0 0 8px}
.panel p{color:#b8c1d0;line-height:1.45}
button{
  border:0;border-radius:11px;background:#ffcf3f;color:#151515;
  padding:12px 18px;font-weight:900;font-size:15px;cursor:pointer
}
.note{font-size:12px;color:#8e98aa;margin-top:11px}
</style>
</head>
<body>
<div class="outer">
<div class="shell">
  <div class="hud">
    <div class="pill">💣 BOMBAS: <span id="bombs">1</span></div>
    <div class="pill">🔥 ALCANCE: <span id="range">2</span></div>
    <div class="pill">🤖 NPC: <span id="enemies">4</span></div>
    <div class="pill">⭐ PUNTOS: <span id="score">0</span></div>
    <div class="pill">ESTADO: <span id="status">VIVO</span></div>
  </div>
  <div class="stage">
    <canvas id="game" width="780" height="660"></canvas>
    <div class="overlay" id="overlay">
      <div class="panel">
        <h2>💣 Bomb Arena</h2>
        <p>
        Rompe cajas y derrota a todos los NPC. Si una explosión te elimina,
        pasarás al borde exterior de la arena. Desde allí podrás lanzar bombas:
        si una de ellas elimina a un NPC, <b>revives</b>.
        </p>
        <button onclick="startGame()">INICIAR PARTIDA</button>
        <div class="note">WASD/Flechas para moverte · Espacio para bomba</div>
      </div>
    </div>
  </div>
</div>
</div>

<script>
const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");

const COLS=13, ROWS=11, T=48;
const OX=78, OY=66;
const W=canvas.width, H=canvas.height;

const hudBombs=document.getElementById("bombs");
const hudRange=document.getElementById("range");
const hudEnemies=document.getElementById("enemies");
const hudScore=document.getElementById("score");
const hudStatus=document.getElementById("status");
const overlay=document.getElementById("overlay");

let grid=[];
let bombs=[];
let flames=[];
let items=[];
let enemies=[];
let player;
let keys={};
let running=false;
let lastTime=0;
let score=0;
let revengeCooldown=0;
let npcIdCounter=1;

const dirs=[
  {x:1,y:0},{x:-1,y:0},{x:0,y:1},{x:0,y:-1}
];

addEventListener("keydown",e=>{
  const k=e.key.toLowerCase();
  keys[k]=true;
  if(["arrowup","arrowdown","arrowleft","arrowright"," "].includes(k)) e.preventDefault();
  if(k===" " && !e.repeat){
    if(running){
      if(player.mode==="arena") placeBomb(player);
      else throwRevengeBomb();
    }
  }
});
addEventListener("keyup",e=>keys[e.key.toLowerCase()]=false);

function rnd(a,b){return a+Math.random()*(b-a)}
function pick(a){return a[Math.floor(Math.random()*a.length)]}
function inGrid(c,r){return c>=0&&c<COLS&&r>=0&&r<ROWS}
function tileKey(c,r){return c+","+r}
function px(c){return OX+c*T+T/2}
function py(r){return OY+r*T+T/2}

function isSolid(c,r){
  if(!inGrid(c,r)) return true;
  return grid[r][c]===1 || grid[r][c]===2;
}
function isBombAt(c,r){
  return bombs.some(b=>b.c===c&&b.r===r&&!b.exploded);
}
function walkable(c,r){
  return inGrid(c,r) && !isSolid(c,r) && !isBombAt(c,r);
}

function createGrid(){
  grid=Array.from({length:ROWS},()=>Array(COLS).fill(0));

  for(let r=0;r<ROWS;r++){
    for(let c=0;c<COLS;c++){
      if(c%2===1 && r%2===1) grid[r][c]=1; // indestructible pillar
    }
  }

  const safe=new Set([
    "0,0","1,0","0,1",
    `${COLS-1},${ROWS-1}`,`${COLS-2},${ROWS-1}`,`${COLS-1},${ROWS-2}`,
    `${COLS-1},0`,`${COLS-2},0`,`${COLS-1},1`,
    `0,${ROWS-1}`,`1,${ROWS-1}`,`0,${ROWS-2}`
  ]);

  for(let r=0;r<ROWS;r++){
    for(let c=0;c<COLS;c++){
      if(grid[r][c]===0 && !safe.has(tileKey(c,r)) && Math.random()<.47){
        grid[r][c]=2; // breakable crate
      }
    }
  }
}

function makePlayer(){
  return{
    c:0,r:0,x:px(0),y:py(0),
    tx:px(0),ty:py(0),
    moving:false,
    dir:{x:0,y:1},
    speed:185,
    bombsMax:1,
    bombsActive:0,
    fire:2,
    alive:true,
    mode:"arena",
    invuln:1.3,
    borderIndex:0,
    borderSide:0
  }
}

function spawnEnemies(){
  const spawn=[
    {c:COLS-1,r:ROWS-1},
    {c:COLS-1,r:0},
    {c:0,r:ROWS-1},
    {c:COLS-3,r:ROWS-3}
  ];
  enemies=spawn.map((s,i)=>({
    id:npcIdCounter++,
    c:s.c,r:s.r,x:px(s.c),y:py(s.r),tx:px(s.c),ty:py(s.r),
    moving:false,dir:pick(dirs),speed:105+rnd(0,30),
    alive:true,think:rnd(.15,.7),bombTimer:rnd(1.7,3.4),
    bombsMax:1,bombsActive:0,fire:2
  }));
}

function startGame(){
  createGrid();
  bombs=[];flames=[];items=[];score=0;
  player=makePlayer();
  spawnEnemies();
  running=true;
  revengeCooldown=0;
  overlay.style.display="none";
  lastTime=performance.now();
  updateHud();
  requestAnimationFrame(loop);
}

function updateHud(){
  hudBombs.textContent=player?player.bombsMax:"1";
  hudRange.textContent=player?player.fire:"2";
  hudEnemies.textContent=enemies.filter(e=>e.alive).length;
  hudScore.textContent=Math.floor(score);
  if(!player) hudStatus.textContent="VIVO";
  else if(player.mode==="revenge") hudStatus.textContent="🚀 REVENGE";
  else if(player.invuln>0) hudStatus.textContent="✨ REVIVIENDO";
  else hudStatus.textContent="VIVO";
}

function entityTile(e){
  return{c:Math.round((e.x-OX-T/2)/T),r:Math.round((e.y-OY-T/2)/T)}
}

function tryMoveEntity(e,dx,dy){
  if(e.moving) return;
  const nc=e.c+dx,nr=e.r+dy;
  if(walkable(nc,nr)){
    e.c=nc;e.r=nr;e.tx=px(nc);e.ty=py(nr);e.moving=true;e.dir={x:dx,y:dy};
  }
}

function moveToward(e,dt){
  if(!e.moving) return;
  const dx=e.tx-e.x,dy=e.ty-e.y;
  const dist=Math.hypot(dx,dy);
  if(dist<2){
    e.x=e.tx;e.y=e.ty;e.moving=false;
    return;
  }
  const step=e.speed*dt;
  e.x += dx/dist*Math.min(step,dist);
  e.y += dy/dist*Math.min(step,dist);
}

function placeBomb(owner){
  if(owner.bombsActive>=owner.bombsMax) return;
  if(isBombAt(owner.c,owner.r)) return;
  bombs.push({
    c:owner.c,r:owner.r,
    timer:2.15,
    range:owner.fire||2,
    owner,
    exploded:false,
    revenge:false
  });
  owner.bombsActive++;
}

function explodeBomb(b){
  if(b.exploded) return;
  b.exploded=true;
  if(b.owner && b.owner.bombsActive>0) b.owner.bombsActive--;

  const cells=[{c:b.c,r:b.r}];

  for(const d of dirs){
    for(let i=1;i<=b.range;i++){
      const c=b.c+d.x*i,r=b.r+d.y*i;
      if(!inGrid(c,r)) break;
      if(grid[r][c]===1) break;

      cells.push({c,r});

      if(grid[r][c]===2){
        grid[r][c]=0;
        score+=8;
        if(Math.random()<.20){
          items.push({
            c,r,
            type:Math.random()<.54?"fire":"bomb",
            active:true
          });
        }
        break;
      }
    }
  }

  for(const cell of cells){
    flames.push({c:cell.c,r:cell.r,time:.48,source:b});
    for(const other of bombs){
      if(!other.exploded && other.c===cell.c && other.r===cell.r){
        other.timer=Math.min(other.timer,.04);
      }
    }
  }
}

function flameHits(c,r){
  return flames.find(f=>f.c===c&&f.r===r&&f.time>0);
}

function killPlayer(){
  if(player.mode!=="arena" || player.invuln>0) return;
  player.alive=false;
  player.mode="revenge";
  player.moving=false;
  player.borderSide=0;
  player.borderIndex=Math.floor(COLS/2);
  player.x=OX+player.borderIndex*T+T/2;
  player.y=OY-T*.7;
  score=Math.max(0,score-120);
  revengeCooldown=.5;
  updateHud();
}

function safeRespawn(){
  const candidates=[
    {c:0,r:0},{c:COLS-1,r:ROWS-1},{c:COLS-1,r:0},{c:0,r:ROWS-1},
    {c:2,r:0},{c:0,r:2},{c:COLS-3,r:ROWS-1},{c:COLS-1,r:ROWS-3}
  ].filter(p=>walkable(p.c,p.r) && !flameHits(p.c,p.r));

  const p=candidates.length?pick(candidates):{c:0,r:0};
  player.c=p.c;player.r=p.r;player.x=px(p.c);player.y=py(p.r);
  player.tx=player.x;player.ty=player.y;
  player.mode="arena";player.alive=true;player.invuln=2.0;
  player.moving=false;
  score+=250;
  updateHud();
}

function killEnemy(e,source){
  if(!e.alive) return;
  e.alive=false;
  score+=150;
  if(source && source.revenge){
    safeRespawn();
    score+=200;
  }
  updateHud();
}

function updateArenaPlayer(dt){
  if(player.invuln>0) player.invuln-=dt;
  if(!player.moving){
    let dx=0,dy=0;
    if(keys["arrowleft"]||keys["a"]) dx=-1;
    else if(keys["arrowright"]||keys["d"]) dx=1;
    else if(keys["arrowup"]||keys["w"]) dy=-1;
    else if(keys["arrowdown"]||keys["s"]) dy=1;
    if(dx||dy) tryMoveEntity(player,dx,dy);
  }
  moveToward(player,dt);

  const f=flameHits(player.c,player.r);
  if(f) killPlayer();

  for(const it of items){
    if(it.active && it.c===player.c && it.r===player.r){
      it.active=false;
      if(it.type==="fire") player.fire=Math.min(6,player.fire+1);
      else player.bombsMax=Math.min(5,player.bombsMax+1);
      score+=35;
      updateHud();
    }
  }
}

function borderPosition(){
  // Four discrete sides around arena; player moves clockwise/counterclockwise.
  const topCount=COLS;
  const rightCount=ROWS-2;
  const bottomCount=COLS;
  const leftCount=ROWS-2;
  const total=topCount+rightCount+bottomCount+leftCount;
  player.borderIndex=(player.borderIndex%total+total)%total;
  let i=player.borderIndex;

  if(i<topCount){
    return{x:px(i),y:OY-T*.72, side:"top", c:i, r:0, inward:{x:0,y:1}};
  }
  i-=topCount;
  if(i<rightCount){
    return{x:OX+COLS*T+T*.72,y:py(i+1), side:"right", c:COLS-1, r:i+1, inward:{x:-1,y:0}};
  }
  i-=rightCount;
  if(i<bottomCount){
    const c=COLS-1-i;
    return{x:px(c),y:OY+ROWS*T+T*.72, side:"bottom", c, r:ROWS-1, inward:{x:0,y:-1}};
  }
  i-=bottomCount;
  const r=ROWS-2-i;
  return{x:OX-T*.72,y:py(r), side:"left", c:0, r, inward:{x:1,y:0}};
}

let borderMoveLatch=false;

function updateRevenge(dt){
  revengeCooldown=Math.max(0,revengeCooldown-dt);
  const moveLeft=keys["arrowleft"]||keys["a"]||keys["arrowup"]||keys["w"];
  const moveRight=keys["arrowright"]||keys["d"]||keys["arrowdown"]||keys["s"];

  if((moveLeft||moveRight) && !borderMoveLatch){
    player.borderIndex += moveRight ? 1 : -1;
    borderMoveLatch=true;
  }
  if(!moveLeft&&!moveRight) borderMoveLatch=false;

  const p=borderPosition();
  player.x=p.x;player.y=p.y;
}

function throwRevengeBomb(){
  if(player.mode!=="revenge" || revengeCooldown>0) return;
  if(bombs.some(b=>b.revenge&&!b.exploded)) return;

  const p=borderPosition();
  const depth=3 + Math.floor(Math.random()*3);
  let c=p.c+p.inward.x*depth;
  let r=p.r+p.inward.y*depth;

  // Walk backwards toward edge if landing tile is solid.
  while((!inGrid(c,r) || grid[r][c]===1) && depth>1){
    c-=p.inward.x;
    r-=p.inward.y;
  }
  if(!inGrid(c,r)) return;

  // Revenge bombs can land on crates and destroy them.
  bombs.push({
    c,r,timer:1.35,range:2,owner:null,exploded:false,revenge:true
  });
  revengeCooldown=.7;
}

function enemyDanger(c,r){
  return bombs.some(b=>{
    if(b.exploded) return false;
    if(b.c===c && Math.abs(b.r-r)<=b.range) return true;
    if(b.r===r && Math.abs(b.c-c)<=b.range) return true;
    return false;
  });
}

function updateEnemy(e,dt){
  if(!e.alive) return;
  moveToward(e,dt);
  e.think-=dt;
  e.bombTimer-=dt;

  const f=flameHits(e.c,e.r);
  if(f){
    killEnemy(e,f.source);
    return;
  }

  if(!e.moving && e.think<=0){
    e.think=rnd(.16,.42);
    let options=dirs.filter(d=>walkable(e.c+d.x,e.r+d.y));

    // Prefer tiles that are not aligned with a bomb.
    const safe=options.filter(d=>!enemyDanger(e.c+d.x,e.r+d.y));
    if(safe.length) options=safe;

    if(options.length){
      // sometimes move roughly toward player if player is in arena
      if(player.mode==="arena" && Math.random()<.42){
        options.sort((a,b)=>{
          const da=Math.abs((e.c+a.x)-player.c)+Math.abs((e.r+a.y)-player.r);
          const db=Math.abs((e.c+b.x)-player.c)+Math.abs((e.r+b.y)-player.r);
          return da-db;
        });
        tryMoveEntity(e,options[0].x,options[0].y);
      }else{
        const d=pick(options);
        tryMoveEntity(e,d.x,d.y);
      }
    }
  }

  if(e.bombTimer<=0 && !e.moving){
    e.bombTimer=rnd(2.1,4.2);
    const nearCrate=dirs.some(d=>{
      const c=e.c+d.x,r=e.r+d.y;
      return inGrid(c,r)&&grid[r][c]===2;
    });
    const nearPlayer=player.mode==="arena" &&
      Math.abs(e.c-player.c)+Math.abs(e.r-player.r)<=3;

    if((nearCrate||nearPlayer||Math.random()<.22) && e.bombsActive<e.bombsMax){
      placeBomb(e);
    }
  }
}

function updateBombs(dt){
  for(const b of bombs){
    if(b.exploded) continue;
    b.timer-=dt;
    if(b.timer<=0) explodeBomb(b);
  }
  bombs=bombs.filter(b=>!b.exploded || Math.random()<1); // keep objects; harmless
}

function updateFlames(dt){
  for(const f of flames) f.time-=dt;
  flames=flames.filter(f=>f.time>0);
}

function checkWin(){
  if(enemies.every(e=>!e.alive)){
    running=false;
    const final=Math.floor(score+500);
    score=final;
    updateHud();
    overlay.style.display="flex";
    overlay.innerHTML=`
      <div class="panel">
        <h2>🏆 Arena despejada</h2>
        <p>Eliminaste a todos los NPC.<br><b>${final} puntos</b></p>
        <button onclick="startGame()">JUGAR DE NUEVO</button>
        <div class="note">Puedes registrar tu puntuación debajo del juego.</div>
      </div>`;
  }
}

function update(dt){
  if(player.mode==="arena") updateArenaPlayer(dt);
  else updateRevenge(dt);

  for(const e of enemies) updateEnemy(e,dt);
  updateBombs(dt);
  updateFlames(dt);

  score+=dt*2;
  updateHud();
  checkWin();
}

function drawTile(c,r){
  const x=OX+c*T,y=OY+r*T;
  ctx.fillStyle=(c+r)%2===0?"#26344b":"#223047";
  ctx.fillRect(x,y,T,T);
  ctx.strokeStyle="rgba(255,255,255,.025)";
  ctx.strokeRect(x,y,T,T);

  if(grid[r][c]===1){
    ctx.fillStyle="#697589";
    ctx.fillRect(x+4,y+4,T-8,T-8);
    ctx.fillStyle="#8994a6";
    ctx.fillRect(x+7,y+7,T-14,7);
    ctx.fillStyle="#414b5c";
    ctx.fillRect(x+7,y+T-13,T-14,7);
  }else if(grid[r][c]===2){
    ctx.fillStyle="#ad7339";
    ctx.fillRect(x+5,y+5,T-10,T-10);
    ctx.strokeStyle="#e0a45f";
    ctx.lineWidth=3;
    ctx.strokeRect(x+7,y+7,T-14,T-14);
    ctx.beginPath();
    ctx.moveTo(x+9,y+9);ctx.lineTo(x+T-9,y+T-9);
    ctx.moveTo(x+T-9,y+9);ctx.lineTo(x+9,y+T-9);
    ctx.stroke();
  }
}

function drawArena(){
  ctx.fillStyle="#090d13";
  ctx.fillRect(0,0,W,H);

  // outer revenge rail
  ctx.strokeStyle="#ffcf3f";
  ctx.lineWidth=5;
  ctx.strokeRect(OX-T*.48,OY-T*.48,COLS*T+T*.96,ROWS*T+T*.96);

  for(let r=0;r<ROWS;r++)
    for(let c=0;c<COLS;c++) drawTile(c,r);
}

function drawItems(){
  for(const it of items){
    if(!it.active) continue;
    const x=px(it.c),y=py(it.r);
    ctx.beginPath();
    ctx.fillStyle=it.type==="fire"?"#ff7043":"#ffe15a";
    ctx.arc(x,y,12,0,Math.PI*2);
    ctx.fill();
    ctx.fillStyle="#141821";
    ctx.font="bold 16px Arial";
    ctx.textAlign="center";
    ctx.textBaseline="middle";
    ctx.fillText(it.type==="fire"?"🔥":"+",x,y+1);
  }
}

function drawBomb(b){
  if(b.exploded) return;
  const x=px(b.c),y=py(b.r);
  ctx.fillStyle=b.revenge?"#ffcf3f":"#161922";
  ctx.beginPath();ctx.arc(x,y,15,0,Math.PI*2);ctx.fill();

  ctx.strokeStyle=b.revenge?"#fff3b1":"#e4e7ed";
  ctx.lineWidth=3;
  ctx.beginPath();ctx.moveTo(x+8,y-11);ctx.quadraticCurveTo(x+16,y-24,x+20,y-15);ctx.stroke();

  ctx.fillStyle=(Math.floor(b.timer*8)%2===0)?"#ff4d4d":"#ff9d3f";
  ctx.beginPath();ctx.arc(x+20,y-15,4,0,Math.PI*2);ctx.fill();
}

function drawFlames(){
  for(const f of flames){
    const x=OX+f.c*T,y=OY+f.r*T;
    ctx.fillStyle="rgba(255,91,42,.86)";
    ctx.fillRect(x+5,y+5,T-10,T-10);
    ctx.fillStyle="rgba(255,222,84,.9)";
    ctx.fillRect(x+13,y+13,T-26,T-26);
  }
}

function drawBomber(x,y,color,ghost=false){
  ctx.save();
  ctx.translate(x,y);
  if(ghost) ctx.globalAlpha=.75;

  ctx.fillStyle=color;
  ctx.beginPath();
  ctx.arc(0,-4,15,0,Math.PI*2);
  ctx.fill();

  ctx.fillStyle="#f1f3f7";
  ctx.fillRect(-10,-11,20,10);
  ctx.fillStyle="#111";
  ctx.fillRect(-6,-8,4,4);
  ctx.fillRect(3,-8,4,4);

  ctx.fillStyle=color;
  ctx.fillRect(-12,9,9,9);
  ctx.fillRect(3,9,9,9);
  ctx.restore();
}

function drawPlayer(){
  if(player.mode==="arena"){
    if(player.invuln>0 && Math.floor(player.invuln*10)%2===0) return;
    drawBomber(player.x,player.y,"#ffcf3f");
  }else{
    // Revenge cart
    ctx.fillStyle="#ffcf3f";
    ctx.beginPath();
    ctx.roundRect(player.x-20,player.y-14,40,28,8);
    ctx.fill();
    ctx.fillStyle="#262b35";
    ctx.beginPath();ctx.arc(player.x-13,player.y+15,6,0,Math.PI*2);ctx.fill();
    ctx.beginPath();ctx.arc(player.x+13,player.y+15,6,0,Math.PI*2);ctx.fill();
    drawBomber(player.x,player.y-7,"#e9edf4",true);
  }
}

function drawEnemies(){
  const colors=["#ff5a65","#6d8cff","#55d7a4","#c777ff","#ff9d3f"];
  enemies.filter(e=>e.alive).forEach((e,i)=>drawBomber(e.x,e.y,colors[i%colors.length]));
}

function draw(){
  drawArena();
  drawItems();
  bombs.forEach(drawBomb);
  drawFlames();
  drawEnemies();
  drawPlayer();

  if(player.mode==="revenge"){
    ctx.fillStyle="rgba(255,207,63,.92)";
    ctx.font="bold 14px Arial";
    ctx.textAlign="center";
    ctx.fillText("REVENGE: MUÉVETE POR EL BORDE Y LANZA UNA BOMBA",W/2,28);
  }
}

function loop(ts){
  if(!running) return;
  const dt=Math.min(.035,(ts-lastTime)/1000||.016);
  lastTime=ts;
  update(dt);
  draw();
  if(running) requestAnimationFrame(loop);
}

createGrid();
player=makePlayer();
spawnEnemies();
draw();
updateHud();
</script>
</body>
</html>
"""

components.html(game_html, height=790, scrolling=False)

st.markdown("### Registrar puntuación")
st.caption("Al terminar la partida, copia aquí el puntaje mostrado en el HUD.")

with st.form("score_form", clear_on_submit=True):
    c1,c2=st.columns([2,1])
    with c1:
        name=st.text_input("Nombre", placeholder="Ej. Jorge")
    with c2:
        score_input=st.number_input("Puntaje", min_value=0, step=1)
    submitted=st.form_submit_button("Guardar puntuación", use_container_width=True)
    if submitted:
        save_score(name,score_input)
        st.success("Puntuación guardada.")

scores=load_scores()
st.markdown("### 🏆 Ranking")
if scores:
    st.dataframe(
        scores[:10],
        column_order=("nombre","puntaje","fecha"),
        hide_index=True,
        use_container_width=True
    )
else:
    st.info("Todavía no hay puntuaciones registradas.")

with st.expander("Reglas del juego"):
    st.markdown("""
- **WASD o flechas:** movimiento.
- **Espacio:** colocar bomba.
- Las explosiones destruyen cajas y pueden activar explosiones en cadena.
- Algunas cajas dejan mejoras de **alcance** o **cantidad de bombas**.
- Una explosión elimina al jugador o a un NPC de un solo golpe.
- Si mueres, pasas al **perímetro exterior** en modo *Revenge*.
- En el perímetro, muévete con WASD/flechas y pulsa **Espacio** para lanzar una bomba hacia el interior.
- Si una bomba lanzada desde el perímetro elimina a un NPC, **revives dentro de la arena**.
- Ganas cuando eliminas a todos los NPC.
""")
