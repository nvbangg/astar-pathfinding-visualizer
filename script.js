// --- Configuration Constants ---
const CELL = 25;
const COLS = 45, ROWS = 25;
const DEFAULT_START = [2, 2];
const DEFAULT_END   = [COLS - 3, ROWS - 3];
const WALL_PROB = 0.3;
const DELAY_START = 10, DELAY_PAUSE = 50, MAX_SPEED_DELAY = 101;

const COLORS = {
  empty:'#FFFFFF', wall:'#808080', start:'#00DD00', end:'#EE4400',
  open:'#98FB98', closed:'#AFEEEE', path:'#FFFF00', grid:'#E0E0E0'
};

// ! 1. SETUP & INITIALIZATION
let gridData = [];
let startNode = [...DEFAULT_START];
let endNode   = [...DEFAULT_END];
let isRunning = false, isPaused = false, isStepMode = false, hasStepEvent = false;
let isVisualized = false;
let drawMode = null, draggedType = null;
let animFrames = [], algoResult = null;
let animTimer = null;

const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');

function resizeCanvas() {
  canvas.width  = COLS * CELL;
  canvas.height = ROWS * CELL;
  ctx.imageSmoothingEnabled = false;
}

function initGrid() {
  gridData = Array.from({length: ROWS}, () => new Array(COLS).fill(0));
}

function drawGrid() {
  for (let y = 0; y < ROWS; y++) {
    for (let x = 0; x < COLS; x++) {
      drawCell(x, y);
    }
  }
}

// ! 2. USER INTERACTION
function cellColor(x, y) {
  if (x === startNode[0] && y === startNode[1]) return COLORS.start;
  if (x === endNode[0]   && y === endNode[1])   return COLORS.end;
  if (gridData[y][x]) return COLORS.wall;
  return COLORS.empty;
}

function drawCell(x, y, type) {
  const color = type ? COLORS[type] : cellColor(x, y);
  const px = x * CELL;
  const py = y * CELL;
  ctx.fillStyle = color;
  ctx.fillRect(px, py, CELL, CELL);
  ctx.strokeStyle = COLORS.grid;
  ctx.lineWidth = 1;
  ctx.strokeRect(px + 0.5, py + 0.5, CELL - 1, CELL - 1);
}

function getCellAt(e) {
  const rect = canvas.getBoundingClientRect();
  const x = (e.clientX - rect.left) * (canvas.width / rect.width);
  const y = (e.clientY - rect.top) * (canvas.height / rect.height);
  const cx = Math.floor(x / CELL);
  const cy = Math.floor(y / CELL);
  if (cx >= 0 && cx < COLS && cy >= 0 && cy < ROWS) return [cx, cy];
  return null;
}

canvas.addEventListener('mousedown', e => {
  const pos = getCellAt(e);
  if (!pos || isRunning) return;
  const [x, y] = pos;
  if (x===startNode[0] && y===startNode[1] && !isVisualized) { draggedType='start'; return; }
  if (x===endNode[0]   && y===endNode[1]   && !isVisualized) { draggedType='end';   return; }
  if (!isVisualized) {
    drawMode = gridData[y][x] ? 'erase' : 'wall';
    paintWall(pos);
  }
});

canvas.addEventListener('mousemove', e => {
  const pos = getCellAt(e);
  if (!pos || isRunning) return;
  const [x, y] = pos;
  if (draggedType) {
    const isSE = (x===startNode[0]&&y===startNode[1]) || (x===endNode[0]&&y===endNode[1]);
    if (!isSE && !gridData[y][x]) {
      if (draggedType==='start') { drawCell(...startNode,'empty'); startNode=[x,y]; drawCell(x,y,'start'); }
      else                       { drawCell(...endNode,  'empty'); endNode  =[x,y]; drawCell(x,y,'end');   }
    }
  } else if (drawMode) {
    paintWall(pos);
  }
});

canvas.addEventListener('mouseup', () => { draggedType=null; drawMode=null; });
canvas.addEventListener('mouseleave', () => { draggedType=null; drawMode=null; });

