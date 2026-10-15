async function refresh(){try{const [s,p]=await Promise.all([fetch('/api/status'),fetch('/api/projects')]);if(!s.ok||!p.ok)throw Error('HTTP error');const status=await s.json(),projects=await p.json();document.getElementById('connection').textContent='Локальная панель доступна';document.getElementById('core').textContent=status.dashboard==='online'?'Панель работает':'Неизвестно';document.getElementById('ollama').textContent='Не проверена';const list=document.getElementById('projects');list.replaceChildren();const select=document.getElementById('project');const current=select.value;select.replaceChildren();for(const p of projects.projects){const option=document.createElement('option');option.value=p.id;option.textContent=p.name;select.append(option)}if(current&&projects.projects.some(p=>p.id===current))select.value=current;for(const project of projects.projects){const li=document.createElement('li');li.textContent=project.name+' · '+project.status;list.append(li)}if(!projects.projects.length){const li=document.createElement('li');li.textContent='Проектов пока нет';list.append(li)}}catch(e){document.getElementById('connection').textContent='Нет соединения'}}refresh();setInterval(refresh,10000);


let sessionToken='';
fetch('/api/session').then(r=>r.json()).then(d=>{sessionToken=d.token}).catch(()=>{});
document.getElementById('chat-form').addEventListener('submit',async event=>{
event.preventDefault();const input=document.getElementById('question'),project=document.getElementById('project').value,send=document.getElementById('send'),chat=document.getElementById('chat'),status=document.getElementById('chat-status');
if(!project||!sessionToken){status.textContent='Нет проекта или соединения';return}
const question=input.value.trim();if(!question)return;
send.disabled=true;input.disabled=true;status.textContent='Генерация…';chat.textContent+='Вы: '+question+'\nJARVIS: ';input.value='';
try{
const response=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json','X-JARVIS-Token':sessionToken},body:JSON.stringify({project_id:project,question})});
if(!response.ok||!response.body)throw Error('HTTP '+response.status);
const reader=response.body.getReader(),decoder=new TextDecoder();let buffer='',finished=false;
while(true){const {value,done}=await reader.read();if(done)break;buffer+=decoder.decode(value,{stream:true});let index;while((index=buffer.indexOf('\n'))!==-1){const line=buffer.slice(0,index);buffer=buffer.slice(index+1);if(!line.trim())continue;const msg=JSON.parse(line);if(msg.chunk)chat.textContent+=msg.chunk;if(msg.error)throw Error(msg.error);if(msg.done)finished=true;}}
if(!finished)throw Error('Поток оборван');status.textContent='Ответ завершён';
}catch(error){status.textContent='Ошибка: '+error.message}finally{chat.textContent+='\n\n';send.disabled=false;input.disabled=false;input.focus()}
});
