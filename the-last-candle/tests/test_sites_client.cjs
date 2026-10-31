/* Site-origin navigation and backend WebSocket URL contract (no browser required). */
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname,'../sites-frontend/app.js'),'utf8');
const siteIndex = fs.readFileSync(path.join(__dirname,'../sites-frontend/index.html'),'utf8');
assert.ok(siteIndex.includes('window.TLC_SITES_FRONTEND = true;'));
assert.ok(siteIndex.includes('wss://the-last-candle.onrender.com/ws'));
assert.ok(siteIndex.includes('./styles.css'));
const exposed = source.replace(/\}\)\(\);\s*$/, 'globalThis.__bridgeTest = { linkToRoom, roomPath, soloPath, roomCodeFromUrl, soloIdFromUrl, websocketUrl };\n})();');
class FakeWS {
  static OPEN = 1;
  static CONNECTING = 0;
  constructor(url) { this.url=url; this.readyState=0; FakeWS.last=this; this.outbound=[]; }
  send(text) { this.outbound.push(JSON.parse(text)); }
  close() { this.readyState=3; }
  open() { this.readyState=1; this.onopen?.(); }
  receive(data) { this.onmessage?.({data:JSON.stringify(data)}); }
}
function setup(search='?room=ABCD') {
  const app={innerHTML:''},toast={textContent:'',classList:{add(){},remove(){}}};
  const callbackMap={};let redirected='';
  const context={
    URLSearchParams,
    location:{protocol:'https:',host:'testsite.openai.chatgpt.site',origin:'https://testsite.openai.chatgpt.site',pathname:'/',search},
    history:{replaceState(_a,_b,url){redirected=url;}},
    window:{TLC_SITES_FRONTEND:true,TLC_WEBSOCKET_URL:'wss://the-last-candle.onrender.com/ws',innerWidth:390,addEventListener(){}},
    document:{getElementById(id){return id==='app'?app:toast;},querySelectorAll(){return[];},querySelector(){return null;},addEventListener(name,fn){callbackMap[name]=fn;}},
    localStorage:{getItem(){return null;},setItem(){}},sessionStorage:{getItem(){return null;},setItem(){}},
    WebSocket:FakeWS,console,Date,Math,Intl,setTimeout(){},clearTimeout(){},setInterval(){},clearInterval(){},
  };
  vm.runInNewContext(exposed,context,{timeout:1000});
  return {context,app,socket:FakeWS.last,bridge:context.__bridgeTest,get redirect(){return redirected;}};
}
const invite=setup('?room=ABCD');
assert.equal(invite.socket.url,'wss://the-last-candle.onrender.com/ws');
assert.equal(invite.bridge.roomCodeFromUrl(),'ABCD');
assert.equal(invite.bridge.linkToRoom('WXYZ'),'https://testsite.openai.chatgpt.site/?room=WXYZ');
assert.ok(invite.app.innerHTML.includes('Waking the spirits'));
invite.socket.open();
assert.equal(invite.socket.outbound[0].type,'HELLO');
invite.socket.receive({type:'WELCOME',roomCode:'ABCD',roomId:'r-123',roomMode:'multiplayer',seatId:'seat-1',token:'secret'});
assert.equal(invite.redirect,'/?room=ABCD');
const solo=setup('?solo=1234567890abcdef1234567890abcdef');
assert.equal(solo.bridge.soloIdFromUrl(),'1234567890abcdef1234567890abcdef');
assert.equal(solo.bridge.soloPath('1234567890abcdef1234567890abcdef'),'/?solo=1234567890abcdef1234567890abcdef');
console.log('Sites frontend bridge tests passed (WebSocket URL, cold start, invite/reconnect routes).');
