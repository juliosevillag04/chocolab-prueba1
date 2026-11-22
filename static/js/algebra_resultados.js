/* Presentación de los pasos y certificados devueltos por los motores de Python. */
export const h = value => String(value ?? '').replace(/[&<>"']/g, c =>
  ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c]));
let decimal = false;
export function setFormat(format) { decimal = format === 'decimal'; }

function number(value) {
  const exact = String(value ?? '—');
  if (!decimal || !exact.includes('/')) return exact;
  const [a, b] = exact.split('/').map(Number);
  const result = a / b;
  return Number.isFinite(result) ? String(Number(result.toPrecision(9))) : exact;
}
const isMatrix = Array.isArray;
const formattedText = text => decimal ? text.replace(/\b\d+\/\d+\b/g, number) : text;
const col = v => v.map(x => [x]);
const identity = n => Array.from({length:n}, (_, i) => Array.from({length:n}, (_, j) => Number(i === j)));
const formula = text => '<p class="ax-formula">' + h(text) + '</p>';
const note = text => '<p class="ax-note">' + h(text) + '</p>';
const line = (...items) => '<div class="ax-math-line">' + items.join('') + '</div>';
const op = text => '<span class="ax-op" aria-hidden="true">' + h(text) + '</span>';
const tile = (name, content) => '<div class="ax-tile"><div class="ax-caption">' + h(name) + '</div>' + content + '</div>';
const ntext = v => '(' + number(v) + ')';

export function matrix(data, {split, mark, label = 'Matriz', pick = false} = {}) {
  if (!isMatrix(data)) return '<strong class="ax-scalar">' + h(number(data)) + '</strong>';
  const rows = data.map((row,i) => '<tr>' + row.map((v,j) => {
    const classes = [split === j ? 'ax-boundary' : '', mark?.(i,j) || ''].join(' ');
    const content = h(number(v));
    const cell = pick ? '<button type="button" data-pick="' + i + ',' + j +
      '" aria-label="Desarrollo de la entrada ' + (i+1) + ', ' + (j+1) + '">' + content + '</button>' : content;
    return '<td class="' + classes + '">' + cell + '</td>';
  }).join('') + '</tr>').join('');
  return '<div class="ax-math-scroll"><div class="ax-bracket"><table class="ax-matrix" aria-label="' +
    h(label) + '"><tbody>' + rows + '</tbody></table></div></div>';
}
const mTile = (title, data, settings = {}) => tile(title, matrix(data, {label:title, ...settings}));
const stage = (phase, title, body) => ({phase, title, body});
const className = {unica:'Solución única', infinitas:'Infinitas soluciones', inconsistente:'Sistema sin solución'};
export const detName = {sarrus:'Sarrus', cofactores:'Cofactores', gauss:'Eliminación gaussiana', lu:'Factorización LU'};

