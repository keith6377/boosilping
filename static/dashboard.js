
  // THEME
  const root = document.documentElement;
  const savedTheme = localStorage.getItem('theme2');
  if (savedTheme === 'dark') root.classList.add('dark');
  const _darkToggle = document.getElementById('darkToggle');
  if (_darkToggle) {
    _darkToggle.onclick = () => {
      root.classList.toggle('dark');
      localStorage.setItem('theme2', root.classList.contains('dark') ? 'dark' : 'light');
    };
  }
  const _year = document.getElementById('year');
  if (_year) _year.textContent = new Date().getFullYear();



  // ✅ 안전한 캔버스 사이징: CSS 높이가 0이어도 attribute/기본값으로 보정
  function sizeCanvas(c, defaultH = 220) {
    // 폭: 우선 clientWidth/offsetWidth → 없으면 부모 폭 → 마지막으로 600
    const w =
      c.clientWidth || c.offsetWidth || (c.parentElement && c.parentElement.clientWidth) || 600;

    // 높이: CSS(client/offset) → HTML attribute(height) → 기본값
    let h = c.clientHeight || c.offsetHeight;
    if (!h) {
      const attrH = parseInt(c.getAttribute('height'), 10);
      h = Number.isFinite(attrH) ? attrH : defaultH;
    }

    c.width = w;
    c.height = h;

    const ctx = c.getContext('2d');
    ctx.clearRect(0, 0, w, h);
    return { w, h, ctx };
  }

  // UTIL
  const clamp=(v,mi,ma)=> Math.max(mi, Math.min(ma,v));
  const rand=(mi,ma)=> Math.floor(Math.random()*(ma-mi+1))+mi;
  const rfloat=(mi,ma)=> mi + Math.random()*(ma-mi);
  const fmtKRW=v=>'₩'+v.toLocaleString('ko-KR');
  const pct=v=> (v).toFixed(1)+'%';

  function spark(el, arr, color){
    const c = typeof el==='string' ? document.getElementById(el) : el;
    if (!c) return;
    const w = c.width = c.clientWidth;
    const h = c.height = c.clientHeight;
    const ctx = c.getContext('2d');
    const max = Math.max(...arr), min = Math.min(...arr);
    const X = i => i*(w/(arr.length-1));
    const Y = v => h - ((v-min)/(max-min || 1))*h;

    ctx.clearRect(0,0,w,h);
    const g = ctx.createLinearGradient(0,0,0,h);
    g.addColorStop(0,color); g.addColorStop(1,'transparent');
    ctx.beginPath(); ctx.moveTo(0,h);
    arr.forEach((v,i)=> ctx.lineTo(X(i), Y(v)));
    ctx.lineTo(w,h); ctx.closePath(); ctx.fillStyle=g; ctx.fill();

    ctx.beginPath(); ctx.lineWidth=2; ctx.strokeStyle=color;
    ctx.moveTo(0, Y(arr[0]));
    arr.forEach((v,i)=> ctx.lineTo(X(i), Y(v)));
    ctx.stroke();
  }

  function lineChart(el, data, color){
    const c = document.getElementById(el);
    if (!c) return; // safely skip if canvas not present
    const ctx = c.getContext('2d');
    
    const w=c.width=c.clientWidth; const h=c.height=c.clientHeight; ctx.clearRect(0,0,w,h);
    const max=Math.max(...data), min=Math.min(...data); const pad=28; const X=i=> pad + i*((w-pad*2)/(data.length-1)); const Y=v=> pad + (h-pad*2) - ((v-min)/(max-min||1))*(h-pad*2);
    // axes
    ctx.strokeStyle='rgba(15,23,42,.12)'; if(root.classList.contains('dark')) ctx.strokeStyle='rgba(226,232,240,.12)';
    ctx.beginPath(); ctx.moveTo(pad,pad); ctx.lineTo(pad,h-pad); ctx.lineTo(w-pad,h-pad); ctx.stroke();
    const g=ctx.createLinearGradient(0,pad,0,h-pad); g.addColorStop(0,color); g.addColorStop(1,'transparent');
    ctx.beginPath(); ctx.moveTo(X(0),Y(data[0])); for(let i=1;i<data.length;i++) ctx.lineTo(X(i),Y(data[i])); ctx.lineTo(w-pad,h-pad); ctx.lineTo(pad,h-pad); ctx.closePath(); ctx.fillStyle=g; ctx.fill();
    ctx.beginPath(); ctx.lineWidth=2; ctx.strokeStyle=color; ctx.moveTo(X(0),Y(data[0])); for(let i=1;i<data.length;i++) ctx.lineTo(X(i),Y(data[i])); ctx.stroke();
  }
  function multiLine(el, series){
  const c = document.getElementById(el);
  const { w, h, ctx } = sizeCanvas(c, 220);
    const all=series.flatMap(s=>s.data); const max=Math.max(...all), min=Math.min(...all); const pad=30; const X=(i,N)=> pad + i*((w-pad*2)/(N-1)); const Y=v=> pad + (h-pad*2) - ((v-min)/(max-min||1))*(h-pad*2);
    ctx.strokeStyle='rgba(15,23,42,.12)'; if(root.classList.contains('dark')) ctx.strokeStyle='rgba(226,232,240,.12)';
    ctx.beginPath(); ctx.moveTo(pad,pad); ctx.lineTo(pad,h-pad); ctx.lineTo(w-pad,h-pad); ctx.stroke();
    series.forEach(s=>{ ctx.beginPath(); ctx.lineWidth=2; ctx.strokeStyle=s.color; ctx.moveTo(X(0,s.data.length),Y(s.data[0])); for(let i=1;i<s.data.length;i++) ctx.lineTo(X(i,s.data.length),Y(s.data[i])); ctx.stroke(); });
  }
  function donut(el, val, total, color){
    const c=document.getElementById(el), ctx=c.getContext('2d'), w=c.width=c.clientWidth, h=c.height=c.clientHeight, r=Math.min(w,h)/2-8, cx=w/2, cy=h/2; ctx.clearRect(0,0,w,h);
    ctx.beginPath(); ctx.lineWidth=r*0.36; ctx.strokeStyle='#e5e7eb'; if(root.classList.contains('dark')) ctx.strokeStyle='#1f2937'; ctx.arc(cx,cy,r*0.6,-Math.PI/2, Math.PI*1.5); ctx.stroke();
    const frac=val/total; const end=-Math.PI/2 + Math.PI*2*frac; const grad=ctx.createLinearGradient(0,0,w,0); grad.addColorStop(0,'#60a5fa'); grad.addColorStop(1,'#2563eb');
    ctx.beginPath(); ctx.lineWidth=r*0.36; ctx.strokeStyle=grad; ctx.lineCap='round'; ctx.arc(cx,cy,r*0.6,-Math.PI/2, end); ctx.stroke();
  }
  function gauge(el, pctVal){
    const c = document.getElementById(el);
    const { w, h, ctx } = sizeCanvas(c, 100);
    const cx=w/2, cy=h*0.9, r=Math.min(w,h*1.6)/2; const start=Math.PI, end=0; // half-circle
    // background arc
    ctx.beginPath(); ctx.lineWidth=14; ctx.strokeStyle='#e5e7eb'; if(root.classList.contains('dark')) ctx.strokeStyle='#1f2937'; ctx.arc(cx,cy,r,start,end); ctx.stroke();
    // value arc with color gradient green->red
    const valAngle = start + (end-start)*(pctVal/100);
    const grad=ctx.createLinearGradient(0,0,w,0); grad.addColorStop(0,'#10b981'); grad.addColorStop(0.5,'#f59e0b'); grad.addColorStop(1,'#ef4444');
    ctx.beginPath(); ctx.lineWidth=14; ctx.strokeStyle=grad; ctx.lineCap='round'; ctx.arc(cx,cy,r,start,valAngle); ctx.stroke();
    // tick
    ctx.fillStyle='var(--muted)'; ctx.font='12px system-ui'; ctx.textAlign='center'; ctx.fillText('0%', cx-r+10, cy+16); ctx.fillText('50%', cx, cy+16); ctx.fillText('100%', cx+r-10, cy+16);
  }
  function radar(el, labels, logValues, maxVal, rawValues, logIndustry, industryRaw){
    const c = document.getElementById(el);
    const { w, h, ctx } = sizeCanvas(c, 240);
    const cx=w/2, cy=h/2, r=Math.min(w,h)/2-24; 
    const N=labels.length; 
    const angle=(i)=> -Math.PI/2 + i*(Math.PI*2/N);

    // === 배경 그리드 ===
    const steps = 4;
    for(let t=0;t<=steps;t++){
      const rr = r*(t/steps);
      ctx.beginPath();
      for(let i=0;i<N;i++){
        const a=angle(i);
        const x=cx+rr*Math.cos(a), y=cy+rr*Math.sin(a);
        i? ctx.lineTo(x,y): ctx.moveTo(x,y);
      }
      ctx.closePath(); ctx.stroke();
    }

    // === 축 라벨 ===
    ctx.fillStyle = root.classList.contains('dark') ? '#e2e8f0' : '#1e293b';
    ctx.font = "12px sans-serif";
    for(let i=0;i<N;i++){
      const a=angle(i);
      const x=cx+(r+15)*Math.cos(a), y=cy+(r+15)*Math.sin(a);
      ctx.textAlign = "center";
      ctx.fillText(labels[i], x, y);
    }

    // === 기업 데이터 다각형 ===
    ctx.beginPath();
    for(let i=0;i<N;i++){
      const a = angle(i);
      const rr = r*(logValues[i]/maxVal);
      const x=cx+rr*Math.cos(a), y=cy+rr*Math.sin(a);
      i? ctx.lineTo(x,y): ctx.moveTo(x,y);

      // 기업 실제 값 라벨
      ctx.fillStyle = root.classList.contains('dark') ? '#e2e8f0' : '#1e293b';
      ctx.fillText(rawValues[i].toFixed(2), x, y-5);
    }
    ctx.closePath();
    ctx.strokeStyle='rgba(37,99,235,1)'; // 기업: 파랑
    ctx.stroke();
    ctx.fillStyle='rgba(37,99,235,.3)';
    ctx.fill();

    // === 업계 평균 다각형 ===
    if (logIndustry){
      ctx.beginPath();
      for(let i=0;i<N;i++){
        const a = angle(i);
        const rr = r*(logIndustry[i]/maxVal);
        const x=cx+rr*Math.cos(a), y=cy+rr*Math.sin(a);
        i? ctx.lineTo(x,y): ctx.moveTo(x,y);

        // 업계 평균 값 라벨 (주황)
        ctx.fillStyle = root.classList.contains('dark') ? '#fb923c' : '#ea580c';
        ctx.fillText(industryRaw[i].toFixed(2), x, y+12);
      }
      ctx.closePath();
      ctx.strokeStyle='rgba(234,88,12,1)'; // 업계 평균: 주황
      ctx.stroke();
      ctx.fillStyle='rgba(234,88,12,.2)';
      ctx.fill();
    }
  }




  function heatmap(el, matrix, rowLabels, colLabels){
  const c = document.getElementById(el);
  const { w, h, ctx } = sizeCanvas(c, 240);
    const rows=matrix.length, cols=matrix[0].length; const padLeft=80, padTop=24, cellW=(w-padLeft-10)/cols, cellH=(h-padTop-10)/rows;
    ctx.font='12px system-ui'; ctx.fillStyle='var(--muted)'; rowLabels.forEach((r,i)=> ctx.fillText(r, 10, padTop+cellH*i+cellH/2+4)); colLabels.forEach((cL,j)=> ctx.fillText(cL, padLeft+cellW*j+6, 16));
    for(let i=0;i<rows;i++) for(let j=0;j<cols;j++){
      const v=matrix[i][j]; // normalize 0..1
      const r=255*(1-v), g=255*(1- Math.abs(0.5-v)*2), b=255*v; // simple blue-red scale
      ctx.fillStyle = `rgb(${r.toFixed(0)},${g.toFixed(0)},${b.toFixed(0)})`;
      ctx.fillRect(padLeft+cellW*j, padTop+cellH*i, cellW-2, cellH-2);
    }
  }


  function hbar(el, labels, values, colors, unit) {
  const c = document.getElementById(el);
  if (!c) return;
  const { w, h, ctx } = sizeCanvas(c, 220);

  const padL = 140, padR = 60;
  const barH = Math.max(1, (h - 20) / labels.length - 6);

  // 숫자 배열 정규화 + 최대값 최소 1 보장
  const v = values.map(x => Number(x) || 0);
  const max = Math.max(...v, 1);           // ← ✅ 0일 때도 최소 1

  ctx.clearRect(0, 0, w, h);
  ctx.font = '12px system-ui';
  const displayUnit = unit || '%';

  labels.forEach((lb, i) => {
    const val = v[i];
    const ratio = val / max;               // ← 0 ≤ ratio ≤ 1
    const width = (w - padL - padR) * ratio;

    const y0 = 10 + i * (barH + 10);
    const x0 = padL;

    // 라벨
    ctx.fillStyle = 'var(--muted)';
    ctx.textAlign = 'left';
    ctx.fillText(lb, 10, y0 + barH - 2);

    // 막대 (색상 인덱스 안전 처리)
    ctx.fillStyle = (colors && colors[i]) ? colors[i] : '#2563eb';
    ctx.fillRect(x0, y0, width, barH);

    // 값 라벨
    ctx.fillStyle = 'var(--text)';
    ctx.textAlign = 'left';
    ctx.fillText(`${val.toFixed(1)} ${displayUnit}`, x0 + width + 6, y0 + barH - 2);
  });
}




