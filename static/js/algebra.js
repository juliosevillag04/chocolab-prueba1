import {h, matrix, lesson, setFormat, detName} from './algebra_resultados.js';

const $ = id => document.getElementById(id);
const view = $('view-linear-workspace');
const controls = $('lab-controls');
const copy = matrix => matrix.map(row => row.map(String));
const resize = (old, rows, cols, fill='0') => Array.from({length:rows}, (_,i) =>
  Array.from({length:cols}, (_,j) => old[i]?.[j] ?? fill));
const initialA = [[2,1,-1],[-3,-1,2],[-2,1,2]];
const initialB = [[8],[-11],[-3]];
const exampleObjects = [
  {nombre:'A',tipo:'Matriz',valores:[[1,2],[3,4]]}, {nombre:'u',tipo:'Vector',valores:[[2],[1]]},
  {nombre:'v',tipo:'Vector',valores:[[1],[3]]}, {nombre:'b',tipo:'Vector',valores:[[11],[25]]}
];
const bank = exampleObjects.map(o => ({...o, valores:copy(o.valores)}));
const sys = {A:copy(initialA), b:copy(initialB), entry:'cells', method:'gauss_jordan',
  names:['x1','x2','x3'], equations:[]};
const det = {A:copy(initialA), method:'sarrus'};
const comb = {mode:'objetivo',target:'b',selected:['u','v']};
const state = {tool:'sistemas',coord:1,format:'fraction',rich:false,expr:'A(u+v)',editor:null,
  result:null,lesson:null,step:0,revision:0,focus:null,busy:false};
