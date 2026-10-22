'use strict';
const $ = (s, root = document) => root.querySelector(s);
const $$ = (s, root = document) => [...root.querySelectorAll(s)];
const shapes = {
 back:'M19 12H5m6-6-6 6 6 6', up:'M12 20V4m-6 6 6-6 6 6',
 folder:'M3 7V5a2 2 0 0 1 2-2h5l2 3h7a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z',
 file:'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8ZM14 2v6h6M8 13h8M8 17h5',
 files:'M14 2H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12V8ZM14 2v6h6M20 12v10H8',
 cloud:'M7 18a5 5 0 1 1 .9-9.9A7 7 0 0 1 21 11a3.5 3.5 0 0 1-1.5 7ZM12 10v8m-3-5 3-3 3 3',
 plus:'M12 5v14M5 12h14', minus:'M5 12h14', x:'m6 6 12 12M6 18 18 6', arrow:'M4 12h16m-6-6 6 6-6 6', chevron:'m6 9 6 6 6-6', right:'m9 6 6 6-6 6',
 clock:'M12 8v4l3 2M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0',
 star:'m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2L12 17.3 6.4 20.2l1.1-6.2L3 9.6l6.2-.9Z',
 image:'M4 3h16a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1ZM3 17l6-6 4 4 3-3 5 5M8 7h.01',
 box:'m3 7 9-5 9 5v10l-9 5-9-5Zm0 0 9 5 9-5M12 12v10M7 4.8l9 5',
 trash:'M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7M14 10v7',
 users:'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M16 3a4 4 0 0 1 0 8M22 21v-2a4 4 0 0 0-3-3.9M13 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0',
 'user-plus':'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M13 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0M20 8v6M17 11h6',
 lock:'M5 10h14v11H5ZM8 10V6a4 4 0 0 1 8 0v4M12 14v3',
 logout:'M9 21H3V3h6M9 12h13m-5-5 5 5-5 5',
 shield:'m12 2 9 4v6c0 5-9 10-9 10S3 17 3 12V6Zm-5 10 3 3 7-7',
 moon:'M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8',
 activity:'M3 12h4l3-8 4 16 3-8h4', menu:'M3 6h18M3 12h18M3 18h18',
 'folder-plus':'M3 7V5a2 2 0 0 1 2-2h5l2 3h7a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2ZM12 10v7M8.5 13.5h7',
 upload:'M12 16V3m-5 5 5-5 5 5M3 16v5h18v-5', download:'M12 3v13m-5-5 5 5 5-5M3 16v5h18v-5',
 search:'M21 21l-5-5M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0',
 list:'M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01',
 grid:'M3 3h7v7H3ZM14 3h7v7h-7ZM3 14h7v7H3ZM14 14h7v7h-7Z',
 refresh:'M20 7v5h-5M4 17v-5h5M5.6 6a8 8 0 0 1 13 .5L20 9M4 15l1.4 2.5a8 8 0 0 0 13 .5',
 eye:'M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12ZM15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0',
 more:'M5 12h.01M12 12h.01M19 12h.01', music:'M9 18V5l12-2v13M9 7l12-2M9 18a3 3 0 1 1-3-3h3M21 16a3 3 0 1 1-3-3h3',
 video:'M3 5h13v14H3ZM16 10l6-4v12l-6-4', check:'m5 12 4 4L19 6', copy:'M8 8h13v13H8ZM16 8V3H3v13h5', restore:'M3 10a9 9 0 1 1 1 7M3 4v6h6M12 7v5l3 2', edit:'m16 3 5 5-12 12-6 1 1-6ZM13 6l5 5'
};
const icon = name => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${shapes[name] || shapes.file}"/></svg>`;
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function icons(root = document) { $$('[data-icon]', root).forEach(el => el.innerHTML = icon(el.dataset.icon)); }
function bytes(n) { if (!n) return '0 B'; const i = Math.min(4, Math.floor(Math.log(n) / Math.log(1000))); return `${(n / 1000 ** i).toFixed(i > 1 ? 1 : 0)} ${['B','KB','MB','GB','TB'][i]}`; }
function date(n) { return new Intl.DateTimeFormat(undefined, {dateStyle:'medium',timeStyle:'short'}).format(n * 1000); }
function stamp(n){return `<time datetime="${new Date(n*1000).toISOString()}" title="${esc(date(n))}">${esc(date(n))}</time>`;}
function avatar(url,name,cls='owner-dot'){return `<span class="${cls}">${url?`<img src="${esc(url)}" alt="" loading="lazy">`:esc((name||'?').slice(0,1).toUpperCase())}</span>`;}
function fileThumbnail(item,type,color){return `<span class="file-type-icon ${color} ${item.cover_url?'has-cover':''}">${item.kind==='folder'?`<img src="${esc(item.cover_url||'/assets/nyuukoria.png')}" alt="" loading="lazy">`:item.cover_url?`<img src="${esc(item.cover_url)}" alt="" loading="lazy">`:item.kind==='file'&&['image/png','image/jpeg','image/webp','image/gif','image/avif'].includes(item.mime)?`<img src="/api/nodes/${encodeURIComponent(item.id)}/download?preview=true" alt="" loading="lazy">`:icon(type)}</span>`;}
const state = { user: null, parent: null, view: 'files', items: [], crumbs: [], selected: new Set(), grid: false, search: '', total: 0, uploads: [], running: 0, listRequest: 0 };
let localSetup = false;
let inviteToken = new URLSearchParams(location.search).get('invite');
try { state.grid = localStorage.getItem('sasu-view') === 'grid'; document.documentElement.classList.toggle('dark', localStorage.getItem('nyuukoria-theme') !== 'light'); } catch {}
function toast(message, error = false) { const el = document.createElement('div'); el.className = 'toast' + (error ? ' error' : ''); el.textContent = message; $('#toasts').append(el); setTimeout(() => el.remove(), error ? 9000 : 4500); }
async function api(path, options = {}) {
 const response = await fetch('/api' + path, { ...options, headers: { ...(options.body && typeof options.body === 'string' ? {'Content-Type':'application/json'} : {}), ...(state.user ? {'X-CSRF-Token': state.user.csrf} : {}), ...options.headers } });
 let data; try { data = await response.json(); } catch { throw new Error('The server returned an unexpected response. Please try again.'); }
 if (!response.ok) { if (response.status === 401 && state.user) { state.uploads.forEach(u => u.controller?.abort()); state.user = null; showAuth(); } throw Object.assign(new Error(typeof data.detail === 'string' ? data.detail : 'Please check the entered information.'), { status: response.status }); }
 return data;
}
const post = (path, data) => api(path, {method:'POST', body:JSON.stringify(data ?? {})});
function showAuth() { $('#drive-screen').hidden=true;$('#auth-screen').hidden=false;if(!inviteToken&&!localSetup){$('#auth-title').textContent='Welcome back.';$('#auth-description').textContent='Sign in to access your files and shared projects.';$('#auth-submit-label').textContent='Sign in';$('#auth-password').value='';$('#auth-email').readOnly=false;$('#name-label').hidden=true;$('#auth-name').required=false;$('#samples-label').hidden=true;$('#auth-password').autocomplete='current-password';} }
function dialog(title, html) { $('#dialog-title').textContent = title; $('#dialog-body').innerHTML = html; icons($('#dialog')); if (!$('#dialog').open) $('#dialog').showModal(); }
function formDialog(title, html, onSubmit) {
 dialog(title, `<form id="dialog-form" class="dialog-form">${html}<p class="form-error" role="alert"></p><button type="submit" class="button primary">Save changes ${icon('arrow')}</button></form>`);
 $('#dialog-form').onsubmit = async e => { e.preventDefault(); const form = e.currentTarget; $('button[type=submit]', form).disabled = true; try { await onSubmit(new FormData(form)); } catch (error) { $('.form-error', form).textContent = error.message; } finally { if (form.isConnected) $('button[type=submit]', form).disabled = false; } };
}
function fileStyle(item) {
 if (item.kind === 'folder') return ['folder', 'sand', 'Folder'];
 const extension = item.name.split('.').pop().toLowerCase();
 if (['unitypackage','fbx','blend','unity','prefab','vrm','glb','gltf'].includes(extension)) return ['box','lilac','3D & world asset'];
 if (item.mime.startsWith('image/')) return ['image','rose','Image'];
 if (item.mime.startsWith('video/')) return ['video','lilac','Video'];
 if (item.mime.startsWith('audio/')) return ['music','sage','Audio'];
 if (['zip','rar','7z','gz','tar'].includes(extension)) return ['box','sand','Archive'];
 return ['file','sage',extension.toUpperCase() + ' file'];
}
const canWrite = () => state.user && state.user.role !== 'viewer';
const canChange = item => canWrite() && (state.user.role === 'owner' || item.owner === state.user.id);
async function enterDrive() {
 $('#auth-screen').hidden = true; $('#drive-screen').hidden = false;
 $('#user-name').textContent = state.user.name; $('#user-role').textContent = state.user.role === 'member' ? 'Member · can upload' : state.user.role;
 renderProfile();
 $$('.owner-only').forEach(el => el.hidden = state.user.role !== 'owner'); $$('.writable').forEach(el => el.hidden = !canWrite());
 const route=readRoute();await Promise.all([refreshStats(),navigate(route.view,route.parent,false)]);
 const pending = await api('/uploads'); if (pending.length) toast(`${pending.length} unfinished upload${pending.length === 1 ? '' : 's'} found. Use “Unfinished uploads” in the upload panel.`);
 if (pending.length) { $('#upload-reopen').hidden = false; $('#upload-reopen').textContent = 'Unfinished uploads'; }
}
async function refreshStats() {
 const stats = await api('/stats'); const percent = Math.min(100, stats.used / stats.capacity * 100);
 $('#storage-percent').textContent = `${percent < 1 && percent > 0 ? '<1' : percent.toFixed(0)}%`;
 $('#storage-bar').style.width = `${Math.max(stats.used ? 1 : 0, percent)}%`;
 $('#storage-label').textContent = `${bytes(stats.used)} of ${bytes(stats.capacity)} used`;
 $('#file-count').textContent = stats.files;
 $('#stat-files').innerHTML = `${stats.files.toLocaleString()} <span>files</span>`;
 $('#stat-folders').innerHTML = `${stats.folders.toLocaleString()} <span>folders</span>`;
 $('#stat-members').innerHTML = `${stats.members} <span>${stats.members === 1 ? 'person' : 'people'}</span>`;
}
const titles = {files:'All files', recent:'Recent files', starred:'Starred', images:'Images', videos:'Videos', audio:'Audio', archives:'Archived', trash:'Trash', members:'Members & invites'};
function readRoute(){const [view,parent]=location.hash.slice(1).split('/');return {view:titles[view]&&(view!=='members'||state.user?.role==='owner')?view:'files',parent:view==='files'&&/^[a-f0-9]{32}$/.test(parent||'')?parent:null};}
function writeRoute(){const hash='#'+state.view+(state.parent?'/'+state.parent:'');if(location.hash!==hash){if(history.state?.driveDepth!==undefined)history.pushState({driveDepth:history.state.driveDepth+1},'',hash);else history.replaceState({driveDepth:0},'',hash);}$('#nav-back').disabled=!(history.state?.driveDepth>0);}
window.addEventListener('popstate',()=>{if(state.user){const route=readRoute();navigate(route.view,route.parent,false).catch(e=>toast(e.message,true));}});
async function navigate(view, parent = null, record = true) {
 if(record)clearTimeout(searchTimer);
 state.view = view; state.parent = parent; state.selected.clear(); state.search = ''; $('#search').value = '';
 $('#inspector').hidden = true; $('#sidebar').classList.remove('open');
 $$('.nav-item').forEach(el => {el.classList.toggle('active', el.dataset.view === view);if(el.dataset.view===view)el.setAttribute('aria-current','page');else el.removeAttribute('aria-current');});
 $('#topbar-current').textContent = titles[view];
 $('#page-title').textContent=titles[view];
 $('#page-description').textContent={members:'Manage access and create private invitation links.',trash:'Restore removed items or delete them permanently.',videos:'Your uploaded videos. Play supported formats or download the original.',audio:'Music, recordings and other audio files.',archives:'Compressed files and project packages.',recent:'Your latest uploads and changes.',starred:'Files and folders you saved for quick access.',images:'Photos, artwork and other images.',files:'Browse, upload and organize your files.'}[view];
 $('#files-section').hidden = view === 'members'; $('#members-section').hidden = view !== 'members'; $('#overview').hidden = view === 'members';
 $$('.file-tools .writable,.drop-hint.writable').forEach(el => el.hidden = !canWrite() || view === 'trash' || view === 'members');
 if (view === 'members'){++state.listRequest;await loadMembers();}else await loadFiles();
 if(record)writeRoute();else{$('#nav-back').disabled=!(history.state?.driveDepth>0);if(history.state?.driveDepth===undefined)history.replaceState({driveDepth:0},'',location.hash||'#files');}$('#nav-up').disabled=!(state.view==='files'&&state.parent);
}
async function loadFiles(append = false) {
 const requestId = ++state.listRequest; const offset = append ? state.items.length : 0;
 const params = new URLSearchParams({view:state.view, q:state.search, offset, limit:200,sort:$('#sort').value}); if (state.parent) params.set('parent', state.parent);
 if (!append) $('#file-list').setAttribute('aria-busy', 'true');
 try {
  const data = await api('/nodes?' + params);
  if (requestId !== state.listRequest) return;
  state.items = append ? [...state.items,...data.items] : data.items; state.crumbs = data.breadcrumbs; state.total = data.total ?? data.items.length;
  renderFiles();
 } finally { $('#file-list').removeAttribute('aria-busy'); }
}
function renderFiles() {
 let items = [...state.items]; const sort = $('#sort').value;
 items.sort((a,b) => a.kind !== b.kind ? (a.kind === 'folder' ? -1 : 1) : sort === 'name' ? a.name.localeCompare(b.name) : sort === 'size' ? b.size-a.size : sort === 'created' ? b.created-a.created : b.updated-a.updated);
 $('#breadcrumbs').innerHTML = state.view === 'files' ? `<button data-folder="">${icon('folder')} All files</button>${state.crumbs.map(c => `${icon('right')}<button data-folder="${esc(c.id)}">${esc(c.name)}</button>`).join('')}` : `<span>${esc(titles[state.view])}</span>`;
 $('#breadcrumbs').querySelectorAll('[data-folder]').forEach(el => el.onclick = () => navigate('files', el.dataset.folder || null).catch(e=>toast(e.message,true)));
 if(state.view==='files'){const current=state.crumbs.at(-1);$('#page-title').textContent=current?.name||'All files';$('#topbar-current').textContent=current?.name||'All files';}$('#nav-up').disabled=!(state.view==='files'&&state.parent);
 $('#file-list').classList.toggle('grid', state.grid); $('#list-view').classList.toggle('active', !state.grid); $('#grid-view').classList.toggle('active', state.grid);
 if (!items.length) {
  const emptyTitle = state.search ? 'No matching files' : state.view === 'starred' ? 'No starred items yet' : state.view === 'trash' ? 'Trash is empty' : 'No files here yet';
  const emptyText = state.search ? 'Try another name, or look in a different collection.' : state.view === 'starred' ? 'Star a file or folder to find it here whenever you need it.' : state.view === 'trash' ? 'Removed files will appear here. You can restore them whenever you change your mind.' : 'Upload files or folders to get started. Videos, projects and any other file types are supported.';
  $('#file-list').innerHTML = `<div class="empty-state"><span class="empty-orbit">${icon(state.view === 'starred' ? 'star' : state.view === 'trash' ? 'trash' : 'folder-plus')}</span><h3>${emptyTitle}</h3><p>${emptyText}</p>${canWrite() && !state.search && state.view === 'files' ? `<button class="button primary" id="empty-upload">${icon('upload')} Add your first files</button>` : ''}</div>`;
  if ($('#empty-upload')) $('#empty-upload').onclick = () => $('#file-input').click();
 } else {
  $('#file-list').innerHTML = `<div class="table-head"><input type="checkbox" id="select-all" aria-label="Select all visible files"><span>Name</span><span class="date-heading">Uploaded</span><span>File size</span><span class="owner-heading">Added by</span><span></span></div>` + items.map(item => {
   const [type,color,label] = fileStyle(item);
   return `<div class="file-row ${state.selected.has(item.id)?'selected':''}" data-id="${esc(item.id)}" tabindex="0" role="button" aria-label="${esc(item.name)}"><input type="checkbox" data-select="${esc(item.id)}" aria-label="Select ${esc(item.name)}" ${state.selected.has(item.id)?'checked':''}><div class="file-name">${fileThumbnail(item,type,color)}<div class="file-name-text"><strong>${esc(item.name)}${item.starred?'<span class="star-mark">✧</span>':''}</strong><small>${esc(item.kind === 'folder' ? `${item.children} item${item.children===1?'':'s'}` : label)}</small><span class="compact-uploader">${avatar(item.owner_avatar,item.owner_name)}<span>${esc(item.owner_name)} · ${stamp(item.created)}</span></span></div></div><span class="file-date">${stamp(item.created)}</span><span class="file-size">${item.kind==='folder'?'—':bytes(item.size)}</span><span class="file-owner">${avatar(item.owner_avatar,item.owner_name)}<span>${esc(item.owner_name)}</span></span><button class="row-action" data-more="${esc(item.id)}" aria-label="Details for ${esc(item.name)}">${icon('more')}</button></div>`;
  }).join('');
  $$('.file-row').forEach(row => {
   const item = state.items.find(i=>i.id===row.dataset.id);
   row.onclick = e => { if (e.target.closest('input,button')) return; if(item.kind==='folder' && state.view!=='trash') navigate('files',item.id).catch(e=>toast(e.message,true)); else inspect(item); };
   row.onkeydown = e => { if(e.target!==row)return; if(e.key==='Enter'){e.preventDefault();row.click();} };
  });
  $$('[data-more]').forEach(button => button.onclick = () => inspect(state.items.find(i=>i.id===button.dataset.more)));
  $$('[data-select]').forEach(input => input.onchange = () => { if(input.checked)state.selected.add(input.dataset.select); else state.selected.delete(input.dataset.select); updateSelection(); });
  $('#select-all').onchange = e => { state.selected.clear(); if(e.target.checked)state.items.forEach(i=>state.selected.add(i.id)); renderFiles(); };
 }
 updateSelection(); $('#load-more').hidden = state.items.length >= state.total;
 $('#item-count').textContent = state.items.length ? `${state.items.length} of ${state.total} items · ${state.items.filter(i=>i.kind==='folder').length} folders` : 'No files yet.';
}
function updateSelection() {
 $('#selection-bar').hidden = !state.selected.size; $('#selection-count').textContent = `${state.selected.size} selected`;
 $('#trash-selection').hidden = !canWrite(); $('#trash-selection').textContent = state.view==='trash' ? 'Restore selected' : 'Move to trash';
 $$('.file-row').forEach(row=>row.classList.toggle('selected',state.selected.has(row.dataset.id)));
}
function inspect(item) {
 const [type,color,label] = fileStyle(item); const trashed = state.view==='trash'; const url = `/api/nodes/${encodeURIComponent(item.id)}/download`;
 let preview = item.kind==='folder'?`<img src="${esc(item.cover_url||'/assets/nyuukoria.png')}" alt="Folder cover">`:icon(type); const extension = item.name.split('.').pop().toLowerCase();
 if (!trashed && ['jpg','jpeg','png','webp','gif','avif'].includes(extension)) preview=`<img src="${url}?preview=true" alt="${esc(item.name)}">`;
 if (!trashed && ['mp4','webm'].includes(extension)) preview=`<video controls preload="metadata" src="${url}?preview=true"></video>`;
 if (!trashed && ['mp3','ogg','wav'].includes(extension)) preview=`<audio controls preload="metadata" src="${url}?preview=true"></audio>`;
 const el=$('#inspector'); el.hidden=false;
 el.innerHTML=`<div class="inspector-head"><strong>File details</strong><button id="inspector-close" class="icon-button" aria-label="Close details">${icon('x')}</button></div><div class="preview-box ${color}">${preview}</div><h3>${esc(item.name)}</h3><dl class="detail-list"><dt>Type</dt><dd>${label}</dd><dt>Size</dt><dd>${item.kind==='folder'?`${item.children} items`:bytes(item.size)}</dd><dt>Uploaded by</dt><dd class="uploader-detail">${avatar(item.owner_avatar,item.owner_name)}${esc(item.owner_name)}</dd><dt>Uploaded</dt><dd>${stamp(item.created)}</dd><dt>Modified</dt><dd>${stamp(item.updated)}</dd></dl><div class="inspector-actions">${!trashed ? (item.kind==='file'?`<a class="button primary" href="${url}">${icon('download')} Download file</a>`:`<button class="button primary" id="open-folder">${icon('folder')} Open folder</button>`)+`<button class="button subtle" id="star-item">${icon('star')} ${item.starred?'Remove star':'Add to starred'}</button>`:''}${canChange(item) ? trashed ? `<button class="button subtle" id="restore-item">${icon('restore')} Restore item</button>` : `${item.kind==='folder'?`<button class="button subtle" id="cover-item">${icon('image')} ${item.cover_url?'Change':'Add'} folder cover</button>${item.cover_url?'<button class="button quiet" id="remove-cover">Remove cover</button>':''}`:''}<button class="button subtle" id="rename-item">${icon('edit')} Rename</button><button class="button subtle" id="move-item">${icon('folder')} Move to folder</button><button class="button quiet" id="trash-item">${icon('trash')} Move to trash</button>`:''}${trashed&&state.user.role==='owner'?'<button class="button danger" id="purge-item">Delete permanently</button>':''}</div>`;
 $('#inspector-close').onclick=()=>el.hidden=true;
 if($('#cover-item'))$('#cover-item').onclick=()=>choosePicture(`/nodes/${item.id}/cover`,async()=>{await loadFiles();const updated=state.items.find(i=>i.id===item.id);if(updated)inspect(updated);});
 if($('#remove-cover'))$('#remove-cover').onclick=async()=>{try{await api(`/nodes/${item.id}/cover`,{method:'DELETE'});item.cover_url=null;inspect(item);await loadFiles();toast('Folder cover removed.');}catch(e){toast(e.message,true);}};
 if($('#open-folder'))$('#open-folder').onclick=()=>navigate('files',item.id).catch(e=>toast(e.message,true));
 if($('#star-item'))$('#star-item').onclick=async()=>{try{const r=await post(`/nodes/${item.id}/star`);item.starred=r.starred;inspect(item);await loadFiles();}catch(e){toast(e.message,true);}};
 if($('#rename-item'))$('#rename-item').onclick=()=>formDialog('Rename item',`<label>Name<input name="name" value="${esc(item.name)}" required maxlength="200"></label>`,async f=>{await api(`/nodes/${item.id}`,{method:'PATCH',body:JSON.stringify({name:f.get('name')})});$('#dialog').close();el.hidden=true;await loadFiles();toast('Name updated.');});
 if($('#move-item'))$('#move-item').onclick=()=>moveDialog(item,null);
 if($('#trash-item'))$('#trash-item').onclick=async()=>{try{await api(`/nodes/${item.id}`,{method:'DELETE'});el.hidden=true;await Promise.all([loadFiles(),refreshStats()]);toast('Moved to trash. You can restore it anytime.');}catch(e){toast(e.message,true);}};
 if($('#restore-item'))$('#restore-item').onclick=async()=>{try{await post(`/nodes/${item.id}/restore`);el.hidden=true;await Promise.all([loadFiles(),refreshStats()]);toast('Item restored.');}catch(e){toast(e.message,true);}};
 if($('#purge-item'))$('#purge-item').onclick=()=>{dialog('Delete this forever?',`<p class="dialog-text">“${esc(item.name)}” and everything inside will be permanently removed from the server. This cannot be undone.</p><button id="confirm-purge" class="button danger">Delete permanently</button>`);$('#confirm-purge').onclick=async()=>{try{await api(`/nodes/${item.id}/permanent`,{method:'DELETE'});$('#dialog').close();el.hidden=true;await Promise.all([loadFiles(),refreshStats()]);toast('Permanently deleted.');}catch(e){toast(e.message,true);}};};
}
async function moveDialog(item,parent) {
 try {
  const p=new URLSearchParams({limit:1000});if(parent)p.set('parent',parent);const data=await api('/nodes?'+p);
  const folders=data.items.filter(i=>i.kind==='folder'&&i.id!==item.id);
  dialog('Move to folder',`<p class="dialog-text">Move “${esc(item.name)}” to ${parent?esc(data.breadcrumbs.at(-1)?.name):'All files'}.</p><div id="destinations">${parent?`<button class="button quiet" id="move-up">← Parent folder</button>`:''}${folders.map(f=>`<div class="folder-destination" role="button" tabindex="0" data-destination="${esc(f.id)}">${icon('folder')}${esc(f.name)}${icon('right')}</div>`).join('')}</div><button id="confirm-move" class="button primary">Move here</button>`);
  $$('[data-destination]').forEach(el=>{el.onclick=()=>moveDialog(item,el.dataset.destination);el.onkeydown=e=>{if(e.key==='Enter')el.click();};});
  if($('#move-up'))$('#move-up').onclick=()=>moveDialog(item,data.breadcrumbs.length>1?data.breadcrumbs.at(-2).id:null);
  $('#confirm-move').onclick=async()=>{try{await api(`/nodes/${item.id}`,{method:'PATCH',body:JSON.stringify({parent,move:true})});$('#dialog').close();$('#inspector').hidden=true;await loadFiles();toast('Item moved.');}catch(e){toast(e.message,true);}};
 }catch(e){toast(e.message,true);}
}
async function loadMembers() {
 const data=await api('/admin');
 $('#members-list').innerHTML=data.users.map(user=>`<div class="member-row ${user.active?'':'inactive'}">${avatar(user.avatar_url,user.name,'avatar')}<div class="member-info"><strong>${esc(user.name)}${user.id===state.user.id?' (you)':''}</strong><small>${esc(user.email)}</small></div><span class="role-tag">${esc(user.role)}</span>${user.role!=='owner'?`<button class="button quiet" data-user="${esc(user.id)}" data-active="${user.active?'0':'1'}">${user.active?'Disable':'Enable'}</button>`:''}</div>`).join('');
 $$('[data-user]').forEach(el=>el.onclick=async()=>{try{await api(`/users/${el.dataset.user}`,{method:'PATCH',body:JSON.stringify({active:el.dataset.active==='1'})});await Promise.all([loadMembers(),refreshStats()]);toast(el.dataset.active==='1'?'Account enabled.':'Access removed and active sessions signed out.');}catch(e){toast(e.message,true);}});
 $('#invites-list').innerHTML=data.invites.length?data.invites.map(inv=>{const status=inv.used?'Accepted':inv.revoked?'Revoked':inv.expires<Date.now()/1000?'Expired':'Pending';return `<div class="member-row"><span class="avatar">${icon('user-plus')}</span><div class="member-info"><strong>${esc(inv.email)}</strong><small>${esc(inv.role)} access · expires ${date(inv.expires)}</small></div><span class="role-tag">${status}</span>${status==='Pending'?`<button class="button quiet" data-revoke="${esc(inv.id)}">Revoke</button>`:''}</div>`;}).join(''):'<p class="muted">No invitations yet. Create one to give someone access.</p>';
 $$('[data-revoke]').forEach(el=>el.onclick=async()=>{try{await api(`/invites/${el.dataset.revoke}`,{method:'DELETE'});await loadMembers();toast('Invitation revoked.');}catch(e){toast(e.message,true);}});
}
function inviteDialog() {
 formDialog('Invite a member',`<p>Send a private invitation link to someone you trust. They’ll choose their own password when they join.</p><label>Their email address<input type="email" name="email" placeholder="friend@example.com" required></label><label>They can…<select name="role"><option value="member">Browse and upload · Member</option><option value="viewer">Browse and download · Viewer</option></select></label><label>Invitation expires in<select name="days"><option value="7">7 days</option><option value="1">24 hours</option><option value="30">30 days</option></select></label>`,async f=>{
  const invite=await post('/invites',{email:f.get('email'),role:f.get('role'),days:Number(f.get('days'))});
  dialog('Invitation link',`<p class="dialog-text">Copy this single-use link and send it privately to <strong>${esc(f.get('email'))}</strong>. It is shown only once. No email has been sent automatically.</p><div class="invite-link-box">${esc(invite.url)}</div><button id="copy-invite" class="button primary">${icon('copy')} Copy invitation link</button>`);
  $('#copy-invite').onclick=async()=>{try{await navigator.clipboard.writeText(invite.url);toast('Invitation copied. Send it privately to your friend.');}catch{toast('Select the link above and copy it manually.');}};
  if(state.view==='members')await loadMembers();
 });
}
async function ensureFolder(parent,parts,cache) {
 let cursor=parent;
 for(const name of parts){const key=(cursor||'root')+'/'+name;if(!cache.has(key))cache.set(key,post('/folders',{parent:cursor,name}));cursor=(await cache.get(key)).id;}
 return cursor;
}
async function queueFiles(entries,emptyFolders=[]) {
 if(!canWrite())return toast('Your account has read-only access.',true);
 if(['trash','members'].includes(state.view))return toast('Open All files or a folder before uploading.',true);
 const parent=state.parent,cache=new Map();
 $('#upload-panel').hidden=false;$('#upload-reopen').hidden=true;
 try{
  for(const folder of emptyFolders)await ensureFolder(parent,folder.split('/').filter(Boolean),cache);
  for(const entry of entries){const parts=(entry.path||entry.file.name).split('/');const name=parts.pop();const item={file:entry.file,name,path:entry.path||entry.file.name,parent,cache,parts,status:'queued',progress:0,loaded:0,paused:false,id:null};state.uploads.push(item);}
  renderUploads();pump();await loadFiles();
 }catch(e){toast(e.message,true);}
}
function resumeKey(item){return `sasu-upload:${state.user.id}:${item.parent||'root'}:${item.path}:${item.file.size}:${item.file.lastModified}`;}
function renderUploads() {
 const active=state.uploads.filter(u=>!['done','cancelled'].includes(u.status)).length;
 $('#upload-heading').textContent=active?`Uploading ${active} file${active===1?'':'s'}`:'Uploads complete';
 $('#upload-items').innerHTML=state.uploads.slice(-100).map((u,index)=>{const realIndex=state.uploads.length>100?index+state.uploads.length-100:index;return `<div class="upload-item"><div>${icon(u.status==='done'?'check':u.status==='error'?'activity':'file')}<strong title="${esc(u.path)}">${esc(u.name)}</strong>${!['done','cancelled'].includes(u.status)?`<button data-pause="${realIndex}">${u.paused||u.status==='error'?'Resume':'Pause'}</button><button data-cancel="${realIndex}" aria-label="Cancel ${esc(u.name)}">×</button>`:''}</div><div class="upload-progress"><span data-progress="${Math.min(100,u.progress)}"></span></div><small>${u.error?esc(u.error):u.status==='done'?'Upload complete':u.status==='cancelled'?'Cancelled':u.paused?'Paused':u.status==='queued'?'Queued':`${bytes(u.loaded)} of ${bytes(u.file.size)} · ${u.progress.toFixed(0)}%`}</small></div>`;}).join('');
 $$('[data-progress]').forEach(el => { el.style.width = `${el.dataset.progress}%`; });
 $$('[data-pause]').forEach(el=>el.onclick=()=>{const u=state.uploads[Number(el.dataset.pause)];if(u.paused||u.status==='error'){u.paused=false;if(u.status==='error')u.status='queued';}else{u.paused=true;u.controller?.abort();}u.error=null;renderUploads();pump();});
 $$('[data-cancel]').forEach(el=>el.onclick=async()=>{const u=state.uploads[Number(el.dataset.cancel)];u.cancelled=true;u.controller?.abort();if(u.status!=='uploading')await removeUpload(u);renderUploads();});
}
async function removeUpload(item){try{if(item.id)await api(`/uploads/${item.id}`,{method:'DELETE'});try{localStorage.removeItem(item.key);}catch{}item.status='cancelled';item.error=null;}catch(e){item.status='error';item.error=e.message;item.cancelled=false;}}
function pump(){if(!state.user)return;for(const item of state.uploads){if(state.running>=2)break;if(item.status!=='queued'||item.paused||item.cancelled)continue;state.running++;item.status='uploading';runUpload(item).catch(e=>{item.status='error';item.error=e.message;}).finally(async()=>{state.running--;renderUploads();pump();if(state.running===0){try{await Promise.all([loadFiles(),refreshStats()]);}catch{}}});}}
async function runUpload(item){
 try{
  item.parent=await ensureFolder(item.parent,item.parts,item.cache);item.parts=[];
  item.key=resumeKey(item);let saved;try{saved=localStorage.getItem(item.key);}catch{}
  let offset=0,chunkSize=8*1024*1024;
  if(saved&&!item.id){try{const status=await api(`/uploads/${saved}`);if(status.node_id){try{localStorage.removeItem(item.key);}catch{}saved=null;}else{item.id=saved;offset=status.offset;}}catch(e){if(e.status!==404)throw e;try{localStorage.removeItem(item.key);}catch{}}}
  if(item.id){const status=await api(`/uploads/${item.id}`);if(status.node_id){item.status='done';item.progress=100;return;}offset=status.offset;}
  else{const result=await post('/uploads',{name:item.name,parent:item.parent,size:item.file.size,mime:item.file.type||'application/octet-stream'});item.id=result.id;chunkSize=result.chunk_size;try{localStorage.setItem(item.key,item.id);}catch{}}
  while(offset<item.file.size){
   if(item.cancelled){await removeUpload(item);return;}
   if(item.paused){item.status='queued';return;}
   item.controller=new AbortController();let attempts=0;
   while(true){
    try{const data=await api(`/uploads/${item.id}`,{method:'PATCH',headers:{'Content-Type':'application/octet-stream','Upload-Offset':String(offset)},body:item.file.slice(offset,offset+chunkSize),signal:item.controller.signal});offset=data.offset;break;}
    catch(e){if(e.name==='AbortError'||e.status===401||e.status===403||e.status===413||++attempts>3)throw e;await new Promise(r=>setTimeout(r,700*attempts));const status=await api(`/uploads/${item.id}`);offset=status.offset;}
   }
   item.loaded=offset;item.progress=item.file.size?offset/item.file.size*100:100;renderUploads();
  }
  if(item.cancelled){await removeUpload(item);return;}
  await post(`/uploads/${item.id}/complete`);item.status='done';item.progress=100;item.loaded=item.file.size;try{localStorage.removeItem(item.key);}catch{}
 }catch(e){if(item.cancelled){await removeUpload(item);return;}if(e.name==='AbortError'&&item.paused){item.status='queued';return;}throw e;}
}
async function pendingDialog() {
 try {
  const pending = await api('/uploads');
  const rows = pending.map(u => `<div class="member-row"><div class="member-info"><strong>${esc(u.name)}</strong><small>${bytes(u.offset)} of ${bytes(u.size)}</small></div><button class="button quiet" data-delete-upload="${esc(u.id)}">Cancel</button></div>`).join('');
  dialog('Things still on their way', pending.length ? `<p class="dialog-text">To resume an upload, choose the same file in the same destination folder again. Cancel an upload to release its reserved space.</p>${rows}` : '<p class="dialog-text">No unfinished uploads. Everything is tucked away.</p>');
  $$('[data-delete-upload]').forEach(el => el.onclick = async () => {
   try { await api(`/uploads/${el.dataset.deleteUpload}`, {method:'DELETE'}); await pendingDialog(); toast('Unfinished upload removed.'); }
   catch(e) { toast(e.message, true); }
  });
 } catch(e) { toast(e.message, true); }
}