function hbarSigned(el, labels, values, colors, unit) {
  const c = document.getElementById(el);
  const { w, h, ctx } = sizeCanvas(c, 220);

  const padL = 140, padR = 60;
  const barH = (h - 20) / labels.length - 6;

  // ✅ 절댓값 기준으로 최대값 잡기
  const max = Math.max(...values.map(v => Math.abs(v)));

  ctx.font = '12px system-ui';
  const displayUnit = unit || '%';

  labels.forEach((lb, i) => {
    const val = values[i];
    const ratio = Math.abs(val) / max;   // ✅ 음수도 양수처럼 비율 계산
    const width = (w - padL - padR) * ratio;

    const y0 = 10 + i * (barH + 10);
    const x0 = padL;

    // 라벨 (항목 이름)
    ctx.fillStyle = '#42464dff';
    ctx.textAlign = 'left';
    ctx.fillText(lb, 10, y0 + barH - 2);

    // 막대 색상: 음수 → 빨강, 양수 → 파랑(또는 기존 colors[i])
    ctx.fillStyle = val < 0 ? '#dc2626' : '#2563eb';
    ctx.fillRect(x0, y0, width, barH);

    // 값 라벨
    ctx.fillStyle = val < 0 ? '#dc2626' : '#2563eb';
    ctx.textAlign = 'left';
    ctx.fillText(
      val.toFixed(1) + ' ' + displayUnit,
      x0 + width + 6,
      y0 + barH - 2
    );
  });
}




// XAI 전용 hbar (기업 값 + 업종 평균 표시)
function hbarXAI(el, labels, values, industryAvgs, unit){
  const c = document.getElementById(el);
  const { w, h, ctx } = sizeCanvas(c, 320);

  const padL = 200, padR = 100;
  const rowH = 31;      // 피쳐 하나당 높이 (기업+평균)
  const barH = 13;    // 막대 높이

  // log 스케일 적용 (0 이하일 때는 그냥 0으로 처리)
  const transformedVals = values.map(v => v ? Math.log1p(Math.abs(v)) : 0);
  const transformedAvgs = industryAvgs.map(v => v ? Math.log1p(Math.abs(v)) : 0);
  const max = Math.max(...transformedVals, ...transformedAvgs, 1); // 0만 있으면 NaN 방지

  ctx.font = '12px system-ui';
  const displayUnit = unit || '%';

  const barColors = [
    '#93c5fd', '#a7f3d0', '#c4b5fd',
    '#fcd34d', '#f9a8d4', '#fde68a'
  ];

  labels.forEach((lb, i) => {
    const val = values[i];
    const avg = industryAvgs[i];

    const tval = val ? transformedVals[i] : 0;
    const tavg = avg ? transformedAvgs[i] : 0;

    const widthVal = ((w - padL - padR) * (tval / max));
    const widthAvg = ((w - padL - padR) * (tavg / max));

    const baseY = 5 + i * rowH;
    const x0 = padL;

    // ✅ 피쳐명
    ctx.fillStyle = '#374151';
    ctx.textAlign = 'left';
    ctx.fillText(lb, 10, baseY + barH);

    // ✅ 기업 값 막대 (데이터 있으면 그림, 없으면 X)
    if (val !== null && val !== undefined) {
      ctx.fillStyle = barColors[i % barColors.length];
      ctx.fillRect(x0, baseY, widthVal, barH);

      ctx.fillStyle = val < 0 ? '#ef4444' : '#3b82f6';
      ctx.textAlign = 'left';
      ctx.fillText(
        (val === 0 ? '데이터 없음' : (val >= 0 ? '+' : '') + val.toFixed(1) + displayUnit),
        x0 + (val === 0 ? 0 : widthVal + 6),
        baseY + barH - 2
      );
    }

    // ✅ 업종 평균 막대
    const avgY = baseY + barH;
    if (avg !== null && avg !== undefined) {
      ctx.fillStyle = '#9ca3af';
      ctx.fillRect(x0, avgY, widthAvg, barH);

      ctx.fillStyle = avg < 0 ? '#ef4444' : '#3b82f6';
      ctx.textAlign = 'left';
      ctx.fillText(
        (avg === 0 ? '데이터 없음' : (avg >= 0 ? '+' : '') + avg.toFixed(1) + displayUnit),
        x0 + (avg === 0 ? 0 : widthAvg + 6),
        avgY + barH - 2
      );
    }
  });
}


function drawChart(ctx, w, h, points, X, Y) {
  const pad=36;

  // --- 축 ---
  ctx.strokeStyle='rgba(15,23,42,.12)';
  if(root.classList.contains('dark')) ctx.strokeStyle='rgba(226,232,240,.12)';
  ctx.beginPath();
  ctx.moveTo(pad,pad);
  ctx.lineTo(pad,h-pad);
  ctx.lineTo(w-pad,h-pad);
  ctx.stroke();

  ctx.font='12px system-ui';
  ctx.fillStyle='var(--muted)';
  ctx.fillText('부채비율(%)', w/2-40, h-6);
  ctx.save();
  ctx.translate(10,h/2);
  ctx.rotate(-Math.PI/2);
  ctx.fillText('ROE(%)', -30, 0);
  ctx.restore();

  let drawnPoints = [];

  // 1) 일반 점 먼저 그림 (빨강/주황 제외)
  points.filter(p =>
    !(p.color && (p.color.includes("239,68,68") || p.color.includes("245,158,11")))
  ).forEach(p => {
    const x = X(p.x), y = Y(p.y);
    const r = p.r ? p.r : 4;

    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI*2);
    ctx.fillStyle = p.color || 'rgba(37,99,235,.5)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(37,99,235,.9)';
    ctx.lineWidth = 1;
    ctx.stroke();

    drawnPoints.push({x, y, r, label:p.label});
  });

  // 2) 강조 점 (빨강 + 주황) → 항상 최상단
  points.filter(p =>
    p.color && (p.color.includes("239,68,68") || p.color.includes("245,158,11"))
  ).forEach(p => {
    const x = X(p.x), y = Y(p.y);
    const r = p.r ? p.r : 4;   // ✅ 다른 점과 동일 크기

    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI*2);
    ctx.fillStyle = p.color;
    ctx.fill();

    // ✅ 테두리 강조
    ctx.strokeStyle = "#000";
    ctx.lineWidth = 1.5;
    ctx.stroke();

    drawnPoints.push({x, y, r, label:p.label});
  });

  return drawnPoints;
}




function bubble(el, points){
  const c = document.getElementById(el);
  const { w, h, ctx } = sizeCanvas(c, 220);

  const pad=36;
  const xs=points.map(p=>p.x), ys=points.map(p=>p.y);
  const maxX=Math.max(...xs), minX=Math.min(...xs);
  const maxY=Math.max(...ys), minY=Math.min(...ys);
  const X=v=> pad + (v-minX)/(maxX-minX||1)*(w-pad*2);
  const Y=v=> h-pad - (v-minY)/(maxY-minY||1)*(h-pad*2);

  // --- 기본 차트 그림 ---
  let drawnPoints = drawChart(ctx, w, h, points, X, Y);

  // 기본 차트 이미지를 저장해둠
  const baseImage = c.toDataURL();

  // hover 이벤트
  c.onmousemove = function(evt) {
    const rect = c.getBoundingClientRect();
    const mx = evt.clientX - rect.left;
    const my = evt.clientY - rect.top;

    // 배경을 저장된 이미지로 복원 (축/점/라벨 유지)
    const img = new Image();
    img.src = baseImage;
    img.onload = function() {
      ctx.clearRect(0,0,w,h);
      ctx.drawImage(img, 0, 0);

      // hover된 점 찾기
      for (let dp of drawnPoints) {
        const dist = Math.sqrt((mx-dp.x)**2 + (my-dp.y)**2);
        if (dist <= dp.r+3) {
          ctx.fillStyle = 'black';
          ctx.fillRect(mx+10, my-20, dp.label.length*7+100, 20);
          ctx.fillStyle = 'white';
          ctx.fillText(dp.label, mx+15, my-6);
          break;
        }
      }
    };
  };
}