const info = {
  sistemas:{title:'Sistemas lineales', icon:'[A | b]', lead:'Sigue los pivotes, las operaciones por filas y la clasificación del sistema.',
    input:'Datos del sistema', hint:'Elige el procedimiento y escribe los coeficientes o las ecuaciones.', steps:'Reducción del sistema'},
  operaciones:{title:'Operaciones matriciales y vectoriales', icon:'A(u + v)', lead:'Define tus matrices y vectores, combínalos en una expresión y examina cada operación.',
    input:'Banco de matrices y vectores',hint:'Abre un objeto para editar sus entradas o crea uno para tu expresión.', steps:'Evaluación de la expresión'},
  combinaciones:{title:'Combinaciones lineales',icon:'Σ cᵢvᵢ',lead:'Busca los coeficientes que permiten construir un vector a partir de otros.',
    input:'Objetivo y generadores',hint:'Edita los componentes en las tarjetas. Los vectores se comparten con el banco de operaciones.',steps:'Sistema de coeficientes'},
  determinantes:{title:'Determinantes',icon:'det(A)',lead:'Sigue las diagonales, los menores o la triangularización de tu matriz.',
    input:'Matriz y método de cálculo',hint:'Ajusta el orden, llena la matriz cuadrada y elige cómo desarrollar el determinante.',steps:'Desarrollo del determinante'}
};
const systemMethods = {gauss_jordan:'Gauss-Jordan',gauss:'Gauss',lu:'Resolver Ax = b por LU',factorizar:'Factorizar A = LU'};
const squareSystem = () => ['lu','factorizar'].includes(sys.method);
const object = name => bank.find(o => o.nombre===name);
const vectors = () => bank.filter(o => o.tipo==='Vector');
const numeric = /^[+-]?(?:\d+\/[1-9]\d*|(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)$/i;
const norm = s => String(s).trim().replace(/−/g,'-').replace(',','.');
const dimLabel = A => A.length+' × '+A[0].length;
const button = (text,action) => `<button type="button" class="ax-small" data-action="${action}">${h(text)}</button>`;
const choice = (id,options,current,label) => `<label class="ax-field" for="${id}"><span>${h(label)}</span><select id="${id}">${options.map(([v,t]) =>
  `<option value="${h(v)}" ${String(v)===String(current)?'selected':''}>${h(t)}</option>`).join('')}</select></label>`;
const sizeChoice = (id,current,label,max=15) => choice(id,Array.from({length:max},(_,i)=>[i+1,i+1]),current,label);
const group = (name,choices,current) => `<div class="ax-segments" role="group" aria-label="${h(name)}">${choices.map(([action,value,label])=>
  `<button type="button" data-action="${action}" data-value="${value}" aria-pressed="${value===current}">${h(label)}</button>`).join('')}</div>`;
const lookupGrid = key => {
  if (key==='A') return state.tool==='determinantes'?det.A:sys.A;
  if (key==='b') return sys.b;
  if (key==='draft') return state.editor?.valores;
  if (key.startsWith('v:')) return object(key.slice(2))?.valores;
};
function coordinate(name,i,j) {
  return state.coord===1 ? `${name}(${i+1},${j+1})` : `${name}[${i}][${j}]`;
}
function inputCell(key,name,data,i,j) {
  const label=coordinate(name,i,j);
  return `<input class="ax-cell" type="text" data-grid="${h(key)}" data-row="${i}" data-col="${j}"
    aria-label="${h(label)}" title="${h(label)}" value="${h(data[i][j])}" placeholder="—" spellcheck="false" autocomplete="off">`;
}
function grid(key,name,data,{rhs,columns,title=name}={}) {
  const cols=data[0].length, base=state.coord;
  const heads=data[0].map((_,j)=>`<th scope="col">${h(columns?.[j]||('C'+(j+base)))}</th>`).join('');
  const rows=data.map((row,i)=>`<tr><th scope="row">F${i+base}</th>${row.map((_,j)=>
    '<td>'+inputCell(key,name,data,i,j)+'</td>').join('')}${rhs?'<td class="ax-rhs">'+inputCell('b','b',rhs,i,0)+'</td>':''}</tr>`).join('');
  return `<div class="ax-grid-box"><div class="ax-grid-head"><h3>${h(title)}</h3><span>${data.length} × ${cols+(rhs?1:0)}</span></div>
    <div class="ax-grid-scroll"><table class="ax-entry-table" aria-label="${h(title)}"><thead><tr><th></th>${heads}${rhs?'<th scope="col" class="ax-rhs">b</th>':''}</tr></thead><tbody>${rows}</tbody></table></div></div>`;
}
const gridHelp = 'Admite enteros, decimales y fracciones como 3/4. Puedes pegar varias filas desde Excel.';
function reading() {
  return sys.A.map((row,i)=>{
    const terms=[];
    row.forEach((v,j)=>{
      const raw=norm(v).replace(/^\+/,'');
      if (raw==='0'||raw==='-0') return;
      const negative=raw.startsWith('-'), magnitude=raw.replace(/^-/,'');
      const sign=negative?' − ':terms.length?' + ':'';
      terms.push(sign+(magnitude==='1'?'':magnitude||'□')+sys.names[j]);
    });
    return '<li>'+h((terms.join('').trim()||'0')+' = '+(sys.b[i][0]||'□'))+'</li>';
  }).join('');
}
function systems() {
  const factor=sys.method==='factorizar', rows=sys.A.length, cols=sys.A[0].length;
  const mode=group('Forma de entrada',[['entry','cells','Matriz aumentada'],['entry','ecuaciones','Ecuaciones']],sys.entry);
  const settings=choice('ax-method',Object.entries(systemMethods),sys.method,'Procedimiento')+
    sizeChoice('ax-rows',rows,squareSystem()?'Orden de A':'Ecuaciones')+(squareSystem()?'':sizeChoice('ax-cols',cols,'Incógnitas'));
  const equations=sys.equations.map((v,i)=>`<label class="ax-eq"><span>Ecuación ${i+1}</span>
    <input data-equation="${i}" class="ax-math-input" value="${h(v)}" placeholder="2x1 + x2 = 5" autocomplete="off" spellcheck="false"></label>`).join('');
  const editor=sys.entry==='ecuaciones'&&!factor?'<div class="ax-equations">'+equations+'</div>':
    grid('A','A',sys.A,{rhs:factor?null:sys.b,columns:factor?null:sys.names,title:factor?'Matriz de coeficientes A':'Matriz aumentada [A | b]'});
  const workspace=sys.entry==='cells'&&!factor?`<div class="ax-system-layout ${cols>7?'ax-wide-system':''}">${editor}
    <details class="ax-reading" ${cols<=7?'open':''}><summary>Lectura del sistema</summary><ol id="ax-equation-preview">${reading()}</ol></details></div>`:editor;
  return `<div class="ax-settings">${settings}</div><div class="ax-linehead">${factor?'<h3>Factorización triangular</h3>':mode}
      <div class="ax-tools">${button('Teclado','keys')}${button('Ejercicio aleatorio','random')}</div></div>
    ${workspace}<p class="ax-hint">${sys.entry==='ecuaciones'?'Usa una ecuación por fila. Admite x, y, z o x1, x2, x3, y coeficientes como 1/3.':gridHelp}
    ${squareSystem()?'Esta factorización del curso requiere pivotes que permitan continuar sin intercambiar filas.':''}</p>`;
}
function preview(o) {
  const A=o.valores;
  const clipped=A.slice(0,3).map(r=>r.length>3?[...r.slice(0,3),'…']:r);
  if (A.length>3) clipped.push(clipped[0].map(()=>'⋮'));
  return matrix(clipped,{label:o.nombre});
}
function editorHTML() {
  const d=state.editor;
  if (!d) return '';
  const force=state.tool==='combinaciones', type=d.tipo;
  return `<div class="ax-object-editor" id="ax-object-editor"><div class="ax-linehead"><h3>${d.original?'Editar '+h(d.original):force?'Nuevo vector':'Nuevo objeto'}</h3>
      ${button('Cerrar','cancel-editor')}</div><div class="ax-settings">
      <label class="ax-field"><span>Nombre</span><input id="ax-object-name" maxlength="15" value="${h(d.nombre)}" autocomplete="off"></label>
      ${force?'':choice('ax-object-type',[['Matriz','Matriz'],['Vector','Vector']],type,'Tipo')}
      ${sizeChoice('ax-object-rows',d.valores.length,type==='Vector'?'Componentes':'Filas')}
      ${type==='Matriz'?sizeChoice('ax-object-cols',d.valores[0].length,'Columnas'):''}</div>
    ${grid('draft',d.nombre||'M',d.valores,{title:type==='Vector'?'Componentes del vector':'Entradas de la matriz'})}
    <div class="ax-tools">${button('Guardar '+(type==='Vector'?'vector':'matriz'),'save-object')}${button('Teclado','keys')}
      ${d.original?button('Eliminar objeto','remove-object'):''}</div><p id="ax-editor-error" class="ax-inline-error" role="status" hidden></p></div>`;
}
function operations() {
  const firstMatrix=bank.find(o=>o.tipo==='Matriz');
  const presets=firstMatrix?['T('+firstMatrix.nombre+')',...(firstMatrix.valores.length===firstMatrix.valores[0].length?[firstMatrix.nombre+'^-1']:[])]:[];
  const cards=bank.map(o=>`<button type="button" data-edit="${h(o.nombre)}" class="ax-object-card" aria-label="Editar ${h(o.nombre)}">
    <span class="ax-object-title"><strong>${h(o.nombre)}</strong><span>${o.tipo} · ${dimLabel(o.valores)}</span></span>${preview(o)}</button>`).join('');
  const names=bank.map(o=>`<button type="button" class="ax-token" data-token="${h(o.nombre)}">${h(o.nombre)}</button>`).join('');
  return `<div class="ax-bank">${cards}<button type="button" class="ax-add-object" data-action="new-object"><b>＋</b>Crear objeto</button></div>
    ${editorHTML()}<div class="ax-compose"><label for="ax-expr">Expresión</label><input class="ax-math-input" id="ax-expr" value="${h(state.expr)}" placeholder="A(u+v)" autocomplete="off" spellcheck="false">
    <div class="ax-tools"><span class="ax-inline-label">Insertar</span>${names}${['+','−','·','(',')','='].map(v=>`<button type="button" class="ax-token" data-token="${v}">${v}</button>`).join('')}
    ${button('Teclado','keys')}</div><div class="ax-tools">${presets.map(s=>`<button type="button" class="ax-small" data-preset="${h(s)}">${h(s.replace('^-1','⁻¹'))}</button>`).join('')}
    <p class="ax-hint">T(A) transpone, det(A) calcula el determinante y A^-1 obtiene la inversa. Para comparar expresiones, sepáralas con =.</p></div></div>`;
}
function activeGenerators() {
  return vectors().filter(o=>comb.selected.includes(o.nombre) && (comb.mode==='analizar'||o.nombre!==comb.target));
}
function comboPreview() {
  const gen=activeGenerators(), target=object(comb.target), goal=comb.mode==='objetivo';
  if (!gen.length || (goal&&!target)) return '<p class="ax-hint">Selecciona los vectores para formar la matriz.</p>';
  const all=goal?[...gen,target]:gen, n=all[0].valores.length;
  if (all.some(o=>o.valores.length!==n)) return '<p class="ax-inline-error">Las dimensiones de los vectores seleccionados deben coincidir.</p>';
  const visible=Array.from({length:n},(_,i)=>all.map(o=>o.valores[i][0]||'□'));
  return `<div><h3>${goal?'Sistema de coeficientes':'Matriz de vectores'}</h3><p class="ax-hint">${h(goal?
    gen.map((o,i)=>'c'+(i+1)+'·'+o.nombre).join(' + ')+' = '+target.nombre:gen.map(o=>o.nombre).join(', ')+' como columnas')}</p></div>${matrix(visible,{split:goal?gen.length:undefined,label:'Columnas seleccionadas'})}`;
}
function combo() {
  const vs=vectors(), goal=comb.mode==='objetivo', target=object(comb.target);
  const mode=group('Análisis de vectores',[['combo-mode','objetivo','Representar un vector'],['combo-mode','analizar','Analizar dependencia']],comb.mode);
  const chips=vs.filter(o=>!goal||o.nombre!==comb.target).map(o=>`<label class="ax-check"><input type="checkbox" data-generator="${h(o.nombre)}" ${comb.selected.includes(o.nombre)?'checked':''}>${h(o.nombre)}</label>`).join('');
  const active=[...(goal&&target?[target]:[]),...activeGenerators()];
  const cards=active.map(o=>{
    const isGoal=goal&&o.nombre===comb.target;
    return `<div class="ax-vector-card ${isGoal?'ax-goal':''}"><div class="ax-linehead"><div><span class="ax-caption">${isGoal?'Objetivo':goal?'Generador':'Vector'}</span><h3>${h(o.nombre)} <small>∈ ℝ<sup>${o.valores.length}</sup></small></h3></div><button type="button" class="ax-small" data-edit="${h(o.nombre)}">Editar</button></div>
      <div class="ax-vector-inputs">${o.valores.map((_,i)=>`<label><span>${h(coordinate(o.nombre,i,0))}</span>${inputCell('v:'+o.nombre,o.nombre,o.valores,i,0)}</label>`).join('')}</div></div>`;
  }).join('');
  return `<div class="ax-linehead">${mode}<div class="ax-tools">${button('＋ Crear vector','new-object')}${button('Teclado','keys')}</div></div>
    <div class="ax-combo-picks">${goal?choice('ax-target',vs.map(o=>[o.nombre,o.nombre+' · '+o.valores.length+' componentes']),comb.target,'Vector objetivo'):''}
      <fieldset class="ax-field"><legend>${goal?'Vectores generadores':'Vectores del conjunto'}</legend><div class="ax-choices">${chips||'Crea un vector para seleccionarlo.'}</div></fieldset></div>
    ${editorHTML()}<div class="ax-vector-cards">${cards}</div><div id="ax-combo-preview" class="ax-combo-preview">${comboPreview()}</div>`;
}
const allowedDet = (method,n) => (method!=='sarrus'||n===3) && (method!=='cofactores'||n<=6);
function determinant() {
  const n=det.A.length, methodHints={sarrus:'Seis diagonales · 3 × 3',cofactores:'Expansión por menores · hasta 6 × 6',gauss:'Producto de pivotes y signo',lu:'Factores triangulares y permutaciones'};
  const choices=Object.entries(detName).map(([key,title])=>`<label class="ax-method-card"><input name="ax-det-method" type="radio" value="${key}" ${key===det.method?'checked':''} ${allowedDet(key,n)?'':'disabled'}>
      <span><strong>${h(title)}</strong><small>${h(methodHints[key])}</small></span></label>`).join('');
  return `<div class="ax-linehead">${sizeChoice('ax-order',n,'Orden de A',8)}<div class="ax-tools">${button('Teclado','keys')}${button('Matriz aleatoria','random')}</div></div>
    <div class="ax-det-layout">${grid('A','A',det.A,{title:'Matriz cuadrada A'})}<fieldset class="ax-det-methods"><legend>Método de cálculo</legend>${choices}</fieldset></div>
    <p class="ax-hint">${gridHelp}</p>`;
}
function submitLabel() {
  return ({sistemas:sys.method==='factorizar'?'Factorizar A':'Resolver sistema',operaciones:'Evaluar expresión',
    combinaciones:comb.mode==='objetivo'?'Encontrar coeficientes':'Analizar vectores',determinantes:'Calcular determinante'})[state.tool];
}
function render() {
  const m=info[state.tool];
  view.dataset.tool=state.tool;
  $('lab-title').textContent=$('lab-breadcrumb').textContent=m.title;
  $('lab-desc').textContent=m.lead; $('lab-symbol').textContent=m.icon;
  $('lab-input-title').textContent=m.input; $('lab-input-hint').textContent=m.hint;
  controls.innerHTML=({sistemas:systems,operaciones:operations,combinaciones:combo,determinantes:determinant})[state.tool]();
  $('lab-submit').textContent=state.busy?'Calculando…':submitLabel()+' →';
  $('lab-submit').disabled=state.busy;
  $('lab-clear').textContent=state.tool==='operaciones'?'Limpiar expresión':state.tool==='combinaciones'?'Limpiar selección':'Limpiar datos';
  $('lab-keyboard').hidden=true; state.focus=null;
  attachRich();
}
function feedback(text='',bad=false) {
  const el=$('lab-feedback');
  el.hidden=!text; el.className=bad?'ax-message ax-error':'ax-message'; el.textContent=text;
}
function invalidate() {
  state.revision++; state.result=null; state.lesson=null; state.busy=false;
  $('lab-output').hidden=true; $('lab-submit').disabled=false; $('lab-submit').textContent=submitLabel()+' →'; feedback();
}
function chooseTool(key) {
  if (!info[key]) return;
  state.tool=key; state.editor=null; invalidate(); render();
}
async function post(action,body) {
  const resp=await fetch('/api/lab/'+action,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...body,exacto:true})});
  const json=await resp.json();
  if (!resp.ok||!json.ok) throw Error(json.error||'No se pudo completar el cálculo.');
  return json.resultado;
}
function makeNames(count) {
  const names=sys.names.slice(0,count);
  for (let i=1;names.length<count;i++) if (!names.includes('x'+i)) names.push('x'+i);
  return names;
}
function resizeSystem(rows,cols) {
  sys.A=resize(sys.A,rows,cols); sys.b=resize(sys.b,rows,1);
  sys.names=makeNames(cols);
  sys.equations=Array.from({length:rows},(_,i)=>sys.equations[i]??'');
}
function badNumber(value) { return !numeric.test(norm(value)); }
function ensureGrid(key,name) {
  const values=lookupGrid(key);
  for (let i=0;i<values.length;i++) for (let j=0;j<values[i].length;j++) {
    if (!badNumber(values[i][j])) continue;
    const input=controls.querySelector(`[data-grid="${CSS.escape(key)}"][data-row="${i}"][data-col="${j}"]`);
    input?.setAttribute('aria-invalid','true'); input?.focus();
    throw Error('Revisa '+coordinate(name,i,j)+'. Escribe un entero, un decimal o una fracción con denominador distinto de cero.');
  }
}
function asEquations() {
  ensureGrid('A','A'); ensureGrid('b','b');
  return sys.A.map((row,i)=>{
    const terms=[];
    row.forEach((v,j)=>{
      const raw=norm(v).replace(/^\+/,''), negative=raw.startsWith('-'), abs=raw.replace(/^-/,'');
      // La primera fila menciona todas las variables para conservar el orden de las columnas.
      if (i>0 && abs==='0') return;
      const sign=negative?'−':terms.length?'+':'';
      terms.push(sign+(abs==='1'?'':abs)+sys.names[j]);
    });
    return (terms.join(' ')||'0')+' = '+norm(sys.b[i][0]);
  });
}
async function setEntry(next, nextMethod=sys.method) {
  if (next===sys.entry && nextMethod===sys.method) return;
  invalidate();
  const token=state.revision;
  try {
    if (sys.entry==='cells'&&next==='ecuaciones') sys.equations=asEquations();
    if (sys.entry==='ecuaciones'&&next==='cells') {
      const r=await post('traducir_ecuaciones',{ecuaciones:sys.equations,variables:sys.A[0].length});
      if (token!==state.revision) return;
      sys.A=copy(r.A); sys.b=copy(r.b); sys.names=r.nombres;
    }
    sys.entry=next; sys.method=nextMethod;
    if (squareSystem()) {
      const n=Math.max(sys.A.length,sys.A[0].length);
      resizeSystem(n,n);
    }
    render();
  } catch(error) { if (token===state.revision) { render(); feedback(error.message,true); } }
}
function nextName(type) {
  const base=type==='Vector'?'v':'M';
  for (let i=1;;i++) if (!object(base+i)) return base+i;
}
function openEditor(name) {
  const o=name?object(name):null;
  const type=o?.tipo || (state.tool==='combinaciones'?'Vector':'Matriz');
  const rows=type==='Vector'?(object(comb.target)?.valores.length||2):2;
  state.editor={original:o?.nombre||'',nombre:o?.nombre||nextName(type),tipo:type,
    valores:o?copy(o.valores):resize([],rows,type==='Vector'?1:2,'')};
  render(); $('ax-object-name').focus();
}
function fixSelection() {
  const vs=vectors();
  if (!vs.some(o=>o.nombre===comb.target)) comb.target=vs[0]?.nombre||'';
  comb.selected=comb.selected.filter(name=>vs.some(o=>o.nombre===name));
}
function saveObject() {
  const d=state.editor, name=d.nombre.trim();
  try {
    if (!/^[A-Za-z][A-Za-z0-9_]*$/.test(name)||['det','T','inv'].includes(name)) throw Error('Usa un nombre que empiece con una letra. T, det e inv se reservan para funciones.');
    if (object(name) && name!==d.original) throw Error('Ya existe un objeto con ese nombre.');
    if (!d.original&&bank.length>=20) throw Error('El banco admite hasta 20 objetos.');
    ensureGrid('draft',name);
    const values={nombre:name,tipo:d.tipo,valores:copy(d.valores)};
    if (d.original) {
      bank[bank.indexOf(object(d.original))]=values;
      if (comb.target===d.original) comb.target=name;
      comb.selected=comb.selected.map(n=>n===d.original?name:n);
    } else {
      bank.push(values);
      if (state.tool==='combinaciones'&&comb.target && name!==comb.target) comb.selected.push(name);
    }
    state.editor=null; fixSelection(); invalidate(); render(); feedback(name+' guardado.');
  } catch(e) {
    const msg=$('ax-editor-error'); msg.textContent=e.message; msg.hidden=false;
  }
}
function removeObject() {
  const name=state.editor.original;
  bank.splice(bank.indexOf(object(name)),1); state.editor=null; fixSelection();
  invalidate(); render(); feedback('Se eliminó '+name+' del banco.');
}
function loadExample() {
  invalidate(); state.editor=null;
  if (state.tool==='sistemas') {
    sys.A=copy(initialA); sys.b=copy(initialB); sys.names=['x1','x2','x3'];
    if (sys.entry==='ecuaciones') sys.equations=asEquations();
  } else if (state.tool==='determinantes') {
    det.A=copy(initialA);
  } else {
    const seeds=state.tool==='operaciones'?exampleObjects: [
      {nombre:'g1',tipo:'Vector',valores:[[1],[2]]},{nombre:'g2',tipo:'Vector',valores:[[2],[-1]]},
      {nombre:'w',tipo:'Vector',valores:[[4],[3]]}];
    const used=[], additions=[];
    for (const seed of seeds) {
      let name=seed.nombre, k=1;
      const values=copy(seed.valores);
      while (object(name) && (object(name).tipo!==seed.tipo || JSON.stringify(object(name).valores)!==JSON.stringify(values))) name=seed.nombre+'_'+k++;
      used.push(name);
      if (!object(name)) additions.push({...seed,nombre:name,valores:values});
    }
    if (bank.length+additions.length>20) { feedback('El banco está lleno. Libera espacio para cargar este ejemplo.',true); return; }
    bank.push(...additions);
    if (state.tool==='operaciones') state.expr=used[0]+'('+used[1]+'+'+used[2]+')';
    else {comb.target=used[2];comb.selected=comb.mode==='objetivo'?used.slice(0,2):used;}
  }
  render(); feedback('Ejemplo cargado.');
}
async function randomData() {
  invalidate();
  const token=state.revision, system=state.tool==='sistemas';
  const A=system?sys.A:det.A;
  const mode=system?({lu:'sistema_lu',factorizar:'lu'})[sys.method]||'sistema':'sistema';
  try {
    const r=await post('aleatorio',{modo:mode,n:A.length,columnas:A[0].length});
    if (token!==state.revision) return;
    if (system) {
      sys.A=copy(r.A); if (r.b) sys.b=copy(r.b);
      if (sys.entry==='ecuaciones') sys.equations=asEquations();
    } else det.A=copy(r.A);
    render(); feedback('Ejercicio aleatorio listo.');
  } catch(e) { if (token===state.revision) feedback(e.message,true); }
}
function clearData() {
  invalidate(); state.editor=null;
  if (state.tool==='sistemas') {
    sys.A=resize([],sys.A.length,sys.A[0].length,'');sys.b=resize([],sys.A.length,1,'');
    sys.equations=Array(sys.A.length).fill('');
  } else if (state.tool==='determinantes') det.A=resize([],det.A.length,det.A.length,'');
  else if (state.tool==='operaciones') state.expr='';
  else comb.selected=[];
  render();
}
function exercise() {
  if (state.editor) throw Error('Guarda el objeto o cierra su editor antes de calcular.');
  if (state.tool==='sistemas') {
    if (sys.entry==='cells') {ensureGrid('A','A');if (sys.method!=='factorizar') ensureGrid('b','b');}
    return {A:sys.A,b:sys.b,entrada:sys.entry,metodo:sys.method,ecuaciones:sys.equations,variables:sys.A[0].length,nombres:sys.names};
  }
  if (state.tool==='determinantes') {ensureGrid('A','A');return {A:det.A,metodo:det.method};}
  if (state.tool==='operaciones') return {objetos:bank,expresion:state.expr};
  const gen=activeGenerators().map(o=>o.nombre);
  const required=comb.mode==='objetivo'?[...gen,comb.target]:gen;
  const values=bank.filter(o=>required.includes(o.nombre));
  for (const o of values) ensureGrid('v:'+o.nombre,o.nombre);
  return {objetos:values,generadores:gen,objetivo:comb.target,modo:comb.mode};
}
async function solve() {
  invalidate();
  const token=state.revision;
  try {
    const payload=exercise(); state.busy=true; $('lab-submit').disabled=true; $('lab-submit').textContent='Calculando…';
    const result=await post(state.tool,payload);
    if (token!==state.revision||view.hidden) return;
    state.result=result; state.step=0; $('lab-all').open=false;
    showResult(); feedback('Cálculo completado.');
    $('lab-development').focus({preventScroll:true}); $('lab-output').scrollIntoView({behavior:'instant',block:'start'});
  } catch(e) { if (token===state.revision) feedback(e.message,true); }
  finally { if (token===state.revision) {state.busy=false; $('lab-submit').disabled=false; $('lab-submit').textContent=submitLabel()+' →';} }
}
function showResult() {
  const model=lesson(state.result); state.lesson=model;
  $('lab-output').hidden=false; $('lab-dev-title').textContent=info[state.tool].steps;
  $('lab-summary').textContent=model.title;
  $('lab-step-select').innerHTML=model.steps.map((s,i)=>`<option value="${i}">${i+1} / ${model.steps.length} · ${h(s.title)}</option>`).join('');
  $('lab-step-list').replaceChildren();
  if ($('lab-all').open) showIndex();
  $('lab-proof').innerHTML=`<h3 class="ax-verdict">${h(model.title)}</h3>`+model.proof();
  showStep(state.step);
}
function showIndex() {
  if (!state.lesson||$('lab-step-list').childElementCount) return;
  $('lab-step-list').innerHTML=state.lesson.steps.map((s,i)=>`<li><details data-inspect="${i}"><summary>${h(s.phase)} · ${h(s.title)}</summary>
    <div class="ax-inspect-body"></div><button type="button" data-step="${i}">Abrir este paso en el visor ↑</button></details></li>`).join('');
}
function showStep(index) {
  const steps=state.lesson.steps;
  state.step=Math.max(0,Math.min(index,steps.length-1));
  const s=steps[state.step];
  $('lab-step-select').value=String(state.step); $('lab-prev').disabled=state.step===0;
  $('lab-next').disabled=state.step===steps.length-1;
  $('lab-stage').innerHTML=`<div class="ax-stage-title"><span>${h(s.phase)}</span><h3>${h(s.title)}</h3></div>${s.body()}`;
}
function exportResult() {
  const model=state.lesson;
  const div=document.createElement('div');
  const plain=html=>{
    div.innerHTML=html;
    div.querySelectorAll('tr').forEach(tr=>tr.replaceWith(document.createTextNode('[ '+Array.from(tr.cells,x=>x.textContent).join('   ')+' ]\n')));
    div.querySelectorAll('h3,p,div,li').forEach(el=>el.append('\n'));
    return div.textContent.replace(/\n{3,}/g,'\n\n').trim();
  };
  const lines=['CHOCO LAB · '+info[state.tool].title,model.title,...model.steps.map((s,i)=>
    (i+1)+'. '+s.phase+' · '+s.title+'\n'+plain(s.body(false))), 'RESULTADO Y VERIFICACIÓN\n'+plain(model.proof())];
  const url=URL.createObjectURL(new Blob(['\uFEFF'+lines.join('\n\n')],{type:'text/plain;charset=utf-8'}));
  const a=document.createElement('a'); a.href=url; a.download='ChocoLab_'+state.tool+'.txt';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}