function pass(before, after, split, extra = '') {
  const changed = (i,j) => String(before[i][j]) !== String(after[i][j]) ? 'ax-changed' : '';
  return line(mTile('Antes', before, {split}), op('→'), mTile('Después', after, {split, mark:changed})) + extra;
}
function rowStages(r, prefix = '') {
  const inverse = r.tipo === 'inversa';
  let previous = inverse ? r.original : r.matriz_original;
  const split = inverse ? previous[0].length / 2 : previous[0].length - 1;
  const result = r.pasos.map(p => {
    const before = previous;
    previous = p.matriz;
    const phase = p.fase === 'reduccion' ? 'Ceros sobre el pivote' : 'Escalonamiento';
    let why;
    const column = p.columna + 1;
    if (p.tipo === 'intercambio') {
      why = 'En la columna '+column+', F'+(p.otra+1)+' aporta el pivote '+number(before[p.otra][p.columna])+'. El intercambio lo coloca en F'+(p.fila+1)+'.';
    } else if (p.tipo === 'escalar') {
      why = 'El pivote de F'+(p.fila+1)+' en la columna '+column+' vale '+number(before[p.fila][p.columna])+'. Multiplica toda la fila por '+number(p.factor)+' para convertirlo en 1.';
    } else if (p.tipo === 'eliminar') {
      why = 'En la columna '+column+', la entrada de F'+(p.fila+1)+' vale '+number(before[p.fila][p.columna])+'. Resta '+ntext(p.factor)+' veces F'+(p.otra+1)+' para obtener cero.';
    }
    return stage(prefix + phase, formattedText(p.operacion), () => pass(before, p.matriz, split, why ? note(why) : ''));
  });
  if (!result.length) {
    result.push(stage(prefix + 'Matriz inicial', 'Leer la forma obtenida', () =>
      mTile(inverse ? '[A | I]' : '[A | b]', previous, {split}) + note('La matriz ya tiene la forma necesaria para leer este resultado.')));
  }
  if (r.modo === 'gauss' && r.clasificacion !== 'inconsistente') {
    const assigned = r.solucion?.map(number) || r.parametros.map(p => formattedText(p.expresion));
    for (const [i,j] of [...r.pivotes].reverse()) {
      const row = r.matriz_escalonada[i];
      const terms = [];
      for (let k=j+1; k<split; k++) {
        if (String(row[k]) !== '0') terms.push(ntext(row[k]) + '·(' + assigned[k] + ')');
      }
      const text = r.nombres[j] + ' = ' + number(row[split]) + terms.map(v => ' − ' + v).join('') +
        (terms.length ? ' = ' + assigned[j] : '');
      result.push(stage('Sustitución hacia atrás', 'Despejar ' + r.nombres[j] + ' en la fila ' + (i+1), () =>
        mTile('Forma escalonada', r.matriz_escalonada, {split, mark:k => k===i?'ax-changed':''}) + formula(text)));
    }
  }
  return result;
}
function luStages(r) {
  let previous = r.matriz_original;
  const steps = r.pasos.map(p => {
    const before = previous;
    previous = p.U;
    return stage('Factorización LU', formattedText(p.operacion), () => pass(before, p.U, undefined) +
      line(mTile('Multiplicadores en L', p.L)) +
      (p.multiplicador != null ? formula('m = ' + number(p.valor_eliminado) + ' / ' + ntext(p.pivote) + ' = ' + number(p.multiplicador)) : ''));
  });
  if (!steps.length) steps.push(stage('Factorización LU', 'Leer los factores triangulares', () => line(mTile('L',r.L),mTile('U',r.U))));
  for (const [items,label,symbol,mat] of [[r.pasos_y,'Ly = b','y',r.L],[r.pasos_x,'Ux = y','x',r.U]]) {
    for (const p of items || []) {
      const name = symbol==='x' ? r.nombres[p.fila] : symbol+(p.fila+1);
      steps.push(stage(label, 'Despejar ' + name, () =>
        mTile('Fila ' + (p.fila+1) + ' de ' + (symbol==='x'?'U':'L'), [mat[p.fila]]) +
        formula(name+' = ('+number(p.rhs)+' − '+ntext(p.suma)+') / '+ntext(p.diagonal)+' = '+number(p.valor))));
    }
  }
  return steps;
}

const opNames = {producto:'Producto matricial',suma:'Suma o resta',escalar_suma:'Operación escalar',escalar_producto:'Producto de escalares',
  escalar:'Multiplicación por escalar',division:'División por escalar',transpuesta:'Transpuesta',determinante:'Determinante'};
