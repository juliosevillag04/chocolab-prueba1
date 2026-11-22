/* Choco Lab · Jacobi y Gauss-Seidel: interfaz educativa, matemática en Python. */
'use strict';
(() => {
  const $=id=>document.getElementById(id);
  const h=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const supermap={'-':'⁻','+':'⁺','0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹'};
  const subsmap={'0':'₀','1':'₁','2':'₂','3':'₃','4':'₄','5':'₅','6':'₆','7':'₇','8':'₈','9':'₉'};
  const su=n=>String(n).split('').map(c=>supermap[c]||c).join('');
  const sb=n=>String(n).split('').map(c=>subsmap[c]||c).join('');
  // Solo la PRESENTACIÓN se redondea: el motor y el CSV conservan
  // los números completos. Máximo seis cifras decimales en formato habitual.
  // Magnitudes pequeñas (especialmente residuos) se muestran en notación
  // científica para no ocultar información ni convertir ceros pequeños en 0.
  const fmt=value=>{
    if(value===null||value===undefined)return '—';
    const x=Number(value);
    if(!Number.isFinite(x))return '—';
    if(x===0)return '0';
    const habitual=x.toFixed(6).replace(/\.?0+$/,'');
    // Ej.: ε = 0.0001 se conserva legible, pero un residuo como
    // 0.000066592 necesita más de seis decimales: 6.6592 × 10⁻⁵.
    if(Math.abs(x)<0.01 && Number(habitual)!==x){
      const [mantisa,exp]=x.toExponential(5).split('e');
      return mantisa.replace(/\.?0+$/,'')+' × 10'+su(Number(exp));
    }
    return habitual;
  };
  const val=(value)=>typeof value==='number'?fmt(value):h(value);
  const PALETTE=['#2366a6','#db7425','#258359','#b74674','#7157b8','#008eac','#b17924','#ba4550','#4169bd','#678a27','#aa4c9a','#007a8c','#ba8033','#68728a','#bb6556'];
  const DASH=['solid','solid','solid','solid','dash','dot','dashdot','longdash','solid','dash','dot','dashdot','longdash','dash','dot'];
  const EX_A=[[10,-1,2,0],[-1,11,-1,3],[2,-1,10,-1],[0,3,-1,8]];
  const EX_B=[6,25,-11,15];
  const EX_E=['10x1-x2+2x3=6','-x1+11x2-x3+3x4=25','2x1-x2+10x3-x4=-11','3x2-x3+8x4=15'];
  const S={method:'jacobi',entry:'ecuaciones',coord:'math',n:4,
    A:EX_A.map(r=>r.map(String)),b:EX_B.map(String),equations:EX_E.slice(),
    x0:[0,0,0,0],names:['x1','x2','x3','x4'],tol:'0.0001',max:'100',reorder:true,
    result:null,comparison:null,step:1,component:0,showAll:false,focused:null,plotRevision:0};
  const KEYS=[['7','7'],['8','8'],['9','9'],['+','+'],['−','-'],['×','*'],['x₁','x1'],['x₂','x2'],['x₃','x3'],['x₄','x4'],['⌨',''],['4','4'],['5','5'],['6','6'],['=','='],['÷','/'],['(', '('],[')', ')'],['1','1'],['2','2'],['3','3'],['0','0'],['.','.'],['½','1/2'],['⌫','BACK']];
  const el=()=>String(S.method)==='jacobi';
  const name=()=>el()?'Jacobi':'Gauss-Seidel';

  async function post(url,data){
    const rsp=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
    let out;
    try{out=await rsp.json();}catch(_){throw Error('El servidor no devolvió una respuesta válida.');}
    if(!rsp.ok||out.ok===false)throw Error(out.error||'No fue posible resolver el ejercicio.');
    return out;
  }
  function msg(text,bad=false){const n=$('iter-feedback');n.hidden=false;n.className='feedback '+(bad?'bad':'good');n.textContent=text;}
  function clearMsg(){$('iter-feedback').hidden=true;}
  function setSegment(ids,selected){ids.forEach(id=>{const btn=$(id);if(!btn)return;const active=id===selected;btn.classList.toggle('active',active);btn.setAttribute('aria-pressed',String(active));});}
  function copyDims(matrix,n){return Array.from({length:n},(_,i)=>Array.from({length:n},(_,j)=>String(matrix[i]?.[j]??'0')));}
  function cleanCurrent(){
    document.querySelectorAll('[data-iter-eq]').forEach(input=>{if(!input.hidden)S.equations[+input.dataset.iterEq]=input.value;});
    document.querySelectorAll('[data-iter-a]').forEach(input=>{const i=+input.dataset.i,j=+input.dataset.j;S.A[i][j]=input.value;});
    document.querySelectorAll('[data-iter-b]').forEach(input=>{S.b[+input.dataset.i]=input.value;});
    document.querySelectorAll('[data-iter-x0]').forEach(input=>{S.x0[+input.dataset.i]=input.value;});
    S.tol=$('iter-tolerance').value;S.max=$('iter-max').value;S.reorder=$('iter-reorder').checked;
  }
  function xName(j){return S.names[j]||`x${j+1}`;}
  function xLabel(j){const v=xName(j);const match=/^x(\d+)$/.exec(v);return match?'x'+sb(match[1]):v;}
  function position(i,j){return S.coord==='math'?`A(${i+1},${j+1})`:`A[${i}][${j}]`;}
  function equationsFromMatrix(){
    // Mantener el texto racional (p.ej. 1/3) sin convertirlo a un decimal aproximado.
    S.equations=S.A.map((row,i)=>{
      const terms=[];
      row.forEach((raw,j)=>{
        const t=String(raw).trim().replace('−','-').replace(',','.');
        if(!t||t==='0')return;
        const negative=t.startsWith('-'),positive=t.startsWith('+');
        const magnitude=(negative||positive?t.slice(1):t);
        const coeff=magnitude==='1'?'':magnitude;
        const term=coeff+(S.names[j]||`x${j+1}`);
        terms.push((negative?'-':terms.length?'+':'')+term);
      });
      return (terms.join('')||'0')+'='+S.b[i];
    });
  }
  function renderEntry(){
    const area=$('iter-entry-area');
    const heading=`<div class="iter-entry-title"><strong>${S.entry==='ecuaciones'?'Sistema de ecuaciones':'Matriz aumentada [A | b]'}</strong><span>${S.n} ecuaciones · ${S.n} incógnitas · Entrada editable</span><button type="button" class="btn btn-subtle" data-iter-keyboard="1" aria-label="Mostrar teclado matemático">⌨ Teclado</button></div>`;
    if(S.entry==='ecuaciones'){
      area.innerHTML=heading+`<div class="iter-equations-box"><span class="iter-curly" aria-hidden="true">{</span><div class="iter-equation-rows">${S.equations.map((eq,i)=>
        `<label class="iter-equation-row"><span class="iter-eq-label">E${i+1}</span><input class="iter-eq-input" type="text" data-iter-eq="${i}" value="${h(eq)}" spellcheck="false" autocomplete="off" aria-label="Ecuación ${i+1}"><button type="button" class="icon-btn" data-iter-keyboard="1" aria-label="Teclado para ecuación ${i+1}" title="Teclado matemático">⌨</button></label>`
      ).join('')}</div></div><p class="muted small">La llave agrupa todas las ecuaciones. Puedes escribir x₁ como x1, fracciones como 1/2, decimales y usar el teclado matemático.</p>`;
      attachMathLive();
    }else{
      const heads=Array.from({length:S.n},(_,j)=>`<th>Col. ${S.coord==='math'?j+1:j} · ${h(xLabel(j))}</th>`).join('');
      const rows=S.A.map((row,i)=>`<tr><th class="iter-matrix-label">Fila ${S.coord==='math'?i+1:i}<small class="iter-matrix-pos">E${i+1}</small></th>${row.map((v,j)=>`<td><span class="iter-matrix-pos">${position(i,j)}</span><input data-iter-a="1" data-i="${i}" data-j="${j}" value="${h(v)}" aria-label="${h(position(i,j))}" spellcheck="false"></td>`).join('')}<td class="iter-b-cell"><span class="iter-matrix-pos">${S.coord==='math'?`b(${i+1},1)`:`b[${i}][0]`}</span><input data-iter-b="1" data-i="${i}" value="${h(S.b[i])}" aria-label="Término independiente de la fila ${i+1}"></td></tr>`).join('');
      area.innerHTML=heading+`<div class="iter-cells-scroll"><table class="iter-table-input" aria-label="Matriz aumentada editable"><thead><tr><th>Fila</th>${heads}<th>Vector b</th></tr></thead><tbody>${rows}</tbody></table></div><p class="muted small">Cada fila representa una ecuación y la última columna corresponde a los términos independientes b. Se admiten fracciones como 3/4.</p>`;
    }
  }
  function renderX0(){
    $('iter-x0-grid').innerHTML=S.x0.map((v,i)=>`<label>${h(xLabel(i))}⁽⁰⁾<input type="text" data-iter-x0="1" data-i="${i}" value="${h(v)}" inputmode="decimal" autocomplete="off" aria-label="Valor inicial de ${h(xLabel(i))}"></label>`).join('');
  }
  function renderKeyboard(){
    $('iter-keyboard-keys').innerHTML=KEYS.filter(([a,b])=>b).map(([label,v])=>`<button type="button" data-iter-key="${h(v)}" aria-label="Insertar ${h(label)}">${h(label)}</button>`).join('');
  }
  function latexFromPlain(txt){
    if(txt.includes('\\'))return txt;
    return txt.replace(/\bx(\d+)\b/g,'x_{$1}').replace(/\*/g,'\\cdot ');
  }
  function attachMathLive(){
    if(!window.customElements?.get('math-field'))return;
    document.querySelectorAll('input[data-iter-eq]').forEach(input=>{
      if(input.hidden||input.nextElementSibling?.tagName==='MATH-FIELD')return;
      const mf=document.createElement('math-field');mf.className='iter-equation-math';
      mf.setAttribute('virtual-keyboard-mode','manual');
      mf.value=latexFromPlain(input.value);
      input.insertAdjacentElement('afterend',mf);input.hidden=true;
      mf.dataset.iterEq=input.dataset.iterEq;
      mf.setAttribute('aria-label','Editor matemático de la ecuación '+(Number(input.dataset.iterEq)+1));
      mf.addEventListener('input',()=>{const text=String(mf.value||'');input.value=text;S.equations[+input.dataset.iterEq]=text;resetResults();});
      mf.addEventListener('focus',()=>{S.focused=mf;});
    });
  }
  function fillConfig(){
    $('iter-dim').innerHTML=Array.from({length:14},(_,i)=>`<option value="${i+2}" ${(i+2)===S.n?'selected':''}>${i+2} × ${i+2}</option>`).join('');
    setSegment(['iter-entry-equations','iter-entry-matrix'],S.entry==='ecuaciones'?'iter-entry-equations':'iter-entry-matrix');
    setSegment(['iter-coord-math','iter-coord-prog'],S.coord==='math'?'iter-coord-math':'iter-coord-prog');
    $('iter-tolerance').value=S.tol;$('iter-max').value=S.max;$('iter-reorder').checked=S.reorder;
    renderEntry();renderX0();renderKeyboard();
  }
  function methodName(method){return method==='jacobi'?'Jacobi':'Gauss-Seidel';}
  function openMethod(m){
    cleanCurrent();
    S.method=m;S.result=null;S.comparison=null;S.step=1;S.component=0;S.showAll=false;
    const seidel=m==='gauss_seidel';
    $('view-iterative-workspace').classList.toggle('iter-method-seidel',seidel);
    $('view-iterative-workspace').classList.toggle('iter-method-jacobi',!seidel);
    $('iter-title').textContent=methodName(m);$('iter-breadcrumb').textContent=methodName(m);
    $('iter-subtitle').textContent=seidel?'Actualiza cada incógnita inmediatamente, aprovechando las componentes nuevas de la misma iteración.':'Calcula simultáneamente las nuevas incógnitas usando exclusivamente el vector anterior.';
    $('iter-header-equation').textContent=seidel?'xᵢ⁽ᵏ⁺¹⁾ = [bᵢ − Σⱼ<ᵢ aᵢⱼxⱼ⁽ᵏ⁺¹⁾ − Σⱼ>ᵢ aᵢⱼxⱼ⁽ᵏ⁾] / aᵢᵢ':'xᵢ⁽ᵏ⁺¹⁾ = [bᵢ − Σⱼ≠ᵢ aᵢⱼxⱼ⁽ᵏ⁾] / aᵢᵢ';
    $('iter-development-title').textContent=seidel?'Actualización secuencial de componentes':'Actualización simultánea de vectores';
    $('iter-development-sub').textContent=seidel?'Selecciona una componente para ver los valores nuevos que ya se habían calculado y los anteriores que aún se usan.':'Compara el vector anterior con el nuevo; todas las sustituciones usan los datos de la iteración anterior.';
    $('iter-solve').textContent='Resolver por '+methodName(m)+' →';
    $('iter-choco').textContent=seidel?'☕ Choco dice: Gauss-Seidel aprovecha los valores recién calculados, pero no siempre converge más rápido.':'☕ Choco dice: Jacobi calcula cada componente únicamente a partir del vector de la iteración anterior.';
    resetResults();fillConfig();clearMsg();
  }
  function resetResults(){
    S.result=null;S.comparison=null;S.step=1;S.component=0;S.showAll=false;
    ['iter-diagnostic-body','iter-variable-plot','iter-error-plot','iter-results','iter-vector-comparator','iter-development-body','iter-verification-body','iter-comparison-body'].forEach(id=>{
      const node=$(id);if(!node)return;
      if(node.classList.contains('iter-plot')){if(window.Plotly)try{Plotly.purge(node);}catch(_){};node.replaceChildren();}
      else node.innerHTML='<div class="iter-placeholder">Completa los datos y resuelve el sistema para explorar este apartado.</div>';
    });
    $('iter-table-head').innerHTML='';$('iter-table-body').innerHTML='<tr><td class="empty-cell">Las iteraciones aparecerán aquí.</td></tr>';
    $('iter-table-status').textContent='Sin resolver';$('iter-step-counter').textContent='—';
    ['iter-prev','iter-next','iter-all','iter-csv','iter-compare-btn'].forEach(id=>$(id).disabled=true);
    $('iter-comparison-plot').hidden=true;
    if(window.Plotly)try{Plotly.purge($('iter-comparison-plot'));}catch(_){}
  }
  function setN(n){
    cleanCurrent();
    const previousN=S.n;S.n=n;S.A=copyDims(S.A,n);
    for(let i=previousN;i<n;i++)S.A[i][i]='1';
    S.b=Array.from({length:n},(_,i)=>String(S.b[i]??'0'));
    S.x0=Array.from({length:n},(_,i)=>S.x0[i]??'0');
    S.names=Array.from({length:n},(_,i)=>`x${i+1}`);
    equationsFromMatrix();
    // Al cambiar dimensiones se generan ecuaciones coherentes con la matriz redimensionada.
    fillConfig();resetResults();clearMsg();
    msg('El sistema se ajustó a '+n+' incógnitas. Revisa las nuevas ecuaciones o casillas antes de resolver.');
  }
  async function setEntry(mode){
    if(S.entry===mode)return;
    cleanCurrent();
    let syncError=null;
    if(mode==='matriz'){
      try{
        const data=await post('/api/iterativos/parse',{ecuaciones:S.equations,n:S.n});
        S.A=(data.A_texto||data.A).map(row=>row.map(String));S.b=(data.b_texto||data.b).map(String);S.names=data.nombres;
      }catch(ex){
        // Nunca bloquear el acceso al editor de casillas por una ecuación incompleta.
        // Conservamos la matriz existente y advertimos que no hubo sincronización.
        syncError=ex.message;
      }
    }else{equationsFromMatrix();}
    S.entry=mode;renderEntry();renderX0();
    setSegment(['iter-entry-equations','iter-entry-matrix'],mode==='ecuaciones'?'iter-entry-equations':'iter-entry-matrix');
    resetResults();clearMsg();
    if(syncError)msg('Se abrió el editor de matriz con los últimos valores guardados. No fue posible sincronizar las ecuaciones: '+syncError,true);
  }
  function payload(){
    cleanCurrent();
    const result={entrada:S.entry,metodo:S.method,n:S.n,
      x0:S.x0,tolerancia:S.tol,max_it:S.max,reordenar:S.reorder};
    if(S.entry==='ecuaciones')result.ecuaciones=S.equations;
    else {result.A=S.A;result.b=S.b;}
    return result;
  }
  function rowMat(A,oneColumn=false){
    const r=oneColumn?A.map(x=>[x]):A;
    return `<div class="iter-matrix-wrap"><span class="iter-matrix-l"></span><table class="iter-numeric-matrix"><tbody>${r.map(row=>`<tr>${row.map(v=>`<td>${h(fmt(v))}</td>`).join('')}</tr>`).join('')}</tbody></table><span class="iter-matrix-r"></span></div>`;
  }
  function metric(label,result,sub){return `<div class="iter-metric"><span>${h(label)}</span><strong>${h(result)}</strong><small>${h(sub)}</small></div>`;}
  function formula(i,r){
    const parts=[`<span>${h(fmt(r.b[i]))}</span>`];
    for(let j=0;j<r.A.length;j++){
      if(i===j||r.A[i][j]===0)continue;
      const a=r.A[i][j],mag=Math.abs(a);
      const coefficient=mag===1?'':h(fmt(mag));
      parts.push(` <b>${a<0?'+':'−'}</b> ${coefficient}<var>${h(xLabel(j))}</var>`);
    }
    return `<var>${h(xLabel(i))}</var> = <span class="iter-frac"><span>${parts.join('')}</span><span>${h(fmt(r.A[i][i]))}</span></span>`;
  }
  function renderDiagnosis(r){
    const d=r.diagnostico;
    const note=d.dominancia_estricta
      ?'<span class="iter-status-good">✓ Dominancia diagonal estricta en todas las filas: condición suficiente de convergencia.</span>'
      :'<span class="iter-status-bad">⚠ No se cumple dominancia diagonal estricta en todas las filas. Puede converger, pero no está garantizado por este criterio.</span>';
    const warning=r.reordenada?`<p class="small muted">Se reordenaron las ecuaciones según el orden original ${r.orden_filas.map(x=>'E'+x).join(', ')} para evitar pivotes diagonales nulos. La solución del sistema no cambia.</p>`:'';
    const table=`<table class="iter-small-table"><thead><tr><th>Fila</th><th>|aᵢᵢ|</th><th>Σⱼ≠ᵢ |aᵢⱼ|</th><th>Evaluación</th></tr></thead><tbody>${d.filas.map(row=>`<tr><td>${row.fila}</td><td>${h(fmt(row.diagonal_abs))}</td><td>${h(fmt(row.suma_fuera))}</td><td class="${row.estricta?'good':'bad'}">${row.estricta?'Cumple':'No cumple'}</td></tr>`).join('')}</tbody></table>`;
    const hint=el()?'Jacobi: todos los valores de la derecha provienen de X⁽ᵏ⁾.':'Gauss-Seidel: utiliza X⁽ᵏ⁺¹⁾ para j < i y X⁽ᵏ⁾ para j > i.';
    $('iter-diagnostic-body').innerHTML=`<div class="iter-diag-headline ${d.dominancia_estricta?'good':'warn'}">${note}</div>${warning}<div class="iter-diagnostic-grid"><div class="iter-subpanel"><h3>Análisis de la diagonal</h3>${table}</div><div class="iter-subpanel"><h3>Despeje de cada incógnita</h3><div class="iter-formula-list">${r.A.map((_,i)=>`<div class="iter-formula-row">${formula(i,r)}</div>`).join('')}</div><p class="muted small">${hint}</p></div></div>`;
  }
  function sourceValue(r,step,i,j){
    const prev=r.filas[step-1].x;
    const fresh=r.filas[step].x;
    const isNew=r.metodo==='gauss_seidel'&&j<i;
    return {value:isNew?fresh[j]:prev[j],fresh:isNew,source:isNew?'recién calculado':'iteración anterior'};
  }
  function componentDetail(r,step,i){
    const now=r.filas[step].x[i];
    const prev=r.filas[step-1].x;
    const nameI=h(xLabel(i));
    const p=[];
    const tags=[];
    for(let j=0;j<r.A.length;j++){
      if(i===j||r.A[i][j]===0)continue;
      const a=r.A[i][j],src=sourceValue(r,step,i,j);
      p.push(`<b> − </b><span>(${h(fmt(a))} · ${h(fmt(src.value))})</span>`);
      tags.push(`<span class="iter-source-tag ${src.fresh?'new':'old'}">${h(xLabel(j))} = ${h(fmt(src.value))} · ${src.fresh?'nuevo':'anterior'}</span>`);
    }
    const numerator=h(fmt(r.b[i]))+p.join('');
    const statement=`<var>${nameI}</var><sup>(${step})</sup> = <span class="iter-frac"><span>${numerator}</span><span>${h(fmt(r.A[i][i]))}</span></span> = <strong>${h(fmt(now))}</strong>`;
    return `<article class="iter-equation-detail"><h3>Componente ${nameI} · iteración ${step}</h3><div class="iter-longmath">${statement}</div><div class="iter-source-tags">${tags.join('')||'<span class="iter-source-tag">Sin otras incógnitas</span>'}</div></article>`;
  }
  function vectorCard(values,label){
    return `<div class="iter-vector-card"><h3>${h(label)}</h3><div class="iter-vector-values">${values.map((value,i)=>`<span class="iter-vector-pill">${h(xLabel(i))} = ${h(fmt(value))}</span>`).join('')}</div></div>`;
  }
  function renderDevelopment(){
    const r=S.result;if(!r)return;
    const max=r.filas.length-1;
    S.step=Math.max(0,Math.min(S.step,max));S.component=Math.max(0,Math.min(S.component,r.A.length-1));
    $('iter-step-counter').textContent=max?`Iteración ${S.step} de ${max}`:'Solución en el vector inicial';
    $('iter-prev').disabled=S.step<=1;
    $('iter-next').disabled=S.step>=max;
    $('iter-all').disabled=max===0;
    $('iter-all').textContent=S.showAll?'Ver iteración seleccionada':'Mostrar todos los pasos';
    const current=r.filas[S.step].x;
    const previous=r.filas[Math.max(0,S.step-1)].x;
    $('iter-vector-comparator').innerHTML=vectorCard(previous,S.step?'Vector anterior X⁽'+(S.step-1)+'⁾':'Vector inicial X⁽⁰⁾')+vectorCard(current,'Vector obtenido X⁽'+S.step+'⁾');
    if(max===0){$('iter-development-body').innerHTML='<div class="iter-placeholder">El vector inicial ya satisface la tolerancia; no se requieren actualizaciones.</div>';return;}
    if(S.step===0){$('iter-development-body').innerHTML='<div class="iter-placeholder">k = 0 corresponde al vector inicial. Selecciona la iteración 1 para revisar las primeras sustituciones.</div>';return;}
    if(S.showAll){
      $('iter-development-body').innerHTML=`<p class="muted small">Despliega cualquier iteración para ver todas las sustituciones sin saturar la pantalla.</p>${r.filas.slice(1).map((row)=>`<details class="iter-equation-detail" data-iter-details="${row.k}"><summary>Iteración ${row.k} · residuo ${h(fmt(row.residuo))} · cambio ${h(fmt(row.cambio))}</summary><div data-iter-detail-body></div></details>`).join('')}`;
      document.querySelectorAll('[data-iter-details]').forEach(card=>card.addEventListener('toggle',()=>{
        if(!card.open)return;
        const target=card.querySelector('[data-iter-detail-body]');if(target.dataset.loaded)return;
        const k=Number(card.dataset.iterDetails);
        target.innerHTML=r.A.map((_,i)=>componentDetail(r,k,i)).join('');target.dataset.loaded='true';
      }));
      return;
    }
    if(el()){
      $('iter-development-body').innerHTML=`<p class="muted small">Todas las sustituciones utilizan exclusivamente las componentes de X⁽${S.step-1}⁾; ninguna emplea resultados de la iteración actual.</p><div class="iter-jacobi-calcs">${r.A.map((_,i)=>componentDetail(r,S.step,i)).join('')}</div><div class="iter-source-tags"><span class="iter-source-tag old">Residuo de esta iteración: ${h(fmt(r.filas[S.step].residuo))}</span><span class="iter-source-tag old">Cambio máximo: ${h(fmt(r.filas[S.step].cambio))}</span></div>`;
    }else{
      const cards=r.A.map((_,i)=>`<button type="button" data-iter-component="${i}" class="${i===S.component?'active':''}"><strong>${h(xLabel(i))}<sup>(${S.step})</sup> = ${h(fmt(current[i]))}</strong><small>${i===0?'Primera actualización':`Utiliza las ${i} componente(s) recién calculadas que correspondan`}</small></button>`).join('');
      $('iter-development-body').innerHTML=`<p class="muted small">Selecciona cada componente siguiendo el orden de actualización. <span class="iter-status-good">Verde: valor nuevo</span> · <span style="color:var(--brown)">Café: valor anterior</span>.</p><div class="iter-steps-board">${cards}</div>${componentDetail(r,S.step,S.component)}<details class="iter-subpanel"><summary>Mostrar las ${r.A.length} sustituciones de esta iteración</summary>${r.A.map((_,i)=>componentDetail(r,S.step,i)).join('')}</details>`;
      $('iter-development-body').querySelectorAll('[data-iter-component]').forEach(button=>button.addEventListener('click',()=>{S.component=+button.dataset.iterComponent;renderDevelopment();}));
    }
  }
  function tableRow(r,row){
    return `<tr data-iter-k="${row.k}" class="${row.k===S.step?'selected':''}" tabindex="0" aria-label="Ver iteración ${row.k}"><td>${row.k}</td>${row.x.map(x=>`<td>${h(fmt(x))}</td>`).join('')}<td>${h(fmt(row.residuo))}</td><td>${h(fmt(row.cambio))}</td></tr>`;
  }
  function renderTable(r){
    $('iter-table-head').innerHTML=`<tr><th>k</th>${r.A.map((_,i)=>`<th>${h(xLabel(i))}<sup>(k)</sup></th>`).join('')}<th>‖b − AX‖∞</th><th>‖ΔX‖∞</th></tr>`;
    $('iter-table-body').innerHTML=r.filas.map(row=>tableRow(r,row)).join('');
    $('iter-table-status').textContent=(r.filas.length)+' filas · incluye X⁽⁰⁾ · '+(r.convergencia?'Convergencia alcanzada':'Sin convergencia confirmada');
    $('iter-csv').disabled=false;
    const tbody=$('iter-table-body');
    tbody.querySelectorAll('[data-iter-k]').forEach(tr=>{
      const fn=()=>setStep(+tr.dataset.iterK);
      tr.addEventListener('click',fn);
      tr.addEventListener('keydown',evt=>{if(evt.key==='Enter'||evt.key===' '){evt.preventDefault();fn();}});
    });
  }
  function setStep(k){
    if(!S.result)return;
    S.step=Math.max(0,Math.min(k,S.result.filas.length-1));S.showAll=false;
    $('iter-table-body').querySelectorAll('[data-iter-k]').forEach(row=>row.classList.toggle('selected',+row.dataset.iterK===S.step));
    renderDevelopment();renderPlots();
  }
  function chartColors(){const style=getComputedStyle(document.body);
    return {text:style.getPropertyValue('--ink').trim()||'#382417',
      muted:style.getPropertyValue('--ink-muted').trim()||'#806b5c',
      surface:style.getPropertyValue('--surface').trim()||'#fffdf9',
      grid:style.getPropertyValue('--grid').trim()||'#e8ddd1',
      accent:style.getPropertyValue('--accent').trim()||'#b4744c'};
  }
  function plotLayout(height=400){
    const c=chartColors();return {paper_bgcolor:c.surface,plot_bgcolor:c.surface,
      font:{color:c.text,family:'DM Sans, Segoe UI, sans-serif',size:11},
      margin:{l:65,r:28,t:25,b:90},height,hovermode:'x unified',
      xaxis:{title:'Iteración k',gridcolor:c.grid,zerolinecolor:c.grid,automargin:true,fixedrange:false},
      yaxis:{title:'Valor aproximado',gridcolor:c.grid,zerolinecolor:c.grid,automargin:true,fixedrange:false,tickformat:'.6~f'},
      legend:{orientation:'h',x:0,y:-.28,xanchor:'left',yanchor:'top',font:{size:11},itemwidth:35},
      uirevision:'iterativos-'+S.plotRevision};
  }
  function plotConfig(){return {responsive:true,displaylogo:false,scrollZoom:true,
    modeBarButtonsToRemove:['lasso2d','select2d','autoScale2d']};}
  function renderPlots(){
    const r=S.result;if(!r)return;
    if(typeof window.Plotly==='undefined'){
      $('iter-variable-plot').textContent='La visualización requiere Plotly, incluido en la instalación de Choco Lab.';
      return;
    }
    const points=r.filas.map(x=>x.k),n=r.A.length;
    const traces=Array.from({length:n},(_,i)=>({
      x:points,y:r.filas.map(q=>q.x[i]),type:'scatter',mode:'lines+markers',name:xLabel(i),
      line:{color:PALETTE[i%PALETTE.length],width:2.6,dash:DASH[i%DASH.length]},
      marker:{size:5,color:PALETTE[i%PALETTE.length]},
      customdata:r.filas.map(q=>fmt(q.x[i])),
      hovertemplate:`${xLabel(i)} · k=%{x}<br>Valor: %{customdata}<extra></extra>`
    }));
    // El foco se marca sobre todas las líneas; nunca se ocultan trazas.
    const selected=r.filas.find(row=>row.k===S.step);
    if(selected){
      traces.push({x:Array(n).fill(selected.k),y:selected.x,type:'scatter',mode:'markers',
        name:'Iteración seleccionada',showlegend:false,marker:{size:12,color:PALETTE.slice(0,n),symbol:'circle',line:{color:chartColors().surface,width:2}},
        customdata:Array.from({length:n},(_,i)=>[xLabel(i),fmt(selected.x[i])]),hovertemplate:'%{customdata[0]} · k=%{x}<br>%{customdata[1]}<extra></extra>'});
    }
    const layout=plotLayout(n>9?500:440);
    layout.shapes=[{type:'line',xref:'x',yref:'paper',x0:S.step,x1:S.step,y0:0,y1:1,
      line:{color:chartColors().accent,dash:'dot',width:1}}];
    const target=$('iter-variable-plot');
    Plotly.react(target,traces,layout,plotConfig()).then(()=>{
      target.removeAllListeners?.('plotly_click');
      target.on('plotly_click',ev=>{if(ev.points?.length){const k=Math.round(+ev.points[0].x);if(Number.isInteger(k))setStep(k);}});
    }).catch(()=>{target.textContent='No fue posible generar la gráfica. Revisa Plotly.';});
    const epsilon=Math.max(r.tolerancia,1e-15);
    const errorData=[
      {x:points,y:r.filas.map(q=>q.residuo>0?q.residuo:null),customdata:r.filas.map(q=>fmt(q.residuo)),hovertemplate:'Residuo · k=%{x}<br>%{customdata}<extra></extra>',mode:'lines+markers',name:'Residuo',type:'scatter',line:{color:'#c65a31',width:2.6},marker:{size:5}},
      {x:points,y:r.filas.map(q=>q.cambio>0?q.cambio:null),customdata:r.filas.map(q=>fmt(q.cambio)),hovertemplate:'Cambio máximo · k=%{x}<br>%{customdata}<extra></extra>',mode:'lines+markers',name:'Cambio máximo',type:'scatter',line:{color:'#277aa2',width:2.6},marker:{size:5}},
      {x:points,y:points.map(()=>epsilon),type:'scatter',mode:'lines',name:'Tolerancia ε',customdata:points.map(()=>fmt(epsilon)),hovertemplate:'Tolerancia ε<br>%{customdata}<extra></extra>',line:{color:chartColors().muted,dash:'dash',width:2}}
    ];
    const errorLayout=plotLayout(320);errorLayout.yaxis.title='Magnitud (escala logarítmica)';errorLayout.yaxis.type='log';
    errorLayout.margin.b=85;
    Plotly.react($('iter-error-plot'),errorData,errorLayout,plotConfig()).catch(()=>{});
    $('iter-plot-caption').textContent=`Se muestran ${n} incógnitas simultáneamente. Cada color representa una variable y los puntos resaltados corresponden a k = ${S.step}. Haz clic en una iteración para ver su desarrollo.`;
  }
  function renderSummary(r){
    $('iter-results').innerHTML=metric('VECTOR SOLUCIÓN APROXIMADO',r.solucion.map((x,i)=>`${xLabel(i)}=${fmt(x)}`).join(' · '),r.convergencia?'Convergencia confirmada':'Aproximación no validada')+
      metric('ITERACIONES',String(r.iteraciones),`Límite establecido: ${r.max_it}`)+
      metric('RESIDUO ‖b − AX‖∞',fmt(r.residuo),`Tolerancia: ${fmt(r.tolerancia)}`)+
      metric('CAMBIO MÁXIMO ‖ΔX‖∞',fmt(r.cambio),r.convergencia?'Se cumplieron los criterios':'No se cumplieron ambos criterios');
  }
  function renderVerification(r){
    const valid=r.convergencia;
    const residualValid=r.residuo<=r.tolerancia;
    const changeValid=r.cambio===null?null:r.cambio<=r.tolerancia;
    const note=valid?'Se alcanzaron los criterios establecidos. La solución es aproximada, no necesariamente exacta.':'No se alcanzaron simultáneamente los criterios. El último vector mostrado NO debe presentarse como una solución convergida.';
    const rowCheck=`<table class="iter-small-table"><thead><tr><th>Ecuación</th><th>(AX)ᵢ</th><th>bᵢ</th><th>Residuo rᵢ</th></tr></thead><tbody>${r.A.map((row,i)=>`<tr><td>E${i+1}</td><td>${h(fmt(r.Ax[i]))}</td><td>${h(fmt(r.b[i]))}</td><td>${h(fmt(r.residual_vector[i]))}</td></tr>`).join('')}</tbody></table>`;
    $('iter-verification-body').innerHTML=`<div class="iter-diag-headline ${valid?'good':'warn'}">${valid?'✓':'⚠'} ${h(note)}</div>
      <p class="muted small">${h(r.motivo)}</p>
      <div class="iter-verification-cards"><div class="iter-subpanel"><h3>Vector aproximado X</h3>${rowMat(r.solucion,true)}</div>
      <div class="iter-subpanel"><h3>Producto AX</h3>${rowMat(r.Ax,true)}</div>
      <div class="iter-subpanel"><h3>Términos independientes b</h3>${rowMat(r.b,true)}</div></div>
      <div class="iter-subpanel"><h3>Verificación de las ecuaciones: r = b − AX</h3>${rowCheck}</div>
      <div class="iter-verify-details" style="margin-top:12px">
      <div class="iter-verify-row"><span>‖b − AX‖∞ = ${h(fmt(r.residuo))} ≤ ${h(fmt(r.tolerancia))}</span><strong class="${residualValid?'iter-status-good':'iter-status-bad'}">${residualValid?'Cumple':'No cumple'}</strong></div>
      <div class="iter-verify-row"><span>‖X⁽ᵏ⁾ − X⁽ᵏ⁻¹⁾‖∞ = ${h(fmt(r.cambio))} ≤ ${h(fmt(r.tolerancia))}</span><strong class="${changeValid||r.iteraciones===0&&residualValid?'iter-status-good':'iter-status-bad'}">${r.iteraciones===0?'No requerido':changeValid?'Cumple':'No cumple'}</strong></div></div>`;
  }
  function renderComparison(data){
    S.comparison=data;
    const names=[['jacobi','Jacobi'],['gauss_seidel','Gauss-Seidel']];
    $('iter-comparison-body').innerHTML=`<div class="iter-compare-cards">${names.map(([key,label])=>{
      const r=data[key];return `<div class="iter-compare-card"><h3>${label}</h3><p><b>Estado:</b> <span class="${r.convergencia?'iter-status-good':'iter-status-bad'}">${r.convergencia?'Convergencia alcanzada':'Sin convergencia confirmada'}</span></p>
      <p><b>Iteraciones:</b> ${r.iteraciones}</p><p><b>Residuo:</b> ${h(fmt(r.residuo))}</p><p><b>Cambio máximo:</b> ${h(fmt(r.cambio))}</p><p><b>Vector obtenido:</b> (${r.solucion.map(v=>h(fmt(v))).join(', ')})</p></div>`;
    }).join('')}</div><p class="muted small">Ambos cálculos usan los mismos datos y criterios. El método más rápido para este ejemplo no necesariamente es mejor para todos los sistemas.</p>`;
    const p=$('iter-comparison-plot');p.hidden=false;
    if(window.Plotly){
      const colors=['#3369b0','#d6782f'];
      const traces=names.map(([key,label],i)=>({x:data[key].filas.map(row=>row.k),
        y:data[key].filas.map(row=>row.residuo>0?row.residuo:null),customdata:data[key].filas.map(row=>fmt(row.residuo)),hovertemplate:label+' · k=%{x}<br>Residuo: %{customdata}<extra></extra>',type:'scatter',mode:'lines+markers',name:label,
        line:{color:colors[i],width:3},marker:{size:5}}));
      const layout=plotLayout(325);layout.yaxis={...layout.yaxis,type:'log',title:'Residuo ‖b−AX‖∞'};
      Plotly.react(p,traces,layout,plotConfig()).catch(()=>{});
    }
  }
  function renderSolution(r){
    S.plotRevision++;
    S.result=r;S.comparison=null;S.step=r.filas.length>1?1:0;S.component=0;S.showAll=false;
    S.names=r.nombres||S.names;
    // Los despejes proceden de la matriz efectivamente usada por el algoritmo.
    renderDiagnosis(r);renderSummary(r);renderTable(r);renderDevelopment();renderPlots();renderVerification(r);
    $('iter-prev').disabled=S.step<=1;$('iter-next').disabled=S.step>=r.iteraciones;
    $('iter-all').disabled=r.iteraciones===0;
    $('iter-csv').disabled=false;
    $('iter-compare-btn').disabled=false;
    $('iter-comparison-body').innerHTML='<div class="iter-placeholder">Puedes comparar este resultado con el otro método usando exactamente los mismos datos.</div>';
    $('iter-comparison-plot').hidden=true;
  }
  async function calculate(compare=false){
    clearMsg();const button=$(compare?'iter-compare-btn':'iter-solve');
    const start=button.textContent;button.disabled=true;button.textContent='Calculando…';
    try{
      const body=payload();
      if(compare){
        const data=await post('/api/iterativos/comparar',body);
        renderComparison(data);
      }else{
        const r=await post('/api/iterativos/resolver',body);renderSolution(r);
      }
      const r=S.result;
      msg(r.convergencia?`Cálculo terminado: ${r.iteraciones} iteraciones; residuo ${fmt(r.residuo)}. Puedes examinar los desarrollos y la verificación.`:`No se alcanzó la tolerancia. ${r.motivo}`,!r.convergencia);
      if(window.innerWidth<800)$(compare?'iter-compare-section':'iter-diagnostic').scrollIntoView({behavior:'smooth',block:'start'});
    }catch(err){msg(err.message,true);}
    finally{button.disabled=false;button.textContent=start;}
  }
  function downloadCsv(){
    const r=S.result;if(!r)return;
    const headers=['k',...r.A.map((_,i)=>xName(i)),'residuo_infinito','cambio_infinito'];
    const rows=r.filas.map(row=>[row.k,...row.x,row.residuo,row.cambio===null?'':row.cambio]);
    const csv='\uFEFF'+[headers,...rows].map(row=>row.join(';')).join('\r\n');
    const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));
    const a=document.createElement('a');a.href=url;a.download=`ChocoLab_${S.method}_iteraciones.csv`;a.click();
    setTimeout(()=>URL.revokeObjectURL(url),3000);
  }
  function example(){
    S.n=4;S.A=EX_A.map(row=>row.map(String));S.b=EX_B.map(String);S.equations=EX_E.slice();
    S.x0=['0','0','0','0'];S.names=['x1','x2','x3','x4'];S.tol='0.0001';S.max='100';S.reorder=true;
    fillConfig();resetResults();clearMsg();msg('Ejemplo del material de clase cargado: 4 ecuaciones y 4 incógnitas.');
  }
  function clearInputs(){
    cleanCurrent();S.A=Array.from({length:S.n},()=>Array.from({length:S.n},()=>''));
    S.b=Array(S.n).fill('');S.equations=Array(S.n).fill('');S.x0=Array(S.n).fill('0');
    fillConfig();resetResults();clearMsg();
  }
  function insertKeyboard(value){
    const input=S.focused;
    if(!input||!input.isConnected){msg('Selecciona una ecuación o una casilla para usar el teclado.',true);return;}
    if(input.tagName==='MATH-FIELD'){
      if(value==='BACK')input.executeCommand('deleteBackward');
      else input.insert(/^x\d+$/.test(value)?`x_{${value.slice(1)}}`:value==='*'?'\\cdot ':value==='1/2'?'\\frac{1}{2}':value,
        {selectionMode:'after'});
      input.dispatchEvent(new Event('input',{bubbles:true}));input.focus();return;
    }
    const start=input.selectionStart??input.value.length,end=input.selectionEnd??start;
    let fresh,position;
    if(value==='BACK'){
      const left=start===end?Math.max(0,start-1):start;
      fresh=input.value.slice(0,left)+input.value.slice(end);position=left;
    }else{
      fresh=input.value.slice(0,start)+value+input.value.slice(end);position=start+value.length;
    }
    input.value=fresh;input.setSelectionRange?.(position,position);
    input.dispatchEvent(new Event('input',{bubbles:true}));input.focus();
  }
  function init(){
    const root=$('view-iterative-workspace');if(!root)return;
    fillConfig();resetResults();
    document.querySelectorAll('[data-iter-method]').forEach(btn=>btn.addEventListener('click',()=>openMethod(btn.dataset.iterMethod)));
    $('iter-dim').addEventListener('change',evt=>setN(+evt.target.value));
    $('iter-entry-equations').addEventListener('click',()=>setEntry('ecuaciones'));
    $('iter-entry-matrix').addEventListener('click',()=>setEntry('matriz'));
    $('iter-coord-math').addEventListener('click',()=>{cleanCurrent();S.coord='math';setSegment(['iter-coord-math','iter-coord-prog'],'iter-coord-math');renderEntry();renderX0();});
    $('iter-coord-prog').addEventListener('click',()=>{cleanCurrent();S.coord='prog';setSegment(['iter-coord-math','iter-coord-prog'],'iter-coord-prog');renderEntry();renderX0();});
    $('iter-solve').addEventListener('click',()=>calculate(false));$('iter-compare-btn').addEventListener('click',()=>calculate(true));
    $('iter-example').addEventListener('click',example);$('iter-clear').addEventListener('click',clearInputs);
    $('iter-prev').addEventListener('click',()=>setStep(S.step-1));$('iter-next').addEventListener('click',()=>setStep(S.step+1));
    $('iter-all').addEventListener('click',()=>{S.showAll=!S.showAll;renderDevelopment();});
    $('iter-csv').addEventListener('click',downloadCsv);
    $('iter-keyboard-close').addEventListener('click',()=>{$('iter-keyboard').hidden=true;});
    $('iter-keyboard-keys').addEventListener('click',evt=>{
      const button=evt.target.closest('[data-iter-key]');if(button)insertKeyboard(button.dataset.iterKey);
    });
    root.addEventListener('click',evt=>{
      const btn=evt.target.closest('[data-iter-keyboard]');
      if(btn){
        const row=btn.closest('.iter-equation-row');const target=row?.querySelector('math-field:not([hidden])')||row?.querySelector('input[data-iter-eq]')||(S.focused?.isConnected?S.focused:document.querySelector('#iter-entry-area input'));
        if(target)S.focused=target;
        $('iter-keyboard').hidden=!$('iter-keyboard').hidden;
        S.focused?.focus();
      }
    });
    root.addEventListener('focusin',evt=>{if(evt.target.matches('input[data-iter-eq], input[data-iter-a], input[data-iter-b], input[data-iter-x0], math-field.iter-equation-math'))S.focused=evt.target;});
    root.addEventListener('input',evt=>{
      const t=evt.target;
      if(t.matches('[data-iter-eq]'))S.equations[+t.dataset.iterEq]=t.value;
      if(t.matches('[data-iter-a]'))S.A[+t.dataset.i][+t.dataset.j]=t.value;
      if(t.matches('[data-iter-b]'))S.b[+t.dataset.i]=t.value;
      if(t.matches('[data-iter-x0]'))S.x0[+t.dataset.i]=t.value;
      if(t.matches('[data-iter-eq], [data-iter-a], [data-iter-b], [data-iter-x0], #iter-max,#iter-tolerance'))resetResults();
    });
    root.addEventListener('change',evt=>{if(evt.target.id==='iter-reorder')resetResults();});
    customElements.whenDefined('math-field').then(()=>attachMathLive());
    new MutationObserver(records=>{if(records.some(record=>record.attributeName==='data-theme')&&S.result&&!root.hidden){renderPlots();if(S.comparison)renderComparison(S.comparison);}}).observe(document.body,{attributes:true,attributeFilter:['data-theme']});
  }
  document.addEventListener('DOMContentLoaded',init);
})();
