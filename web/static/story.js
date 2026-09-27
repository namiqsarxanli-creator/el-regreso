/* Story features share the existing graph renderer and socket. */
const $ = (id) => document.getElementById(id);
const textNode = (tag, text, cls) => { const e = document.createElement(tag); e.textContent = text; if (cls) e.className = cls; return e; };
let profiles = [], currentValues = {}, branchRows = [], activeBranch = null, busy = false, waiting = false, loadVersion = 0;
let draft = [], draftKey = '';
let forgettingPerson = null;
const forgottenPortraits = new Set();
let speechContext=null, speechSource=null, speechGain=null, speechRequest=null, speechVersion=0, speechLoading=false;
const characterVoices={abuela:'Nənənin səsi',donchuy:'Babanın səsi',mateo:'Uşaq səsi',tio:'Əminin səsi'};
const meanings = {
 'cempasúchil':'Narıncı ləçəklər ruhun evə gələn yolunu göstərir.', 'su':'Uzun yoldan gələn ruh üçün su.',
 'duz':'Altarın təmizlik və qorunma rəmzi.', 'pan de muerto':'Görüş üçün hazırlanan ənənəvi çörək.',
 'copal':'Tanış buxur qoxusu evi xatırladır.', 'şam':'Qaranlıqda yanan xatirə işığı.', 'şəkil':'Sevdiyimiz insanın görünən xatirəsi.',
 'mezcal':'Böyüklər üçün xatirə içkisi.', 'siqaret':'Tanış bir vərdişin izi.', 'tamales':'Ailə süfrəsindən bir pay.',
 'qəhvə':'Köhnə söhbətlərin tanış qoxusu.', 'süd':'Uşaq altarına qoyulan içki.', 'şokolad':'Uşaqlığın şirin xatirəsi.',
 'şəkər kəllə':'Həyatı xatırladan rəngli bayram şirniyyatı.', 'oyuncaq':'Uşaqlıq sevincindən bir parça.', 'meyvə':'Süfrəyə gətirilən təzə pay.'
};
const icons = {'cempasúchil':'✿','su':'◈','duz':'△','pan de muerto':'◒','copal':'≋','şam':'♧','şəkil':'▣','mezcal':'♜','siqaret':'≋','tamales':'◒','qəhvə':'☕','süd':'◈','şokolad':'▦','şəkər kəllə':'☠','oyuncaq':'✧','meyvə':'❧'};
function soulName() { return $('soul').value; }
function profile() { return profiles.find(s=>s.name===soulName()); }
function storeDraft() { try { localStorage.setItem(draftKey, JSON.stringify(draft)); } catch {} }
function prepareDraft() {
 const p=profile(); if(!p) return;
 draftKey=`el-regreso:altar:${p.name}:${$('year').value}`;
 draft=[...(p.offerings?.[$('year').value]||[])];
 try {const saved=JSON.parse(localStorage.getItem(draftKey)); if(Array.isArray(saved)&&saved.every(x=>Object.hasOwn(meanings,x))) draft=[...new Set(saved)];} catch {}
 renderDraft();
}
function renderDraft() {
 $('draft-items').replaceChildren();
 draft.forEach(item=>{const b=textNode('button',`${icons[item]||'✦'} ${item} ×`,'draft-gift'); b.title=`${item} — altardan götür`; b.disabled=busy||!!activeBranch||waiting; b.onclick=()=>{draft=draft.filter(x=>x!==item);storeDraft();renderDraft();};$('draft-items').append(b);});
 $('draft-count').textContent=`· ${draft.length} əşya`;
 $('draft-note').textContent=draft.includes('cempasúchil')?'Ləçək yolu hazırdır.': 'Cempasúchil yoxdur — ruh yolu itirib ailənin köməyini gözləyə bilər.';
 $('draft-year').textContent=`${profile()?.display||''} · ${$('year').value}`;
 $('gift-catalog').replaceChildren();
 Object.entries(meanings).filter(([name])=>profile()?.kind!=='angelito'||!['mezcal','siqaret'].includes(name)).forEach(([name,meaning])=>{
  const b=document.createElement('button'); b.type='button'; b.className='gift-choice'; b.draggable=!busy&&!waiting&&!activeBranch; b.disabled=busy||waiting||!!activeBranch; b.setAttribute('aria-pressed',String(draft.includes(name)));
  b.append(textNode('span',icons[name],'gift-icon'),textNode('strong',name),textNode('small',meaning));
  b.onclick=()=>addGift(name); b.ondragstart=e=>e.dataTransfer.setData('text/plain',name); $('gift-catalog').append(b);
 });
}
function addGift(name) {if(busy||waiting||activeBranch||!Object.hasOwn(meanings,name))return;if(!draft.includes(name)){draft.push(name);storeDraft();renderDraft();}}
$('offering-drop').ondragover=e=>{e.preventDefault();if(!busy&&!waiting&&!activeBranch)$('offering-drop').classList.add('drag-over');};
$('offering-drop').ondragleave=()=>$('offering-drop').classList.remove('drag-over');
$('offering-drop').ondrop=e=>{e.preventDefault();$('offering-drop').classList.remove('drag-over');addGift(e.dataTransfer.getData('text/plain'));};
$('reset-offering').onclick=()=>{draft=[...(profile()?.offerings?.[$('year').value]||[])];storeDraft();renderDraft();};
function renderProfile() {
 const p=profile();if(!p)return;
 $('soul-heading').textContent=p.display;
 $('soul-bio').textContent=p.bio||'';
 $('soul-favorites').textContent=`${p.relation} · Sevdiyi hədiyyələr: ${(p.favorites||[]).join(', ')}`;
 $('soul-portrait').style.backgroundPosition=`${(p.portrait||0)*100/3}% center`;
 $('soul-portrait').setAttribute('aria-label',`${p.display} üçün bədii portret`);
 $('soul-portrait').classList.toggle('soul-forgotten',forgottenPortraits.has(p.name));
 if(forgottenPortraits.has(p.name))$('soul-portrait').setAttribute('aria-label',`${p.display} uzaqlaşdı — cempasúchil xatirəsi`);
 $('character-voice').textContent=`${characterVoices[p.name]||p.display} · İspanca`;
}
function renderAlbum(values) {
 const visits=values.visits||[]; $('album-cards').replaceChildren();
 $('album-context').textContent=activeBranch?'Alternativ budağın xatirələri':'Əsas hekayənin xatirələri';
 if(!visits.length){$('album-cards').append(textNode('p','Hələ ziyarət yoxdur. İlk gecə bitəndə albomun ilk səhifəsi yaranacaq.','empty-state'));return;}
 visits.map((v,i)=>({v,i})).reverse().forEach(({v,i})=>{
  const card=textNode('article','','album-card');
  card.append(textNode('span',`XATİRƏ ${String(i+1).padStart(2,'0')}`,'eyebrow'),textNode('h3',String(v.year)),textNode('p',v.arrived?'Evə qayıtdı':'Yolu tapa bilmədi','arrival'));
  card.append(textNode('p',`Xatırlanma ${v.remembrance??'—'}/100 · İstilik ${v.warmth??'—'}/100`,'visit-stats'));
  const tags=textNode('div','','album-gifts');(v.ofrenda||[]).forEach(x=>tags.append(textNode('span',x)));card.append(tags);
  const details=document.createElement('details');details.append(textNode('summary','Sözləri və şeiri aç'));
  details.append(textNode('blockquote',v.words||v.note||'Bu ziyarətdə söz qeydə alınmayıb.'));
  if(!v.words&&v.note)details.append(textNode('small','Köhnə qeyddə sözlərin yalnız qısa hissəsi saxlanıb.'));
  details.append(textNode('pre',v.calaverita||'Bu ziyarətin şeiri ayrıca saxlanmayıb.'));
  card.append(details);$('album-cards').append(card);
 });
}
function outcomeCard(title,values) {
 const c=textNode('article','','outcome-card');c.append(textNode('h3',title));
 c.append(textNode('p',`${values.year??'—'} · ${values.arrived?'Evə qayıtdı':'Görüş baş tutmayıb'}`));
 c.append(textNode('strong',`Xatırlanma: ${values.remembrance??'—'}/100`),textNode('p',`İstilik: ${values.judgement?.warmth??'—'}/100`));
 c.append(textNode('p',(values.ofrenda||[]).join(' · ')||'Boş altar'),textNode('blockquote',values.words||'Hələ söz yoxdur.'));
 const d=document.createElement('details');d.append(textNode('summary','Şeiri göstər'),textNode('pre',values.calaverita||'Şeir yoxdur.'));c.append(d);return c;
}
function renderComparison() {
 const row=branchRows.find(r=>r.id===$('branch-select').value);$('comparison-cards').replaceChildren();$('resume-branch').hidden=true;
 $('return-main').hidden=!activeBranch;
 if(!row){$('comparison-diff').textContent='Müqayisə üçün əvvəl bir alternativ budaq yaradın.';return;}
 const a=row.baseline,b=row.values;
 const complete=row.complete;
 const added=(b.ofrenda||[]).filter(x=>!(a.ofrenda||[]).includes(x));
 const delta=(b.remembrance??0)-(a.remembrance??0);
 $('comparison-diff').textContent=complete?`Əlavə: ${added.join(', ')||'yoxdur'} · Xatırlanma fərqi: ${delta>0?'+':''}${delta} · İstilik fərqi: ${(b.judgement?.warmth??0)-(a.judgement?.warmth??0)}`:'Alternativ gecə hələ tamamlanmayıb. Nəticələr yekun deyil.';
 $('comparison-cards').append(outcomeCard('Əsas gecə',a),outcomeCard('Alternativ gecə',b));
 if(!complete&&!busy){$('resume-branch').hidden=false;$('resume-branch').onclick=()=>{activeBranch=row.id;loadState();};}
}
function setBranches(rows) {
 const previous=$('branch-select').value;branchRows=rows||[];$('branch-select').replaceChildren();
 if(!branchRows.length)$('branch-select').append(new Option('Hələ budaq yoxdur',''));
 branchRows.forEach((r,i)=>$('branch-select').append(new Option(`${r.year} · alternativ ${branchRows.length-i}`,r.id)));
 if(branchRows.some(r=>r.id===activeBranch))$('branch-select').value=activeBranch;
 else if(branchRows.some(r=>r.id===previous))$('branch-select').value=previous;
 renderComparison();
}
$('branch-select').onchange=renderComparison;
$('return-main').onclick=()=>{activeBranch=null;loadState();};
function setBusy(value) {
 busy=value;
 for(const id of ['soul','year','branch-select','return-main','resume-branch'])$(id).disabled=value;
 for(const id of ['run','run-prepared','reset-offering'])$(id).disabled=value||waiting||!!activeBranch;
 $('forget').disabled=value;
 $('fork').querySelector('button[type="submit"],button.primary').disabled=value;
 $('narrate').disabled=!currentValues.words||speechLoading||value;
 renderDraft();
}
function sendStory(message) {
 if(!ws||ws.readyState!==WebSocket.OPEN){toast('Serverə bağlantı yoxdur. Yenidən qoşulma gözlənilir.');return false;}
 if(busy)return false;
 ++loadVersion;setBusy(true);ws.send(JSON.stringify({...message,soul:soulName(),branch_id:activeBranch}));return true;
}
function runPrepared(){stopSpeech();sendStory({action:'run',year:$('year').value,gifts:draft});}
$('run').onclick=runPrepared;$('run-prepared').onclick=runPrepared;
$('forget').onclick=()=>{
 if(busy)return;
 stopSpeech();
 forgettingPerson={...profile()};
 SoulFarewell.prepare(forgettingPerson,Number($('volume').value)/100);
 if(!sendStory({action:'forget'})){SoulFarewell.cancel();forgettingPerson=null;}
};
$('ask-form').onsubmit=e=>{e.preventDefault();const gift=$('ask-input').value.trim();if(gift&&sendStory({action:'resume',gift})){$('ask').hidden=true;$('ask-input').value='';}};
$('fork').onsubmit=e=>{e.preventDefault();if(!selected)return;const gifts=$('fork-gift').value.split(',').map(x=>x.trim()).filter(Boolean);if(sendStory({action:'fork',checkpoint:selected.id,gifts}))$('fork').hidden=true;};
const baseHandle=handle;
handle=function(msg){
 if(msg.type==='forgotten'){
  const person=forgettingPerson;forgettingPerson=null;
  stopSpeech();clearInterval(soundTimer);ambientOn=false;
  if(master&&audioContext?.state!=='closed')master.gain.setTargetAtTime(0,audioContext.currentTime,.2);
  $('ambience').setAttribute('aria-pressed','false');$('ambience').textContent='♫ Atmosferi aç';
  $('audio-note').textContent='Son vida — həzin musiqi.';
  if(person)forgottenPortraits.add(person.name);
  setBusy(true);
  SoulFarewell.show().finally(()=>{
   baseHandle(msg);activeBranch=null;currentValues={};waiting=false;
   renderProfile();$('audio-note').textContent='Vida bitdi. Səs söndürüldü.';
   setBusy(false);loadState();
  });
  return;
 }
 if(msg.type==='fork')activeBranch=msg.branch_id||activeBranch;
 baseHandle(msg);
 if(msg.type==='interrupt'){waiting=true;setBusy(false);}
 if(msg.type==='start'){forgottenPortraits.delete(soulName());renderProfile();waiting=false;setBusy(true);}
 if(msg.type==='done'){stopSpeech();currentValues=msg.values;waiting=false;setBusy(false);renderAlbum(currentValues);loadState();}
 if(msg.type==='error'){SoulFarewell.cancel();forgettingPerson=null;setBusy(false);loadState();}
};
renderHistory=function(rows){
 history=rows||[];$('dots').replaceChildren();
 history.slice().reverse().forEach(row=>{const dot=textNode('button',row.can_fork?'✿':'','cp'+(row.can_fork?' forkable':''));dot.type='button';dot.disabled=busy||!!activeBranch||!row.can_fork;dot.title=`${row.year??'—'} · ${row.can_fork?'Bu altardan alternativ yarat':'Yaddaş anı'}`;dot.setAttribute('aria-label',dot.title);dot.onclick=()=>selectCheckpoint(row,dot);$('dots').append(dot);});
};
loadState=async function(){
 const version=++loadVersion; const soul=soulName(); if(!soul)return;
 try{
 const response=await fetch(`/api/state/${encodeURIComponent(soul)}${activeBranch?'?branch_id='+encodeURIComponent(activeBranch):''}`);
 if(!response.ok)throw new Error('Yaddaş yüklənmədi');const data=await response.json();if(version!==loadVersion)return;
 currentValues=data.values;waiting=!!data.interrupt;lastAltar=[];
 renderAltar(data.values.ofrenda||[]);renderMemory(data.values);renderVerdict(data.values);renderCalaverita(data.values);renderVoices(data.values);renderHistory(data.history);renderAlbum(data.values);setBranches(data.branches);
 $('words').hidden=!data.values.words;$('ask').hidden=!data.interrupt;
 if(data.interrupt){$('ask-text').textContent=data.interrupt.question;$('ask-hint').textContent=data.interrupt.hint;}
 $('graph-status').textContent=data.interrupt?'Ailənin hədiyyəsi gözlənilir':activeBranch?'Alternativ hekayə':'gözləyir';
 selected=null;$('fork').hidden=true;setBusy(false);
 }catch(err){toast(err.message);setBusy(false);}
};
loadSouls=async function(){
 try {const response=await fetch('/api/souls');if(!response.ok)throw new Error('Ruhlar yüklənmədi');profiles=await response.json();$('soul').replaceChildren();profiles.forEach(p=>$('soul').append(new Option(`${p.display} · ${p.kind}`,p.name)));
 $('soul').onchange=()=>{activeBranch=null;stopSpeech();resetGraph();$('year').replaceChildren();profile().years.forEach(y=>$('year').append(new Option(y,y)));renderProfile();prepareDraft();loadState();};
 $('year').onchange=prepareDraft;$('soul').onchange();
 }catch(e){toast(e.message);}
};

