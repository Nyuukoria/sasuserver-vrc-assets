const {test} = require('node:test');
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const {JSDOM} = require('jsdom');
const html = readFileSync('web/index.html','utf8');
const source = readFileSync('web/app.js','utf8');
async function waitFor(check) { for(let i=0;i<100;i++){ if(check())return; await new Promise(r=>setImmediate(r)); } throw new Error('UI did not settle'); }
function environment(role='owner', invited=false, local=false) {
 const dom = new JSDOM(html,{url:'https://sasutendo.tech/'+(invited?'?invite=fake-test-invitation-token':''),runScripts:'outside-only'});
 const w=dom.window, requests=[],items=[],uploads=new Map();let profile={name:'Yuuki',avatar_url:'/api/pictures/avatar-test'};let signedIn=false, next=1;
 w.HTMLDialogElement.prototype.showModal=function(){this.open=true;};w.HTMLDialogElement.prototype.close=function(){this.open=false;};
 w.confirm=()=>true;
 w.fetch=async(path,options={})=>{
  const u=new URL(path,'https://sasutendo.tech');const body=typeof options.body==='string'?JSON.parse(options.body):options.body;
  const method=options.method||'GET';requests.push({path:u.pathname,method,body,headers:options.headers});
  const respond=(data,status=200)=>new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json'}});
  if(u.pathname==='/api/me'&&method==='PATCH'){profile.name=body.name;return respond({ok:true});}
  if(u.pathname==='/api/me/avatar'){profile.avatar_url=method==='DELETE'?null:'/api/pictures/new-avatar';return respond({url:profile.avatar_url});}
  if(u.pathname==='/api/me')return signedIn?respond({id:'test-user',...profile,email:'owner@example.com',role,csrf:'fake-csrf'}):respond({detail:'Sign in'},401);
  if(u.pathname==='/api/status')return respond({configured:!local,local_test:local});
  if(u.pathname==='/api/login'||u.pathname==='/api/join'||u.pathname==='/api/local-setup'){signedIn=true;return respond({ok:true});}
  if(u.pathname==='/api/invite')return respond({email:'friend@example.com',role:'member',expires:2e9});
  if(u.pathname==='/api/stats')return respond({files:items.filter(i=>i.kind==='file').length,folders:items.filter(i=>i.kind==='folder').length,members:1,used:3,capacity:4e12});
  if(u.pathname.endsWith('/cover')){const item=items.find(i=>i.id===u.pathname.split('/')[3]);item.cover_url=method==='DELETE'?null:'/api/pictures/cover-test';return respond({url:item.cover_url});}
  if(u.pathname==='/api/nodes'&&method==='GET')return respond({items:items.filter(i=>!u.searchParams.get('q')||i.name.includes(u.searchParams.get('q'))),breadcrumbs:[],total:items.length});
  if(u.pathname==='/api/admin')return respond({users:[{id:'test-user',name:'Yuuki',email:'owner@example.com',role:'owner',active:1}],invites:[]});
  if(u.pathname==='/api/invites')return respond({id:'invite-1',url:'https://sasutendo.tech/?invite=single-use-test-link'});
  if(u.pathname==='/api/folders'){const item={id:'folder-'+next++,name:body.name,parent:body.parent,kind:'folder',children:0,owner:'test-user',owner_name:'Yuuki',created:1.8e9,updated:1.8e9};items.push(item);return respond(item);}
  if(u.pathname==='/api/uploads'&&method==='GET')return respond([]);
  if(u.pathname==='/api/uploads'&&method==='POST'){const id='upload-'+next++;uploads.set(id,{...body,offset:0,node_id:null});return respond({id,offset:0,chunk_size:8*1024*1024});}
  if(u.pathname.startsWith('/api/uploads/')){
   const id=u.pathname.split('/')[3],upload=uploads.get(id);
   if(!upload)return respond({detail:'Not found'},404);
   if(u.pathname.endsWith('/complete')){upload.node_id=id;items.push({id,name:upload.name,kind:'file',size:upload.size,mime:upload.mime,owner:'test-user',owner_name:'Yuuki',created:1.8e9,updated:1.8e9});return respond({id});}
   if(method==='PATCH'){upload.offset+=body.size;return respond({offset:upload.offset});}
   return respond({id,...upload});
  }
  return respond({detail:'Unexpected route '+u.pathname},500);
 };
 w.eval(source + "\nwindow._queueFilesForTest = queueFiles;");
 return {dom,w,requests,items,uploads};
}
async function login(env){await waitFor(()=>env.requests.some(r=>r.path==='/api/status'));const {w}=env;w.document.querySelector('#auth-email').value='owner@example.com';w.document.querySelector('#auth-password').value='test-password';w.document.querySelector('#auth-form').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await waitFor(()=>!w.document.querySelector('#drive-screen').hidden);await waitFor(()=>env.requests.some(r=>r.path==='/api/uploads'));}