const signs = {producto:'·',escalar_producto:'·',escalar:'·',division:'÷'};
function component(p,i,j) {
  const a=p.a,b=p.b, val=(v,row,k)=>number(isMatrix(v)?v[row][k]:v);
  let calc;
  if (p.operacion==='producto') calc=a[i].map((x,k)=>ntext(x)+'·'+ntext(b[k][j])).join(' + ');
  else if (p.operacion==='transpuesta') calc=p.etiqueta_a+'('+(j+1)+','+(i+1)+')';
  else calc='('+val(a,i,j)+') '+(p.detalle||signs[p.operacion])+' ('+val(b,i,j)+')';
  return 'Entrada ('+(i+1)+', '+(j+1)+') = '+calc+' = '+number(p.resultado[i][j]);
}
function expressionStages(r) {
  if (!r.pasos.length) return [stage('Lectura directa', 'Leer el valor de la expresión', () => mTile(r.expresion, r.resultado))];
  return r.pasos.flatMap((p,index) => {
    const symbol=p.detalle || signs[p.operacion] || '';
    const title = p.b != null ? p.etiqueta_a+' '+symbol+' '+p.etiqueta_b : (p.operacion==='transpuesta'?'T':'det')+'('+p.etiqueta_a+')';
    const side = r.comparacion==null ? '' : (index<r.inicio_derecho?'Miembro izquierdo · ':'Miembro derecho · ');
    const item=stage(side+opNames[p.operacion],title,(interactive=true) => {
      const parts=[mTile(p.etiqueta_a,p.a)];
      if (p.b!=null) parts.push(op(symbol),mTile(p.etiqueta_b,p.b));
      parts.push(op(p.b==null?'→':'='),mTile('Resultado',p.resultado,{pick:interactive&&isMatrix(p.resultado)}));
      let html=line(...parts);
      if (isMatrix(p.resultado)) {
        const first=formula(component(p,0,0));
        html+=interactive?note('Selecciona una entrada del resultado para ver su cálculo.')+'<div id="ax-component">'+first+'</div>':first;
      }
      if (p.explicacion?.length) html+='<ul class="ax-calcs">'+p.explicacion.map(t=>'<li>'+h(t)+'</li>').join('')+'</ul>';
      return html;
    });
    if (isMatrix(p.resultado)) item.pick=(i,j)=>formula(component(p,i,j));
    let previous=p.a;
    const reductions=(p.transformaciones||[]).map(change=>{
      const before=previous;
      previous=change.matriz;
      return stage(side+title,formattedText(change.operacion),()=>pass(before,change.matriz));
    });
    return [...reductions,item];
  });
}
function comboStages(a) {
  const r=a.resolucion, split=a.generadores.length;
  return [stage(a.objetivo+' · Planteamiento', 'Organizar los vectores en columnas', () =>
    mTile('['+a.generadores.join('  ')+' | '+a.objetivo+']',r.matriz_original,{split})+
    formula(a.generadores.map((g,i)=>'c'+(i+1)+'·'+g).join(' + ')+' = '+a.objetivo)),
    ...rowStages(r,a.objetivo+' · ')];
}
function detStages(r) {
  const d=r.datos,A=r.matriz_original,n=A.length;
  if (r.metodo==='sarrus') {
    const extended=A.map(row=>[...row,row[0],row[1]]);
    const steps=[];
    for (const [key,sign] of [['positivos',1],['negativos',-1]]) {
      d[key].forEach((values,k)=>{
        const start=sign===1?k:(k===2?2:k+3);
        steps.push(stage('Sarrus · '+(sign===1?'descendente':'ascendente'),
          'Diagonal '+(k+1)+(sign===1?' ↘':' ↗'), () =>
            mTile('A con sus dos primeras columnas repetidas',extended,
              {split:3,mark:(i,j)=>j===start+sign*i?'ax-path':''})+
            formula(values.map(ntext).join(' × ')+' = '+number(d['productos_'+key][k]))));
      });
    }
    steps.push(stage('Sarrus','Restar las dos sumas',()=>formula('S↘ = '+d.productos_positivos.map(ntext).join(' + ')+' = '+number(d.suma_positiva))+
      formula('S↗ = '+d.productos_negativos.map(ntext).join(' + ')+' = '+number(d.suma_negativa))+
      formula('det(A) = '+ntext(d.suma_positiva)+' − '+ntext(d.suma_negativa)+' = '+number(r.determinante))));
    return steps;
  }
  if (r.metodo==='cofactores') return d.recorrido.map(p=>{
    if (p.tipo==='expandir') return stage('Expansión de '+p.nombre,'Elegir '+p.linea+' '+(p.indice+1),()=>
      mTile(p.nombre,p.matriz,{mark:(i,j)=>(p.linea==='fila'?i:j)===p.indice?'ax-path':''})+
      note('Se elige una línea con el menor número de términos distintos de cero.'));
    if (p.tipo==='menor') return stage('Cofactores','Formar el menor '+p.nombre,()=>
      line(mTile('Suprimir F'+(p.fila+1)+' y C'+(p.columna+1),p.matriz,{mark:(i,j)=>i===p.fila||j===p.columna?'ax-cut':''}),op('→'),mTile(p.nombre,p.menor))+
      formula('Coeficiente = '+number(p.coeficiente)+'     Signo del cofactor = '+(p.signo>0?'+1':'−1')));
    if (p.tipo==='base') return stage('Caso base','Calcular det('+p.nombre+')',()=>{
      const m=p.matriz;
      return mTile(p.nombre,m)+formula(m.length===1?'det('+p.nombre+') = '+number(p.valor):
        ntext(m[0][0])+'·'+ntext(m[1][1])+' − '+ntext(m[0][1])+'·'+ntext(m[1][0])+' = '+number(p.valor));
    });
    return stage('Suma de cofactores','Reunir los aportes de '+p.nombre,()=>mTile(p.nombre,p.matriz)+
      p.aportes.map(([s,a,m,v])=>formula(ntext(s)+'·'+ntext(a)+'·'+ntext(m)+' = '+number(v))).join('')+
      formula('det('+p.nombre+') = '+(p.aportes.length?p.aportes.map(t=>ntext(t[3])).join(' + ')+' = ':'')+number(p.valor)));
  });
  let previous=A;
  const steps=d.pasos.map(p=>{
    const before=previous;
    previous=p.U;
    const title=p.operacion || (p.tipo==='sin_pivote'?'Columna '+(p.columna+1)+' sin pivote':
      'F'+(p.fila+1)+' ← F'+(p.fila+1)+' − '+ntext(p.multiplicador)+'F'+(p.columna+1));
    return stage(detName[r.metodo],title,()=>pass(before,p.U,undefined)+
      (p.multiplicador!=null?formula('m = '+number(p.fila_antes[p.columna])+' / '+ntext(p.pivote)+' = '+number(p.multiplicador)):'')+
      (p.L?line(mTile('L',p.L),...(p.P?[mTile('P',p.P)]:[])): ''));
  });
  const stopped=d.pasos.at(-1)?.tipo==='sin_pivote' && r.metodo==='gauss';
  steps.push(stage(detName[r.metodo],stopped?'Identificar la falta de pivote':'Producto de la diagonal',()=>
    mTile(stopped?'Matriz al detener la eliminación':'Matriz triangular U',d.U,{mark:(i,j)=>i===j?'ax-path':''})+
    (stopped?formula('Falta un pivote en la columna '+(d.pasos.at(-1).columna+1)+' ⇒ det(A) = 0'):
      formula('det(A) = (−1)^'+d.intercambios+' × '+d.U.map((row,i)=>ntext(row[i])).join(' × ')+' = '+number(r.determinante))) ));
  return steps;
}

