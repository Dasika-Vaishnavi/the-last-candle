/* Static UI contract: Stage 3 must render from sanitized server states only. */
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),assert=require('node:assert/strict');
const src=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
const stop=/  if\(urlSolo\)\{[\s\S]*?  else connect\('HELLO'\);/;
assert.match(src,stop);
function makeState(solo=false,role='walker',phase='playing'){
  const roles=['medium','archivist','lantern','locksmith','walker'],now=Date.now();
  return {phase,stage:'crypt',round:1,version:5,serverNow:now,
    room:{code:solo?null:'RUNE',mode:solo?'solo':'multiplayer',id:'f'.repeat(32),hostId:'w',capacity:solo?1:2},
    players:solo?[{id:'w',name:'Wanderer',connected:true,primaryRole:null,roles,ack:true}]:[
      {id:'w',name:'Wren',connected:true,primaryRole:'walker',roles:['walker'],ack:true},
      {id:'g',name:'Guide',connected:true,primaryRole:'medium',roles:['medium','archivist','lantern','locksmith'],ack:true}],
    me:{id:solo?'w':role==='walker'?'w':'g',name:role==='walker'?'Wren':'Guide',roles:solo?roles:role==='walker'?['walker']:['medium','archivist','lantern','locksmith'],primaryRole:solo?null:role==='walker'?'walker':'medium',ack:true},
    solo:solo?{activeLens:role,targetLens:null,lensReadyAt:null,equippedAbilities:['walker','medium']}:null,
    timer:{durationMs:solo?1500000:1200000,deadlineAt:now+1000000,totalPenaltyMs:30000,freezeUntil:null,frozenRemainingMs:null},
    selection:{deadlineAt:null},abilities:{used:Object.fromEntries(roles.map(r=>[r,false])),secondTurnArmed:false},
    crypt:{size:6,position:[4,0],start:[5,0],visible:[[3,0],[4,0],[4,1],[5,0]],knownTraps:role==='walker'?[]:[[1,1],[2,4]],safeTile:role==='archivist'?[3,2]:null,canMove:role==='walker',canGuide:role!=='walker',exitVisible:false,steps:1,trapHits:0,sureStepArmed:false,sureStepUsed:false},
    hints:['Wren must be guided'],hintLevel:1,chat:[],solvedAt:now-4000,clues:role==='walker'?{walker:{message:'Darkness'}}:{medium:{message:'Right half'}},
    story:{wick:{text:'You descend into the Crypt. Your footsteps sound expensive.',at:now},
      ghost:{id:'crypt',name:'Sir Reginald Rattle',job:'a knight',warmth:1,coldUntil:null,exchange:0,maxExchanges:1,speakerId:'w',speakerName:'Wren',history:[],fragments:[],finished:false,closed:phase==='crypt_solved',goodbye:'You found the light.',options:[],votes:{},crossroads:null,rollsUsed:0,advantage:false},
      choices:[],stats:{},flags:{items:[],shortCut:false,crits:0,fumbles:0,votesTaken:0,diceRolls:0}}
  };
}
function render(s){
  const app={innerHTML:''},toast={classList:{add(){},remove(){}},textContent:''};
  const doc={getElementById(n){return n==='app'?app:toast},querySelector(){return null},querySelectorAll(){return[]},addEventListener(){},body:{classList:{add(){},remove(){}}}};
  const context={window:{innerWidth:375,addEventListener(){},matchMedia(){return {matches:true}}},document:doc,location:{pathname:'/',origin:'https://example.com'},history:{replaceState(){}},localStorage:{getItem(){return null},setItem(){}},sessionStorage:{getItem(){return null},setItem(){}},WebSocket:{OPEN:1},URLSearchParams,setInterval(){},clearInterval(){},setTimeout(){},clearTimeout(){},console,Date,Math,Intl};
  vm.runInNewContext(src.replace(stop,`state=${JSON.stringify(s)};connectionState='connected';render();`),context,{timeout:2500});
  return app.innerHTML;
}
const wren=render(makeState());
assert.ok(wren.includes('THE CRYPT OF THE HOLLOWS'));
assert.equal((wren.match(/role="gridcell"/g)||[]).length,36);
assert.equal((wren.match(/data-action="crypt-move"/g)||[]).length,4);
assert.ok(wren.includes('WHAT YOU CAN SEE')&&wren.includes('WHAT YOU MUST DO'));
assert.ok(wren.includes('WREN · You see adjacent outlines only'));
assert.ok(!wren.includes('R2 C2'));
const guide=render(makeState(false,'medium'));
assert.ok(guide.includes('R2 C2')&&guide.includes('R3 C5'));
assert.ok(guide.includes('THE GUIDE'));
assert.match(guide,/Move north" disabled/);
const solo=render(makeState(true,'medium'));
assert.ok(solo.includes('Switch to Wren'));
assert.equal((solo.match(/class="lens-portrait /g)||[]).length,5);
const solved=render(makeState(true,'walker','crypt_solved'));
assert.ok(solved.includes('SOMETHING WAITS BEYOND.'));
assert.ok(solved.includes('data-action="continue-crypt"'));
const next=render(makeState(true,'walker','stage4_preview'));
assert.ok(next.includes('FINALE NOW PLAYABLE'));
assert.match(fs.readFileSync(path.join(__dirname,'../static/styles.css'),'utf8'),/\.crypt-grid/);
assert.match(fs.readFileSync(path.join(__dirname,'../sites-frontend/app.js'),'utf8'),/function cryptStage\(\)/);
console.log('Crypt UI contract passed: 36 tiles, asymmetric fog, movement, solo Lens, seal reveal, Sites parity.');
