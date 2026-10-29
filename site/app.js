// N64 Open Labels gallery: filter, pick labels, build an actual-size PDF in the browser.
(function(){
 const LABEL_W=63,LABEL_H=16;
 const PAPER={a4:{w:210,h:297,name:'A4'},letter:{w:215.9,h:279.4,name:'US Letter'}};
 const $=s=>document.querySelector(s);
 const state={labels:[],byId:{},repo:'',q:'',region:'All',stage:'All',picked:new Set()};

 const store={
  get(k){try{return localStorage.getItem(k)}catch(e){return null}},
  set(k,v){try{localStorage.setItem(k,v)}catch(e){}}
 };

 function toast(msg){const t=$('#toast');t.textContent=msg;t.hidden=false;clearTimeout(toast.t);toast.t=setTimeout(()=>t.hidden=true,2600)}

 function chips(el,values,key){
  el.innerHTML='';
  for(const v of values){
   const b=document.createElement('button');b.type='button';b.className='chip';b.textContent=v;
   b.setAttribute('aria-pressed',String(state[key]===v));
   b.onclick=()=>{state[key]=v;chips(el,values,key);render()};
   el.appendChild(b);
  }
 }

 function visible(){
  const q=state.q.trim().toLowerCase();
  return state.labels.filter(l=>(state.region==='All'||l.region===state.region)&&
   (state.stage==='All'||l.stage===state.stage.toLowerCase())&&
   (!q||l.title.toLowerCase().includes(q)||l.sort.includes(q)));
 }

 function issueUrl(l){
  const title=encodeURIComponent(`Label: ${l.title} (${l.region})`);
  const body=encodeURIComponent(`**Game:** ${l.title}\n**Region:** ${l.region}\n**Label:** ${location.origin}${location.pathname.replace(/[^/]*$/,'')}${l.png}\n\nWhat looks wrong (crop, colours, logo, fit after printing)?\n`);
  return `https://github.com/${state.repo}/issues/new?title=${title}&body=${body}`;
 }

 function card(l){
  const c=document.createElement('article');c.className='cart'+(state.picked.has(l.id)?' picked':'');c.dataset.id=l.id;
  const picked=state.picked.has(l.id);
  c.innerHTML=`<img class="label" loading="lazy" decoding="async" width="640" height="163" alt="${esc(l.title)} end label">
   <div class="ridges" aria-hidden="true"></div>
   <h3></h3>
   <div class="meta"><span class="badge region">${l.region}</span><span class="badge ${l.stage}">${l.stage}</span></div>
   <div class="actions">
    <button type="button" class="btn add" aria-pressed="${picked}">${picked?'✓ On sheet':'+ Add to sheet'}</button>
    <a class="btn ghost" download>PNG</a>
    <a class="btn ghost" target="_blank" rel="noopener" title="Report a problem with this label">Report</a>
   </div>`;
  c.querySelector('img').src=l.thumb;
  c.querySelector('h3').textContent=l.title;
  const [png,report]=c.querySelectorAll('a');png.href=l.png;report.href=issueUrl(l);
  c.querySelector('.add').onclick=()=>toggle(l.id);
  return c;
 }

 function esc(s){return s.replace(/[&<>"]/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[ch]))}

 function render(){
  const list=visible(),grid=$('#grid');grid.innerHTML='';
  const groups=new Map();
  for(const l of list){if(!groups.has(l.letter))groups.set(l.letter,[]);groups.get(l.letter).push(l)}
  const frag=document.createDocumentFragment();
  for(const [letter,items] of groups){
   const h=document.createElement('div');h.className='group-head';h.id='letter-'+letter;
   const sheets=[...new Set(items.filter(i=>i.region==='USA').map(i=>i.sheet))];
   h.innerHTML=`<h2>${letter}</h2>`+(sheets.length?`<a href="${sheets[0]}" download>Full ${letter} sheet, A4 PDF</a>`:'');
   frag.appendChild(h);
   for(const l of items)frag.appendChild(card(l));
  }
  grid.appendChild(frag);
  $('#empty').hidden=list.length>0;
  const present=new Set(list.map(l=>l.letter));
  const letters=$('#letters');letters.innerHTML='';
  for(const L of ['0-9',...'ABCDEFGHIJKLMNOPQRSTUVWXYZ']){
   const e=document.createElement(present.has(L)?'a':'span');e.textContent=L;
   if(present.has(L))e.href='#letter-'+L;
   letters.appendChild(e);
  }
 }

 function toggle(id){
  state.picked.has(id)?state.picked.delete(id):state.picked.add(id);
  save();
  const c=document.querySelector(`.cart[data-id="${CSS.escape(id)}"]`);
  if(c){const on=state.picked.has(id);c.classList.toggle('picked',on);const b=c.querySelector('.add');b.setAttribute('aria-pressed',String(on));b.textContent=on?'✓ On sheet':'+ Add to sheet'}
 }

 function save(){
  store.set('n64ol.picked',[...state.picked].join(','));
  const n=state.picked.size;$('#tray').hidden=n===0;$('#count').textContent=n;$('#count-word').textContent=n===1?'label':'labels';
 }

 async function dataUrl(src){
  const blob=await (await fetch(src)).blob();
  return new Promise((ok,fail)=>{const r=new FileReader();r.onload=()=>ok(r.result);r.onerror=fail;r.readAsDataURL(blob)});
 }

 function layout(paper){
  const margin=7,gapX=2,gapY=4,top=20,bottom=16;
  const cols=Math.floor((paper.w-2*margin+gapX)/(LABEL_W+gapX));
  const rows=Math.floor((paper.h-top-bottom+gapY)/(LABEL_H+gapY));
  const x0=(paper.w-(cols*LABEL_W+(cols-1)*gapX))/2;
  return {cols,rows,x0,top,gapX,gapY};
 }

 function marks(doc,x,y){
  doc.setDrawColor(150);doc.setLineWidth(.15);
  for(const [cx,dx] of [[x,-1],[x+LABEL_W,1]])for(const [cy,dy] of [[y,-1],[y+LABEL_H,1]]){
   doc.line(cx+dx*.4,cy,cx+dx*1.4,cy);doc.line(cx,cy+dy*.4,cx,cy+dy*1.4);
  }
 }

 function pageFrame(doc,paper,page,pages){
  doc.setFont('helvetica','bold');doc.setFontSize(11);doc.setTextColor(30);
  doc.text('N64 OPEN LABELS',7,10);
  doc.setFont('helvetica','normal');doc.setFontSize(7.5);doc.setTextColor(80);
  doc.text(`63 x 16 mm labels on ${paper.name}. Print at 100% / actual size, no "fit to page".   Page ${page}/${pages}`,7,14.5);
  const y=paper.h-9;doc.setDrawColor(40);doc.setLineWidth(.3);doc.line(7,y,57,y);
  for(let i=0;i<=10;i++)doc.line(7+i*5,y,7+i*5,y-(i%2?1:2));
  doc.text('This line must measure 50 mm.',60,y);
  doc.text(location.host+location.pathname,paper.w-7,paper.h-4,{align:'right'});
 }

 async function buildPdf(){
  const btn=$('#pdf');if(!window.jspdf){toast('PDF library failed to load. Check your connection.');return}
  const items=[...state.picked].map(id=>state.byId[id]).filter(Boolean).sort((a,b)=>a.sort.localeCompare(b.sort));
  if(!items.length)return;
  const paper=PAPER[$('#paper').value],L=layout(paper),per=L.cols*L.rows,pages=Math.ceil(items.length/per);
  btn.disabled=true;
  try{
   const doc=new jspdf.jsPDF({unit:'mm',format:[paper.w,paper.h],compress:true});
   for(let i=0;i<items.length;i++){
    btn.textContent=`Building ${i+1}/${items.length}…`;
    const k=i%per;
    if(k===0){if(i)doc.addPage([paper.w,paper.h]);pageFrame(doc,paper,i/per+1,pages)}
    const x=L.x0+(k%L.cols)*(LABEL_W+L.gapX),y=L.top+Math.floor(k/L.cols)*(LABEL_H+L.gapY);
    doc.addImage(await dataUrl(items[i].png),'PNG',x,y,LABEL_W,LABEL_H,items[i].id,'FAST');
    marks(doc,x,y);
   }
   doc.save(`n64-labels-${items.length}-${$('#paper').value}.pdf`);
   toast(`PDF ready: ${items.length} labels on ${pages} page${pages>1?'s':''}`);
  }catch(e){console.error(e);toast('Could not build the PDF. Try again or use the letter PDFs.')}
  finally{btn.disabled=false;btn.textContent='Download PDF'}
 }

 async function init(){
  const data=await (await fetch('labels.json')).json();
  state.labels=data.labels;state.repo=data.repo;
  for(const l of data.labels)state.byId[l.id]=l;
  $('#repo-link').href=`https://github.com/${data.repo}`;
  $('#issue-link').href=`https://github.com/${data.repo}/issues/new?title=${encodeURIComponent('Missing label: ')}`;
  $('#missing-list').textContent=data.missing.length?data.missing.join(', ')+'.':'Nothing, every catalogued game has a label.';
  const usa=data.labels.filter(l=>l.region==='USA').length,approved=data.labels.filter(l=>l.stage==='approved').length;
  $('#stats').textContent=`${usa} US games · ${data.labels.length-usa} Japanese · ${approved} hand-tuned · 100% free`;
  const regions=['All',...new Set(data.labels.map(l=>l.region))];
  chips($('#region'),regions,'region');chips($('#stage'),['All','Approved','Draft'],'stage');
  // A shared link (?sheet=id,id) wins over the saved selection.
  const shared=new URLSearchParams(location.search).get('sheet');
  for(const id of (shared||store.get('n64ol.picked')||'').split(','))if(state.byId[id])state.picked.add(id);
  const paper=store.get('n64ol.paper');if(paper&&PAPER[paper])$('#paper').value=paper;
  $('#paper').onchange=e=>store.set('n64ol.paper',e.target.value);
  $('#q').oninput=e=>{state.q=e.target.value;render()};
  $('#pdf').onclick=buildPdf;
  $('#clear').onclick=()=>{state.picked.clear();save();render()};
  $('#share').onclick=async()=>{
   const url=`${location.origin}${location.pathname}?sheet=${[...state.picked].join(',')}`;
   try{await navigator.clipboard.writeText(url);toast('Link copied')}catch(e){prompt('Copy this link:',url)}
  };
  render();save();
 }
 init().catch(e=>{console.error(e);$('#grid').textContent='Could not load the label list.'});
})();