async function traverse(entry,prefix,result,folders){const path=prefix+entry.name;if(entry.isFile){const file=await new Promise((resolve,reject)=>entry.file(resolve,reject));result.push({file,path});}else if(entry.isDirectory){folders.push(path);const reader=entry.createReader();while(true){const children=await new Promise((resolve,reject)=>reader.readEntries(resolve,reject));if(!children.length)break;for(const child of children)await traverse(child,path+'/',result,folders);}}}
let dragDepth=0;
window.addEventListener('dragenter',e=>{if(!state.user||!canWrite()||!e.dataTransfer.types.includes('Files'))return;e.preventDefault();dragDepth++;$('#drop-overlay').hidden=false;});
window.addEventListener('dragover',e=>{if(state.user&&e.dataTransfer.types.includes('Files'))e.preventDefault();});
window.addEventListener('dragleave',()=>{if(--dragDepth<=0){dragDepth=0;$('#drop-overlay').hidden=true;}});
window.addEventListener('drop',async e=>{if(!state.user)return;e.preventDefault();dragDepth=0;$('#drop-overlay').hidden=true;try{const entries=[...e.dataTransfer.items].map(i=>i.webkitGetAsEntry?.()).filter(Boolean);const result=[],folders=[];if(entries.length)for(const entry of entries)await traverse(entry,'',result,folders);else for(const file of e.dataTransfer.files)result.push({file,path:file.name});await queueFiles(result,folders);}catch(error){toast(error.message,true);}});
$('#auth-form').onsubmit=async e=>{e.preventDefault();$('.auth-submit').disabled=true;$('#auth-error').textContent='';try{const body={email:$('#auth-email').value,password:$('#auth-password').value};if(localSetup){body.name=$('#auth-name').value;body.samples=$('#setup-samples').checked;await post('/local-setup',body);localSetup=false;$('#samples-label').hidden=true;}else if(inviteToken){body.token=inviteToken;body.name=$('#auth-name').value;await post('/join',body);history.replaceState({},'',location.pathname);inviteToken=null;}else await post('/login',body);state.user=await api('/me');await enterDrive();}catch(error){$('#auth-error').textContent=error.message;}finally{$('.auth-submit').disabled=false;}};
$('#show-password').onclick=()=>{const input=$('#auth-password');input.type=input.type==='password'?'text':'password';$('#show-password').setAttribute('aria-label',input.type==='password'?'Show password':'Hide password');};
$('#logout').onclick=async()=>{try{if(state.uploads.some(u=>u.status==='uploading')&&!confirm('Uploads are still running. Sign out and pause them?'))return;state.uploads.forEach(u=>{u.paused=true;u.controller?.abort();});await post('/logout');state.user=null;state.uploads=[];state.items=[];state.selected.clear();$('#members-list').textContent='';$('#invites-list').textContent='';$('#file-list').textContent='';$('#inspector').textContent='';$('#upload-panel').hidden=true;$('#upload-reopen').hidden=true;showAuth();toast('Signed out. See you soon ♡');}catch(e){toast(e.message,true);}};
$$('[data-view]').forEach(el=>el.onclick=()=>navigate(el.dataset.view).catch(e=>toast(e.message,true)));
$('#sidebar-open').onclick=()=>$('#sidebar').classList.add('open');$('#sidebar-close').onclick=()=>$('#sidebar').classList.remove('open');
$('#nav-back').onclick=()=>history.back();$('#nav-up').onclick=()=>navigate('files',state.crumbs.length>1?state.crumbs.at(-2).id:null).catch(e=>toast(e.message,true));
$('#theme-toggle').onclick=()=>{const dark=document.documentElement.classList.toggle('dark');try{localStorage.setItem('nyuukoria-theme',dark?'dark':'light');}catch{}};
$('#dialog-close').onclick=()=>$('#dialog').close();$('#dialog').onclick=e=>{if(e.target===$('#dialog')){const rect=$('#dialog').getBoundingClientRect();if(e.clientX<rect.left||e.clientX>rect.right||e.clientY<rect.top||e.clientY>rect.bottom)$('#dialog').close();}};
$('#invite-button').onclick=$('#add-invite').onclick=inviteDialog;
$('#new-folder').onclick=()=>formDialog('New folder',`<p>Create a folder in ${state.crumbs.length?esc(state.crumbs.at(-1).name):'All files'}.</p><label>Folder name<input name="name" placeholder="Folder name" required maxlength="200" autofocus></label>`,async f=>{await post('/folders',{name:f.get('name'),parent:state.parent});$('#dialog').close();await Promise.all([loadFiles(),refreshStats()]);toast('Folder created.');});
$('#upload-toggle').onclick=()=>$('#upload-menu').hidden=!$('#upload-menu').hidden;
$('#sidebar-upload').onclick=()=>{if(['trash','members'].includes(state.view)){navigate('files').then(()=>$('#file-input').click()).catch(e=>toast(e.message,true));}else $('#file-input').click();};
$('#pick-files').onclick=()=>{$('#upload-menu').hidden=true;$('#file-input').click();};$('#pick-folder').onclick=()=>{$('#upload-menu').hidden=true;$('#folder-input').click();};
for(const selector of ['#file-input','#folder-input'])$(selector).onchange=e=>{queueFiles([...e.target.files].map(file=>({file,path:file.webkitRelativePath||file.name}))).catch(e=>toast(e.message,true));e.target.value='';};
document.addEventListener('click',e=>{if(!e.target.closest('.upload-menu-wrap'))$('#upload-menu').hidden=true;});
let searchTimer;$('#search').oninput=e=>{clearTimeout(searchTimer);state.search=e.target.value;state.selected.clear();searchTimer=setTimeout(()=>loadFiles().catch(e=>toast(e.message,true)),250);};
$('#sort').onchange=()=>loadFiles().catch(e=>toast(e.message,true));$('#refresh').onclick=()=>Promise.all([loadFiles(),refreshStats()]).catch(e=>toast(e.message,true));$('#load-more').onclick=()=>loadFiles(true).catch(e=>toast(e.message,true));
$('#list-view').onclick=()=>{state.grid=false;try{localStorage.setItem('sasu-view','list');}catch{}renderFiles();};$('#grid-view').onclick=()=>{state.grid=true;try{localStorage.setItem('sasu-view','grid');}catch{}renderFiles();};
$('#clear-selection').onclick=()=>{state.selected.clear();renderFiles();};$('#trash-selection').onclick=async()=>{let succeeded=0;for(const id of state.selected){try{if(state.view==='trash')await post(`/nodes/${id}/restore`);else await api(`/nodes/${id}`,{method:'DELETE'});succeeded++;}catch(e){toast(e.message,true);}}state.selected.clear();await Promise.all([loadFiles(),refreshStats()]);toast(`${succeeded} item${succeeded===1?'':'s'} ${state.view==='trash'?'restored':'moved to trash'}.`);};
$('#minimize-uploads').onclick=()=>{$('#upload-panel').hidden=true;$('#upload-reopen').hidden=false;$('#upload-reopen').textContent='Show uploads';};$('#upload-reopen').onclick=()=>{if(!state.uploads.length){pendingDialog();return;}$('#upload-panel').hidden=false;$('#upload-reopen').hidden=true;};$('#pending-button').onclick=pendingDialog;
$('#activity-button').onclick=async()=>{try{const rows=await api('/activity');dialog('Recent activity',rows.length?rows.map(r=>`<div class="activity-row"><strong>${esc(r.actor||'A member')}</strong> ${esc(r.action)}<br>${esc(r.name)}<small>${date(r.created)}</small></div>`).join(''):'<p class="dialog-text">Uploads, folder changes and invitations will appear here.</p>');}catch(e){toast(e.message,true);}};
document.addEventListener('keydown',e=>{if(e.key==='/'&&state.user&&!$('#dialog').open&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)){e.preventDefault();$('#search').focus();}if(e.key==='Escape'){$('#inspector').hidden=true;$('#sidebar').classList.remove('open');}});
window.addEventListener('beforeunload',e=>{if(state.uploads.some(u=>u.status==='uploading'||u.status==='queued')){e.preventDefault();e.returnValue='';}});
async function init(){icons();try{const initialStatus=await api('/status');$('#local-test-banner').hidden=!initialStatus.local_test;if(initialStatus.local_test&&!initialStatus.configured&&!inviteToken){localSetup=true;$('#auth-title').textContent='Set up your local drive';$('#auth-eyebrow').textContent='YOUR LOCAL TEST DRIVE';$('#auth-description').textContent='Choose your local owner account. Your test files and login stay on this PC.';$('#name-label').hidden=false;$('#auth-name').required=true;$('#samples-label').hidden=false;$('#auth-password').minLength=10;$('#auth-password').autocomplete='new-password';$('#auth-password').placeholder='At least 10 characters';$('#auth-submit-label').textContent='Create my local drive';return;}if(inviteToken){const invite=await api('/invite?token='+encodeURIComponent(inviteToken));$('#auth-title').textContent='You’re invited.';$('#auth-eyebrow').textContent='PRIVATE INVITATION';$('#auth-description').textContent=`Join the circle with ${invite.role==='viewer'?'read-only':'upload'} access. Choose a name and password to make yourself at home.`;$('#name-label').hidden=false;$('#auth-name').required=true;$('#auth-email').value=invite.email;$('#auth-email').readOnly=true;$('#auth-password').minLength=10;$('#auth-password').autocomplete='new-password';$('#auth-password').placeholder='At least 10 characters';$('#auth-submit-label').textContent='Join the circle';return;}try{state.user=await api('/me');await enterDrive();}catch(e){if(e.status!==401)throw e;showAuth();const status=await api('/status');$('#setup-note').hidden=status.configured;}}catch(e){$('#auth-error').textContent=e.message;}}