test('sign in renders the actual empty workspace without fake files',async()=>{const e=environment();try{await login(e);assert.equal(e.w.document.querySelector('#auth-screen').hidden,true);assert.match(e.w.document.querySelector('#file-list').textContent,/No files here yet/);assert.equal(e.items.length,0);assert.equal(e.w.document.querySelector('#user-name').textContent,'Yuuki');assert.ok(e.requests.find(r=>r.path==='/api/login').body.password);}finally{e.dom.window.close();}});

test('viewer UI hides uploads and account management',async()=>{const e=environment('viewer');try{await login(e);for(const el of e.w.document.querySelectorAll('.writable,.owner-only'))assert.equal(el.hidden,true);assert.equal(e.w.document.querySelector('#empty-upload'),null);}finally{e.dom.window.close();}});

test('folder creation submits the destination and updates the file list',async()=>{const e=environment();try{await login(e);e.w.document.querySelector('#new-folder').click();const form=e.w.document.querySelector('#dialog-form');form.elements.name.value='Cozy worlds';form.dispatchEvent(new e.w.Event('submit',{cancelable:true}));await waitFor(()=>e.items.length===1);await waitFor(()=>e.w.document.querySelector('#file-list').textContent.includes('Cozy worlds'));const request=e.requests.find(r=>r.path==='/api/folders');assert.deepEqual(request.body,{name:'Cozy worlds',parent:null});assert.equal(request.headers['X-CSRF-Token'],'fake-csrf');}finally{e.dom.window.close();}});

test('folder upload preserves nested paths and finalizes file content',async()=>{const e=environment();try{await login(e);const file=new e.w.File(['abc'],'avatar.unitypackage',{type:'application/octet-stream'});await e.w._queueFilesForTest([{file,path:'Assets/Avatars/avatar.unitypackage'}]);await waitFor(()=>[...e.uploads.values()].some(u=>u.node_id));assert.deepEqual(e.requests.filter(r=>r.path==='/api/folders').map(r=>r.body.name),['Assets','Avatars']);assert.equal([...e.uploads.values()][0].offset,3);await waitFor(()=>e.w.document.querySelector('#upload-items').textContent.includes('Upload complete'));assert.match(e.w.document.querySelector('#upload-items').textContent,/avatar.unitypackage/);}finally{e.dom.window.close();}});

test('invitation screen binds email and removes token after joining',async()=>{const e=environment('member',true);try{await waitFor(()=>e.w.document.querySelector('#auth-title').textContent==='You’re invited.');assert.equal(e.w.document.querySelector('#auth-email').value,'friend@example.com');assert.equal(e.w.document.querySelector('#auth-email').readOnly,true);e.w.document.querySelector('#auth-name').value='Friend';e.w.document.querySelector('#auth-password').value='test-password';e.w.document.querySelector('#auth-form').dispatchEvent(new e.w.Event('submit',{cancelable:true}));await waitFor(()=>!e.w.document.querySelector('#drive-screen').hidden);assert.equal(e.w.location.search,'');assert.equal(e.requests.find(r=>r.path==='/api/join').body.email,'friend@example.com');}finally{e.dom.window.close();}});

test('owner invitation flow returns a copyable private link',async()=>{const e=environment();try{await login(e);e.w.document.querySelector('#invite-button').click();const form=e.w.document.querySelector('#dialog-form');form.elements.email.value='friend@example.com';form.dispatchEvent(new e.w.Event('submit',{cancelable:true}));await waitFor(()=>e.w.document.querySelector('#copy-invite'));assert.match(e.w.document.querySelector('.invite-link-box').textContent,/invite=single-use-test-link/);assert.match(e.w.document.querySelector('#dialog-body').textContent,/No email has been sent automatically/);}finally{e.dom.window.close();}});


