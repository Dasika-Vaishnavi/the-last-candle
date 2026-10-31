/* Finale HTML contract, with a simulated authoritative server STATE. */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
const stop=/  if\(urlSolo\)\{[\s\S]*?  else connect\('HELLO'\);/;
assert.match(source,stop);
const roles=['medium','archivist','lantern','locksmith','walker'];
function fixture(solo=false,part='streams',phase='playing'){
 const now=Date.now();return {
 phase,stage:'finale',round:1,version:10,serverNow:now,
 room:{code:solo?null:'RUNE',id:'a'.repeat(32),hostId:'a',capacity:solo?1:2,mode:solo?'solo':'multiplayer'},
 players:solo?[{id:'a',name:'Wanderer',connected:true,roles,primaryRole:null,ready:true,ack:true}]:[{id:'a',name:'Ada',connected:true,roles:['medium','lantern','walker'],primaryRole:'medium',ready:true,ack:true},{id:'b',name:'Bram',connected:true,roles:['archivist','locksmith'],primaryRole:'archivist',ready:true,ack:true}],
 me:{id:'a',name:'Ada',roles:solo?roles:['medium','lantern','walker'],primaryRole:solo?null:'medium',ack:true},
 solo:solo?{activeLens:'medium',equippedAbilities:['medium','archivist'],targetLens:null,lensReadyAt:null}:null,
 timer:{durationMs:solo?1500000:1200000,deadlineAt:now+400000,frozenRemainingMs:null,freezeUntil:null},
 selection:{deadlineAt:null},abilities:{used:Object.fromEntries(roles.map(r=>[r,false])),secondTurnArmed:false},
 chat:[],hints:[],hintLevel:0,clues:{},
 story:{wick:{text:'The manor falls away. You stand beneath Kaashi.',at:now},ghost:null,flags:{items:[],crits:0,fumbles:0,votesTaken:0},choices:[]},
 finale:{part,enteredAt:now-6500,sections:[0,1,2].map(i=>({id:i,connected:false,owned:solo?i===0:i!==1,tiles:solo?i===0?tiles():undefined:i!==1?tiles():undefined})),rotations:2,offeredSeats:[],myOffer:null,canOfferAbilities:['medium','lantern'],threshold:solo?1:2,offerRound:1,reveal:part==='reveal'?{accepted:true,total:2,threshold:2,offers:[{seatId:'a',name:'Ada',kind:'ability',role:'medium'},{seatId:'b',name:'Bram',kind:'candle',role:null}]}:null},
 result:phase==='won'?{rank:'Dawnkeeper',secondsRemaining:400,leaderboard:solo?'solo':'multiplayer',players:[{name:'Ada',characters:['VESPER','WREN']}],abilitiesUsed:['Veil Sight'],funStat:{label:'Crypt traps shaken off',value:2},storyFlags:{crits:1,fumbles:0,votesTaken:2},eleanor:'The dawn is warm.'}:null,
 solutions:{order:['✶','☾','❦','⚱'],code:[1,2,3,4]},librarySolution:{word:'RAVEN'},cryptSolution:{route:[[5,0],[4,0]],traps:[[3,1]]},finaleSolution:[{section:0,route:[[2,1],[1,1],[0,1]]}],
 };
}
function tiles(){return [{row:2,col:1,ports:['S','N'],index:0},{row:1,col:1,ports:['N','E'],index:1},{row:1,col:2,ports:['W','N'],index:2},{row:0,col:2,ports:['S','W'],index:3},{row:0,col:1,ports:['E','N'],index:4}];}
function render(st){const app={innerHTML:''},toast={classList:{add(){},remove(){}},textContent:''};
 const doc={body:{classList:{add(){},remove(){}}},getElementById(id){return id==='app'?app:toast;},querySelector(){return null},querySelectorAll(){return[]},addEventListener(){}};
 const c={window:{innerWidth:375,addEventListener(){},matchMedia(){return {matches:true}}},document:doc,location:{pathname:'/',origin:'https://test.example'},history:{replaceState(){}},localStorage:{getItem(){return null},setItem(){}},sessionStorage:{getItem(){return null},setItem(){}},WebSocket:{OPEN:1},URLSearchParams,setInterval(){},clearInterval(){},setTimeout(){},clearTimeout(){},console,Date,Math,Intl};
 vm.runInNewContext(source.replace(stop,`state=${JSON.stringify(st)};connectionState='connected';render();`),c,{timeout:4000});return app.innerHTML;}
const stage=render(fixture());
assert.match(stage,/BENEATH KAASHI/);assert.match(stage,/CAVE OF THE SEVERED FLAME/);
assert.match(stage,/GODDESS CHINNAMASTA/);assert.match(stage,/aria-label=".*Goddess Chinnamasta/);
assert.equal((stage.match(/data-action="stream-turn"/g)||[]).length,10);
assert.match(stage,/Another soul holds this part/);
assert.match(stage,/theme-kaashi/);
const solo=render(fixture(true));
assert.equal((solo.match(/data-action="stream-turn"/g)||[]).length,5);
assert.match(solo,/Switch Lenses to turn each section/);
assert.equal((solo.match(/class="lens-portrait /g)||[]).length,5);
const offering=render(fixture(false,'offering'));
assert.match(offering,/THE OFFERING/);assert.match(offering,/data-action="offer" data-kind="nothing"/);
assert.match(offering,/data-kind="candle"/);assert.match(offering,/60 seconds of candle/);
assert.match(offering,/two minutes/i);
const sealed=fixture(false,'offering');sealed.finale.offeredSeats=['a'];sealed.finale.myOffer={kind:'nothing'};
const hidden=render(sealed);
assert.match(hidden,/YOUR OFFERING IS SEALED/);assert.doesNotMatch(hidden,/data-action="offer"/);
assert.doesNotMatch(hidden,/Kept everything/);
const revealed=fixture(false,'reveal','finale_reveal');const result=render(revealed);
assert.match(result,/THE SHRINE WEIGHS/);assert.match(result,/Gave 60 seconds/);
const win=render(fixture(false,'complete','won'));
assert.match(win,/THE LAST CANDLE/);assert.match(win,/DAWN AT HOLLOW MANOR/);assert.match(win,/data-action="again"/);
const loss=render(fixture(false,'streams','lost'));
assert.match(loss,/THE CANDLE IS LOST/);assert.match(loss,/CRYPT · SAFE ROUTE/);assert.match(loss,/KAASHI · THREE STREAMS/);
const css=fs.readFileSync(path.join(__dirname,'../static/styles.css'),'utf8');
assert.match(css,/\.theme-kaashi/);assert.match(css,/\.stream-grid/);assert.match(css,/@media\(prefers-reduced-motion:reduce\)/);
assert.equal(source,fs.readFileSync(path.join(__dirname,'../sites-frontend/app.js'),'utf8'));
console.log('Stage 4 UI checks passed: split streams, solo Lens, secret offers, reveal, win, loss, Sites parity.');
if(process.env.FINALE_EXPORT_LAYOUT){
 const index=fs.readFileSync(path.join(__dirname,'../static/index.html'),'utf8');
 const filter=index.match(/<svg xmlns="http:\/\/www.w3.org\/2000\/svg"[^]*?<\/svg>/)?.[0]||'';
 const style=fs.readFileSync(path.join(__dirname,'../static/styles.css'),'utf8');
 const markup=render(fixture());
 fs.writeFileSync('/mnt/data/finale-layout-check.html',`<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link href="https://fonts.googleapis.com/css2?family=Patrick+Hand&family=Nunito:wght@600;800&display=swap" rel="stylesheet"><style>${style}</style></head><body>${filter}<div id="app">${markup}</div></body></html>`);
}