function contradiction(r) {
  return mTile('Fila '+(r.prueba.fila+1)+' de la matriz escalonada',[r.prueba.contradiccion],{split:r.nombres.length})+
    formula('0 = '+number(r.prueba.contradiccion.at(-1)))+note('Esta fila impide satisfacer todas las ecuaciones a la vez.');
}
function systemProof(r) {
  if (r.clasificacion==='inconsistente') return contradiction(r);
  const p=r.prueba;
  let text;
  if (r.clasificacion==='unica') text=formula(r.nombres.map((name,i)=>name+' = '+number(r.solucion[i])).join('     '));
  else text=formula(r.parametros.map(v=>v.variable+' = '+formattedText(v.expresion)).join('     '))+
    note('Cada parámetro puede tomar cualquier valor real. Con todos los parámetros en cero se obtiene la solución particular.');
  const A=r.matriz_original.map(row=>row.slice(0,-1));
  text+=line(mTile('A',A),op('·'),mTile(r.clasificacion==='unica'?'x':'x particular',col(p.x)),op('='),mTile('Ax',p.Ax),op('='),mTile('b',p.b));
  p.direcciones.forEach((v,i)=>{text+=line(mTile('Dirección de t'+(i+1),col(v)),op('→'),mTile('A por esta dirección',p.imagenes[i]));});
  return text;
}
function comboProof(a) {
  const r=a.resolucion;
  let text='<h3>'+h(a.objetivo)+(a.es_combinacion?' sí pertenece':' no pertenece')+' al espacio generado por '+h(a.generadores.join(', '))+'</h3>';
  if (!a.es_combinacion) return text+contradiction(r);
  text+=formula(a.objetivo+' = '+a.generadores.map((g,i)=>ntext(a.pesos[i])+'·'+g).join(' + '));
  if (r.clasificacion==='infinitas') text+=note('Estos pesos son una elección posible. La familia completa de coeficientes es')+
    formula(r.parametros.map(p=>p.variable+' = '+formattedText(p.expresion)).join('     '));
  return text+line(mTile('Generadores',r.matriz_original.map(row=>row.slice(0,-1))),op('·'),mTile('Pesos',col(a.pesos)),
    op('='),mTile('Vector reconstruido',r.prueba.Ax),op('='),mTile(a.objetivo,r.prueba.b));
}
function fullProof(r) {
  switch (r.tipo) {
    case 'gauss': return systemProof(r);
    case 'lu': case 'factorizar': {
      let text=line(mTile('L',r.L),op('·'),mTile('U',r.U),op('='),mTile('LU',r.producto_LU),op('='),mTile('A',r.matriz_original));
      if (r.tipo==='lu') text+=formula(r.nombres.map((n,i)=>n+' = '+number(r.solucion[i])).join('     '))+
        line(mTile('Ly',col(r.Ly)),op('='),mTile('b',col(r.b)))+line(mTile('Ux',col(r.Ux)),op('='),mTile('y',col(r.y)))+
        line(mTile('Ax',col(r.Ax)),op('='),mTile('b',col(r.b)));
      return text;
    }
    case 'expresion': {
      let text=formula(r.expresion);
      if (r.comparacion!=null) text+=line(mTile('Miembro izquierdo',r.resultado),op(r.comparacion?'=':'≠'),mTile('Miembro derecho',r.lado_derecho));
      else text+=line(mTile('Resultado',r.resultado),mTile('Cálculo independiente',r.referencia));
      return text+note(r.verificacion?'La evaluación independiente con SymPy coincide con el cálculo por pasos.':'Los dos cálculos difieren.');
    }
    case 'inversa':
      if (!r.invertible) return mTile('Última matriz [A | I] transformada',r.reducida,{split:r.original.length})+
        note(r.columna_sin_pivote!=null?'La columna '+(r.columna_sin_pivote+1)+' del bloque izquierdo carece de pivote. No existe la inversa.':'El bloque izquierdo no alcanza la identidad.');
      return mTile(r.nombre+'⁻¹',r.resultado)+line(mTile('A · A⁻¹',r.producto_a_inversa),op('='),mTile('I',identity(r.resultado.length)),op('='),mTile('A⁻¹ · A',r.producto_inversa_a));
    case 'combinacion': return comboProof(r);
    case 'analisis': return r.analisis.map(a=>'<div class="ax-case">'+comboProof(a)+'</div>').join('');
    case 'determinante': {
      const vals=Object.entries(r.valores_metodos).map(([k,v])=>'<div><span>'+h(detName[k])+'</span><strong>'+h(number(v))+'</strong></div>').join('');
      const times=Object.entries(r.rendimiento?.tiempos||{}).map(([k,v])=>h(detName[k])+' '+(v*1000).toFixed(4)+' ms').join(' · ');
      return formula('det(A) = '+number(r.determinante))+'<div class="ax-comparison">'+vals+'</div>'+
        (r.metodo==='lu'?line(mTile('P · A',r.datos.producto_pa),op('='),mTile('L · U',r.datos.producto_lu)):'')+
        '<details class="ax-index"><summary>Comparar la eficiencia de los métodos</summary>'+note(detName[r.recomendacion]+' · '+r.razon)+
        '<ul>'+r.criterios.map(c=>'<li>'+h(c)+'</li>').join('')+'</ul>'+(times?note('Mediana de tres ejecuciones locales · '+times):'')+'</details>';
    }
  }
}
export function lesson(r) {
  let title, steps;
  switch (r.tipo) {
    case 'gauss': title=className[r.clasificacion]; steps=rowStages(r); break;
    case 'factorizar': case 'lu': title=r.tipo==='lu'?'Solución por sustitución triangular':'Factorización A = LU'; steps=luStages(r); break;
    case 'inversa': title=r.invertible?'Matriz invertible':'Matriz singular'; steps=rowStages(r); break;
    case 'expresion': title=r.comparacion==null?'Resultado de '+r.expresion:r.comparacion?'Igualdad verdadera':'Igualdad falsa'; steps=expressionStages(r); break;
    case 'combinacion': title=r.es_combinacion?'El vector admite una combinación lineal':'El vector queda fuera del espacio generado'; steps=comboStages(r); break;
    case 'analisis': title=r.analisis.some(a=>a.es_combinacion)?'Conjunto linealmente dependiente':'Conjunto linealmente independiente'; steps=r.analisis.flatMap(comboStages); break;
    case 'determinante': title='det(A) = '+number(r.determinante); steps=detStages(r); break;
  }
  return {title, steps, proof:()=>fullProof(r)};
}
