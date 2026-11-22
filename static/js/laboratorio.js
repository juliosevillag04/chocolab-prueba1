/* Choco Lab · Temas complementarios y medidor de memoria. */
'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const safe = x => String(x ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const S = {comp:'bases', base:2, baseValue:'110.11', romanMode:'convertir', romanSource:'Arábigo',
    romanValue:'4000', romanAType:'Romano', romanBType:'Arábigo', romanA:'(IV)', romanB:'6',
    romanOperator:'+', compLast:null, compExportText:''};
  const names = {bases:'Conversión de sistemas numéricos', romanos:'Números romanos'};
  function notify(text,bad=false,comp=false){const el=$(comp?'comp-feedback':'lab-feedback');if(!el)return;el.hidden=false;el.className='feedback '+(bad?'bad':'good');el.textContent=text;}
  function clearNotice(comp=false){const el=$(comp?'comp-feedback':'lab-feedback');if(el)el.hidden=true;}
  function block(title,html){return `<div class="lab-result-block"><div class="lab-result-label">${safe(title)}</div>${html}</div>`;}
  function options(values,current){return values.map(x=>`<option value="${safe(x[0])}" ${String(x[0])===String(current)?'selected':''}>${safe(x[1])}</option>`).join('');}
  function field(label,html){return `<div class="lab-fieldset"><label>${label}</label>${html}</div>`;}
  function renderComplement(){
    const c=S.comp;$('comp-breadcrumb').textContent=names[c];$('comp-title').textContent=names[c];
    $('comp-desc').textContent=c==='bases'?'Conserva los pasos de conversión entre bases, incluso las partes fraccionarias.':'Convierte entre arábigos y romanos y opera con la extensión de vinculum.';
    $('comp-symbol').textContent=c==='bases'?'₂ ₈ ₁₆':'Ⅻ';
    $('comp-choco').textContent=c==='bases'?'☕ Choco dice: 110.11 en binario tiene una parte fraccionaria.':'☕ Choco dice: (IV) representa 4000; cada nivel de paréntesis equivale a una barra superior.';
    if(c==='bases'){
      $('comp-controls').innerHTML=`${field('Sistema de origen',`<select id="comp-base">${options([[2,'Binario · base 2'],[8,'Octal · base 8'],[10,'Decimal · base 10'],[16,'Hexadecimal · base 16']],S.base)}</select>`)}
        ${field('Número a convertir',`<input id="comp-base-value" value="${safe(S.baseValue)}" autocomplete="off" spellcheck="false">`)}
        <p class="lab-hint">Acepta números negativos, enteros y fracciones como 110.11₂ o A.F₁₆. Utiliza punto o coma decimal.</p>`;
    }else{
      $('comp-controls').innerHTML=`${field('¿Qué deseas realizar?',`<select id="comp-roman-mode">${options([['convertir','Convertir números romanos'],['operar','Operaciones entre números']],S.romanMode)}</select>`)}
      ${S.romanMode==='convertir'?`${field('Tipo de entrada',`<select id="comp-roman-source">${options([['Arábigo','Arábigo → Romano'],['Romano','Romano → Arábigo']],S.romanSource)}</select>`)}
       ${field('Número',`<input id="comp-roman-value" value="${safe(S.romanValue)}" autocomplete="off" spellcheck="false">`)}`:
      `<div class="lab-two-inputs">${field('Primer tipo',`<select id="comp-roman-type-a">${options([['Romano','Romano'],['Arábigo','Arábigo']],S.romanAType)}</select>`)}${field('Segundo tipo',`<select id="comp-roman-type-b">${options([['Romano','Romano'],['Arábigo','Arábigo']],S.romanBType)}</select>`)}</div>
      <div class="lab-two-inputs">${field('Primer número',`<input id="comp-roman-a" value="${safe(S.romanA)}">`)}${field('Segundo número',`<input id="comp-roman-b" value="${safe(S.romanB)}">`)}</div>
      ${field('Operación',`<select id="comp-roman-op">${options([['+','Suma +'],['-','Resta −'],['*','Multiplicación ×'],['/','División ÷']],S.romanOperator)}</select>`)}`}
      <div class="lab-inline-actions"><button type="button" id="comp-roman-wrap" class="lab-small-btn">( ) Vinculum ×1000</button><button type="button" id="comp-roman-double" class="lab-small-btn">(( )) Vinculum ×10⁶</button></div>
      <p class="lab-hint">Para valores mayores de 3999, una barra superior multiplica por 1000. Puedes escribir (IV) o ((IV)); los símbolos ↀ, ↁ, ↂ también se reconocen.</p>`;
    }
    $('comp-submit').textContent=c==='bases'?'Convertir entre bases →':S.romanMode==='convertir'?'Convertir números →':'Calcular operación →';
    if(S.compLast)drawCompLast();
  }
  async function send(endpoint,data){
    const rsp=await fetch('/api/lab/'+endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
    const json=await rsp.json();if(!json.ok)throw Error(json.error||'No se pudo resolver el ejercicio.');return json.resultado;
  }
  function compCapture(){
    if($('comp-base'))S.base=$('comp-base').value;
    if($('comp-base-value'))S.baseValue=$('comp-base-value').value;
    if($('comp-roman-mode'))S.romanMode=$('comp-roman-mode').value;
    if($('comp-roman-source'))S.romanSource=$('comp-roman-source').value;
    if($('comp-roman-value'))S.romanValue=$('comp-roman-value').value;
    if($('comp-roman-type-a'))S.romanAType=$('comp-roman-type-a').value;
    if($('comp-roman-type-b'))S.romanBType=$('comp-roman-type-b').value;
    if($('comp-roman-a'))S.romanA=$('comp-roman-a').value;
    if($('comp-roman-b'))S.romanB=$('comp-roman-b').value;
    if($('comp-roman-op'))S.romanOperator=$('comp-roman-op').value;
  }
  function drawCompLast(){
    const r=S.compLast;if(!r)return;let html='',steps=[];
    if(r.tipo==='bases'){
      const n={'10':'Decimal','2':'Binario','8':'Octal','16':'Hexadecimal'};
      html=`<div class="lab-inline-matrices">${Object.entries(r.equivalencias).map(([base,v])=>block(`${n[base]} · base ${base}`,`<div class="lab-result-title">${safe(v)}<sub>${base}</sub></div>`)).join('')}</div>`;
      steps=[{title:`Número de origen: ${r.entrada} en base ${r.base}`},{title:'Expansión posicional',text:r.expansion}];
      Object.entries(r.desarrollo).forEach(([base,list])=>{steps.push({title:`Conversión a base ${base}`});list.forEach(x=>steps.push({title:x}));});
    }else if(r.tipo==='romanos'){
      html=block('Número arábigo',`<div class="lab-result-title">${safe(r.arabigo)}</div>`)+block('Número romano',`<div class="lab-result-title">${safe(r.romano)}</div>`)+block('Escritura alternativa de teclado',`<div class="lab-result-title">${safe(r.teclado)}</div>`);
      steps=(r.desarrollo||[]).map(g=>({title:`Bloque ${g.bloque}: ${g.valor}`,text:`Nivel de vinculum ${g.nivel} → multiplica por 1000^${g.nivel}`}));steps.push({title:r.nota});
    }else if(r.tipo==='roman_operacion'){
      html=block('Resultado arábigo',`<div class="lab-result-title">${safe(r.a)} ${safe(r.operador)} ${safe(r.b)} = ${safe(r.resultado)}</div>`);
      html+=block('Representación romana',`<div class="lab-result-title">${safe(r.romano||'No se representa como romano')}</div>${r.teclado?`<p>Teclado: ${safe(r.teclado)}</p>`:''}`);
      steps=[{title:`Interpretar el primer número: ${r.a} = ${r.roman_a}`},{title:`Interpretar el segundo número: ${r.b} = ${r.roman_b}`},{title:`Aplicar la operación: ${r.a} ${r.operador} ${r.b} = ${r.resultado}`}];
      if(r.nota)steps.push({title:r.nota});
    }
    $('comp-visual').innerHTML=html;$('comp-status').textContent='Conversión completada';
    $('comp-steps').innerHTML=steps.map((p,i)=>`<div class="lab-step-card" style="cursor:default"><div class="lab-step-top"><span>Paso ${i+1}</span></div><div class="lab-step-description">${safe(p.title)}</div>${p.text?`<div class="lab-step-description">${safe(p.text)}</div>`:''}</div>`).join('');
    S.compExportText=steps.map((p,i)=>`${i+1}. ${p.title} ${p.text||''}`).join('\n');$('comp-export').disabled=false;
  }
  async function solveComplement(){
    compCapture();clearNotice(true);const btn=$('comp-submit');btn.disabled=true;btn.textContent='Calculando…';
    try{
      let action=S.comp,data;
      if(action==='bases')data={base:S.base,numero:S.baseValue};
      else if(S.romanMode==='convertir')data={modo:'convertir',origen:S.romanSource,valor:S.romanValue};
      else data={modo:'operar',a:S.romanA,b:S.romanB,tipo_a:S.romanAType,tipo_b:S.romanBType,operador:S.romanOperator};
      S.compLast=await send(action,data);drawCompLast();notify('Conversión realizada correctamente.',false,true);
    }catch(e){notify(e.message,true,true);$('comp-status').textContent='Revisa los datos';}
    finally{btn.disabled=false;btn.textContent=S.comp==='bases'?'Convertir entre bases →':S.romanMode==='convertir'?'Convertir números →':'Calcular operación →';}
  }
  function downloadText(content,name){
    const blob=new Blob([content],{type:'text/plain;charset=utf-8'}),url=URL.createObjectURL(blob);
    const a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  function onClick(e){
    const button=e.target.closest('button');if(!button)return;
    const tool=button.dataset.linearTool;
    if(tool==='bases'||tool==='romanos'){
      S.comp=tool;S.compLast=null;$('comp-status').textContent='Sin calcular';$('comp-export').disabled=true;
      $('comp-visual').innerHTML='<div class="lab-empty"><span>Ⅰ</span><strong>Introduce los datos para comenzar.</strong></div>';
      $('comp-steps').innerHTML='<div class="empty-cell">El procedimiento aparecerá después de calcular.</div>';renderComplement();
    }
    if(button.id==='comp-submit'){solveComplement();return;}
    if(button.id==='comp-clear'){S.compLast=null;if(S.comp==='bases')S.baseValue='';else S.romanValue='';renderComplement();$('comp-visual').innerHTML='<div class="lab-empty">Datos limpios.</div>';$('comp-steps').innerHTML='';$('comp-export').disabled=true;return;}
    if(button.id==='comp-export'){downloadText('CHOCO LAB · TEMAS COMPLEMENTARIOS\n\n'+S.compExportText,'ChocoLab_conversion.txt');return;}
    if(['comp-roman-wrap','comp-roman-double'].includes(button.id)){
      const fieldId=S.romanMode==='convertir'?'comp-roman-value':'comp-roman-a';const input=$(fieldId);if(!input)return;
      const n=button.id==='comp-roman-double'?2:1,a=input.selectionStart??0,b=input.selectionEnd??0;
      const selected=input.value.slice(a,b)||'IV';input.value=input.value.slice(0,a)+'('.repeat(n)+selected+')'.repeat(n)+input.value.slice(b);
      input.focus();compCapture();return;
    }
  }
  function init(){
    document.addEventListener('click',onClick);
    document.addEventListener('change',e=>{
      if(['comp-roman-mode','comp-roman-source','comp-roman-type-a','comp-roman-type-b'].includes(e.target.id)){
        compCapture();renderComplement();
      }
    });
    const ram=async()=>{
      try{const rsp=await fetch('/api/lab/ram');const r=await rsp.json();if(r.ok&&$('lab-ram'))$('lab-ram').textContent=`RAM Python: ${r.mb} MB`;}catch(_){/* no disponible */}
    };
    ram();window.setInterval(ram,12000);
  }
  document.addEventListener('DOMContentLoaded',init);
})();