function attachRich() {
  if (!state.rich||!customElements.get('math-field')) return;
  for (const input of controls.querySelectorAll('.ax-math-input')) {
    const mf=document.createElement('math-field');
    mf.mathVirtualKeyboardPolicy='manual';
    mf.setAttribute('aria-label',input.id==='ax-expr'?'Expresión':'Ecuación '+(1+Number(input.dataset.equation)));
    mf.value=input.value; input.hidden=true; input.after(mf);
    mf.addEventListener('input',()=>{
      const ascii=mf.getValue('ascii-math');
      input.value=ascii.replace(/_\(?(\d+)\)?/g,'$1').replace(/\\left|\right/g,'')
        .replace(/[−–]/g,'-').replace(/\\cdot|×|⋅/g,'*').replace(/\^\(-1\)|\^\{-1\}/g,'^-1')
        .replace(/\^\(T\)|\^\{T\}/g,'^T').replace(/\(([-+]?\d+)\)\/\((\d+)\)/g,'$1/$2')
        .replace(/\(([-+]?\d+\/\d+)\)/g,'$1');
      input.dispatchEvent(new Event('input',{bubbles:true}));
    });
  }
}
const keyPairs=[['7','7'],['8','8'],['9','9'],['+','+'],['−','-'],['⌫','Backspace'],['4','4'],['5','5'],['6','6'],
  ['×','*'],['÷','/'],['=','='],['1','1'],['2','2'],['3','3'],['(','('],[')',')'],['½','1/2'],['0','0'],['.','.'],
  ['x₁','x1'],['x₂','x2'],['x₃','x3'],['ᵀ','^T'],['A','A'],['B','B'],['u','u'],['v','v'],['⁻¹','^-1']];
