/* Story UI smoke test with authoritative state supplied as the server would send it. */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
const end=/  if\(urlSolo\)\{[\s\S]*?  else connect\('HELLO'\);/;
assert.match(source,end);
const roles=['medium','archivist','lantern','locksmith','walker'];
function mock(mode='multiplayer',seat='a'){
 const solo=mode==='solo';
 return {room:{code:solo?null:'RUNE',id:'f'.repeat(32),mode,hostId:'a',capacity:solo?1:2},
  phase:'playing',stage:'foyer',round:1,version:3,serverNow:Date.now(),
  me:{id:seat,name:solo?'Wanderer':seat==='a'?'Ada':'Bram',roles:solo?roles:seat==='a'?['medium','lantern','walker']:['archivist','locksmith'],primaryRole:solo?null:seat==='a'?'medium':'archivist',ack:true},
  players:solo?[{id:'a',name:'Wanderer',connected:true,roles,primaryRole:null}]:[
    {id:'a',name:'Ada',connected:true,roles:['medium','lantern','walker'],primaryRole:'medium'},
    {id:'b',name:'Bram',connected:true,roles:['archivist','locksmith'],primaryRole:'archivist'}],
  solo:solo?{equippedAbilities:['medium','locksmith'],activeLens:'medium',targetLens:null,lensReadyAt:null}:null,
  timer:{durationMs:solo?1500000:1200000,deadlineAt:Date.now()+1100000,frozenRemainingMs:null,freezeUntil:null},
  selection:{deadlineAt:null},hints:[],hintLevel:0,wrongAttempts:0,
  clues:{medium:{portraits:['☾','✶','⚱','❦']},lantern:{order:['✶','☾','❦','⚱']},archivist:{entries:[]},locksmith:{dials:4},walker:{message:'The crypt awaits'}},
  abilities:{used:Object.fromEntries(roles.map(x=>[x,false])),secondTurnArmed:false},chat:[],
  story:{wick:{text:'You open the door. It opens back. Rude.',at:Date.now()},ghost:{id:'foyer',name:'Horace Tock',job:'clockmaker · deceased 1871',warmth:2,coldUntil:null,exchange:1,maxExchanges:4,speakerId:'a',speakerName:'Ada',history:[{speaker:'Bram',text:'I hope you are well.',ghostText:'I am permanently on time.',mood:'pleased'}],fragments:['The moon ☾ saw the first hour'],finished:false,closed:false,goodbye:null,options:[{id:'foyer:1:medium:0',label:'✦ Whisper: compliments',stat:'CHARM',dc:12,tone:'kind'}, {id:'foyer:1:medium:1',label:'✦ Listen: ask about clock',stat:null,dc:null,tone:'curious'}],votes:{},crossroads:null,rollsUsed:1,advantage:false},choices:[],stats:{medium:{CHARM:2,WITS:0,NERVE:1}},flags:{crits:0,fumbles:0,votesTaken:0,items:[]}}
 };
}
function render(state){let app={innerHTML:''},toast={classList:{add(){},remove(){}},textContent:''};
 const doc={body:{classList:{add(){},remove(){}}},getElementById(id){return id==='app'?app:id==='toast'?toast:null;},querySelector(){return null},querySelectorAll(){return []},addEventListener(){}};
 let context={window:{innerWidth:390,addEventListener(){},matchMedia(){return {matches:true}}},document:doc,location:{pathname:'/',origin:'http://localhost:8080'},history:{replaceState(){}},localStorage:{getItem(){return null},setItem(){}},sessionStorage:{getItem(){return null},setItem(){}},WebSocket:{OPEN:1},URLSearchParams,setInterval(){},clearInterval(){},setTimeout(){},clearTimeout(){},console,Date,Math,Intl};
 vm.runInNewContext(source.replace(end,`state=${JSON.stringify(state)};connectionState='connected';render();`),context,{timeout:2500});return app.innerHTML;}
let html=render(mock());
assert.ok(html.includes('WICK · THE NARRATOR'));
assert.ok(html.includes('HORACE')||html.includes('Horace Tock'));
assert.ok(html.includes('WARMTH 2/3'));
assert.ok(html.includes('CHARM 12'));
assert.ok(html.includes('data-action="ghost-reply"'));
assert.ok(html.includes('SHARED CLUE FRAGMENTS'));
assert.ok(html.includes('HELP')||html.includes('Help'));
let notSpeaker=render(mock('multiplayer','b'));
assert.ok(notSpeaker.includes('Bram')&&notSpeaker.includes('Ada IS SPEAKING'));
assert.ok(notSpeaker.includes('disabled'));
let solo=render(mock('solo'));
assert.ok(solo.includes('Steady your breath'));
assert.ok(solo.includes('data-action="solo-lens"'));
let post=mock();post.story.ghost.finished=true;post.story.ghost.options=[];post.story.choices=[{id:'watch',label:'Pry the pocket watch',stat:'WITS',dc:13},{id:'leave',label:'Leave it',stat:null,dc:null}];
assert.ok(render(post).includes('VOTE TO DECIDE'));
console.log('Ghost + Wick RPG UI smoke tests passed for speaker, non-speaker, solo and crossroads.');
