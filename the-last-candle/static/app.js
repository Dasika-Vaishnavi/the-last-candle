/* THE LAST CANDLE — UI only. Every authoritative decision is made server-side. */
(() => {
  'use strict';
  // Sites deploy: the frontend lives on a separate origin, but game state
  // remains authoritative on Render. Leave these unset for the original
  // combined Render deployment.
  const sitesFrontend = window.TLC_SITES_FRONTEND === true;
  const websocketUrl = window.TLC_WEBSOCKET_URL || `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws`;
  const roomPath = code => sitesFrontend ? `/?room=${encodeURIComponent(code)}` : `/room/${code}`;
  const soloPath = id => sitesFrontend ? `/?solo=${encodeURIComponent(id)}` : `/solo/${id}`;
  const roomCodeFromUrl = () => new URLSearchParams(location.search).get('room')?.toUpperCase()
    || location.pathname.match(/^\/room\/([A-Z]{4})$/i)?.[1]?.toUpperCase();
  const soloIdFromUrl = () => new URLSearchParams(location.search).get('solo')
    || location.pathname.match(/^\/solo\/([a-f0-9]{32})$/i)?.[1];
  const app = document.getElementById('app');
  const toastEl = document.getElementById('toast');
  const roles = {
    medium: {character:'VESPER',name:'The Medium',glyph:'☾',icon:'☾',classTag:'SEER',color:'#6B4E71',tag:'Listener of the dead',ability:'Veil Sight',abilityText:'Reveal a secret diary-hour clue to everyone for 10 seconds.',see:'Four portraits beneath luminous spirit symbols. Their faces have no names.',do:'Describe the symbols above the portraits. Speak with the Archivist and Lantern-bearer; help the team connect the spirits.'},
    archivist: {character:'QUILL',name:'The Archivist',glyph:'✶',icon:'✒',classTag:'KEEPER',color:'#E3B23C',tag:'Keeper of lost hours',ability:'Remembered Page',abilityText:'Reveal the next escalating hint to everyone without burning candle time.',see:'A family diary recording four deaths, their spirit symbols, and the exact hour each life ended.',do:'Tell your companions the hour beside each symbol. The Locksmith needs the hours in the Lantern-bearer’s order.'},
    lantern: {character:'EMBER',name:'The Lantern-bearer',glyph:'✧',icon:'✧',classTag:'LIGHT',color:'#E8735A',tag:'Witness in the darkness',ability:'Steady Flame',abilityText:'Hold the candle still for 20 seconds. The timer resumes automatically.',see:'Your lantern reveals scratches hidden on the clock face: the precise order of four symbols.',do:'Read the symbols aloud in their exact order. Ask the Archivist for each matching hour.'},
    locksmith: {character:'CROWE',name:'The Locksmith',glyph:'⚿',icon:'⚿',classTag:'BINDER',color:'#EDE6D6',tag:'The only hand that turns the key',ability:'Second Turn',abilityText:'Shield the next incorrect code submission from its 30-second penalty.',see:'Four adjustable clock dials, numbered one to twelve, and a key that can open the sealed passage.',do:'Only you can submit the four-hour code. Ask the Lantern-bearer for the order and the Archivist for the hours.'},
    walker: {character:'WREN',name:'The Walker',glyph:'◇',icon:'♜',classTag:'VOYAGER',color:'#9FC6B8',tag:'Footsteps in forgotten halls',ability:'Sure Step',abilityText:'Arm one safe passage through a trap in the Crypt.',see:'The spirits are quiet for you in the Foyer. Your path opens in the Crypt.',do:'Help your team communicate. Your movement powers arrive in a later stage.'}
  };
  const roster = ['medium','archivist','lantern','locksmith','walker'];
  let previewCharacter='medium', deckScroll=0, castTimer=null;
  const castQueue=[];let castActive=false;
  // Direct approved SVG artwork from style-preview.html (the attached v2 reference).
  const landingGhostSVG = `<svg aria-label="a small ghost peeking beside a candle" class="boil" viewBox="0 0 300 250" width="290">
<!-- candle -->
<g>
<path d="M200 120 h46 v100 h-46 z" fill="#F4E9D8" stroke="#1A1A1A" stroke-linejoin="round" stroke-width="6"></path>
<path d="M200 132 q8 18 14 0 q6 26 14 0 q6 14 18 0" fill="none" stroke="#1A1A1A" stroke-linecap="round" stroke-width="5"></path>
<path d="M223 120 v-12" stroke="#1A1A1A" stroke-linecap="round" stroke-width="5"></path>
<g class="flick"><path d="M223 70 C240 90 238 104 223 108 C208 104 206 90 223 70 Z" fill="#E3B23C" stroke="#1A1A1A" stroke-linejoin="round" stroke-width="5"></path>
<path d="M223 88 C229 96 228 101 223 103 C218 101 217 96 223 88 Z" fill="#E8735A"></path></g>
<path d="M188 222 h70" stroke="#1A1A1A" stroke-linecap="round" stroke-width="6"></path>
</g>
<!-- ghost -->
<g class="bob">
<path d="M48 200 C40 110 72 50 116 50 C160 50 188 110 182 200
                     Q172 214 162 200 Q151 186 140 200 Q129 214 118 200 Q107 186 96 200 Q85 214 74 200 Q63 186 48 200 Z" fill="#F4E9D8" stroke="#1A1A1A" stroke-linejoin="round" stroke-width="6"></path>
<ellipse cx="96" cy="118" fill="#1A1A1A" rx="7" ry="10"></ellipse>
<ellipse cx="134" cy="118" fill="#1A1A1A" rx="7" ry="10"></ellipse>
<circle cx="98" cy="114" fill="#F4E9D8" r="2.5"></circle><circle cx="136" cy="114" fill="#F4E9D8" r="2.5"></circle>
<ellipse cx="82" cy="140" fill="#F2A7A0" rx="10" ry="6"></ellipse>
<ellipse cx="148" cy="140" fill="#F2A7A0" rx="10" ry="6"></ellipse>
<ellipse cx="115" cy="146" fill="#1A1A1A" rx="7" ry="9"></ellipse>
<path d="M178 140 q22 -6 26 -22" fill="none" stroke="#1A1A1A" stroke-linecap="round" stroke-width="6"></path>
</g>
</svg>`;
  const vesperSVG = `<svg aria-label="Vesper, the medium" class="boil" viewBox="0 0 260 250" width="205">
<!-- floating moon -->
<g class="bob"><path d="M200 40 a26 26 0 1 0 22 40 a20 20 0 1 1 -22 -40 z" fill="#F4E9D8" stroke="#1A1A1A" stroke-linejoin="round" stroke-width="5"></path></g>
<!-- cloak -->
<path d="M40 252 C50 190 80 168 130 168 C180 168 210 190 220 252 Z" fill="#6B4E71" stroke="#1A1A1A" stroke-linejoin="round" stroke-width="6"></path>
<!-- hood -->
<path d="M74 176 C66 100 96 58 130 58 C164 58 194 100 186 176 Q130 196 74 176 Z" fill="#6B4E71" stroke="#1A1A1A" stroke-linejoin="round" stroke-width="6"></path>
<!-- face -->
<ellipse cx="130" cy="132" fill="#F4E9D8" rx="38" ry="42" stroke="#1A1A1A" stroke-width="6"></ellipse>
<path d="M108 128 q8 7 16 0 M136 128 q8 7 16 0" fill="none" stroke="#1A1A1A" stroke-linecap="round" stroke-width="5"></path>
<ellipse cx="108" cy="146" fill="#F2A7A0" rx="7" ry="4"></ellipse><ellipse cx="152" cy="146" fill="#F2A7A0" rx="7" ry="4"></ellipse>
<path d="M123 154 q7 6 14 0" fill="none" stroke="#1A1A1A" stroke-linecap="round" stroke-width="5"></path>
<!-- third-eye dot -->
<circle cx="130" cy="108" fill="#E3B23C" r="5" stroke="#1A1A1A" stroke-width="3"></circle>
<!-- clasp -->
<circle cx="130" cy="200" fill="#E3B23C" r="8" stroke="#1A1A1A" stroke-width="4"></circle>
</svg>`;
  const horaceSVG = `<svg aria-label="Horace Tock the clockmaker ghost" class="boil" id="horace" viewBox="0 0 300 290" width="250">
<g class="bob">
<!-- pendulum tail -->
<g class="pend">
<path d="M150 230 v26" stroke="#1A1A1A" stroke-linecap="round" stroke-width="6"></path>
<circle cx="150" cy="268" fill="#E3B23C" r="13" stroke="#1A1A1A" stroke-width="5"></circle>
</g>
<!-- body -->
<path d="M64 130 C58 70 98 36 150 36 C202 36 242 70 236 130 C232 172 208 188 188 198 Q166 210 158 232 L142 232 Q134 210 112 198 C92 188 68 172 64 130 Z" fill="#F4E9D8" stroke="#1A1A1A" stroke-linejoin="round" stroke-width="6"></path>
<!-- hair curl -->
<path d="M140 42 c-6 -18 14 -24 18 -12 c3 9 -8 12 -10 4" fill="none" stroke="#1A1A1A" stroke-linecap="round" stroke-width="5"></path>
<!-- arms -->
<path d="M66 150 q-22 4 -28 -14" fill="none" stroke="#1A1A1A" stroke-linecap="round" stroke-width="6"></path>
<path d="M234 150 q22 4 28 -14" fill="none" stroke="#1A1A1A" stroke-linecap="round" stroke-width="6"></path>
<!-- brows -->
<path d="M100 82 L128 74" id="browL" stroke="#1A1A1A" stroke-linecap="round" stroke-width="6"></path>
<path d="M172 74 L200 82" id="browR" stroke="#1A1A1A" stroke-linecap="round" stroke-width="6"></path>
<!-- spectacles -->
<circle cx="117" cy="110" fill="#FFF8EC" r="22" stroke="#1A1A1A" stroke-width="5"></circle>
<circle cx="183" cy="110" fill="#FFF8EC" r="22" stroke="#1A1A1A" stroke-width="5"></circle>
<path d="M139 108 q11 -8 22 0" fill="none" stroke="#1A1A1A" stroke-linecap="round" stroke-width="5"></path>
<circle cx="117" cy="112" fill="#1A1A1A" id="eyeL" r="7"></circle>
<circle cx="183" cy="112" fill="#1A1A1A" id="eyeR" r="7"></circle>
<!-- blush -->
<g id="blush" opacity="0"><ellipse cx="96" cy="146" fill="#F2A7A0" rx="11" ry="6"></ellipse><ellipse cx="204" cy="146" fill="#F2A7A0" rx="11" ry="6"></ellipse></g>
<!-- mouth -->
<path d="M138 172 q6 -5 12 0 q6 5 12 0" fill="none" id="mouth" stroke="#1A1A1A" stroke-linecap="round" stroke-width="5"></path>
<!-- tear -->
<path d="M200 128 c6 10 6 16 0 18 c-6 -2 -6 -8 0 -18 z" fill="#9FC6E8" id="tear" opacity="0" stroke="#1A1A1A" stroke-width="3"></path>
</g>
</svg>`;
  const otherCharacterSVG = {
    archivist: `<svg class="character-art boil" viewBox="0 0 260 250" width="205" role="img" aria-label="Quill, the keeper"><g stroke="#1A1A1A" stroke-linejoin="round" stroke-linecap="round"><path d="M36 255 Q40 187 100 176 L161 176 Q221 192 225 255Z" fill="#6B4E71" stroke-width="6"/><path d="M82 192L63 247M179 192L202 247" fill="none" stroke-width="5"/><path d="M66 95Q58 43 132 43Q202 45 193 97L184 165Q161 193 128 194Q96 193 75 167Z" fill="#F4E9D8" stroke-width="6"/><path d="M69 100Q89 63 129 69Q162 69 191 97" fill="none" stroke-width="6"/><path d="M68 78Q94 32 137 37Q179 37 196 78L195 92Q126 82 66 93Z" fill="#1F2A44" stroke-width="6"/><rect x="83" y="25" width="106" height="32" rx="8" fill="#1F2A44" stroke-width="6"/><path d="M115 25L119 8L151 8L157 25" fill="#1F2A44" stroke-width="5"/><circle cx="112" cy="128" r="6" fill="#1A1A1A" stroke="none"/><circle cx="154" cy="128" r="6" fill="#1A1A1A" stroke="none"/><path d="M100 113q12 -7 22 0M143 113q12 -7 22 0" fill="none" stroke-width="5"/><ellipse cx="94" cy="145" rx="10" ry="5" fill="#F2A7A0" stroke="none"/><ellipse cx="171" cy="145" rx="10" ry="5" fill="#F2A7A0" stroke="none"/><path d="M121 161q12 8 24 0" fill="none" stroke-width="5"/><path d="M126 192L127 237L147 237L146 192" fill="#E3B23C" stroke-width="5"/><path d="M174 202 Q209 161 210 88 Q231 122 217 165 Q206 191 174 202Z" fill="#EDE6D6" stroke-width="5"/><path d="M177 204L205 122" fill="none" stroke-width="4"/></g></svg>`,
    lantern: `<svg class="character-art boil" viewBox="0 0 260 250" width="205" role="img" aria-label="Ember, the light-bearer"><g stroke="#1A1A1A" stroke-linejoin="round" stroke-linecap="round"><path d="M36 255Q40 186 94 176L164 176Q215 184 223 255Z" fill="#E8735A" stroke-width="6"/><path d="M78 185L57 250M190 184L206 252" fill="none" stroke-width="5"/><path d="M74 90Q76 43 131 43Q187 43 191 90L186 160Q170 194 132 194Q92 194 77 161Z" fill="#F4E9D8" stroke-width="6"/><path d="M72 90Q84 22 138 32Q190 35 193 91Q160 79 140 65Q117 86 72 90Z" fill="#1F2A44" stroke-width="6"/><circle cx="112" cy="128" r="6" fill="#1A1A1A" stroke="none"/><circle cx="157" cy="128" r="6" fill="#1A1A1A" stroke="none"/><path d="M101 113q11 -5 19 0M146 113q11 -5 19 0" fill="none" stroke-width="5"/><ellipse cx="95" cy="145" rx="11" ry="5" fill="#F2A7A0" stroke="none"/><ellipse cx="174" cy="145" rx="11" ry="5" fill="#F2A7A0" stroke="none"/><path d="M122 160Q134 173 146 160" fill="none" stroke-width="5"/><path d="M101 196L133 224L164 196" fill="none" stroke-width="6"/><path d="M186 195l28 -30" fill="none" stroke-width="6"/><rect x="203" y="163" width="34" height="50" rx="7" fill="#E3B23C" stroke-width="6"/><path d="M210 164V151Q220 133 230 151V164" fill="none" stroke-width="5"/><path d="M220 171Q232 186 220 197Q208 187 220 171Z" fill="#F4E9D8" stroke-width="4"/></g></svg>`,
    locksmith: `<svg class="character-art boil" viewBox="0 0 260 250" width="205" role="img" aria-label="Crowe, the binder"><g stroke="#1A1A1A" stroke-linejoin="round" stroke-linecap="round"><path d="M36 255Q52 178 103 174L166 174Q219 186 225 255Z" fill="#1F2A44" stroke-width="6"/><path d="M89 192L62 255M174 193L204 255" fill="none" stroke-width="5"/><path d="M75 88Q69 46 132 41Q193 45 191 91L188 152Q174 189 135 195Q94 192 79 157Z" fill="#F4E9D8" stroke-width="6"/><path d="M70 96Q74 30 130 28Q184 29 196 98Q173 82 155 64Q123 93 70 96Z" fill="#6B4E71" stroke-width="6"/><circle cx="110" cy="132" r="6" fill="#1A1A1A" stroke="none"/><circle cx="158" cy="132" r="6" fill="#1A1A1A" stroke="none"/><path d="M97 118L121 114M146 114L169 118" fill="none" stroke-width="5"/><ellipse cx="94" cy="148" rx="10" ry="5" fill="#F2A7A0" stroke="none"/><ellipse cx="172" cy="148" rx="10" ry="5" fill="#F2A7A0" stroke="none"/><path d="M122 165Q135 170 149 163" fill="none" stroke-width="5"/><path d="M129 196L128 239M141 196L143 239" fill="none" stroke-width="5"/><circle cx="207" cy="211" r="19" fill="#E3B23C" stroke-width="6"/><path d="M188 211L161 211L161 227M174 211L174 225" fill="none" stroke-width="6"/></g></svg>`,
    walker: `<svg class="character-art boil" viewBox="0 0 260 250" width="205" role="img" aria-label="Wren, the voyager"><g stroke="#1A1A1A" stroke-linejoin="round" stroke-linecap="round"><path d="M27 255Q47 178 108 177L155 177Q214 185 235 255Z" fill="#2F6F73" stroke-width="6"/><path d="M92 190L71 253M167 190L189 253" fill="none" stroke-width="5"/><path d="M78 92Q80 38 135 39Q188 39 192 95L188 156Q168 193 133 193Q96 191 81 160Z" fill="#F4E9D8" stroke-width="6"/><path d="M63 101Q70 32 129 26Q188 28 200 101Q155 90 133 55Q106 89 63 101Z" fill="#1F2A44" stroke-width="6"/><path d="M80 89Q136 44 183 89" fill="none" stroke-width="5"/><circle cx="109" cy="131" r="6" fill="#1A1A1A" stroke="none"/><circle cx="157" cy="131" r="6" fill="#1A1A1A" stroke="none"/><path d="M100 113Q110 108 120 115M147 115Q158 108 167 113" fill="none" stroke-width="5"/><ellipse cx="95" cy="148" rx="10" ry="5" fill="#F2A7A0" stroke="none"/><ellipse cx="172" cy="148" rx="10" ry="5" fill="#F2A7A0" stroke="none"/><path d="M122 164Q134 173 149 164" fill="none" stroke-width="5"/><path d="M131 191L126 231L145 231L141 191" fill="#E3B23C" stroke-width="5"/><path d="M221 105L202 246" fill="none" stroke-width="6"/><path d="M220 107Q196 109 191 121" fill="none" stroke-width="5"/></g></svg>`
  };
  function charArt(role){ return role === 'medium' ? vesperSVG : (otherCharacterSVG[role]||vesperSVG); }
  function horacePortrait(){return `<div class="horace-figure">${horaceSVG}</div>`;}
  const prudenceSVG = `<svg class="boil character-art ghost-svg" viewBox="0 0 300 290" width="250" aria-label="Prudence Page, the librarian ghost"><path d="M61 188Q48 122 81 79Q112 40 155 43Q210 41 238 99Q257 142 236 204Q223 236 197 245Q179 234 154 249Q126 234 106 244Q78 221 61 188Z" fill="#F4E9D8" stroke="#1A1A1A" stroke-width="6" stroke-linejoin="round"/><path d="M102 84Q152 58 209 87" fill="none" stroke="#1A1A1A" stroke-width="6" stroke-linecap="round"/><path d="M100 95Q150 68 207 96" fill="none" stroke="#1A1A1A" stroke-width="5"/><rect x="83" y="28" width="150" height="35" rx="8" fill="#E3B23C" stroke="#1A1A1A" stroke-width="6"/><path d="M100 37v18M217 35v20" fill="none" stroke="#1A1A1A" stroke-width="5"/><circle cx="117" cy="144" r="7" fill="#1A1A1A"/><circle cx="189" cy="144" r="7" fill="#1A1A1A"/><path d="M100 122Q116 115 131 122M175 122Q190 115 205 122" fill="none" stroke="#1A1A1A" stroke-width="5" stroke-linecap="round"/><ellipse cx="94" cy="167" rx="12" ry="6" fill="#F2A7A0"/><ellipse cx="211" cy="167" rx="12" ry="6" fill="#F2A7A0"/><path d="M140 176Q154 185 166 176" fill="none" stroke="#1A1A1A" stroke-width="5" stroke-linecap="round"/><g transform="rotate(-10 227 205)"><rect x="198" y="180" width="66" height="56" rx="5" fill="#2F6F73" stroke="#1A1A1A" stroke-width="5"/><path d="M209 189v38M222 195h29M222 206h24" fill="none" stroke="#F4E9D8" stroke-width="4" stroke-linecap="round"/></g><path d="M90 200Q64 204 57 179" fill="none" stroke="#1A1A1A" stroke-width="6" stroke-linecap="round"/></svg>`;
  const reginaldSVG = `<svg class="boil character-art ghost-svg" viewBox="0 0 300 290" width="250" aria-label="Sir Reginald Rattle, the knight ghost"><path d="M66 134Q66 59 150 55Q234 59 234 134L226 217Q201 246 174 237Q150 253 126 237Q97 248 74 217Z" fill="#EDE6D6" stroke="#1A1A1A" stroke-width="6"/><path d="M101 68L112 30L150 50L186 30L199 68" fill="#E3B23C" stroke="#1A1A1A" stroke-width="6" stroke-linejoin="round"/><circle cx="117" cy="139" r="8" fill="#1A1A1A"/><circle cx="183" cy="139" r="8" fill="#1A1A1A"/><ellipse cx="96" cy="169" rx="13" ry="7" fill="#F2A7A0"/><ellipse cx="203" cy="169" rx="13" ry="7" fill="#F2A7A0"/><path d="M134 191Q150 199 166 191" fill="none" stroke="#1A1A1A" stroke-width="5" stroke-linecap="round"/><path d="M103 117Q117 107 132 117M169 117Q183 107 198 117" fill="none" stroke="#1A1A1A" stroke-width="5" stroke-linecap="round"/><path d="M60 188L35 220L71 217" fill="none" stroke="#1A1A1A" stroke-width="6" stroke-linecap="round"/><path d="M240 183L267 217L232 221" fill="none" stroke="#1A1A1A" stroke-width="6" stroke-linecap="round"/></svg>`;
  const eleanorSVG = `<svg class="boil character-art ghost-svg" viewBox="0 0 300 290" width="250" aria-label="Eleanor Hollow, the manor ghost"><path d="M65 155Q58 47 150 42Q242 47 235 155L228 238Q204 221 178 246Q147 225 119 246Q93 221 68 237Z" fill="#F4E9D8" stroke="#1A1A1A" stroke-width="6"/><path d="M82 95Q148 38 220 97" fill="none" stroke="#1A1A1A" stroke-width="6" stroke-linecap="round"/><circle cx="120" cy="140" r="7" fill="#1A1A1A"/><circle cx="184" cy="140" r="7" fill="#1A1A1A"/><ellipse cx="101" cy="166" rx="12" ry="6" fill="#F2A7A0"/><ellipse cx="203" cy="166" rx="12" ry="6" fill="#F2A7A0"/><path d="M136 184Q150 192 165 184" fill="none" stroke="#1A1A1A" stroke-width="5" stroke-linecap="round"/><path d="M101 118L131 115M170 115L201 118" fill="none" stroke="#1A1A1A" stroke-width="5" stroke-linecap="round"/><path d="M62 179Q42 162 40 143M238 179Q258 162 260 143" fill="none" stroke="#1A1A1A" stroke-width="6" stroke-linecap="round"/></svg>`;
  const rpgStats = {medium:[2,0,1],archivist:[1,2,0],lantern:[0,1,2],locksmith:[0,2,1],walker:[1,0,2]};
  function statBadges(role){const [c,w,n]=rpgStats[role]||[0,0,0];return `<div class="stat-row" aria-label="Character stats"><span>CHARM +${c}</span><span>WITS +${w}</span><span>NERVE +${n}</span></div>`;}
  function wickBox(){const line=state?.story?.wick?.text||'You open the door. It opens back. Rude.';return `<aside class="wick-box" aria-label="Wick the candle spirit narrates"><span class="wick-icon" aria-hidden="true">🕯</span><div><strong>WICK · THE NARRATOR</strong><p>${esc(line)}</p></div></aside>`;}
  function spiritFlames(warmth){return `<div class="spirit-flames" aria-label="Ghost warmth ${warmth} of 3">${[0,1,2].map(i=>`<svg viewBox="0 0 22 28" width="23" height="28" aria-hidden="true"><path d="M11 2C20 12 19 22 11 25C3 22 2 12 11 2Z" fill="${i<warmth?'#E3B23C':'none'}" stroke="${i<warmth?'#1A1A1A':'#F4E9D8'}" stroke-width="3" stroke-linejoin="round"/></svg>`).join('')}<small>WARMTH ${warmth}/3</small></div>`;}
  function ghostConversation(){
    const info=state?.story?.ghost;
    if(!info) return horaceFallback();
    const isMyTurn=isSolo()||info.speakerId===state.me.id;
    const last=info.history?.at(-1), line=info.goodbye||(last?.ghostText)||({foyer:"Oh! Visitors. You're early. Or I'm late. I've been on time since 1871, so it's hard to tell.",library:'Shh. The books have been crying again. Do you know how hard it is to reshelve a sob?'}[info.id]||'The ghost waits for someone to speak.');
    const art={foyer:horaceSVG,library:prudenceSVG,crypt:reginaldSVG,seance:eleanorSVG}[info.id]||horaceSVG;
    const cold=info.coldUntil&&Date.now()+serverOffset<info.coldUntil;
    const mood=info.closed?'pleased':cold?'sad':info.coldCount?'grumpy':last?.mood||'nervous';
    let replies='';
    if(info.closed){replies='<p class="ghost-ending">✦ Closure found. They can finally rest.</p>';}
    else if(cold){replies=`<div class="ghost-cold" role="status">The ghost has gone cold for 30 seconds. The candle lost 30 seconds too.</div>`;}
    else if(info.finished){replies=crossroadsUI();}
    else {replies=`<div class="speaker-pill">${isMyTurn?'✦ YOUR TURN TO SPEAK':`✦ ${esc(info.speakerName||'Someone')} IS SPEAKING`} · ${info.exchange+1}/${info.maxExchanges}</div><div class="ghost-replies">${(info.options||[]).map(o=>`<button type="button" class="horace-reply" data-action="ghost-reply" data-value="${esc(o.id)}" ${!isMyTurn?'disabled':''}>${esc(o.label)}${o.stat?` <b class="check-label">[${o.stat} ${o.dc}]</b>`:''}</button>`).join('')}</div>${isMyTurn?isSolo()?`<button type="button" class="ghost-help" data-action="steady-breath" ${info.advantage?'disabled':''}>Steady your breath · −30s · advantage</button>`:(info.advantage?'<p class="thin-note">Someone is helping. The next roll has advantage.</p>':''):(info.helpBy?'<p class="thin-note">Help already offered.</p>':`<button type="button" class="ghost-help" data-action="help-speaker">HELP · spend your next turn to give advantage</button>`)}`;}
    return `<section class="story-area" aria-label="Resident ghost dialogue">${wickBox()}<div class="horace-conversation ghost-chapter ${cold?'ghost-faded':''}" aria-label="${esc(info.name)} conversation"><div class="ghost-portrait"><div class="horace-figure">${art}</div><div class="horace-name">${esc(info.name)}<small>${esc(info.job)}</small></div>${spiritFlames(info.warmth)}</div><div class="ghost-dialogue"><div class="speaker-pill">${info.closed?'A tender goodbye':'THE GHOST SAYS'}</div><p class="horace-line" data-ghost-text>${esc(line)}</p>${last&&!info.closed?`<p class="ghost-last"><b>${esc(last.speaker)}:</b> ${esc(last.text)}</p>`:''}${replies}${info.fragments?.length?`<div class="ghost-fragments"><b>SHARED CLUE FRAGMENTS</b>${info.fragments.map(f=>`<p>✦ ${esc(f)}</p>`).join('')}</div>`:''}<div class="ghost-progress">${Math.min(info.exchange,info.maxExchanges)} / ${info.maxExchanges} conversations · ${info.rollsUsed}/4 dice checks</div></div></div></section>`;
  }
  function horaceFallback(){return `<section class="horace-conversation" aria-label="Horace Tock the clockmaker ghost"><div class="ghost-portrait">${horacePortrait()}</div><div class="ghost-dialogue"><p class="horace-line">Oh! Visitors. You're early. Or I'm late.</p></div></section>`;}
  function crossroadsUI(){const st=state?.story||{}, ghost=st.ghost;if(!ghost)return '';if(ghost.crossroads)return `<div class="crossroads-result"><b>✦ THE PARTY CHOSE:</b> ${esc(ghost.crossroads.choice)} · ${ghost.crossroads.success?'success':'failure'}</div>`;const votes=Object.values(ghost.votes||{});return `<div class="crossroads"><div class="speaker-pill">WICK'S CROSSROADS · VOTE TO DECIDE</div>${(st.choices||[]).map(c=>`<button type="button" class="horace-reply" data-action="crossroads-vote" data-value="${esc(c.id)}" ${ghost.votes?.[state.me.id]?'disabled':''}>${esc(c.label)} ${c.stat?`[${c.stat} ${c.dc}]`:''}<span class="vote-total">${votes.filter(v=>v===c.id).length} vote(s)</span></button>`).join('')}<p class="thin-note">${ghost.votes?.[state.me.id]?'Your vote is in. Waiting for the party…':'Majority wins; ties are settled by server-rolled d20s.'}</p></div>`;}
  function typeGhostLine(){
    const el=document.querySelector('[data-ghost-text]');
    const ghost=state?.story?.ghost;
    if(!el||!ghost) return;
    const key=[state.round,ghost.id,ghost.closed,ghost.history?.at(-1)?.at||0].join(':');
    if(key===lastTypedGhostKey)return;
    lastTypedGhostKey=key;
    if(window.matchMedia?.('(prefers-reduced-motion: reduce)').matches)return;
    if(ghostTypingTimer)clearInterval(ghostTypingTimer);
    const text=el.textContent;
    el.textContent='';let i=0;
    ghostTypingTimer=setInterval(()=>{el.textContent=text.slice(0,++i);if(i>=text.length){clearInterval(ghostTypingTimer);ghostTypingTimer=null;}},24);
  }
  function diceRollOverlay(roll){if(!roll)return;const old=document.querySelector('.dice-layer');old?.remove();const wrapper=document.createElement('div');wrapper.className='dice-layer';wrapper.setAttribute('role','status');wrapper.setAttribute('aria-live','assertive');const tie=roll.context==='vote_tie';const values=tie?Object.entries(roll.diceByOption||{}).map(([id,val])=>`${id} ${val}`).join(' · '):`${(roll.dice||[]).join(' / ')} + ${roll.modifier} = ${roll.total} vs DC ${roll.dc}`;wrapper.innerHTML=`<div class="dice-box">${roll.critical?`<div class="crit-ghosts" aria-hidden="true">${Array.from({length:6},(_,i)=>`<svg class="boil crit-ghost crit-ghost-${i}" viewBox="0 0 30 35"><path d="M4 31V15Q4 4 15 4Q26 4 26 15V31L21 27L15 31L9 27Z" fill="#F4E9D8" stroke="#1A1A1A" stroke-width="3.5"/><circle cx="11" cy="17" r="2" fill="#1A1A1A"/><circle cx="19" cy="17" r="2" fill="#1A1A1A"/></svg>`).join('')}</div>`:''}<svg class="d20-svg boil" viewBox="0 0 120 120" aria-hidden="true"><path d="M60 5L112 42L93 108H27L8 42Z" fill="#E3B23C" stroke="#1A1A1A" stroke-width="6" stroke-linejoin="round"/><path d="M60 5L60 108M8 42L93 108M112 42L27 108M8 42L112 42" stroke="#1A1A1A" stroke-width="4" fill="none"/></svg><div class="dice-score">${esc(values)}</div><div class="dice-outcome">${tie?'TIE-BREAKER: '+esc(roll.winner):roll.critical?'NATURAL 20 · CRITICAL! +30s':roll.fumble?'NATURAL 1 · FUMBLE':roll.success?'SUCCESS':'NOT QUITE'}</div></div>`;document.body.appendChild(wrapper);setTimeout(()=>wrapper.remove(),1900);}
  const horaceFaces = {
    nervous:{bl:'M100 82 L128 74',br:'M172 74 L200 82',m:'M138 172 q6 -5 12 0 q6 5 12 0',blush:0,tear:0,ey:112},
    happy:{bl:'M100 80 Q114 68 128 78',br:'M172 78 Q186 68 200 80',m:'M132 166 Q150 188 168 166',blush:1,tear:0,ey:110},
    sad:{bl:'M100 78 L128 70',br:'M172 70 L200 78',m:'M136 178 Q150 166 164 178',blush:0,tear:1,ey:116},
    grumpy:{bl:'M100 72 L128 84',br:'M172 84 L200 72',m:'M136 174 L164 174',blush:0,tear:0,ey:114}
  };
  function setHoraceFace(mood){const f=horaceFaces[mood]||horaceFaces.nervous; const el=document.getElementById('horace');if(!el)return;for(const [id,prop,val] of [['browL','d',f.bl],['browR','d',f.br],['mouth','d',f.m],['blush','opacity',f.blush],['tear','opacity',f.tear],['eyeL','cy',f.ey],['eyeR','cy',f.ey]])el.querySelector('#'+id)?.setAttribute(prop,String(val));}
  let state = null, ws = null, mode = 'landing', nameDraft = '', codeDraft = '', capacityDraft = 5;
  let token = null, seatId = null, roomCode = null, intentionalClose = false, reconnectAttempt = 0, connectGeneration = 0, retryTimer = null;
  let soundEnabled = localStorage.getItem('tlc:sound') === 'on';
  let serverOffset = 0, connectionState = 'idle', dials = [1,1,1,1], chatCollapsed = window.innerWidth < 540;
  let libraryWordDraft = '', leverPointerHeld = false, lastTypedGhostKey = null, ghostTypingTimer = null;
  let audioCtx = null, ambience = null, heartbeatInterval = null, toastTimeout = null, pendingConnect = null, lastPing = 0;
  const portraitSvg = `<svg class="boil" viewBox="0 0 70 100" role="img" aria-label="Victorian silhouette portrait"><path d="M9 98Q9 65 27 61Q22 46 22 31Q22 13 35 13Q50 13 49 31Q49 47 43 62Q64 70 65 98Z" fill="#F4E9D8" stroke="#1A1A1A" stroke-width="5" stroke-linejoin="round"/><path d="M18 26Q22 3 35 9Q52 10 54 26" fill="none" stroke="#1A1A1A" stroke-width="5"/><circle cx="29" cy="35" r="3" fill="#1A1A1A"/><circle cx="42" cy="35" r="3" fill="#1A1A1A"/><path d="M30 49Q36 55 43 49" fill="none" stroke="#1A1A1A" stroke-width="4"/><ellipse cx="23" cy="44" rx="5" ry="3" fill="#F2A7A0"/><ellipse cx="48" cy="44" rx="5" ry="3" fill="#F2A7A0"/></svg>`;
  const lockSVG = `<svg class="boil" width="55" height="55" viewBox="0 0 80 80" aria-hidden="true"><path d="M23 35V24a17 17 0 0 1 34 0v11" stroke="#1A1A1A" stroke-width="6" fill="none"/><rect x="15" y="35" width="50" height="35" rx="9" fill="#E3B23C" stroke="#1A1A1A" stroke-width="6"/><circle cx="40" cy="49" r="6" fill="#1A1A1A"/><path d="M40 53v8" stroke="#1A1A1A" stroke-width="5"/></svg>`;
  function esc(s) { return String(s??'').replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
  function showToast(text) { toastEl.textContent=text; toastEl.classList.add('show'); clearTimeout(toastTimeout); toastTimeout=setTimeout(()=>toastEl.classList.remove('show'),3900); }
  function linkToRoom(code) { return `${location.origin}${roomPath(code)}`; }
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
    if (t.frozenRemainingMs !== null && t.freezeUntil && Date.now()+serverOffset<t.freezeUntil) return t.frozenRemainingMs;
    if(t.deadlineAt===null) return t.durationMs || (isSolo()?1500000:1200000);
    return Math.max(0, t.deadlineAt-(Date.now()+serverOffset));
  }
  function clockText(ms) { const s=Math.ceil(Math.max(0,ms)/1000); return `${String(Math.floor(s/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`; }
  function candle(small=false,id='') { return `<div class="${small?'small-candle':'big-candle'}" ${id?`id="${id}"`:''} role="img" aria-label="The candle representing the shared countdown"><svg class="boil candle-svg" viewBox="0 0 100 195" aria-hidden="true"><path d="M26 78h48v102H26z" fill="#F4E9D8" stroke="#1A1A1A" stroke-width="6" stroke-linejoin="round"/><path d="M26 92q10 16 16 0q9 25 17 0q8 17 15 0" fill="none" stroke="#1A1A1A" stroke-width="5" stroke-linecap="round"/><path d="M50 78V64" fill="none" stroke="#1A1A1A" stroke-width="5" stroke-linecap="round"/><g class="flame flick"><path d="M50 17C69 36 69 55 50 64C31 56 31 36 50 17Z" fill="#E3B23C" stroke="#1A1A1A" stroke-width="5"/><path d="M50 40q8 10 0 16q-8-6 0-16" fill="#E8735A"/></g><path d="M16 184h68" fill="none" stroke="#1A1A1A" stroke-width="6" stroke-linecap="round"/><rect class="wax-shade" x="30" y="94" width="40" height="0" fill="#6B4E71" opacity=".2" /></svg><div class="candle-time">${isSolo()?'25:00':'20:00'}</div></div>`; }

  let tlcNavOpen = false;

  function tlcBackButton() {
    if (!state && mode === 'landing') return '';
    return `<button type="button" class="tlc-back-arrow"
      data-action="tlc-back">← Back</button>`;
  }

  function tlcNavigationDialog() {
    if (!tlcNavOpen) return '';
    const chapter = {
      foyer: 'The Foyer',
      library: 'The Library',
      crypt: 'The Crypt',
      finale: 'Beneath Kaashi'
    }[state?.stage] || 'Character selection';

    return `<div class="tlc-nav-shade">
      <section class="tlc-nav-dialog" role="dialog"
        aria-modal="true" aria-labelledby="tlc-nav-title">
        <div class="tlc-nav-eyebrow">
          THE LAST CANDLE · YOUR POCKET MAP
        </div>
        <h2 id="tlc-nav-title">Where to?</h2>
        <p>You are at <strong>${chapter}</strong>.</p>
        <p>Returning cannot rewind shared puzzles or restore candle time.</p>
        <div class="tlc-nav-actions">
          <button type="button" class="tlc-nav-choice"
            data-action="tlc-back-close">← Back to game</button>
          <button type="button" class="tlc-nav-choice"
            data-action="tlc-back-home">⌂ Return to home</button>
        </div>
        <p class="tlc-nav-note">
          The live round keeps running if you leave.
          Use your room link to rejoin while the server is running.
        </p>
      </section>
    </div>`;
  }
  function topbar() { return `<header class="topbar"><div class="tlc-brandbar">${tlcBackButton()}<div class="brand">THE LAST CANDLE</div></div><div class="top-controls"><button class="ghost-btn ${soundEnabled?'active':''}" data-action="sound" aria-pressed="${soundEnabled}" title="Sound ${soundEnabled?'on':'off'}">${soundEnabled?'♪ Sound on':'♫ Sound off'}</button>${state?`<span class="tag">${isSolo()?'SOLO RITUAL':esc(state.room.code)}</span>`:''}</div></header>`; }
  function shell(content) { const theme = state?.stage==='finale' ? 'theme-kaashi' : state?.stage==='library' || state?.phase==='library_solved' ? 'theme-library' : state?.stage==='foyer' || state?.phase==='foyer_solved' ? 'theme-foyer' : mode==='landing' && !state ? 'theme-landing' : state?.phase==='stage3_preview' || state?.phase==='crypt_solved' || state?.phase==='stage4_preview' || state?.stage==='crypt' ? 'theme-crypt' : 'theme-selection'; return `<div class="app-shell ${theme}">${topbar()}<main class="app-main fade-in">${content}</main></div>${connectionState==='reconnecting'?'<div class="connection-warning" role="alert">Reconnecting to the manor… the candle continues to burn.</div>':''}`; }
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
    const hero = `<section class="hero"><div class="landing-copy"><div class="hero-pills"><span class="tag">🕯 1–5 players</span><span class="tag">No login</span></div><div class="kicker">FOUR CHAPTERS · HOLLOW MANOR · 1893</div><h1><span>The Last</span><span>Candle</span></h1><p class="story">A cozy little haunting. The ghosts just want someone to listen. Eleanor Hollow has other plans, unfortunately.</p><div class="hero-actions"><button class="btn" data-action="create-screen">Gather a Circle</button><button class="btn outline" data-action="solo-create">Enter Alone</button></div><p class="hero-note">2–5 together · 20 minutes / alone · 25 minutes</p><button class="hero-join-link" data-action="join-screen">Have a 4-letter code? Join your friends →</button>${returnLink?`<div class="return-links">${returnLink}</div>`:''}</div><div class="illustration" aria-label="A small ghost peeks beside a candle">${landingGhostSVG}</div></section>`;
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
        <div class="solo-pick-art">${charArt(id)}</div><div class="solo-pick-copy"><span class="char-class">${r.classTag}</span><strong>${r.character}</strong><span>${esc(r.ability)}</span><small>${esc(r.abilityText)}</small>${statBadges(id)}${id==='walker'?'<em>Ability available in Stage 3, not the Foyer.</em>':''}</div>
        <div class="solo-pick-mark">${picked?'✦ EQUIPPED':'◇ SELECT'}</div></button>`;}).join('');
    return shell(`<section class="solo-prep"><div class="kicker">ONE SOUL · FIVE LENSES · 1893</div><h1 class="page-title">ENTER THE VEIL ALONE</h1><p class="subhead">You will carry all five characters' clues, but only one portrait can speak at a time. Each change of Lens takes two real seconds while the candle burns.</p>
      <div class="solo-prep-summary"><span>☾ 25:00 CANDLE</span><span>✦ ${equipped.length} / 2 POWERS CHOSEN</span><span>⚿ FIVE LENSES</span></div>
      <h2 class="section-title">Choose two powers</h2><p class="thin-note">Every character's clues remain accessible through the Lens. Only the two powers you equip now can be cast this round. Tap a card again to remove it.</p>
      <div class="solo-pick-grid" role="group" aria-label="Choose exactly two solo abilities">${list}</div>
      <div class="solo-prep-footer"><div><div class="eyebrow">YOUR SOLITARY VIGIL</div><p>${equipped.length===2?`Equipped: ${equipped.map(id=>roles[id].character).join(' + ')}.`:'Select exactly two abilities before the flame is lit.'}</p></div><button class="btn" data-action="solo-start" ${equipped.length!==2?'disabled':''}>BEGIN ALONE →</button></div></section>`);
  }
  function soloRoleReveal(){
    const r=roles.medium;
    return shell(`<div class="reveal-shell"><div class="reveal-frame" style="--role-color:${r.color}"><div class="eyebrow">FIVE SPIRITS · ONE VESSEL</div><div class="reveal-art">${charArt('medium')}</div><div class="reveal-role">THE FIRST LENS · SEER</div><h1 class="reveal-name">VESPER</h1>${statBadges('medium')}<p class="reveal-instruction">The manor lends you five pairs of eyes, but will only let you look through one at a time.</p><div class="detail-heading">WHAT YOU CAN SEE</div><p class="reveal-instruction">Only the active portrait's private clues. The Lens bar below lets you become Quill, Ember, Crowe or Wren.</p><div class="detail-heading">WHAT YOU MUST DO</div><p class="reveal-instruction">Remember each clue as you switch. Every change costs two seconds. Enter the clock hours only while wearing Crowe's Lens.</p><div class="carry-declaration">EQUIPPED POWERS: ${state.solo.equippedAbilities.map(id=>roles[id].character+' · '+roles[id].ability).join(' / ')}</div><p class="thin-note">The 25-minute candle is already burning. Audio is optional and off by default.</p><button class="btn" data-action="ack">OPEN YOUR EYES →</button></div></div>`);
  }
  function soloLensBar(){
    const active=state.solo.activeLens, target=state.solo.targetLens;
    return `<nav class="lens-bar" aria-label="Switch character lens"><div class="lens-heading"><span>✧ THE LENS</span><span>${target?'Smoke is gathering…':'One vision at a time · 2 seconds per switch'}</span></div><div class="lens-portraits">${roster.map(id=>{const r=roles[id],isActive=active===id,isTarget=target===id;
      return `<button class="lens-portrait ${isActive?'current':''} ${isTarget?'summoning':''}" style="--role-color:${r.color}" data-action="solo-lens" data-value="${id}" ${target||isActive?'disabled':''} aria-current="${isActive?'true':'false'}" aria-label="${r.character}, ${r.name}${isActive?', current Lens':''}"><span class="lens-art">${charArt(id)}</span><strong>${r.character}</strong><small>${r.glyph}</small></button>`;}).join('')}</div></nav>`;
  }
  function soloAbilityPanel(){
    const id=state.solo.activeLens;
    if(!id)return '';
    const r=roles[id], equipped=state.solo.equippedAbilities.includes(id),used=state.abilities.used?.[id],future=id==='walker'&&state.stage!=='crypt',exhausted=id==='archivist'&&state.hintLevel>=3;
    return `<section class="ability-panel" style="--role-color:${r.color}"><div class="eyebrow">${r.character} · ONCE-PER-ROUND POWER</div><div class="power-item"><span class="power-rune">${r.glyph}</span><div class="power-copy"><strong>${esc(r.ability)}</strong><small>${esc(r.abilityText)}</small>${statBadges(id)}</div><button class="power-cast" data-action="cast-ability" data-value="${id}" ${!equipped||used||future||exhausted?'disabled':''}>${!equipped?'NOT EQUIPPED':used?'USED':future?'STAGE 3':exhausted?'NO HINTS':'CAST'}</button></div>${state.abilities.secondTurnArmed?'<div class="power-status">⚿ Second Turn is armed: the next wrong code costs no time.</div>':''}${state.timer.freezeUntil&&Date.now()+serverOffset<state.timer.freezeUntil?'<div class="power-status">✧ Steady Flame holds the clock still.</div>':''}</section>`;
  }
  function soloFoyer(){
    const active=state.solo.activeLens,target=state.solo.targetLens,r=active?roles[active]:null;
    const focal=target?`<div class="solo-veil-wait" role="status" aria-live="polite"><div class="solo-smoke" aria-hidden="true"></div><div class="solo-veil-content"><span class="solo-veil-glyph">${roles[target].glyph}</span><h2>Through the smoke…</h2><p>Summoning ${roles[target].character}'s memories. The candle does not wait.</p><strong data-lens-remaining>2.0s</strong></div></div>`:`${veilPanel()}${soloAbilityPanel()}${cluePanel(active,state.clues[active]||{})}`;
    return shell(`${timerHeader()}<div class="stage-header"><div><div class="kicker">SOLO VIGIL · CHAPTER I OF IV</div><h1 class="page-title">The Foyer</h1><p class="stage-story">Four portraits stare from the wall. The grandfather clock has stopped. Eleanor whispers: <em>“They each died at their hour.”</em></p></div><span class="tag">${target?'SHIFTING…':r?.character+' · '+r?.name}</span></div>${ghostConversation()}<div class="game-layout solo-game"><div class="solo-clue-space">${focal}</div><aside class="sidebar">${hints()}<div class="solo-reminder"><strong>ONE LENS · FIVE SECRETS</strong><p>Read each character's clue, remember the details, then switch. Crowe alone can turn the key.</p></div></aside></div>${soloLensBar()}`);
  }
  function soloPreview(){const result=state.result||{},score=result.secondsRemaining??Math.floor(timeLeft()/1000);
    return shell(`<div class="ending-shell solo-ending"><div class="eyebrow">SOLO TRIAL · STAGE ONE COMPLETE</div><h1 class="page-title">The Clock Awakens</h1><div class="door-frame"><div class="door-glow on"></div><div class="door open"></div></div><p>You held five memories in one mind. The doors open, but the Library still waits in shadow.</p><div class="kicker">SOLO FOYER RANK · SEPARATE FROM TEAM SCORES</div><div class="solo-rank">${esc(result.rank||'The Last Witness')}</div><div class="ending-time">${clockText(score*1000)}</div><p class="thin-note">This result belongs to an older room. All four chapters are playable now. Start a fresh vigil to continue the complete story.</p><button class="btn" data-action="again">↺ Begin another solo vigil</button></div>`);
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
      return `<button type="button" class="character-card ${active?'is-preview':''} ${owner?'is-locked':''}" style="--role-color:${r.color}" data-action="preview-character" data-value="${id}" aria-pressed="${active}" aria-label="View ${r.character}, ${r.name}${owner?', locked by '+owner.name:''}"><div class="char-index">0${roster.indexOf(id)+1}<span class="char-rune">${r.glyph}</span></div><div class="char-silhouette">${charArt(id)}</div><div class="char-card-content"><span class="char-class">${r.classTag}</span><div class="char-name">${r.character}</div><span class="char-role">${r.name}</span>${statBadges(id)}</div>${owner?`<div class="char-lock-banner"><span>◆ LOCKED</span><strong>${esc(owner.name)}</strong></div>`:''}</button>`;}).join('');
    const detail=`<section class="character-detail" style="--role-color:${selected.color}" aria-live="polite"><div class="detail-glyph">${selected.glyph}</div><div class="detail-main"><div class="kicker">${selected.classTag} · ${selected.name}</div><h2>${selected.character}</h2><div class="detail-columns"><div><div class="detail-heading">WHAT YOU CAN SEE</div><p>${esc(selected.see)}</p></div><div><div class="detail-heading">ONCE-PER-GAME ABILITY · ${esc(selected.ability)}</div><p>${esc(selected.abilityText)}</p></div></div>${statBadges(previewCharacter)}<div class="detail-actions">${locked?`<div class="locked-callout">◆ LOCKED IN AS ${roles[currentRole].character}</div>`:selectedOwner?`<div class="locked-callout">Claimed by ${esc(selectedOwner.name)}</div>`:`<button class="btn lock-button" data-action="lock-character" data-value="${previewCharacter}" ${!canLock?'disabled':''}>${selectClosed?'THE VEIL HAS CLOSED':'◆ LOCK IN '+selected.character}</button>`}${locked?`<span class="carry-hint">${secondaryRoles(mine).length?'You also carry: '+secondaryRoles(mine).map(id=>roles[id].character).join(', '):'Additional responsibilities are assigned when all players lock in.'}</span>`:''}</div></div></section>`;
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
  function abilityPanel(){const abilities=state.abilities||{used:{}};return `<section class="ability-panel"><div class="eyebrow">YOUR ONCE-PER-GAME POWERS</div><div class="power-grid">${state.me.roles.map(id=>{const r=roles[id],used=abilities.used?.[id],future=id==='walker'&&state.stage!=='crypt',exhausted=id==='archivist'&&state.hintLevel>=3;return `<div class="power-item" style="--role-color:${r.color}"><span class="power-rune">${r.glyph}</span><div class="power-copy"><strong>${r.character} · ${r.ability}</strong><small>${esc(r.abilityText)}</small>${statBadges(id)}</div><button class="power-cast" data-action="cast-ability" data-value="${id}" ${used||future||exhausted?'disabled':''}>${used?'USED':future?'STAGE 3':exhausted?'NO HINTS':'CAST'}</button></div>`;}).join('')}</div>${abilities.secondTurnArmed?'<div class="power-status">⚿ SECOND TURN ARMED — the next wrong code costs no time.</div>':''}${state.timer.freezeUntil&&Date.now()+serverOffset<state.timer.freezeUntil?'<div class="power-status">✧ STEADY FLAME — candle held still for 20 seconds.</div>':''}</section>`;}
  function veilPanel(){return state.veilClue?`<div class="veil-revelation" data-veil-clue data-expires="${state.veilClue.expiresAt}" role="status"><div class="detail-heading">VESPER · VEIL SIGHT</div><strong>A hidden whisper escapes: ${esc(state.veilClue.symbol)} marks the hour ${state.veilClue.hour}.</strong><div class="veil-remaining">Fades in <span data-veil-time></span></div></div>`:'';}
  function foyer(){return shell(`${timerHeader()}<div class="stage-header"><div><div class="kicker">CHAPTER I OF IV</div><h1 class="page-title">The Foyer</h1><p class="stage-story">Four portraits stare from the wall. The grandfather clock has stopped. Eleanor whispers: <em>“They each died at their hour.”</em></p></div><span class="tag">${state.me.roles.map(r=>roles[r].name.replace('The ','')).join(' + ')}</span></div>${ghostConversation()}<div class="game-layout"><div>${veilPanel()}${abilityPanel()}${state.me.roles.map(id=>cluePanel(id,state.clues[id]||{})).join('')}</div><aside class="sidebar">${hints()}${chat(true)}<div class="thin-note" style="text-align:center">✧ Only the Locksmith can submit the clock code.<br>Talk aloud or use the spirit board to share what you see.</div></aside></div>`);}
  const libraryInstructions = {
    medium: {see:'Five ghost-written spirit symbols burning into the library wall. In Solo, only Vesper remembers the three-beat cadence.',do:'Read the symbols in order. In Solo, memorize the three intervals before changing to Crowe.'},
    archivist: {see:'A torn cipher wheel translating spirit symbols into letters; the wheel changes with each new round.',do:'Translate Vesper’s five symbols in order and tell Crowe the letters.'},
    lantern: {see:'Books whose spines glow with five letters. Other titles are dark decoys.',do:'Read the glowing letters aloud. Use them to check that the decoded five-letter word is correct.'},
    locksmith: {see:'The binding lectern for a five-letter word, followed by a sealed lever mechanism.',do:'Ask Vesper, Quill and Ember for the decoded word. Bind it, then operate the lever when the mechanism opens.'},
    walker: {see:'A brass lever marked with your seat’s name, summoned after the cipher is bound.',do:'Keep your hand on the lever at the same time as the whole circle for three uninterrupted seconds.'}
  };
  function libraryCluePanel(role,detail){
    const r=roles[role], info=libraryInstructions[role], part=state.library?.part;
    let content='';
    if(role==='medium')content=`<div class="wall-script" aria-label="Ghost writing symbols in order">${(detail.symbols||[]).map(g=>`<span class="spectral-symbol">${esc(g)}</span>`).join('')}</div>${isSolo()?`<div class="cadence-card"><div class="detail-heading">VESPER'S THREE-BEAT MEMORY</div><p>After the lever is held, the three glowing beats are spaced at:</p><div class="cadence-list">${(detail.cadence||[]).map((v,i)=>`<span>BEAT ${i+1}<strong>${(v/1000).toFixed(2)}s</strong></span>`).join('')}</div><p class="thin-note">The first beat starts after a 1-second ritual opening, then these intervals. Remember them before switching to Crowe.</p></div>`:''}`;
    if(role==='archivist')content=`<div class="cipher-wheel" role="table" aria-label="Symbol to letter cipher wheel">${(detail.wheel||[]).map(x=>`<div class="cipher-pair" role="row"><span role="cell">${esc(x.symbol)}</span><span class="cipher-spoke">⟶</span><strong role="cell">${esc(x.letter)}</strong></div>`).join('')}</div>`;
    if(role==='lantern')content=`<div class="bookcase" aria-label="Books in the haunted library">${(detail.books||[]).map((b,i)=>`<div class="book-spine ${b.glowing?'is-glowing':'is-dark'}" style="--book-index:${i}" aria-label="${b.glowing?'Glowing':'Unlit'} spine ${esc(b.letter)}"><span>${esc(b.letter)}</span><i aria-hidden="true">${b.glowing?'✦':'—'}</i></div>`).join('')}</div><p class="thin-note">Only spines marked ✦ and glowing belong to Eleanor’s five-letter word. The letters are not in reading order.</p>`;
    if(role==='locksmith')content=part==='cipher'?`<form class="library-word-form" id="library-word-form"><label for="library-word" class="detail-heading">THE WORD THAT OPENS THE SHELF</label><input id="library-word" class="input library-word" name="word" maxlength="5" autocomplete="off" autocapitalize="characters" spellcheck="false" value="${esc(libraryWordDraft)}" placeholder="_ _ _ _ _" aria-label="Five-letter decoded word" /><button class="btn full" type="submit">⚿ BIND THE WORD</button></form>`:'<div class="binder-seal">⚿ <span>THE CIPHER HAS BEEN BOUND</span></div>';
    if(role==='walker')content='<div class="walker-promise">◇ Your lever is waiting behind the sealed shelf.</div>';
    return `<section class="role-panel library-role" style="--role-color:${r.color}" aria-label="${esc(r.name)} library clue"><div class="kicker">${r.character} · ${r.classTag}</div><h3>${r.glyph} ${r.name}</h3><div class="instruction-title">WHAT YOU CAN SEE</div><p class="instruction">${esc(info.see)}</p>${content}<div class="instruction-title">WHAT YOU MUST DO</div><p class="instruction">${esc(info.do)}</p></section>`;
  }
  function libraryLevers(){
    const lib=state.library, mineHeld=lib.heldSeats?.includes(state.me.id),holdStarted=lib.holdStartedAt;
    if(isSolo()){
      const r=lib.rhythm||{},pending=!!state.solo.targetLens;
      const crowe=state.solo.activeLens==='locksmith';
      return `<section class="lever-chamber solo-rhythm">
        <div class="eyebrow">THE THREE-TAP SOLO RITE</div>
        <h2>One hand. Three easy knocks.</h2>
        <p>Use Crowe's Lens and tap the brass lever three times.
        <strong>No timing or holding required.</strong></p>
        <div class="rhythm-beats">
        ${[0,1,2].map(i=>`<div class="rhythm-beat ${r.beatIndex>i?'complete':''}">
        <span>${r.beatIndex>i?'✓':'✦'}</span>
        <small>${i+1}</small></div>`).join('')}</div>
        <div class="rhythm-progress">${r.beatIndex||0} / 3 TAPS COMPLETED</div>
        ${!crowe||pending?
        `<button class="btn" type="button" data-action="rhythm-switch"
        ${pending?'disabled':''}>${pending?'SWITCHING TO CROWE…':'SWITCH TO CROWE →'}</button>`:
        `<button class="lever-button solo-lever" type="button"
        data-action="rhythm-tap">TAP THE LEVER ·
        ${Math.min(3,(r.beatIndex||0)+1)} OF 3</button>`}
        </section>`;
    }
    return `<section class="lever-chamber"><div class="eyebrow">ALL SOULS MUST HOLD · 3 SECONDS</div><h2>The Circle of Brass</h2><p>Every player must <strong>press and hold</strong> their lever together. If any hand releases or disconnects, the ritual resets for everyone.</p><div class="lever-party">${state.players.map(p=>`<div class="lever-seat ${lib.heldSeats.includes(p.id)?'held':''} ${!p.connected?'offline':''}" data-seat-id="${p.id}"><span class="lever-presence">${lib.heldSeats.includes(p.id)?'✦':'◇'}</span><b>${esc(p.name)}</b><small>${lib.heldSeats.includes(p.id)?'HOLDING':'AWAITING'}</small></div>`).join('')}</div><div class="lever-progress"><div class="lever-progress-fill" data-hold-progress style="width:0%"></div></div><p class="thin-note" data-hold-count>${lib.heldSeats.length} of ${state.players.length} hands on brass</p><button class="lever-button ${mineHeld?'held':''}" data-lever-hold="multi" aria-pressed="${mineHeld}" aria-label="Press and hold your lever for three seconds"><span>⚙</span><strong>${mineHeld?'KEEP HOLDING':'PRESS AND HOLD'}</strong></button><p class="thin-note">Touch, mouse, or keyboard: keep the lever down until the shelf opens.</p></section>`;
  }
  function library(){
    const part=state.library?.part||'cipher', active=isSolo()?state.solo.activeLens:null,target=isSolo()?state.solo.targetLens:null;
    const focal=target?`<div class="solo-veil-wait" role="status" aria-live="polite"><div class="solo-smoke" aria-hidden="true"></div><div class="solo-veil-content"><span class="solo-veil-glyph">${roles[target].glyph}</span><h2>Through the smoke…</h2><p>Summoning ${roles[target].character}’s memories.</p><strong data-lens-remaining>2.0s</strong></div></div>`:
      `${isSolo()?soloAbilityPanel():abilityPanel()}${(isSolo()?[active]:state.me.roles).filter(Boolean).map(id=>libraryCluePanel(id,state.clues[id]||{})).join('')}`;
    return shell(`${timerHeader()}<div class="library-stage"><div class="library-ambient" aria-hidden="true"><div class="library-pillar"></div><div class="library-pillar"></div><div class="library-embers">✦ &nbsp; ✧ &nbsp; ✦</div></div><div class="kicker">CHAPTER II OF IV · ${part==='cipher'?'THE CIPHER':'THE LEVERS'}</div><h1 class="page-title library-title">THE LIBRARY OF WHISPERS</h1><p class="stage-story">Books rearrange themselves. A voice hisses a word you cannot quite hear.</p><div class="library-progress"><span class="${part==='cipher'?'now':'done'}">I · DECODE</span><span class="${part==='levers'?'now':'waiting'}">II · AWAKEN THE LEVERS</span></div></div>${ghostConversation()}<div class="game-layout ${isSolo()?'solo-game':''}"><div class="solo-clue-space">${part==='levers' ? libraryLevers():''}${focal}</div><aside class="sidebar">${hints()}${isSolo()?'<div class="solo-reminder"><strong>ONE LENS · ONE MEMORY</strong><p>Switch portraits to combine the five symbols, the wheel and the glowing books. The two-second switch cost still applies.</p></div>':chat(true)}</aside></div>${isSolo()?soloLensBar():''}`);
  }
  function librarySolved(){
    const solo=isSolo();
    return shell(`${timerHeader()}${ghostConversation()}<section class="elevation-scene" role="status" aria-live="polite"><div class="elevation-bookshelf" aria-hidden="true"><div class="shelf-door"><span>✶</span><span>✦</span><span>✶</span></div></div><div class="elevation-copy"><div class="kicker">THE MANOR HAS HEARD YOU</div><h1 class="elevation-title">THE SHELF YIELDS</h1><p>The living circle holds. An ancient bookshelf swings open as light tears through the dust.</p><button class="btn" data-action="continue-library" disabled>FOLLOW THE LIGHT →</button></div></section>`);
  }
  const cryptSkullSVG = `<svg class="crypt-skull boil" viewBox="0 0 42 44" aria-hidden="true"><path d="M10 28C4 22 6 8 21 7C36 8 38 22 32 28V38H10Z" fill="#EDE6D6" stroke="#1A1A1A" stroke-width="4.5" stroke-linejoin="round"/><circle cx="15" cy="22" r="4" fill="#1A1A1A"/><circle cx="27" cy="22" r="4" fill="#1A1A1A"/><path d="M19 30l2-3 2 3M15 37v-6m6 6v-6m6 6v-6" stroke="#1A1A1A" stroke-width="3" fill="none" stroke-linecap="round"/></svg>`;
  function cryptGrid(){
    const info=state.crypt||{}, position=info.position||[5,0], fog=new Set((info.visible||[]).map(p=>p.join(',')));
    const known=new Set((info.knownTraps||[]).map(p=>p.join(','))),safe=info.safeTile?.join(',');
    const cells=[];
    for(let y=0;y<6;y++)for(let x=0;x<6;x++){
      const id=y+','+x,near=fog.has(id), me=position[0]===y&&position[1]===x;
      const trap=known.has(id),start=y===5&&x===0,atExit=y===0&&x===5;
      const symbol=me?'◇':(trap&&near)?(isSolo()&&state.solo.activeLens==='lantern'?'✕':cryptSkullSVG):safe===id&&near?'✦':start&&near?'S':atExit&&info.exitVisible?'⚿':'';
      cells.push(`<div class="crypt-tile ${near?'visible':'fogged'} ${me?'wren-here':''} ${trap&&near?'known-trap':''} ${safe===id&&near?'known-safe':''} ${atExit?'crypt-exit':''}" role="gridcell" aria-label="row ${y+1} column ${x+1}${me?', Wren is here':''}${trap?', known trap':''}${safe===id?', Quill confirms safe':''}${near?', visible tile':', fog'}"><span>${symbol}</span></div>`);
    }
    return `<div class="crypt-grid" role="grid" aria-label="Six by six crypt tiles. South-west entrance, north-east exit.">${cells.join('')}</div>`;
  }
  function cryptDirections(){
    const enabled=!!state.crypt?.canMove;
    return `<div class="crypt-controller" aria-label="Wren movement"><div class="kicker">WREN'S FOOTSTEPS</div><div class="crypt-arrows"><button type="button" class="crypt-arrow up" data-action="crypt-move" data-value="up" aria-label="Move north" ${enabled?'':'disabled'}>↑</button><button type="button" class="crypt-arrow left" data-action="crypt-move" data-value="left" aria-label="Move west" ${enabled?'':'disabled'}>←</button><span class="crypt-center">◇</span><button type="button" class="crypt-arrow right" data-action="crypt-move" data-value="right" aria-label="Move east" ${enabled?'':'disabled'}>→</button><button type="button" class="crypt-arrow down" data-action="crypt-move" data-value="down" aria-label="Move south" ${enabled?'':'disabled'}>↓</button></div><p class="thin-note">${enabled?'Tap an arrow, or use the keyboard arrow keys. Ask your guides before stepping.':isSolo()?'Switch to Wren’s Lens to move. The two-second switch still burns candle time.':'Only the player carrying Wren may walk. Your trap clues are theirs to hear.'}</p></div>`;
  }
  function cryptGuide(){
    const c=state.crypt||{}, role=isSolo()?state.solo.activeLens:null,guide=c.canGuide;
    const trapNames=(c.knownTraps||[]).map(([y,x])=>`R${y+1} C${x+1}`);
    const message=isSolo() ? (role==='lantern'?'EMBER · The LEFT half of the trap ledger.':role==='medium'?'VESPER · The RIGHT half appears as spectral skulls.':role==='archivist'?'QUILL · An old inscription names one safe tile.':role==='walker'?'WREN · You can only see your own position and the four neighboring tiles.':'This Lens has no trap-sight. The footsteps belong to Wren.') : c.canMove ? 'WREN · You see adjacent outlines only. Your guides must describe what lies beyond.' : state.players.length===2 ? 'THE GUIDE · You see ALL eight trap coordinates, while the floor remains fogged beyond Wren.' : 'GUIDE · Ember knows the left half; Vesper knows the right; Quill knows one safe tile.';
    return `<div class="crypt-intelligence" aria-label="Private crypt guidance"><div class="instruction-title">WHAT YOU CAN SEE</div><p>${esc(message)}</p>${guide&&trapNames.length?`<div class="trap-ledger"><b>TRAPS · ${trapNames.length} REVEALED</b><p>${esc(trapNames.join(' · '))}</p></div>`:''}${guide&&c.safeTile?`<div class="safe-inscription"><b>QUILL'S INSCRIPTION</b><p>“Stone at row ${c.safeTile[0]+1}, column ${c.safeTile[1]+1} will bear the weight of the living.”</p></div>`:''}<div class="instruction-title">WHAT YOU MUST DO</div><p>${c.canMove?'Move one tile at a time toward the north-east exit. A trapped tile costs −30 seconds and sends you back.': 'Guide Wren using the private ledger; if you cannot see traps in this Lens, switch or ask another guide.'}</p></div>`;
  }
  function cryptStage(){
    const c=state.crypt||{}, lensWait=isSolo()&&!!state.solo.targetLens;
    return shell(`${timerHeader()}<section class="crypt-stage" aria-label="Crypt maze"><div class="kicker">CHAPTER III OF IV · THE BLIND MAZE</div><h1 class="page-title">THE CRYPT OF THE HOLLOWS</h1><p class="stage-story">The candle flickers. The crypt floor is a grid of ancient tiles, and some of them are traps.</p><div class="crypt-stage-heading"><span class="pill">◇ WREN · R${(c.position?.[0]??5)+1} C${(c.position?.[1]??0)+1}</span><span class="pill">⚿ EXIT · NORTH-EAST</span><span class="pill">✕ TRAPS ${c.trapHits||0}</span></div></section>${ghostConversation()}<div class="crypt-layout"><section class="crypt-board-panel"><div class="crypt-board-top"><strong>THE FLOOR REMEMBERS</strong><span>6 × 6 · SPEAK, THEN STEP</span></div>${lensWait?`<div class="solo-veil-wait crypt-lens-wait" role="status"><span>${esc(roles[state.solo.targetLens].glyph)}</span><p>The Lens is shifting…</p><strong data-lens-remaining>2.0s</strong></div>`:cryptGrid()}${cryptDirections()}${c.sureStepArmed?'<p class="crypt-sure">◇ SURE STEP ARMED · your next trapped tile is safe.</p>':''}</section><div class="crypt-sidebar">${lensWait?'':cryptGuide()}${isSolo()?soloAbilityPanel():abilityPanel()}${hints()}${isSolo()?'<div class="solo-reminder">Only Wren can walk. Ember reveals LEFT traps, Vesper RIGHT traps. Switch Lenses, remember the coordinates, then return to Wren.</div>':chat(true)}</div></div>${isSolo()?soloLensBar():''}`);
  }
  function cryptSolved(){
    return shell(`${timerHeader()}${ghostConversation()}<section class="crypt-elevation" role="status" aria-live="polite"><div class="crypt-sealed-door" aria-hidden="true"><svg class="boil" viewBox="0 0 240 300"><path d="M36 295V108Q36 30 120 30Q204 30 204 108V295Z" fill="#1A1A1A" stroke="#EDE6D6" stroke-width="6"/><path d="M53 285V109Q53 51 120 51Q187 51 187 109V285Z" fill="#E3B23C" stroke="#1A1A1A" stroke-width="6"/><path d="M120 52V284M75 150h90M75 204h90" stroke="#1A1A1A" stroke-width="5"/><circle cx="155" cy="233" r="10" fill="#EDE6D6" stroke="#1A1A1A" stroke-width="5"/></svg><span class="crypt-rays">✶　✦　✶</span></div><div class="crypt-elevation-copy"><div class="kicker">THE SEAL IS BREAKING · ONE MORE CHAPTER</div><h1 class="crypt-impact">SOMETHING WAITS BEYOND.</h1><p>A mysterious golden light pours through the ancient door. Something on the other side has been waiting a very long time.</p><button class="btn" data-action="continue-crypt" disabled>FOLLOW THE LIGHT →</button></div></section>`);
  }
  const goddessSVG = `<svg class="kaashi-goddess-svg boil" viewBox="0 0 480 480" role="img" aria-label="A reverent abstract silhouette of Goddess Chinnamasta within a lotus yantra, holding a light orb; three symbolic crimson-gold streams of light"><g class="lotus-frame" fill="none" stroke="#5E181C" stroke-width="6" stroke-linejoin="round"><circle cx="240" cy="226" r="175" stroke="#E3B23C" stroke-width="10"/><circle cx="240" cy="226" r="146"/><path d="M240 53L386 308H94Z"/><path d="M240 395L94 142H386Z"/>${Array.from({length:12},(_,i)=>`<g transform="rotate(${i*30} 240 226)"><path d="M240 55Q204 25 240 0Q276 25 240 55Z" fill="#F6C25D"/></g>`).join('')}</g><g class="deity-outline" stroke="#5E181C" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"><path d="M209 171Q204 131 240 116Q276 131 271 171L294 185Q306 201 294 225L284 293Q312 321 345 351H135Q168 321 196 293L186 225Q174 201 186 185Z" fill="#E8735A"/><path d="M212 171Q240 189 268 171" fill="none"/><path d="M194 211Q152 228 125 204M286 211Q328 228 355 204" fill="none"/><path d="M194 291Q176 331 143 344M286 291Q304 331 337 344" fill="none"/><circle cx="240" cy="205" r="25" fill="#F4E9D8"/><path d="M227 205h26M240 192v26" fill="none"/><circle cx="240" cy="116" r="42" fill="#E3B23C"/><path d="M208 104Q238 80 272 104M216 132Q240 142 264 132" fill="none"/><path d="M223 114h9m16 0h9" stroke-width="5"/><path d="M214 88L240 58L266 88" fill="#F4E9D8"/></g><g class="kaashi-rays" fill="none" stroke-width="8" stroke-linecap="round"><path d="M225 176Q160 202 83 274" stroke="#E3B23C"/><path d="M240 180Q240 244 240 291" stroke="#B82F31"/><path d="M255 176Q320 202 397 274" stroke="#E3B23C"/></g><g fill="#E3B23C" stroke="#5E181C" stroke-width="5"><ellipse cx="83" cy="288" rx="28" ry="11"/><ellipse cx="240" cy="304" rx="28" ry="11"/><ellipse cx="397" cy="288" rx="28" ry="11"/></g><path d="M128 385Q240 410 352 385M153 402Q240 420 327 402" stroke="#E3B23C" stroke-width="7" stroke-linecap="round" fill="none"/></svg> `;
  const streamNames = ['SAFFRON · THE FIRST STREAM','CRIMSON · THE SECOND STREAM','GOLD · THE THIRD STREAM'];
  const STREAM_ORDER = ['N','E','S','W'];
  function streamTile(t,i,section){
    const rays=(t.ports||[]).map(d=>{const pt={N:[32,0],E:[64,32],S:[32,64],W:[0,32]}[d];return `<path d="M32 32L${pt[0]} ${pt[1]}" stroke="#5E181C" stroke-width="8" stroke-linecap="round"/>`;}).join('');
    return `<button class="stream-tile" data-action="stream-turn" data-section="${section}" data-index="${i}" aria-label="Rotate stream ${section+1} tile row ${t.row+1} column ${t.col+1} clockwise"><svg class="boil" viewBox="0 0 64 64" aria-hidden="true"><rect x="3" y="3" width="58" height="58" rx="9" fill="#F4E9D8" stroke="#1A1A1A" stroke-width="5"/>${rays}<circle cx="32" cy="32" r="6" fill="#B82F31" stroke="#1A1A1A" stroke-width="3"/></svg></button>`;
  }
  function sectionBoard(section){
    const tiles=new Map((section.tiles||[]).map(t=>[`${t.row},${t.col}`,t]));
    const owned=section.owned && !!section.tiles;
    const cells=Array.from({length:9},(_,i)=>{const r=Math.floor(i/3),c=i%3,t=tiles.get(`${r},${c}`);return t?streamTile(t,t.index,section.id):`<div class="stream-blank" aria-hidden="true">✧</div>`;});
    return `<section class="stream-section ${section.connected?'stream-lit':''} ${owned?'stream-owned':'stream-sealed'}" aria-label="Stream ${section.id+1}, ${section.connected?'connected':'unconnected'}"><div class="stream-head"><b>${streamNames[section.id]}</b><span class="pill">${section.connected?'✦ BOWL LIT':owned?'↻ YOUR TILES':'SEALED TO YOU'}</span></div>${owned?`<span class="stream-bowl" aria-hidden="true">◡ BOWL ${section.id+1}</span><div class="stream-grid">${cells.join('')}</div><span class="stream-entry">↑ LIGHT FROM THE CENTRE</span><p class="stream-instruction">Tap each tile to turn the light path. The bowl fills when the route is continuous.</p>`:`<div class="stream-other"><span aria-hidden="true">${section.connected?'✦':'◇'}</span><p>${section.connected?'Connected to the bowl.': 'Another soul holds this part of the yantra.'}</p></div>`}</section>`;
  }
  function finaleIntro(){const f=state.finale||{};const age=Date.now()+serverOffset-(f.enteredAt||0);if(!f.enteredAt||age>4500)return '';return `<div class="kaashi-intro-overlay" role="status" aria-live="polite"><div class="kaashi-cracks" aria-hidden="true"><span>◇</span><span>◈</span><span>◇</span></div><p>THE MANOR FALLS AWAY</p><h1>BENEATH KAASHI<br><span>THE CAVE OF THE SEVERED FLAME</span></h1><p>THE SHRINE REMEMBERS.</p></div>`;}
  function offeringPanel(){const f=state.finale||{},myOffer=f.myOffer,allowed=f.canOfferAbilities||[];const waiting=(f.offeredSeats||[]).length;return `<section class="offering-panel" aria-label="Secret cooperative offerings"><div class="kicker">PART II · THE OFFERING · A TRUST ROUND</div><h2>What will you give?</h2><p>The Goddess asks something freely given. Your choice remains sealed until <strong>everyone</strong> offers. The threshold is ${f.threshold} ${f.threshold===1?'offering':'offerings'} from ${f.threshold} ${f.threshold===1?'soul':'souls'}. An unused ability or 60 seconds of candle each counts as one. Nothing counts as zero. If the party hoards, the candle loses <strong>two minutes</strong> and you try again.</p><div class="offering-counter">${waiting} / ${state.players.length} offerings sealed · round ${f.offerRound}</div>${myOffer?`<div class="sealed-choice" role="status">✦ YOUR OFFERING IS SEALED. Waiting for the others…</div>`:`<div class="offering-options">${allowed.map(r=>`<button class="btn offering-choice" data-action="offer" data-kind="ability" data-role="${r}">✦ Give up ${roles[r].character}'s unused ${roles[r].ability} power</button>`).join('')}<button class="btn offering-choice" data-action="offer" data-kind="candle">🕯 Give 60 seconds of candle</button><button class="btn offering-choice offering-none" data-action="offer" data-kind="nothing">◇ Offer nothing</button></div>`}</section>`;}
  function offeringReveal(){const f=state.finale||{},r=f.reveal||{};return `<section class="offering-reveal" role="status" aria-live="polite"><div class="kicker">THE SHRINE WEIGHS WHAT WAS GIVEN</div><h2>${r.accepted?'THE THREE STREAMS ANSWER':'THE FLAME GROWS QUIETER'}</h2><div class="reveal-offers">${(r.offers||[]).map((o,i)=>`<div class="revealed-offer" style="--delay:${i*.5}s"><strong>${esc(o.name)}</strong><span>${o.kind==='ability'?`Gave ${esc(roles[o.role]?.ability||'an ability')}`:o.kind==='candle'?'Gave 60 seconds of candle':'Kept everything'}</span></div>`).join('')}</div><p>${r.total} / ${r.threshold} offerings · ${r.accepted?'The Goddess accepts your trust.':'Two minutes will be lost. Choose again together.'}</p><p class="thin-note">Each choice was hidden until the last offer was sealed.</p></section>`;}
  function finaleStage(){const f=state.finale||{}, part=f.part;return shell(`${timerHeader()}<section class="kaashi-chapter" aria-label="Beneath Kaashi finale"><div class="kicker">CHAPTER IV OF IV · THE ONLY KAASHI SCENE</div><h1 class="kaashi-title">BENEATH KAASHI <span>THE CAVE OF THE SEVERED FLAME</span></h1><p class="kaashi-story">Eleanor's father took what was never his: a sacred yantra from this shrine. The Goddess has waited a hundred years. Return it, and give something of yourselves.</p><div class="kaashi-deity">${goddessSVG}<p class="reverence">GODDESS CHINNAMASTA · KEEPER OF THE THREE STREAMS</p><p class="deity-voice">“Return what was taken. Give what is yours to give. The light cannot be held by a closed hand.”</p></div>${wickBox()}${part==='streams'?`<div class="stream-instructions"><h2>Part I · The Three Streams</h2><p>Each stream begins at the centre of the yantra and must reach its own bowl. Rotate the five path tiles in your sections until all three bowls shine <strong>at once</strong>.</p><div class="stream-leds">${(f.sections||[]).map((x,i)=>`<span class="pill ${x.connected?'lit':''}">${x.connected?'✦':'◇'} ${i+1} ${x.connected?'LIT':'UNLIT'}</span>`).join('')}</div></div><div class="stream-section-layout">${(f.sections||[]).map(sectionBoard).join('')}</div>`:part==='offering'?offeringPanel():part==='reveal'?offeringReveal():'<div class="offering-reveal">The shrine has heard you.</div>'}${part==='streams'&&isSolo()?`<div class="solo-reminder">SOLO · Vesper controls the first stream, Quill the second, and Ember the third. Switch Lenses to turn each section. Wren and Crowe cannot turn tiles.</div>`:''}${hints()}${isSolo()&&part==='streams'?soloLensBar():''}</section>${finaleIntro()}`);}
  function finaleWin(){const r=state.result||{},f=r.storyFlags||{};const cards=(r.players||[]).map(p=>`<div class="finale-player-card"><strong>${esc(p.name)}</strong><span>${esc((p.characters||[]).join(' · '))}</span></div>`).join('');return shell(`<section class="dawn-ending" aria-label="The yantra is returned and Hollow Manor finds peace"><div class="dawn-temple"><span>✦</span><svg class="boil" viewBox="0 0 260 190" aria-hidden="true"><path d="M130 20L228 160H32Z" fill="#E3B23C" stroke="#1A1A1A" stroke-width="6"/><path d="M130 160L32 45H228Z" fill="#E8735A" stroke="#1A1A1A" stroke-width="6"/><circle cx="130" cy="97" r="34" fill="#F4E9D8" stroke="#1A1A1A" stroke-width="6"/><circle cx="130" cy="97" r="12" fill="#B82F31" stroke="#1A1A1A" stroke-width="5"/></svg></div><div class="kicker">THE YANTRA IS HOME · DAWN AT HOLLOW MANOR</div><h1 class="kaashi-win-title">THE LAST CANDLE<br>STILL BURNS.</h1><div class="eleanor-goodbye">${eleanorSVG}<p>“${esc(r.eleanor||'The dawn is warm. You may carry us forward now.')}”</p><p>Eleanor fades into the first honest light the manor has seen in a century.</p></div><div class="finale-score"><span>${isSolo()?'SOLO · THE ONE WHO RETURNED':'THE CIRCLE · TOGETHER'}</span><strong>${esc(r.rank||'The Dawnkeeper')}</strong><b>${clockText((r.secondsRemaining||0)*1000)} remaining</b></div><h2>Your living circle</h2><div class="finale-party">${cards}</div><p class="ending-data">Abilities used or given: ${esc((r.abilitiesUsed||[]).join(', ')||'None')} · ${esc(r.funStat?.label||'Crypt traps')}: ${Number(r.funStat?.value||0)} · Criticals: ${Number(f.crits||0)} · Fumbles: ${Number(f.fumbles||0)} · Votes: ${Number(f.votesTaken||0)}</p>${isHost()?'<button class="btn" data-action="again">↺ Play Again · a new haunting</button>':'<p>Waiting for the host to summon another circle…</p>'}</section>`);}
  function finaleLost(){const sol=state.solutions||{},crypt=state.cryptSolution||{},fin=state.finaleSolution||[];return shell(`<section class="kaashi-loss" aria-label="The candle dies"><div class="kicker">THE LIGHT HAS GONE OUT</div><h1>THE CANDLE IS LOST.</h1><div class="dead-flame" aria-hidden="true">◇</div><p>Eleanor whispers: “Even an unfinished story was worth sharing.”</p><p>Darkness settles on the empty shrine. Every secret is laid bare.</p><div class="solution-panels"><div><strong>FOYER · CLOCK</strong><p>Symbols: ${esc((sol.order||[]).join(' → '))}<br>Hours: ${esc((sol.code||[]).join(' · '))}</p></div><div><strong>LIBRARY · CIPHER</strong><p>Word: ${esc(state.librarySolution?.word||'Not yet known')}</p></div><div><strong>CRYPT · SAFE ROUTE</strong><p>${esc((crypt.route||[]).map(x=>`R${x[0]+1}C${x[1]+1}`).join(' → ')||'Not yet revealed')}</p><p>Traps: ${esc((crypt.traps||[]).map(x=>`R${x[0]+1}C${x[1]+1}`).join(', '))}</p></div><div><strong>KAASHI · THREE STREAMS</strong><p>${fin.length?fin.map(x=>`Stream ${x.section+1}: ${x.route.map(z=>`${z[0]+1},${z[1]+1}`).join(' → ')}`).join(' · '):'Unreached'}</p><p>The offering requires one gift from every soul.</p></div></div>${isHost()?'<button class="btn" data-action="again">↺ Play Again · new randomized puzzles</button>':'<p>Waiting for the host to restart…</p>'}</section>`);}
  function stage4Preview(){const result=state.result||{},solo=isSolo();return shell(`<div class="ending-shell ${solo?'solo-ending':''}"><div class="eyebrow">${solo?'SOLO VIGIL':'THE CIRCLE'} · THREE CHAPTERS COMPLETE</div><h1 class="page-title">SOMETHING WAITS BEYOND.</h1><div class="crypt-next-icon">✶</div><p>The sealed crypt door leads to a vision waiting beyond Hollow Manor. The Kaashi finale is now available in a new round.</p><div class="kicker">STAGE 4 · FINALE NOW PLAYABLE</div>${solo?`<p>SOLO CRYPT TRIAL · SEPARATE FROM THE TEAM</p><div class="solo-rank">${esc(result.rank||'The Unbroken Witness')}</div><div class="ending-time">${clockText((result.secondsRemaining||0)*1000)}</div>`:''}<p class="thin-note">This older round stopped before the finale. Play a new round to reach all four chapters.</p>${isHost()?'<button class="btn" data-action="again">↺ Begin another vigil</button>':'<p>Waiting for the host to restart…</p>'}</div>`);}
  function trapHandsOverlay(){const layer=document.createElement('div');layer.className='crypt-trap-overlay';layer.setAttribute('role','status');layer.innerHTML=`<div><svg class="boil" viewBox="0 0 280 220" aria-hidden="true"><g fill="#EDE6D6" stroke="#1A1A1A" stroke-width="6" stroke-linejoin="round" stroke-linecap="round"><path d="M58 218L42 136Q36 111 46 107Q60 103 70 134L62 43Q60 28 74 28Q88 28 90 45L96 114L98 18Q100 3 114 8Q128 10 127 26L128 116L144 38Q148 23 162 28Q175 34 170 49L161 128L183 71Q190 56 202 65Q214 73 204 91L176 164Q178 194 158 218Z"/><path d="M208 218L220 147Q226 126 236 129Q248 130 244 154L259 99Q262 85 273 92L253 175L259 218Z"/></g></svg><strong>THE CRYPT GRABS BACK</strong><span>−30 seconds · back to the entrance</span></div>`;document.body.appendChild(layer);setTimeout(()=>layer.remove(),1250);}
  function stage3Preview(){
    const score=state.result?.secondsRemaining??Math.floor(timeLeft()/1000), solo=isSolo();
    return shell(`<div class="ending-shell ${solo?'solo-ending':''}"><div class="eyebrow">${solo?'SOLO VIGIL':'THE CIRCLE'} · TWO CHAPTERS COMPLETE</div><h1 class="page-title">THE CRYPT AWAITS</h1><div class="door-frame"><div class="door-glow on"></div><div class="door open"></div></div><p>The Library opens onto the stairs beneath Hollow Manor. The Crypt comes next.</p><div class="kicker">STAGE 3 · NOW PLAYABLE</div>${solo?`<div class="kicker">SOLO LIBRARY TRIAL · SEPARATE FROM TEAM SCORES</div><div class="solo-rank">${esc(state.result?.rank||'The Unbroken Witness')}</div><div class="ending-time">${clockText(score*1000)}</div>`:''}<p class="thin-note">This is an older trial result; the Crypt and finale are now playable. ${solo?'Choose new powers and replay with a new puzzle seed.':'Your circle may replay with a new puzzle seed.'}</p>${isHost()?'<button class="btn" data-action="again">↺ Enter the manor again</button>':'<p>Waiting for the host to restart…</p>'}</div>`);
  }
  function solved(){return shell(`${timerHeader()}${ghostConversation()}<div class="ending-shell"><div class="kicker">THE LOCK HAS YIELDED</div><h1 class="page-title">The Clock Awakens</h1><div class="door-frame"><div class="door-glow"></div><div class="door"></div></div><p>At the fourth chime, the lock snaps free. Across the foyer, a door groans open. A colder darkness waits beyond.</p><div class="ending-time">${clockText(timeLeft())}</div><p class="thin-note">The candle keeps burning. Continue into the Library of Whispers.</p><button class="btn" data-action="continue" disabled>Continue into the darkness →</button></div>`);}
  function preview(){return shell(`<div class="ending-shell"><div class="eyebrow">THE PASSAGE BEYOND</div><h1 class="page-title">The Library Awaits</h1><div class="door-frame"><div class="door-glow on"></div><div class="door open"></div></div><p>You have survived the Foyer. Beyond the doorway, ancient books whisper names no living soul remembers.</p><div class="kicker">STAGE 2 · NOW PLAYABLE</div><p class="thin-note">This is an older trial result. Start a new round to explore all four chapters, including the Library and Kaashi finale.</p>${isHost()?`<button class="btn" data-action="again">↺ Try the Foyer again</button>`:'<p class="thin-note">Waiting for the host to begin another round…</p>'}</div>`);}
  function lost(){const sol=state.solutions||{};return shell(`<div class="ending-shell"><div class="eyebrow">THE LAST LIGHT HAS GONE OUT</div><h1 class="page-title" style="color:#b86060">Consumed by Darkness</h1><div style="font-size:100px;margin:15px 0;color:#8a7570;filter:grayscale(1)">♱</div><p>The final candle dies. Eleanor's silence fills the manor. The doors will not open tonight.</p><div class="frame" style="text-align:left;margin:25px 0"><div class="kicker">THE FOYER · ANSWER REVEALED</div><p>Symbol order: <strong>${(sol.order||[]).join(' → ')}</strong></p><p>Clock hours: <strong>${(sol.code||[]).join(' · ')}</strong></p><p class="thin-note">A new round will generate new diary hours and a fresh code.</p></div>${isHost()?`<button class="btn" data-action="again">↺ Try again with the same party</button>`:'<p class="thin-note">Waiting for the host to start another round…</p>'}</div>`);}
  function updateLeverLive(){
    if(!state?.library)return;
    const lib=state.library;
    for(const el of document.querySelectorAll('[data-seat-id].lever-seat')){
      const held=lib.heldSeats.includes(el.dataset.seatId);
      el.classList.toggle('held',held);
      const label=el.querySelector('small');if(label)label.textContent=held?'HOLDING':'AWAITING';
      const badge=el.querySelector('.lever-presence');if(badge)badge.textContent=held?'✦':'◇';
    }
    const lever=document.querySelector('[data-lever-hold]');
    if(lever){const held=isSolo()?lib.rhythm?.held:lib.heldSeats.includes(state.me.id);
      lever.classList.toggle('held',Boolean(held));lever.setAttribute('aria-pressed',String(Boolean(held)));
      const title=lever.querySelector('strong');if(title)title.textContent=held?'KEEP HOLDING':'PRESS AND HOLD';
    }
    const holdCount=document.querySelector('[data-hold-count]');
    if(holdCount)holdCount.textContent=`${lib.heldSeats.length} of ${state.players.length} hands on brass`;
    const rhythmCount=document.querySelector('.rhythm-progress');
    if(rhythmCount&&lib.rhythm)rhythmCount.textContent=`${lib.rhythm.beatIndex||0} / 3 BEATS COMPLETED`;
    for(const beat of document.querySelectorAll('[data-beat]')){
      if(lib.rhythm)beat.classList.toggle('complete',Number(beat.dataset.beat)<lib.rhythm.beatIndex);
    }
    updateClock();
  }
  function render(){const current=(state?.phase||'landing');let content=mode==='room-reset'&&!state?resetRoom():state?(isSolo()?(current==='lobby'?soloLobby():current==='playing'&&!state.me.ack?soloRoleReveal():current==='playing'?(state.stage==='library'?library():state.stage==='crypt'?cryptStage():state.stage==='finale'?finaleStage():soloFoyer()):current==='foyer_solved'?solved():current==='library_solved'?librarySolved():current==='crypt_solved'?cryptSolved():current==='won'?finaleWin():current==='finale_reveal'?finaleStage():current==='stage4_preview'?stage4Preview():current==='stage3_preview'?stage3Preview():current==='stage2_preview'?soloPreview():current==='lost'?finaleLost():soloLobby()):(current==='lobby'?lobby():current==='playing'&&!state.me.ack?roleReveal():current==='playing'?(state.stage==='library'?library():state.stage==='crypt'?cryptStage():state.stage==='finale'?finaleStage():foyer()):current==='foyer_solved'?solved():current==='library_solved'?librarySolved():current==='crypt_solved'?cryptSolved():current==='won'?finaleWin():current==='finale_reveal'?finaleStage():current==='stage4_preview'?stage4Preview():current==='stage3_preview'?stage3Preview():current==='stage2_preview'?preview():current==='lost'?finaleLost():lobby())):(connectionState==='waking'||connectionState==='reconnecting'||connectionState==='connecting'?waking():landing());const oldDeck=document.querySelector('.character-deck');if(oldDeck)deckScroll=oldDeck.scrollLeft;app.innerHTML=content+tlcNavigationDialog();const newDeck=document.querySelector('.character-deck');if(newDeck)newDeck.scrollLeft=deckScroll;if(state?.stage==='finale' && state.finale?.enteredAt){const wait=4600-(Date.now()+serverOffset-state.finale.enteredAt);if(wait>0)setTimeout(()=>{document.querySelector('.kaashi-intro-overlay')?.remove();},wait);}if(current==='crypt_solved'){setTimeout(()=>{const b=document.querySelector('[data-action=continue-crypt]');if(b)b.disabled=false;},Math.max(10,3100-(Date.now()+serverOffset-(state?.solvedAt||Date.now()))));}if(current==='library_solved'){setTimeout(()=>{const btn=document.querySelector('[data-action=continue-library]');if(btn)btn.disabled=false;},Math.max(10,3700-(Date.now()+serverOffset-(state?.solvedAt||Date.now()))));}if(current==='foyer_solved'){setTimeout(()=>{document.querySelector('.door-frame .door')?.classList.add('open');document.querySelector('.door-frame .door-glow')?.classList.add('on');},110);setTimeout(()=>{const btn=document.querySelector('[data-action=continue]');if(btn)btn.disabled=false;},Math.max(10,2500-(Date.now()+serverOffset-(state?.solvedAt||Date.now()))));}if(state?.story?.ghost?.id==='foyer')setHoraceFace(state.story.ghost.closed?'happy':state.story.ghost.coldUntil?'sad':state.story.ghost.history?.at(-1)?.mood==='pleased'?'happy':state.story.ghost.history?.at(-1)?.mood||'nervous');updateClock();typeGhostLine();const c=document.getElementById('chat-messages');if(c)c.scrollTop=c.scrollHeight;}
  function updateClock(){let ms=timeLeft();const sc=document.querySelector('[data-select-clock]');if(sc&&state?.selection){sc.textContent=state.selection.deadlineAt===null?'45':String(Math.ceil(selectionRemaining()/1000)).padStart(2,'0');}const veil=document.querySelector('[data-veil-clue]');if(veil){const secs=Math.max(0,Math.ceil((Number(veil.dataset.expires)-(Date.now()+serverOffset))/1000));const t=veil.querySelector('[data-veil-time]');if(t)t.textContent=secs+'s';if(secs===0)veil.hidden=true;}for(const el of document.querySelectorAll('[data-timer],.candle-time'))el.textContent=clockText(ms);const maxMs=state?.timer?.durationMs || 1200000;for(const el of document.querySelectorAll('[data-progress]'))el.style.width=`${Math.max(0,Math.min(100,ms/maxMs*100))}%`;for(const el of document.querySelectorAll('.wax-shade'))el.style.height=`${Math.min(96, (1-ms/maxMs)*96)}%`;const holdProgress=document.querySelector('[data-hold-progress]');if(holdProgress&&state?.library?.holdStartedAt){holdProgress.style.width=`${Math.min(100,Math.max(0,(Date.now()+serverOffset-state.library.holdStartedAt)/30))}%`;}for(const beat of document.querySelectorAll('[data-beat]')){const idx=Number(beat.dataset.beat),rh=state?.library?.rhythm;if(rh)beat.classList.toggle('lit',rh.beatIndex===idx&&rh.beatGlowUntil>Date.now()+serverOffset);}const lensTime=document.querySelector('[data-lens-remaining]');if(lensTime&&state?.solo?.lensReadyAt)lensTime.textContent=(Math.max(0,state.solo.lensReadyAt-(Date.now()+serverOffset))/1000).toFixed(1)+'s';const flameHidden=ms<=0&&state&&state.phase!=='lobby';for(const el of document.querySelectorAll('.flame'))el.style.opacity=flameHidden?'0':'1';if(soundEnabled&&state?.phase==='playing'&&ms<120000&&!heartbeatInterval)startHeartbeat();if((!state||state.phase!=='playing'||ms>=120000)&&heartbeatInterval){clearInterval(heartbeatInterval);heartbeatInterval=null;}}
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
    try{ws=new WebSocket(websocketUrl);}
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
  function onPacket(data){if(data.type==='ROOM_RESET'){const lostCode=roomCode||codeDraft||roomCodeFromUrl();if(lostCode)sessionStorage.removeItem('tlc:seat:'+lostCode);const lostSolo=soloIdFromUrl();if(lostSolo){sessionStorage.removeItem('tlc:solo:'+lostSolo);sessionStorage.removeItem('tlc:lastSoloId');}token=null;seatId=null;roomCode=null;state=null;mode='room-reset';connectionState='idle';intentionalClose=true;if(ws)ws.close();render();return;}if(data.type==='READY'){connectionState='connected';reconnectAttempt=0;render();return;}if(data.type==='WELCOME'){roomCode=data.roomCode;token=data.token;seatId=data.seatId;if(data.roomMode==='solo'){sessionStorage.setItem('tlc:solo:'+data.roomId,JSON.stringify({token,seatId}));sessionStorage.setItem('tlc:lastSoloId',data.roomId);history.replaceState({},'',soloPath(data.roomId));}else{localStorage.setItem('tlc:lastRoom',roomCode);sessionStorage.setItem('tlc:seat:'+roomCode,JSON.stringify({token,seatId}));history.replaceState({},'',roomPath(roomCode));}connectionState='connected';reconnectAttempt=0;return;}
    if(data.type==='STATE'){if(!state||data.state.version>=state.version||data.state.room.code!==state.room.code){const prev=state?.phase;state=data.state;serverOffset=state.serverNow-Date.now();if(prev!==state.phase&&state.phase==='lobby'){dials=[1,1,1,1];libraryWordDraft='';previewCharacter='medium';deckScroll=0;}if(leverPointerHeld&&state.phase==='playing'&&state.stage==='library'&&state.library?.part==='levers'&&(!isSolo()||state.library.rhythm?.active)){updateLeverLive();}else render();}return;}
    if(data.type==='SYNC'){if(state?.timer&&data.freezeUntil!==undefined){state.timer.freezeUntil=data.freezeUntil;state.timer.frozenRemainingMs=data.frozenRemainingMs;state.timer.deadlineAt=data.deadlineAt;}if(state?.selection&&data.selectionDeadlineAt!==undefined)state.selection.deadlineAt=data.selectionDeadlineAt;if(data.serverNow){const calc=data.serverNow-Date.now();serverOffset=Math.abs(serverOffset-calc)>1800?calc:serverOffset*.85+calc*.15;}updateClock();return;}
    if(data.type==='PONG'){const mid=(Number(data.clientSentAt)+Date.now())/2;const calc=data.serverNow-mid;serverOffset=serverOffset*.5+calc*.5;return;}
    if(data.type==='ERROR'){showToast(data.message||'The manor rejects your request');if(!state){connectionState='idle';if(ws){intentionalClose=true;ws.close();}render();}return;}
    if(data.type==='REPLACED'){intentionalClose=true;showToast('This seat was opened in another browser tab.');return;}
    if(data.type==='EFFECT'){effect(data.effect);return;}
  }
  function effect(effect){if(!effect)return;if(effect.roll)diceRollOverlay(effect.roll);if(effect.tieRoll)diceRollOverlay(effect.tieRoll);switch(effect.name){case 'WRONG_ANSWER':{document.body.classList.add('shake','pulse-red');setTimeout(()=>document.body.classList.remove('shake','pulse-red'),650);playGhost();showToast('The clock rejects the code. −30 seconds.');break;}
      case 'HINT':playWhisper();showToast('Eleanor whispers. −60 seconds.');break;
      case 'FOYER_SOLVED':playChimes();showToast('The clock chimes! A door begins to open…');break;
      case 'LIBRARY_CIPHER_SOLVED':playWhisper();showToast('The word is bound. Gather around the levers.');break;
      case 'WRONG_LIBRARY_WORD':document.body.classList.add('shake','pulse-red');setTimeout(()=>document.body.classList.remove('shake','pulse-red'),650);playGhost();showToast('The library rejects the word. −30 seconds.');break;
      case 'LIBRARY_SOLVED':playDrumHit();playChimes();showToast('THE SHELF YIELDS — the passage is open!');break;
      case 'CRYPT_ENTERED':showToast('The Crypt of the Hollows opens. Follow Wren, but mind the tiles.');break;
      case 'CRYPT_TRAP':trapHandsOverlay();playGhost();showToast('Skeletal hands! −30 seconds · back to start.');break;
      case 'CRYPT_SURE_STEP':playChime();showToast('Sure Step catches Wren over a trap!');break;
      case 'CRYPT_SOLVED':playDrumHit();playChimes();showToast('SOMETHING WAITS BEYOND.');break;
      case 'FINALE_ENTERED':playKaashiDrums();playChimes();showToast('BENEATH KAASHI · THE CAVE OF THE SEVERED FLAME');break;
      case 'STREAMS_RESTORED':playDrumHit();playChimes();showToast('THREE STREAMS RESTORED · THE OFFERING AWAITS');break;
      case 'OFFERING_SEALED':playChime();break;
      case 'OFFERINGS_REVEALED':playDrumHit();showToast('The Goddess weighs every offering.');break;
      case 'OFFERINGS_RETRY':playGhost();showToast('The shrine waits. −2 minutes · offer again together.');break;
      case 'FINALE_WON':playDrumHit();playChimes();showToast('THE DAWN RETURNS.');break;
      case 'LEVERS_RESET':showToast('A hand slipped. The three-second hold resets.');break;
      case 'RHYTHM_BEAT':playChime();break;
      case 'RHYTHM_MISSED':playGhost();showToast('The cadence breaks. Try the ritual again.');break;
      case 'TIME_EXPIRED':playGhost();showToast('The last flame has died.');break;
      case 'GAME_STARTED':playChime();break;
      case 'CHARACTER_LOCKED':castOverlay(effect.character,`${effect.by} LOCKED IN`,effect.role);break;
      case 'ABILITY_CAST':castOverlay(effect.character,effect.ability, effect.role);showToast(`${effect.by} cast ${effect.ability}!`);break;
      case 'WRONG_SHIELDED':castOverlay('CROWE','SECOND TURN · NO TIME LOST','locksmith');playChime();break;
      case 'GHOST_REPLY':playWhisper();break;
      case 'GHOST_RETURNED':showToast('The ghost returns, just a little grumpier.');break;
      case 'ADVANTAGE_GRANTED':showToast('Advantage granted. The next check rolls twice.');break;
      case 'CROSSROADS_RESOLVED':showToast('The party has made its choice.');break;
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
  function playKaashiDrums(){[0,260,480,690,870,1060,1320].forEach((delay,i)=>setTimeout(()=>{tone(90-i*4,.38,'triangle',.05+i*.009);tone(55,.28,'sine',.05+i*.007);},delay));}
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

    if(a==='tlc-back'){
      if(!state){
        mode='landing';
        render();
      }else{
        tlcNavOpen=true;
        render();
      }
      return;
    }
    if(a==='tlc-back-close'){
      tlcNavOpen=false;
      render();
      return;
    }
    if(a==='tlc-back-home'){
      if(!window.confirm(
        'Return to home? The game and candle timer will continue.'
      )) return;
      tlcNavOpen=false;
      leave();
      return;
    }

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
    else if(a==='ghost-reply')send('GHOST_REPLY',{optionId:el.dataset.value});
    else if(a==='help-speaker')send('HELP_SPEAKER');
    else if(a==='steady-breath')send('STEADY_BREATH');
    else if(a==='crossroads-vote')send('VOTE_CROSSROADS',{choice:el.dataset.value});
    else if(a==='hint'){if(confirm('Spend 60 seconds of the shared candle to reveal the next hint to everyone?'))send('REQUEST_HINT');}
    else if(a==='continue')send('CONTINUE');
    else if(a==='continue-library')send('CONTINUE_LIBRARY');
    else if(a==='continue-crypt')send('CONTINUE_CRYPT');
    else if(a==='crypt-move')send('CRYPT_MOVE',{direction:el.dataset.value});
    else if(a==='stream-turn')send('ROTATE_STREAM_TILE',{section:Number(el.dataset.section),tile:Number(el.dataset.index)});
    else if(a==='offer')send('SEAL_OFFERING',{kind:el.dataset.kind,role:el.dataset.role||null});
    else if(a==='rhythm-switch')send('SWITCH_LENS',{role:'locksmith'});
    else if(a==='rhythm-tap')send('SOLO_RHYTHM_TAP');
    else if(a==='again')send('TRY_AGAIN');
    else if(a==='chat-toggle'){chatCollapsed=!chatCollapsed;render();}
  });
  document.addEventListener('submit',e=>{if(e.target.id==='entry-form'){e.preventDefault();const data=new FormData(e.target);nameDraft=String(data.get('name')||'').trim();if(!nameDraft){showToast('Enter your name.');return;}if(mode==='create'){capacityDraft=Number(data.get('capacity'));connect('CREATE_ROOM',{name:nameDraft,capacity:capacityDraft});}else{codeDraft=String(data.get('code')||'').toUpperCase().trim();if(!/^[A-Z]{4}$/.test(codeDraft)){showToast('Enter a four-letter room code.');return;}const existing=savedToken(codeDraft);if(existing){token=existing;roomCode=codeDraft;connect('RESUME_SEAT',{code:codeDraft,token:existing});}else connect('JOIN_ROOM',{code:codeDraft,name:nameDraft});}}
    else if(e.target.id==='library-word-form'){e.preventDefault();send('SUBMIT_LIBRARY_WORD',{word:libraryWordDraft.toUpperCase()});}
    else if(e.target.id==='chat-form'){e.preventDefault();const field=e.target.elements.text;const text=field?.value.trim();if(text){send('SEND_CHAT',{text});field.value='';}}
  });
  document.addEventListener('input',e=>{if(e.target.id==='name')nameDraft=e.target.value;if(e.target.id==='code')codeDraft=e.target.value.toUpperCase().replace(/[^A-Z]/g,'').slice(0,4);if(e.target.id==='capacity')capacityDraft=Number(e.target.value);if(e.target.id==='library-word')libraryWordDraft=e.target.value.toUpperCase().replace(/[^A-Z]/g,'').slice(0,5);});
  // Keyboard arrows are an accessible alternative to the large touch buttons.
  document.addEventListener('keydown',e=>{if(state?.phase!=='playing'||state?.stage!=='crypt'||!state.crypt?.canMove||e.repeat)return;if(['INPUT','TEXTAREA','SELECT'].includes(document.activeElement?.tagName))return;const d={ArrowUp:'up',ArrowDown:'down',ArrowLeft:'left',ArrowRight:'right'}[e.key];if(d){e.preventDefault();send('CRYPT_MOVE',{direction:d});}});
  // Pointer events work on touch and mouse. Keyboard holding is supported as well.
  // Listen for release on window because a server STATE may replace the button while held.
  document.addEventListener('pointerdown',e=>{
    const button=e.target.closest?.('[data-lever-hold]');
    if(!button||button.disabled||leverPointerHeld)return;
    e.preventDefault();leverPointerHeld=true;
    send(button.dataset.leverHold==='solo'?'SOLO_LEVER_DOWN':'LEVER_DOWN');
  });
  function releaseLever(){
    if(!leverPointerHeld)return;
    leverPointerHeld=false;
    if(state?.phase!=='playing'||state?.stage!=='library'||state?.library?.part!=='levers')return;
    send(isSolo()?'SOLO_LEVER_UP':'LEVER_UP');
  }
  window.addEventListener('pointerup',releaseLever);
  window.addEventListener('pointercancel',releaseLever);
  document.addEventListener('keydown',e=>{
    const button=e.target.closest?.('[data-lever-hold]');
    if(!button||button.disabled||leverPointerHeld||![' ','Enter'].includes(e.key))return;
    e.preventDefault();leverPointerHeld=true;
    send(button.dataset.leverHold==='solo'?'SOLO_LEVER_DOWN':'LEVER_DOWN');
  });
  window.addEventListener('keyup',e=>{if([' ','Enter'].includes(e.key))releaseLever();});
  // Approved style-preview.html: exactly three hand-drawn animation frames, 140 ms each.
  if(typeof window.matchMedia==='function' && !window.matchMedia('(prefers-reduced-motion: reduce)').matches){
    let frame=0;const frames=[3,17,42];
    setInterval(()=>{const t=document.getElementById('turb');if(t)t.setAttribute('seed',String(frames[frame=(frame+1)%3]));},140);
  }
  const urlCode=roomCodeFromUrl();
  const urlSolo=soloIdFromUrl();
  setInterval(()=>{updateClock();if(ws?.readyState===1&&Date.now()-lastPing>=25000){lastPing=Date.now();ws.send(JSON.stringify({type:'PING',clientSentAt:lastPing}));}},250);
  if(urlSolo){if(savedSoloToken(urlSolo))returnSolo(urlSolo);else{mode='landing';connect('HELLO');showToast('This private solo chamber belongs to another browser session.');}}
  else if(urlCode){codeDraft=urlCode;if(savedToken(urlCode))returnSeat(urlCode);else{mode='join';connect('HELLO');}}
  else connect('HELLO');
})();
