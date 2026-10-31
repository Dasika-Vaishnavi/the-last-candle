/* THE LAST CANDLE — UI only. Every authoritative decision is made server-side. */
(() => {
  'use strict';
  const app = document.getElementById('app');
  const toastEl = document.getElementById('toast');
  const roles = {
    medium: {character:'VESPER',name:'The Medium',glyph:'☾',icon:'☾',classTag:'SEER',color:'#8fd7e8',tag:'Listener of the dead',ability:'Veil Sight',abilityText:'Reveal a secret diary-hour clue to everyone for 10 seconds.',see:'Four portraits beneath luminous spirit symbols. Their faces have no names.',do:'Describe the symbols above the portraits. Speak with the Archivist and Lantern-bearer; help the team connect the spirits.'},
    archivist: {character:'QUILL',name:'The Archivist',glyph:'✶',icon:'✒',classTag:'KEEPER',color:'#d5a7ff',tag:'Keeper of lost hours',ability:'Remembered Page',abilityText:'Reveal the next escalating hint to everyone without burning candle time.',see:'A family diary recording four deaths, their spirit symbols, and the exact hour each life ended.',do:'Tell your companions the hour beside each symbol. The Locksmith needs the hours in the Lantern-bearer’s order.'},
    lantern: {character:'EMBER',name:'The Lantern-bearer',glyph:'✧',icon:'✧',classTag:'LIGHT',color:'#efbc70',tag:'Witness in the darkness',ability:'Steady Flame',abilityText:'Hold the candle still for 20 seconds. The timer resumes automatically.',see:'Your lantern reveals scratches hidden on the clock face: the precise order of four symbols.',do:'Read the symbols aloud in their exact order. Ask the Archivist for each matching hour.'},
    locksmith: {character:'CROWE',name:'The Locksmith',glyph:'⚿',icon:'⚿',classTag:'BINDER',color:'#d99791',tag:'The only hand that turns the key',ability:'Second Turn',abilityText:'Shield the next incorrect code submission from its 30-second penalty.',see:'Four adjustable clock dials, numbered one to twelve, and a key that can open the sealed passage.',do:'Only you can submit the four-hour code. Ask the Lantern-bearer for the order and the Archivist for the hours.'},
    walker: {character:'WREN',name:'The Walker',glyph:'◇',icon:'♜',classTag:'VOYAGER',color:'#abd49f',tag:'Footsteps in forgotten halls',ability:'Sure Step',abilityText:'Cross one crypt trap tile safely. Unlocks in Stage 3.',see:'The spirits are quiet for you in the Foyer. Your path opens in the Crypt.',do:'Help your team communicate. Your movement powers arrive in a later stage.'}
  };
  const roster = ['medium','archivist','lantern','locksmith','walker'];
  let previewCharacter='medium', deckScroll=0, castTimer=null;
  const castQueue=[];let castActive=false;
  function charArt(role){
    const r=roles[role], trim={
      medium:'<path d="M74 100 Q109 44 140 100 L141 136 L71 136Z" fill="#232b37" opacity=".85"/><path d="M80 82 Q106 52 136 82" stroke="#b2dfea" stroke-width="4" fill="none" opacity=".64"/><circle cx="107" cy="44" r="15" fill="none" stroke="currentColor" stroke-width="2" opacity=".7"/>',
      archivist:'<path d="M79 105 L77 77 L137 77 L139 105" stroke="#6c5379" stroke-width="15"/><path d="M82 54 L90 15 L130 15 L136 54" fill="#302839" stroke="#9276a2" stroke-width="2"/><path d="M91 34 L125 34" stroke="currentColor" stroke-width="3"/><path d="M135 68 Q175 12 158 9 Q145 44 139 75" fill="none" stroke="currentColor" stroke-width="3"/>',
      lantern:'<path d="M79 80 L69 149 L146 149 L134 80" fill="#272221" stroke="#8c6c4c" stroke-width="2"/><path d="M149 98 L173 86 L176 125 L151 131" fill="#cf8e48" opacity=".35"/><rect x="158" y="100" width="24" height="34" rx="2" fill="#e6bb6d" opacity=".8"/><path d="M161 104v-12q8-10 16 0v12" stroke="#efc984" stroke-width="3" fill="none"/>',
      locksmith:'<path d="M81 74 L68 156 L148 156 L133 74" fill="#2c2228" stroke="#885c5b" stroke-width="2"/><path d="M80 66 Q106 2 133 66 L141 93 Q106 65 72 93Z" fill="#3b2c35" stroke="#bd8783" stroke-width="2"/><path d="M150 131v-20a11 11 0 0 1 22 0v20" fill="none" stroke="currentColor" stroke-width="4"/><rect x="147" y="127" width="30" height="22" rx="3" fill="#87574e"/>',
      walker:'<path d="M78 73 L58 153 L154 153 L134 73" fill="#233025" stroke="#6e9c71" stroke-width="2"/><path d="M74 78L106 38 L143 78" fill="#243729" stroke="currentColor" stroke-width="2"/><path d="M98 110 L95 154M119 110L125 154" stroke="#6d8668" stroke-width="9"/><path d="M145 83 L171 162" stroke="#9cb58a" stroke-width="6"/>'
    }[role];
    return `<svg class="character-art" viewBox="0 0 214 225" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Original silhouette portrait of ${r.character}, ${r.name}">
      <defs><radialGradient id="aura-${role}"><stop stop-color="${r.color}" stop-opacity=".34"/><stop offset="1" stop-color="${r.color}" stop-opacity="0"/></radialGradient><linearGradient id="cloak-${role}" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#3f3741"/><stop offset="1" stop-color="#100f17"/></linearGradient></defs>
      <circle cx="108" cy="89" r="93" fill="url(#aura-${role})"/><path d="M31 220 Q49 144 80 127L87 111Q70 91 81 66Q82 33 108 31Q136 31 136 66Q146 96 126 113L135 127Q171 143 187 220Z" fill="url(#cloak-${role})" stroke="${r.color}" stroke-opacity=".45" stroke-width="2"/><ellipse cx="107" cy="84" rx="24" ry="31" fill="#554a4d"/><path d="M88 85L98 86M116 86L126 85" stroke="${r.color}" opacity=".8" stroke-width="2"/>${trim}<path d="M49 210 Q107 173 169 210" fill="none" stroke="${r.color}" stroke-width="2" opacity=".5"/><text x="107" y="199" fill="${r.color}" font-size="33" text-anchor="middle" opacity=".74">${r.glyph}</text></svg>`;
  }
  let state = null, ws = null, mode = 'landing', nameDraft = '', codeDraft = '', capacityDraft = 5;
  let token = null, seatId = null, roomCode = null, intentionalClose = false, reconnectAttempt = 0, connectGeneration = 0, retryTimer = null;
  let soundEnabled = localStorage.getItem('tlc:sound') === 'on';
  let serverOffset = 0, connectionState = 'idle', dials = [1,1,1,1], chatCollapsed = window.innerWidth < 540;
  let audioCtx = null, ambience = null, heartbeatInterval = null, toastTimeout = null, pendingConnect = null, lastPing = 0;
  const portraitSvg = `<svg viewBox="0 0 65 106" aria-hidden="true"><defs><linearGradient id="fig" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#514850"/><stop offset="1" stop-color="#211a21"/></linearGradient></defs><path d="M12 104 C12 79 21 76 26 73 L25 63 C20 59 17 43 20 32 C18 18 25 15 33 15 C44 15 50 23 47 32 C49 49 42 59 39 63 L40 72 C55 79 60 91 60 104Z" fill="url(#fig)" stroke="#72636b" stroke-width="1"/><path d="M24 35C29 30 36 30 43 35M27 47 L31 46 M37 46L42 47" stroke="#8d8584" opacity=".5" fill="none" stroke-width="1.5"/><path d="M22 21Q31 3 43 18" stroke="#3d303a" stroke-width="12" fill="none"/><path d="M20 103 Q30 80 44 103" fill="none" stroke="#9f8b7c" opacity=".3"/></svg>`;
  const lockSVG = `<svg width="55" height="55" viewBox="0 0 80 80" aria-hidden="true"><path d="M23 35V23a17 17 0 0 1 34 0v12" stroke="#d1a873" stroke-width="7" fill="none"/><rect x="15" y="34" width="50" height="36" rx="4" fill="#ad8d63" stroke="#e1c190" stroke-width="3"/><circle cx="40" cy="49" r="6" fill="#352522"/><path d="M40 50v9" stroke="#352522" stroke-width="4"/></svg>`;
  function esc(s) { return String(s??'').replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
  function showToast(text) { toastEl.textContent=text; toastEl.classList.add('show'); clearTimeout(toastTimeout); toastTimeout=setTimeout(()=>toastEl.classList.remove('show'),3900); }
  function linkToRoom(code) { return `${location.origin}/room/${code}`; }
  function isSolo() { return state?.room?.mode === 'solo'; }
  function savedSoloToken(id) { try { return JSON.parse(sessionStorage.getItem('tlc:solo:'+id)||'null')?.token; } catch { return null; } }
  function savedToken(code) { try { return JSON.parse(sessionStorage.getItem('tlc:seat:'+code)||'null')?.token; } catch {return null;} }
  function newAction() { return (typeof crypto !== 'undefined' && crypto.randomUUID) ? crypto.randomUUID() : `${Date.now()}_${Math.random().toString(36).slice(2,12)}`; }
  function isHost() { return state && state.me.id === state.room.hostId; }
  function myPlayer() { return state?.players.find(p=>p.id===state.me.id); }
  function readyToStart() { return state && state.players.length>=2 && state.players.every(p=>p.connected&&p.primaryRole&&p.ready); }
  function timeLeft() {
    if(!state) return 1200000;
    const t = state.timer;
    if (t.frozenRemainingMs !== null && (state.phase!=='playing' || (t.freezeUntil && Date.now()+serverOffset<t.freezeUntil))) return t.frozenRemainingMs;
    if(t.deadlineAt===null) return t.durationMs || (isSolo()?1500000:1200000);
    return Math.max(0, t.deadlineAt-(Date.now()+serverOffset));
  }
  function clockText(ms) { const s=Math.ceil(Math.max(0,ms)/1000); return `${String(Math.floor(s/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`; }
  function candle(small=false, id='') { return `<div class="${small?'small-candle':'big-candle'}" ${id?`id="${id}"`:''} role="img" aria-label="A burning candle representing the shared countdown"><div class="candle-halo"></div><div class="flame"></div><div class="wick"></div><div class="wax"><div class="wax-shade"></div></div><div class="candle-time">${isSolo()?'25:00':'20:00'}</div></div>`; }
  function topbar() { return `<header class="topbar"><div class="brand">THE LAST CANDLE</div><div class="top-controls"><button class="ghost-btn ${soundEnabled?'active':''}" data-action="sound" aria-pressed="${soundEnabled}" title="Sound ${soundEnabled?'on':'off'}">${soundEnabled?'♪ Sound on':'♫ Sound off'}</button>${state?`<span class="tag">${isSolo()?'SOLO RITUAL':esc(state.room.code)}</span>`:''}</div></header>`; }
  function shell(content) { return `<div class="app-shell">${topbar()}<main class="app-main fade-in">${content}</main></div>${connectionState==='reconnecting'?'<div class="connection-warning" role="alert">Reconnecting to the manor… the candle continues to burn.</div>':''}`; }
  function waking() {
    return shell(`<section class="waking-scene" role="status" aria-live="polite">
      <div class="waking-halo" aria-hidden="true"><div class="waking-flame">✦</div></div>
      <div class="kicker">HOLLOW MANOR · THE VEIL IS THIN</div>
      <h1 class="waking-title">Waking the spirits…</h1>
      <p class="waking-copy">The manor is stirring. Its doors will open when the connection returns.</p>
      <div class="waking-progress" aria-hidden="true"><span></span></div>
      <p class="thin-note">This may take around a minute on free hosting. Reconnecting automatically.</p>
    </section>`);
  }
  function resetRoom() { return shell(`<section class="waking-scene" role="alert"><div class="waking-halo" aria-hidden="true">✦</div><h1 class="page-title">The flame has gone out</h1><p class="waking-copy">The spirits have reset this room. Create a new one</p><button class="btn" data-action="create-screen">Create a new room →</button></section>`); }
  function landing() {
    const lastCode=localStorage.getItem('tlc:lastRoom');
    const lastSolo=sessionStorage.getItem('tlc:lastSoloId');
    const returnLink=(lastCode&&savedToken(lastCode)?`<button class="ghost-btn" data-action="return" data-value="${esc(lastCode)}">↺ Return to circle ${esc(lastCode)}</button>`:'')+(lastSolo&&savedSoloToken(lastSolo)?`<button class="ghost-btn" data-action="return-solo" data-value="${esc(lastSolo)}">↺ Return to your solitary vigil</button>`:'');
    const hero = `<section class="hero"><div><div class="kicker">HOLLOW MANOR · OCTOBER 1893</div><h1><span>THE LAST</span><span><em>CANDLE</em></span></h1><div class="rule"></div><p class="story">A séance has gone terribly wrong. Eleanor Hollow has sealed the manor. <em>Four rooms. One dying flame. The darkness knows your name.</em></p><div class="hero-actions"><button class="btn" data-action="create-screen">Gather a Circle <span aria-hidden="true">↗</span></button><button class="btn outline" data-action="solo-create">Enter Alone <span aria-hidden="true">☾</span></button></div><p class="hero-note">✧ Circle: 2–5 players · 20 minutes &nbsp; / &nbsp; Alone: one soul · 25 minutes</p><button class="hero-join-link" data-action="join-screen">Have a circle code? Join your friends →</button>${returnLink?`<div style="margin-top:18px">${returnLink}</div>`:''}</div><div class="illustration" aria-hidden="true"><div class="window"><div class="moon"></div><div class="mist"></div></div><div class="floor"></div>${candle(false,'hero-candle')}</div></section>`;
    if(mode==='landing')return shell(hero);
    const create=mode==='create';
    return shell(`<div class="landing-panel"><button class="back" data-action="home">← Return to the gates</button><div class="frame"><div class="eyebrow">${create?'THE FIRST SEAT':'A SEAT AWAITS'}</div><h1 class="page-title">${create?'Summon your party':'Enter the manor'}</h1><p class="subhead">${create?'Create a private chamber. Share the four-letter code with your fellow investigators.':'Ask your host for the four-letter room code.'}</p><form id="entry-form"><div class="form-group"><label class="form-label" for="name">Your name</label><input class="input" id="name" name="name" maxlength="22" placeholder="A name the spirits will remember" autocomplete="nickname" value="${esc(nameDraft)}" required /></div>${create?`<div class="form-group"><label class="form-label" for="capacity">Maximum players</label><select class="select" id="capacity" name="capacity">${[2,3,4,5].map(n=>`<option value="${n}" ${n===capacityDraft?'selected':''}>${n} players</option>`).join('')}</select></div>`:`<div class="form-group"><label class="form-label" for="code">Four-letter room code</label><input class="input code-input" id="code" name="code" maxlength="4" placeholder="ABCD" autocapitalize="characters" spellcheck="false" autocomplete="off" value="${esc(codeDraft)}" required /></div>`}<button class="btn full" type="submit" ${connectionState==='connecting'?'disabled':''}>${connectionState==='connecting'?'Opening the door…':create?'Create room →':'Join room →'}</button></form><div class="separator">✧</div><p class="thin-note center">${create?'The candle does not begin until you start the game.':'New players can join only before the host starts. Returning players can reclaim their seat.'}</p></div></div>`);
  }
  function renderPlayers(){return `<div class="players">${state.players.map(p=>`<div class="player"><div class="player-avatar">${esc((p.name||'?').slice(0,1).toUpperCase())}</div><div style="flex:1;min-width:0"><div class="player-name">${esc(p.name)} ${p.id===state.me.id?'<span style="color:#b7a28f">(you)</span>':''}</div><div class="player-meta">${p.primaryRole?esc(roles[p.primaryRole]?.name||p.primaryRole):'Role not chosen'} · ${p.ready?'Ready':'Not ready'}</div></div>${p.id===state.room.hostId?'<span class="tag">Host</span>':''}<span title="${p.connected?'Connected':'Disconnected'}" aria-label="${p.connected?'Connected':'Disconnected'}" class="presence ${p.connected?'':'off'}"></span></div>`).join('')}</div>`;}
  function chat(allowCollapse=false) { const msgs=state.chat||[];return `<section class="chat-card ${chatCollapsed&&allowCollapse?'collapsed':''}"><div class="chat-heading"><span>✥ SPIRIT BOARD</span>${allowCollapse?`<button class="ghost-btn mobile-chat-toggle" data-action="chat-toggle">${chatCollapsed?'Open':'Hide'} ▾</button>`:''}</div><div class="chat-messages" id="chat-messages" aria-live="polite">${msgs.length?msgs.map(m=>`<div class="message"><b>${esc(m.name)}:</b> ${esc(m.text)}</div>`).join(''):'<div class="message empty">The board is quiet. Speak, or leave a message…</div>'}</div><form class="chat-form" id="chat-form"><input name="text" maxlength="180" aria-label="Send a spirit board message" placeholder="Whisper to the team…" /><button type="submit" aria-label="Send message">➤</button></form></section>`;}
  function selectionRemaining(){const d=state?.selection?.deadlineAt;return d==null?45000:Math.max(0,d-(Date.now()+serverOffset));}
  function secondaryRoles(player){return (player?.roles||[]).filter(id=>id!==player.primaryRole);}
  function compositionBar(){return `<div class="composition-bar" aria-label="Team composition"><span class="composition-label">TEAM COMPOSITION</span><div class="composition-slots">${roster.map(id=>{const r=roles[id],owner=state.players.find(p=>p.primaryRole===id);const carrier=state.players.find(p=>p.roles.includes(id));return `<div class="composition-slot ${owner?'filled':''}" style="--role-color:${r.color}" title="${r.character}: ${owner?owner.name:carrier?'carried by '+carrier.name:'unclaimed'}"><span class="composition-glyph">${r.glyph}</span><span class="composition-name">${r.character}</span><span class="composition-owner">${owner?esc(owner.name):carrier?`+ ${esc(carrier.name)}`:'OPEN'}</span></div>`;}).join('')}</div></div>`;}
  function soloLobby(){
    const equipped=state.solo.equippedAbilities||[];
    const list=roster.map(id=>{const r=roles[id],picked=equipped.includes(id);
      return `<button class="solo-pick ${picked?'chosen':''}" style="--role-color:${r.color}" data-action="solo-equip" data-value="${id}" aria-pressed="${picked}" aria-label="${picked?'Unequip':'Equip'} ${r.character} ability ${r.ability}">
        <div class="solo-pick-art">${charArt(id)}</div><div class="solo-pick-copy"><span class="char-class">${r.classTag}</span><strong>${r.character}</strong><span>${esc(r.ability)}</span><small>${esc(r.abilityText)}</small>${id==='walker'?'<em>Ability available in Stage 3, not the Foyer.</em>':''}</div>
        <div class="solo-pick-mark">${picked?'✦ EQUIPPED':'◇ SELECT'}</div></button>`;}).join('');
    return shell(`<section class="solo-prep"><div class="kicker">ONE SOUL · FIVE LENSES · 1893</div><h1 class="page-title">ENTER THE VEIL ALONE</h1><p class="subhead">You will carry all five characters' clues, but only one portrait can speak at a time. Each change of Lens takes two real seconds while the candle burns.</p>
      <div class="solo-prep-summary"><span>☾ 25:00 CANDLE</span><span>✦ ${equipped.length} / 2 POWERS CHOSEN</span><span>⚿ FIVE LENSES</span></div>
      <h2 class="section-title">Choose two powers</h2><p class="thin-note">Every character's clues remain accessible through the Lens. Only the two powers you equip now can be cast this round. Tap a card again to remove it.</p>
      <div class="solo-pick-grid" role="group" aria-label="Choose exactly two solo abilities">${list}</div>
      <div class="solo-prep-footer"><div><div class="eyebrow">YOUR SOLITARY VIGIL</div><p>${equipped.length===2?`Equipped: ${equipped.map(id=>roles[id].character).join(' + ')}.`:'Select exactly two abilities before the flame is lit.'}</p></div><button class="btn" data-action="solo-start" ${equipped.length!==2?'disabled':''}>BEGIN ALONE →</button></div></section>`);
  }
  function soloRoleReveal(){
    const r=roles.medium;
    return shell(`<div class="reveal-shell"><div class="reveal-frame" style="--role-color:${r.color}"><div class="eyebrow">FIVE SPIRITS · ONE VESSEL</div><div class="reveal-art">${charArt('medium')}</div><div class="reveal-role">THE FIRST LENS · SEER</div><h1 class="reveal-name">VESPER</h1><p class="reveal-instruction">The manor lends you five pairs of eyes, but will only let you look through one at a time.</p><div class="detail-heading">WHAT YOU CAN SEE</div><p class="reveal-instruction">Only the active portrait's private clues. The Lens bar below lets you become Quill, Ember, Crowe or Wren.</p><div class="detail-heading">WHAT YOU MUST DO</div><p class="reveal-instruction">Remember each clue as you switch. Every change costs two seconds. Enter the clock hours only while wearing Crowe's Lens.</p><div class="carry-declaration">EQUIPPED POWERS: ${state.solo.equippedAbilities.map(id=>roles[id].character+' · '+roles[id].ability).join(' / ')}</div><p class="thin-note">The 25-minute candle is already burning. Audio is optional and off by default.</p><button class="btn" data-action="ack">OPEN YOUR EYES →</button></div></div>`);
  }
  function soloLensBar(){
    const active=state.solo.activeLens, target=state.solo.targetLens;
    return `<nav class="lens-bar" aria-label="Switch character lens"><div class="lens-heading"><span>✧ THE LENS</span><span>${target?'Smoke is gathering…':'One vision at a time · 2 seconds per switch'}</span></div><div class="lens-portraits">${roster.map(id=>{const r=roles[id],isActive=active===id,isTarget=target===id;
      return `<button class="lens-portrait ${isActive?'current':''} ${isTarget?'summoning':''}" style="--role-color:${r.color}" data-action="solo-lens" data-value="${id}" ${target||isActive?'disabled':''} aria-current="${isActive?'true':'false'}" aria-label="${r.character}, ${r.name}${isActive?', current Lens':''}"><span class="lens-art">${charArt(id)}</span><strong>${r.character}</strong><small>${r.glyph}</small></button>`;}).join('')}</div></nav>`;
  }
  function soloAbilityPanel(){
    const id=state.solo.activeLens;
    if(!id)return '';
    const r=roles[id], equipped=state.solo.equippedAbilities.includes(id),used=state.abilities.used?.[id],future=id==='walker',exhausted=id==='archivist'&&state.hintLevel>=3;
    return `<section class="ability-panel" style="--role-color:${r.color}"><div class="eyebrow">${r.character} · ONCE-PER-ROUND POWER</div><div class="power-item"><span class="power-rune">${r.glyph}</span><div class="power-copy"><strong>${esc(r.ability)}</strong><small>${esc(r.abilityText)}</small></div><button class="power-cast" data-action="cast-ability" data-value="${id}" ${!equipped||used||future||exhausted?'disabled':''}>${!equipped?'NOT EQUIPPED':used?'USED':future?'STAGE 3':exhausted?'NO HINTS':'CAST'}</button></div>${state.abilities.secondTurnArmed?'<div class="power-status">⚿ Second Turn is armed: the next wrong code costs no time.</div>':''}${state.timer.freezeUntil&&Date.now()+serverOffset<state.timer.freezeUntil?'<div class="power-status">✧ Steady Flame holds the clock still.</div>':''}</section>`;
  }
  function soloFoyer(){
    const active=state.solo.activeLens,target=state.solo.targetLens,r=active?roles[active]:null;
    const focal=target?`<div class="solo-veil-wait" role="status" aria-live="polite"><div class="solo-smoke" aria-hidden="true"></div><div class="solo-veil-content"><span class="solo-veil-glyph">${roles[target].glyph}</span><h2>Through the smoke…</h2><p>Summoning ${roles[target].character}'s memories. The candle does not wait.</p><strong data-lens-remaining>2.0s</strong></div></div>`:`${veilPanel()}${soloAbilityPanel()}${cluePanel(active,state.clues[active]||{})}`;
    return shell(`${timerHeader()}<div class="stage-header"><div><div class="kicker">SOLO VIGIL · CHAPTER I OF IV</div><h1 class="page-title">The Foyer</h1><p class="stage-story">Four portraits stare from the wall. The grandfather clock has stopped. Eleanor whispers: <em>“They each died at their hour.”</em></p></div><span class="tag">${target?'SHIFTING…':r?.character+' · '+r?.name}</span></div><div class="game-layout solo-game"><div class="solo-clue-space">${focal}</div><aside class="sidebar">${hints()}<div class="solo-reminder"><strong>ONE LENS · FIVE SECRETS</strong><p>Read each character's clue, remember the details, then switch. Crowe alone can turn the key.</p></div></aside></div>${soloLensBar()}`);
  }
  function soloPreview(){const result=state.result||{},score=result.secondsRemaining??Math.floor(timeLeft()/1000);
    return shell(`<div class="ending-shell solo-ending"><div class="eyebrow">SOLO TRIAL · STAGE ONE COMPLETE</div><h1 class="page-title">The Clock Awakens</h1><div class="door-frame"><div class="door-glow on"></div><div class="door open"></div></div><p>You held five memories in one mind. The doors open, but the Library still waits in shadow.</p><div class="kicker">SOLO FOYER RANK · SEPARATE FROM TEAM SCORES</div><div class="solo-rank">${esc(result.rank||'The Last Witness')}</div><div class="ending-time">${clockText(score*1000)}</div><p class="thin-note">This is a Stage 1 trial result, not a full-game escape. Stage 2 is coming soon.</p><button class="btn" data-action="again">↺ Begin another solo vigil</button></div>`);
  }
  function soloLost(){const sol=state.solutions||{};
    return shell(`<div class="ending-shell solo-ending"><div class="eyebrow">SOLO VIGIL · THE CANDLE IS GONE</div><h1 class="page-title" style="color:#b86060">The Last Witness Falls</h1><div class="solo-dead-candle">♱</div><p>One soul carried five voices, but Eleanor's clock would not relent.</p><div class="frame" style="text-align:left;margin:25px 0"><div class="kicker">THE FOYER · SOLUTION REVEALED</div><p>Order: <strong>${(sol.order||[]).join(' → ')}</strong></p><p>Hours: <strong>${(sol.code||[]).join(' · ')}</strong></p></div><button class="btn" data-action="again">↺ Try the solo vigil again</button></div>`);
  }
  function lobby(){
    const mine=myPlayer(), currentRole=mine.primaryRole, selected=roles[previewCharacter]||roles.medium;
    const selectedOwner=state.players.find(p=>p.primaryRole===previewCharacter);
    const locked=Boolean(currentRole);
    const selectClosed=selectionRemaining()===0 && state.selection.deadlineAt!==null;
    const canLock=!locked&&!selectedOwner&&!selectClosed;
    const rosterCards=roster.map(id=>{const r=roles[id],owner=state.players.find(p=>p.primaryRole===id),active=previewCharacter===id;
      return `<button type="button" class="character-card ${active?'is-preview':''} ${owner?'is-locked':''}" style="--role-color:${r.color}" data-action="preview-character" data-value="${id}" aria-pressed="${active}" aria-label="View ${r.character}, ${r.name}${owner?', locked by '+owner.name:''}"><div class="char-index">0${roster.indexOf(id)+1}<span class="char-rune">${r.glyph}</span></div><div class="char-silhouette">${charArt(id)}</div><div class="char-card-content"><span class="char-class">${r.classTag}</span><div class="char-name">${r.character}</div><span class="char-role">${r.name}</span></div>${owner?`<div class="char-lock-banner"><span>◆ LOCKED</span><strong>${esc(owner.name)}</strong></div>`:''}</button>`;}).join('');
    const detail=`<section class="character-detail" style="--role-color:${selected.color}" aria-live="polite"><div class="detail-glyph">${selected.glyph}</div><div class="detail-main"><div class="kicker">${selected.classTag} · ${selected.name}</div><h2>${selected.character}</h2><div class="detail-columns"><div><div class="detail-heading">WHAT YOU CAN SEE</div><p>${esc(selected.see)}</p></div><div><div class="detail-heading">ONCE-PER-GAME ABILITY · ${esc(selected.ability)}</div><p>${esc(selected.abilityText)}</p></div></div><div class="detail-actions">${locked?`<div class="locked-callout">◆ LOCKED IN AS ${roles[currentRole].character}</div>`:selectedOwner?`<div class="locked-callout">Claimed by ${esc(selectedOwner.name)}</div>`:`<button class="btn lock-button" data-action="lock-character" data-value="${previewCharacter}" ${!canLock?'disabled':''}>${selectClosed?'THE VEIL HAS CLOSED':'◆ LOCK IN '+selected.character}</button>`}${locked?`<span class="carry-hint">${secondaryRoles(mine).length?'You also carry: '+secondaryRoles(mine).map(id=>roles[id].character).join(', '):'Additional responsibilities are assigned when all players lock in.'}</span>`:''}</div></div></section>`;
    return shell(`<section class="select-layout"><div class="select-header"><div><div class="kicker">HALLOWEEN NIGHT · HOLLOW MANOR · 1893</div><h1 class="page-title">CHOOSE YOUR FATE</h1><p class="subhead">Five callings. One candle. No one survives alone.</p></div><div class="select-code"><div class="eyebrow">ROOM CODE</div><div class="room-code">${esc(state.room.code)}</div><button class="ghost-btn" data-action="copy">⧉ Copy invite</button></div></div><div class="select-topline"><div class="timer-badge"><span class="eyebrow">SELECTION ENDS IN</span><strong data-select-clock>${state.selection.deadlineAt===null?'45':Math.ceil(selectionRemaining()/1000)}</strong><span class="timer-suffix">SEC</span></div><p class="thin-note">${state.selection.deadlineAt===null?'The countdown starts when a second player joins.':'When time ends, the manor chooses for anyone not locked in.'}</p></div><div class="character-deck" role="group" aria-label="Choose a character">${rosterCards}</div>${detail}<div class="select-bottom"><section class="frame select-party"><div class="kicker">YOUR PARTY · ${state.players.length}/${state.room.capacity}</div>${renderPlayers()}<div class="readybar"><button class="btn ${mine.ready?'outline':''}" data-action="ready" ${!locked?'disabled':''}>${mine.ready?'✓ READY — CANCEL':'I AM READY'}</button>${isHost()?`<button class="btn" data-action="start" ${!readyToStart()?'disabled':''}>START THE SÉANCE →</button>`:'<span class="ready-pill">Waiting for the host to begin…</span>'}</div><p class="footnote">At least two connected players must lock in and be ready. Unchosen responsibilities merge automatically when everyone is selected.</p></section>${chat(true)}</div>${compositionBar()}</section>`);
  }
  function roleReveal(){const roleList=state.me.roles||[];const primary=state.me.primaryRole||roleList[0];const r=roles[primary]||roles.medium;return shell(`<div class="reveal-shell"><div class="reveal-frame" style="--role-color:${r.color}"><div class="eyebrow">THE VEIL HAS CHOSEN</div><div class="reveal-art">${charArt(primary)}</div><div class="reveal-role">${r.classTag} · ${r.name}</div><h1 class="reveal-name">${r.character}</h1><p class="reveal-instruction">${esc(r.tag)}.</p><div class="detail-heading">WHAT YOU CAN SEE</div><p class="reveal-instruction">${esc(r.see)}</p><div class="detail-heading">WHAT YOU MUST DO</div><p class="reveal-instruction">${esc(r.do)}</p><div class="detail-heading">YOUR POWER · ${r.ability}</div><p class="reveal-instruction">${esc(r.abilityText)}</p>${secondaryRoles(state.me).length?`<div class="carry-declaration">YOU ALSO CARRY: ${secondaryRoles(state.me).map(id=>roles[id].character+' · '+roles[id].name).join(' / ')}</div>`:''}<div class="reveal-cards">${roleList.map(id=>`<span class="role-chip">${roles[id].glyph} ${roles[id].character}</span>`).join('')}</div><p class="thin-note">The shared candle is burning. Your private clues await in the Foyer.</p><button class="btn" data-action="ack">ENTER THE FOYER →</button></div></div>`);}
  function diaryEntries(entries){return `<div class="diary"><div style="text-align:center;font-size:24px;margin:0 0 8px">The Hollow Family Record</div><p style="font-size:15px;font-style:italic;text-align:center">October, 1893 · Things the living must not forget</p>${entries.map(e=>`<div class="diary-entry"><b>${esc(e.name)}</b><span class="diary-glyph">${esc(e.symbol)}</span><div>Lost to ${esc(e.cause)} as the clock struck <strong>${e.hour}</strong>.</div></div>`).join('')}</div>`;}
  function cluePanel(role,detail){const r=roles[role];let inner='';
    if(role==='medium')inner=`<div class="portraits">${detail.portraits.map((sym,i)=>`<div class="portrait"><span class="glyph">${esc(sym)}</span>${portraitSvg}<div style="color:#a28f84;font-size:11px">PORTRAIT ${i+1}</div></div>`).join('')}</div>`;
    if(role==='archivist')inner=`<div class="parchment" style="margin-top:16px">${diaryEntries(detail.entries)}</div>`;
    if(role==='lantern')inner=`<div class="glyph-row" aria-label="Symbol order: star, crescent moon, flower, urn">${detail.order.map((sym,i)=>`${i?'<span class="arrow">➜</span>':''}<span>${esc(sym)}</span>`).join('')}</div><p class="footnote">These scratch marks appear only when the lantern beam crosses the clock face.</p>`;
    if(role==='locksmith')inner=`<div class="clock-lock" style="margin-top:16px"><div class="lock-icon">${lockSVG}</div><p class="thin-note">Set the four hours, then turn the key.</p><div class="dials">${dials.map((n,i)=>`<div class="dial"><div class="dial-label">DIAL ${i+1}</div><button class="dial-control" data-action="dial" data-index="${i}" data-delta="1" aria-label="Increase dial ${i+1}">⌃</button><div class="dial-number" data-dial-number="${i}">${n}</div><button class="dial-control" data-action="dial" data-index="${i}" data-delta="-1" aria-label="Decrease dial ${i+1}">⌄</button></div>`).join('')}</div><button class="btn" data-action="unlock">⚿ Turn the key</button></div>`;
    if(role==='walker')inner=`<p class="footnote">The Crypt is not yet open. Your role remains vital to the group in later stages.</p>`;
    return `<section class="role-panel" aria-label="${esc(r.name)} clues"><div class="kicker">${esc(r.tag)}</div><h3>${r.icon} ${esc(r.name)}</h3><div class="instruction-title">What you can see</div><p class="instruction">${esc(r.see)}</p>${inner}<div class="instruction-title">What you must do</div><p class="instruction">${esc(r.do)}</p></section>`;}
  function timerHeader(){const solo=isSolo(),minutes=solo?25:20;return `<div class="timer-top"><div><div class="kicker">${solo?'YOUR SOLITARY FLAME':'THE SHARED FLAME'}</div><div class="timer-readout" data-timer>${minutes}:00</div><div class="timer-meta">${state.timer.totalPenaltyMs?'Time lost to the manor: '+Math.round(state.timer.totalPenaltyMs/1000)+'s':`${minutes} minutes. The candle is burning.`}</div></div>${candle(true,'timer-candle')}<div style="text-align:right"><div class="eyebrow">ROUND ${state.round}</div><div class="tag" style="margin-top:5px">${solo?'SOLO':esc(state.room.code)}</div></div></div><div class="progress-wrap"><div class="progress" data-progress></div></div>`;}
  function hints(){return `<section class="hint-card"><div class="eyebrow">ELEANOR'S WHISPERS</div><h2 class="section-title" style="margin-top:7px">Need a sign?</h2><p class="thin-note">Three escalating hints. Each costs <strong>60 seconds</strong> from everyone's candle.</p><div class="hint-list">${(state.hints||[]).map((h,i)=>`<div class="hint-item"><span style="color:#cfad7c;font-size:12px">WHISPER ${i+1}</span><br>${esc(h)}</div>`).join('')}</div><button class="btn outline full" data-action="hint" ${state.hintLevel>=3?'disabled':''}>${state.hintLevel>=3?'All whispers revealed':`Reveal hint ${state.hintLevel+1} · −1:00`}</button></section>`;}
  function abilityPanel(){const abilities=state.abilities||{used:{}};return `<section class="ability-panel"><div class="eyebrow">YOUR ONCE-PER-GAME POWERS</div><div class="power-grid">${state.me.roles.map(id=>{const r=roles[id],used=abilities.used?.[id],future=id==='walker',exhausted=id==='archivist'&&state.hintLevel>=3;return `<div class="power-item" style="--role-color:${r.color}"><span class="power-rune">${r.glyph}</span><div class="power-copy"><strong>${r.character} · ${r.ability}</strong><small>${esc(r.abilityText)}</small></div><button class="power-cast" data-action="cast-ability" data-value="${id}" ${used||future||exhausted?'disabled':''}>${used?'USED':future?'STAGE 3':exhausted?'NO HINTS':'CAST'}</button></div>`;}).join('')}</div>${abilities.secondTurnArmed?'<div class="power-status">⚿ SECOND TURN ARMED — the next wrong code costs no time.</div>':''}${state.timer.freezeUntil&&Date.now()+serverOffset<state.timer.freezeUntil?'<div class="power-status">✧ STEADY FLAME — candle held still for 20 seconds.</div>':''}</section>`;}
  function veilPanel(){return state.veilClue?`<div class="veil-revelation" data-veil-clue data-expires="${state.veilClue.expiresAt}" role="status"><div class="detail-heading">VESPER · VEIL SIGHT</div><strong>A hidden whisper escapes: ${esc(state.veilClue.symbol)} marks the hour ${state.veilClue.hour}.</strong><div class="veil-remaining">Fades in <span data-veil-time></span></div></div>`:'';}
  function foyer(){return shell(`${timerHeader()}<div class="stage-header"><div><div class="kicker">CHAPTER I OF IV</div><h1 class="page-title">The Foyer</h1><p class="stage-story">Four portraits stare from the wall. The grandfather clock has stopped. Eleanor whispers: <em>“They each died at their hour.”</em></p></div><span class="tag">${state.me.roles.map(r=>roles[r].name.replace('The ','')).join(' + ')}</span></div><div class="game-layout"><div>${veilPanel()}${abilityPanel()}${state.me.roles.map(id=>cluePanel(id,state.clues[id]||{})).join('')}</div><aside class="sidebar">${hints()}${chat(true)}<div class="thin-note" style="text-align:center">✧ Only the Locksmith can submit the clock code.<br>Talk aloud or use the spirit board to share what you see.</div></aside></div>`);}
  function solved(){return shell(`${timerHeader()}<div class="ending-shell"><div class="kicker">THE LOCK HAS YIELDED</div><h1 class="page-title">The Clock Awakens</h1><div class="door-frame"><div class="door-glow"></div><div class="door"></div></div><p>At the fourth chime, the lock snaps free. Across the foyer, a door groans open. A colder darkness waits beyond.</p><div class="ending-time">${clockText(timeLeft())}</div><p class="thin-note">Candle time preserved at completion of the Milestone 1 demo.</p><button class="btn" data-action="continue" disabled>Continue into the darkness →</button></div>`);}
  function preview(){return shell(`<div class="ending-shell"><div class="eyebrow">THE PASSAGE BEYOND</div><h1 class="page-title">The Library Awaits</h1><div class="door-frame"><div class="door-glow on"></div><div class="door open"></div></div><p>You have survived the Foyer. Beyond the doorway, ancient books whisper names no living soul remembers.</p><div class="kicker">STAGE 2 · COMING SOON</div><p class="thin-note">Milestone 1 complete. Your party remains together; the host may begin a new round with a new randomized clock solution.</p>${isHost()?`<button class="btn" data-action="again">↺ Try the Foyer again</button>`:'<p class="thin-note">Waiting for the host to begin another round…</p>'}</div>`);}
  function lost(){const sol=state.solutions||{};return shell(`<div class="ending-shell"><div class="eyebrow">THE LAST LIGHT HAS GONE OUT</div><h1 class="page-title" style="color:#b86060">Consumed by Darkness</h1><div style="font-size:100px;margin:15px 0;color:#8a7570;filter:grayscale(1)">♱</div><p>The final candle dies. Eleanor's silence fills the manor. The doors will not open tonight.</p><div class="frame" style="text-align:left;margin:25px 0"><div class="kicker">THE FOYER · ANSWER REVEALED</div><p>Symbol order: <strong>${(sol.order||[]).join(' → ')}</strong></p><p>Clock hours: <strong>${(sol.code||[]).join(' · ')}</strong></p><p class="thin-note">A new round will generate new diary hours and a fresh code.</p></div>${isHost()?`<button class="btn" data-action="again">↺ Try again with the same party</button>`:'<p class="thin-note">Waiting for the host to start another round…</p>'}</div>`);}
  function render(){const current=(state?.phase||'landing');let content=mode==='room-reset'&&!state?resetRoom():state?(isSolo()?(current==='lobby'?soloLobby():current==='playing'&&!state.me.ack?soloRoleReveal():current==='playing'?soloFoyer():current==='foyer_solved'?solved():current==='stage2_preview'?soloPreview():current==='lost'?soloLost():soloLobby()):(current==='lobby'?lobby():current==='playing'&&!state.me.ack?roleReveal():current==='playing'?foyer():current==='foyer_solved'?solved():current==='stage2_preview'?preview():current==='lost'?lost():lobby())):(connectionState==='waking'||connectionState==='reconnecting'||connectionState==='connecting'?waking():landing());const oldDeck=document.querySelector('.character-deck');if(oldDeck)deckScroll=oldDeck.scrollLeft;app.innerHTML=content;const newDeck=document.querySelector('.character-deck');if(newDeck)newDeck.scrollLeft=deckScroll;if(current==='foyer_solved'){setTimeout(()=>{document.querySelector('.door-frame .door')?.classList.add('open');document.querySelector('.door-frame .door-glow')?.classList.add('on');},110);setTimeout(()=>{const btn=document.querySelector('[data-action=continue]');if(btn)btn.disabled=false;},Math.max(10,2500-(Date.now()+serverOffset-(state?.solvedAt||Date.now()))));}updateClock();const c=document.getElementById('chat-messages');if(c)c.scrollTop=c.scrollHeight;}
  function updateClock(){let ms=timeLeft();const sc=document.querySelector('[data-select-clock]');if(sc&&state?.selection){sc.textContent=state.selection.deadlineAt===null?'45':String(Math.ceil(selectionRemaining()/1000)).padStart(2,'0');}const veil=document.querySelector('[data-veil-clue]');if(veil){const secs=Math.max(0,Math.ceil((Number(veil.dataset.expires)-(Date.now()+serverOffset))/1000));const t=veil.querySelector('[data-veil-time]');if(t)t.textContent=secs+'s';if(secs===0)veil.hidden=true;}for(const el of document.querySelectorAll('[data-timer],.candle-time'))el.textContent=clockText(ms);const maxMs=state?.timer?.durationMs || 1200000;for(const el of document.querySelectorAll('[data-progress]'))el.style.width=`${Math.max(0,Math.min(100,ms/maxMs*100))}%`;for(const el of document.querySelectorAll('.wax-shade'))el.style.height=`${Math.min(96, (1-ms/maxMs)*96)}%`;const lensTime=document.querySelector('[data-lens-remaining]');if(lensTime&&state?.solo?.lensReadyAt)lensTime.textContent=(Math.max(0,state.solo.lensReadyAt-(Date.now()+serverOffset))/1000).toFixed(1)+'s';const flameHidden=ms<=0&&state&&state.phase!=='lobby';for(const el of document.querySelectorAll('.flame'))el.style.opacity=flameHidden?'0':'1';if(soundEnabled&&state?.phase==='playing'&&ms<120000&&!heartbeatInterval)startHeartbeat();if((!state||state.phase!=='playing'||ms>=120000)&&heartbeatInterval){clearInterval(heartbeatInterval);heartbeatInterval=null;}}
  function send(type,payload={}){if(ws?.readyState!==WebSocket.OPEN){showToast('No connection. Rejoining the manor…');return;}ws.send(JSON.stringify({type,...payload,actionId:newAction()}));}
  function dialStep(i,delta){dials[i]=((dials[i]-1+delta+12)%12)+1;const el=document.querySelector(`[data-dial-number="${i}"]`);if(el)el.textContent=dials[i];}
  function connect(type,payload={}) {
    intentionalClose = false;
    pendingConnect = {type,...payload};
    if(retryTimer){clearTimeout(retryTimer);retryTimer=null;}
    // Keep the same healthy socket for the readiness handshake and room admission.
    if(ws?.readyState===WebSocket.OPEN){
      ws.send(JSON.stringify(pendingConnect));
      pendingConnect=null;
      return;
    }
    if(ws?.readyState===WebSocket.CONNECTING)return;
    connectionState = 'waking';
    if(!state)render();
    const generation=++connectGeneration;
    const proto=location.protocol==='https:'?'wss':'ws';
    try{ws=new WebSocket(`${proto}://${location.host}/ws`);}
    catch{scheduleRetry(generation,{type,...payload});return;}
    ws.onopen=()=>{
      if(generation!==connectGeneration)return;
      lastPing=Date.now();
      const request=pendingConnect||{type:'HELLO'};
      pendingConnect=null;
      ws.send(JSON.stringify(request));
    };
    ws.onmessage=event=>{
      if(generation!==connectGeneration)return;
      let data;try{data=JSON.parse(event.data);}catch{return;}
      onPacket(data);
    };
    ws.onclose=()=>{
      if(intentionalClose||generation!==connectGeneration)return;
      const retryCode=roomCode||payload.code;
      const intent=retryCode&&token
        ? {type:'RESUME_SEAT',code:retryCode,token}
        : pendingConnect||{type,...payload};
      scheduleRetry(generation,intent);
    };
    ws.onerror=()=>{}; // onclose schedules the retry after a failed handshake.
  }
  function scheduleRetry(generation,intent){
    if(intentionalClose||generation!==connectGeneration)return;
    connectionState='reconnecting';
    render();
    const delay=Math.min(8000,1000*Math.pow(1.6,Math.min(reconnectAttempt++,5)));
    retryTimer=setTimeout(()=>{
      if(!intentionalClose&&generation===connectGeneration){
        ws=null;
        connect(intent.type,Object.fromEntries(Object.entries(intent).filter(([k])=>k!=='type')));
      }
    },delay);
  }
  function onPacket(data){if(data.type==='ROOM_RESET'){const lostCode=roomCode||codeDraft||location.pathname.match(/^\/room\/([A-Z]{4})$/i)?.[1]?.toUpperCase();if(lostCode)sessionStorage.removeItem('tlc:seat:'+lostCode);const lostSolo=location.pathname.match(/^\/solo\/([a-f0-9]{32})$/i)?.[1];if(lostSolo){sessionStorage.removeItem('tlc:solo:'+lostSolo);sessionStorage.removeItem('tlc:lastSoloId');}token=null;seatId=null;roomCode=null;state=null;mode='room-reset';connectionState='idle';intentionalClose=true;if(ws)ws.close();render();return;}if(data.type==='READY'){connectionState='connected';reconnectAttempt=0;render();return;}if(data.type==='WELCOME'){roomCode=data.roomCode;token=data.token;seatId=data.seatId;if(data.roomMode==='solo'){sessionStorage.setItem('tlc:solo:'+data.roomId,JSON.stringify({token,seatId}));sessionStorage.setItem('tlc:lastSoloId',data.roomId);history.replaceState({},'',`/solo/${data.roomId}`);}else{localStorage.setItem('tlc:lastRoom',roomCode);sessionStorage.setItem('tlc:seat:'+roomCode,JSON.stringify({token,seatId}));history.replaceState({},'',`/room/${roomCode}`);}connectionState='connected';reconnectAttempt=0;return;}
    if(data.type==='STATE'){if(!state||data.state.version>=state.version||data.state.room.code!==state.room.code){const prev=state?.phase;state=data.state;serverOffset=state.serverNow-Date.now();if(prev!==state.phase&&state.phase==='lobby'){dials=[1,1,1,1];previewCharacter='medium';deckScroll=0;}render();}return;}
    if(data.type==='SYNC'){if(state?.timer&&data.freezeUntil!==undefined){state.timer.freezeUntil=data.freezeUntil;state.timer.frozenRemainingMs=data.frozenRemainingMs;state.timer.deadlineAt=data.deadlineAt;}if(state?.selection&&data.selectionDeadlineAt!==undefined)state.selection.deadlineAt=data.selectionDeadlineAt;if(data.serverNow){const calc=data.serverNow-Date.now();serverOffset=Math.abs(serverOffset-calc)>1800?calc:serverOffset*.85+calc*.15;}updateClock();return;}
    if(data.type==='PONG'){const mid=(Number(data.clientSentAt)+Date.now())/2;const calc=data.serverNow-mid;serverOffset=serverOffset*.5+calc*.5;return;}
    if(data.type==='ERROR'){showToast(data.message||'The manor rejects your request');if(!state){connectionState='idle';if(ws){intentionalClose=true;ws.close();}render();}return;}
    if(data.type==='REPLACED'){intentionalClose=true;showToast('This seat was opened in another browser tab.');return;}
    if(data.type==='EFFECT'){effect(data.effect);return;}
  }
  function effect(effect){if(!effect)return;switch(effect.name){case 'WRONG_ANSWER':{document.body.classList.add('shake','pulse-red');setTimeout(()=>document.body.classList.remove('shake','pulse-red'),650);playGhost();showToast('The clock rejects the code. −30 seconds.');break;}
      case 'HINT':playWhisper();showToast('Eleanor whispers. −60 seconds.');break;
      case 'FOYER_SOLVED':playChimes();showToast('The clock chimes! A door begins to open…');break;
      case 'TIME_EXPIRED':playGhost();showToast('The last flame has died.');break;
      case 'GAME_STARTED':playChime();break;
      case 'CHARACTER_LOCKED':castOverlay(effect.character,`${effect.by} LOCKED IN`,effect.role);break;
      case 'ABILITY_CAST':castOverlay(effect.character,effect.ability, effect.role);showToast(`${effect.by} cast ${effect.ability}!`);break;
      case 'WRONG_SHIELDED':castOverlay('CROWE','SECOND TURN · NO TIME LOST','locksmith');playChime();break;
      case 'FLAME_RESUMED':showToast('The candle burns once more.');break;
      case 'LENS_SWITCH_STARTED':playWhisper();break;
      case 'LENS_SWITCH_COMPLETE':playChime();break;
    }}
  function castOverlay(title,subtitle,role){
    castQueue.push({title,subtitle,role});
    if(!castActive)showNextCast();
  }
  function showNextCast(){
    const entry=castQueue.shift();
    if(!entry){castActive=false;return;}
    castActive=true;
    const r=roles[entry.role]||roles.medium;
    const el=document.createElement('div');el.className='cast-overlay';el.style.setProperty('--role-color',r.color);
    el.setAttribute('role','status');el.setAttribute('aria-live','polite');
    el.innerHTML=`<div class="cast-glow"></div><div class="cast-rune">${r.glyph}</div><div class="cast-sub">${esc(entry.subtitle)}</div><div class="cast-title">${esc(entry.title)}</div>`;
    document.body.appendChild(el);playDrumHit();
    clearTimeout(castTimer);
    castTimer=setTimeout(()=>{el.remove();showNextCast();},1900);
  }
  function playDrumHit(){tone(88,.68,'sine',.095);tone(52,.85,'triangle',.065,.09);tone(165,.2,'sawtooth',.02,.02);}
  function safeAudio(){if(!soundEnabled)return null;const AudioCtor=window.AudioContext||window.webkitAudioContext;if(!AudioCtor)return null;try{audioCtx ||=new AudioCtor();if(audioCtx.state==='suspended')audioCtx.resume();return audioCtx;}catch{return null;}}
  function tone(freq,duration=0.2,type='sine',volume=.04,delay=0){const ctx=safeAudio();if(!ctx)return;const osc=ctx.createOscillator(),gain=ctx.createGain(),t=ctx.currentTime+delay;osc.type=type;osc.frequency.setValueAtTime(freq,t);gain.gain.setValueAtTime(.0001,t);gain.gain.exponentialRampToValueAtTime(Math.max(.001,volume),t+.025);gain.gain.exponentialRampToValueAtTime(.0001,t+duration);osc.connect(gain).connect(ctx.destination);osc.start(t);osc.stop(t+duration+.03);}
  function playGhost(){tone(87,.65,'sawtooth',.045);tone(112,.9,'triangle',.03,.08);}
  function playWhisper(){tone(344,.19,'triangle',.025);tone(414,.24,'triangle',.025,.12);}
  function playChime(){tone(523,.54,'sine',.05);}
  function playChimes(){[392,494,587,784].forEach((f,i)=>tone(f,1.5,'sine',.045,i*.34));}
  function startAmbience(){const ctx=safeAudio();if(!ctx||ambience)return;try{const seconds=2, len=ctx.sampleRate*seconds,buf=ctx.createBuffer(1,len,ctx.sampleRate),arr=buf.getChannelData(0);for(let i=0;i<len;i++)arr[i]=Math.random()*2-1;const noise=ctx.createBufferSource();noise.buffer=buf;noise.loop=true;const lp=ctx.createBiquadFilter();lp.type='lowpass';lp.frequency.value=210;const gain=ctx.createGain();gain.gain.value=.015;noise.connect(lp).connect(gain).connect(ctx.destination);noise.start();ambience={noise};}catch{}}
  function stopAmbience(){if(ambience){try{ambience.noise.stop();}catch{}ambience=null;}if(heartbeatInterval){clearInterval(heartbeatInterval);heartbeatInterval=null;}}
  function startHeartbeat(){heartbeatInterval=setInterval(()=>{if(soundEnabled&&state?.phase==='playing'&&timeLeft()<120000){tone(63,.12,'sine',.036);tone(56,.16,'sine',.03,.24);}},1000);}
  function toggleSound(){soundEnabled=!soundEnabled;localStorage.setItem('tlc:sound',soundEnabled?'on':'off');if(soundEnabled){startAmbience();playChime();}else stopAmbience();render();}
  function returnSolo(id){const t=savedSoloToken(id);if(!t){showToast('The solitary seat was lost on this browser.');return;}token=t;roomCode=null;connect('RESUME_SEAT',{roomId:id,token:t});}
  function returnSeat(code){const t=savedToken(code);if(!t){showToast('No saved seat for this room on this browser.');return;}token=t;roomCode=code;connect('RESUME_SEAT',{code,token:t});}
  function leave(){intentionalClose=true;if(ws?.readyState===1)ws.close();ws=null;state=null;roomCode=null;seatId=null;token=null;history.replaceState({},'','/');mode='landing';connectionState='idle';render();}
  document.addEventListener('click',async (e)=>{const el=e.target.closest('[data-action]');if(!el)return;const a=el.dataset.action;
    if(a==='create-screen'){mode='create';render();}
    else if(a==='solo-create')connect('CREATE_SOLO');
    else if(a==='solo-equip')send('EQUIP_SOLO_ABILITY',{role:el.dataset.value});
    else if(a==='solo-start')send('START_SOLO');
    else if(a==='solo-lens')send('SWITCH_LENS',{role:el.dataset.value});
    else if(a==='return-solo')returnSolo(el.dataset.value);
    else if(a==='join-screen'){mode='join';render();}
    else if(a==='home'){mode='landing';render();}
    else if(a==='return')returnSeat(el.dataset.value);
    else if(a==='sound')toggleSound();
    else if(a==='copy'){try{await navigator.clipboard.writeText(linkToRoom(state.room.code));showToast('Invite link copied');}catch{showToast('Invite your friends with code '+state.room.code);}}
    else if(a==='preview-character'){previewCharacter=el.dataset.value;render();}
    else if(a==='lock-character')send('LOCK_CHARACTER',{role:el.dataset.value});
    else if(a==='cast-ability')send('USE_ABILITY',{role:el.dataset.value});
    else if(a==='ready')send('SET_READY',{ready:!myPlayer().ready});
    else if(a==='start')send('START_GAME');
    else if(a==='ack')send('ACK_REVEAL');
    else if(a==='dial')dialStep(+el.dataset.index,+el.dataset.delta);
    else if(a==='unlock')send('SUBMIT_CLOCK_CODE',{hours:[...dials]});
    else if(a==='hint'){if(confirm('Spend 60 seconds of the shared candle to reveal the next hint to everyone?'))send('REQUEST_HINT');}
    else if(a==='continue')send('CONTINUE');
    else if(a==='again')send('TRY_AGAIN');
    else if(a==='chat-toggle'){chatCollapsed=!chatCollapsed;render();}
  });
  document.addEventListener('submit',e=>{if(e.target.id==='entry-form'){e.preventDefault();const data=new FormData(e.target);nameDraft=String(data.get('name')||'').trim();if(!nameDraft){showToast('Enter your name.');return;}if(mode==='create'){capacityDraft=Number(data.get('capacity'));connect('CREATE_ROOM',{name:nameDraft,capacity:capacityDraft});}else{codeDraft=String(data.get('code')||'').toUpperCase().trim();if(!/^[A-Z]{4}$/.test(codeDraft)){showToast('Enter a four-letter room code.');return;}const existing=savedToken(codeDraft);if(existing){token=existing;roomCode=codeDraft;connect('RESUME_SEAT',{code:codeDraft,token:existing});}else connect('JOIN_ROOM',{code:codeDraft,name:nameDraft});}}
    else if(e.target.id==='chat-form'){e.preventDefault();const field=e.target.elements.text;const text=field?.value.trim();if(text){send('SEND_CHAT',{text});field.value='';}}
  });
  document.addEventListener('input',e=>{if(e.target.id==='name')nameDraft=e.target.value;if(e.target.id==='code')codeDraft=e.target.value.toUpperCase().replace(/[^A-Z]/g,'').slice(0,4);if(e.target.id==='capacity')capacityDraft=Number(e.target.value);});
  const urlCode=location.pathname.match(/^\/room\/([A-Z]{4})$/i)?.[1]?.toUpperCase();
  const urlSolo=location.pathname.match(/^\/solo\/([a-f0-9]{32})$/i)?.[1];
  setInterval(()=>{updateClock();if(ws?.readyState===1&&Date.now()-lastPing>=25000){lastPing=Date.now();ws.send(JSON.stringify({type:'PING',clientSentAt:lastPing}));}},250);
  if(urlSolo){if(savedSoloToken(urlSolo))returnSolo(urlSolo);else{mode='landing';connect('HELLO');showToast('This private solo chamber belongs to another browser session.');}}
  else if(urlCode){codeDraft=urlCode;if(savedToken(urlCode))returnSeat(urlCode);else{mode='join';connect('HELLO');}}
  else connect('HELLO');
})();