function paintWall([x,y]) {
  const isWall = drawMode==='wall';
  if (gridData[y][x] !== (isWall?1:0)) {
    gridData[y][x] = isWall ? 1 : 0;
    drawCell(x, y, isWall?'wall':'empty');
  }
}

// ! 3. MAP TOOLS & MAZE
function clearPath() {
  if (animTimer) { clearTimeout(animTimer); animTimer=null; }
  isRunning=isPaused=isVisualized=isStepMode=hasStepEvent=false;
  animFrames=[]; algoResult=null;
  setStartBtn('Start','#4CAF50');
  for (let y=0;y<ROWS;y++) for (let x=0;x<COLS;x++) {
    if (!gridData[y][x]) drawCell(x,y);
  }
  resetStats();
}

function clearWalls() {
  clearPath();
  initGrid();
  drawGrid();
}

function resetStartEnd() {
  startNode=[...DEFAULT_START]; endNode=[...DEFAULT_END];
  gridData[startNode[1]][startNode[0]]=0;
  gridData[endNode[1]][endNode[0]]=0;
  drawGrid();
}

function randomWalls() {
  clearWalls();
  for (let y=0;y<ROWS;y++) for (let x=0;x<COLS;x++)
    if (Math.random()<WALL_PROB) gridData[y][x]=1;
  resetStartEnd();
}

function randomMaze() {
  clearWalls();
  for (let y=1;y<ROWS-1;y++) for (let x=1;x<COLS-1;x++) gridData[y][x]=1;
  const stack=[...DEFAULT_START];
  gridData[DEFAULT_START[1]][DEFAULT_START[0]]=0;
  while (stack.length) {
    const [cx,cy] = stack.slice(-2);
    const neighbors=[];
    for (const [dy,dx] of [[-2,0],[2,0],[0,-2],[0,2]]) {
      const nx=cx+dx, ny=cy+dy;
      if (nx>1&&nx<COLS-2&&ny>1&&ny<ROWS-2&&gridData[ny][nx])
        neighbors.push([nx,ny,cx+Math.floor(dx/2),cy+Math.floor(dy/2)]);
    }
    if (neighbors.length) {
      const [nx,ny,mx,my]=neighbors[Math.floor(Math.random()*neighbors.length)];
      gridData[my][mx]=gridData[ny][nx]=0;
      stack.push(nx,ny);
    } else { stack.pop(); stack.pop(); }
  }
  resetStartEnd();
}

function saveMap() {
  const data = JSON.stringify({matrix:gridData, start:startNode, end:endNode});
  const a=document.createElement('a');
  a.href='data:application/json,'+encodeURIComponent(data);
  a.download='map.json'; a.click();
}

document.getElementById('file-input').addEventListener('change', e => {
  const file=e.target.files[0]; if(!file) return;
  const reader=new FileReader();
  reader.onload=ev=>{
    const data=JSON.parse(ev.target.result);
    const d=Array.isArray(data)?data[0]:data;
    clearWalls();
    const m=d.matrix||[];
    for (let y=0;y<Math.min(ROWS,m.length);y++)
      for (let x=0;x<Math.min(COLS,m[y].length);x++)
        gridData[y][x]=m[y][x];
    if(d.start) startNode=[...d.start];
    if(d.end)   endNode  =[...d.end];
    drawGrid();
  };
  reader.readAsText(file);
  e.target.value='';
});

// ! 4. A* ALGORITHM LOGIC
function heuristic(a, b, name) {
  const dx=Math.abs(a[0]-b[0]), dy=Math.abs(a[1]-b[1]);
  name = name || document.getElementById('heuristic').value;
  if (name==='Manhattan') return dx+dy;
  if (name==='Euclidean') return Math.hypot(dx,dy);
  if (name==='Octile')    return Math.max(dx,dy)+(Math.SQRT2-1)*Math.min(dx,dy);
  if (name==='Chebyshev') return Math.max(dx,dy);
  return 0;
}

