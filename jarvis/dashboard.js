/* Local JARVIS dashboard controller. No third-party services. */
'use strict';
const $=id=>document.getElementById(id);
let token='',controller=null,voiceEnabled=false,recognition=null;
const avatar=window.JarvisAvatar||{setMode() {},setQuality() {}};
const formatGB=n=>n==null?'Недоступно':(n/1073741824).toFixed(1)+' ГБ';
async function refresh(){
try{
const [s,p]=await Promise.all([fetch('/api/status',{cache:'no-store'}),fetch('/api/projects',{cache:'no-store'})]);
if(!s.ok||!p.ok)throw Error('HTTP');
const status=await s.json(),data=await p.json();
$('connection').textContent='Локальная панель доступна';$('core').textContent='Работает';
$('ollama').textContent=status.ollama==='online'?'Подключена':'Недоступна';
$('cpu').textContent=status.cpu_count==null?'Недоступно':status.cpu_count+' потоков';
$('ram').textContent=status.ram_total_bytes==null?'Недоступно':formatGB(status.ram_total_bytes-status.ram_available_bytes)+' / '+formatGB(status.ram_total_bytes);
const select=$('project'),selected=select.value;select.replaceChildren();$('projects').replaceChildren();
for(const p of data.projects){const option=document.createElement('option');option.value=p.id;option.textContent=p.name;select.append(option);const li=document.createElement('li');li.textContent=p.name+' · '+p.status;$('projects').append(li);}
if(data.projects.some(p=>p.id===selected))select.value=selected;
if(!data.projects.length){const li=document.createElement('li');li.textContent='Создайте проект через projects_cli.py';$('projects').append(li);}
}catch(e){$('connection').textContent='Сервер недоступен';$('core').textContent='Нет связи';}
}
async function session(){try{const r=await fetch('/api/session');if(r.ok)token=(await r.json()).token;}catch(e){token='';}}
function say(text){if(!voiceEnabled||!('speechSynthesis' in window))return;
const utterance=new SpeechSynthesisUtterance(text);utterance.lang='ru-RU';utterance.rate=1;
const voices=speechSynthesis.getVoices(),ru=voices.find(v=>v.lang.toLowerCase().startsWith('ru'));if(ru){utterance.voice=ru;$('voice-label').textContent=ru.name;}
utterance.onstart=()=>avatar.setMode('speaking');utterance.onend=()=>avatar.setMode('idle');utterance.onerror=()=>avatar.setMode('idle');speechSynthesis.speak(utterance);}
function stop(){if(controller){controller.abort();controller=null;}if('speechSynthesis' in window)speechSynthesis.cancel();avatar.setMode('idle');$('stop').disabled=true;}
$('quality').addEventListener('change',e=>avatar.setQuality(e.target.value));
$('voice').addEventListener('click',()=>{voiceEnabled=!voiceEnabled;$('voice').textContent='Озвучивание: '+(voiceEnabled?'вкл.':'выкл.');$('voice').setAttribute('aria-pressed',String(voiceEnabled));if(!voiceEnabled&&'speechSynthesis' in window)speechSynthesis.cancel();$('voice-status').textContent=voiceEnabled?'Используется голос браузера; это не обязательно «Руслан».':'Озвучивание выключено';});
$('stop').addEventListener('click',()=>{stop();$('chat-status').textContent='Получение ответа прервано';});
$('listen').addEventListener('click',()=>{
const SpeechRecognition=window.SpeechRecognition||window.webkitSpeechRecognition;
if(!SpeechRecognition){$('voice-status').textContent='Распознавание речи в этом браузере недоступно';return;}
if(recognition){recognition.stop();recognition=null;return;}
recognition=new SpeechRecognition();recognition.lang='ru-RU';recognition.interimResults=false;avatar.setMode('listening');
recognition.onresult=e=>{$('question').value=e.results[0][0].transcript;};
recognition.onerror=()=>{$('voice-status').textContent='Ошибка распознавания';avatar.setMode('idle');};
recognition.onend=()=>{recognition=null;avatar.setMode('idle');};
try{recognition.start();}catch(e){recognition=null;avatar.setMode('idle');$('voice-status').textContent='Микрофон недоступен';}
});
$('chat-form').addEventListener('submit',async e=>{
e.preventDefault();const project=$('project').value,question=$('question').value.trim();
if(!project||!token){$('chat-status').textContent='Нет проекта или соединения';return;}if(!question)return;
$('send').disabled=true;$('question').disabled=true;$('stop').disabled=false;controller=new AbortController();
$('chat').textContent+='\n\nВы: '+question+'\nJARVIS: ';$('question').value='';$('chat-status').textContent='Генерация…';avatar.setMode('thinking');
let answer='',completed=false;
try{
const response=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json','X-JARVIS-Token':token},body:JSON.stringify({project_id:project,question}),signal:controller.signal});
if(!response.ok||!response.body)throw Error('HTTP '+response.status);
const reader=response.body.getReader(),decoder=new TextDecoder();let buffer='';
while(true){const {value,done}=await reader.read();if(done)break;buffer+=decoder.decode(value,{stream:true});let index;
while((index=buffer.indexOf('\n'))!==-1){const line=buffer.slice(0,index);buffer=buffer.slice(index+1);if(!line.trim())continue;
const msg=JSON.parse(line);if(msg.chunk){answer+=msg.chunk;$('chat').textContent+=msg.chunk;$('chat').scrollTop=$('chat').scrollHeight;}if(msg.error)throw Error(msg.error);if(msg.done)completed=true;}}
if(!completed)throw Error('Поток ответа оборван');
$('chat-status').textContent='Ответ завершён';say(answer);
}catch(error){$('chat-status').textContent=error.name==='AbortError'?'Прервано':'Ошибка: '+error.message;
}finally{controller=null;$('stop').disabled=true;$('send').disabled=false;$('question').disabled=false;$('question').focus();if(!('speechSynthesis' in window)||!speechSynthesis.speaking)avatar.setMode('idle');}
});
session();refresh();setInterval(refresh,10000);