test('local first launch creates an owner with optional samples',async()=>{const e=environment('owner',false,true);try{await waitFor(()=>e.w.document.querySelector('#auth-title').textContent==='Set up your local drive');assert.equal(e.w.document.querySelector('#samples-label').hidden,false);e.w.document.querySelector('#auth-name').value='Yuuki';e.w.document.querySelector('#auth-email').value='local@example.com';e.w.document.querySelector('#auth-password').value='local-test-password';e.w.document.querySelector('#auth-form').dispatchEvent(new e.w.Event('submit',{cancelable:true}));await waitFor(()=>!e.w.document.querySelector('#drive-screen').hidden);const setup=e.requests.find(r=>r.path==='/api/local-setup');assert.equal(setup.body.samples,true);assert.equal(setup.body.name,'Yuuki');assert.equal(e.w.document.querySelector('#local-test-banner').hidden,false);}finally{e.dom.window.close();}});


test('dark theme, artwork and clear navigation are available on first visit',async()=>{const e=environment();try{await login(e);assert.equal(e.w.document.documentElement.classList.contains('dark'),true);assert.equal(e.w.document.title,'Nyuukoria Drive');assert.ok(e.w.document.querySelector('.story-art').src.endsWith('/assets/nyuukoria.png'));assert.equal(e.w.document.querySelector('[data-view="archives"]').textContent.trim(),'Archived');assert.ok(e.w.document.querySelector('[data-view="videos"]'));e.w.document.querySelector('#theme-toggle').click();assert.equal(e.w.localStorage.getItem('nyuukoria-theme'),'light');}finally{e.dom.window.close();}});

test('profile dialog saves a name and removes the existing avatar',async()=>{const e=environment();try{await login(e);e.w.document.querySelector('#profile-button').click();assert.ok(e.w.document.querySelector('.large-avatar img'));e.w.document.querySelector('#remove-avatar').click();await waitFor(()=>e.requests.some(r=>r.path==='/api/me/avatar'&&r.method==='DELETE'));await waitFor(()=>!e.w.document.querySelector('#remove-avatar'));const form=e.w.document.querySelector('#dialog-form');form.elements.name.value='Nyuukoria';form.dispatchEvent(new e.w.Event('submit',{cancelable:true}));await waitFor(()=>e.w.document.querySelector('#toasts').textContent.includes('Profile updated.'));assert.equal(e.w.document.querySelector('#user-name').textContent,'Nyuukoria');assert.equal(e.requests.find(r=>r.path==='/api/me'&&r.method==='PATCH').body.name,'Nyuukoria');}finally{e.dom.window.close();}});

test('folder covers, uploader avatars and upload times render in list and grid',async()=>{const e=environment();try{await login(e);e.items.push({id:'example',name:'Videos',kind:'folder',children:2,owner:'test-user',owner_name:'Yuuki',owner_avatar:'/api/pictures/uploader',cover_url:'/api/pictures/cover',created:1800000000,updated:1900000000});e.w.document.querySelector('#refresh').click();await waitFor(()=>e.w.document.querySelector('.file-row'));assert.ok(e.w.document.querySelector('.file-type-icon img').src.endsWith('/api/pictures/cover'));assert.ok(e.w.document.querySelector('.file-owner img').src.endsWith('/api/pictures/uploader'));assert.equal(e.w.document.querySelector('.file-date time').dateTime,new Date(1800000000*1000).toISOString());e.w.document.querySelector('[data-more]').click();assert.ok(e.w.document.querySelector('#cover-item'));e.w.document.querySelector('#remove-cover').click();await waitFor(()=>e.w.document.querySelector('#toasts').textContent.includes('Folder cover removed.'));e.w.document.querySelector('#grid-view').click();assert.equal(e.w.document.querySelector('#file-list').classList.contains('grid'),true);assert.ok(e.w.document.querySelector('.file-owner img'));}finally{e.dom.window.close();}});
