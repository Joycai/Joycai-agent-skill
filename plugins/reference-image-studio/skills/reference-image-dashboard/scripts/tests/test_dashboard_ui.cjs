// Dependency-free interaction smoke test against a built dashboard snapshot.
// node test_dashboard_ui.cjs /path/to/workspace/dashboard/index.html
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
class Element {
  constructor(){this.value='';this.children=[];this.style={setProperty(){}};this.open=false;this.q={};this.dataset={};this.classes=new Set();this.classList={toggle:(name,on)=>{const enabled=on??!this.classes.has(name);enabled?this.classes.add(name):this.classes.delete(name);return enabled}}}
  replaceChildren(){this.children=[]}append(x){this.children.push(x)}
  querySelector(key){return this.q[key]??=new Element()}
  querySelectorAll(key){const attr=key==='button'?'tab':'image';return [...(this.innerHTML||'').matchAll(new RegExp(`data-${attr}="([^"]+)"`,'g'))].map(m=>{const e=new Element();e.dataset[attr]=m[1];return e})}
  showModal(){this.open=true}close(){this.open=false}addEventListener(){}scrollIntoView(){}
}
const elements={};const context={document:{getElementById(id){return elements[id]??=new Element()},createElement(){return new Element()},addEventListener(){}},localStorage:{getItem(){return null},setItem(){}},navigator:{clipboard:{async writeText(){}}},window:{prompt(){}},location:{reload(){}}};
for(const id of ['model','state'])context.document.getElementById(id).value=id==='model'?'all':'confirmed';
vm.createContext(context);const html=fs.readFileSync(process.argv[2],'utf8');const script=html.split('<script>')[1].split('</script>')[0];vm.runInContext(script,context);
const run=code=>vm.runInContext(code,context);
assert.equal(elements.grid.children.length,run("project.references.filter(x=>x.status==='confirmed').length")||1);
run("tab='tasks';render()");const all=run('visible().length');assert(all>=1);
run("$('model').value=catalog.find(x=>x.section==='tasks'&&x.model)?.model||'all';render()");assert(run('visible().every(x=>$(\'model\').value===\'all\'||x.model===$(\'model\').value)'));
run("$('model').value='all';$('search').value='definitely-no-match-76591';render()");assert.equal(run('visible().length'),0);
run("$('search').value='';render()");
const images=run("catalog.filter(x=>x.section==='tasks'&&x.asset?.exists&&x.asset?.image).length");
if(images>=2){run("selected=new Set(catalog.filter(x=>x.section==='tasks'&&x.asset?.exists&&x.asset?.image).slice(0,2).map(x=>x.key));save();$('compare').onclick()");assert.equal(elements.viewer.open,true);assert.equal(elements.view.style.gridTemplateColumns,'repeat(2,minmax(0,1fr))');run("$('viewclose').onclick();$('clear').onclick()");assert.equal(elements.compare.disabled,true)}
if(run('project.retained.length')){run("showDetails(catalog.find(x=>x.section==='retained'))");assert.equal(elements.detail.open,true);assert(run("$('detailbody').innerHTML.includes(esc(project.retained[0].origin.task))"));const prompt=run("taskMap.get(project.retained[0].origin.task).steps.find(s=>s.id===project.retained[0].origin.step).prompt.text");assert(elements.detailbody.innerHTML.includes(run('esc('+JSON.stringify(prompt)+')')))}
run("tab='unregistered';render()");assert.equal(run('visible().length'),run('project.unregistered.length'));
console.log('Passed: confirmed-reference filtering, task/model/search filters, comparison, clearing, retained provenance/prompt, unregistered separation.');

run("tab='archived';$('model').value='all';$('search').value='';render()");assert(run("visible().every(x=>x.asset.archived)"));assert(run("catalog.filter(x=>x.section==='tasks').every(x=>!x.asset?.archived)"));
console.log('Passed: archived items separated from active tasks.');