function getNeighbors([x,y]) {
  const allowDiag  = document.getElementById('allow-diagonal').checked;
  const noCross    = document.getElementById('no-cross-corners').checked;
  const diagCost1  = document.getElementById('diagonal-cost-one').checked;
  const diagCost   = diagCost1 ? 1.0 : Math.SQRT2;
  const result=[];
  for (const [dx,dy] of [[-1,0],[1,0],[0,-1],[0,1]]) {
    const nx=x+dx,ny=y+dy;
    if(nx>=0&&nx<COLS&&ny>=0&&ny<ROWS&&!gridData[ny][nx])
      result.push([[nx,ny],1.0]);
  }
  if (allowDiag) {
    for (const [dx,dy] of [[-1,-1],[1,-1],[1,1],[-1,1]]) {
      const nx=x+dx,ny=y+dy;
      if(nx>=0&&nx<COLS&&ny>=0&&ny<ROWS&&!gridData[ny][nx]){
        const w1=gridData[y+dy][x], w2=gridData[y][x+dx];
        if(noCross){ if(w1||w2) continue; }
        else       { if(w1&&w2) continue; }
        result.push([[nx,ny],diagCost]);
      }
    }
  }
  return result;
}

function runAstar(hName=null) {
  const start=[...startNode], end=[...endNode];
  const key=([x,y])=>`${x},${y}`;
  const gScore={[key(start)]:0};
  const cameFrom={[key(start)]:null};
  let tieBreak=0, ops=1;
  const h0=heuristic(start,end,hName);
  const openSet=[{f:h0,h:h0,tb:tieBreak,pos:start}];
  const closedSet=new Set();
  const frames=[];
  const t0=performance.now();
  const heap = {
    data: openSet,
    push(item){ this.data.push(item); this.data.sort((a,b)=>a.f-b.f||a.h-b.h||a.tb-b.tb); },
    pop(){ return this.data.shift(); }
  };
  while (heap.data.length) {
    const {pos:current}=heap.pop();
    const ck=key(current);
    if(closedSet.has(ck)) continue;
    ops++;
    closedSet.add(ck);
    const isStartEnd=(current[0]===start[0]&&current[1]===start[1])||(current[0]===end[0]&&current[1]===end[1]);
    if(!isStartEnd) frames.push(['closed',current]);
    if(current[0]===end[0]&&current[1]===end[1]){
      const path=[];
      let cursor=[...end];
      while(cursor){ path.push(cursor); cursor=cameFrom[key(cursor)]; }
      const elapsed=performance.now()-t0;
      return [{path_cost:gScore[key(end)].toFixed(2),visited_nodes:closedSet.size,execution_time:elapsed.toFixed(2),operations_count:ops,path}, frames];
    }
    for (const [neighbor,cost] of getNeighbors(current)) {
      const nk=key(neighbor);
      if(closedSet.has(nk)) continue;
      const ng=gScore[ck]+cost;
      if(!(nk in gScore)||ng<gScore[nk]){
        if(!(nk in gScore)){
          ops++;
          const ne=(neighbor[0]===end[0]&&neighbor[1]===end[1]);
          if(!ne) frames.push(['open',neighbor]);
        }
        gScore[nk]=ng;
        cameFrom[nk]=current;
        tieBreak++;
        const h=heuristic(neighbor,end,hName);
        heap.push({f:ng+h,h,tb:tieBreak,pos:neighbor});
      }
    }
  }
  const elapsed=performance.now()-t0;
  return [{path_cost:'-',visited_nodes:closedSet.size,execution_time:elapsed.toFixed(2),operations_count:ops,path:null},frames];
}

// ! 5. EXECUTION & ANIMATION
function setStartBtn(text,bg){ const b=document.getElementById('btn-start'); b.textContent=text; b.style.background=bg; }

function toggleExecution() {
  if(isRunning){
    if(isStepMode){ isStepMode=isPaused=false; setStartBtn('Pause','#FF9800'); }
    else{ isPaused = !isPaused; setStartBtn(isPaused?'Start':'Pause', isPaused?'#4CAF50':'#FF9800'); }
  } else {
    clearPath();
    [algoResult,animFrames]=runAstar();
    refreshStats();
    isRunning=true; isPaused=isStepMode=false;
    setStartBtn('Pause','#FF9800');
    animTimer=setTimeout(()=>playback(0),DELAY_START);
  }
}