// ✅ 서버에서 넘겨준 데이터만 사용
if (!window.SERVER_COMPANIES) {
  console.error("SERVER_COMPANIES 데이터가 없습니다. FastAPI가 데이터를 넘겨줘야 합니다.");
}
const companies = window.SERVER_COMPANIES;



  // STATE / FILTERS
  const state = {
    industry:'all', size:'all', grade:'all', pdMin:0, pdMax:20,
    query:'', range:'36m', year:'all',
    companyId: null
  };


  // KPI & Derived
  function computeIndustryAvg(list){
    const arr=list.map(x=>x.pd); const avg=arr.reduce((a,b)=>a+b,0)/(arr.length||1); return avg;
  }
  function percentileRank(list, val){
    const arr=[...list].sort((a,b)=>a-b); const idx=arr.findIndex(v=> v>=val); return Math.round((idx/arr.length)*100);
  }

  // RENDER: KPIs
  function renderKPIs(filtered){
    const company = filtered[0] || companies[0]; // 대표 기업 (필터 후 첫번째)
    const pd = company.pd; const grade = company.grade; const score = company.score;
    // PD Gauge
    // gauge('gaugePD', pd);
    if (document.getElementById('kpiPD')) document.getElementById('kpiPD').textContent = pct(pd);
    const industryAvg = computeIndustryAvg(filtered);
    const rank = percentileRank(filtered.map(x=>x.pd), pd);
    if (document.getElementById('kpiPDNote')) document.getElementById('kpiPDNote').textContent = rank>=90? '상위 10% 위험군' : '상위 10% 위험군 아님';
    const d = pd - industryAvg; const delta = (d>=0?'+':'')+d.toFixed(1)+'pp 업종대비';
    // const dEl = document.getElementById('kpiPDDelta') && document.getElementById('kpiPDDelta'); dEl.textContent = delta; dEl.className = 'delta ' + (d<=0? 'good': 'bad');
    const dEl = document.getElementById('kpiPDDelta'); if (dEl) {dEl.textContent = delta; dEl.className = 'delta ' + (d <= 0 ? 'good' : 'bad');}
    // Grade donut
    const map={A:820,B:720,C:630,D:540}; const total=900; const val=map[grade]||score;
    // donut('scoreDonut', val, total, '#60a5fa');
    if (document.getElementById('kpiGrade')) document.getElementById('kpiGrade').textContent = grade;
    const gd = grade==='A'?'good': grade==='B'?'neutral':'bad';
    const ge = document.getElementById('kpiGradeDelta'); if (ge) { ge.className='delta '+gd; ge.textContent = grade==='A'? '등급 안정' : grade==='B'? '주시 필요' : '개선 필요'; }
    if (document.getElementById('kpiScore')) document.getElementById('kpiScore').textContent = score;

    const gradeEl = document.getElementById('kpiGrade');
    if (gradeEl) {
      gradeEl.textContent = grade;
      gradeEl.className = ''; // 기존 클래스 초기화
      gradeEl.classList.add('num', 'grade-' + grade); 
    }
    
  

    // Industry spark
    const sparkSeries = Array.from({length:24}, ()=> clamp(industryAvg + rfloat(-1,1), 0.2, 22));
    if (document.getElementById('sparkIndustry')) spark('sparkIndustry', sparkSeries, '#2563eb');
    if (document.getElementById('kpiIndustry')) document.getElementById('kpiIndustry').textContent = pct(industryAvg);
    if (document.getElementById('kpiIndustryDelta')) document.getElementById('kpiIndustryDelta').textContent = `업종 내 위치: 상위 ${rank}%`;
    // Macro composite spark (dummy)
    const macroComposite = Array.from({length:24}, (_,i)=> 50 + Math.sin(i/3)*10 + rand(-3,3));
    if (document.getElementById('sparkMacro')) spark('sparkMacro', macroComposite, '#10b981');
    const last=macroComposite.at(-1); if (document.getElementById('kpiMacro')) document.getElementById('kpiMacro').textContent = last>55? '완화' : last<45? '긴축' : '안정';
    if (document.getElementById('kpiMacroDelta')) document.getElementById('kpiMacroDelta').textContent = '리스크 ' + (last>55? '낮음' : last<45? '높음' : '중립');
  }

// RENDER: Industry Average Credit Score (산업 평균용, 별도 함수)
  function renderIndustryCreditScore(filtered){
    const company = filtered[0] || companies[0];
    const industry = company.industry;

    const peers = companies.filter(c => c.industry === industry);
    const industryScore = Math.round(peers.reduce((a, b) => a + b.score, 0) / peers.length);

    let industryGrade = "D";
    if (industryScore >= 820) industryGrade = "A";
    else if (industryScore >= 720) industryGrade = "B";
    else if (industryScore >= 630) industryGrade = "C";

    const total = 900;
    // donut('scoreDonutIndustry', industryScore, total, '#60a5fa');

    const gradeEl = document.getElementById('kpiGradeIndustry');
    if (gradeEl) {
  gradeEl.textContent = industryGrade;
  gradeEl.className = ''; // 기존 클래스 초기화
  gradeEl.classList.add('num', 'grade-' + industryGrade);
}

    const gd = industryGrade==='A' ? 'good' : industryGrade==='B' ? 'neutral' : 'bad';
    const ge = document.getElementById('kpiGradeDeltaIndustry');
    if (ge) {
      ge.className = 'delta ' + gd;
      ge.textContent = industryGrade==='A' ? '등급 안정' :
                      industryGrade==='B' ? '주시 필요' : '개선 필요';
    }

    const scoreEl = document.getElementById('kpiScoreIndustry');
    if (scoreEl) scoreEl.textContent = industryScore;
  }

  function gaugeMini(el, value, goodRange){
  value = Number(value);
  if (!isFinite(value)) value = 0;

  const c = document.getElementById(el);
  const { w, h, ctx } = sizeCanvas(c, 100);
  const cx=w/2, cy=h*0.8, r=Math.min(w,h*1.6)/2;
  const start=Math.PI, end=0;

  ctx.beginPath(); ctx.lineWidth=12; ctx.strokeStyle='#e5e7eb';
  if(root.classList.contains('dark')) ctx.strokeStyle='#1f2937';
  ctx.arc(cx,cy,r,start,end); ctx.stroke();

  const grad=ctx.createLinearGradient(0,0,w,0);
  grad.addColorStop(0,'#10b981'); grad.addColorStop(0.6,'#f59e0b'); grad.addColorStop(1,'#ef4444');

  const ratio = clamp(value / (goodRange.max*1.5), 0, 1);
  ctx.beginPath(); ctx.lineWidth=12; ctx.strokeStyle=grad; ctx.lineCap='round';
  ctx.arc(cx,cy,r,start, start + (end-start)*ratio ); ctx.stroke();

  ctx.font='12px system-ui'; ctx.fillStyle='var(--muted)'; ctx.textAlign='center';
  ctx.fillText(value.toFixed(0)+'%', cx, cy+14);
}

  function renderSolvency(firm){
    if (!firm) return;

    const peers = companies.filter(c => c.industry === firm.industry);
    const avg = (key) => peers.reduce((a,b)=> a + (b[key]||0), 0) / (peers.length||1);

    const labels = ['부채비율', '유동비율', '당좌비율'];
    const values = [
      firm.debt_ratio ?? 0,
      firm.current_ratio ?? 0,
      firm.quick_ratio ?? 0
    ];
    const industryValues = [
      avg('debt_ratio'),
      avg('current_ratio'),
      avg('quick_ratio')
    ];
    const colors = ['#2563eb', '#9ca3af']; // 기업: 파랑, 업종: 회색

    vbar('chartSolvency', labels, values, industryValues, colors);

    const sum = document.getElementById('solvencySummary');
    if (sum) {
      sum.innerHTML = `<b>${firm.name}</b> vs 업종 평균 안정성 지표`;
    }
  }


  // Profitability & Growth
  const baseSeries = Array.from({length:36}, ()=> rand(-6, 18)); // growth %
  const profitSeries = { 
    ROE: Array.from({length:36}, ()=> rfloat(-2, 16)), 
    ROA: Array.from({length:36}, ()=> rfloat(-1, 9)), 
    ROIC: Array.from({length:36}, ()=> rfloat(0, 14)) 
  };

  function renderProfit(filtered){
    const firm = (filtered && filtered[0]) || companies[0];  // ✅ 필터링된 기업 반영
    

    const labels = ['매출성장률','영업이익성장률','ROE','ROA','ROIC'];
    const values = [
      firm.sales_growth ?? 0,
      firm.profit_growth ?? 0,
      firm.roe ?? 0,
      firm.roa ?? 0,
      firm.roic ?? 0
    ];
    const colors = ['#2563eb','#60a5fa','#10b981','#22c55e','#0ea5e9'];

    hbarSigned('chartProfitGrowth', labels, values, colors);

    const sum = document.getElementById('profitSummary');
    if (sum) {
      sum.innerHTML = `<b>${firm.name}</b>의 주요 수익성 · 성장성 지표`;
    }
  }

  // Profitability & Growth (업종평균)
  function renderProfitIndustry(filtered){
    const company = filtered[0] || companies[0];
    const peers = companies.filter(c =>
      c.industry === company.industry &&
      (state.year === 'all' || String(c.year) === String(state.year))
    );

    const avg = (key) => peers.reduce((a,b)=> a + (b[key]||0), 0) / (peers.length||1);
    const labels = ['매출성장률','영업이익성장률','ROE','ROA','ROIC'];
    const values = [
      avg('sales_growth'),
      avg('profit_growth'),
      avg('roe'),
      avg('roa'),
      avg('roic')
    ];
    const colors = ['#2563eb','#60a5fa','#10b981','#22c55e','#0ea5e9'];

    hbarSigned('chartProfitGrowthIndustry', labels, values, colors);

    // 요약 텍스트도 업데이트 가능
    const summaryEl = document.getElementById('profitSummaryIndustry');
if (summaryEl) {
  summaryEl.innerHTML =
    `업종 평균: <b>${company.industry}</b> (${peers.length}개 기업)`;
}
  }


  // Activity (Radar) & CashFlow (Heatmap)
  function renderActivity(firm){
    if (!firm) return;
    const labels = ['재고회전', '채권회전', '총자산회전', '비유동회전'];

    // 기업 실제 값
    const rawVals = [
      Number(firm.inventory_turnover) || 0,
      Number(firm.receivables_turnover) || 0,
      Number(firm.asset_turnover) || 0,
      Number(firm.fixed_asset_turnover) || 0
    ];

    // === 업계 평균 구하기 ===
    const industryFirms = companies.filter(c => 
      c.industry === firm.industry &&
      (state.year === 'all' || String(c.year) === String(state.year))
    );
    const industryAverages = labels.map((_, idx) => {
      const key = ["inventory_turnover","receivables_turnover","asset_turnover","fixed_asset_turnover"][idx];
      const vals = industryFirms.map(c => Number(c[key]) || 0);
      return vals.length ? vals.reduce((a,b)=>a+b,0)/vals.length : 0;
    });


    // 로그 변환
    const logVals = rawVals.map(v => Math.log(1+v));
    const logIndustry = industryAverages.map(v => Math.log(1+v));
    const maxVal = Math.max(...logVals, ...logIndustry, 1);

    // Radar 호출 (기업값 + 업계 평균)
    radar('chartRadar', labels, logVals, maxVal, rawVals, logIndustry, industryAverages);
  }


  function renderCashFlow(){
  const firm = companies[0];
  const rows = ['영업CF/자산', '영업CF/부채', '영업CF/매출'];
  const cols = ['최근'];

  let raw = [
    Number(firm.operating_cf_to_assets) || 0,
    Number(firm.operating_cf_to_debt) || 0,
    Number(firm.operating_cf_to_sales) || 0
  ];

  // 🔹 절대값 기준으로 -1 ~ +1 범위 정규화
  const maxAbs = Math.max(...raw.map(v => Math.abs(v)), 1);
  const matrix = raw.map(v => [v / maxAbs]);

  heatmap('chartHeat', matrix, rows, cols);
}



