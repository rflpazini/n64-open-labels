// N64 Open Labels: find games, tap to select, build an actual-size PDF in the browser.
(function(){
 const LABEL_W=63,LABEL_H=16;
 const PAPER={a4:{w:210,h:297,name:'A4'},letter:{w:215.9,h:279.4,name:'US Letter'}};
 const $=s=>document.querySelector(s);
 const state={labels:[],byId:{},repo:'',q:'',region:'USA',regions:[],picked:new Set()};

 const store={
  get(k){try{return localStorage.getItem(k)}catch(e){return null}},
  set(k,v){try{localStorage.setItem(k,v)}catch(e){}}
 };

 function toast(msg){const t=$('#toast');t.textContent=msg;t.hidden=false;clearTimeout(toast.t);toast.t=setTimeout(()=>t.hidden=true,2600)}

 // US and Canada print on Letter; nearly everyone else uses A4.
 function defaultPaper(){
  const lang=(navigator.languages&&navigator.languages[0])||navigator.language||'';
  return /-(US|CA|MX|PH)$/i.test(lang)?'letter':'a4';
 }
 function defaultRegion(){
  const lang=(navigator.languages&&navigator.languages[0])||navigator.language||'';
  return /^ja\b/i.test(lang)?'Japan':'USA';
 }
 const REGION_LABEL={USA:'USA',Japan:'Japan'};
 function regionTabs(){
  const el=$('#region');el.innerHTML='';
  for(const r of state.regions){
   const b=document.createElement('button');b.type='button';b.textContent=REGION_LABEL[r]||r;
   b.setAttribute('aria-pressed',String(state.region===r));
   b.onclick=()=>{state.region=r;store.set('n64ol.region',r);regionTabs();render()};
   el.appendChild(b);
  }
 }

 function normalize(s){return s.toLowerCase().normalize('NFKD').replace(/[̀-ͯ]/g,'').replace(/[^a-z0-9]+/g,' ').trim()}

 function visible(){
  const q=normalize(state.q);
  return state.labels.filter(l=>l.region===state.region&&(!q||l.search.includes(q)));
 }

 function issueUrl(l){
  const title=encodeURIComponent(`Label: ${l.title} (${l.region})`);
  const body=encodeURIComponent(`**Game:** ${l.title}\n**Region:** ${l.region}\n**Label:** ${new URL(l.png,location.href)}\n\nWhat looks wrong (crop, colours, logo, fit after printing)?\n`);
  return `https://github.com/${state.repo}/issues/new?title=${title}&body=${body}`;
 }

 function card(l){
  const on=state.picked.has(l.id);
  const c=document.createElement('article');c.className='card';c.dataset.id=l.id;
  c.innerHTML=`<button type="button" class="pick" aria-pressed="${on}">
    <img loading="lazy" decoding="async" width="640" height="163" alt="">
    <span class="state" aria-hidden="true"><svg class="ico"><use href="#i-${on?'check':'plus'}"/></svg></span>
   </button>
   <div class="card-meta"><h3></h3><span class="card-links"><a download>PNG</a><a target="_blank" rel="noopener">Report</a></span></div>`;
  const btn=c.querySelector('.pick'),img=c.querySelector('img');
  img.src=l.thumb;
  btn.setAttribute('aria-label',`${l.title}: ${on?'selected, tap to remove':'tap to add to your sheet'}`);
  c.querySelector('h3').textContent=l.title;
  const [png,report]=c.querySelectorAll('.card-links a');
  png.href=l.png;png.setAttribute('aria-label',`Download ${l.title} PNG`);
  report.href=issueUrl(l);report.setAttribute('aria-label',`Report a problem with ${l.title}`);
  btn.onclick=()=>toggle(l.id);
  return c;
 }

 function render(){
  const list=visible(),grid=$('#grid');grid.innerHTML='';
  const groups=new Map();
  for(const l of list){if(!groups.has(l.letter))groups.set(l.letter,[]);groups.get(l.letter).push(l)}
  const frag=document.createDocumentFragment();
  for(const [letter,items] of groups){
   const h=document.createElement('div');h.className='group-head';h.id='letter-'+letter;
   h.innerHTML=`<h2>${letter}</h2>`;
   const sheet=items[0];
   if(sheet&&!state.q){const a=document.createElement('a');a.href=sheet.sheet;a.download='';a.textContent=`All ${letter} games (A4 PDF)`;h.appendChild(a)}
   frag.appendChild(h);
   for(const l of items)frag.appendChild(card(l));
  }
  grid.appendChild(frag);
  const empty=list.length===0;
  $('#empty').hidden=!empty;$('#empty-q').textContent=state.q.trim();
  $('#result-line').textContent=empty?'':state.q.trim()?`${list.length} game${list.length===1?'':'s'} found`:`${list.length} ${state.region==='USA'?'US':'Japanese'} games. Tap a label to add it to your sheet.`;
  const present=new Set(list.map(l=>l.letter)),letters=$('#letters');letters.innerHTML='';
  for(const L of ['0-9',...'ABCDEFGHIJKLMNOPQRSTUVWXYZ']){
   const e=document.createElement(present.has(L)?'a':'span');e.textContent=L;
   if(present.has(L))e.href='#letter-'+L;else e.setAttribute('aria-hidden','true');
   letters.appendChild(e);
  }
 }

 function toggle(id){
  state.picked.has(id)?state.picked.delete(id):state.picked.add(id);
  save();
  const c=document.querySelector(`.card[data-id="${CSS.escape(id)}"]`);
  if(c){
   const on=state.picked.has(id),l=state.byId[id],btn=c.querySelector('.pick');
   btn.setAttribute('aria-pressed',String(on));
   btn.setAttribute('aria-label',`${l.title}: ${on?'selected, tap to remove':'tap to add to your sheet'}`);
   btn.querySelector('use').setAttribute('href',on?'#i-check':'#i-plus');
  }
 }

 function save(){
  store.set('n64ol.picked',[...state.picked].join(','));
  const n=state.picked.size;
  $('#tray').hidden=n===0;document.body.classList.toggle('has-tray',n>0);
  $('#count').textContent=n;$('#count-word').textContent=n===1?'label':'labels';
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
  const btn=$('#pdf'),label=btn.querySelector('span');
  if(!window.jspdf){toast('The PDF tool did not load. Check your connection and reload.');return}
  const items=[...state.picked].map(id=>state.byId[id]).filter(Boolean).sort((a,b)=>a.sort.localeCompare(b.sort));
  if(!items.length)return;
  const key=$('#paper').value,paper=PAPER[key],L=layout(paper),per=L.cols*L.rows,pages=Math.ceil(items.length/per);
  btn.disabled=true;
  try{
   const doc=new jspdf.jsPDF({unit:'mm',format:[paper.w,paper.h],compress:true});
   for(let i=0;i<items.length;i++){
    label.textContent=`Preparing ${i+1} of ${items.length}…`;
    const k=i%per;
    if(k===0){if(i)doc.addPage([paper.w,paper.h]);pageFrame(doc,paper,i/per+1,pages)}
    const x=L.x0+(k%L.cols)*(LABEL_W+L.gapX),y=L.top+Math.floor(k/L.cols)*(LABEL_H+L.gapY);
    doc.addImage(await dataUrl(items[i].png),'PNG',x,y,LABEL_W,LABEL_H,items[i].id,'FAST');
    marks(doc,x,y);
   }
   doc.save(`n64-labels-${items.length}-${key}.pdf`);
   if(store.get('n64ol.tips')!=='off'&&$('#tips').showModal)$('#tips').showModal();
   else toast(`PDF ready: ${items.length} label${items.length>1?'s':''} on ${pages} page${pages>1?'s':''}`);
  }catch(e){console.error(e);toast('Could not make the PDF. Try again, or use the letter PDFs.')}
  finally{btn.disabled=false;label.textContent='Download PDF'}
 }

 async function init(){
  const data=await (await fetch('labels.json')).json();
  state.repo=data.repo;
  state.labels=data.labels.map(l=>Object.assign(l,{search:normalize(`${l.title} ${l.sort} ${l.region}`)}));
  for(const l of state.labels)state.byId[l.id]=l;
  for(const id of ['#repo-link','#foot-repo'])$(id).href=`https://github.com/${data.repo}`;
  $('#empty-issue').href=`https://github.com/${data.repo}/issues/new?title=${encodeURIComponent('Missing label: ')}`;
  $('#missing-list').textContent=data.missing.length?`These have no label yet: ${data.missing.join(', ')}. Know where to find a clean logo? Open an issue on GitHub.`:'None. Every US and Japanese retail cartridge in the catalog has a label. Europe is next.';
  state.regions=data.regions||[...new Set(state.labels.map(l=>l.region))];
  const savedRegion=store.get('n64ol.region');
  state.region=state.regions.includes(savedRegion)?savedRegion:defaultRegion();
  regionTabs();
  // A shared link (?sheet=id,id) wins over the saved selection.
  const shared=new URLSearchParams(location.search).get('sheet');
  for(const id of (shared||store.get('n64ol.picked')||'').split(','))if(state.byId[id])state.picked.add(id);
  // Open a shared link on the region its labels come from.
  if(shared&&state.picked.size){state.region=state.byId[[...state.picked][0]].region;regionTabs()}
  $('#paper').value=store.get('n64ol.paper')||defaultPaper();
  $('#paper').onchange=e=>store.set('n64ol.paper',e.target.value);
  let t;$('#q').oninput=e=>{state.q=e.target.value;clearTimeout(t);t=setTimeout(render,120)};
  $('#empty-clear').onclick=()=>{state.q='';$('#q').value='';render();$('#q').focus()};
  $('#pdf').onclick=buildPdf;
  $('#clear').onclick=()=>{state.picked.clear();save();render()};
  $('#tips').addEventListener('close',()=>{if($('#tips-off').checked)store.set('n64ol.tips','off')});
  $('#share').onclick=async()=>{
   const url=`${location.origin}${location.pathname}?sheet=${[...state.picked].join(',')}`;
   try{await navigator.clipboard.writeText(url);toast('Link copied. Anyone with it sees your selection.')}catch(e){prompt('Copy this link:',url)}
  };
  render();save();
 }
 init().catch(e=>{console.error(e);$('#grid').textContent='Could not load the label list. Please reload the page.'});
})();
