/* Genuine WebGL 3D procedural neural face, no external libraries or CDN. */
(()=>{'use strict';
const canvas=document.getElementById('avatar3d'),status=document.getElementById('avatar-state');
if(!canvas)return;
const gl=canvas.getContext('webgl',{alpha:true,antialias:true,powerPreference:'low-power'});
if(!gl){status.textContent='WebGL недоступен';return;}
const vs='attribute vec3 p; uniform mat4 m; uniform float pulse; varying float glow; void main(){gl_Position=m*vec4(p,1.0);gl_PointSize=2.0+pulse*1.5;glow=0.65+0.35*pulse;}';
const fs='precision mediump float;varying float glow;uniform vec4 tint;void main(){gl_FragColor=vec4(tint.rgb*glow,tint.a);}';
function shader(type,source){const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;}
const program=gl.createProgram();gl.attachShader(program,shader(gl.VERTEX_SHADER,vs));gl.attachShader(program,shader(gl.FRAGMENT_SHADER,fs));gl.linkProgram(program);
if(!gl.getProgramParameter(program,gl.LINK_STATUS)){status.textContent='Ошибка WebGL';return;}
gl.useProgram(program);const loc=gl.getAttribLocation(program,'p'),mat=gl.getUniformLocation(program,'m'),tint=gl.getUniformLocation(program,'tint'),pulse=gl.getUniformLocation(program,'pulse');
const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.enableVertexAttribArray(loc);gl.vertexAttribPointer(loc,3,gl.FLOAT,false,0,0);
let mode='idle',quality='balanced',visible=true,mouthLevel=0;
const states={idle:'ОЖИДАНИЕ',listening:'СЛУШАЕТ',thinking:'ДУМАЕТ',speaking:'ГОВОРИТ',error:'ОШИБКА'};
function setMode(v){mode=states[v]?v:'idle';status.textContent=states[mode];}
window.JarvisAvatar={setMode,setQuality(v){quality=['cinematic','balanced','eco'].includes(v)?v:'balanced';},getMode(){return mode;},setMouth(v){mouthLevel=Math.max(0,Math.min(1,Number(v)||0));}};
function point(x,y,z,out){out.push(x,y,z);}
function face(t){const data=[],rings=quality==='cinematic'?46:quality==='eco'?19:30,cols=quality==='cinematic'?76:quality==='eco'?32:52;
const mouth=mode==='speaking'?(0.012+0.14*mouthLevel):0.012;
const blink=Math.pow(Math.max(0,Math.cos(t*0.83)),36)*0.12;
for(let i=0;i<rings;i++){const v=-Math.PI/2+Math.PI*i/(rings-1);for(let j=0;j<cols;j++){const u=-Math.PI+2*Math.PI*j/(cols-1);const x=0.77*Math.cos(v)*Math.sin(u),y=1.15*Math.sin(v),z=0.54*Math.cos(v)*Math.cos(u);
let zz=z; if(Math.abs(x)<0.20&&y>-0.15&&y<0.40&&z>0)zz+=0.13*(1-Math.abs(x)/0.2);
if(i+1<rings){const v2=-Math.PI/2+Math.PI*(i+1)/(rings-1),xx=0.77*Math.cos(v2)*Math.sin(u),yy=1.15*Math.sin(v2),z2=0.54*Math.cos(v2)*Math.cos(u);point(x,y,zz,data);point(xx,yy,z2,data);}
if(j+1<cols){const u2=-Math.PI+2*Math.PI*(j+1)/(cols-1);point(x,y,zz,data);point(0.77*Math.cos(v)*Math.sin(u2),y,0.54*Math.cos(v)*Math.cos(u2),data);}
}}
function arc(cx,cy,rx,ry,z,start,end,n){for(let k=0;k<n;k++){const a=start+(end-start)*k/n,b=start+(end-start)*(k+1)/n;point(cx+rx*Math.cos(a),cy+ry*Math.sin(a),z,data);point(cx+rx*Math.cos(b),cy+ry*Math.sin(b),z,data);}}
arc(-0.29,0.24,0.17,Math.max(0.01,0.085-blink),0.53,0,Math.PI*2,30);
arc(0.29,0.24,0.17,Math.max(0.01,0.085-blink),0.53,0,Math.PI*2,30);
arc(0,-0.38,0.28,mouth,0.56,0,Math.PI*2,36);
for(let k=0;k<14;k++){const a=k*Math.PI/7;point(0.58*Math.cos(a),-1.03,0,data);point(0.9*Math.cos(a),-1.5,0.1*Math.sin(a),data);}
return new Float32Array(data);}
function render(time){if(!visible){requestAnimationFrame(render);return;}const t=time/1000,dpr=Math.min(devicePixelRatio||1,1.5),w=Math.max(1,canvas.clientWidth*dpr|0),h=Math.max(1,canvas.clientHeight*dpr|0);
if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;gl.viewport(0,0,w,h);}
gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT);gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE);
const angle=Math.sin(t*0.35)*0.12,co=Math.cos(angle),si=Math.sin(angle),aspect=w/h;
const m=new Float32Array([co/aspect*0.88,0,-si*0.88,0,0,0.88,0,0,si/aspect*0.88,0,co*0.88,0,0,-0.05,0,1]);
gl.uniformMatrix4fv(mat,false,m);gl.uniform4f(tint,0.19,0.75,1,0.38);gl.uniform1f(pulse,mode==='thinking'?Math.abs(Math.sin(t*3)):mode==='speaking'?Math.abs(Math.sin(t*9)):0.35);
const vertices=face(t);gl.bufferData(gl.ARRAY_BUFFER,vertices,gl.DYNAMIC_DRAW);gl.drawArrays(gl.LINES,0,vertices.length/3);
requestAnimationFrame(render);}
document.addEventListener('visibilitychange',()=>{visible=!document.hidden;});
requestAnimationFrame(render);
})();