// === XAI: 상위 요인 (기업 + 업종 평균) ===
function renderDrivers(entity) {
  if (!entity) return;
  const ySel = document.getElementById('fYear')?.value;
  const year =
    (window.state?.year && window.state.year !== 'all')
       ? window.state.year
       : (ySel && ySel !== 'all' ? ySel : (entity?.year || 2023));
  const cid = entity.idx;

  fetch(`/api/drivers?year=${encodeURIComponent(year)}&company_id=${encodeURIComponent(cid)}`)
    .then(r => r.json())
    .then(d => {
      if (!d || !Array.isArray(d.labels) || !Array.isArray(d.effects)) {
        // 데이터 없을 때 안내
        hbarXAI('chartDrivers', ['(데이터 없음)'], [0], [0], '%');
        return;
      }
      hbarXAI('chartDrivers', d.labels, d.effects, d.industry_avgs || new Array(d.effects.length).fill(0), '%');
    })
    .catch(console.error);
}




  // Simulation
  function modelPD({roe, optl, ffoeq, profitGrowth, apTurn, icr}) {
    let base = 15; // 기준 PD

    // 값이 클수록 PD가 줄어듦
    base -= (roe / 20) * 5;             // ROE
    base -= (optl / 10) * 4;            // 영업이익/총부채
    base -= (ffoeq / 20) * 3;           // FFOEQ
    base -= (profitGrowth / 50) * 4;    // 영업손익증가율
    base -= (apTurn / 10) * 2;          // 매입채무회전율
    base -= (icr / 10) * 5;             // 재무보상비율

    return clamp(base, 0.2, 35); // 최소~최대 범위
  }

// === REPLACE WHOLE FUNCTION ===
function bindSimulation(companyId, year) {
  const get = id => document.getElementById(id);

  // 슬라이더 (있는 것만 사용)
  const sROE = get('sROE'), sOPTL = get('sOPTL'), sFFOEQ = get('sFFOEQ');
  const sProfitGrowth = get('sProfitGrowth'), sAPTurn = get('sAPTurn'), sICR = get('sICR');
  const sliders = [sROE, sOPTL, sFFOEQ, sProfitGrowth, sAPTurn, sICR].filter(Boolean);

  // 전역 목록/선택 기업/연도
  const list = (window.companies || window.SERVER_COMPANIES || []);
  const fallbackFirm = list[0] || {};
  const cid = companyId ?? window.state?.companyId ?? fallbackFirm.idx;
  const yr  = year ?? ((window.state?.year && window.state.year !== 'all') ? window.state.year : (fallbackFirm.year || new Date().getFullYear()));

  // 선택 기업과 현재 PD(실데이터)
  const firm = list.find(c => String(c.idx) === String(cid)) || fallbackFirm;
  const baselinePd = Number(firm?.pd) || 0;

  // 표시 타깃
  const eNow   = get('simNow');
  const eAfter = get('simAfter');
  const eImp   = get('improveChance');

  // 값 읽기 (range/number 대응)
  const num = el => {
    if (!el) return 0;
    if (typeof el.valueAsNumber === 'number' && !Number.isNaN(el.valueAsNumber)) return el.valueAsNumber;
    const v = parseFloat(el.value); return Number.isFinite(v) ? v : 0;
  };

  // 피처 기여도(“값↑ ⇒ PD↓” 방향) 점수 함수
  // 👉 가중치는 기존 modelPD와 동일한 비율을 사용
  const contribution = ({roe, optl, ffoeq, profitGrowth, apTurn, icr}) =>
      (roe/20)*5 + (optl/10)*4 + (ffoeq/20)*3 + (profitGrowth/50)*4 + (apTurn/10)*2 + (icr/10)*5;

  // 현재 슬라이더로 피처 묶음 얻기
  const getFeats = () => ({
    roe: num(sROE),
    optl: num(sOPTL),
    ffoeq: num(sFFOEQ),
    profitGrowth: num(sProfitGrowth),
    apTurn: num(sAPTurn),
    icr: num(sICR),
  });

  // 기준 기여도(서버 초기 피처값 기준) — 이후 “변화분”을 계산하는 기준점
  let baseScore = 0;

  // 현재 PD는 한 번만 고정 표시
  if (eNow) eNow.textContent = baselinePd.toFixed(1) + '%';

  // 개선 후 PD 재계산 (항상 baselinePd에서 출발)
  function recalc() {
    // 변화분(+)이면 PD 내려감, 변화분(-)이면 PD 올라감
    const delta = contribution(getFeats()) - baseScore;
    let after = baselinePd - delta;                 // ← “현재 PD”에서 변화분만 반영
    after = Math.max(0.2, Math.min(35, after));    // 안전 클램프
    if (eAfter) eAfter.textContent = after.toFixed(1) + '%';
    if (eImp)   eImp.textContent   = `현재 PD와의 차이: ${(baselinePd - after).toFixed(1)}pp`;
  }

  // 리스너 중복 제거 후 재바인딩 (input + change 모두)
  if (window._sim && Array.isArray(window._sim.handlers)) {
    window._sim.handlers.forEach(({el, on}) => {
      try { el.removeEventListener('input', on); } catch {}
      try { el.removeEventListener('change', on); } catch {}
    });
  }
  const handlers = [];
  sliders.forEach(el => {
    const on = () => {
      const lbl = get(el.id + 'V');
      if (lbl) lbl.textContent = el.value;
      recalc();
    };
    el.addEventListener('input', on);
    el.addEventListener('change', on);
    handlers.push({ el, on });
  });
  window._sim = { handlers, cid, yr };

  // 1) 서버 도착 전, 현재 슬라이더 값으로 임시 기준/표시
  baseScore = contribution(getFeats());
  recalc();

  // 2) 서버 초기 피처값 반영 → 그 값으로 기준점(baseScore) 재설정 → 다시 계산
  fetch(`/api/drivers?year=${encodeURIComponent(yr)}&company_id=${encodeURIComponent(cid)}`)
    .then(r => r.json())
    .then(d => {
      const pairs = [
        { el: sROE,          idx: 0, label: 'sROEV' },
        { el: sOPTL,         idx: 1, label: 'sOPTLV' },
        { el: sFFOEQ,        idx: 2, label: 'sFFOEQV' },
        { el: sProfitGrowth, idx: 3, label: 'sProfitGrowthV' },
        { el: sAPTurn,       idx: 4, label: 'sAPTurnV' },
        { el: sICR,          idx: 5, label: 'sICRV' },
      ];

      if (Array.isArray(d?.effects)) {
        pairs.forEach(({el, idx, label}) => {
          if (!el) return;
          const v = Number(d.effects[idx] ?? 0);
          el.value = v;
          const margin = Math.abs(v) * 1.5 || 10;
          el.min = Math.floor(v - margin);
          el.max = Math.ceil(v + margin);
          const lbl = get(label);
          if (lbl) lbl.textContent = v.toFixed(1);
        });
      }

      // 서버가 준 “현재 피처값”으로 기준점 재설정
      baseScore = contribution(getFeats());
      recalc();  // ← 기준 재설정 후 바로 업데이트
    })
    .catch(console.error);
}







  // Roadmap
  function renderRoadmap(){
    const c = document.getElementById('chartRoadmap');
    if (!c) return;  // ← 요소 없으면 그냥 종료

    const ctx = c.getContext('2d'),
          w = c.width = c.clientWidth,
          h = c.height = c.clientHeight;

    ctx.clearRect(0,0,w,h);

    const segments=[
      {name:'Planned',v:rand(20,40), color:'#93c5fd'},
      {name:'In-progress',v:rand(30,50), color:'#60a5fa'},
      {name:'Completed',v:rand(10,40), color:'#2563eb'}
    ];
    const total = segments.reduce((a,b)=>a+b.v,0), pad=20;
    let x=pad; const barH=38; const y=(h-barH)/2;

    segments.forEach(s=>{
      const wSeg=(w-pad*2)*s.v/total;
      ctx.fillStyle=s.color;
      ctx.fillRect(x,y,wSeg,barH);
      x+=wSeg+2;
    });

    ctx.font='12px system-ui';
    ctx.fillStyle='var(--muted)';
    let labelX=pad;
    segments.forEach(s=>{
      const wSeg=(w-pad*2)*s.v/total;
      ctx.fillText(`${s.name} ${Math.round(s.v/total*100)}%`, labelX+6, y-6);
      labelX+=wSeg;
    });

    const summary = document.getElementById('roadmapSummary');
    if (summary){
      summary.innerHTML = `<span class="status ok">Completed ${Math.round(segments[2].v/total*100)}%</span> · <span class="status">In-progress ${Math.round(segments[1].v/total*100)}%</span>`;
    }
  }


  // Peers bubble
  // 동종업계 비교 산점도 렌더 (교체)
