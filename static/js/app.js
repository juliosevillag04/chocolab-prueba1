/* Choco Lab · Interfaz. El cálculo de los cuatro métodos se realiza exclusivamente en Python. */
'use strict';
(() => {
  const $ = id => document.getElementById(id);
   const state = {view:'home',method:'biseccion',theme:'light',mode:'auto',candidates:[],selectedCandidate:null,
    preview:null,solution:null,selectedStep:null,clickStage:0,mathLive:false,formulaLast:'',firstPreview:true,plotView:'roots',plotRevision:0};
  const keyboardKeys = {
    basic:[['x','x'],['y','y'],['π','pi'],['e','e'],['7','7'],['8','8'],['9','9'],['×','*'],['÷','/'],['x²','^2'],['xⁿ','^'],['√','sqrt('],['|x|','abs('],['4','4'],['5','5'],['6','6'],['+','+'],['−','-'],['(', '('],[')', ')'],['1','1'],['2','2'],['3','3'],['0','0'],['.','.'],['⌫','BACK'],['Limpiar','CLEAR']],
    functions:[['sen','sin('],['cos','cos('],['tg','tan('],['arcsen','asin('],['arccos','acos('],['arctg','atan('],['ln','ln('],['log','log('],['eˣ','exp('],['√x','sqrt('],['x³','^3'],['π','pi'],['x','x'],['(', '('],[')', ')'],['÷','/'],['×','*'],['⌫','BACK']],
    letters:['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z'].map(k=>[k,k]),
    symbols:[['+','+'],['−','-'],['×','*'],['÷','/'],['^','^'],['(', '('],[')', ')'],['.','.'],[',',','],['π','pi'],['√','sqrt('],['=','='],['⌫','BACK'],['Limpiar','CLEAR']]
  };
  const escapeHtml = text => String(text).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fmt = (val, digits=6) => {
    if (val === null || val === undefined || !Number.isFinite(Number(val))) return '—';
    const n = Number(val);
    if (n === 0) return '0';

    if (Math.abs(n) < Math.pow(10, -digits)) return n.toExponential(2);
    return n.toFixed(digits).replace(/\.?0+$/, '');
  };
  // Residuos muy pequeños: mostrar su magnitud real, no "0" por redondeo.
  // Un cero matemáticamente exacto no se reemplaza por un número inventado.
  const fmtResiduo = val => {
    if (val === null || val === undefined || !Number.isFinite(Number(val))) return '—';
    const n = Math.abs(Number(val));
    if (n === 0) return 'Exacto o límite numérico';
    if (n >= 0.00001) return fmt(n,10);
    const [coef,exponente] = n.toExponential(2).split('e');
    const superindices = {'-':'⁻','+':'⁺','0':'⁰','1':'¹','2':'²','3':'³',
      '4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹'};
    const exp = String(Number(exponente)).split('').map(c=>superindices[c]||c).join('');
    return `${coef} × 10${exp}`;
  };
  function toast(msg) {
    const el=$('toast'); el.textContent=msg; el.hidden=false;
    window.clearTimeout(toast.timer); toast.timer=window.setTimeout(()=>el.hidden=true,4500);
  }
  function feedback(msg, bad=false) {
    const el=$('feedback'); el.hidden=false; el.textContent=msg;
    el.className='feedback '+(bad?'bad':'good');
  }
  function clearFeedback(){$('feedback').hidden=true;}
  const methodConfig = {
    biseccion:{name:'Bisección',value:'c',fx:'f(c)',formula:'c = <span class="fraction"><span>a + b</span><span>2</span></span>',
      description:'Escribe tu función, selecciona un intervalo válido y observa cómo converge a una raíz.',
      aria:'Fórmula del punto medio'},
    regla_falsa:{name:'Regla Falsa',value:'Xr',fx:'f(Xr)',
      formula:'Xr = b − <span class="fraction"><span>f(b) · (a − b)</span><span>f(a) − f(b)</span></span>',
      description:'Utiliza la interpolación lineal para aproximar la raíz y observa las secantes de cada iteración.',
      aria:'Fórmula del método de Regla Falsa'},
    newton_raphson:{name:'Newton-Raphson',value:'xₙ₊₁',fx:'f(xₙ₊₁)',
      formula:'x<sub>n+1</sub> = x<sub>n</sub> − <span class="fraction"><span>f(x<sub>n</sub>)</span><span>f′(x<sub>n</sub>)</span></span>',
      description:'Elige un punto inicial x₀ y observa cómo las tangentes se aproximan a una raíz.',
      aria:'Fórmula de Newton-Raphson'},
    secante:{name:'Secante',value:'xₙ₊₁',fx:'f(xₙ₊₁)',
      formula:'x<sub>n+1</sub> = x<sub>n</sub> − <span class="fraction"><span>f(x<sub>n</sub>) · (x<sub>n</sub> − x<sub>n−1</sub>)</span><span>f(x<sub>n</sub>) − f(x<sub>n−1</sub>)</span></span>',
      description:'Elige dos puntos iniciales x₀ y x₁ y observa las rectas secantes que aproximan la raíz.',
      aria:'Fórmula del método de la Secante'}
  };
  function currentMethod(){return methodConfig[state.method];}
  function isOpenMethod(){return state.method==='newton_raphson'||state.method==='secante';}
  function setMethodLabels(){
    const m=currentMethod(), falsa=state.method==='regla_falsa';
    const newton=state.method==='newton_raphson', secante=state.method==='secante';
    const abierto=isOpenMethod();
    $('breadcrumb-method').textContent=m.name;
    $('breadcrumb-family').textContent=abierto?'Métodos abiertos':'Métodos cerrados';
    const familyView = abierto ? 'methods-abiertos' : 'methods-cerrados';
    $('breadcrumb-family').dataset.view = familyView;
    $('solver-family-back').dataset.view = familyView;
    $('solver-family-back').textContent = '← Volver a métodos ' + (abierto ? 'abiertos' : 'cerrados');
    $('solver-category').textContent=(abierto?'MÉTODOS ABIERTOS':'MÉTODOS CERRADOS')+' · BÚSQUEDA DE RAÍCES';
    $('method-title').textContent=m.name;
    $('method-description').textContent=m.description;
    $('method-formula').innerHTML=m.formula;
    $('method-formula').setAttribute('aria-label',m.aria);
    $('method-formula').classList.toggle('formula-regla',falsa);
    $('method-formula').classList.toggle('formula-newton',newton);
    $('method-formula').classList.toggle('formula-secante',secante);
    $('setup-subtitle').textContent=secante?'Función y dos puntos iniciales':newton?'Función y punto inicial x₀':'Función e intervalo de búsqueda';
    $('selection-heading').textContent=abierto?'Selección de puntos iniciales':'Selección del intervalo';
    $('selection-hint').textContent=secante?'x₀, x₁':newton?'x₀':'a < b';
    $('interval-fields').hidden=abierto;
    $('newton-region').hidden=!abierto;
    $('secant-x1-region').hidden=!secante;
    $('max-iterations-region').hidden=!abierto;
    $('auto-region').hidden=abierto||state.mode!=='auto';
    $('manual-region').hidden=abierto||state.mode!=='manual';
    $('derivative-note').hidden=!newton||!$('derivative-value').hasChildNodes();
    $('precision-label').textContent=abierto?'Precisión (ambos criterios)':`Precisión |${m.fx}|`;
    $('summary-error-label').textContent=abierto?'RESIDUO |f(xₙ₊₁)|':`ERROR |${m.fx}|`;
    $('plot-legend-text').textContent=secante?'raíz / xₙ₊₁ · secante':newton?'raíz / xₙ · tangente':falsa?'raíz / Xr · secante':'raíz / c';
    $('plot-hint').textContent=secante
      ?'Selecciona una iteración para ver su secante. En modo manual, haz dos clics para elegir x₀ y x₁.'
      :newton?'Selecciona una iteración para ver la tangente. En modo manual, haz clic sobre la gráfica para elegir x₀.'
      :'Usa la rueda del mouse para ampliar. En modo manual, selecciona dos posiciones sobre la gráfica.';
    $('iterations-hint').textContent=secante
      ?'Selecciona una fila para visualizar la secante correspondiente a esa iteración.'
      :newton?'Selecciona una fila para visualizar la tangente correspondiente a esa iteración.'
      :'Selecciona una fila para visualizar el intervalo de esa iteración en la gráfica.';
    $('solve-btn').innerHTML=`Resolver por ${m.name} <span aria-hidden="true">→</span>`;
    $('iteration-table').querySelector('thead tr').innerHTML=secante
      ?'<th>It</th><th>x<sub>n−1</sub></th><th>x<sub>n</sub></th><th>f(x<sub>n−1</sub>)</th><th>f(x<sub>n</sub>)</th><th>x<sub>n+1</sub></th><th>Residuo = |f(x<sub>n+1</sub>)|</th><th>Cambio = |x<sub>n+1</sub> − x<sub>n</sub>|</th>'
      :newton?'<th>It</th><th>x<sub>n</sub></th><th>f(x<sub>n</sub>)</th><th>f′(x<sub>n</sub>)</th><th>x<sub>n+1</sub></th><th>Residuo = |f(x<sub>n+1</sub>)|</th><th>Cambio = |x<sub>n+1</sub> − x<sub>n</sub>|</th>'
      :falsa?'<th>It</th><th>a</th><th>b</th><th>f(a)</th><th>f(b)</th><th>Xr</th><th>f(Xr)</th><th>Error = |f(Xr)|</th><th>Decisión</th>'
      :'<th>It</th><th>a</th><th>b</th><th>c = (a+b)/2</th><th>f(a)</th><th>f(b)</th><th>f(c)</th><th>Error = |f(c)|</th><th>Decisión</th>';
    if(abierto)updateOpenModeHint();
  }
  function switchView(view) {
    state.view=view;
    document.querySelectorAll('.view').forEach(el=>el.hidden=el.id!==`view-${view}`);
    document.querySelectorAll('.navlink').forEach(el=>{
      const active=el.id===`nav-${view==='solver'||view==='iterative-workspace'||view.startsWith('methods-')?'methods':view==='linear-workspace'?'algebra':view==='complement-workspace'?'complementary':view}`;
      el.classList.toggle('is-current',active);
      if(active) el.setAttribute('aria-current','page'); else el.removeAttribute('aria-current');
    });
    window.scrollTo({top:0,behavior:'instant'});
    if(view==='solver') requestAnimationFrame(()=>{if(!state.preview)preview(); else drawPlot();});
  }
  function openMethod(method){
    if(!methodConfig[method])return;
    state.method=method;
    state.mode='auto';
    state.solution=null;
    state.selectedStep=null;
    state.selectedCandidate=null;
    state.clickStage=0;
    $('auto-btn').classList.add('active');$('manual-btn').classList.remove('active');
    $('auto-btn').setAttribute('aria-pressed','true');$('manual-btn').setAttribute('aria-pressed','false');
    renderDerivative(null);
    setMethodLabels();
    clearFeedback();
    resetResults();
    if(state.preview)renderCandidates();
    switchView('solver');
  }
  function toggleTheme(){
    state.theme=state.theme==='light'?'dark':'light';
    document.body.dataset.theme=state.theme;
    $('theme-switch').setAttribute('aria-label',state.theme==='light'?'Activar modo oscuro':'Activar modo claro');
    try{localStorage.setItem('chocolab-theme',state.theme);}catch(_){}
    if(state.view==='solver'&&state.preview)drawPlot();
  }
  function getFormula(){
    if(state.mathLive){return $('formula-math').value.trim();}
    return $('formula-plain').value.trim();
  }
  function setFormula(str){
    $('formula-plain').value=str;
    if(state.mathLive)$('formula-math').value=str;
  }
  function addKey(value){
    if(value==='CLEAR'){setFormula('');return;}
    if(state.mathLive){
      const mf=$('formula-math');
      if(value==='BACK') mf.executeCommand('deleteBackward');
      else {
        const latexMap={'pi':'\\pi','sqrt(':'\\sqrt{#0}','sin(':'\\sin(#0)','cos(':'\\cos(#0)',
          'tan(':'\\tan(#0)','ln(':'\\ln(#0)','log(':'\\log(#0)','exp(':'e^{#0}',
          'abs(':'\\left|#0\\right|','asin(':'\\arcsin(#0)','acos(':'\\arccos(#0)','atan(':'\\arctan(#0)',
          'x':'x','^2':'^{2}','^3':'^{3}','^':'^{#0}','*':'\\cdot','/':'\\frac{#@}{#0}'};
        mf.insert(latexMap[value]||value, {selectionMode:'placeholder'});
      }
      mf.focus();
    } else {
      const input=$('formula-plain'),a=input.selectionStart,b=input.selectionEnd,old=input.value;
      if(value==='BACK') {
        const first=a===b?Math.max(0,a-1):a;
        input.value=old.substring(0,first)+old.substring(b);
        input.setSelectionRange(first,first);
      } else {
        input.value=old.substring(0,a)+value+old.substring(b);
        input.setSelectionRange(a+value.length,a+value.length);
      }
      input.focus();
    }
  }
  function fillKeys(tab='basic'){
    document.querySelectorAll('.key-tab').forEach(b=>b.classList.toggle('active',b.dataset.keys===tab));
    const grid=$('keyboard-grid');grid.replaceChildren();
    for(const [label,value] of keyboardKeys[tab]){
      const btn=document.createElement('button');btn.type='button';btn.className='kbd-key';
      btn.textContent=label;btn.title=`Insertar ${label}`;
      btn.addEventListener('click',()=>addKey(value));grid.appendChild(btn);
    }
  }
  function initMathLive(){
    // Intentar MathLive local primero; si todavía no se ha preparado,
    // utilizar CDN. El teclado propio funciona incluso sin ninguno.
    const ready=()=>{
      if(!customElements.get('math-field'))return;
      const mf=$('formula-math');
      mf.value=$('formula-plain').value;
      mf.setAttribute('virtual-keyboard-mode','manual');
      mf.setAttribute('smart-fence','');
      mf.hidden=false;$('formula-plain').hidden=true;
      state.mathLive=true;
      mf.addEventListener('input',()=>{
        if(state.solution){state.solution=null;state.selectedStep=null;resetResults();}
        renderDerivative(null);
      });
      $('editor-hint').hidden=true;
      // Si MathLive termina de cargar después de la vista previa, mejora el formato de la derivada.
      if(state.method==='newton_raphson' && state.preview?.derivada_latex && getFormula()===state.formulaLast)
        renderDerivative(state.preview);
    };
    const external=()=>{
      const cdn=document.createElement('script');
      cdn.src='https://cdn.jsdelivr.net/npm/mathlive/mathlive.min.js';cdn.async=true;
      cdn.onload=ready;
      cdn.onerror=()=>{$('editor-hint').textContent='El teclado matemático propio está listo. Para un editor visual sin Internet, ejecuta PREPARAR_MATHLIVE_OFFLINE.bat.';};
      document.head.appendChild(cdn);
    };
    const local=document.createElement('script');
    local.src='/static/vendor/mathlive.min.js';local.async=true;
    local.onload=ready;local.onerror=external;
    document.head.appendChild(local);
  }
  function setPlotView(mode){
    state.plotView=mode;
    state.plotRevision+=1;
    updateFocusButtons();
    drawPlot();
  }
  function updateFocusButtons(){
    $('focus-roots').classList.toggle('active',state.plotView==='roots');
    $('focus-all').classList.toggle('active',state.plotView==='full');
  }
  function getRange(){
    const parts=$('range').value.split(/[,;]/).map(s=>Number(s.trim()));
    if(parts.length!==2||parts.some(x=>!Number.isFinite(x)))throw new Error('Escribe el rango gráfico como «-10, 10».');
    if(parts[0]>=parts[1])throw new Error('El rango debe tener un mínimo menor que el máximo.');
    return parts;
  }
  async function post(url,body){
    let response;
    try{
      response=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    }catch(_){throw Error('No hay conexión con Python. Comprueba que el servidor esté ejecutándose.');}
    let data;
    try{data=await response.json();}catch(_){throw Error('El servidor no respondió con datos válidos.');}
    if(!response.ok||!data.ok)throw Error(data.error||'Ocurrió un error inesperado.');
    return data;
  }
  function renderDerivative(data){
    const wrapper=$('derivative-note'), target=$('derivative-value');
    target.replaceChildren();
    wrapper.hidden=true;
    if(state.method!=='newton_raphson'||!data?.derivada_latex)return;

    const prefix=document.createElement('span');
    prefix.className='derivative-prefix';
    prefix.textContent='f′(x) =';
    target.appendChild(prefix);

    // MathLive ofrece una expresión tipografiada, sin operadores de código.
    // MathML nativo mantiene el formato incluso cuando se trabaja sin Internet.
    if(customElements.get('math-field')){
      const math=document.createElement('math-field');
      math.className='derivative-math';
      math.setAttribute('read-only','');
      math.setAttribute('virtual-keyboard-mode','off');
      math.setAttribute('aria-label','Expresión matemática de la derivada');
      target.appendChild(math);
      math.readOnly=true;
      math.value=data.derivada_latex;
    }else if(data.derivada_mathml){
      const math=document.createElement('span');
      math.className='derivative-mathml';
      // El MathML proviene de SymPy sobre expresiones admitidas por el parser seguro.
      math.innerHTML=`<math xmlns="http://www.w3.org/1998/Math/MathML" display="inline">${data.derivada_mathml}</math>`;
      target.appendChild(math);
    }else{
      // Respaldo accesible para una respuesta antigua sin MathML.
      const fallback=document.createElement('span');
      fallback.textContent=data.derivada_latex;
      target.appendChild(fallback);
    }
    wrapper.hidden=false;
  }

  async function preview(){
    clearFeedback();
    const btn=$('preview-btn');btn.disabled=true;btn.textContent='Calculando gráfica…';
    try{
      const [min,max]=getRange();
      const formula=getFormula(), metodo=state.method;
      const resp=await post('/api/preview',{formula,min,max,metodo});
      if(metodo!==state.method||state.view!=='solver')return;
      state.preview=resp;
      state.candidates=resp.candidatos;
      state.solution=null;
      state.selectedStep=null;
      state.selectedCandidate=null;
      state.clickStage=0;
      state.formulaLast=formula;
      renderDerivative(resp);
      state.plotView='roots';state.plotRevision+=1;updateFocusButtons();
      renderCandidates();
      resetResults();
      drawPlot();
      $('plot-status').textContent=`${state.candidates.length} candidato(s)`;
      if(state.candidates.length===0) feedback('No se detectaron intervalos candidatos en este rango. Puedes ampliar el rango o usar el modo manual.',false);
    }catch(err){feedback(err.message,true);}
    finally{btn.disabled=false;btn.textContent='↗   Graficar y buscar raíces';}
  }
  function chooseCandidate(index){
    const c=state.candidates[index];if(!c)return;
    if(state.solution){state.solution=null;state.selectedStep=null;resetResults();}
    state.selectedCandidate=index;
    document.querySelectorAll('.candidate').forEach(b=>b.classList.toggle('active',Number(b.dataset.index)===index));
    if(isOpenMethod()){
      // En Manual, seleccionar A/B/C no modifica los puntos escritos.
      if(state.mode==='auto'){
        if(state.method==='secante'){
          let x0=c.a, x1=c.b;
          if(x0===x1){
            const span=state.preview?.grafica?.max-state.preview?.grafica?.min||20;
            const delta=Math.max(0.01,Math.min(0.15,span/200));
            x0=c.estimado-delta;
            x1=c.estimado+delta*.6;
          }
          $('val-x0').value=Number(x0.toPrecision(13));
          $('val-x1').value=Number(x1.toPrecision(13));
        }else $('val-x0').value=Number(c.estimado.toPrecision(12)).toString();
      }
      updateOpenModeHint();
    }else if(c.exacta){
      const span=(state.preview.grafica.max-state.preview.grafica.min)/2400;
      const b=c.a+Math.max(span,0.00001);
      $('val-a').value=fmt(c.a,12);$('val-b').value=fmt(b,12);
    }else{
      $('val-a').value=fmt(c.a,12);$('val-b').value=fmt(c.b,12);
    }
    if(state.preview)drawPlot();
  }
  function renderCandidates(){
    const buildList=(el,abierto)=>{
      el.replaceChildren();
      if(!state.candidates.length){
        el.innerHTML=abierto
          ?'<div class="empty-note">No se detectaron posibles raíces. Amplía el rango o usa Manual para introducir los puntos iniciales.</div>'
          :'<div class="empty-note">No se detectaron intervalos candidatos en este rango. Amplía la búsqueda o usa Manual.</div>';
        return;
      }
      for(const [idx,c] of state.candidates.entries()){
        const b=document.createElement('button');b.type='button';b.dataset.index=String(idx);b.className='candidate';
        if(abierto&&state.mode==='manual'){
          b.innerHTML=`<span class="candidate-letter">${escapeHtml(c.etiqueta)}</span><span class="candidate-data"><strong>Raíz ${escapeHtml(c.etiqueta)}</strong></span>`;
        }else{
          b.innerHTML=`<span class="candidate-letter">${escapeHtml(c.etiqueta)}</span><span class="candidate-data"><strong>Raíz ${escapeHtml(c.etiqueta)} · x ≈ ${fmt(c.estimado,6)}</strong><small>${c.exacta?'Cero detectado en muestreo':abierto?'Candidato detectado cerca de este punto':`Intervalo [${fmt(c.a,6)}, ${fmt(c.b,6)}]`}</small></span>`;
        }
        b.classList.toggle('active',idx===state.selectedCandidate);
        b.addEventListener('click',()=>chooseCandidate(idx));el.appendChild(b);
      }
    };
    buildList($('candidate-list'),false);
    buildList($('newton-candidate-list'),true);
    if(state.mode==='auto'&&state.candidates.length)chooseCandidate(state.selectedCandidate??0);
    else updateOpenModeHint();
  }
  function updateOpenModeHint(){
    const manual=state.mode==='manual', secante=state.method==='secante';
    $('val-x0').disabled=!manual;
    $('val-x1').disabled=!manual;
    $('newton-mode-hint').textContent=secante
      ?(manual
        ?'Introducí libremente x₀ y x₁ (distintos). También podés seleccionarlos con dos clics en la gráfica.'
        :'Seleccioná una posible raíz. Choco Lab propondrá x₀ y x₁; no garantiza la convergencia a esa raíz.')
      :(manual
        ?'Escribí x₀ libremente o seleccioná antes una raíz candidata. También podés elegir x₀ con un clic en la gráfica.'
        :'Seleccioná una raíz A, B o C. Choco Lab propondrá automáticamente un x₀ cercano.');
  }
  function setMode(mode){
    state.mode=mode;
    $('auto-btn').classList.toggle('active',mode==='auto');
    $('manual-btn').classList.toggle('active',mode==='manual');
    $('auto-btn').setAttribute('aria-pressed',String(mode==='auto'));
    $('manual-btn').setAttribute('aria-pressed',String(mode==='manual'));
    const abierto=isOpenMethod();
    $('auto-region').hidden=abierto||mode!=='auto';
    $('manual-region').hidden=abierto||mode!=='manual';
    if(abierto){
      updateOpenModeHint();
      renderCandidates(); // Manual: A/B/C sin mostrar la aproximación.
    }
    state.clickStage=0;
    if(mode==='auto' && state.candidates.length){chooseCandidate(state.selectedCandidate??0);}
    else if(state.preview)drawPlot();
    toast(abierto
      ?(mode==='manual'
        ?(state.method==='secante'?'Modo manual: indicá x₀ y x₁, o elegilos con dos clics.':'Modo manual: elegí libremente x₀.')
        :(state.method==='secante'?'Modo automático: seleccioná una raíz para sugerir x₀ y x₁.':'Modo automático: seleccioná una raíz para sugerir x₀.'))
      :(mode==='manual'?'Modo manual: introduce a y b o haz clic dos veces en la gráfica.':'Modo automático: elige un candidato de la lista.'));
  }
  function css(name){return getComputedStyle(document.body).getPropertyValue(name).trim();}
  function drawPlot(){
    if(!state.preview||typeof Plotly==='undefined'||$('view-solver').hidden)return;
    const gd=$('plot'),p=state.preview.grafica;
    const newton=state.method==='newton_raphson',secante=state.method==='secante',abierto=isOpenMethod();
    let a=Number($('val-a').value),b=Number($('val-b').value);
    const validAB=!abierto&&Number.isFinite(a)&&Number.isFinite(b)&&a<b;
    const row=state.solution?.filas?.length
      ? (state.selectedStep!==null ? state.solution.filas[state.selectedStep]
         : state.method==='regla_falsa' ? state.solution.filas.at(-1) : null) : null;
    if(row&&!abierto){a=row.a;b=row.b;}
    const x0Input=$('val-x0').value,x1Input=$('val-x1').value;
    const pointX=row&&newton?row.xn:row&&secante?row.xprev:(x0Input!==''?Number(x0Input):NaN);
    const pointX1=row&&secante?row.xn:(x1Input!==''?Number(x1Input):NaN);
    const validX0=abierto&&Number.isFinite(pointX);
    const validX1=secante&&Number.isFinite(pointX1);
    const traces=[{
      x:p.x,y:p.y,type:'scatter',mode:'lines',name:'f(x)',
      line:{color:css('--plot'),width:3},hovertemplate:'x = %{x:.5f}<br>f(x) = %{y:.6g}<extra></extra>',connectgaps:false
    }];
    if(state.candidates.length){
      traces.push({x:state.candidates.map(c=>c.estimado),y:state.candidates.map(()=>0),
        type:'scatter',mode:'markers+text',name:'Candidatos',text:state.candidates.map(c=>c.etiqueta),
        textposition:'top center',textfont:{size:13,color:css('--accent')},
        marker:{color:css('--accent'),size:10,line:{width:2,color:css('--surface')}},
        hovertemplate:'Posible raíz %{text}<extra></extra>'});
    }
    if(row && newton){
      const pad=Math.max(Math.min((p.max-p.min)*.045,1.0),Math.abs(row.xnext-row.xn)*.35,0.28);
      const xleft=Math.min(row.xn,row.xnext)-pad;
      const xright=Math.max(row.xn,row.xnext)+pad;
      const tangentY=x=>row.fxn+row.dfxn*(x-row.xn);
      traces.push({x:[xleft,xright],y:[tangentY(xleft),tangentY(xright)],type:'scatter',mode:'lines',
        name:'Recta tangente',line:{color:'#df8e4c',width:3},hovertemplate:'Recta tangente<extra></extra>'});
      traces.push({x:[row.xn],y:[row.fxn],type:'scatter',mode:'markers',name:'Punto de tangencia',
        marker:{color:'#df8e4c',size:13,line:{color:css('--surface'),width:2}},
        hovertemplate:'xₙ=%{x:.9f}<br>f(xₙ)=%{y:.6g}<extra></extra>'});
      traces.push({x:[row.xnext],y:[0],type:'scatter',mode:'markers',name:'Intersección xₙ₊₁',
        marker:{color:'#3c95a0',size:12,line:{color:css('--surface'),width:2}},
        hovertemplate:'xₙ₊₁=%{x:.9f}<extra></extra>'});
    }else if(row && secante){
      const m=(row.fxn-row.fxprev)/(row.xn-row.xprev);
      const pad=Math.max(Math.min((p.max-p.min)*.025,0.6),Math.abs(row.xn-row.xprev)*.08,0.1);
      const left=Math.min(row.xprev,row.xn,row.xnext)-pad;
      const right=Math.max(row.xprev,row.xn,row.xnext)+pad;
      const secanteY=x=>row.fxprev+m*(x-row.xprev);
      traces.push({x:[left,right],y:[secanteY(left),secanteY(right)],type:'scatter',mode:'lines',
        name:'Recta secante',line:{color:'#df8e4c',width:3},
        hovertemplate:'Recta secante<extra></extra>'});
      traces.push({x:[row.xprev,row.xn],y:[row.fxprev,row.fxn],type:'scatter',mode:'markers',
        name:'Puntos de la secante',marker:{color:'#df8e4c',size:11,line:{color:css('--surface'),width:2}},
        hovertemplate:'Punto inicial: x=%{x:.8f}<br>f(x)=%{y:.6g}<extra></extra>'});
      traces.push({x:[row.xnext],y:[0],type:'scatter',mode:'markers',name:'Intersección xₙ₊₁',
        marker:{color:'#3c95a0',size:13,line:{color:css('--surface'),width:2}},
        hovertemplate:'xₙ₊₁=%{x:.9f}<extra></extra>'});
      traces.push({x:[row.xnext,row.xnext],y:[0,row.fxnext],type:'scatter',mode:'lines',
        name:'Residuo vertical',line:{color:'#3c95a0',width:1.6,dash:'dot'},hoverinfo:'skip'});
    }else if(row && state.method==='regla_falsa'){
      // La secante representa la interpolación real entre (a,f(a)) y (b,f(b)).
      traces.push({x:[row.a,row.b],y:[row.fa,row.fb],type:'scatter',mode:'lines',name:'Recta secante',
        line:{color:'#df8e4c',width:2.5,dash:'solid'},
        hovertemplate:'Secante<br>x=%{x:.6f}<br>y=%{y:.6f}<extra></extra>'});
      traces.push({x:[row.xr,row.xr],y:[0,row.fxr],type:'scatter',mode:'lines',name:'Error vertical',
        line:{color:'#3c95a0',width:1.8,dash:'dot'},hoverinfo:'skip'});
      traces.push({x:[row.xr],y:[0],type:'scatter',mode:'markers',name:'Xr: intersección',
        marker:{color:'#df8e4c',size:12,line:{color:css('--surface'),width:2}},
        hovertemplate:'Xr = %{x:.9f}<br>Intersección de la secante<extra></extra>'});
      traces.push({x:[row.xr],y:[row.fxr],type:'scatter',mode:'markers',name:'f(Xr)',
        marker:{color:'#3c95a0',size:11,line:{color:css('--surface'),width:2}},
        hovertemplate:'Xr=%{x:.9f}<br>f(Xr)=%{y:.7g}<extra></extra>'});
    }else if(row){
      traces.push({x:[row.c],y:[row.fc],type:'scatter',mode:'markers',name:'Punto c',
        marker:{color:'#df8e4c',size:13,line:{color:css('--surface'),width:3}},
        hovertemplate:'c=%{x:.8f}<br>f(c)=%{y:.7g}<extra></extra>'});
    }else if(state.solution){
      traces.push({x:[state.solution.raiz],y:[0],type:'scatter',mode:'markers',name:'Raíz aproximada',
        marker:{color:'#4d997b',size:14,line:{color:css('--surface'),width:3}},
        hovertemplate:'Raíz ≈ %{x:.8f}<extra></extra>'});
    }
    // Vista enfocada en las raíces para evitar que los valores enormes de
    // los extremos aplasten visualmente los cruces con el eje X.
    let xrange=[p.min,p.max],yrange=null;
    if(state.plotView==='roots' && state.candidates.length){
      const first=state.candidates[0].estimado;
      const last=state.candidates[state.candidates.length-1].estimado;
      const span=Math.max(1,last-first);
      const pad=Math.max(0.8,Math.min(2,span*0.17));
      xrange=[Math.max(p.min,first-pad),Math.min(p.max,last+pad)];
      const values=p.x.map((x,i)=>x>=xrange[0]&&x<=xrange[1]?p.y[i]:null)
        .filter(v=>v!==null&&Number.isFinite(v)).sort((a,b)=>a-b);
      if(values.length>20){
        const lo=values[Math.floor(values.length*.06)],hi=values[Math.floor(values.length*.91)];
        const margin=Math.max(1,(hi-lo)*.17);
        yrange=[Math.min(lo-margin,-margin),Math.max(hi+margin,margin)];
      }
    }
    const layout={paper_bgcolor:css('--surface'),plot_bgcolor:css('--surface'),
      margin:{l:55,r:25,t:32,b:47},showlegend:false,hovermode:'closest',
      clickanywhere:true,
      xaxis:{title:{text:'x',font:{size:12}},gridcolor:css('--grid'),zerolinecolor:css('--ink-muted'),color:css('--ink-muted'),range:xrange,automargin:true},
      yaxis:{title:{text:'f(x)',font:{size:12}},gridcolor:css('--grid'),zerolinecolor:css('--ink-muted'),color:css('--ink-muted'),range:yrange||undefined,automargin:true},
      font:{family:'DM Sans, Segoe UI, Arial',color:css('--ink')},
      shapes:validX0?[
        {type:'line',xref:'x',yref:'paper',x0:pointX,x1:pointX,y0:0,y1:1,line:{color:'#3c95a0',width:2,dash:'dash'}},
        ...(validX1?[{type:'line',xref:'x',yref:'paper',x0:pointX1,x1:pointX1,y0:0,y1:1,line:{color:'#d68b54',width:2,dash:'dash'}}]:[])
      ]:validAB?[
        {type:'rect',xref:'x',yref:'paper',x0:a,x1:b,y0:0,y1:1,fillcolor:css('--accent'),opacity:.09,line:{width:0},layer:'below'},
        {type:'line',xref:'x',yref:'paper',x0:a,x1:a,y0:0,y1:1,line:{color:'#3c95a0',width:2,dash:'dash'}},
        {type:'line',xref:'x',yref:'paper',x0:b,x1:b,y0:0,y1:1,line:{color:'#d68b54',width:2,dash:'dash'}}
      ]:[],
      annotations:validX0?[
        {xref:'x',yref:'paper',x:pointX,y:1,showarrow:false,text:row&&secante?'xₙ₋₁':row?'xₙ':'x₀',font:{color:'#3c95a0',size:13},yshift:7},
        ...(validX1?[{xref:'x',yref:'paper',x:pointX1,y:1,showarrow:false,text:row?'xₙ':'x₁',font:{color:'#d68b54',size:13},yshift:7}]:[])
      ]:validAB?[
        {xref:'x',yref:'paper',x:a,y:1,showarrow:false,text:'a',font:{color:'#3c95a0',size:13},yshift:7},
        {xref:'x',yref:'paper',x:b,y:1,showarrow:false,text:'b',font:{color:'#d68b54',size:13},yshift:7}
      ]:[],uirevision:state.formulaLast+'|'+p.min+'|'+p.max+'|'+state.plotRevision};
    Plotly.react(gd,traces,layout,{responsive:true,displaylogo:false,scrollZoom:true,modeBarButtonsToRemove:['lasso2d','select2d']}).then(()=>{
      if(!gd._chocolabBound){
        gd._chocolabBound=true;
        gd.on('plotly_click',plotClicked);
      }
    });
  }
  function plotClicked(event){
    if(state.method==='secante' && state.mode==='manual'){
      let x=event.xvals?.[0];
      if(!Number.isFinite(x))x=event.points?.[0]?.x;
      if(!Number.isFinite(x))return;
      x=Number(x.toFixed(7));
      if(state.clickStage===0){
        $('val-x0').value=x;state.clickStage=1;
        toast(`Primer punto x₀ = ${x}. Elegí el segundo punto x₁.`);
      }else{
        $('val-x1').value=x;state.clickStage=0;
        toast('Dos puntos iniciales seleccionados. Podés resolver.');
      }
      if(state.solution){state.solution=null;state.selectedStep=null;resetResults();}
      drawPlot();return;
    }
    if(state.method==='newton_raphson' && state.mode==='manual'){
      let x=event.xvals?.[0];
      if(!Number.isFinite(x))x=event.points?.[0]?.x;
      if(!Number.isFinite(x))return;
      $('val-x0').value=Number(x.toFixed(7));
      if(state.solution){state.solution=null;state.selectedStep=null;resetResults();}
      toast(`Punto inicial x₀ = ${$('val-x0').value}. Ya podés resolver.`);
      drawPlot();return;
    }
    if(state.mode!=='manual'){
      if(event.points?.[0]){
        const x=Number(event.points[0].x);
        const idx=state.candidates.findIndex(c=>Math.abs(c.estimado-x)<1e-8);
        if(idx>=0) chooseCandidate(idx);
      }
      return;
    }
    let x=event.xvals?.[0];
    if(!Number.isFinite(x))x=event.points?.[0]?.x;
    if(!Number.isFinite(x))return;
    x=Number(x.toFixed(6));
    if(state.clickStage===0){$('val-a').value=x;state.clickStage=1;toast(`Primer extremo registrado: ${x}. Selecciona ahora el segundo.`);}
    else{
      let a=Number($('val-a').value);
      $('val-a').value=Math.min(a,x);$('val-b').value=Math.max(a,x);
      state.clickStage=0;toast('Intervalo seleccionado. Puedes pulsar Resolver.');
    }
    drawPlot();
  }
  function resetResults(){
    $('summary-root').textContent='—';$('summary-iterations').textContent='—';$('summary-error').textContent='—';
    const m=currentMethod(),abierto=isOpenMethod();
    $('summary-root-sub').textContent='Pendiente de resolver';
    $('summary-iterations-sub').textContent='Convergencia';
    $('summary-error-sub').textContent=abierto?'Residuo absoluto |f(xₙ₊₁)|':`Error = |${m.fx}|`;
    $('iteration-body').innerHTML=`<tr><td colspan="${abierto?(state.method==='secante'?8:7):9}" class="empty-cell">Completa los datos y pulsa «Resolver por ${m.name}» para ver las iteraciones.</td></tr>`;
    $('prev-step').disabled=true;$('next-step').disabled=true;$('show-all').disabled=true;$('csv-btn').disabled=true;
    $('step-counter').textContent='';
    $('result-explanation').textContent=abierto
      ?`${m.name} verifica dos criterios: residuo |f(xₙ₊₁)| y cambio |xₙ₊₁ − xₙ|. Ambos deben ser menores o iguales que la precisión.`
      :`La columna Error muestra |${m.fx}| en cada iteración. El método se detiene cuando el residuo es menor o igual que la precisión indicada.`;
  }
  async function solve(){
    clearFeedback();
    const btn=$('solve-btn'),formula=getFormula(),metodo=state.method;
    btn.disabled=true;btn.textContent='Resolviendo…';
    try{
      if(!state.preview||formula!==state.formulaLast){
        const [min,max]=getRange();
        const resp=await post('/api/preview',{formula,min,max,metodo});
        if(metodo!==state.method||state.view!=='solver')return;
        state.preview=resp;state.formulaLast=formula;state.candidates=resp.candidatos;state.solution=null;
        state.selectedCandidate=null;
        renderCandidates();
      }
      const newton=metodo==='newton_raphson',secante=metodo==='secante',abierto=newton||secante;
      if(abierto&&state.mode==='auto'&&state.selectedCandidate===null)
        throw Error('En modo automático seleccioná una raíz candidata, o cambiá a Manual para escribir los valores iniciales.');
      const body={formula,metodo,tolerancia:$('precision').value};
      if(abierto){
        body.x0=$('val-x0').value;
        body.max_it=$('max-iterations').value;
        if(secante)body.x1=$('val-x1').value;
      }else {body.a=$('val-a').value;body.b=$('val-b').value;}
      const chosenIndex=state.selectedCandidate;
      const rootsBefore=state.candidates;
      const result=await post('/api/solve',body);
      if(metodo!==state.method||state.view!=='solver')return;
      state.solution=result;state.selectedStep=null;
      $('summary-root').textContent=fmt(result.raiz,10);
      $('summary-iterations').textContent=String(result.iteraciones);
      $('summary-error').textContent=abierto?fmtResiduo(result.residuo):fmt(result.residuo,10);
      const m=currentMethod();
      $('summary-root-sub').textContent=`Aproximación obtenida por ${m.name}`;
      $('summary-iterations-sub').textContent=`${m.name} en Python`;
      $('summary-error-sub').textContent=`Residuo absoluto |${m.fx}|`;
      $('result-explanation').textContent=abierto
        ?result.motivo+` · Residuo: ${fmtResiduo(result.residuo)} · Cambio: ${fmt(result.cambio,10)}. Ambos se contrastan con la tolerancia.`
        :result.motivo+` · La columna Error representa el valor absoluto de ${m.fx} en cada iteración.`;
      // La derivada solo se muestra al usar «Graficar y buscar raíces».
      renderTable(result.filas);
      $('prev-step').disabled=true;
      $('next-step').disabled=result.filas.length===0;
      $('show-all').disabled=result.filas.length===0;
      $('csv-btn').disabled=false;
      let msg=result.convergencia===false
        ?`${result.motivo} No se alcanzaron ambos criterios.`
        :'Cálculo realizado correctamente. Selecciona una iteración para ver su representación en la gráfica.';
      let warning=result.convergencia===false;
      if(abierto && chosenIndex!==null && result.convergencia!==false && rootsBefore.length>1){
        const nearest=rootsBefore.reduce((best,c,i)=>Math.abs(c.estimado-result.raiz)<Math.abs(rootsBefore[best].estimado-result.raiz)?i:best,0);
        if(nearest!==chosenIndex){
          warning=true;
          msg=`La iteración convergió cerca de la raíz ${rootsBefore[nearest].etiqueta}, distinta de la raíz ${rootsBefore[chosenIndex].etiqueta} seleccionada. Cambia los puntos iniciales para intentar otra raíz.`;
        }
      }
      feedback(msg,warning);
      if(abierto && result.filas.length){selectStep(0);}else drawPlot();
      if(window.innerWidth<840)$('iterations-section').scrollIntoView({behavior:'smooth',block:'start'});
    }catch(err){feedback(err.message,true);}
    finally{btn.disabled=false;btn.textContent=`Resolver por ${currentMethod().name}  →`;}
  }
  function renderTable(rows){
    const body=$('iteration-body'),newton=state.method==='newton_raphson',secante=state.method==='secante',abierto=isOpenMethod();
    if(!rows.length){
      body.innerHTML=`<tr><td colspan="${secante?8:newton?7:9}" class="empty-cell">${abierto?'Uno de los puntos iniciales ya es una raíz. No se necesitan iteraciones.':'La raíz ya coincide con un extremo. No se necesitan iteraciones.'}</td></tr>`;
      return;
    }
    const falsa=state.method==='regla_falsa';
    body.innerHTML=rows.map((r,i)=>{
      const cells=secante
        ?[r.it,fmt(r.xprev,10),fmt(r.xn,10),fmt(r.fxprev,9),fmt(r.fxn,9),fmt(r.xnext,10),fmtResiduo(r.residuo),fmt(r.cambio,10)]
        :newton
        ?[r.it,fmt(r.xn,10),fmt(r.fxn,9),fmt(r.dfxn,9),fmt(r.xnext,10),fmtResiduo(r.residuo),fmt(r.cambio,10)]
        :falsa
        ?[r.it,fmt(r.a),fmt(r.b),fmt(r.fa,7),fmt(r.fb,7),fmt(r.xr,10),fmt(r.fxr,7),fmt(r.error,9),escapeHtml(r.decision)]
        :[r.it,fmt(r.a),fmt(r.b),fmt(r.c,10),fmt(r.fa,7),fmt(r.fb,7),fmt(r.fc,7),fmt(r.error,9),escapeHtml(r.decision)];
      return `<tr data-iteration="${i}" tabindex="0" aria-label="Mostrar iteración ${r.it}">${cells.map(v=>`<td>${v}</td>`).join('')}</tr>`;
    }).join('');
    body.querySelectorAll('[data-iteration]').forEach(el=>{
      el.addEventListener('click',()=>selectStep(Number(el.dataset.iteration)));
      el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();selectStep(Number(el.dataset.iteration));}});
    });
  }
  function selectStep(index){
    if(!state.solution?.filas?.length)return;
    if(index===null){state.selectedStep=null;}
    else state.selectedStep=Math.max(0,Math.min(index,state.solution.filas.length-1));
    document.querySelectorAll('[data-iteration]').forEach(el=>el.classList.toggle('selected',Number(el.dataset.iteration)===state.selectedStep));
    $('prev-step').disabled=state.selectedStep===null||state.selectedStep===0;
    $('next-step').disabled=state.selectedStep===state.solution.filas.length-1;
    $('step-counter').textContent=state.selectedStep===null?'Todas las iteraciones':`Iteración ${state.selectedStep+1} de ${state.solution.filas.length}`;
    drawPlot();
    if(state.selectedStep!==null){
      const tr=document.querySelector(`[data-iteration="${state.selectedStep}"]`);
      if(tr&&tr.getBoundingClientRect().bottom>window.innerHeight)tr.scrollIntoView({behavior:'smooth',block:'nearest'});
    }
  }
  function exportCsv(){
    if(!state.solution)return;
    const newton=state.method==='newton_raphson',secante=state.method==='secante',abierto=isOpenMethod(),falsa=state.method==='regla_falsa';
    const cols=secante?['it','xprev','xn','fxprev','fxn','xnext','residuo','cambio']
      :newton?['it','xn','fxn','dfxn','xnext','residuo','cambio']
      :falsa?['it','a','b','fa','fb','xr','fxr','error','decision']:['it','a','b','c','fa','fb','fc','error','decision'];
    const heads=secante?['It','x_(n-1)','x_n','f(x_(n-1))','f(x_n)','x_(n+1)','Residuo = |f(x_(n+1))|','Cambio = |x_(n+1)-x_n|']
      :newton?['It','x_n','f(x_n)',"f'(x_n)",'x_(n+1)','Residuo = |f(x_(n+1))|','Cambio = |x_(n+1)-x_n|']
      :falsa?['It','a','b','f(a)','f(b)','Xr','f(Xr)','Error = |f(Xr)|','Decisión']
      :['It','a','b','c = (a+b)/2','f(a)','f(b)','f(c)','Error = |f(c)|','Decisión'];
    const csv=[heads.join(';'),...state.solution.filas.map(row=>cols.map(k=>
      String(abierto && k==='residuo' && row[k]===0 ? 'Exacto o límite numérico' : row[k]).replaceAll(';',',')
    ).join(';'))].join('\r\n');
    const blob=new Blob(['\uFEFF'+csv],{type:'text/csv;charset=utf-8;'}),url=URL.createObjectURL(blob);
    const a=document.createElement('a');a.href=url;a.download=`chocolab_${state.method}_iteraciones.csv`;a.click();
    setTimeout(()=>URL.revokeObjectURL(url),4000);
  }
  function init(){
    try{state.theme=localStorage.getItem('chocolab-theme')==='dark'?'dark':'light';}catch(_){state.theme='light';}
    document.body.dataset.theme=state.theme;
    document.querySelectorAll('[data-view]').forEach(btn=>btn.addEventListener('click',()=>switchView(btn.dataset.view)));
    document.querySelectorAll('[data-method]').forEach(btn=>btn.addEventListener('click',()=>openMethod(btn.dataset.method)));
    setMethodLabels();
    $('theme-switch').addEventListener('click',toggleTheme);
    $('keyboard-toggle').addEventListener('click',()=>{
      const el=$('keyboard');el.hidden=!el.hidden;
      $('keyboard-toggle').setAttribute('aria-expanded',String(!el.hidden));
    });
    document.querySelectorAll('.key-tab').forEach(btn=>btn.addEventListener('click',()=>fillKeys(btn.dataset.keys)));
    fillKeys();
    $('preview-btn').addEventListener('click',preview);
    $('focus-roots').addEventListener('click',()=>setPlotView('roots'));
    $('focus-all').addEventListener('click',()=>setPlotView('full'));
    $('auto-btn').addEventListener('click',()=>setMode('auto'));
    $('manual-btn').addEventListener('click',()=>setMode('manual'));
    for(const key of ['val-a','val-b','val-x0','val-x1','max-iterations']){
      $(key).addEventListener('change',()=>{
        if(state.solution){state.solution=null;state.selectedStep=null;resetResults();}
        if(state.preview)drawPlot();
      });
    }
    $('formula-plain').addEventListener('input',()=>{
      if(state.solution){state.solution=null;state.selectedStep=null;resetResults();}
      if(state.method==='newton_raphson')renderDerivative(null);
    });
    $('solve-btn').addEventListener('click',solve);
    $('prev-step').addEventListener('click',()=>selectStep((state.selectedStep??1)-1));
    $('next-step').addEventListener('click',()=>selectStep((state.selectedStep??-1)+1));
    $('show-all').addEventListener('click',()=>selectStep(null));
    $('csv-btn').addEventListener('click',exportCsv);
    document.querySelector('.navlink.is-current')?.setAttribute('aria-current','page');
    initMathLive();
  }
  document.addEventListener('DOMContentLoaded',init);
})();
