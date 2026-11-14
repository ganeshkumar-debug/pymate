/* ═══════════════════════════════════════════════════
   PyMate v3 — Client Application
   Server-key mode + model selector + faster streaming
   ═══════════════════════════════════════════════════ */
(function(){
'use strict';

// ── Storage Keys ──
const K = {
  CHATS: 'pm_chats', CUR: 'pm_cur', MODEL: 'pm_model'
};

// ── State ──
const S = {
  model: localStorage.getItem(K.MODEL) || 'gemini-3.5-flash',
  chats: [],
  curId: localStorage.getItem(K.CUR) || null,
  generating: false,
  abort: null,
  ready: false,
  models: []
};

// Load chats from storage safely
try { S.chats = JSON.parse(localStorage.getItem(K.CHATS) || '[]'); } catch(e) { S.chats = []; }

// ── DOM refs ──
const $ = id => document.getElementById(id);
const D = {
  sidebar: $('sidebar'), openSb: $('openSidebar'), closeSb: $('closeSidebar'),
  newChat: $('newChatBtn'), clearHist: $('clearHistBtn'), histList: $('histList'),
  modelSelect: $('modelSelect'), statusDot: $('statusDot'), statusText: $('statusText'),
  chatArea: $('chatArea'), welcome: $('welcome'), msgList: $('msgList'),
  form: $('chatForm'), input: $('chatInput'), sendBtn: $('sendBtn'),
  latency: $('latency'),
  toasts: $('toasts')
};

// ── Init ──
function init(){
  setupMarked();
  bind();
  renderHist();
  loadChat();
  checkHealth();
  
  // Focus input on load (desktop only)
  if(window.innerWidth > 900) D.input.focus();
}

// ── Marked.js config ──
function setupMarked(){
  if(!window.marked) return;
  marked.setOptions({gfm:true, breaks:true});
}

function renderMd(text){
  try{ return marked.parse(text); }
  catch(e){ return esc(text); }
}

function esc(s){ const d=document.createElement('div'); d.textContent=s; return d.innerHTML; }

// ── Health check ──
async function checkHealth(){
  try{
    const r = await fetch('/api/health');
    if(r.ok){
      const d = await r.json();
      S.ready = !!d.ready;
      
      // Populate model selector
      if(d.models && d.models.length){
        S.models = d.models;
        populateModels(d.models);
      }
      
      // Set model from health if no saved preference
      if(!localStorage.getItem(K.MODEL) && d.model){
        S.model = d.model;
        D.modelSelect.value = S.model;
      }
    }
  }catch(e){}
  updateStatusUI();
}

function populateModels(models){
  D.modelSelect.innerHTML = '';
  models.forEach(m => {
    const opt = document.createElement('option');
    opt.value = m.id;
    opt.textContent = m.id;
    opt.title = m.desc || '';
    D.modelSelect.appendChild(opt);
  });
  // Restore saved model selection
  if(S.model && D.modelSelect.querySelector('option[value="'+S.model+'"]')){
    D.modelSelect.value = S.model;
  } else {
    S.model = D.modelSelect.value;
  }
}

function updateStatusUI(){
  if(S.ready){
    D.statusDot.className='dot-sm on';
    D.statusText.textContent='Ready';
  } else {
    D.statusDot.className='dot-sm warn';
    D.statusText.textContent='Connecting…';
  }
}

// Retry health check until ready
let _healthInterval = setInterval(()=>{
  if(!S.ready) checkHealth();
  else clearInterval(_healthInterval);
}, 5000);

// ── Event binding ──
function bind(){
  D.openSb.onclick = ()=> D.sidebar.classList.add('open');
  D.closeSb.onclick = ()=> D.sidebar.classList.remove('open');
  D.newChat.onclick = newChat;
  D.clearHist.onclick = clearAll;

  // Model selector
  D.modelSelect.onchange = ()=>{
    S.model = D.modelSelect.value;
    localStorage.setItem(K.MODEL, S.model);
    toast('Model: ' + S.model);
  };

  // Starter cards & chips
  document.querySelectorAll('.card,.chip').forEach(el=>{
    el.onclick = ()=>{ D.input.value = el.dataset.q || ''; autoSize(); D.input.focus(); };
  });

  // Form
  D.form.onsubmit = e=>{ e.preventDefault(); send(); };
  D.input.addEventListener('keydown', e=>{
    if(e.key==='Enter' && !e.shiftKey){ e.preventDefault(); send(); }
  });
  D.input.addEventListener('input', autoSize);

  // Keyboard shortcut: Ctrl+K → new chat
  document.addEventListener('keydown', e=>{
    if((e.ctrlKey||e.metaKey) && e.key==='k'){ e.preventDefault(); newChat(); }
  });
  
  // Close sidebar when clicking overlay on mobile
  document.addEventListener('click', e=>{
    if(window.innerWidth <= 900 && D.sidebar.classList.contains('open')){
      if(!D.sidebar.contains(e.target) && e.target !== D.openSb){
        D.sidebar.classList.remove('open');
      }
    }
  });
}

function autoSize(){
  D.input.style.height = 'auto';
  D.input.style.height = Math.min(D.input.scrollHeight, 150)+'px';
}

// ── Chat Management ──
function getChat(){
  if(S.curId){ const c = S.chats.find(x=>x.id===S.curId); if(c) return c; }
  if(S.chats.length){ S.curId = S.chats[0].id; save(); return S.chats[0]; }
  return null;
}

function curChat(){
  let c = getChat();
  if(!c){ c = mkChat(); S.chats.unshift(c); S.curId = c.id; save(); }
  return c;
}

function mkChat(title){
  return { id:'c_'+Date.now()+'_'+Math.random().toString(36).slice(2,7), title: title||'New chat', msgs:[], ts:Date.now() };
}

function newChat(){
  const c = mkChat();
  S.chats.unshift(c);
  S.curId = c.id;
  save(); renderHist(); renderMsgs();
  D.input.focus();
  if(innerWidth<=900) D.sidebar.classList.remove('open');
}

function save(){
  try{
    localStorage.setItem(K.CHATS, JSON.stringify(S.chats));
    localStorage.setItem(K.CUR, S.curId||'');
  }catch(e){
    // Storage full — trim oldest chats
    while(S.chats.length > 5){
      S.chats.pop();
      try{ localStorage.setItem(K.CHATS, JSON.stringify(S.chats)); return; }catch(_){}
    }
  }
}

function renderHist(){
  if(!S.chats.length){ D.histList.innerHTML='<div class="hist-empty">No chats yet</div>'; return; }
  D.histList.innerHTML = '';
  S.chats.forEach(c=>{
    const el = document.createElement('div');
    el.className = 'hist-item'+(c.id===S.curId?' active':'');
    const t = document.createElement('span');
    t.textContent = c.title||'Untitled';
    t.style.cssText = 'overflow:hidden;text-overflow:ellipsis;flex:1';
    const x = document.createElement('button');
    x.className='del'; x.textContent='✕';
    x.onclick = e=>{ e.stopPropagation(); delChat(c.id); };
    el.appendChild(t); el.appendChild(x);
    el.onclick = ()=>{
      S.curId=c.id; save(); renderHist(); renderMsgs();
      if(innerWidth<=900) D.sidebar.classList.remove('open');
    };
    D.histList.appendChild(el);
  });
}

function delChat(id){
  S.chats = S.chats.filter(c=>c.id!==id);
  if(S.curId===id) S.curId = S.chats.length?S.chats[0].id:null;
  save(); renderHist(); renderMsgs();
}

function clearAll(){
  if(!S.chats.length) return;
  if(!confirm('Delete all conversations?')) return;
  S.chats=[]; S.curId=null; save(); renderHist(); renderMsgs();
}

function loadChat(){ renderMsgs(); }

// ── Render Messages ──
function renderMsgs(){
  const c = getChat();
  if(!c || !c.msgs.length){
    D.welcome.style.display='block'; D.msgList.style.display='none'; D.msgList.innerHTML=''; return;
  }
  D.welcome.style.display='none'; D.msgList.style.display='flex'; D.msgList.innerHTML='';
  c.msgs.forEach(m=> addMsgDOM(m.role, m.content, m.lat));
  scrollBot();
}

function addMsgDOM(role, content, lat){
  const isUser = role==='user';
  const row = document.createElement('div');
  row.className = 'msg '+(isUser?'user':'bot');

  const av = document.createElement('div');
  av.className = 'avatar';
  if(isUser) av.textContent='YOU';
  else av.innerHTML='<img src="/assets/logo.svg" alt="">';

  const wrap = document.createElement('div');
  wrap.className = 'bubble-wrap';
  const bub = document.createElement('div');
  bub.className = 'bubble';

  if(isUser) bub.textContent = content;
  else { bub.innerHTML = renderMd(content); enhanceCode(bub); }

  wrap.appendChild(bub);

  if(!isUser){
    const meta = document.createElement('div');
    meta.className = 'msg-meta';
    if(lat){ const lp = document.createElement('span'); lp.className='lat-pill'; lp.textContent='⚡ '+lat+'ms'; meta.appendChild(lp); }
    const cp = document.createElement('button');
    cp.className='copy-btn'; cp.textContent='Copy';
    cp.onclick = ()=>{ navigator.clipboard.writeText(content).then(()=>toast('Copied!')); };
    meta.appendChild(cp);
    wrap.appendChild(meta);
  }

  row.appendChild(av); row.appendChild(wrap);
  D.msgList.appendChild(row);
  return bub;
}

// ── Code block enhancement ──
function enhanceCode(container){
  container.querySelectorAll('pre').forEach(pre=>{
    if(pre.parentElement && pre.parentElement.classList.contains('code-box')) return;
    const code = pre.querySelector('code');
    let lang = 'python';
    if(code){ for(const c of code.className.split(' ')){ if(c.startsWith('language-')){ lang=c.slice(9); break; } } }

    const box = document.createElement('div'); box.className='code-box';
    const head = document.createElement('div'); head.className='code-head';
    const tag = document.createElement('span'); tag.textContent = lang.toUpperCase();
    const cp = document.createElement('button'); cp.className='copy-code'; cp.textContent='Copy';
    cp.onclick = ()=>{
      navigator.clipboard.writeText((code||pre).innerText).then(()=>{
        cp.textContent='Copied!'; cp.classList.add('done');
        setTimeout(()=>{ cp.textContent='Copy'; cp.classList.remove('done'); },1500);
      });
    };
    head.appendChild(tag); head.appendChild(cp);
    pre.parentNode.insertBefore(box, pre);
    box.appendChild(head); box.appendChild(pre);
    if(window.Prism && code) try{ Prism.highlightElement(code); }catch(e){}
  });
}

function scrollBot(){ 
  requestAnimationFrame(()=>{
    D.chatArea.scrollTop = D.chatArea.scrollHeight; 
  });
}

// ── Send Message ──
async function send(){
  if(S.generating){ if(S.abort) S.abort.abort(); return; }

  const text = D.input.value.trim();
  if(!text) return;
  D.input.value=''; autoSize();

  if(!S.ready){
    toast('⚠️ Server not ready. Reconnecting…');
    checkHealth();
    return;
  }

  const chat = curChat();

  // Auto-title
  if(!chat.msgs.length){
    chat.title = text.length>35 ? text.slice(0,35)+'…' : text;
    save(); renderHist();
  }

  chat.msgs.push({role:'user', content:text});
  save();

  D.welcome.style.display='none'; D.msgList.style.display='flex';
  addMsgDOM('user', text);
  scrollBot();

  // Bot placeholder with typing dots
  const botRow = document.createElement('div'); botRow.className='msg bot';
  const av = document.createElement('div'); av.className='avatar'; av.innerHTML='<img src="/assets/logo.svg" alt="">';
  const wrap = document.createElement('div'); wrap.className='bubble-wrap';
  const bub = document.createElement('div'); bub.className='bubble';
  bub.innerHTML='<div class="dots"><span class="dot-bounce"></span><span class="dot-bounce"></span><span class="dot-bounce"></span></div>';
  wrap.appendChild(bub); botRow.appendChild(av); botRow.appendChild(wrap);
  D.msgList.appendChild(botRow); scrollBot();

  setGen(true);
  const t0 = performance.now();
  let firstLat = null, acc = '';
  S.abort = new AbortController();

  // Optimized render — batch updates with requestAnimationFrame
  let renderScheduled = false;
  function scheduleRender(){
    if(renderScheduled) return;
    renderScheduled = true;
    requestAnimationFrame(()=>{
      renderScheduled = false;
      bub.innerHTML = renderMd(acc);
      scrollBot();
    });
  }

  try{
    // Build message history — only send last 20 messages for speed
    const histMsgs = chat.msgs.slice(-20);
    
    const res = await fetch('/api/chat',{
      method:'POST',
      headers:{ 'Content-Type':'application/json' },
      body: JSON.stringify({
        messages: histMsgs,
        model: S.model,
        temperature: 0.3
      }),
      signal: S.abort.signal
    });

    if(!res.ok){
      let d; try{ d=await res.json(); }catch(_){ d={detail:res.status+' '+res.statusText}; }
      throw new Error(d.detail||d.message||d.msg||'Request failed');
    }

    const reader = res.body.getReader();
    const dec = new TextDecoder();
    let buf = '';

    while(true){
      const {value,done} = await reader.read();
      if(done) break;
      buf += dec.decode(value,{stream:true});
      
      // Process all complete SSE events in buffer
      let idx;
      while((idx = buf.indexOf('\n\n')) !== -1){
        const line = buf.slice(0, idx);
        buf = buf.slice(idx + 2);
        
        if(!line.startsWith('data: ')) continue;
        const raw = line.slice(6).trim();
        if(raw==='[DONE]') break;
        
        try{
          const j = JSON.parse(raw);
          if(j.e) throw new Error(j.e);
          if(j.t){
            if(firstLat===null){ 
              firstLat=Math.round(performance.now()-t0); 
              D.latency.textContent=firstLat+'ms'; 
            }
            acc += j.t;
            scheduleRender();
          }
        }catch(pe){
          if(pe.message && !pe.message.includes('JSON')) throw pe;
        }
      }
    }

    // Final render with syntax highlighting
    bub.innerHTML = renderMd(acc||'No response.');
    enhanceCode(bub);

    const totalLat = firstLat || Math.round(performance.now()-t0);
    chat.msgs.push({role:'assistant', content:acc, lat:totalLat});
    save();

    // Meta bar
    const meta = document.createElement('div'); meta.className='msg-meta';
    const lp = document.createElement('span'); lp.className='lat-pill'; lp.textContent='⚡ '+totalLat+'ms';
    meta.appendChild(lp);
    const cp = document.createElement('button'); cp.className='copy-btn'; cp.textContent='Copy';
    cp.onclick=()=>{ navigator.clipboard.writeText(acc).then(()=>toast('Copied!')); };
    meta.appendChild(cp);
    wrap.appendChild(meta);
    scrollBot();

  }catch(err){
    if(err.name==='AbortError'){
      bub.innerHTML += '<p><em>[Stopped]</em></p>';
    } else {
      bub.innerHTML = '<div style="color:#f87171;background:rgba(239,68,68,.08);padding:10px;border-radius:8px;border:1px solid rgba(239,68,68,.25)"><b>⚠️ Error:</b> '+esc(err.message)+'</div>';
      // If model error, suggest switching
      if(err.message.includes('Model') || err.message.includes('model') || err.message.includes('unavailable')){
        toast('💡 Try switching to a different model');
      }
    }
  } finally {
    setGen(false); S.abort=null;
  }
}

function setGen(on){
  S.generating = on;
  if(on){
    D.sendBtn.classList.add('stop');
    D.sendBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="5" y="5" width="14" height="14" rx="2"/></svg>';
  } else {
    D.sendBtn.classList.remove('stop');
    D.sendBtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>';
  }
}

// ── Toast ──
function toast(msg){
  const t = document.createElement('div'); t.className='toast'; t.textContent=msg;
  D.toasts.appendChild(t);
  setTimeout(()=>{ t.style.opacity='0'; t.style.transition='.3s'; setTimeout(()=>t.remove(),300); }, 2500);
}

// ── Boot ──
document.addEventListener('DOMContentLoaded', init);
})();