function renderPeers(list, searchCompany = null) {
  const lead = (window.companies || []).find(
    c => String(c.idx) === String(state.companyId)
  ) || (list && list[0]);
  if (!lead) return;

  const peers = Array.isArray(list) ? list : [];

  // 회색 점들
  const pts = peers.map(e => ({
    x: e.debt_ratio,
    y: e.roe,
    r: 0,
    label: e.name,
    color: "rgba(99,102,241,.60)"  // 회색
  }));

  // 초록 점 (검색 기업) - 먼저 추가
  if (searchCompany && String(searchCompany.idx) !== String(lead.idx)) {
    pts.push({
      x: Number(searchCompany.debt_ratio) || 0,
      y: Number(searchCompany.roe) || 0,
      r: 0,
      label: searchCompany.name,
      color: "rgba(245,158,11,.9)"
    });
  }

  // 🔴 빨간 점(선택 기업) - 마지막에 push → 항상 최상단
  pts.push({
    x: Number(lead.debt_ratio) || 0,
    y: Number(lead.roe) || 0,
    r: 6,
    label: lead.name,
    color: "rgba(239,68,68,.9)" // 빨강
  });

  bubble("chartPeers", pts);
}






  // Macro multi
  const macro={ months:36, GDP:[], CPI:[], UNEMP:[], RATE:[] };
  for(let i=0;i<36;i++){ macro.GDP.push(rfloat(0,5)+Math.sin(i/8)); macro.CPI.push(rfloat(0,6)); macro.UNEMP.push(rfloat(2,7)); macro.RATE.push(rfloat(1,5)+Math.cos(i/10)); }
  function renderMacro(m){
    const len=m; const slice=(arr)=>arr.slice(-len);
    lineChart('mGDP', slice(macro.GDP), '#10b981');
    lineChart('mCPI', slice(macro.CPI), '#ef4444');
    lineChart('mUNEMP', slice(macro.UNEMP), '#f59e0b');
    lineChart('mRATE', slice(macro.RATE), '#2563eb');
  }

  // Entities table
  let sortKey='pd', sortDir='asc';
  function renderTable(list){
    const tbody = document.getElementById('entBody'); if (!tbody) return;
    tbody.innerHTML = '';
    list.forEach((e,i)=>{
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${i + 1}</td>
        <td>${e.name ?? '-'}</td>
        <td>${e.industry ?? '-'}</td>
        <td>${e.size ?? '-'}</td>
        <td>${Number(e.pd ?? 0).toFixed(1)}</td>
        <td>${e.grade ?? '-'}</td>
        <td>${Number(e.score ?? 0).toFixed(1)}</td>
        <td>${Number(e.debt_ratio ?? 0).toFixed(1)}</td>
        <td>${Number(e.roe ?? 0).toFixed(1)}</td>
        <td>${Number(e.assets ?? 0).toLocaleString()}</td>
      `;
      tr.onclick = () => {            // ✅ 클릭 시 선택 기업 기억 후 리렌더
        state.companyId = e.idx;
        applyFilters();
      };
      tbody.appendChild(tr);
    });
  }

// === renderTable(list) 함수 끝 ===

// ✅ 여기 추가
function loadCompaniesByYear(year) {
  if (year === "all") {
    filterAndRender();
    return;
  }
  fetch(`/api/companies?year=${encodeURIComponent(year)}`)
    .then(r => r.json())
    .then(data => {
      window.companies = Array.isArray(data) ? data : [];
      filterAndRender();
    })
    .catch(console.error);
}

function filterAndRender() {
  let list = window.companies.slice();

  if (state.industry !== "all") list = list.filter(c => c.industry === state.industry);
  if (state.size     !== "all") list = list.filter(c => c.size === state.size);
  if (state.grade    !== "all") list = list.filter(c => c.grade === state.grade);

  list = list.filter(c => {
    const pd = Number(c.pd) || 0;
    return pd >= state.pdMin && pd <= state.pdMax;
  });

  const newLead = list.find(c => String(c.idx) === String(state.companyId)) || list[0];
    if (newLead) {
      state.companyId = newLead.idx;
      renderDrivers(newLead);
      renderProfit([newLead]);
      renderProfitIndustry([newLead, ...list]);
      renderSolvency(newLead);
      renderActivity(newLead);
      renderPeers(list);
    }
    renderTable(list);
  // 👉 여기에 필요하면 KPI/차트 갱신 함수도 같이 호출
}

  

  // === 교체: applyFilters 함수 ===
function applyFilters(force=false) {
  // 0) 항상 DOM에서 최신 값을 읽어와 state를 갱신 (한 곳에서만)
  const el = id => document.getElementById(id);
  state.industry = (el("fIndustry")?.value) ?? state.industry ?? "all";
  state.size     = (el("fSize")?.value)     ?? state.size     ?? "all";
  state.grade    = (el("fGrade")?.value)    ?? state.grade    ?? "all";
  state.year     = (el("fYear")?.value)     ?? state.year     ?? "all";
  {
   const vFilter = el("fQuery")?.value;
   const vTopbar = el("q")?.value;
   if (typeof vFilter === "string" || typeof vTopbar === "string") {
     state.query = ((vFilter ?? vTopbar) || "").trim().toLowerCase();
   }
   // 둘 다 없으면 기존 state.query 유지
  }
  state.pdMin    = Number(el("fPDMin")?.value ?? state.pdMin ?? 0);
  (document.getElementById('fPDMax')||{}).value = 100;
  state.pdMax = 100;

  // 1) 원본 목록
  let list = (window.companies || window.SERVER_COMPANIES || []).slice();

  // 2) 필터들 적용 (연도 제외) — 연도는 API 파라미터로만 사용
  if (state.industry !== "all") list = list.filter(c => String(c.industry) === String(state.industry));
  if (state.size     !== "all") list = list.filter(c => String(c.size)     === String(state.size));
  if (state.grade    !== "all") list = list.filter(c => String(c.grade)    === String(state.grade));

  const pdMin = Number.isFinite(+state.pdMin) ? +state.pdMin : 0;
  const pdMax = Number.isFinite(+state.pdMax) ? +state.pdMax : 1000;
  list = list.filter(c => {
    const v = Number(c.pd) || 0;
    return v >= pdMin && v <= pdMax;
  });

  
  if (state.query) {
    const q = state.query.toLowerCase();
    list = list.filter(c => String(c.name||"").toLowerCase().includes(q) || String(c.company_code||"").toLowerCase().includes(q));
  }

  // 3) 대표 기업(lead): 선택 유지 → 없으면 필터 결과 첫 항목
  const selected = list.find(c => String(c.idx) === String(state.companyId));
  const lead = selected || list[0] || (window.companies || window.SERVER_COMPANIES || [])[0];
  if (lead) state.companyId = lead.idx;

  // 4) 화면 렌더 (기존 함수들 호출)
  if (list.length > 0) {
    renderKPIs([lead]);
    renderIndustryCreditScore([lead, ...list]);
    renderSolvency(lead);
    renderPeers(list);
    renderTable(list);                // ← 표에서 기업 클릭 시 반드시 state.companyId = e.idx; applyFilters(true);
    renderProfit([lead]);
    renderProfitIndustry([lead, ...list]);
    renderCompanyProfile(lead);
    renderPDCompare([lead, ...list]);
    renderCashFlowTrend(lead);
    renderDrivers(lead);
    if (document.getElementById('sROE') || document.getElementById('simNow')) {
      const yr = (state.year && state.year !== 'all')
        ? state.year
        : (lead.year || new Date().getFullYear());
      bindSimulation(lead.idx, yr);   // ✅ 필터 있을 때는 여기서 호출
    }
    renderMacro(36);
    renderActivity(lead);
  } else {
    renderTable([]);
  }


  
  // 5) 기업/KPI + 평균 차트: 연도는 API에만 전달
  if (lead && state.year !== "all") {
    const cid = lead.idx;
    const yr  = String(state.year);

    // 기업 KPI
    fetch(`/api/credit-score?year=${encodeURIComponent(yr)}&company_id=${encodeURIComponent(cid)}`)
      .then(r => r.json())
      .then(d => {
        document.getElementById("kpiGrade").textContent = d.grade ?? "-";
        document.getElementById("kpiGradeDelta").textContent = d.delta ?? "-";
        document.getElementById("kpiScore").textContent = d.score ?? 0;
      })
      .catch(console.error);

    // ✅ 기업 기본정보(연도별) 갱신 추가
    fetch(`/api/company-info?year=${encodeURIComponent(yr)}&company_id=${encodeURIComponent(cid)}`)
      .then(r => r.json())
      .then(info => {
        document.getElementById("selectedCompanyName").textContent = info.name ?? "-";
        document.getElementById("selectedCompanyCode").textContent = "기업코드: " + (info.code ?? "-");
        document.getElementById("companyFounded").textContent     = info.established_date ?? "-";
        document.getElementById("companyCEO").textContent         = info.ceo ?? "-";
        document.getElementById("companySize").textContent        = info.size ?? "-";
        document.getElementById("companyIndustry").textContent    = info.industry ?? "-";
      })
      .catch(console.error);

    // 평균 차트 (기업 vs 업종/규모 평균)
    fetch(`/api/credit-score-avg?year=${encodeURIComponent(yr)}&company_id=${encodeURIComponent(cid)}`)
      .then(r => r.json())
      .then(updateCreditCompareChart)
      .catch(console.error);

    // ✅ PD (부실확률)
    fetch(`/api/pd?year=${encodeURIComponent(yr)}&company_id=${encodeURIComponent(cid)}`)
    .then(r => r.json())
    .then(d => {
      const pdVal = Number(d.pd) || 0;
      const indVal = Number(d.industry_avg) || 0;

      document.getElementById("kpiPD").textContent = pdVal.toFixed(1) + "%";
      document.getElementById("kpiPDNote").textContent =
        pdVal >= 10 ? "상위 10% 위험군" : "상위 10% 위험군 아님";

      const delta = pdVal - indVal;
      const dEl = document.getElementById("kpiPDDelta");
      if (dEl) {
        dEl.textContent = `${delta >= 0 ? '+' : ''}${delta.toFixed(1)}pp 업종대비`;
        dEl.className = 'delta ' + (delta <= 0 ? 'good' : 'bad');
      }
    })

    fetch(`/api/pd-avg?year=${encodeURIComponent(yr)}&company_id=${encodeURIComponent(cid)}`)
    .then(r => r.json())
    .then(d => updatePDCompareChart(d, lead))
    
    // 동종업계 비교 (연도별)
    fetch(`/api/peers?year=${encodeURIComponent(yr)}&company_id=${encodeURIComponent(cid)}`)
    .then(r => r.json())
    .then(d => {
      if (d && d.peers) {
        updatePeersChart(d.peers, lead);
        window.currentPeers = d.peers; // 검색용 캐시
      }
    })
    

      // ✅ 수익성·성장성 (연도별)
    fetch(`/api/profit-growth?year=${encodeURIComponent(yr)}&company_id=${encodeURIComponent(cid)}`)
      .then(r => r.json())
      .then(d => updateProfitGrowthChart(d, lead))


      // ✅ 수익성·성장성 (업종평균, 연도별)
    fetch(`/api/profit-growth-industry?year=${encodeURIComponent(yr)}&company_id=${encodeURIComponent(cid)}`)
      .then(r => r.json())
      .then(d => updateProfitGrowthIndustryChart(d))

      // ✅ 안정성 지표
    fetch(`/api/solvency?year=${encodeURIComponent(yr)}&company_id=${encodeURIComponent(cid)}`)
      .then(r => r.json())
      .then(d => updateSolvencyChart(d))
    
      // ✅ 활동성 지표(회전율) – 연도별
    fetch(`/api/activity?year=${encodeURIComponent(yr)}&company_id=${encodeURIComponent(cid)}`)
      .then(r => r.json())
      .then(updateActivityChart)
    

    fetch(`/api/companies?year=${encodeURIComponent(yr)}`)
    .then(r => r.json())
    .then(data => {
      // 전역 데이터 교체
      window.companies = Array.isArray(data) ? data : [];

      // 기존 로컬 필터들 (업종/규모/등급/PD 범위) 다시 적용
      let list = window.companies.slice();
      if (state.industry !== "all") list = list.filter(c => String(c.industry) === String(state.industry));
      if (state.size     !== "all") list = list.filter(c => String(c.size)     === String(state.size));
      if (state.grade    !== "all") list = list.filter(c => String(c.grade)    === String(state.grade));
      list = list.filter(c => {
        const pd = Number(c.pd) || 0;
        return pd >= state.pdMin && pd <= state.pdMax;
      });

      renderTable(list);

      const newLead =
     list.find(c => String(c.idx) === String(state.companyId)) || list[0];
      if (newLead && (document.getElementById('sROE') || document.getElementById('simNow'))) {
        bindSimulation(newLead.idx, yr);
      }
    })

    .catch(console.error);
    }

  return list;
}



  // EVENT BINDINGS

  if (document.getElementById('resetFilters')) document.getElementById('resetFilters').onclick =()=>{
    (document.getElementById('fIndustry')||{}).value='all';
    (document.getElementById('fSize')||{}).value='all';
    (document.getElementById('fGrade')||{}).value='all';
    (document.getElementById('fPDMin')||{}).value=0; (document.getElementById('fPDMax')||{}).value=20;
    (document.getElementById('fQuery')||{}).value='';
    (document.getElementById('fRange')||{}).value='36m';
    (document.getElementById('fYear')||{}).value='all'; state.year='all';
    state.industry='all'; state.size='all'; state.grade='all'; state.pdMin=0; state.pdMax=20; state.query=''; state.range='36m';
    applyFilters();
  };

  document.querySelectorAll('[data-range]').forEach(btn => btn.onclick = () => { state.range = btn.dataset.range; const filtered = applyFilters(); renderProfit(filtered); });
  document.querySelectorAll('[data-m]').forEach(btn=> btn.onclick=()=> renderMacro(+btn.dataset.m));

  
  // Search (topbar + peers)
  {
    const _btn = document.getElementById('searchBtn');
    if (_btn) {
      _btn.onclick = () => {
        const _qin = document.getElementById('q');
        const q = _qin ? _qin.value.trim().toLowerCase() : '';
        if (!q) return;

        // state.query 에 반영 → applyFilters()와 동일한 로직으로 필터링
        state.query = q;
        applyFilters();
      };
    }

    // 동종업계 비교 - 검색 버튼 이벤트
// 동종업계 비교 - 검색 버튼 이벤트 (교체)
const peerBtn = document.getElementById("peerSearch");
if (peerBtn) {
  peerBtn.onclick = () => {
    const qEl = document.getElementById("peerQuery");
    const q = qEl ? qEl.value.trim().toLowerCase() : "";

    // ✅ 베이스: /api/peers 결과 (실데이터)
    const basePeers = Array.isArray(window.currentPeers) ? window.currentPeers : [];

    // ✅ 검색 풀: /api/companies?year=... 로 로딩된 실데이터
    const pool = Array.isArray(window.companies) ? window.companies : [];

    // 검색 기업 찾기(업종 무시, 이름 부분일치)
    const searchCompany = q ? pool.find(x => (x.name || '').toLowerCase().includes(q)) : null;

    // ✅ 산점도 갱신 (검색 기업은 초록점으로 추가)
    renderPeers(basePeers, searchCompany);
  };

  // 엔터키도 동작
  const qEl = document.getElementById("peerQuery");
  if (qEl) {
    qEl.addEventListener("keypress", (e) => {
      if (e.key === "Enter") peerBtn.click();
    });
  }
}





  }

  // Sorting table
  function sortBy(key){
    const dir = (sortKey===key && sortDir==='asc')? 'desc':'asc'; sortKey=key; sortDir=dir; const mul=dir==='asc'?1:-1;
    const rows=[...document.querySelectorAll('#entBody tr')];
    rows.sort((A,B)=>{
      const get=(tr,k)=>{
        const map={pd:4, score:6, debt:7}; const cell=tr.children[map[k]]; const txt=cell.textContent.replace(/[^\d.-]/g,''); return parseFloat(txt)||0; };
      return (get(A,key)-get(B,key))*mul;
    });
    const tbody=document.getElementById('entBody'); if (!tbody) return; tbody.innerHTML=''; rows.forEach(r=> tbody.appendChild(r));
  }
  if (document.getElementById('sortPD')) document.getElementById('sortPD').onclick =()=> sortBy('pd');
  if (document.getElementById('sortScore')) document.getElementById('sortScore').onclick =()=> sortBy('score');
  if (document.getElementById('sortDebt')) document.getElementById('sortDebt').onclick =()=> sortBy('debt');

  // Export CSV
  if (document.getElementById('exportCsv')) document.getElementById('exportCsv').onclick =()=>{
    const headers=['idx','name','industry','size','pd','grade','score','debt','roe','assets'];
    const rows=companies.map(e=> [e.idx,e.name,e.industry,e.size,e.pd,e.grade,e.score,e.debt,e.roe,e.assets].join(','));
    const blob=new Blob([[headers.join(','),...rows].join('\n')], {type:'text/csv'}); const url=URL.createObjectURL(blob); const a=Object.assign(document.createElement('a'),{href:url,download:'companies.csv'}); a.click(); URL.revokeObjectURL(url);
  };

  // INIT
  function onResize(){
  const filtered = applyFilters();
  spark('sparkIndustry', Array.from({length:24}, ()=> computeIndustryAvg(filtered)+rfloat(-1,1)), '#2563eb');

  renderProfit(filtered);                      // ✅ filtered로 교체
  renderActivity(filtered[0] || companies[0]); // ✅ firm 넘겨주기
  renderCashFlow();
  renderRoadmap();
  renderPeers(filtered);
  renderMacro(36);
}

  window.addEventListener('resize', onResize);

  // bootstrap
  // renderProfit(state.range); bindSimulation(); applyFilters(); renderActivity(); renderCashFlow(); renderDrivers(companies[0]); renderRoadmap(); renderPeers(companies); renderMacro(36);
  // Topbar검색시 페이지 이동 관련?
  document.addEventListener("DOMContentLoaded", async () =>  {
    try {
      const filtered = applyFilters();                 // 먼저 리스트/대표기업 확정
      const firm = filtered[0] || companies?.[0];
      renderProfit?.(filtered);

      if (document.getElementById('chartRadar'))      renderActivity(firm);
      if (document.getElementById('chartCashflow'))   renderCashFlowTrend(firm);
      if (document.getElementById('chartDrivers'))    renderDrivers(firm);
      if (companies && companies.length) {
        renderRoadmap?.();
        renderPeers?.(filtered);                      // ← peers도 필터 반영
      }
      if (document.getElementById('mGDP')) renderMacro?.(36);
      if (document.getElementById('sROE') && firm) {
            
          }
    } catch (e) {
      console.warn('[bootstrap skipped]', e);
    }
  });


  // 사이드바 로드
  fetch("/sidebar")
    .then(res => res.text())
    .then(html => {
      const _sEl=document.getElementById("sidebar"); if (_sEl) _sEl.innerHTML = html;

      // 여기서 closeBtn을 찾아야 함
      const sidebar = document.getElementById("sidebar");
      const closeBtn = document.getElementById("closeSidebar");
      if (closeBtn) {
        closeBtn.addEventListener("click", () => {
          sidebar.classList.remove("open");
        });
      }
    });

  // 메뉴 버튼은 기존처럼 바로 연결 가능
  document.addEventListener("DOMContentLoaded", () => {
    const sidebar = document.getElementById("sidebar");
    const openBtn = document.getElementById("openSidebar");
    if (openBtn && sidebar) {
      openBtn.addEventListener("click", () => {
        sidebar.classList.toggle("open");
      });
    }
  });



  
  // 기업명 출력
  // 기업 정보 렌더링 (main.py에서 내려준 필드명 사용)
function renderCompanyProfile(firm) {
  if (!firm) return;

  const setText = (id, value) => {
    const el = document.getElementById(id);
    if (el) el.textContent = value ?? "-";
  };

  setText("selectedCompanyName", firm.name);
  setText("selectedCompanyCode", `기업코드: ${firm.company_code || "-"}`);
  setText("companyFounded", firm.established_date || "-");
  setText("companyCEO", firm.ceo || "-");
  setText("companySize", firm.size || "-");
  setText("companyIndustry", firm.industry || "-");
}


// 첫 번째 기업 자동 표시
document.addEventListener("DOMContentLoaded", () => {
  if (window.SERVER_COMPANIES && window.SERVER_COMPANIES.length) {
    renderCompanyProfile(window.SERVER_COMPANIES[0]);
  }
});


  function renderPDCompare(filtered){
  const company = (filtered && filtered[0]) || companies[0];
  if (!company) return;

  // 업종 평균
  const peersIndustry = companies.filter(c => c.industry === company.industry);
  const industryAvgPD = peersIndustry.reduce((a,b)=> a + (b.pd||0), 0) / (peersIndustry.length||1);

  // 규모 평균 (Large / Mid / SME)
  const peersSize = companies.filter(c => c.size === company.size);
  const sizeAvgPD = peersSize.reduce((a,b)=> a + (b.pd||0), 0) / (peersSize.length||1);

  // 라벨 & 값
  const labels = [
    company.name,
    company.industry + " 평균",
    company.size + " 평균"
  ];
  const values = [
    company.pd,
    industryAvgPD,
    sizeAvgPD
  ];

  // 색상 (기업: 파랑, 업종: 회색, 규모: 초록)
  const colors = ['#3b82f6', '#9ca3af', '#10b981'];

  hbar('chartPDCompare', labels, values, colors);
}



function vbar(el, labels, values, industryValues){
  const c = document.getElementById(el);
  if (!c) return;
  const { w, h, ctx } = sizeCanvas(c, 220);

  const padL = 30, padR = 30, padTop = 16, padBottom = 28;
  const groupGap = 36;  // 그룹(지표) 간격
  const barGap   = 10;  // 그룹 내부 막대 간격
  const N = labels.length;

  const innerW = Math.max(1, w - padL - padR);
  const usableH = Math.max(1, h - padTop - padBottom);
  const maxVal = Math.max(...values, ...industryValues, 1);

  // 막대 폭 계산
  let barW = (innerW - (N - 1) * groupGap - N * barGap) / (N * 2);
  const MIN_BAR_W = 8;
  if (barW < MIN_BAR_W) barW = MIN_BAR_W;

  const contentW = N * (2 * barW + barGap) + (N - 1) * groupGap;
  const offsetX = padL + Math.max(0, (innerW - contentW) / 2);

  ctx.clearRect(0, 0, w, h);
  ctx.font = '12px system-ui';
  ctx.textBaseline = 'bottom';

  for (let i = 0; i < N; i++) {
    const v1 = Number(values[i]) || 0;         // 기업 값
    const v2 = Number(industryValues[i]) || 0; // 업종 평균 값

    const groupX   = offsetX + i * (2 * barW + barGap + groupGap);
    const bar1X    = groupX;
    const bar2X    = groupX + barW + barGap;
    const groupCtr = groupX + (2 * barW + barGap) / 2;

    const y1 = padTop + usableH * (1 - v1 / maxVal);
    const y2 = padTop + usableH * (1 - v2 / maxVal);

    // 기업 막대 색상: 평균보다 높으면 파랑, 낮으면 빨강
    // ctx.fillStyle = v1 >= v2 ? '#2563eb' : '#ef4444';
    ctx.fillStyle = '#10b981';  // 기업 막대: 항상 파랑으로 고정
    ctx.fillRect(bar1X, y1, barW, padTop + usableH - y1);

    // 업종 평균 막대 (회색)
    ctx.fillStyle = '#9ca3af';
    ctx.fillRect(bar2X, y2, barW, padTop + usableH - y2);

    // 값 라벨
    ctx.fillStyle = 'var(--text)';
    ctx.textAlign = 'center';
    ctx.fillText(Math.round(v1) + '%', bar1X + barW / 2, y1 - 6);
    ctx.fillText(Math.round(v2) + '%', bar2X + barW / 2, y2 - 6);

    // 축 라벨 (지표명)
    ctx.fillStyle = 'var(--muted)';
    ctx.textAlign = 'center';
    ctx.fillText(labels[i], groupCtr, h - 6);
  }
}


// 멀티 라인차트: 축/눈금/그리드/범례/값 라벨 포함
function cfLineChart(el, labels, series, colors, opts = {}){
  const c = document.getElementById(el);
  if (!c) return;
  const { w, h, ctx } = sizeCanvas(c, 220);

  const flat = series.flat().map(v => Number(v)).filter(v => isFinite(v));
  ctx.clearRect(0,0,w,h);
  if (flat.length === 0) {
    ctx.font = '14px system-ui';
    ctx.fillStyle = 'var(--muted)';
    ctx.textAlign = 'center';
    ctx.fillText('데이터 없음', w/2, h/2);
    return;
  }

  // 옵션
  const yUnit = opts.yUnit ?? '%';
  const yTicksCount = opts.yTicks ?? 5;
  const padL = opts.padL ?? 56, padR = opts.padR ?? 16, padT = opts.padT ?? 22, padB = opts.padB ?? 30;

  // 범위 계산 + 마진
  let min = Math.min(...flat), max = Math.max(...flat);
  if (min === max) { const pad = (Math.abs(min) || 1) * 0.1; min -= pad; max += pad; }
  const span = max - min; min -= span * 0.1; max += span * 0.1;

  // 예쁜 눈금(step) 계산
  const rawStep = (max - min) / yTicksCount;
  const pow10 = Math.pow(10, Math.floor(Math.log10(Math.abs(rawStep) || 1)));
  const candidates = [1, 2, 2.5, 5, 10].map(m => m * pow10);
  const step = candidates.find(s => rawStep <= s) || candidates[candidates.length - 1];

  const tickStart = Math.ceil(min / step) * step;
  const tickEnd   = Math.floor(max / step) * step;
  const ticks = [];
  for (let t = tickStart; t <= tickEnd + 1e-9; t += step) ticks.push(t);

  const innerW = w - padL - padR;
  const innerH = h - padT - padB;
  const xStep = labels.length > 1 ? innerW / (labels.length - 1) : 0;
  const yFor = v => padT + (1 - (v - min) / (max - min)) * innerH;

  // Y 그리드 + Y 눈금 라벨
  ctx.strokeStyle = 'rgba(15,23,42,.12)';
  ctx.fillStyle = 'var(--muted)';
  ctx.textAlign = 'right';
  ctx.textBaseline = 'middle';
  ctx.font = '12px system-ui';

  ticks.forEach(t => {
    const y = yFor(t);
    ctx.beginPath(); ctx.moveTo(padL, y + 0.5); ctx.lineTo(w - padR, y + 0.5); ctx.stroke();
    const needs1 = Math.abs(step) < 1;
    const lab = yUnit === '%' ? (needs1 ? t.toFixed(1) : Math.round(t)).toString() + '%' : (needs1 ? t.toFixed(1) : Math.round(t)).toString();
    ctx.fillText(lab, padL - 20, y);
  });

  // 0 기준선
  if (min < 0 && max > 0) {
    const y0 = yFor(0);
    ctx.save();
    ctx.setLineDash([4,4]);
    ctx.strokeStyle = 'rgba(0,0,0,.35)';
    ctx.beginPath(); ctx.moveTo(padL, y0 + 0.5); ctx.lineTo(w - padR, y0 + 0.5); ctx.stroke();
    ctx.restore();
  }

  // X 라벨(연도)
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';
  ctx.fillStyle = 'var(--muted)';
  labels.forEach((lb, i) => {
    const x = padL + i * xStep;
    ctx.fillText(lb, x, h - padB + 6);
  });

  // 라인 + 포인트 + 마지막 값 라벨
  series.forEach((arr, si) => {
  const color = colors[si % colors.length];
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.beginPath();
  arr.forEach((v, i) => {
    const x = padL + i * xStep;
    const y = yFor(v);
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // 포인트
  if (opts.showPoints !== false) {
    ctx.fillStyle = color;
    arr.forEach((v, i) => {
      const x = padL + i * xStep;
      const y = yFor(v);
      ctx.beginPath(); ctx.arc(x, y, 2.5, 0, Math.PI * 2); ctx.fill();

      // ✅ 각 포인트 위에 값 표시
      ctx.fillStyle = 'var(--text)';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'bottom';
      const valStr = yUnit === '%' ? (Number(v).toFixed(1) + '%') : Number(v).toFixed(1);
      ctx.fillText(valStr, x, y - 4);
    });
  }
});

  // 범례: div가 있으면 div에, 없으면 캔버스 안에
  const labelsLegend = opts.seriesLabels || series.map((_, i) => `Series ${i+1}`);
  if (opts.legendElId) {
    const el = document.getElementById(opts.legendElId);
    if (el) {
      el.innerHTML = labelsLegend.map((lb, i) =>
        `<span style="display:inline-block;width:12px;height:12px;background:${colors[i%colors.length]};margin-right:4px;border-radius:2px"></span>${lb}`
      ).join('&nbsp;&nbsp;');
    }
  }

  // (선택) Y축 제목
  if (opts.yLabel) {
    ctx.save();
    ctx.translate(12, padT + innerH / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillStyle = 'var(--muted)';
    ctx.fillText(opts.yLabel, 0, 0);
    ctx.restore();
  }
}



function renderCashFlowTrend(firm){
  const canvas = document.getElementById('chartCashflow');
  if (!canvas) return;

  // ✅ firm이 얕으면 서버 원본으로 승격
  if (!firm?.cashflow?.years?.length) {
    const byIdx = (window.SERVER_COMPANIES || [])
      .find(c => String(c.idx) === String(firm?.idx ?? window.state?.companyId));
    firm = byIdx || firm;
  }

  const ctx = canvas.getContext('2d');
  const w = canvas.width, h = canvas.height;

  if (!firm?.cashflow?.years?.length){   // 그래도 없으면 그때만 메시지
    ctx.clearRect(0,0,w,h);
    ctx.font = '14px system-ui';
    ctx.fillStyle = 'var(--muted)';
    ctx.textAlign = 'center';
    ctx.fillText("현금흐름 데이터 없음", w/2, h/2);
    return;
  }

  const years  = firm.cashflow.years;
  const series = [firm.cashflow.operating, firm.cashflow.investing, firm.cashflow.financing];
  const colors = ['#2563eb', '#10b981', '#f59e0b'];
  cfLineChart('chartCashflow', years, series, colors);


  // ✅ 범례
  const legend = document.getElementById('chartCashflowLegend');
  if (legend) {
    const labels = ["OCF / Assets", "OCF / Debt", "OCF / Sales"];
    legend.innerHTML = labels.map((lb, i) => `
      <span style="display:inline-block;width:12px;height:12px;background:${colors[i]};margin-right:4px"></span>
      ${lb}
    `).join("&nbsp;&nbsp;");
  }
}


// [TOP OF FILE] Topbar 검색 → 항상 firm.html로 이동 (ID 중복 방지 위해 topbar 범위로 한정)
document.addEventListener('DOMContentLoaded', () => {
  const btn   = document.querySelector('.topbar .search #searchBtn');
  const input = document.querySelector('.topbar .search #q');
  if (!btn || !input) return;
  const isFirm = location.pathname.includes('/firm');

  const go = () => {
    const q = input.value.trim();
    if (!q) return;
    if (!isFirm) {
      // 목록 화면 등에서는 상세 페이지로 이동
      window.location.href = `/firm?q=${encodeURIComponent(q)}`;
    } else {
      // firm 화면에서는 필터로 동작
      state.query = q.toLowerCase();
      applyFilters(true);
    }
  };
  btn.addEventListener('click', go);
  input.addEventListener('keydown', e => { if (e.key === 'Enter') go(); });
});






document.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(location.search);
  const q = params.get("q");
  if (q) {
    state.query = q.toLowerCase();
    document.getElementById("q").value = q;
  }
  applyFilters(true);
});








// === 교체: DOMContentLoaded 블록 ===
document.addEventListener("DOMContentLoaded", () => {
  // 1) 데이터 소스 보정 (companies가 비어있으면 SERVER_COMPANIES 사용)
  window.companies = Array.isArray(window.companies) && window.companies.length
    ? window.companies
    : (window.SERVER_COMPANIES || []);

  // 2) 기본 연도 2023 셋팅 (요구사항)
  const yearSelect = document.getElementById("fYear");
  if (yearSelect) {
    state.year = "2023";
    yearSelect.value = "2023";

    // 연도 변경 시: 값만 저장 (즉시 적용 X)
    yearSelect.addEventListener("change", (e) => {
      state.year = e.target.value || "all";
      if (!state.companyId) {
      const base = (window.companies || window.SERVER_COMPANIES || [])[0];
      if (base) state.companyId = base.idx;
      }
    });
  }

  // 3) 적용 버튼: 이때만 실제 필터 적용
  const btnApply = document.getElementById("applyFilters");
  if (btnApply) {
    btnApply.addEventListener("click", () => applyFilters(true)); // force=true
  }

  // 4) 리셋 버튼
  const btnReset = document.getElementById("resetFilters");
  if (btnReset) {
    btnReset.addEventListener("click", () => {
      state = { industry:"all", size:"all", grade:"all", pdMin:0, pdMax:20, query:"", range:"36m", year:"all", companyId: state.companyId || null };
      const ids = ["fIndustry","fSize","fGrade","fPDMin","fPDMax","fYear","fQuery","fRange"];
      ids.forEach(id => { const el = document.getElementById(id); if (el) el.value = (id==="fYear"?"all":"all"); });
      applyFilters(true);
    });
  }

  // 5) 첫 화면은 2023으로 즉시 렌더
  applyFilters(true);
});



// 연도=all 또는 초기 화면에서 리스트로 평균 차트 그리기
function updateCreditCompareChart(data) { 
  // 1) 현재 선택된 기업 찾기 (없으면 첫 기업)
  const lead =
    (companies || []).find(c => String(c.idx) === String(state.companyId)) ||
    (companies && companies[0]);

  // 2) 라벨 치환용 텍스트 준비 (lead 없으면 원문 유지)
  const industryLabel = lead ? `${lead.industry} 평균` : '업종 평균';
  const sizeLabel     = lead ? `${lead.size} 평균`     : '규모 평균';



  // 4) API에서 넘어온 고정 라벨을 동적으로 치환
  const labels = data.map(d => {
    if (d.label === '업종 평균') return industryLabel;
    if (d.label === '규모 평균') return sizeLabel;
    return d.label; // '기업' 등은 그대로
  });

  // 5) 값/색상
  const scores = data.map(d => Number(d.value) || 0);
  const colors = ["#2563eb", "#9ca3af", "#10b981", "#f59e0b"]; // ✅ 전체 평균 색상 추가

  hbar("chartCreditCompare", labels, scores, colors, "pt");
}




function updatePDCompareChart(data, company) {
  // 동적으로 라벨 치환 (기업 업종/규모 이름 반영)
  const industryLabel = company ? `${company.industry} 평균` : '업종 평균';
  const sizeLabel     = company ? `${company.size} 평균`     : '규모 평균';

  // ✅ 전체 평균 데이터 추가 (API 응답에 없다면 여기서 직접 push 필요)
  const overallAvg = computeOverallPDAvg(); 
  data.push({ label: "전체 평균", value: overallAvg });

  // 라벨 변환
  const labels = data.map(d => {
    if (d.label === '업종 평균') return industryLabel;
    if (d.label === '규모 평균') return sizeLabel;
    if (d.label === '전체 평균') return '전체 평균';  // ✅ 추가
    return d.label;
  });

  // 값/색상
  const values = data.map(d => Number(d.value) || 0);
  const colors = ["#3b82f6", "#9ca3af", "#10b981", "#f59e0b"]; // ✅ 색상 하나 더

  hbar("chartPDCompare", labels, values, colors, "%");
}

// ✅ 전체 평균 계산 함수 (window.companies 활용)
function computeOverallPDAvg() {
  if (!window.companies) return 0;
  const arr = window.companies.map(c => Number(c.pd) || 0);  // ← PD 필드 확인 필요
  return arr.reduce((a, b) => a + b, 0) / (arr.length || 1);
}



// 동종업계 비교 (연도별)
function updatePeersChart(peers, company) {
  if (!peers || peers.length === 0) return;

  const pts = peers.map(p => ({
    x: p.debt_ratio,
    y: p.roe,
    r: 0,
    label: p.name,
    color: (company && p.idx === company.idx) ? 'rgba(239,68,68,.9)' : 'rgba(99,102,241,.60)'
  }));

  bubble("chartPeers", pts);
}


//연도별 기업 수익성·성장성

function updateProfitGrowthChart(data, company) {
  const labels = ['매출성장률','영업이익성장률','ROE','ROA','ROIC'];
  const values = [
    Number(data.sales_growth) || 0,
    Number(data.profit_growth) || 0,
    Number(data.roe) || 0,
    Number(data.roa) || 0,
    Number(data.roic) || 0
  ];
  const colors = ['#2563eb','#60a5fa','#10b981','#22c55e','#0ea5e9'];

  hbarSigned("chartProfitGrowth", labels, values, colors);
  const summary = document.getElementById("profitSummary");
  if (summary) {
    summary.innerHTML = `<b>${company?.name ?? ''}</b>의 주요 수익성 · 성장성 지표`;
  }
}


function updateProfitGrowthIndustryChart(data) {
  const labels = ['매출성장률','영업이익성장률','ROE','ROA','ROIC'];
  const values = [
    Number(data.sales_growth) || 0,
    Number(data.profit_growth) || 0,
    Number(data.roe) || 0,
    Number(data.roa) || 0,
    Number(data.roic) || 0
  ];
  const colors = ['#2563eb','#60a5fa','#10b981','#22c55e','#0ea5e9'];

  hbarSigned("chartProfitGrowthIndustry", labels, values, colors);
  const summary = document.getElementById("profitSummaryIndustry");
  if (summary) {
    summary.innerHTML = `<b>${data.industry ?? '-'}</b>의 평균 수익성 · 성장성 지표`;
  }
}


// ✅ 연도별 안정성 지표 업데이트 (기업 vs 업종 평균)
function updateSolvencyChart(data) {
  const labels = ["부채비율", "유동비율", "당좌비율"];

  // 기업 값
  const companyValues = [
    Number(data.company?.debt_ratio)   || 0,
    Number(data.company?.current_ratio)|| 0,
    Number(data.company?.quick_ratio)  || 0
  ];

  // 업종 평균 값
  const industryValues = [
    Number(data.industry?.debt_ratio)   || 0,
    Number(data.industry?.current_ratio)|| 0,
    Number(data.industry?.quick_ratio)  || 0
  ];

  // 우리 캔버스 유틸로 그리기 (Chart.js 아님)
  vbar("chartSolvency", labels, companyValues, industryValues);

  // (선택) 요약 텍스트 갱신
  const sum = document.getElementById("solvencySummary");
  if (sum) {
    const iname = data.industry_name || "업종 평균";
    sum.innerHTML = `<b>${data.company_name ?? "기업"}</b> vs <b>${iname}</b> 안정성 지표`;
  }
}



// ✅ 연도별 활동성 지표(회전율) 업데이트
function updateActivityChart(data) {
  if (!data || !data.company || !data.industry) return;

  const labels = ["재고회전", "채권회전", "총자산회전", "비유동회전"];

  // 원시값
  const rawCompany = [
    Number(data.company.inventory_turnover) || 0,
    Number(data.company.receivables_turnover) || 0,
    Number(data.company.asset_turnover) || 0,
    Number(data.company.fixed_asset_turnover) || 0
  ];
  const rawIndustry = [
    Number(data.industry.inventory_turnover) || 0,
    Number(data.industry.receivables_turnover) || 0,
    Number(data.industry.asset_turnover) || 0,
    Number(data.industry.fixed_asset_turnover) || 0
  ];

  // 레이더 헬퍼는 로그 스케일을 기대(프로젝트 기존 스타일 유지)
  const logCompany = rawCompany.map(v => Math.log(1 + v));
  const logIndustry = rawIndustry.map(v => Math.log(1 + v));
  const maxVal = Math.max(...logCompany, ...logIndustry, 1);

  // 커스텀 radar(el, labels, logCompany, maxVal, rawCompany, logIndustry, rawIndustry)
  radar("chartRadar", labels, logCompany, maxVal, rawCompany, logIndustry, rawIndustry);

  // (선택) 하단 요약/범례 텍스트 업데이트가 필요하면 여기서 갱신
  // 예) document.getElementById("activitySummary")?.innerHTML = `<b>${data.company.name ?? '-'}</b> vs <b>${data.industry.name ?? '업계 평균'}</b>`;
}


function renderCompanyList(data) {
  const tbody = document.getElementById("entBody");
  if (!tbody) return;
  tbody.innerHTML = "";

  data.forEach((c, i) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${i + 1}</td>
      <td>${c.name}</td>
      <td>${c.industry}</td>
      <td>${c.size}</td>
      <td>${(c.pd ?? 0).toFixed(1)}</td>
      <td>${c.grade ?? "-"}</td>
      <td>${(c.score ?? 0).toFixed(1)}</td>
      <td>${(c.debt_ratio ?? 0).toFixed(1)}</td>
      <td>${(c.roe ?? 0).toFixed(1)}</td>
      <td>${(c.assets ?? 0).toLocaleString()}</td>
    `;
    tbody.appendChild(tr);
  });
}