function renderProfile() {
  for (const id of ['#user-avatar', '#circle-avatar']) {
    $(id).innerHTML = state.user.avatar_url
      ? `<img src="${esc(state.user.avatar_url)}" alt="">`
      : esc(state.user.name.slice(0, 1).toUpperCase());
  }
  $('#user-name').textContent = state.user.name;

  if (state.user.theme_color) {
    document.documentElement.style.setProperty(
      '--user-theme-color',
      state.user.theme_color
    );
  }
}

function choosePicture(endpoint, onDone) {
  const input = $('#picture-input');
  input.value = '';
  input.onchange = async () => {
    const file = input.files[0];
    if (!file) return;
    if (file.size > 8 * 1024 * 1024)
      return toast('Choose an image smaller than 8 MB.', true);
    try {
      toast('Saving picture…');
      await api(endpoint, {
        method: 'POST',
        body: file,
        headers: { 'Content-Type': file.type || 'application/octet-stream' },
      });
      await onDone();
      await refreshStats();
      toast('Picture updated.');
    } catch (e) {
      toast(e.message, true);
    } finally {
      input.value = '';
    }
  };
  input.click();
}

async function refreshProfile() {
  state.user = await api('/me');
  renderProfile();
  if (state.view === 'members') await loadMembers();
  else await loadFiles();
}

