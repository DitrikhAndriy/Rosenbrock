const form=document.querySelector('#parameters'), canvas=document.querySelector('#plot');
const colors={standard:'#416c88',modified:'#d18b55'};
let results=[],config=null,busy=false;
const names={standard:'Standard',modified:'Modified'};
function settings(){
  const data={};
  for(const [key,value] of new FormData(form)) if(value!=='') data[key]=value;
  return data;
}
function updateFields(){
  const method=form.elements.method.value, constraint=form.elements.constraint.value;
  function toggle(el,visible){
    el.hidden=!visible;
    el.querySelectorAll('input,select').forEach(input=>input.disabled=!visible);
  }
  toggle(document.querySelector('#line-settings'),method!=='standard');
  document.querySelectorAll('.standard-options').forEach(el=>toggle(el,method!=='modified'));
  document.querySelectorAll('.modified-options').forEach(el=>toggle(el,method!=='standard'));
  document.querySelectorAll('[data-constraint]').forEach(el=>{
    toggle(el,el.dataset.constraint===constraint);
  });
  document.querySelector('#run').textContent=method==='compare'?'Run comparison':'Run optimization';
  updateAccuracyHelp();
}
function updateAccuracyHelp(){
  document.querySelector('#accuracy-help').textContent=form.elements.termination.value==='step'
    ? 'ε sets how small steps must be before stopping.'
    : 'ε sets the allowed relative change in the point and function value. Standard also requires small steps.';
}
form.elements.method.addEventListener('change',updateFields);
form.elements.constraint.addEventListener('change',updateFields);
form.elements.termination.addEventListener('change',updateAccuracyHelp);
document.querySelector('#show-plot').addEventListener('change',draw);
const fmt=(n,digits=6)=>Number(Number(n).toPrecision(digits)).toString();
function showResults(){
  const area=document.querySelector('#results');area.replaceChildren();
  for(const r of results){
    const card=document.createElement('div');card.className='result';
    card.innerHTML=`<div class="result-heading"><div><i class="dot" style="background:${colors[r.method]}"></i>${names[r.method]}</div><span class="badge ${r.converged?'':'partial'}">${r.converged?'Converged':'Stopped'}</span></div><div class="point">(${fmt(r.x[0])}, ${fmt(r.x[1])})</div><div class="statistics"><div><span title="Function value">f(x, y)</span><strong>${Number(r.fun).toExponential(3)}</strong></div><div><span>Evaluations</span><strong>${r.nfev.toLocaleString()}</strong></div><div><span>Iterations</span><strong>${r.iterations.toLocaleString()}</strong></div></div>`;
    if(!r.converged){const message=document.createElement('p');message.className='result-message';message.textContent=r.message;card.append(message);}
    area.append(card);
  }
  document.querySelector('#legend').innerHTML=results.map(r=>`<span><i class="dot" style="background:${colors[r.method]}"></i>${names[r.method]}</span>`).join('');
}
async function run(event){
  if(event)event.preventDefault();if(busy)return;
  busy=true;const button=document.querySelector('#run'),status=document.querySelector('#status');
  button.disabled=true;status.className='';status.textContent='Computing…';
  const snapshot=settings(), started=performance.now();
  try{
    const response=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(snapshot)});
    const body=await response.json();if(!response.ok)throw new Error(body.error||'Calculation failed.');
    results=body.results;config=snapshot;showResults();draw();
    status.textContent=JSON.stringify(settings())===JSON.stringify(snapshot)?'':'Parameters changed · run to update.';
    document.querySelector('#run-note').textContent=`Last run · ${Math.round(performance.now()-started)} ms`;
  }catch(error){status.className='error';status.textContent=error.message;}
  finally{busy=false;button.disabled=false;}
}
form.addEventListener('submit',run);
form.addEventListener('input',event=>{
  if(event.target.id==='show-plot'||busy)return;
  const status=document.querySelector('#status');status.className='';
  status.textContent=results.length?'Parameters changed · run to update.':'';
});
function draw(){
  const visible=document.querySelector('#show-plot').checked;
  canvas.hidden=!visible;document.querySelector('#placeholder').hidden=visible;
  if(!visible||!config)return;
  const rect=canvas.getBoundingClientRect(),ratio=window.devicePixelRatio||1;
  if(rect.width<1||rect.height<1)return;
  canvas.width=Math.round(rect.width*ratio);canvas.height=Math.round(rect.height*ratio);
  const ctx=canvas.getContext('2d');ctx.scale(ratio,ratio);
  const W=rect.width,H=rect.height, pad={l:43,r:18,t:14,b:38};
  let minX=0,maxX=1,minY=0,maxY=1;
  for(const result of results)for(const [x,y] of result.path){
    minX=Math.min(minX,x);maxX=Math.max(maxX,x);
    minY=Math.min(minY,y);maxY=Math.max(maxY,y);
  }
  if(config.constraint==='disk'){
    const radius=Number(config.radius),cx=Number(config.center_x),cy=Number(config.center_y);
    minX=Math.min(minX,cx-radius);maxX=Math.max(maxX,cx+radius);
    minY=Math.min(minY,cy-radius);maxY=Math.max(maxY,cy+radius);
  }
  const xmid=(minX+maxX)/2,ymid=(minY+maxY)/2;
  const span=Math.max(2.6,maxX-minX,maxY-minY)*1.25;
  const scale=Math.min((W-pad.l-pad.r)/span,(H-pad.t-pad.b)/span);
  const pw=span*scale,ph=pw,L=pad.l+(W-pad.l-pad.r-pw)/2,T=pad.t+(H-pad.t-pad.b-ph)/2;
  const xmin=xmid-span/2,ymin=ymid-span/2,xmax=xmin+span,ymax=ymin+span;
  const px=x=>L+(x-xmin)*scale,py=y=>T+(ymax-y)*scale;
  const f=(x,y)=>config.function==='sphere'?x*x+y*y:(1-x)**2+100*(y-x*x)**2;
  const allowed=(x,y)=>{
    if(config.constraint==='disk')return Math.hypot(x-Number(config.center_x),y-Number(config.center_y))<=Number(config.radius);
    if(config.constraint==='halfplane'){
      const boundary=Number(config.slope)*x+Number(config.intercept);
      return config.side==='above'?y>=boundary:y<=boundary;
    }
    if(config.constraint==='box')return x>=Number(config.xmin)&&x<=Number(config.xmax)&&y>=Number(config.ymin)&&y<=Number(config.ymax);
    return true;
  };
  ctx.clearRect(0,0,W,H);ctx.fillStyle='#fff';ctx.fillRect(L,T,pw,ph);
  ctx.save();ctx.beginPath();ctx.rect(L,T,pw,ph);ctx.clip();
  if(config.constraint!=='none'){
    ctx.fillStyle='#eef0f2';const tile=5;
    for(let sx=L;sx<L+pw;sx+=tile)for(let sy=T;sy<T+ph;sy+=tile){
      if(!allowed(xmin+(sx-L+tile/2)/scale,ymax-(sy-T+tile/2)/scale))ctx.fillRect(sx,sy,tile+.5,tile+.5);
    }
  }
  const grid=75,dx=span/grid,values=[];
  for(let j=0;j<=grid;j++){values[j]=[];for(let i=0;i<=grid;i++)values[j][i]=f(xmin+i*dx,ymin+j*dx);}
  const levels=config.function==='sphere'?[.1,.25,.5,1,2,4,8,16]:[.001,.01,.1,.5,1,2,5,10,30,100,300,1000];
  ctx.strokeStyle='#d9e1e5';ctx.lineWidth=.8;
  for(const level of levels){
    ctx.beginPath();
    for(let j=0;j<grid;j++)for(let i=0;i<grid;i++){
      const corners=[[xmin+i*dx,ymin+j*dx],[xmin+(i+1)*dx,ymin+j*dx],[xmin+(i+1)*dx,ymin+(j+1)*dx],[xmin+i*dx,ymin+(j+1)*dx]];
      const z=[values[j][i],values[j][i+1],values[j+1][i+1],values[j+1][i]],crossings=[];
      for(let k=0;k<4;k++){const n=(k+1)%4;if((z[k]<=level&&z[n]>level)||(z[n]<=level&&z[k]>level)){
        const fraction=(level-z[k])/(z[n]-z[k]);crossings.push([corners[k][0]+fraction*(corners[n][0]-corners[k][0]),corners[k][1]+fraction*(corners[n][1]-corners[k][1])]);
      }}
      for(let k=0;k+1<crossings.length;k+=2){ctx.moveTo(px(crossings[k][0]),py(crossings[k][1]));ctx.lineTo(px(crossings[k+1][0]),py(crossings[k+1][1]));}
    }
    ctx.stroke();
  }
  ctx.strokeStyle='#a9a5a0';ctx.lineWidth=1;ctx.setLineDash([4,4]);ctx.beginPath();
  if(config.constraint==='disk')ctx.arc(px(Number(config.center_x)),py(Number(config.center_y)),Number(config.radius)*scale,0,Math.PI*2);
  if(config.constraint==='halfplane'){ctx.moveTo(px(xmin),py(Number(config.slope)*xmin+Number(config.intercept)));ctx.lineTo(px(xmax),py(Number(config.slope)*xmax+Number(config.intercept)));}
  if(config.constraint==='box')ctx.rect(px(Number(config.xmin)),py(Number(config.ymax)),(Number(config.xmax)-Number(config.xmin))*scale,(Number(config.ymax)-Number(config.ymin))*scale);
  ctx.stroke();ctx.setLineDash([]);
  for(const r of results){
    ctx.strokeStyle=colors[r.method];ctx.fillStyle=colors[r.method];ctx.lineWidth=1.5;ctx.beginPath();
    r.path.forEach((p,i)=>i?ctx.lineTo(px(p[0]),py(p[1])):ctx.moveTo(px(p[0]),py(p[1])));ctx.stroke();
    for(const p of r.path){ctx.beginPath();ctx.arc(px(p[0]),py(p[1]),1.7,0,Math.PI*2);ctx.fill();}
    const end=r.x;ctx.beginPath();ctx.arc(px(end[0]),py(end[1]),4.5,0,Math.PI*2);ctx.fill();
  }
  const start=results[0]?.path[0];if(start){ctx.strokeStyle='#43515e';ctx.fillStyle='#fff';ctx.lineWidth=1.4;ctx.beginPath();ctx.arc(px(start[0]),py(start[1]),4,0,Math.PI*2);ctx.fill();ctx.stroke();}
  ctx.restore();ctx.strokeStyle='#dde2e6';ctx.lineWidth=1;ctx.strokeRect(L,T,pw,ph);
  ctx.fillStyle='#9ba6ae';ctx.font='12px Segoe UI, sans-serif';
  const step=span>10?5:span>5?1:.5;
  ctx.textAlign='center';for(let x=Math.ceil(xmin/step)*step;x<=xmax;x+=step)ctx.fillText(Number(x.toFixed(2)),px(x),T+ph+19);
  ctx.textAlign='right';for(let y=Math.ceil(ymin/step)*step;y<=ymax;y+=step)ctx.fillText(Number(y.toFixed(2)),L-10,py(y)+3);
  ctx.textAlign='center';ctx.fillStyle='#7e8c96';ctx.fillText('x',L+pw/2,T+ph+35);
  ctx.save();ctx.translate(L-32,T+ph/2);ctx.rotate(-Math.PI/2);ctx.fillText('y',0,0);ctx.restore();
  document.querySelector('#plot-description').textContent=config.function==='sphere'?'f(x, y) = x² + y²':'f(x, y) = (1 − x)² + 100(y − x²)²';
}
new ResizeObserver(draw).observe(document.querySelector('#plot-area'));
updateFields();run();