/* Ambient sound is synthesized locally: quiet chords and filtered candle noise. */
let audioContext=null, master=null, soundTimer=null, ambientOn=false;
async function toggleAmbience(){
 try{
 if(!audioContext){audioContext=new(window.AudioContext||window.webkitAudioContext)();master=audioContext.createGain();master.gain.value=0;master.connect(audioContext.destination);}
 if(ambientOn){clearInterval(soundTimer);master.gain.setTargetAtTime(0,audioContext.currentTime,.15);await audioContext.suspend();ambientOn=false;}
 else{await audioContext.resume();master.gain.setTargetAtTime(Number($('volume').value)/100*.16,audioContext.currentTime,.3);ambientOn=true;playChord();soundTimer=setInterval(playChord,4200);}
 $('ambience').setAttribute('aria-pressed',String(ambientOn));$('ambience').textContent=ambientOn?'♫ Atmosferi söndür':'♫ Atmosferi aç';$('audio-note').textContent=ambientOn?'Sakit akkordlar və şam xışıltısı açıqdır.':'Atmosfer söndürüldü.';
 }catch{$('audio-note').textContent='Bu brauzerdə atmosfer səsi açıla bilmədi.';}
}
let chordIndex=0;
function playChord(){
 const chords=[[220,261.63,329.63],[174.61,220,261.63],[196,246.94,293.66],[164.81,220,329.63]];
 const now=audioContext.currentTime;
 chords[chordIndex++%chords.length].forEach((frequency,i)=>{const o=audioContext.createOscillator(),g=audioContext.createGain();o.type='sine';o.frequency.value=frequency;g.gain.setValueAtTime(0,now);g.gain.linearRampToValueAtTime(.2,now+.4+i*.1);g.gain.exponentialRampToValueAtTime(.001,now+4);o.connect(g);g.connect(master);o.start(now);o.stop(now+4.1);o.onended=()=>{o.disconnect();g.disconnect();};});
 const buffer=audioContext.createBuffer(1,audioContext.sampleRate*4,audioContext.sampleRate),samples=buffer.getChannelData(0);for(let i=0;i<samples.length;i++)samples[i]=(Math.random()*2-1)*.025;
 const n=audioContext.createBufferSource(),filter=audioContext.createBiquadFilter();filter.type='lowpass';filter.frequency.value=550;n.buffer=buffer;n.connect(filter);filter.connect(master);n.start();n.onended=()=>{n.disconnect();filter.disconnect();};
}
$('ambience').onclick=toggleAmbience;
$('volume').oninput=()=>{
 const volume=Number($('volume').value)/100;
 if(master&&ambientOn)master.gain.setTargetAtTime(volume*(speechSource?.12:.16),audioContext.currentTime,.1);
 if(speechGain&&speechContext?.state==='running')speechGain.gain.setTargetAtTime(volume,speechContext.currentTime,.08);
};
function stopSpeech(){
 ++speechVersion;speechRequest?.abort();speechRequest=null;speechLoading=false;
 if(speechSource){speechSource.onended=null;try{speechSource.stop();}catch{}speechSource.disconnect();speechSource=null;}
 speechGain?.disconnect();speechGain=null;
 if(speechContext&&speechContext.state!=='closed')speechContext.close().catch(()=>{});
 speechContext=null;
 $('narrate').textContent='Ruhun sözlərini dinlə';
 $('narrate').disabled=busy||!currentValues.words;
 $('stop-voice').disabled=true;
 if(master&&ambientOn&&audioContext.state==='running')master.gain.setTargetAtTime(Number($('volume').value)/100*.16,audioContext.currentTime,.15);
}
$('stop-voice').onclick=()=>{stopSpeech();$('audio-note').textContent='Oxunuş dayandırıldı.';};
$('narrate').onclick=async()=>{
 if(!currentValues.words||busy)return;
 stopSpeech();const version=speechVersion,person={...profile()};
 const controller=new AbortController();speechRequest=controller;speechLoading=true;
 $('narrate').disabled=true;$('narrate').textContent='Səs hazırlanır…';$('stop-voice').disabled=false;
 $('audio-note').textContent=`${person.display} üçün ispan dilində səs hazırlanır…`;
 try{
  const Context=window.AudioContext||window.webkitAudioContext;
  if(!Context)throw new Error('Bu brauzerdə audio oxutmaq mümkün deyil.');
  const context=new Context();speechContext=context;
  await context.resume();
  if(version!==speechVersion)return;
  const response=await fetch(`/api/narration/${encodeURIComponent(person.name)}${activeBranch?'?branch_id='+encodeURIComponent(activeBranch):''}`,{signal:controller.signal});
  if(!response.ok){let message='Səs hazırlanmadı. Yenidən dinlə.';try{message=(await response.json()).detail||message;}catch{}throw new Error(message);}
  const bytes=await response.arrayBuffer();
  if(version!==speechVersion)return;
  const buffer=await context.decodeAudioData(bytes);
  if(version!==speechVersion)return;
  const source=context.createBufferSource(),volume=context.createGain();
  speechSource=source;speechGain=volume;source.buffer=buffer;
  volume.gain.value=Number($('volume').value)/100;source.connect(volume);volume.connect(context.destination);
  source.onended=()=>{if(version===speechVersion){stopSpeech();$('audio-note').textContent='Oxunuş bitdi.';}};
  source.start();speechLoading=false;speechRequest=null;
  if(master&&ambientOn)master.gain.setTargetAtTime(Number($('volume').value)/100*.12,audioContext.currentTime,.15);
  $('narrate').textContent='Yenidən dinlə';$('narrate').disabled=false;
  $('audio-note').textContent=`${person.display} ispanca danışır…`;
 }catch(error){
  if(version!==speechVersion)return;
  stopSpeech();if(error.name!=='AbortError')$('audio-note').textContent=error.message;
 }
};
window.addEventListener('pagehide',()=>{stopSpeech();clearInterval(soundTimer);audioContext?.close();});
loadSouls();