function insert(input,value) {
  if (!input) return;
  if (input.tagName==='MATH-FIELD') {
    if (value==='Backspace') input.executeCommand('deleteBackward');
    else input.insert(({'*':'\\cdot','·':'\\cdot','/':'\\frac{#@}{#0}','^-1':'^{-1}','^T':'^{T}'})[value]||value);
    input.dispatchEvent(new Event('input',{bubbles:true}));
  } else {
    const start=input.selectionStart??input.value.length, end=input.selectionEnd??start;
    const erase=value==='Backspace';
    input.setRangeText(erase?'':value,erase&&start===end?Math.max(start-1,0):start,end,'end');
    input.dispatchEvent(new Event('input',{bubbles:true}));
  }
  input.focus();
}
function defaultKeyTarget() {
  if (state.focus?.isConnected) return state.focus;
  const editor=$('ax-object-editor');
  return (editor||controls).querySelector('math-field,.ax-math-input:not([hidden]),.ax-cell');
}
function onInput(e) {
  const el=e.target, key=el.dataset.grid;
  if (key) {
    const data=lookupGrid(key); data[+el.dataset.row][+el.dataset.col]=el.value;
    if (el.value && badNumber(el.value)) el.setAttribute('aria-invalid','true'); else el.removeAttribute('aria-invalid');
    if (key!=='draft') {
      invalidate();
      if (state.tool==='combinaciones') $('ax-combo-preview').innerHTML=comboPreview();
      if ($('ax-equation-preview')) $('ax-equation-preview').innerHTML=reading();
    }
  } else if (el.dataset.equation!==undefined) {sys.equations[Number(el.dataset.equation)]=el.value;invalidate();}
  else if (el.id==='ax-expr') {state.expr=el.value;invalidate();}
  else if (el.id==='ax-object-name') state.editor.nombre=el.value;
}
function onChange(e) {
  const el=e.target;
  if (el.id==='lab-step-select') {showStep(+el.value);return;}
  if (el.id==='lab-format') {state.format=el.value;setFormat(el.value);render();if (state.result) showResult();return;}
  if (el.id==='lab-coords') {state.coord=+el.value;render();return;}
  if (el.id==='lab-rich') {state.rich=el.checked;render();return;}
  if (el.id==='ax-method') {setEntry(el.value==='factorizar'?'cells':sys.entry,el.value);return;}
  if (el.id==='ax-rows'||el.id==='ax-cols') {
    invalidate();
    const rows=+$('ax-rows').value;resizeSystem(rows,squareSystem()?rows:+$('ax-cols').value);render();
  } else if (el.id==='ax-order') {
    invalidate();
    const n=+el.value,previous=det.method;det.A=resize(det.A,n,n);
    if (!allowedDet(previous,n)) det.method=n<=2?'cofactores':'gauss';
    render();
    if (previous!==det.method) feedback('Para el orden '+n+' se seleccionó '+detName[det.method]+'.');
  } else if (el.name==='ax-det-method') {det.method=el.value;invalidate();}
  else if (el.id==='ax-target') {comb.target=el.value;invalidate();render();}
  else if (el.dataset.generator) {
    const n=el.dataset.generator;
    comb.selected=comb.selected.filter(v=>v!==n);if (el.checked) comb.selected.push(n);
    invalidate();render();
    controls.querySelector('[data-generator="'+CSS.escape(n)+'"]')?.focus({preventScroll:true});
  } else if (['ax-object-type','ax-object-rows','ax-object-cols'].includes(el.id)) {
    const d=state.editor;
    d.tipo=$('ax-object-type')?.value||'Vector';
    d.valores=resize(d.valores,+$('ax-object-rows').value,d.tipo==='Vector'?1:+($('ax-object-cols')?.value||2),'');
    render();
  }
}
function onClick(e) {
  const b=e.target.closest('button');
  if (!b) return;
  const a=b.dataset.action, value=b.dataset.value;
  if (b.id==='lab-submit') {solve();return;}
  if (b.id==='lab-clear') {clearData();return;}
  if (b.id==='lab-example') {loadExample();return;}
  if (b.id==='lab-prev'||b.id==='lab-next') {showStep(state.step+(b.id==='lab-prev'?-1:1));return;}
  if (b.id==='lab-export') {exportResult();return;}
  if (b.dataset.step!==undefined) {showStep(+b.dataset.step);$('lab-all').open=false;$('lab-step-select').focus();return;}
  if (b.dataset.pick!==undefined) {
    const [i,j]=b.dataset.pick.split(',').map(Number);$('ax-component').innerHTML=state.lesson.steps[state.step].pick(i,j);
    $('lab-stage').querySelectorAll('[data-pick]').forEach(el=>el.setAttribute('aria-pressed',String(el===b)));return;
  }
  if (b.dataset.edit) {openEditor(b.dataset.edit);return;}
  if (b.dataset.preset) {
    state.expr=b.dataset.preset;invalidate();render();
    const input=$('ax-expr'); (input.hidden?input.nextElementSibling:input).focus();return;
  }
  if (b.dataset.token!==undefined) {
    const expr=$('ax-expr');insert(expr.hidden?expr.nextElementSibling:expr,b.dataset.token);return;
  }
  if (b.dataset.key!==undefined) {insert(defaultKeyTarget(),b.dataset.key);return;}
  switch (a) {
    case 'entry': setEntry(value);break;
    case 'random': randomData();break;
    case 'combo-mode': comb.mode=value;invalidate();render();break;
    case 'new-object': openEditor();break;
    case 'save-object': saveObject();break;
    case 'cancel-editor': state.editor=null;render();break;
    case 'remove-object': removeObject();break;
    case 'keys': {
      const panel=$('lab-keyboard');panel.hidden=!panel.hidden;
      if (!panel.hidden) {state.focus=defaultKeyTarget();panel.scrollIntoView({block:'nearest'});}
      break;
    }
    case 'close-keys': $('lab-keyboard').hidden=true;state.focus?.focus();break;
  }
}
function pasteGrid(e) {
  const el=e.target;
  if (!el.dataset.grid) return;
  const text=e.clipboardData?.getData('text/plain').trim();
  if (!text||!/[\n\t; ]/.test(text)) return;
  e.preventDefault();
  let rows=text.split(/\r?\n|;/).map(l=>l.trim().split(/[\t ]+/));
  const key=el.dataset.grid, data=lookupGrid(key), startI=+el.dataset.row,startJ=+el.dataset.col;
  const augmented=key==='A' && state.tool==='sistemas' && sys.method!=='factorizar';
  if (!augmented && data[0].length===1 && rows.length===1) rows=rows[0].map(v=>[v]);
  const limit=data[0].length+(augmented?1:0);
  if (startI+rows.length>data.length||rows.some(row=>row.length!==rows[0].length||row.length+startJ>limit)) {
    feedback('El bloque no cabe en esas casillas. Ajusta las dimensiones o empieza en la primera entrada.',true);return;
  }
  const invalid=rows.flat().find(badNumber);
  if (invalid!==undefined) {feedback('Revisa el valor «'+invalid+'» en el bloque que pegaste.',true);return;}
  rows.forEach((row,i)=>row.forEach((v,j)=>{
    if (startJ+j===data[0].length) sys.b[startI+i][0]=v;
    else data[startI+i][startJ+j]=v;
  }));
  invalidate();render();feedback('Se pegaron '+rows.length+' filas y '+rows[0].length+' columnas.');
  controls.querySelector('[data-grid="'+CSS.escape(key)+'"][data-row="'+startI+'"][data-col="'+startJ+'"]')?.focus({preventScroll:true});
}
function moveCell(e) {
  const el=e.target;
  if (!el.classList.contains('ax-cell')) return;
  const key=e.key, row=+el.dataset.row, col=+el.dataset.col;
  const direction=({ArrowDown:[1,0],ArrowUp:[-1,0],Enter:[e.shiftKey?-1:1,0],ArrowLeft:[0,-1],ArrowRight:[0,1]})[key];
  if (!direction || (key==='ArrowLeft'&&el.selectionStart!==0) || (key==='ArrowRight'&&el.selectionEnd!==el.value.length)) return;
  let gridKey=el.dataset.grid, nextCol=col+direction[1];
  if (state.tool==='sistemas'&&sys.method!=='factorizar') {
    if (gridKey==='A'&&nextCol===sys.A[0].length) {gridKey='b';nextCol=0;}
    else if (gridKey==='b'&&nextCol===-1) {gridKey='A';nextCol=sys.A[0].length-1;}
  }
  const target=controls.querySelector('[data-grid="'+CSS.escape(gridKey)+'"][data-row="'+(row+direction[0])+'"][data-col="'+nextCol+'"]');
  if (target) {e.preventDefault();target.focus();target.select();}
}

