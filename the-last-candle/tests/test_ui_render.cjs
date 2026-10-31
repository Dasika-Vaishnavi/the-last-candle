/* Render-smoke tests of the real client logic without a browser or network. */
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync(require('node:path').join(__dirname,'../static/app.js'),'utf8');
const end = /  if\(urlSolo\)\{[\s\S]*?  else connect\('HELLO'\);/;
assert.match(source,end);
const roles=['medium','archivist','lantern','locksmith','walker'];
const mkState=(phase)=>({
  phase,round:1,version:4,room:{code:'RUNE',mode:'multiplayer',capacity:5,hostId:'a'},
  players:[{id:'a',name:'Ada',connected:true,primaryRole:'medium',roles:['medium','lantern','walker'],ready:false,ack:false,lockedAt:123},
  {id:'b',name:'Bram',connected:true,primaryRole:'archivist',roles:['archivist','locksmith'],ready:false,ack:false,lockedAt:123}],
  me:{id:'a',name:'Ada',primaryRole:'medium',roles:['medium','lantern','walker'],ack:phase==='playing',lockedAt:123},
  selection:{startedAt:Date.now(),deadlineAt:Date.now()+45000,durationMs:45000},
  timer:{startedAt:Date.now(),deadlineAt:Date.now()+1200000,frozenRemainingMs:null,freezeUntil:null,totalPenaltyMs:0},
  abilities:{used:Object.fromEntries(roles.map(r=>[r,false])),secondTurnArmed:false},
  veilClue:null,hints:[],hintLevel:0,chat:[],serverNow:Date.now(),solvedAt:null,wrongAttempts:0,
  clues:{medium:{portraits:['☾','✶','⚱','❦']},lantern:{order:['✶','☾','❦','⚱']},walker:{message:'Quiet'}}
});
for(const phase of ['lobby','playing']){
  const app={innerHTML:''}, toast={textContent:'',classList:{add(){},remove(){}}};
  const doc={getElementById(id){return id==='app'?app:toast;},querySelector(){return null;},querySelectorAll(){return[];},addEventListener(){}};
  const context={document:doc,window:{innerWidth:390},location:{pathname:'/',origin:'http://localhost:8080'},history:{replaceState(){}},localStorage:{getItem(){return null},setItem(){}},sessionStorage:{getItem(){return null},setItem(){}},console,setTimeout(){},setInterval(){},clearTimeout(){},Date,Math,Intl,WebSocket:{OPEN:1}};
  const injection='  state='+JSON.stringify(mkState(phase))+';connectionState="connected";render();';
  vm.runInNewContext(source.replace(end,injection),context,{timeout:1000});
  assert.ok(app.innerHTML.includes('THE LAST CANDLE'));
  if(phase==='lobby'){
    assert.equal((app.innerHTML.match(/class="character-card /g)||[]).length,5);
    assert.ok(app.innerHTML.includes('TEAM COMPOSITION'));
    assert.ok(app.innerHTML.includes('YOU ALSO CARRY')||app.innerHTML.includes('You also carry'));
    assert.ok(app.innerHTML.includes('Veil Sight'));
    assert.ok(app.innerHTML.includes('LOCKED'));
  } else {
    assert.ok(app.innerHTML.includes('YOUR ONCE-PER-GAME POWERS'));
    assert.ok(app.innerHTML.includes('Steady Flame'));
    assert.ok(app.innerHTML.includes('Stage 3'));
  }
}

const soloState=(phase, active='medium', target=null)=>({
  phase, round:1,version:6,room:{code:null,id:'f'.repeat(32),mode:'solo',capacity:1,hostId:'a'},
  me:{id:'a',name:'The Wanderer',primaryRole:null,roles:[...roles],ack:phase==='playing'},
  players:[{id:'a',name:'The Wanderer',connected:true,primaryRole:null,roles:[...roles],ready:false,ack:true}],
  solo:{equippedAbilities:['medium','locksmith'],activeLens:target?null:active,targetLens:target,lensReadyAt:Date.now()+2000,switchDurationMs:2000},
  selection:{startedAt:null,deadlineAt:null,durationMs:45000},
  timer:{startedAt:Date.now(),deadlineAt:Date.now()+1500000,durationMs:1500000,frozenRemainingMs:null,freezeUntil:null,totalPenaltyMs:0},
  abilities:{used:Object.fromEntries(roles.map(r=>[r,false])),secondTurnArmed:false},
  veilClue:null,hints:[],hintLevel:0,chat:[],serverNow:Date.now(),solvedAt:null,wrongAttempts:0,
  clues:target?{}:{[active]: active==='medium'?{portraits:['☾','✶','⚱','❦']}: {entries:[]}},
  result:phase==='stage2_preview'?{outcome:'trial_complete',secondsRemaining:1300,rank:'Lone Lightkeeper',leaderboard:'solo'}:null
});
for(const [phase,active,target] of [['lobby','medium',null],['playing','medium',null],['playing',null,'archivist'],['stage2_preview','medium',null]]){
  const app={innerHTML:''},toast={textContent:'',classList:{add(){},remove(){}}};
  const doc={getElementById(id){return id==='app'?app:toast;},querySelector(){return null;},querySelectorAll(){return[];},addEventListener(){}};
  const context={document:doc,window:{innerWidth:390},location:{pathname:'/',origin:'http://localhost:8080'},history:{replaceState(){}},localStorage:{getItem(){return null},setItem(){}},sessionStorage:{getItem(){return null},setItem(){}},console,setTimeout(){},setInterval(){},clearTimeout(){},Date,Math,Intl,WebSocket:{OPEN:1}};
  vm.runInNewContext(source.replace(end,'  state='+JSON.stringify(soloState(phase,active,target))+';connectionState="connected";render();'),context,{timeout:1000});
  assert.ok(app.innerHTML.includes('SOLO RITUAL'));
  assert.ok(!app.innerHTML.includes('RUNE'));  // No invite codes in the solo interface.
  if(phase==='lobby'){
    assert.equal((app.innerHTML.match(/class="solo-pick /g)||[]).length,5);
    assert.ok(app.innerHTML.includes('Choose two powers'));
  } else if(phase==='playing') {
    assert.equal((app.innerHTML.match(/class="lens-portrait /g)||[]).length,5);
    assert.ok(app.innerHTML.includes('25:00'));
    if(target){
      assert.ok(app.innerHTML.includes('Through the smoke'));
      assert.ok(!app.innerHTML.includes('four portraits beneath luminous'));
    } else assert.ok(app.innerHTML.includes('The Medium'));
  } else {
    assert.ok(app.innerHTML.includes('Lone Lightkeeper'));
    assert.ok(app.innerHTML.includes('SOLO FOYER RANK'));
  }
}
console.log('UI rendering smoke tests passed (multiplayer lobby/foyer + solo prep/lens/smoke/rank).');