function stepExecution() {
  if(!isRunning){
    clearPath(); [algoResult,animFrames]=runAstar(); refreshStats();
    isRunning=true; isPaused=false; isStepMode=true;
    setStartBtn('Start','#4CAF50');
    animTimer=setTimeout(()=>playback(0),DELAY_START);
  } else {
    isStepMode=true; isPaused=false; hasStepEvent=true;
    setStartBtn('Start','#4CAF50');
  }
}

function playback(index) {
  if(!isRunning) return;
  if(isPaused&&!isStepMode){ animTimer=setTimeout(()=>playback(index),DELAY_PAUSE); return; }
  if(isStepMode&&!hasStepEvent&&index>0){ animTimer=setTimeout(()=>playback(index),DELAY_PAUSE); return; }
  hasStepEvent=false;
  if(index<animFrames.length){
    const [type,pos]=animFrames[index];
    drawCell(pos[0],pos[1],type);
    const speed=parseInt(document.getElementById('speed').value);
    const delay=Math.max(1,MAX_SPEED_DELAY-speed);
    animTimer=setTimeout(()=>playback(index+1),delay);
  } else {
    if(algoResult&&algoResult.path){
      for(const p of algoResult.path){
        const isSE=(p[0]===startNode[0]&&p[1]===startNode[1])||(p[0]===endNode[0]&&p[1]===endNode[1]);
        if(!isSE) drawCell(p[0],p[1],'path');
      }
    }
    isRunning=false; isVisualized=true;
    setStartBtn('Start','#4CAF50');
  }
}

// ! 6. STATS & COMPARISON
function resetStats(){ ['st-cost','st-visited','st-time','st-ops'].forEach(id=>document.getElementById(id).textContent='-'); }
function refreshStats(){
  if(!algoResult) return;
  document.getElementById('st-cost').textContent    = algoResult.path_cost;
  document.getElementById('st-visited').textContent = algoResult.visited_nodes;
  document.getElementById('st-time').textContent    = algoResult.execution_time+' ms';
  document.getElementById('st-ops').textContent     = algoResult.operations_count;
}

function compareAll() {
  const names=['Euclidean','Manhattan','Octile','Chebyshev','Dijkstra (h=0)'];
  const headers=['Heuristic','Path Cost','Visited Nodes','Execution Time (ms)','Operations'];
  const keys=['heuristic','path_cost','visited_nodes','execution_time','operations_count'];
  const results=names.map(h=>{ const [r]=runAstar(h); r.heuristic=h; return r; });
  const table=document.getElementById('compare-table');
  table.innerHTML='<tr>'+headers.map(h=>`<th>${h}</th>`).join('')+'</tr>'
    +results.map(r=>`<tr class="${r.path_cost!=='-'?'ok':'err'}">`+keys.map(k=>`<td>${r[k]}</td>`).join('')+'</tr>').join('');
  document.getElementById('compare-modal').classList.add('show');
}

// ! 7. HELPER METHODS & LISTENERS
document.getElementById('allow-diagonal').addEventListener('change',e=>{
  const dis=!e.target.checked;
  document.getElementById('no-cross-corners').disabled=dis;
  document.getElementById('diagonal-cost-one').disabled=dis;
});

document.getElementById('btn-start').addEventListener('click',toggleExecution);
document.getElementById('btn-step').addEventListener('click',stepExecution);
document.getElementById('btn-clear-path').addEventListener('click',clearPath);
document.getElementById('btn-clear-walls').addEventListener('click',clearWalls);
document.getElementById('btn-rand-walls').addEventListener('click',randomWalls);
document.getElementById('btn-rand-maze').addEventListener('click',randomMaze);
document.getElementById('btn-save').addEventListener('click',saveMap);
document.getElementById('btn-load').addEventListener('click',()=>document.getElementById('file-input').click());
document.getElementById('btn-compare').addEventListener('click',compareAll);
document.getElementById('close-modal').addEventListener('click',()=>document.getElementById('compare-modal').classList.remove('show'));

resizeCanvas();
initGrid();
drawGrid();