$('lab-keys').innerHTML=keyPairs.map(([label,key])=>`<button type="button" class="ax-token" data-key="${h(key)}">${h(label)}</button>`).join('');
$('lab-all').addEventListener('toggle',()=>{if ($('lab-all').open) showIndex();});
$('lab-step-list').addEventListener('toggle',e=>{
  const el=e.target;
  if (el.dataset.inspect===undefined||!el.open) return;
  const body=el.querySelector('.ax-inspect-body');
  if (body.childElementCount) return;
  body.innerHTML=state.lesson.steps[Number(el.dataset.inspect)].body(false);
},true);
view.addEventListener('input',onInput);view.addEventListener('change',onChange);view.addEventListener('click',onClick);
controls.addEventListener('paste',pasteGrid);controls.addEventListener('keydown',moveCell);
controls.addEventListener('focusin',e=>{
  if (e.target.matches('.ax-cell,.ax-math-input,math-field')) state.focus=e.target;
});
document.addEventListener('click',e=>{
  const nav=e.target.closest('button[data-view]');
  if (nav?.dataset.linearTool && info[nav.dataset.linearTool]) chooseTool(nav.dataset.linearTool);
  else if (nav && nav.dataset.view!=='linear-workspace') state.revision++;
});
customElements.whenDefined('math-field').then(()=>{$('lab-rich-option').hidden=false;});