function profileDialog() {
  formDialog(
    'Your profile & settings',
    `
  <div class="profile-preview">
    ${avatar(state.user.avatar_url, state.user.name, 'avatar large-avatar')}
    <div>
      <button type="button" class="button subtle" id="change-avatar">${icon('image')} Change avatar</button>
      ${state.user.avatar_url ? '<button type="button" class="button quiet" id="remove-avatar">Remove avatar</button>' : ''}
    </div>
  </div>
  <p class="muted">Avatar: PNG, JPG, WebP or GIF · up to 8 MB.</p>
  
  <div style="margin-top:15px;">
    <button type="button" class="button subtle" id="change-banner">${icon('image')} ${state.user.banner_url ? 'Change' : 'Add'} profile banner</button>
    ${state.user.banner_url ? '<button type="button" class="button quiet" id="remove-banner">Remove banner</button>' : ''}
  </div>

  <label>Display name<input name="name" value="${esc(state.user.name)}" required maxlength="60"></label>
  <label>Bio / Status<textarea name="bio" rows="2" maxlength="500" placeholder="Tell members about yourself...">${esc(state.user.bio || '')}</textarea></label>
  <label>Accent Color<input type="color" name="theme_color" value="${esc(state.user.theme_color || '#ac4569')}"></label>
  <label>Email<input value="${esc(state.user.email)}" readonly></label>

  <hr style="border:0;border-top:1px solid var(--line);margin:20px 0;">
  <h3>Change Password</h3>
  <label>Current Password<input type="password" id="current_password" placeholder="Current password"></label>
  <label>New Password<input type="password" id="new_password" placeholder="At least 6 characters" minlength="6"></label>
  <button type="button" class="button subtle" id="update-password-btn" style="margin-top:10px;">Update Password</button>
  `,
    async (f) => {
      const themeColor = f.get('theme_color');
      await api('/me', {
        method: 'PATCH',
        body: JSON.stringify({
          name: f.get('name'),
          bio: f.get('bio'),
          theme_color: themeColor,
        }),
      });
      document.documentElement.style.setProperty(
        '--user-theme-color',
        themeColor
      );
      await refreshProfile();
      $('#dialog').close();
      toast('Profile updated.');
    }
  );

  $('#change-avatar').onclick = () =>
    choosePicture('/me/avatar', async () => {
      await refreshProfile();
      profileDialog();
    });
  if ($('#remove-avatar'))
    $('#remove-avatar').onclick = async () => {
      try {
        await api('/me/avatar', { method: 'DELETE' });
        await refreshProfile();
        profileDialog();
        await refreshStats();
        toast('Profile picture removed.');
      } catch (e) {
        toast(e.message, true);
      }
    };

  $('#change-banner').onclick = () =>
    choosePicture('/me/banner', async () => {
      await refreshProfile();
      profileDialog();
    });
  if ($('#remove-banner'))
    $('#remove-banner').onclick = async () => {
      try {
        await api('/me/banner', { method: 'DELETE' });
        await refreshProfile();
        profileDialog();
        await refreshStats();
        toast('Banner removed.');
      } catch (e) {
        toast(e.message, true);
      }
    };

  $('#update-password-btn').onclick = async () => {
    const current_password = $('#current_password').value;
    const new_password = $('#new_password').value;
    if (!current_password || !new_password)
      return toast('Please enter both current and new passwords.', true);
    if (new_password.length < 6)
      return toast('New password must be at least 6 characters.', true);
    try {
      await post('/auth/change-password', { current_password, new_password });
      $('#current_password').value = '';
      $('#new_password').value = '';
      toast('Password changed successfully!');
    } catch (e) {
      toast(e.message, true);
    }
  };
}

$('#user-avatar').onclick = $('#profile-button').onclick = profileDialog;
document.addEventListener('keydown', (e) => {
  if (
    !state.user ||
    $('#dialog').open ||
    ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)
  )
    return;
  if (e.altKey && e.key === 'ArrowUp' && state.parent) {
    e.preventDefault();
    $('#nav-up').click();
  }
  if (
    (e.ctrlKey || e.metaKey) &&
    e.key.toLowerCase() === 'a' &&
    state.view !== 'members'
  ) {
    e.preventDefault();
    state.items.forEach((i) => state.selected.add(i.id));
    renderFiles();
  }
});

init();


// Apply user custom theme color on load
if (user.theme_color) {
    document.documentElement.style.setProperty('--user-theme-color', user.theme_color);
}

// Client theme customizer handler
function applyCustomTheme(hexColor) {
    document.documentElement.style.setProperty('--user-theme-color', hexColor);
    // Send to PATCH /api/me with theme_color to persist across devices
}