(function(){
  const btn = document.getElementById('toTopBtn');
  const SHOW_AFTER = 300; // px 이상 스크롤 시 표시

  const onScroll = () => {
    if (window.scrollY > SHOW_AFTER) btn.classList.add('show');
    else btn.classList.remove('show');
  };

  // 초기 상태 & 스크롤 감지
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  // 클릭 시 스무스 스크롤
  btn.addEventListener('click', () => {
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    window.scrollTo({ top: 0, behavior: prefersReduced ? 'auto' : 'smooth' });
  });
})();




document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("genReportBtn");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    const list = applyFilters(true);
    const firm =
      list.find(c => String(c.idx) === String(state.companyId)) || list[0];
    if (!firm) {
      alert("선택된 기업이 없습니다.");
      return;
    }

    const reportBox = document.getElementById("reportBox");
    reportBox.innerText = "⏳ 리포트 생성 중입니다. 잠시만 기다려주세요...";

    try {
      const res = await fetch("/generate-report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ firm })
      });

      if (!res.ok) {
        const msg = await res.text();
        console.error("Report API failed", res.status, msg);
        reportBox.innerText = `⚠️ 리포트 생성 실패 (${res.status})\n${msg}`;
        return;
      }

      const data = await res.json();
      console.log("Report API response:", data);

      // ✅ 로컬 스토리지에 리포트 저장
      localStorage.setItem("latestReport", data.report);

      // ✅ 완료 팝업 표시
      alert("리포트 생성이 완료되었습니다.");

      // ✅ 페이지 내 문구 변경
      reportBox.innerText = "✅ 리포트 생성이 완료되었습니다. 리포트를 확인하세요.";

      // ✅ '리포트 확인하기' 버튼 생성
      if (!document.getElementById("viewReportBtn")) {
        const viewBtn = document.createElement("button");
        viewBtn.id = "viewReportBtn";
        viewBtn.innerText = "리포트 확인하기";
        viewBtn.style.marginTop = "10px";
        viewBtn.onclick = () => {
          window.open(
            "/report",
            "reportWindow",
            "width=800,height=600,scrollbars=yes,resizable=yes"
          );
        };
        btn.insertAdjacentElement("afterend", viewBtn);
      }

    } catch (err) {
      console.error(err);
      reportBox.innerText = "⚠️ 리포트 생성 중 오류가 발생했습니다.";
    }
  });
});

